# Change Request

## Project
- Name: mssql-pyodbc-mcp
- Existing Project Path: /mnt/d/AIProject/Workspaces/mssql-pyodbc-mcp

## Change Type
- New feature / configuration expansion.

## Reason / Goal
- The tool currently supports the required default MSSQL connection and an optional secondary MSSQL connection.
- The user needs the same MCP server to also connect to three additional named MSSQL databases:
  - Tend
  - ProjectWorkTracker
  - TWNTaxiAD
- The goal is to let agents select these new DB targets through the existing tool `db` argument without breaking existing default and secondary behavior.

## Current Behavior
- The default profile uses `MSSQL_*` environment variables.
- The optional secondary profile uses `MSSQL_SECONDARY_*` environment variables.
- Tools accept optional `db`, where omitted or `default` uses the default profile.
- Existing supported selectors include `default`, `secondary`, and configured database names from `MSSQL_DATABASE` / `MSSQL_SECONDARY_DATABASE`.
- The supported tools are:
  - `test_connection`
  - `list_tables`
  - `describe_table`
  - `query`

## Expected Behavior
- Add three optional named MSSQL DB profiles:
  - `Tend`
  - `ProjectWorkTracker`
  - `TWNTaxiAD`
- Each added profile uses the same setting fields as existing profiles:
  - server
  - database
  - user
  - password
  - driver
  - port
  - trust server certificate
- Environment variable keys use full uppercase profile names after `MSSQL_`.
- Expected environment variable groups:
  - `MSSQL_TEND_SERVER`
  - `MSSQL_TEND_DATABASE`
  - `MSSQL_TEND_USER`
  - `MSSQL_TEND_PASSWORD`
  - `MSSQL_TEND_DRIVER`
  - `MSSQL_TEND_PORT`
  - `MSSQL_TEND_TRUST_SERVER_CERTIFICATE`
  - `MSSQL_PROJECTWORKTRACKER_SERVER`
  - `MSSQL_PROJECTWORKTRACKER_DATABASE`
  - `MSSQL_PROJECTWORKTRACKER_USER`
  - `MSSQL_PROJECTWORKTRACKER_PASSWORD`
  - `MSSQL_PROJECTWORKTRACKER_DRIVER`
  - `MSSQL_PROJECTWORKTRACKER_PORT`
  - `MSSQL_PROJECTWORKTRACKER_TRUST_SERVER_CERTIFICATE`
  - `MSSQL_TWNTAXIAD_SERVER`
  - `MSSQL_TWNTAXIAD_DATABASE`
  - `MSSQL_TWNTAXIAD_USER`
  - `MSSQL_TWNTAXIAD_PASSWORD`
  - `MSSQL_TWNTAXIAD_DRIVER`
  - `MSSQL_TWNTAXIAD_PORT`
  - `MSSQL_TWNTAXIAD_TRUST_SERVER_CERTIFICATE`
- Tools should select these profiles with:
  - `db="Tend"`
  - `db="ProjectWorkTracker"`
  - `db="TWNTaxiAD"`
- Existing `MSSQL_SECONDARY_*` and `db="secondary"` compatibility must remain.

## Scope
- In Scope:
  - Add support for three additional optional named MSSQL profiles.
  - Preserve default and secondary profile behavior.
  - Preserve selection by configured database name where applicable.
  - Update configuration resolution, docs, env example, and tests.
  - Ensure all existing tools can target the new profiles through `db`.
- Out of Scope:
  - Adding write SQL support.
  - Changing authentication model beyond existing SQL username/password auth.
  - Changing read-only SQL validation policy.
  - Adding UI.
  - Removing or renaming existing `MSSQL_*` or `MSSQL_SECONDARY_*` settings.

## Affected Areas
- UI:
  - None.
- API:
  - MCP tool schemas remain the same, but valid `db` values expand.
- Data:
  - No database schema or stored data changes expected.
- Workflow:
  - Agents can choose one of five total configured targets: default, secondary, Tend, ProjectWorkTracker, TWNTaxiAD.
- Tests:
  - Add tests for the three named profiles, environment variable resolution, optional profile behavior, and backward compatibility.
- Docs:
  - Update README and environment example.
- Deployment:
  - Runtime environment setup must include any desired new `MSSQL_<PROFILE>_*` variables.

## Non-Regression Requirements
- Existing default profile behavior must continue to work with `MSSQL_*`.
- Existing secondary profile behavior must continue to work with `MSSQL_SECONDARY_*`.
- `db="secondary"` must continue to work.
- Omitting `db` must continue to use `default`.
- Passwords and full connection strings must not be returned in tool responses or documentation examples.
- Read-only query enforcement must remain unchanged.
- Missing optional named profiles must not prevent using configured profiles.

## Data / Content Impact
- No database data migration is expected.
- No content, image, license, or UI text impact beyond documentation.
- The added profile names are configuration identifiers and should be documented consistently.

## Evidence
- Screenshots: N/A
- Error Messages: N/A
- Sample Data: N/A
- Reproduction Steps: N/A
- References:
  - Existing CR-001 added secondary DB support.
  - Current project README documents default and secondary environment variable patterns.

## Acceptance Signals
- A user can configure `MSSQL_TEND_*` and call tools with `db="Tend"`.
- A user can configure `MSSQL_PROJECTWORKTRACKER_*` and call tools with `db="ProjectWorkTracker"`.
- A user can configure `MSSQL_TWNTAXIAD_*` and call tools with `db="TWNTaxiAD"`.
- Existing `default` and `secondary` profile tests still pass.
- Unit tests cover missing optional profile behavior.
- README and env example describe all supported profiles.

## Constraints
- Keep Python and pyodbc.
- Keep local stdio MCP server behavior.
- Preserve existing project layout and naming style.
- Do not expose passwords or sensitive connection strings.
- Do not implement code during CRA stage.

## Assumptions
- The three new profiles are optional, like the existing secondary profile.
- The profile selector should be case-insensitive for matching, consistent with current profile/database-name matching behavior.
- The actual `DATABASE` value for each profile may match the profile name, but PM/SD should decide whether exact equality is required.
- Default optional values should remain aligned with existing defaults:
  - driver: `ODBC Driver 18 for SQL Server`
  - port: `1433`
  - trust server certificate: `yes`

## Open Questions
- Should `db` also accept lower-case aliases such as `tend`, `projectworktracker`, and `twntaxiad`, or only the exact display names?
- Should the implementation generalize profile definitions to a list/map, or keep fixed profile constants for this known set? This is for PM/SD planning.
- Should docs recommend setting `MSSQL_<PROFILE>_DATABASE` equal to the profile name?

## Ready for PM
- Yes
