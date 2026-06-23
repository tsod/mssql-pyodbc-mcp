# RA Handover

## Requirement Summary

Build a local stdio MCP server in Python that uses pyodbc to connect to one configured Microsoft SQL Server database. The server is intended for Codex and other agents to inspect database metadata and run read-only SQL queries safely.

## Product Goal

Provide a controlled MCP tool for agents to query a specified MSSQL database during development or analysis work, without manually opening a database client.

## Target Users

- Primary user: Developer using Codex to inspect MSSQL data.
- Secondary users: Agent workflows that need database context or read-only query results.

## Core Scenarios

- Agent starts the MCP server locally through stdio.
- Agent verifies the configured DB connection before querying.
- Agent lists available user tables.
- Agent describes a table schema before composing SQL.
- Agent executes a read-only SELECT query and receives structured results.

## Scope

- In Scope:
  - Python MCP server using pyodbc.
  - stdio transport for local Codex/agent usage.
  - Single MSSQL DB connection profile.
  - Environment-variable based DB configuration.
  - SQL account/password authentication.
  - Tools:
    - `test_connection`
    - `list_tables`
    - `describe_table`
    - `query`
  - General SELECT query support, including common query features such as CTE, JOIN, WHERE, GROUP BY, ORDER BY, and subqueries.
  - Maximum query result size of 100 rows.
  - Simple table schema output.
- Out of Scope:
  - Multiple DB profiles.
  - Remote HTTP/SSE MCP hosting.
  - Windows Authentication / trusted connection.
  - Insert, update, delete, or schema-changing operations.
  - UI or web dashboard.
  - Query history persistence.

## Data Elements

- DB connection configuration from environment variables:
  - `MSSQL_SERVER`
  - `MSSQL_DATABASE`
  - `MSSQL_USER`
  - `MSSQL_PASSWORD`
  - `MSSQL_DRIVER`
  - `MSSQL_PORT`
  - `MSSQL_TRUST_SERVER_CERTIFICATE`
- `list_tables` output:
  - table schema/name information sufficient for an agent to identify tables.
- `describe_table` output:
  - `column_name`
  - `data_type`
  - `nullable`
- `query` output:
  - structured rows and column names.

## Business Rules

- Only read-only SQL query behavior is allowed.
- `query` permits arbitrary SQL SELECT statements.
- `INSERT`, `UPDATE`, and `DELETE` must be forbidden.
- DDL and other non-read operations should be treated as disallowed unless explicitly approved in a later requirement.
- `query` must return at most 100 rows.
- Initial release supports only one configured DB.
- The DB account should be expected to use SQL username/password authentication.

## Acceptance Signals

- Codex can start the MCP server through stdio.
- `test_connection` confirms the configured MSSQL DB is reachable.
- `list_tables` returns available user tables.
- `describe_table` returns a simple schema for a selected table.
- `query` executes a valid SELECT and returns at most 100 rows.
- Attempts to use write operations such as INSERT, UPDATE, or DELETE are rejected.
- Missing or invalid environment variables produce clear, agent-readable errors without exposing secrets.

## Constraints

- Runtime: Python.
- DB library preference: pyodbc.
- Database: Microsoft SQL Server.
- MCP transport: stdio.
- Authentication: SQL account/password only.
- Configuration: environment variables.
- Initial deployment target: local developer/agent runtime.

## Content Source / Asset Constraints

- No image, audio, video, document corpus, or other creative content assets are required for this project.
- No licensing constraints were identified for content assets.

## Technical Constraints / Preferences

- Must use Python and pyodbc.
- Must expose MCP-compatible tools for Codex/agent usage.
- Must use stdio for the initial MCP server interface.
- Must support only one DB profile in the first version.
- Environment variables must include:
  - `MSSQL_SERVER`
  - `MSSQL_DATABASE`
  - `MSSQL_USER`
  - `MSSQL_PASSWORD`
  - `MSSQL_DRIVER`
  - `MSSQL_PORT`
  - `MSSQL_TRUST_SERVER_CERTIFICATE`
- Error messages should be useful to agents but must not reveal passwords or sensitive connection string details.

## Assumptions

- `list_tables` should return user tables only, not system tables.
- `describe_table` can be implemented with standard SQL Server metadata views.
- `MSSQL_DRIVER`, `MSSQL_PORT`, and `MSSQL_TRUST_SERVER_CERTIFICATE` may have documented defaults, but the exact defaults should be confirmed during PM/SD planning.
- The database login should ideally have read-only permissions, even though the MCP server also enforces read-only behavior.
- Stored procedures and EXEC-style calls are out of scope for the first version.

## Open Questions

- What default values should be used for `MSSQL_DRIVER`, `MSSQL_PORT`, and `MSSQL_TRUST_SERVER_CERTIFICATE`?
- Should blocked SQL return a standardized MCP error code/message shape?
- Should table names in `describe_table` support schema-qualified input such as `dbo.Users`?
- Should query row limiting be implemented by SQL wrapping, cursor fetch limit, or both?

## Project Name Suggestions

- `mssql-pyodbc-mcp`
- `mssql-query-mcp-server`
- `mcp-mssql-query-tool`

## Confirmed Project Name

- `mssql-pyodbc-mcp`

## Ready for PM

- Yes
