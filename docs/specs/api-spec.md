# API Spec

## Overview

This project exposes MCP tools over stdio. It does not expose HTTP endpoints. Tool inputs and outputs should be JSON-serializable and optimized for agent consumption.

## Authentication / Authorization

- MCP layer: no separate user login in the first release.
- Database layer: SQL Server username/password from environment variables for the selected DB profile.
- Authorization is delegated to the configured SQL Server account, with application-level read-only checks as an additional guard.

## Tools

### `test_connection`

- Purpose: Validate environment configuration and confirm the MSSQL DB can be reached.
- Input:
  - `db`: optional string, defaults to `default`; allowed values are `default` and `secondary`.
- Output:
  - `ok`: boolean
  - `db`: string
  - `server`: string, redacted/safe server identifier
  - `database`: string
  - `message`: string
- Validation Rules:
  - Required environment variables must be present.
  - Password must never be returned.
  - Connection errors must be summarized without exposing the full connection string.

### `list_tables`

- Purpose: Return available user tables.
- Input:
  - `db`: optional string, defaults to `default`; allowed values are `default` and `secondary`.
- Output:
  - `db`: string
  - `server`: string
  - `database`: string
  - `tables`: array of objects
    - `schema`: string
    - `name`: string
    - `full_name`: string, for example `dbo.Users`
- Validation Rules:
  - Exclude system tables.
  - Return an empty list if no accessible user tables exist.

### `describe_table`

- Purpose: Return simple schema metadata for one table.
- Input:
  - `table_name`: string, preferably schema-qualified such as `dbo.Users`
  - `db`: optional string, defaults to `default`; allowed values are `default` and `secondary`.
- Output:
  - `db`: string
  - `server`: string
  - `database`: string
  - `table`: string
  - `columns`: array of objects
    - `column_name`: string
    - `data_type`: string
    - `nullable`: boolean
- Validation Rules:
  - `table_name` is required.
  - Schema-qualified input should be supported.
  - Unknown table returns a safe not-found error or an empty column list with a clear message.
  - Ambiguous unqualified table names should return an ambiguity error if multiple schemas match.

### `query`

- Purpose: Execute a read-only SELECT query and return structured results.
- Input:
  - `sql`: string
  - `db`: optional string, defaults to `default`; allowed values are `default` and `secondary`.
- Output:
  - `db`: string
  - `server`: string
  - `database`: string
  - `columns`: array of strings
  - `rows`: array of objects keyed by column name
  - `row_count`: integer
  - `truncated`: boolean
  - `max_rows`: integer, always 100 in the first release
- Validation Rules:
  - `sql` is required and cannot be empty.
  - General SELECT syntax is allowed, including CTEs.
  - Write, DDL, administrative, EXEC, and multi-statement patterns must be rejected.
  - At most 100 rows are returned.
  - Values must be converted to JSON-serializable forms.

## Error Cases

- `CONFIG_MISSING`: required environment variable is missing.
- `CONFIG_INVALID`: environment variable is present but invalid, or an unknown DB profile is selected.
- `CONNECTION_FAILED`: DB connection attempt failed.
- `SQL_REJECTED`: SQL is not allowed by read-only policy.
- `TABLE_NOT_FOUND`: requested table cannot be found.
- `TABLE_AMBIGUOUS`: unqualified table name matches multiple schemas.
- `QUERY_FAILED`: DB rejected the query or execution failed.
- `SERIALIZATION_FAILED`: query result contains an unsupported value shape.

## Environment Variables

- `MSSQL_SERVER`: SQL Server hostname or address.
- `MSSQL_DATABASE`: target database name.
- `MSSQL_USER`: SQL login username.
- `MSSQL_PASSWORD`: SQL login password.
- `MSSQL_DRIVER`: ODBC driver name.
- `MSSQL_PORT`: SQL Server port.
- `MSSQL_TRUST_SERVER_CERTIFICATE`: whether to trust server certificate.
- `MSSQL_SECONDARY_SERVER`: optional secondary SQL Server hostname or address.
- `MSSQL_SECONDARY_DATABASE`: optional secondary database name.
- `MSSQL_SECONDARY_USER`: optional secondary SQL login username.
- `MSSQL_SECONDARY_PASSWORD`: optional secondary SQL login password.
- `MSSQL_SECONDARY_DRIVER`: optional secondary ODBC driver name.
- `MSSQL_SECONDARY_PORT`: optional secondary SQL Server port.
- `MSSQL_SECONDARY_TRUST_SERVER_CERTIFICATE`: optional secondary trust server certificate flag.

## Notes

- Defaults:
  - `MSSQL_PORT`: `1433`
  - `MSSQL_TRUST_SERVER_CERTIFICATE`: `yes`
  - `MSSQL_DRIVER`: `ODBC Driver 18 for SQL Server`
