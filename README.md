# mssql-pyodbc-mcp

Local stdio MCP server for read-only Microsoft SQL Server access through Python and pyodbc.

## Features

- `test_connection`: validates configuration and checks DB connectivity.
- `list_tables`: lists accessible user tables.
- `describe_table`: returns simple column metadata.
- `query`: executes read-only `SELECT` queries and returns at most 100 rows.

The server supports a required default MSSQL connection plus optional named MSSQL connections. All connections use SQL username/password authentication. Agents can select a connection by passing either the internal profile name or the configured database name from any configured profile.

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

Optional second DB:

- `MSSQL_SECONDARY_SERVER`
- `MSSQL_SECONDARY_DATABASE`
- `MSSQL_SECONDARY_USER`
- `MSSQL_SECONDARY_PASSWORD`
- `MSSQL_SECONDARY_DRIVER=ODBC Driver 18 for SQL Server`
- `MSSQL_SECONDARY_PORT=1433`
- `MSSQL_SECONDARY_TRUST_SERVER_CERTIFICATE=yes`

Optional named DBs:

- `MSSQL_TEND_SERVER`
- `MSSQL_TEND_DATABASE`
- `MSSQL_TEND_USER`
- `MSSQL_TEND_PASSWORD`
- `MSSQL_TEND_DRIVER=ODBC Driver 18 for SQL Server`
- `MSSQL_TEND_PORT=1433`
- `MSSQL_TEND_TRUST_SERVER_CERTIFICATE=yes`
- `MSSQL_PROJECTWORKTRACKER_SERVER`
- `MSSQL_PROJECTWORKTRACKER_DATABASE`
- `MSSQL_PROJECTWORKTRACKER_USER`
- `MSSQL_PROJECTWORKTRACKER_PASSWORD`
- `MSSQL_PROJECTWORKTRACKER_DRIVER=ODBC Driver 18 for SQL Server`
- `MSSQL_PROJECTWORKTRACKER_PORT=1433`
- `MSSQL_PROJECTWORKTRACKER_TRUST_SERVER_CERTIFICATE=yes`
- `MSSQL_TWNTAXIAD_SERVER`
- `MSSQL_TWNTAXIAD_DATABASE`
- `MSSQL_TWNTAXIAD_USER`
- `MSSQL_TWNTAXIAD_PASSWORD`
- `MSSQL_TWNTAXIAD_DRIVER=ODBC Driver 18 for SQL Server`
- `MSSQL_TWNTAXIAD_PORT=1433`
- `MSSQL_TWNTAXIAD_TRUST_SERVER_CERTIFICATE=yes`

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

To enable a second DB, also export:

```bash
export MSSQL_SECONDARY_SERVER=localhost
export MSSQL_SECONDARY_DATABASE=OtherDatabase
export MSSQL_SECONDARY_USER=other_user
export MSSQL_SECONDARY_PASSWORD=other_password
```

To enable a named DB, export its matching group:

```bash
export MSSQL_TEND_SERVER=localhost
export MSSQL_TEND_DATABASE=Tend
export MSSQL_TEND_USER=tend_user
export MSSQL_TEND_PASSWORD=tend_password
```

All tools accept an optional `db` argument. The most natural value is the configured database name:

```json
{"db": "MyDatabase", "sql": "SELECT TOP 10 * FROM dbo.Users"}
{"db": "OtherDatabase", "sql": "SELECT TOP 10 * FROM dbo.Users"}
{"db": "Tend", "sql": "SELECT TOP 10 * FROM dbo.Users"}
```

Selection rules:

- `db="default"` uses `MSSQL_*` variables.
- `db="Tend"` uses `MSSQL_TEND_*` variables.
- `db="ProjectWorkTracker"` uses `MSSQL_PROJECTWORKTRACKER_*` variables.
- `db="TWNTaxiAD"` uses `MSSQL_TWNTAXIAD_*` variables.
- `db="<MSSQL_DATABASE value>"` uses `MSSQL_*` variables.
- `db="<configured database name>"` uses the matching configured profile.
- `db="secondary"` still works for backward compatibility.
- Profile selectors are case-insensitive.
- Omitting `db` uses `default`.

## Live DB Checks

After exporting the environment variables, verify the local setup with:

```bash
python scripts/check_odbc_connection.py
python scripts/check_mcp_tools.py
python scripts/check_mcp_tools.py OtherDatabase
python scripts/check_mcp_tools.py Tend
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
