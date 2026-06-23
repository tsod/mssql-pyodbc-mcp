import pytest

from mssql_pyodbc_mcp.config import DatabaseConfig
from mssql_pyodbc_mcp.errors import ToolError


BASE_ENV = {
    "MSSQL_SERVER": "localhost",
    "MSSQL_DATABASE": "appdb",
    "MSSQL_USER": "sa",
    "MSSQL_PASSWORD": "secret",
}


def test_config_defaults_are_applied():
    config = DatabaseConfig.from_env(BASE_ENV)

    assert config.driver == "ODBC Driver 18 for SQL Server"
    assert config.port == 1433
    assert config.trust_server_certificate == "yes"


def test_missing_required_vars_are_reported_without_password_value():
    with pytest.raises(ToolError) as error:
        DatabaseConfig.from_env({"MSSQL_SERVER": "localhost"})

    payload = error.value.to_dict()
    assert payload["code"] == "CONFIG_MISSING"
    assert "MSSQL_PASSWORD" in payload["details"]["missing"]
    assert "secret" not in str(payload)


def test_invalid_port_is_rejected():
    env = {**BASE_ENV, "MSSQL_PORT": "abc"}

    with pytest.raises(ToolError) as error:
        DatabaseConfig.from_env(env)

    assert error.value.code == "CONFIG_INVALID"


def test_connection_string_includes_expected_driver_and_auth():
    config = DatabaseConfig.from_env({**BASE_ENV, "MSSQL_PORT": "11433", "MSSQL_TRUST_SERVER_CERTIFICATE": "no"})

    conn = config.connection_string()

    assert "DRIVER={ODBC Driver 18 for SQL Server};" in conn
    assert "SERVER=localhost,11433;" in conn
    assert "UID=sa;" in conn
    assert "PWD=secret;" in conn
    assert "Encrypt=no;" in conn
    assert "TrustServerCertificate=no;" in conn
