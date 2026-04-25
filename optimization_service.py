"""Optimization service wrapper for the SQL optimization stage."""

from typing import Any, Dict
import sqlite3

from optimizer import analyze_performance


class SQLOptimizationService:
    """Optimize and benchmark SQL against the active SQLite database."""

    def optimize(self, conn: sqlite3.Connection, sql: str) -> Dict[str, Any]:
        """Return JSON-safe optimizer output."""
        optimization = analyze_performance(conn, sql, runs=10)
        return {
            "plan_before": optimization["plan_before"],
            "issues": optimization["issues"],
            "recommended_indexes": optimization["recommended_indexes"],
            "benchmark": {
                "before_ms": round(optimization["benchmark"]["before_ms"], 4),
                "after_ms": round(optimization["benchmark"]["after_ms"], 4),
                "speedup": round(optimization["benchmark"]["speedup"], 2),
            },
        }
