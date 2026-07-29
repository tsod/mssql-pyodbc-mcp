# Change Request

## Project
- Name: mssql-pyodbc-mcp
- Existing Project Path: /mnt/d/AIProject/Workspaces/mssql-pyodbc-mcp

## Change Type
- New feature / configuration expansion.
- Breaking configuration rename for the existing `secondary` profile.

## Reason / Goal
- Add a new optional `TWTaxiAD53` MSSQL connection that agents can access through the existing read-only MCP tools.
- Replace the generic `secondary` connection name with the business-specific `GlobalBusiness` name.
- Keep connection selection explicit and consistent with the project's existing fixed-profile model.

## Current Behavior
- The project uses fixed MSSQL profile definitions backed by environment-variable groups.
- The existing optional `secondary` profile uses:
  - `MSSQL_SECONDARY_SERVER`
  - `MSSQL_SECONDARY_DATABASE`
  - `MSSQL_SECONDARY_USER`
  - `MSSQL_SECONDARY_PASSWORD`
  - `MSSQL_SECONDARY_DRIVER`
  - `MSSQL_SECONDARY_PORT`
  - `MSSQL_SECONDARY_TRUST_SERVER_CERTIFICATE`
- Callers can select the existing profile with `db="secondary"` or its configured database name.
- `TWTaxiAD53` is not currently a registered profile, so it cannot be selected through `db`.
- All four tools accept an optional `db` selector:
  - `test_connection`
  - `list_tables`
  - `describe_table`
  - `query`

## Expected Behavior
- Add a new optional fixed profile with:
  - Internal profile ID: `twntaxiad53`
  - Display selector: `TWTaxiAD53`
  - Environment prefix: `MSSQL_TWNTAXIAD53`
- Direct profile selectors remain case-insensitive.
- The actual database name is determined by `MSSQL_TWNTAXIAD53_DATABASE` and may also be used as a selector.
- Add these seven blank fields to the runtime env file for the user to populate manually:
  - `MSSQL_TWNTAXIAD53_SERVER`
  - `MSSQL_TWNTAXIAD53_DATABASE`
  - `MSSQL_TWNTAXIAD53_USER`
  - `MSSQL_TWNTAXIAD53_PASSWORD`
  - `MSSQL_TWNTAXIAD53_DRIVER`
  - `MSSQL_TWNTAXIAD53_PORT`
  - `MSSQL_TWNTAXIAD53_TRUST_SERVER_CERTIFICATE`
- Rename the existing `secondary` profile to:
  - Internal profile ID: `global_business`
  - Display selector: `GlobalBusiness`
  - Environment prefix: `MSSQL_GLOBAL_BUSINESS`
- Rename the complete existing environment-variable group:
  - `MSSQL_SECONDARY_SERVER` to `MSSQL_GLOBAL_BUSINESS_SERVER`
  - `MSSQL_SECONDARY_DATABASE` to `MSSQL_GLOBAL_BUSINESS_DATABASE`
  - `MSSQL_SECONDARY_USER` to `MSSQL_GLOBAL_BUSINESS_USER`
  - `MSSQL_SECONDARY_PASSWORD` to `MSSQL_GLOBAL_BUSINESS_PASSWORD`
  - `MSSQL_SECONDARY_DRIVER` to `MSSQL_GLOBAL_BUSINESS_DRIVER`
  - `MSSQL_SECONDARY_PORT` to `MSSQL_GLOBAL_BUSINESS_PORT`
  - `MSSQL_SECONDARY_TRUST_SERVER_CERTIFICATE` to `MSSQL_GLOBAL_BUSINESS_TRUST_SERVER_CERTIFICATE`
- Preserve the existing runtime values when renaming the `MSSQL_SECONDARY_*` keys.
- Remove all `MSSQL_SECONDARY_*` keys after their values have been migrated.
- Remove `db="secondary"` completely. No backward-compatible environment-variable or selector alias is required.
- `db="secondary"` must return the existing safe unknown-selector error after the change.
- The configured Global Business database name remains a valid selector.

## Scope
- In Scope:
  - Register the `TWTaxiAD53` fixed profile.
  - Add blank `MSSQL_TWNTAXIAD53_*` fields to the runtime env file.
  - Replace the fixed `secondary` profile with `GlobalBusiness`.
  - Migrate all seven existing runtime `MSSQL_SECONDARY_*` values to `MSSQL_GLOBAL_BUSINESS_*`.
  - Remove the old environment-variable names and `secondary` selector.
  - Preserve selection by configured database name for both profiles.
  - Support both profiles across all four existing tools.
  - Update configuration resolution, automated tests, README, and the env example.
  - Perform automated verification before live database verification.
  - Perform live database verification after the user fills the `TWTaxiAD53` values.
- Out of Scope:
  - Dynamic runtime profile registration or a general profile-system refactor.
  - Backward compatibility for `MSSQL_SECONDARY_*` or `db="secondary"`.
  - Database schema changes or data migration.
  - Write SQL, DDL, administrative SQL, `EXEC`, or multi-statement support.
  - Authentication-model changes.
  - UI changes.

## Affected Areas
- UI:
  - None.
- API:
  - MCP tool signatures remain unchanged.
  - Valid `db` selectors add `TWTaxiAD53` and `GlobalBusiness`.
  - The `secondary` selector is intentionally removed.
- Data:
  - No database schema or stored-data changes.
  - Runtime configuration keys change, but existing Global Business connection values must be preserved.
- Workflow:
  - Agents select the renamed connection with `db="GlobalBusiness"`.
  - Agents select the new connection with `db="TWTaxiAD53"`.
  - The MCP process must be restarted or refreshed after runtime environment changes.
- Tests:
  - Add configuration and service coverage for `TWTaxiAD53`.
  - Replace `secondary` profile expectations with `GlobalBusiness`.
  - Verify case-insensitive direct selectors.
  - Verify selection by configured database name.
  - Verify `secondary` is rejected as an unknown selector.
  - Run regression tests for every unaffected profile and the default behavior.
- Docs:
  - Update README and the env example.
  - Do not include real credentials.
- Deployment:
  - Update the runtime env file.
  - Preserve existing Global Business values during the key rename.
  - Leave the new `TWTaxiAD53` values blank for the user to fill.
  - Restart or refresh the MCP server after configuration is complete.

## Non-Regression Requirements
- The existing `TWNTaxiAD` profile must remain separate from `TWTaxiAD53` and continue working unchanged.
- Default, Tend, ProjectWorkTracker, TWNTaxiAD, 254global, and any other unaffected registered profiles must retain their existing behavior.
- Omitting `db` must continue to use the default profile.
- Configured database-name selection must continue to work.
- Existing Global Business connection values must not be altered while their environment-variable keys are renamed.
- Missing or blank optional `TWTaxiAD53` settings must not prevent other configured profiles from working.
- Read-only SQL validation and query restrictions must remain unchanged.
- Passwords and complete connection strings must not appear in tool responses, tests, documentation, status files, or change-request documents.
- The intentional removal of `secondary` is the only approved compatibility break in this change.

## Data / Content Impact
- No database data migration is required.
- No existing database records are modified.
- Runtime configuration names change for one existing connection.
- Documentation gains the `GlobalBusiness` and `TWTaxiAD53` configuration identifiers.
- No image, media, content-license, or UI-text impact.

## Evidence
- Screenshots: N/A
- Error Messages: N/A
- Sample Data: N/A; connection values are intentionally excluded.
- Reproduction Steps:
  - Calling a tool with `db="TWTaxiAD53"` currently fails because the profile is not registered.
  - The existing Global Business connection is currently represented by `MSSQL_SECONDARY_*` and `db="secondary"`.
- References:
  - CR-001 introduced optional secondary DB support.
  - CR-002 introduced additional fixed named DB profiles.
  - Current fixed profile metadata and environment-variable mapping in `src/mssql_pyodbc_mcp/config.py`.

## Acceptance Signals
- Automated phase:
  - The complete automated test suite passes.
  - Tests prove `TWTaxiAD53` and `GlobalBusiness` resolve case-insensitively.
  - Tests prove the configured database name resolves to the matching profile.
  - Tests prove `db="secondary"` returns the safe unknown-selector error.
  - Tests prove blank optional `TWTaxiAD53` settings do not affect other profiles.
  - Regression tests pass for all unaffected profiles and the default behavior.
  - README and the env example contain the new environment-variable groups without real credentials.
  - The runtime env file contains blank `MSSQL_TWNTAXIAD53_*` fields.
  - Existing `MSSQL_SECONDARY_*` runtime values are present under the corresponding `MSSQL_GLOBAL_BUSINESS_*` keys, and the old keys are absent.
- Live DB phase after the user supplies `TWTaxiAD53` values:
  - `test_connection(db="TWTaxiAD53")` succeeds.
  - `list_tables(db="TWTaxiAD53")` succeeds.
  - `describe_table(..., db="TWTaxiAD53")` succeeds for a valid table.
  - `query(..., db="TWTaxiAD53")` succeeds for an allowed read-only query.
  - The four tools work through `db="GlobalBusiness"`.
  - Both profiles can also be selected by their configured database names.

## Constraints
- Keep the existing Python, pyodbc, stdio MCP, and fixed-profile approach.
- Use uppercase environment-variable names.
- Do not expose or replace existing Global Business connection values.
- The user will manually fill the new `TWTaxiAD53` connection values.
- Live `TWTaxiAD53` verification cannot complete until those values are supplied.
- CRA does not perform technical design or implementation.

## Assumptions
- `GlobalBusiness` refers to the database connection currently represented by `secondary`.
- Renaming the Global Business keys does not change its server, database, account, driver, port, or trust-certificate settings.
- Optional field defaults remain consistent with existing behavior unless PM/SD identifies a documented constraint.
- Deployment operators can restart or refresh Codex/MCP after the environment changes.

## Open Questions
- None for CRA handoff.

## Ready for PM
- Yes
