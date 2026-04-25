"""Validation service wrapper for the SQL validation stage."""

from typing import Any, Dict
import sqlite3

from validator import validate_and_rewrite_query


class SQLValidationService:
    """Validate and optionally rewrite generated SQL."""

    def validate(
        self,
        question: str,
        schema_text: str,
        generated_sql: str,
        conn: sqlite3.Connection,
    ) -> Dict[str, Any]:
        """Run the validator against the current question, schema, and SQL."""
        return validate_and_rewrite_query(question, schema_text, generated_sql, conn)
