from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from .config import PROFILE_DEFAULT, DatabaseConfig
from .db import ConnectionFactory, DatabaseClient
from .errors import ToolError
from .sql_policy import validate_read_only_sql


class MssqlToolService:
    def __init__(self, env: Mapping[str, str] | None = None, pyodbc_module: Any | None = None):
        self.env = env if env is not None else os.environ
        self.pyodbc_module = pyodbc_module

    def test_connection(self, db: str = PROFILE_DEFAULT) -> dict[str, Any]:
        return self._client(db).test_connection()

    def list_tables(self, db: str = PROFILE_DEFAULT) -> dict[str, Any]:
        return self._client(db).list_tables()

    def describe_table(self, table_name: str, db: str = PROFILE_DEFAULT) -> dict[str, Any]:
        return self._client(db).describe_table(table_name)

    def query(self, sql: str, db: str = PROFILE_DEFAULT) -> dict[str, Any]:
        safe_sql = validate_read_only_sql(sql)
        return self._client(db).execute_query(safe_sql)

    def _client(self, db: str = PROFILE_DEFAULT) -> DatabaseClient:
        config = DatabaseConfig.from_env(self.env, db)
        return DatabaseClient(ConnectionFactory(config, pyodbc_module=self.pyodbc_module))


def as_tool_response(operation: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        return operation(*args, **kwargs)
    except ToolError as exc:
        return exc.to_dict()
