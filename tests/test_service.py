from mssql_pyodbc_mcp.config import DatabaseConfig
from mssql_pyodbc_mcp.db import ConnectionFactory, DatabaseClient, MAX_ROWS
from mssql_pyodbc_mcp.errors import ToolError
from mssql_pyodbc_mcp.service import MssqlToolService, as_tool_response


ENV = {
    "MSSQL_SERVER": "localhost",
    "MSSQL_DATABASE": "appdb",
    "MSSQL_USER": "sa",
    "MSSQL_PASSWORD": "secret",
}

SECONDARY_ENV = {
    **ENV,
    "MSSQL_SECONDARY_SERVER": "analytics",
    "MSSQL_SECONDARY_DATABASE": "dw",
    "MSSQL_SECONDARY_USER": "reader",
    "MSSQL_SECONDARY_PASSWORD": "secondary-secret",
}


class FakeCursor:
    def __init__(self):
        self.description = [("id",), ("name",)]
        self.last_sql = None
        self.params = ()

    def execute(self, sql, *params):
        self.last_sql = sql
        self.params = params
        return self

    def fetchone(self):
        return (1,)

    def fetchall(self):
        sql = self.last_sql or ""
        if "INFORMATION_SCHEMA.TABLES" in sql and "TABLE_NAME = ?" in sql:
            return [("dbo", self.params[0])]
        if "INFORMATION_SCHEMA.TABLES" in sql:
            return [("dbo", "Users")]
        if "INFORMATION_SCHEMA.COLUMNS" in sql:
            return [("id", "int", "NO"), ("name", "nvarchar", "YES")]
        return []

    def fetchmany(self, size):
        return [(idx, f"name-{idx}") for idx in range(size)]


class FakeConnection:
    def __init__(self):
        self.closed = False
        self.cursor_obj = FakeCursor()

    def cursor(self):
        return self.cursor_obj

    def close(self):
        self.closed = True


class FakePyodbc:
    def __init__(self):
        self.connection = FakeConnection()
        self.connection_strings = []

    def connect(self, connection_string, timeout):
        self.connection_strings.append(connection_string)
        assert "PWD=" in connection_string
        assert timeout == 5
        return self.connection


def test_connection_tool_uses_safe_identity():
    service = MssqlToolService(ENV, pyodbc_module=FakePyodbc())

    result = service.test_connection()

    assert result["ok"] is True
    assert result["db"] == "default"
    assert result["server"] == "localhost,1433"
    assert result["database"] == "appdb"
    assert "secret" not in str(result)


def test_list_tables_returns_user_table_shape():
    service = MssqlToolService(ENV, pyodbc_module=FakePyodbc())

    result = service.list_tables()

    assert result == {
        "ok": True,
        "db": "default",
        "server": "localhost,1433",
        "database": "appdb",
        "tables": [{"schema": "dbo", "name": "Users", "full_name": "dbo.Users"}],
    }


def test_describe_table_returns_simple_schema():
    service = MssqlToolService(ENV, pyodbc_module=FakePyodbc())

    result = service.describe_table("dbo.Users")

    assert result["db"] == "default"
    assert result["table"] == "dbo.Users"
    assert result["columns"] == [
        {"column_name": "id", "data_type": "int", "nullable": False},
        {"column_name": "name", "data_type": "nvarchar", "nullable": True},
    ]


def test_query_limits_to_max_rows_and_marks_truncated():
    service = MssqlToolService(ENV, pyodbc_module=FakePyodbc())

    result = service.query("SELECT id, name FROM dbo.Users")

    assert result["row_count"] == MAX_ROWS
    assert result["db"] == "default"
    assert result["truncated"] is True
    assert result["max_rows"] == MAX_ROWS
    assert result["rows"][0] == {"id": 0, "name": "name-0"}


def test_as_tool_response_returns_structured_error():
    def fail():
        raise ToolError("SQL_REJECTED", "No.")

    assert as_tool_response(fail) == {"ok": False, "code": "SQL_REJECTED", "message": "No."}


def test_database_client_can_be_constructed_directly():
    config = DatabaseConfig.from_env(ENV)
    client = DatabaseClient(ConnectionFactory(config, pyodbc_module=FakePyodbc()))

    assert client.test_connection()["ok"] is True


def test_service_routes_to_secondary_profile():
    fake_pyodbc = FakePyodbc()
    service = MssqlToolService(SECONDARY_ENV, pyodbc_module=fake_pyodbc)

    result = service.test_connection(db="secondary")

    assert result["ok"] is True
    assert result["db"] == "secondary"
    assert result["server"] == "analytics,1433"
    assert result["database"] == "dw"
    assert "SERVER=analytics,1433;" in fake_pyodbc.connection_strings[0]
    assert "UID=reader;" in fake_pyodbc.connection_strings[0]
    assert "PWD=secondary-secret;" in fake_pyodbc.connection_strings[0]


def test_as_tool_response_returns_invalid_profile_error():
    service = MssqlToolService(ENV, pyodbc_module=FakePyodbc())

    result = as_tool_response(service.list_tables, "archive")

    assert result["ok"] is False
    assert result["code"] == "CONFIG_INVALID"
