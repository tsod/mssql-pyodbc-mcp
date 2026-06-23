from __future__ import annotations

from typing import Any

from .service import MssqlToolService, as_tool_response


def create_server() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("The 'mcp' package is required to run the MCP server.") from exc

    app = FastMCP("mssql-pyodbc-mcp")
    service = MssqlToolService()

    @app.tool()
    def test_connection(db: str = "default") -> dict[str, Any]:
        """Validate MSSQL environment configuration and test database connectivity."""

        return as_tool_response(service.test_connection, db)

    @app.tool()
    def list_tables(db: str = "default") -> dict[str, Any]:
        """List accessible user tables in the selected MSSQL database."""

        return as_tool_response(service.list_tables, db)

    @app.tool()
    def describe_table(table_name: str, db: str = "default") -> dict[str, Any]:
        """Return column_name, data_type, and nullable for a table."""

        return as_tool_response(service.describe_table, table_name, db)

    @app.tool()
    def query(sql: str, db: str = "default") -> dict[str, Any]:
        """Execute a read-only SELECT query and return at most 100 rows."""

        return as_tool_response(service.query, sql, db)

    return app


def main() -> None:
    create_server().run()
