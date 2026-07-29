# Impact Analysis

## Project
- Name: mssql-pyodbc-mcp
- CR: CR-003
- Change: Add `TWTaxiAD53` and rename the existing `secondary` profile to `GlobalBusiness`.

## PM Summary
- Add one optional fixed MSSQL profile:
  - Internal ID: `twntaxiad53`
  - Display selector: `TWTaxiAD53`
  - Environment prefix: `MSSQL_TWNTAXIAD53`
- Replace the existing optional profile:
  - From: `secondary` / `MSSQL_SECONDARY_*`
  - To: `global_business` / `GlobalBusiness` / `MSSQL_GLOBAL_BUSINESS_*`
- The rename is intentionally breaking:
  - `MSSQL_SECONDARY_*` must be removed after its values are migrated.
  - `db="secondary"` must return a safe unknown-selector error.
  - No environment-variable or selector fallback is allowed.
- MCP tool names and input shapes remain unchanged.
- SQL policy, authentication, connection behavior, result limits, and serialization remain unchanged.
- Verification has two phases:
  - Automated implementation and Global Business migration verification.
  - Live `TWTaxiAD53` verification after the user fills the new runtime values.
- The current baseline is healthy: `python3 -m pytest` passes all 46 tests before CR-003 implementation.

## Current State Evidence
- Fixed profile metadata is centralized in `src/mssql_pyodbc_mcp/config.py`.
- Current source includes:
  - `default`
  - `secondary`
  - `tend`
  - `projectworktracker`
  - `twntaxiad`
  - `254global`
- `DatabaseConfig.from_env()` performs lazy validation for the selected profile.
- `resolve_profile()` checks fixed selectors first and configured database names second.
- `service.py` and `server.py` already pass the optional `db` selector through a shared path.
- `scripts/check_mcp_tools.py` already accepts an arbitrary selector and exercises all four tools.
- The runtime env file is loaded by `scripts/run_mcp_from_env.sh`.
- The runtime env currently contains all seven `MSSQL_SECONDARY_*` keys. New Global Business and `TWTaxiAD53` keys were not present during PM inspection. Only key names were inspected; no values were read into planning documents or exposed.
- The working tree already contains uncommitted changes, including the `254global` profile. CR-003 implementation must preserve them and use narrow edits.

## SA Analysis

### Requirement Understanding
- `TWNTaxiAD` and `TWTaxiAD53` are separate optional targets and must coexist.
- Global Business is the same connection currently represented by `secondary`; only its configuration identifiers change.
- No SQL Server schema or stored-data migration is involved.
- The only values migrated are the seven existing runtime connection settings for Global Business.

### Business Rules
- The fixed profile set after CR-003 is:
  - `default` / `default` / `MSSQL_*`, required
  - `global_business` / `GlobalBusiness` / `MSSQL_GLOBAL_BUSINESS_*`, optional
  - `tend` / `Tend` / `MSSQL_TEND_*`, optional
  - `projectworktracker` / `ProjectWorkTracker` / `MSSQL_PROJECTWORKTRACKER_*`, optional
  - `twntaxiad` / `TWNTaxiAD` / `MSSQL_TWNTAXIAD_*`, optional
  - `254global` / `254global` / `MSSQL_254GLOBAL_*`, optional
  - `twntaxiad53` / `TWTaxiAD53` / `MSSQL_TWNTAXIAD53_*`, optional
- Direct profile selectors remain case-insensitive.
- Configured database names remain case-insensitive selectors.
- Internal IDs remain accepted by the existing resolver, while user documentation should prefer display selectors.
- `TWTaxiAD53` must never read or fall back to `MSSQL_TWNTAXIAD_*`.
- Global Business must never read or fall back to `MSSQL_SECONDARY_*`.
- `secondary` is a retired selector and must be rejected before configured database-name matching.
- `secondary` must not appear in the allowed selector list, even if a configured database name later uses that text.
- Missing, blank, partial, or invalid optional-profile settings affect only the selected profile.
- Omitting `db` or passing a blank selector continues to select `default`.
- Successful responses identify the resolved profile using the internal ID, including `global_business` and `twntaxiad53`.
- Read-only SQL restrictions, the 100-row limit, SQL username/password authentication, and secret-redaction rules apply to every profile.

### Workflow Rules
1. Preserve all existing Global Business values without logging them.
2. Verify the seven old keys exist and the seven new keys do not conflict.
3. Rename each `MSSQL_SECONDARY_*` key to the corresponding `MSSQL_GLOBAL_BUSINESS_*` key with the exact existing value.
4. Add seven blank `MSSQL_TWNTAXIAD53_*` keys; do not copy credentials from another profile.
5. Verify the old key count is zero and both new groups contain seven keys, using key-name-only checks.
6. Update code and runtime env before restarting the MCP process.
7. Verify Global Business and the retired selector immediately after restart.
8. Wait for the user to fill all `TWTaxiAD53` values.
9. Restart the MCP process again and perform the four live tool checks for `TWTaxiAD53`.

### Edge Cases
- `TWNTaxiAD` and `TWTaxiAD53` are visually similar and may be accidentally conflated.
- Only old `MSSQL_SECONDARY_*` keys remain after code deployment.
- Both old and new Global Business key groups exist with conflicting values.
- A configured database is literally named `secondary`.
- Two profiles have the same configured database name; existing first-match behavior would be ambiguous to users.
- A configured database name overlaps a fixed display selector; fixed selector precedence must remain unchanged.
- `TWTaxiAD53` is blank, whitespace-only, or partially configured.
- `TWTaxiAD53` has an invalid port or trust-certificate flag.
- Blank driver and port retain existing fallback behavior; blank `TRUST_SERVER_CERTIFICATE` remains invalid when that profile is selected, so it must be filled before live verification.
- Runtime env changes are complete but an old MCP process is still running.
- Unknown-selector or missing-key errors accidentally expose values.
- A live connection fails because of user-supplied credentials, network access, ODBC driver, SQL permissions, or the target database rather than implementation logic.

### Acceptance Considerations
- Tests must cover both new profile definitions, all environment prefixes, direct selectors, case-insensitive selectors, and configured database-name selectors.
- Tests must prove `MSSQL_SECONDARY_*` has no runtime effect.
- `db="secondary"` must return `CONFIG_INVALID`, not `CONFIG_MISSING`.
- The allowed selector list must include `GlobalBusiness` and `TWTaxiAD53` and exclude `secondary`.
- Optional `TWTaxiAD53` settings must not affect default or other configured profiles until selected.
- Missing-key errors must name only the new-prefixed keys and never their values.
- Regression coverage must retain default, Tend, ProjectWorkTracker, TWNTaxiAD, and 254global behavior.
- README, env example, and canonical specs must distinguish `TWNTaxiAD` from `TWTaxiAD53`.
- Automated completion does not imply live `TWTaxiAD53` acceptance.

### Open Questions
- None blocking implementation planning.

## SD Analysis

### Design Assumptions
- Keep the existing fixed `DatabaseProfileDefinition` registry.
- Keep lazy per-selection configuration validation.
- Keep `DatabaseConfig`, connection-string construction, service routing, MCP tools, DB operations, SQL policy, and serialization contracts unchanged.
- Preserve current internal-ID selector behavior but document display selectors as the preferred public form.
- Add an explicit retired-selector rule for `secondary`.

### Affected Modules
- `src/mssql_pyodbc_mcp/config.py`
  - Replace `PROFILE_SECONDARY` with `PROFILE_GLOBAL_BUSINESS`.
  - Add `PROFILE_TWNTAXIAD53`.
  - Replace the secondary definition with Global Business and add `TWTaxiAD53`.
  - Add a retired-selector set or equivalent guard before database-name fallback.
  - Keep `allowed_db_values()` consistent with the retired-selector rule.
- `src/mssql_pyodbc_mcp/service.py`
  - No production change expected.
  - Existing `_client(db)` routing should work after configuration changes.
- `src/mssql_pyodbc_mcp/server.py`
  - No tool signature or registration change expected.
- `src/mssql_pyodbc_mcp/db.py`
  - No change expected.
- `src/mssql_pyodbc_mcp/sql_policy.py`
  - No change expected.
- `src/mssql_pyodbc_mcp/serialization.py`
  - No change expected.
- `tests/test_config.py`
  - Replace secondary fixtures/tests with Global Business.
  - Add `TWTaxiAD53` coverage and retired-selector coverage.
  - Preserve all unaffected-profile regression coverage.
- `tests/test_service.py`
  - Replace secondary routing tests.
  - Add four-tool routing coverage for Global Business and `TWTaxiAD53`.
  - Verify internal IDs in safe response metadata.
- Runtime/config/docs
  - Migrate the runtime env keys without exposing values.
  - Update env example, README, and canonical specifications.

### Main Workflow
1. MCP client calls one of the existing tools with optional `db`.
2. `MssqlToolService` passes the selector to `DatabaseConfig.from_env`.
3. Configuration resolution:
   - defaults blank selectors to `default`;
   - rejects retired `secondary`;
   - resolves a fixed case-insensitive selector;
   - otherwise resolves a configured database name;
   - otherwise returns safe `CONFIG_INVALID`.
4. `env_key()` maps the resolved internal ID to the profile's fixed environment prefix.
5. Existing validation builds one `DatabaseConfig`.
6. Existing connection, metadata, or query behavior executes unchanged.

### Data Model Impact
- `DatabaseProfileDefinition` fields do not change.
- `DatabaseConfig` fields do not change.
- The fixed mapping changes:

| State | Internal ID | Display selector | Environment prefix |
|---|---|---|---|
| Removed | `secondary` | `secondary` | `MSSQL_SECONDARY` |
| Added/renamed | `global_business` | `GlobalBusiness` | `MSSQL_GLOBAL_BUSINESS` |
| Added | `twntaxiad53` | `TWTaxiAD53` | `MSSQL_TWNTAXIAD53` |

- No persisted application state or SQL Server data changes.
- Runtime env migration is a configuration-key rename, not a database migration.

### API Impact
- Tool names and argument shapes remain unchanged:
  - `test_connection(db: str = "default")`
  - `list_tables(db: str = "default")`
  - `describe_table(table_name: str, db: str = "default")`
  - `query(sql: str, db: str = "default")`
- New preferred selectors:
  - `GlobalBusiness`
  - `TWTaxiAD53`
- Existing resolver-compatible internal selectors:
  - `global_business`
  - `twntaxiad53`
- Removed selector:
  - `secondary`
- Observable response change:
  - Global Business responses change from `"db": "secondary"` to `"db": "global_business"`.
  - `TWTaxiAD53` responses use `"db": "twntaxiad53"`.

### Technical Risks
- Removing the secondary profile definition alone does not guarantee rejection because database-name fallback could accept the text `secondary`.
- Code and runtime env are a coordinated breaking deployment; mixed versions temporarily make Global Business unavailable.
- Runtime env contains secrets and must not be printed, embedded in patches, copied into documentation, or exposed through shell tracing.
- Existing new target keys must not be overwritten silently.
- Duplicate configured database names preserve existing first-match behavior; explicit display selectors should be used when ambiguity exists.
- The working tree is already dirty and includes 254global work. Broad rewrites or line-ending normalization could overwrite unrelated user changes.
- Current canonical specs do not fully describe the implemented 254global profile; CR-003 spec updates must preserve and document it.

### Open Questions
- None blocking PG handoff.

## Main Spec Updates
- Updated during PM planning because the target fixed-profile set and selector contract are now approved:
  - `docs/specs/system-spec.md`
    - Replaced secondary with Global Business.
    - Added `TWTaxiAD53`.
    - Corrected the fixed-profile count and retained 254global.
    - Documented retired-selector behavior.
  - `docs/specs/api-spec.md`
    - Replaced the secondary environment-variable group.
    - Added Global Business, 254global, and `TWTaxiAD53` environment-variable groups and selectors.
    - Documented response internal IDs and `secondary` rejection.
  - `docs/specs/domain-model.md`
    - Updated supported `DatabaseProfile` values and business constraints.
    - Retained 254global.
- Still required during PG implementation because these files describe runnable setup:
  - `README.md`
    - Update configuration, selector, breaking-change, and live-check guidance.
  - `scripts/mssql-pyodbc-mcp.env.example`
    - Replace the secondary group with Global Business.
    - Add a separate `TWTaxiAD53` example.

## Decisions
- Keep fixed profile metadata; do not introduce dynamic registration.
- Use `global_business`, `GlobalBusiness`, and `MSSQL_GLOBAL_BUSINESS`.
- Use `twntaxiad53`, `TWTaxiAD53`, and `MSSQL_TWNTAXIAD53`.
- Preserve internal IDs as case-insensitive selectors, but prefer display selectors in user documentation.
- Treat `secondary` as an explicitly retired selector and reject it before database-name fallback.
- Exclude `secondary` from allowed selector output.
- Preserve the existing first-match rule for duplicate configured database names; do not expand CR-003 into ambiguity handling.
- Update code and runtime env in one maintenance step before restarting MCP.
- Preserve Global Business values exactly and never log them.
- Require the user to fill all seven `TWTaxiAD53` fields before live verification; do not change blank trust-certificate behavior.
- Do not modify service/tool contracts, DB operations, SQL policy, row limits, authentication, or serialization.
- Preserve all current 254global work and other unrelated working-tree changes.

## Ready for PG
- Yes

## Blockers
- None for implementation.
- Live `TWTaxiAD53` acceptance remains pending until the user supplies runtime connection values, but this does not block PG implementation or automated verification.
