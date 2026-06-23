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
    def test_connection() -> dict[str, Any]:
        """Validate MSSQL environment configuration and test database connectivity."""

        return as_tool_response(service.test_connection)

    @app.tool()
    def list_tables() -> dict[str, Any]:
        """List accessible user tables in the configured MSSQL database."""

        return as_tool_response(service.list_tables)

    @app.tool()
    def describe_table(table_name: str) -> dict[str, Any]:
        """Return column_name, data_type, and nullable for a table."""

        return as_tool_response(service.describe_table, table_name)

    @app.tool()
    def query(sql: str) -> dict[str, Any]:
        """Execute a read-only SELECT query and return at most 100 rows."""

        return as_tool_response(service.query, sql)

    return app


def main() -> None:
    create_server().run()
