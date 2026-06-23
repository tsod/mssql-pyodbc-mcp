import pytest

from mssql_pyodbc_mcp.config import DatabaseConfig
from mssql_pyodbc_mcp.errors import ToolError


BASE_ENV = {
    "MSSQL_SERVER": "localhost",
    "MSSQL_DATABASE": "appdb",
    "MSSQL_USER": "sa",
    "MSSQL_PASSWORD": "secret",
}

SECONDARY_ENV = {
    **BASE_ENV,
    "MSSQL_SECONDARY_SERVER": "analytics",
    "MSSQL_SECONDARY_DATABASE": "dw",
    "MSSQL_SECONDARY_USER": "reader",
    "MSSQL_SECONDARY_PASSWORD": "secondary-secret",
    "MSSQL_SECONDARY_PORT": "11433",
    "MSSQL_SECONDARY_TRUST_SERVER_CERTIFICATE": "no",
}


def test_config_defaults_are_applied():
    config = DatabaseConfig.from_env(BASE_ENV)

    assert config.profile == "default"
    assert config.driver == "ODBC Driver 18 for SQL Server"
    assert config.port == 1433
    assert config.trust_server_certificate == "yes"


def test_missing_required_vars_are_reported_without_password_value():
    with pytest.raises(ToolError) as error:
        DatabaseConfig.from_env({"MSSQL_SERVER": "localhost"})

    payload = error.value.to_dict()
    assert payload["code"] == "CONFIG_MISSING"
    assert payload["details"]["db"] == "default"
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


def test_secondary_profile_uses_prefixed_environment_variables():
    config = DatabaseConfig.from_env(SECONDARY_ENV, "secondary")

    assert config.profile == "secondary"
    assert config.server == "analytics"
    assert config.database == "dw"
    assert config.user == "reader"
    assert config.port == 11433
    assert config.trust_server_certificate == "no"
    assert "SERVER=analytics,11433;" in config.connection_string()
    assert "PWD=secondary-secret;" in config.connection_string()


def test_default_database_name_can_select_default_profile():
    config = DatabaseConfig.from_env(SECONDARY_ENV, "appdb")

    assert config.profile == "default"
    assert config.server == "localhost"
    assert config.database == "appdb"


def test_secondary_database_name_can_select_secondary_profile():
    config = DatabaseConfig.from_env(SECONDARY_ENV, "dw")

    assert config.profile == "secondary"
    assert config.server == "analytics"
    assert config.database == "dw"
    assert config.user == "reader"


def test_blank_profile_defaults_to_default():
    config = DatabaseConfig.from_env(BASE_ENV, "")

    assert config.profile == "default"


def test_unknown_profile_is_rejected():
    with pytest.raises(ToolError) as error:
        DatabaseConfig.from_env(BASE_ENV, "archive")

    payload = error.value.to_dict()
    assert payload["code"] == "CONFIG_INVALID"
    assert payload["details"]["allowed"] == ["default", "secondary", "appdb"]


def test_missing_secondary_profile_reports_prefixed_keys_without_secret_values():
    with pytest.raises(ToolError) as error:
        DatabaseConfig.from_env(BASE_ENV, "secondary")

    payload = error.value.to_dict()
    assert payload["code"] == "CONFIG_MISSING"
    assert payload["details"]["db"] == "secondary"
    assert "MSSQL_SECONDARY_PASSWORD" in payload["details"]["missing"]
    assert "secret" not in str(payload)
