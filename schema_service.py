"""Schema extraction utilities for the integrated NLP-to-SQL pipeline."""

from typing import Dict, List
import sqlite3


def list_user_tables(conn: sqlite3.Connection) -> List[str]:
    """Return all non-system table names from the database."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )
    return [row[0] for row in cursor.fetchall()]


def get_table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    """Return column names for a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def get_sample_rows(conn: sqlite3.Connection, table_name: str, limit: int = 2) -> List[Dict[str, str]]:
    """Return a small sample of rows from a table."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    column_names = [description[0] for description in cursor.description] if cursor.description else []
    rows = []
    for raw_row in cursor.fetchall():
        rows.append({column_names[index]: raw_row[index] for index in range(len(column_names))})
    return rows


def build_schema_bundle(conn: sqlite3.Connection, sample_limit: int = 2) -> Dict[str, object]:
    """Build structured schema data plus a compact schema text representation."""
    tables = []
    for table_name in list_user_tables(conn):
        columns = get_table_columns(conn, table_name)
        tables.append(
            {
                "table_name": table_name,
                "columns": columns,
                "sample_rows": get_sample_rows(conn, table_name, limit=sample_limit),
            }
        )

    schema_text = "\n".join(
        f"{table['table_name']}({', '.join(table['columns'])})"
        for table in tables
    )
    headers = [column for table in tables for column in table["columns"]]

    return {
        "tables": tables,
        "schema_text": schema_text,
        "headers": headers,
    }
