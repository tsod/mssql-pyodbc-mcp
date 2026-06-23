#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${MSSQL_PYODBC_MCP_ENV_FILE:-$HOME/.config/mssql-pyodbc-mcp/env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing MSSQL MCP env file: $ENV_FILE" >&2
  echo "Create it with MSSQL_SERVER, MSSQL_DATABASE, MSSQL_USER, MSSQL_PASSWORD, and related settings." >&2
  exit 1
fi

set -a
# shellcheck source=/dev/null
. "$ENV_FILE"
set +a

exec /mnt/d/AIProject/Workspaces/mssql-pyodbc-mcp/.venv/bin/mssql-pyodbc-mcp
