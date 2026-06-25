# Implementation Plan

## Project
- Name: mssql-pyodbc-mcp
- CR: CR-001
- Branch target: pg/CR-001-multi-db-support

## Goal
- Add a second optional MSSQL DB profile while preserving existing single-DB behavior.

## Design Summary
- Keep `DatabaseConfig` responsible for one concrete DB connection.
- Add profile-aware loading in `config.py`.
- `default` profile uses existing `MSSQL_*` variables.
- `secondary` profile uses `MSSQL_SECONDARY_*` variables.
- Add optional `db` argument to all MCP tools and service methods.
- Resolve selected profile before creating `ConnectionFactory`.
- Return safe `db` metadata in tool responses.

## Environment Variables
- Required default:
  - `MSSQL_SERVER`
  - `MSSQL_DATABASE`
  - `MSSQL_USER`
  - `MSSQL_PASSWORD`
- Optional default:
  - `MSSQL_DRIVER`
  - `MSSQL_PORT`
  - `MSSQL_TRUST_SERVER_CERTIFICATE`
- Optional secondary:
  - `MSSQL_SECONDARY_SERVER`
  - `MSSQL_SECONDARY_DATABASE`
  - `MSSQL_SECONDARY_USER`
  - `MSSQL_SECONDARY_PASSWORD`
  - `MSSQL_SECONDARY_DRIVER`
  - `MSSQL_SECONDARY_PORT`
  - `MSSQL_SECONDARY_TRUST_SERVER_CERTIFICATE`

## Tasks
1. Update config model.
   - Add profile field to `DatabaseConfig`.
   - Add profile env loading for default and secondary.
   - Validate selected profile names.
   - Treat secondary as optional unless selected or partially configured.
2. Update service layer.
   - Add optional `db` parameter to tool service methods.
   - Resolve selected profile and construct `DatabaseClient`.
3. Update DB response metadata.
   - Include safe `db` identity on connection, metadata, and query responses where useful.
4. Update MCP server tool signatures.
   - Add `db: str = "default"` to existing tools.
5. Update scripts and docs.
   - README usage and env variable reference.
   - `scripts/mssql-pyodbc-mcp.env.example`.
   - Optional `db` CLI argument in `scripts/check_mcp_tools.py`.
   - Main specs impacted by this CR.
6. Update tests.
   - Config tests for default profile compatibility.
   - Config tests for secondary profile loading.
   - Invalid profile tests.
   - Missing/partial secondary config tests.
   - Service tests for routing to secondary.
   - Existing tests must keep passing.
7. Verify.
   - `python3 -m pytest`
   - `python3 -m compileall src tests`

## Acceptance Criteria
- `test_connection()` uses default profile and remains backward compatible.
- `test_connection(db="<MSSQL_SECONDARY_DATABASE value>")` uses secondary variables when configured.
- `list_tables`, `describe_table`, and `query` can target `default` or `secondary`.
- Invalid profile names return `CONFIG_INVALID`.
- Selecting unconfigured `secondary` returns `CONFIG_MISSING` without exposing secrets.
- Partial secondary config returns a safe missing-variable error.
- All read-only SQL restrictions and 100-row result limit still apply.
- Docs and env example describe both profiles.

## Ready for PG
- Yes

## Notes
- Cross-database object references inside SQL are not specially parsed in CR-001.
- Future work can generalize profiles to named N-profile configuration if needed.
