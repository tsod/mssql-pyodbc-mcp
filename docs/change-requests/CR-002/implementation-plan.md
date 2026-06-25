# Implementation Plan

## Project
- Name: mssql-pyodbc-mcp
- CR: CR-002
- Branch target: pg/CR-002-named-db-profiles

## Goal
- Add three optional named MSSQL DB profiles while preserving existing default and secondary behavior.

## Design Summary
- Keep MCP tool interfaces stable.
- Keep `DatabaseConfig` as the single selected connection model.
- Replace the current two-profile-only env key mapping with fixed profile metadata.
- Supported profiles:
  - `default`: required, `MSSQL_*`
  - `secondary`: optional, `MSSQL_SECONDARY_*`
  - `tend`: optional, `MSSQL_TEND_*`
  - `projectworktracker`: optional, `MSSQL_PROJECTWORKTRACKER_*`
  - `twntaxiad`: optional, `MSSQL_TWNTAXIAD_*`
- Direct selectors should be case-insensitive and documented with display values:
  - `Tend`
  - `ProjectWorkTracker`
  - `TWNTaxiAD`
- Configured database-name selection should work for all configured profiles.

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
- Optional Tend:
  - `MSSQL_TEND_SERVER`
  - `MSSQL_TEND_DATABASE`
  - `MSSQL_TEND_USER`
  - `MSSQL_TEND_PASSWORD`
  - `MSSQL_TEND_DRIVER`
  - `MSSQL_TEND_PORT`
  - `MSSQL_TEND_TRUST_SERVER_CERTIFICATE`
- Optional ProjectWorkTracker:
  - `MSSQL_PROJECTWORKTRACKER_SERVER`
  - `MSSQL_PROJECTWORKTRACKER_DATABASE`
  - `MSSQL_PROJECTWORKTRACKER_USER`
  - `MSSQL_PROJECTWORKTRACKER_PASSWORD`
  - `MSSQL_PROJECTWORKTRACKER_DRIVER`
  - `MSSQL_PROJECTWORKTRACKER_PORT`
  - `MSSQL_PROJECTWORKTRACKER_TRUST_SERVER_CERTIFICATE`
- Optional TWNTaxiAD:
  - `MSSQL_TWNTAXIAD_SERVER`
  - `MSSQL_TWNTAXIAD_DATABASE`
  - `MSSQL_TWNTAXIAD_USER`
  - `MSSQL_TWNTAXIAD_PASSWORD`
  - `MSSQL_TWNTAXIAD_DRIVER`
  - `MSSQL_TWNTAXIAD_PORT`
  - `MSSQL_TWNTAXIAD_TRUST_SERVER_CERTIFICATE`

## Tasks
1. Update config profile metadata.
   - Add fixed profile definitions for default, secondary, Tend, ProjectWorkTracker, and TWNTaxiAD.
   - Preserve exported constants needed by existing imports.
   - Generalize `ALLOWED_PROFILES`, `resolve_profile`, `match_database_name`, `allowed_db_values`, and `env_key`.
   - Keep internal profile ids stable and lowercase for non-default named profiles.
2. Update config validation.
   - Default remains required when selected or when tools omit `db`.
   - Optional profiles report `CONFIG_MISSING` only when selected and required fields are missing.
   - Invalid ports/trust flags return `CONFIG_INVALID` with safe details.
   - Error payloads list variable names only, never values.
3. Update service and server if needed.
   - Confirm existing optional `db` flow works for all profiles after config changes.
   - Avoid changing MCP tool names or required arguments.
4. Update tests.
   - Add config tests for each named profile.
   - Add case-insensitive selector tests such as `db="tend"`.
   - Add database-name selector tests for the new profiles.
   - Add safe missing-profile and partial-profile tests.
   - Keep default and secondary regression tests.
   - Add service routing tests for at least one named profile, ideally all three.
5. Update docs and examples.
   - README environment variable reference and selector examples.
   - `scripts/mssql-pyodbc-mcp.env.example` with commented new profiles.
   - Main specs listed in the impact analysis.
6. Verify.
   - `python3 -m pytest`
   - `python3 -m compileall src tests`

## Acceptance Criteria
- `test_connection(db="Tend")` uses `MSSQL_TEND_*` when configured.
- `test_connection(db="ProjectWorkTracker")` uses `MSSQL_PROJECTWORKTRACKER_*` when configured.
- `test_connection(db="TWNTaxiAD")` uses `MSSQL_TWNTAXIAD_*` when configured.
- Lowercase equivalents such as `db="tend"` also resolve to the same profile.
- Configured database-name selection works for all configured profiles.
- `list_tables`, `describe_table`, and `query` can target the new profiles through `db`.
- Existing default and secondary behaviors remain backward compatible.
- Selecting an unconfigured optional profile returns safe `CONFIG_MISSING`.
- Unknown selectors return safe `CONFIG_INVALID` with allowed values.
- No passwords or full connection strings appear in tool responses or errors.
- Docs and env example describe all five supported profiles.

## Ready for PG
- Yes

## Notes
- This CR intentionally supports a fixed set of named profiles. A future CR can introduce arbitrary profile registration if needed.
- Cross-database object references inside SQL remain outside this CR and are governed by existing SQL Server permissions plus current read-only policy.
