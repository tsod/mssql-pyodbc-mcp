from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .errors import ToolError


DEFAULT_DRIVER = "ODBC Driver 18 for SQL Server"
DEFAULT_PORT = 1433
DEFAULT_TRUST_SERVER_CERTIFICATE = "yes"
REQUIRED_ENV_VARS = ("MSSQL_SERVER", "MSSQL_DATABASE", "MSSQL_USER", "MSSQL_PASSWORD")


@dataclass(frozen=True)
class DatabaseConfig:
    server: str
    database: str
    user: str
    password: str
    driver: str = DEFAULT_DRIVER
    port: int = DEFAULT_PORT
    trust_server_certificate: str = DEFAULT_TRUST_SERVER_CERTIFICATE

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "DatabaseConfig":
        missing = [key for key in REQUIRED_ENV_VARS if not env.get(key, "").strip()]
        if missing:
            raise ToolError(
                "CONFIG_MISSING",
                "Missing required MSSQL environment variables.",
                {"missing": missing},
            )

        port_text = env.get("MSSQL_PORT", str(DEFAULT_PORT)).strip() or str(DEFAULT_PORT)
        try:
            port = int(port_text)
        except ValueError as exc:
            raise ToolError("CONFIG_INVALID", "MSSQL_PORT must be an integer.", {"key": "MSSQL_PORT"}) from exc
        if not 1 <= port <= 65535:
            raise ToolError("CONFIG_INVALID", "MSSQL_PORT must be between 1 and 65535.", {"key": "MSSQL_PORT"})

        trust = env.get("MSSQL_TRUST_SERVER_CERTIFICATE", DEFAULT_TRUST_SERVER_CERTIFICATE).strip().lower()
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
                "MSSQL_TRUST_SERVER_CERTIFICATE must be yes/no or true/false.",
                {"key": "MSSQL_TRUST_SERVER_CERTIFICATE"},
            )

        return cls(
            server=env["MSSQL_SERVER"].strip(),
            database=env["MSSQL_DATABASE"].strip(),
            user=env["MSSQL_USER"].strip(),
            password=env["MSSQL_PASSWORD"],
            driver=env.get("MSSQL_DRIVER", DEFAULT_DRIVER).strip() or DEFAULT_DRIVER,
            port=port,
            trust_server_certificate=trust_map[trust],
        )

    def safe_identity(self) -> dict[str, str]:
        return {"server": f"{self.server},{self.port}", "database": self.database}

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
