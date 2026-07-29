import pytest

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

GLOBAL_BUSINESS_ENV = {
    **ENV,
    "MSSQL_GLOBAL_BUSINESS_SERVER": "analytics",
    "MSSQL_GLOBAL_BUSINESS_DATABASE": "dw",
    "MSSQL_GLOBAL_BUSINESS_USER": "reader",
    "MSSQL_GLOBAL_BUSINESS_PASSWORD": "global-business-secret",
}

NAMED_ENV = {
    **GLOBAL_BUSINESS_ENV,
    "MSSQL_TEND_SERVER": "tend-host",
    "MSSQL_TEND_DATABASE": "TendDb",
    "MSSQL_TEND_USER": "tend-user",
    "MSSQL_TEND_PASSWORD": "tend-secret",
    "MSSQL_PROJECTWORKTRACKER_SERVER": "tracker-host",
    "MSSQL_PROJECTWORKTRACKER_DATABASE": "ProjectWorkTrackerDb",
    "MSSQL_PROJECTWORKTRACKER_USER": "tracker-user",
    "MSSQL_PROJECTWORKTRACKER_PASSWORD": "tracker-secret",
    "MSSQL_TWNTAXIAD_SERVER": "taxi-host",
    "MSSQL_TWNTAXIAD_DATABASE": "TWNTaxiADDb",
    "MSSQL_TWNTAXIAD_USER": "taxi-user",
    "MSSQL_TWNTAXIAD_PASSWORD": "taxi-secret",
    "MSSQL_TWNTAXIAD53_SERVER": "taxi53-host",
    "MSSQL_TWNTAXIAD53_DATABASE": "TWTaxiAD53Db",
    "MSSQL_TWNTAXIAD53_USER": "taxi53-user",
    "MSSQL_TWNTAXIAD53_PASSWORD": "taxi53-secret",
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


def test_service_routes_to_global_business_profile():
    fake_pyodbc = FakePyodbc()
    service = MssqlToolService(GLOBAL_BUSINESS_ENV, pyodbc_module=fake_pyodbc)

    result = service.test_connection(db="GlobalBusiness")

    assert result["ok"] is True
    assert result["db"] == "global_business"
    assert result["server"] == "analytics,1433"
    assert result["database"] == "dw"
    assert "SERVER=analytics,1433;" in fake_pyodbc.connection_strings[0]
    assert "UID=reader;" in fake_pyodbc.connection_strings[0]
    assert "PWD=global-business-secret;" in fake_pyodbc.connection_strings[0]


def test_service_routes_by_configured_database_name():
    fake_pyodbc = FakePyodbc()
    service = MssqlToolService(GLOBAL_BUSINESS_ENV, pyodbc_module=fake_pyodbc)

    result = service.test_connection(db="dw")

    assert result["ok"] is True
    assert result["db"] == "global_business"
    assert result["server"] == "analytics,1433"
    assert result["database"] == "dw"
    assert "SERVER=analytics,1433;" in fake_pyodbc.connection_strings[0]


def test_service_routes_to_tend_profile():
    fake_pyodbc = FakePyodbc()
    service = MssqlToolService(NAMED_ENV, pyodbc_module=fake_pyodbc)

    result = service.test_connection(db="Tend")

    assert result["ok"] is True
    assert result["db"] == "tend"
    assert result["server"] == "tend-host,1433"
    assert result["database"] == "TendDb"
    assert "SERVER=tend-host,1433;" in fake_pyodbc.connection_strings[0]
    assert "UID=tend-user;" in fake_pyodbc.connection_strings[0]
    assert "PWD=tend-secret;" in fake_pyodbc.connection_strings[0]


def test_service_routes_to_projectworktracker_profile():
    fake_pyodbc = FakePyodbc()
    service = MssqlToolService(NAMED_ENV, pyodbc_module=fake_pyodbc)

    result = service.test_connection(db="ProjectWorkTracker")

    assert result["ok"] is True
    assert result["db"] == "projectworktracker"
    assert result["server"] == "tracker-host,1433"
    assert result["database"] == "ProjectWorkTrackerDb"
    assert "SERVER=tracker-host,1433;" in fake_pyodbc.connection_strings[0]


def test_service_routes_to_twntaxiad_profile():
    fake_pyodbc = FakePyodbc()
    service = MssqlToolService(NAMED_ENV, pyodbc_module=fake_pyodbc)

    result = service.test_connection(db="TWNTaxiAD")

    assert result["ok"] is True
    assert result["db"] == "twntaxiad"
    assert result["server"] == "taxi-host,1433"
    assert result["database"] == "TWNTaxiADDb"
    assert "SERVER=taxi-host,1433;" in fake_pyodbc.connection_strings[0]


@pytest.mark.parametrize(
    ("selector", "expected_profile", "expected_server"),
    [
        ("GlobalBusiness", "global_business", "analytics,1433"),
        ("TWTaxiAD53", "twntaxiad53", "taxi53-host,1433"),
    ],
)
def test_all_service_tools_route_to_new_profiles(selector, expected_profile, expected_server):
    service = MssqlToolService(NAMED_ENV, pyodbc_module=FakePyodbc())

    connection_result = service.test_connection(db=selector)
    tables_result = service.list_tables(db=selector)
    describe_result = service.describe_table("dbo.Users", db=selector)
    query_result = service.query("SELECT id, name FROM dbo.Users", db=selector)

    assert connection_result["db"] == expected_profile
    assert connection_result["server"] == expected_server
    assert tables_result["db"] == expected_profile
    assert tables_result["tables"][0]["full_name"] == "dbo.Users"
    assert describe_result["db"] == expected_profile
    assert describe_result["table"] == "dbo.Users"
    assert query_result["db"] == expected_profile
    assert query_result["row_count"] == MAX_ROWS


def test_service_routes_named_profile_by_configured_database_name():
    fake_pyodbc = FakePyodbc()
    service = MssqlToolService(NAMED_ENV, pyodbc_module=fake_pyodbc)

    result = service.test_connection(db="TendDb")

    assert result["ok"] is True
    assert result["db"] == "tend"
    assert result["database"] == "TendDb"
    assert "SERVER=tend-host,1433;" in fake_pyodbc.connection_strings[0]


def test_as_tool_response_returns_invalid_profile_error():
    service = MssqlToolService(ENV, pyodbc_module=FakePyodbc())

    result = as_tool_response(service.list_tables, "archive")

    assert result["ok"] is False
    assert result["code"] == "CONFIG_INVALID"


def test_as_tool_response_rejects_retired_secondary_selector():
    service = MssqlToolService(NAMED_ENV, pyodbc_module=FakePyodbc())

    result = as_tool_response(service.list_tables, "secondary")

    assert result["ok"] is False
    assert result["code"] == "CONFIG_INVALID"
    assert result["details"]["db"] == "secondary"
    assert all(value.lower() != "secondary" for value in result["details"]["allowed"])
