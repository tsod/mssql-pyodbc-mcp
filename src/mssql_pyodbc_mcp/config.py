from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .errors import ToolError


DEFAULT_DRIVER = "ODBC Driver 18 for SQL Server"
DEFAULT_PORT = 1433
DEFAULT_TRUST_SERVER_CERTIFICATE = "yes"
PROFILE_DEFAULT = "default"
PROFILE_GLOBAL_BUSINESS = "global_business"
PROFILE_TEND = "tend"
PROFILE_PROJECTWORKTRACKER = "projectworktracker"
PROFILE_TWNTAXIAD = "twntaxiad"
PROFILE_254GLOBAL = "254global"
PROFILE_TWNTAXIAD53 = "twntaxiad53"
RETIRED_DB_SELECTORS = frozenset({"secondary"})
REQUIRED_ENV_VARS = ("MSSQL_SERVER", "MSSQL_DATABASE", "MSSQL_USER", "MSSQL_PASSWORD")


@dataclass(frozen=True)
class DatabaseProfileDefinition:
    profile: str
    display_name: str
    env_prefix: str
    required: bool = False


PROFILE_DEFINITIONS = (
    DatabaseProfileDefinition(PROFILE_DEFAULT, "default", "MSSQL", required=True),
    DatabaseProfileDefinition(PROFILE_GLOBAL_BUSINESS, "GlobalBusiness", "MSSQL_GLOBAL_BUSINESS"),
    DatabaseProfileDefinition(PROFILE_TEND, "Tend", "MSSQL_TEND"),
    DatabaseProfileDefinition(PROFILE_PROJECTWORKTRACKER, "ProjectWorkTracker", "MSSQL_PROJECTWORKTRACKER"),
    DatabaseProfileDefinition(PROFILE_TWNTAXIAD, "TWNTaxiAD", "MSSQL_TWNTAXIAD"),
    DatabaseProfileDefinition(PROFILE_254GLOBAL, "254global", "MSSQL_254GLOBAL"),
    DatabaseProfileDefinition(PROFILE_TWNTAXIAD53, "TWTaxiAD53", "MSSQL_TWNTAXIAD53"),
)
ALLOWED_PROFILES = tuple(definition.profile for definition in PROFILE_DEFINITIONS)
PROFILE_DEFINITIONS_BY_ID = {definition.profile: definition for definition in PROFILE_DEFINITIONS}
PROFILE_IDS_BY_SELECTOR = {
    selector.lower(): definition.profile
    for definition in PROFILE_DEFINITIONS
    for selector in (definition.profile, definition.display_name)
}


@dataclass(frozen=True)
class DatabaseConfig:
    server: str
    database: str
    user: str
    password: str
    profile: str = PROFILE_DEFAULT
    driver: str = DEFAULT_DRIVER
    port: int = DEFAULT_PORT
    trust_server_certificate: str = DEFAULT_TRUST_SERVER_CERTIFICATE

    @classmethod
    def from_env(cls, env: Mapping[str, str], profile: str = PROFILE_DEFAULT) -> "DatabaseConfig":
        profile = resolve_profile(env, profile)
        missing = [env_key(profile, key) for key in REQUIRED_ENV_VARS if not env.get(env_key(profile, key), "").strip()]
        if missing:
            raise ToolError(
                "CONFIG_MISSING",
                "Missing required MSSQL environment variables.",
                {"db": profile, "missing": missing},
            )

        port_key = env_key(profile, "MSSQL_PORT")
        port_text = env.get(port_key, str(DEFAULT_PORT)).strip() or str(DEFAULT_PORT)
        try:
            port = int(port_text)
        except ValueError as exc:
            raise ToolError("CONFIG_INVALID", f"{port_key} must be an integer.", {"db": profile, "key": port_key}) from exc
        if not 1 <= port <= 65535:
            raise ToolError(
                "CONFIG_INVALID",
                f"{port_key} must be between 1 and 65535.",
                {"db": profile, "key": port_key},
            )

        trust_key = env_key(profile, "MSSQL_TRUST_SERVER_CERTIFICATE")
        trust = env.get(trust_key, DEFAULT_TRUST_SERVER_CERTIFICATE).strip().lower()
        trust_map = {
            "1": "yes",
            "true": "yes",
            "yes": "yes",
            "y": "yes",
            "0": "no",
            "false": "no",
            "no": "no",
            "n": "no",
        }
        if trust not in trust_map:
            raise ToolError(
                "CONFIG_INVALID",
                f"{trust_key} must be yes/no or true/false.",
                {"db": profile, "key": trust_key},
            )

        driver_key = env_key(profile, "MSSQL_DRIVER")
        return cls(
            profile=profile,
            server=env[env_key(profile, "MSSQL_SERVER")].strip(),
            database=env[env_key(profile, "MSSQL_DATABASE")].strip(),
            user=env[env_key(profile, "MSSQL_USER")].strip(),
            password=env[env_key(profile, "MSSQL_PASSWORD")],
            driver=env.get(driver_key, DEFAULT_DRIVER).strip() or DEFAULT_DRIVER,
            port=port,
            trust_server_certificate=trust_map[trust],
        )

    def safe_identity(self) -> dict[str, str]:
        return {"db": self.profile, "server": f"{self.server},{self.port}", "database": self.database}

    def connection_string(self) -> str:
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.user};"
            f"PWD={self.password};"
            "Encrypt=no;"
            f"TrustServerCertificate={self.trust_server_certificate};"
        )


def resolve_profile(env: Mapping[str, str], profile: str | None) -> str:
    if profile is None or not profile.strip():
        return PROFILE_DEFAULT

    normalized = profile.strip().lower()
    if normalized in RETIRED_DB_SELECTORS:
        raise ToolError(
            "CONFIG_INVALID",
            "Unknown MSSQL DB selector.",
            {"db": normalized, "allowed": allowed_db_values(env)},
        )

    matched_selector = PROFILE_IDS_BY_SELECTOR.get(normalized)
    if matched_selector is None:
        matched_profile = match_database_name(env, normalized)
        if matched_profile is not None:
            return matched_profile

        raise ToolError(
            "CONFIG_INVALID",
            "Unknown MSSQL DB selector.",
            {"db": normalized, "allowed": allowed_db_values(env)},
        )
    return matched_selector


def match_database_name(env: Mapping[str, str], database_name: str) -> str | None:
    for profile in ALLOWED_PROFILES:
        configured_database = env.get(env_key(profile, "MSSQL_DATABASE"), "").strip().lower()
        if configured_database and configured_database == database_name:
            return profile
    return None


def allowed_db_values(env: Mapping[str, str]) -> list[str]:
    values = [definition.display_name for definition in PROFILE_DEFINITIONS]
    for profile in ALLOWED_PROFILES:
        database = env.get(env_key(profile, "MSSQL_DATABASE"), "").strip()
        if database.lower() in RETIRED_DB_SELECTORS:
            continue
        if database and database.lower() not in {value.lower() for value in values}:
            values.append(database)
    return values


def env_key(profile: str, key: str) -> str:
    definition = PROFILE_DEFINITIONS_BY_ID[profile]
    if definition.profile == PROFILE_DEFAULT:
        return key
    return key.replace("MSSQL", definition.env_prefix, 1)
