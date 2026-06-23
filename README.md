# mssql-pyodbc-mcp

Local stdio MCP server for read-only Microsoft SQL Server access through Python and pyodbc.

## Features

- `test_connection`: validates configuration and checks DB connectivity.
- `list_tables`: lists accessible user tables.
- `describe_table`: returns simple column metadata.
- `query`: executes read-only `SELECT` queries and returns at most 100 rows.

The server supports a required `default` MSSQL profile and an optional `secondary` MSSQL profile. Both profiles use SQL username/password authentication.

## Environment Variables

Required:

- `MSSQL_SERVER`
- `MSSQL_DATABASE`
- `MSSQL_USER`
- `MSSQL_PASSWORD`

Optional defaults:

- `MSSQL_DRIVER=ODBC Driver 18 for SQL Server`
- `MSSQL_PORT=1433`
- `MSSQL_TRUST_SERVER_CERTIFICATE=yes`

Optional secondary profile:

- `MSSQL_SECONDARY_SERVER`
- `MSSQL_SECONDARY_DATABASE`
- `MSSQL_SECONDARY_USER`
- `MSSQL_SECONDARY_PASSWORD`
- `MSSQL_SECONDARY_DRIVER=ODBC Driver 18 for SQL Server`
- `MSSQL_SECONDARY_PORT=1433`
- `MSSQL_SECONDARY_TRUST_SERVER_CERTIFICATE=yes`

The implementation sets `Encrypt=no` and passes `TrustServerCertificate` from the environment. For production-like environments, use a properly trusted server certificate and tighten encryption settings before exposing the server beyond local agent usage.

Some older SQL Server instances only support legacy TLS settings. If pyodbc fails with `unsupported protocol`, run the MCP server with:

```bash
export OPENSSL_CONF="$PWD/scripts/openssl-legacy.cnf"
```

## Install

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

You also need a Microsoft SQL Server ODBC driver installed on the host, such as ODBC Driver 18 for SQL Server.

## Run

```bash
export MSSQL_SERVER=localhost
export MSSQL_DATABASE=MyDatabase
export MSSQL_USER=my_user
export MSSQL_PASSWORD=my_password
export MSSQL_DRIVER="ODBC Driver 18 for SQL Server"
export MSSQL_PORT=1433
export MSSQL_TRUST_SERVER_CERTIFICATE=yes
export OPENSSL_CONF="$PWD/scripts/openssl-legacy.cnf"

mssql-pyodbc-mcp
```

To enable a second profile, also export:

```bash
export MSSQL_SECONDARY_SERVER=localhost
export MSSQL_SECONDARY_DATABASE=OtherDatabase
export MSSQL_SECONDARY_USER=other_user
export MSSQL_SECONDARY_PASSWORD=other_password
```

All tools accept an optional `db` argument:

- `db="default"` uses `MSSQL_*` variables.
- `db="secondary"` uses `MSSQL_SECONDARY_*` variables.
- Omitting `db` uses `default`.

## Live DB Checks

After exporting the environment variables, verify the local setup with:

```bash
python scripts/check_odbc_connection.py
python scripts/check_mcp_tools.py
python scripts/check_mcp_tools.py secondary
```

## Codex MCP Example

Configure your MCP client to run the command:

```bash
mssql-pyodbc-mcp
```

Pass the environment variables through your MCP client configuration or shell environment.

## Safety Notes

- The `query` tool accepts general `SELECT` and CTE-style read queries.
- Mutating, schema-changing, administrative, `EXEC`, and multi-statement SQL are rejected by policy.
- Query results are limited to 100 rows.
- Use a read-only SQL Server account whenever possible.
- Passwords and full connection strings are not returned in tool responses.

## Tests

```bash
pytest
```

The unit tests do not require a live MSSQL instance.
