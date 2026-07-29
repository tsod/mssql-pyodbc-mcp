import pytest

from mssql_pyodbc_mcp.config import DatabaseConfig
from mssql_pyodbc_mcp.errors import ToolError


BASE_ENV = {
    "MSSQL_SERVER": "localhost",
    "MSSQL_DATABASE": "appdb",
    "MSSQL_USER": "sa",
    "MSSQL_PASSWORD": "secret",
}

GLOBAL_BUSINESS_ENV = {
    **BASE_ENV,
    "MSSQL_GLOBAL_BUSINESS_SERVER": "analytics",
    "MSSQL_GLOBAL_BUSINESS_DATABASE": "dw",
    "MSSQL_GLOBAL_BUSINESS_USER": "reader",
    "MSSQL_GLOBAL_BUSINESS_PASSWORD": "global-business-secret",
    "MSSQL_GLOBAL_BUSINESS_DRIVER": "ODBC Driver 17 for SQL Server",
    "MSSQL_GLOBAL_BUSINESS_PORT": "11433",
    "MSSQL_GLOBAL_BUSINESS_TRUST_SERVER_CERTIFICATE": "no",
}

NAMED_ENV = {
    **GLOBAL_BUSINESS_ENV,
    "MSSQL_TEND_SERVER": "tend-host",
    "MSSQL_TEND_DATABASE": "TendDb",
    "MSSQL_TEND_USER": "tend-user",
    "MSSQL_TEND_PASSWORD": "tend-secret",
    "MSSQL_TEND_PORT": "21433",
    "MSSQL_PROJECTWORKTRACKER_SERVER": "tracker-host",
    "MSSQL_PROJECTWORKTRACKER_DATABASE": "ProjectWorkTrackerDb",
    "MSSQL_PROJECTWORKTRACKER_USER": "tracker-user",
    "MSSQL_PROJECTWORKTRACKER_PASSWORD": "tracker-secret",
    "MSSQL_PROJECTWORKTRACKER_TRUST_SERVER_CERTIFICATE": "false",
    "MSSQL_TWNTAXIAD_SERVER": "taxi-host",
    "MSSQL_TWNTAXIAD_DATABASE": "TWNTaxiADDb",
    "MSSQL_TWNTAXIAD_USER": "taxi-user",
    "MSSQL_TWNTAXIAD_PASSWORD": "taxi-secret",
    "MSSQL_TWNTAXIAD_DRIVER": "ODBC Driver 17 for SQL Server",
    "MSSQL_TWNTAXIAD53_SERVER": "taxi53-host",
    "MSSQL_TWNTAXIAD53_DATABASE": "TWTaxiAD53Db",
    "MSSQL_TWNTAXIAD53_USER": "taxi53-user",
    "MSSQL_TWNTAXIAD53_PASSWORD": "taxi53-secret",
    "MSSQL_TWNTAXIAD53_DRIVER": "ODBC Driver 18 for SQL Server",
    "MSSQL_TWNTAXIAD53_PORT": "31433",
    "MSSQL_TWNTAXIAD53_TRUST_SERVER_CERTIFICATE": "true",
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


def test_global_business_profile_uses_prefixed_environment_variables():
    config = DatabaseConfig.from_env(GLOBAL_BUSINESS_ENV, "GlobalBusiness")

    assert config.profile == "global_business"
    assert config.server == "analytics"
    assert config.database == "dw"
    assert config.user == "reader"
    assert config.driver == "ODBC Driver 17 for SQL Server"
    assert config.port == 11433
    assert config.trust_server_certificate == "no"
    assert "SERVER=analytics,11433;" in config.connection_string()
    assert "PWD=global-business-secret;" in config.connection_string()


def test_default_database_name_can_select_default_profile():
    config = DatabaseConfig.from_env(GLOBAL_BUSINESS_ENV, "appdb")

    assert config.profile == "default"
    assert config.server == "localhost"
    assert config.database == "appdb"


def test_global_business_database_name_can_select_profile():
    config = DatabaseConfig.from_env(GLOBAL_BUSINESS_ENV, "dw")

    assert config.profile == "global_business"
    assert config.server == "analytics"
    assert config.database == "dw"
    assert config.user == "reader"


def test_tend_profile_uses_prefixed_environment_variables():
    config = DatabaseConfig.from_env(NAMED_ENV, "Tend")

    assert config.profile == "tend"
    assert config.server == "tend-host"
    assert config.database == "TendDb"
    assert config.user == "tend-user"
    assert config.port == 21433
    assert "SERVER=tend-host,21433;" in config.connection_string()
    assert "PWD=tend-secret;" in config.connection_string()


def test_projectworktracker_profile_uses_prefixed_environment_variables():
    config = DatabaseConfig.from_env(NAMED_ENV, "ProjectWorkTracker")

    assert config.profile == "projectworktracker"
    assert config.server == "tracker-host"
    assert config.database == "ProjectWorkTrackerDb"
    assert config.user == "tracker-user"
    assert config.trust_server_certificate == "no"


def test_twntaxiad_profile_uses_prefixed_environment_variables():
    config = DatabaseConfig.from_env(NAMED_ENV, "TWNTaxiAD")

    assert config.profile == "twntaxiad"
    assert config.server == "taxi-host"
    assert config.database == "TWNTaxiADDb"
    assert config.user == "taxi-user"
    assert config.driver == "ODBC Driver 17 for SQL Server"


def test_twtaxiad53_profile_uses_prefixed_environment_variables():
    config = DatabaseConfig.from_env(NAMED_ENV, "TWTaxiAD53")

    assert config.profile == "twntaxiad53"
    assert config.server == "taxi53-host"
    assert config.database == "TWTaxiAD53Db"
    assert config.user == "taxi53-user"
    assert config.driver == "ODBC Driver 18 for SQL Server"
    assert config.port == 31433
    assert config.trust_server_certificate == "yes"


def test_254global_profile_uses_prefixed_environment_variables():
    env = {
        **BASE_ENV,
        "MSSQL_254GLOBAL_SERVER": "global-host",
        "MSSQL_254GLOBAL_DATABASE": "254global",
        "MSSQL_254GLOBAL_USER": "global-user",
        "MSSQL_254GLOBAL_PASSWORD": "global-secret",
    }

    config = DatabaseConfig.from_env(env, "254global")

    assert config.profile == "254global"
    assert config.server == "global-host"
    assert config.database == "254global"
    assert config.user == "global-user"


def test_named_profile_selectors_are_case_insensitive():
    config = DatabaseConfig.from_env(NAMED_ENV, "tend")

    assert config.profile == "tend"
    assert config.database == "TendDb"


@pytest.mark.parametrize(
    ("selector", "expected_profile"),
    [
        ("GLOBALBUSINESS", "global_business"),
        ("global_business", "global_business"),
        ("twtaxiad53", "twntaxiad53"),
        ("TWTAXIAD53", "twntaxiad53"),
    ],
)
def test_new_profile_selectors_are_case_insensitive(selector, expected_profile):
    config = DatabaseConfig.from_env(NAMED_ENV, selector)

    assert config.profile == expected_profile


def test_named_profile_database_name_can_select_profile():
    config = DatabaseConfig.from_env(NAMED_ENV, "ProjectWorkTrackerDb")

    assert config.profile == "projectworktracker"
    assert config.server == "tracker-host"


def test_twtaxiad53_database_name_can_select_profile():
    config = DatabaseConfig.from_env(NAMED_ENV, "TWTaxiAD53Db")

    assert config.profile == "twntaxiad53"
    assert config.server == "taxi53-host"


def test_blank_profile_defaults_to_default():
    config = DatabaseConfig.from_env(BASE_ENV, "")

    assert config.profile == "default"


def test_unknown_profile_is_rejected():
    with pytest.raises(ToolError) as error:
        DatabaseConfig.from_env(BASE_ENV, "archive")

    payload = error.value.to_dict()
    assert payload["code"] == "CONFIG_INVALID"
    assert payload["details"]["allowed"] == [
        "default",
        "GlobalBusiness",
        "Tend",
        "ProjectWorkTracker",
        "TWNTaxiAD",
        "254global",
        "TWTaxiAD53",
        "appdb",
    ]


def test_missing_global_business_profile_reports_prefixed_keys_without_secret_values():
    with pytest.raises(ToolError) as error:
        DatabaseConfig.from_env(BASE_ENV, "GlobalBusiness")

    payload = error.value.to_dict()
    assert payload["code"] == "CONFIG_MISSING"
    assert payload["details"]["db"] == "global_business"
    assert "MSSQL_GLOBAL_BUSINESS_PASSWORD" in payload["details"]["missing"]
    assert "secret" not in str(payload)


def test_retired_secondary_selector_is_rejected_without_database_name_fallback():
    env = {
        **GLOBAL_BUSINESS_ENV,
        "MSSQL_GLOBAL_BUSINESS_DATABASE": "secondary",
    }

    with pytest.raises(ToolError) as error:
        DatabaseConfig.from_env(env, "secondary")

    payload = error.value.to_dict()
    assert payload["code"] == "CONFIG_INVALID"
    assert payload["details"]["db"] == "secondary"
    assert all(value.lower() != "secondary" for value in payload["details"]["allowed"])


def test_old_secondary_environment_does_not_configure_global_business():
    old_env = {
        **BASE_ENV,
        "MSSQL_SECONDARY_SERVER": "old-host",
        "MSSQL_SECONDARY_DATABASE": "old-db",
        "MSSQL_SECONDARY_USER": "old-user",
        "MSSQL_SECONDARY_PASSWORD": "old-secret",
    }

    with pytest.raises(ToolError) as error:
        DatabaseConfig.from_env(old_env, "GlobalBusiness")

    payload = error.value.to_dict()
    assert payload["code"] == "CONFIG_MISSING"
    assert "MSSQL_GLOBAL_BUSINESS_SERVER" in payload["details"]["missing"]
    assert "old-secret" not in str(payload)


def test_missing_named_profile_reports_prefixed_keys_without_secret_values():
    with pytest.raises(ToolError) as error:
        DatabaseConfig.from_env(BASE_ENV, "Tend")

    payload = error.value.to_dict()
    assert payload["code"] == "CONFIG_MISSING"
    assert payload["details"]["db"] == "tend"
    assert "MSSQL_TEND_PASSWORD" in payload["details"]["missing"]
    assert "secret" not in str(payload)


def test_partial_named_profile_reports_missing_prefixed_keys():
    with pytest.raises(ToolError) as error:
        DatabaseConfig.from_env({**BASE_ENV, "MSSQL_TWNTAXIAD_SERVER": "taxi-host"}, "TWNTaxiAD")

    payload = error.value.to_dict()
    assert payload["code"] == "CONFIG_MISSING"
    assert payload["details"]["db"] == "twntaxiad"
    assert "MSSQL_TWNTAXIAD_DATABASE" in payload["details"]["missing"]
    assert "MSSQL_TWNTAXIAD_PASSWORD" in payload["details"]["missing"]


def test_partial_twtaxiad53_profile_reports_new_prefixed_keys_only_when_selected():
    env = {
        **BASE_ENV,
        "MSSQL_TWNTAXIAD53_SERVER": "taxi53-host",
        "MSSQL_TWNTAXIAD53_DATABASE": "",
        "MSSQL_TWNTAXIAD53_USER": "",
        "MSSQL_TWNTAXIAD53_PASSWORD": "",
        "MSSQL_TWNTAXIAD53_DRIVER": "",
        "MSSQL_TWNTAXIAD53_PORT": "",
        "MSSQL_TWNTAXIAD53_TRUST_SERVER_CERTIFICATE": "",
    }

    assert DatabaseConfig.from_env(env).profile == "default"

    with pytest.raises(ToolError) as error:
        DatabaseConfig.from_env(env, "TWTaxiAD53")

    payload = error.value.to_dict()
    assert payload["code"] == "CONFIG_MISSING"
    assert payload["details"]["db"] == "twntaxiad53"
    assert "MSSQL_TWNTAXIAD53_DATABASE" in payload["details"]["missing"]
    assert "MSSQL_TWNTAXIAD53_PASSWORD" in payload["details"]["missing"]
    assert all(not key.startswith("MSSQL_TWNTAXIAD_") for key in payload["details"]["missing"])


def test_twntaxiad_and_twtaxiad53_profiles_remain_independent():
    original = DatabaseConfig.from_env(NAMED_ENV, "TWNTaxiAD")
    added = DatabaseConfig.from_env(NAMED_ENV, "TWTaxiAD53")

    assert original.profile == "twntaxiad"
    assert original.server == "taxi-host"
    assert added.profile == "twntaxiad53"
    assert added.server == "taxi53-host"
