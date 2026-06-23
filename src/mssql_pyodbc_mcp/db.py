from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol

from .config import DatabaseConfig
from .errors import ToolError
from .serialization import to_json_safe

MAX_ROWS = 100


class CursorLike(Protocol):
    description: Iterable[Any] | None

    def execute(self, sql: str, *params: Any) -> "CursorLike": ...

    def fetchone(self) -> Any: ...

    def fetchall(self) -> list[Any]: ...

    def fetchmany(self, size: int) -> list[Any]: ...


class ConnectionLike(Protocol):
    def cursor(self) -> CursorLike: ...

    def close(self) -> None: ...


class ConnectionFactory:
    def __init__(self, config: DatabaseConfig, pyodbc_module: Any | None = None, timeout_seconds: int = 5):
        self.config = config
        self.pyodbc_module = pyodbc_module
        self.timeout_seconds = timeout_seconds

    def connect(self) -> ConnectionLike:
        module = self.pyodbc_module
        if module is None:
            try:
                import pyodbc as module  # type: ignore[no-redef]
            except ImportError as exc:
                raise ToolError("CONFIG_INVALID", "pyodbc is not installed.") from exc

        try:
            connection = module.connect(self.config.connection_string(), timeout=self.timeout_seconds)
            if hasattr(connection, "timeout"):
                connection.timeout = 30
            return connection
        except Exception as exc:  # pyodbc exposes driver-specific exception classes.
            raise ToolError("CONNECTION_FAILED", "Could not connect to MSSQL database.", self.config.safe_identity()) from exc


class DatabaseClient:
    def __init__(self, factory: ConnectionFactory):
        self.factory = factory

    def test_connection(self) -> dict[str, Any]:
        connection = self.factory.connect()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return {"ok": True, **self.factory.config.safe_identity(), "message": "Connection successful."}
        finally:
            connection.close()

    def list_tables(self) -> dict[str, Any]:
        rows = self._fetch_all(
            """
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
              AND TABLE_SCHEMA NOT IN ('sys', 'INFORMATION_SCHEMA')
            ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
        )
        tables = [
            {"schema": row[0], "name": row[1], "full_name": f"{row[0]}.{row[1]}"}
            for row in rows
        ]
        return {"ok": True, **self.factory.config.safe_identity(), "tables": tables}

    def describe_table(self, table_name: str) -> dict[str, Any]:
        schema, name = parse_table_name(table_name)
        if schema is None:
            matches = self._fetch_all(
                """
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                  AND TABLE_NAME = ?
                ORDER BY TABLE_SCHEMA
                """,
                name,
            )
            if not matches:
                raise ToolError("TABLE_NOT_FOUND", "Table was not found.", {"table_name": table_name})
            if len(matches) > 1:
                raise ToolError(
                    "TABLE_AMBIGUOUS",
                    "Table name matches multiple schemas; use schema-qualified name.",
                    {"matches": [f"{row[0]}.{row[1]}" for row in matches]},
                )
            schema = matches[0][0]

        rows = self._fetch_all(
            """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ?
              AND TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
            """,
            schema,
            name,
        )
        if not rows:
            raise ToolError("TABLE_NOT_FOUND", "Table was not found or has no visible columns.", {"table_name": table_name})

        columns = [
            {"column_name": row[0], "data_type": row[1], "nullable": str(row[2]).upper() == "YES"}
            for row in rows
        ]
        return {"ok": True, **self.factory.config.safe_identity(), "table": f"{schema}.{name}", "columns": columns}

    def execute_query(self, sql: str) -> dict[str, Any]:
        connection = self.factory.connect()
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            fetched = cursor.fetchmany(MAX_ROWS + 1)
            truncated = len(fetched) > MAX_ROWS
            rows = fetched[:MAX_ROWS]
            columns = [description[0] for description in (cursor.description or [])]
            return {
                "ok": True,
                **self.factory.config.safe_identity(),
                "columns": columns,
                "rows": [row_to_dict(columns, row) for row in rows],
                "row_count": len(rows),
                "truncated": truncated,
                "max_rows": MAX_ROWS,
            }
        except ToolError:
            raise
        except Exception as exc:
            raise ToolError("QUERY_FAILED", "Query execution failed.") from exc
        finally:
            connection.close()

    def _fetch_all(self, sql: str, *params: Any) -> list[Any]:
        connection = self.factory.connect()
        try:
            cursor = connection.cursor()
            cursor.execute(sql, *params)
            return cursor.fetchall()
        except ToolError:
            raise
        except Exception as exc:
            raise ToolError("QUERY_FAILED", "Metadata query failed.") from exc
        finally:
            connection.close()


def parse_table_name(table_name: str) -> tuple[str | None, str]:
    cleaned = table_name.strip()
    if not cleaned:
        raise ToolError("TABLE_NOT_FOUND", "table_name is required.")

    parts = [part.strip().strip("[]") for part in cleaned.split(".")]
    if len(parts) == 1:
        return None, parts[0]
    if len(parts) == 2 and all(parts):
        return parts[0], parts[1]
    raise ToolError("TABLE_NOT_FOUND", "Use table name or schema-qualified table name.", {"table_name": table_name})


def row_to_dict(columns: list[str], row: Any) -> dict[str, Any]:
    return {column: to_json_safe(value) for column, value in zip(columns, row)}
