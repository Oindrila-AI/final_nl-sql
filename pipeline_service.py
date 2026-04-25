"""Pipeline orchestration for the modular NLP-to-SQL backend."""

from typing import Any, Dict
import sqlite3

from generator_service import SQLGeneratorService
from optimization_service import SQLOptimizationService
from schema_service import build_schema_bundle
from validation_service import SQLValidationService


class NL2SQLPipelineService:
    """Coordinate schema extraction, SQL generation, validation, and optimization."""

    def __init__(
        self,
        generator: SQLGeneratorService,
        validator: SQLValidationService,
        optimizer: SQLOptimizationService,
    ) -> None:
        """Store the pipeline dependencies."""
        self.generator = generator
        self.validator = validator
        self.optimizer = optimizer

    def run(self, question: str, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Execute the full pipeline while passing shared state across stages."""
        schema_bundle = build_schema_bundle(conn)
        generated_input = self.generator.build_input(question, schema_bundle["headers"])
        generated_sql = self.generator.generate_sql(question, schema_bundle["headers"])
        validation = self.validator.validate(question, schema_bundle["schema_text"], generated_sql, conn)
        validated_sql = validation.get("corrected_sql") or generated_sql
        execution = self._execute_with_fallback(conn, validated_sql, generated_sql)

        try:
            optimization = self.optimizer.optimize(conn, execution["executed_sql"])
        except Exception:
            optimization = {
                "plan_before": [],
                "issues": [],
                "recommended_indexes": [],
                "benchmark": {},
            }

        return {
            "schema_bundle": schema_bundle,
            "generated_input": generated_input,
            "generated_sql": generated_sql,
            "validation": validation,
            "validated_sql": validated_sql,
            "final_sql": execution["executed_sql"],
            "result": execution["rows"],
            "optimization": optimization,
        }

    @staticmethod
    def _execute_with_fallback(
        conn: sqlite3.Connection,
        preferred_sql: str,
        fallback_sql: str,
    ) -> Dict[str, Any]:
        """Execute validated SQL, then fall back to the original generated SQL if needed."""
        try:
            cursor = conn.execute(preferred_sql)
            return {
                "executed_sql": preferred_sql,
                "rows": [dict(row) for row in cursor.fetchall()],
            }
        except Exception:
            cursor = conn.execute(fallback_sql)
            return {
                "executed_sql": fallback_sql,
                "rows": [dict(row) for row in cursor.fetchall()],
            }
