# Implementation Plan

## Project
- Name: mssql-pyodbc-mcp
- CR: CR-003
- Branch target: `pg/CR-003-twtaxiad53-global-business`

## Goal
- Add the optional `TWTaxiAD53` profile.
- Replace the existing `secondary` profile with `GlobalBusiness`.
- Safely migrate the existing Global Business runtime configuration without changing its values.
- Preserve all unaffected profiles and existing read-only behavior.

## Design Summary
- Keep the existing fixed `DatabaseProfileDefinition` registry.
- Keep one selected `DatabaseConfig` per tool call.
- Keep MCP tool names, parameters, service flow, DB operations, SQL policy, row limit, and serialization unchanged.
- Change the supported profile registry to:

| Internal ID | Display selector | Environment prefix | Required |
|---|---|---|---|
| `default` | `default` | `MSSQL` | Yes |
| `global_business` | `GlobalBusiness` | `MSSQL_GLOBAL_BUSINESS` | No |
| `tend` | `Tend` | `MSSQL_TEND` | No |
| `projectworktracker` | `ProjectWorkTracker` | `MSSQL_PROJECTWORKTRACKER` | No |
| `twntaxiad` | `TWNTaxiAD` | `MSSQL_TWNTAXIAD` | No |
| `254global` | `254global` | `MSSQL_254GLOBAL` | No |
| `twntaxiad53` | `TWTaxiAD53` | `MSSQL_TWNTAXIAD53` | No |

- Direct profile selectors remain case-insensitive.
- Configured database-name selectors remain case-insensitive.
- Fixed selectors retain precedence over configured database names.
- Add an explicit retired-selector guard for `secondary` before database-name matching.
- User-facing documentation prefers `GlobalBusiness` and `TWTaxiAD53`; existing internal IDs remain accepted.

## Environment Variable Changes

### Global Business Rename

| Old key | New key |
|---|---|
| `MSSQL_SECONDARY_SERVER` | `MSSQL_GLOBAL_BUSINESS_SERVER` |
| `MSSQL_SECONDARY_DATABASE` | `MSSQL_GLOBAL_BUSINESS_DATABASE` |
| `MSSQL_SECONDARY_USER` | `MSSQL_GLOBAL_BUSINESS_USER` |
| `MSSQL_SECONDARY_PASSWORD` | `MSSQL_GLOBAL_BUSINESS_PASSWORD` |
| `MSSQL_SECONDARY_DRIVER` | `MSSQL_GLOBAL_BUSINESS_DRIVER` |
| `MSSQL_SECONDARY_PORT` | `MSSQL_GLOBAL_BUSINESS_PORT` |
| `MSSQL_SECONDARY_TRUST_SERVER_CERTIFICATE` | `MSSQL_GLOBAL_BUSINESS_TRUST_SERVER_CERTIFICATE` |

- Preserve each existing value exactly.
- Do not retain old keys after successful migration.
- Do not add fallback logic for old keys.

### New TWTaxiAD53 Group
- Add these runtime fields blank for the user to populate:
  - `MSSQL_TWNTAXIAD53_SERVER`
  - `MSSQL_TWNTAXIAD53_DATABASE`
  - `MSSQL_TWNTAXIAD53_USER`
  - `MSSQL_TWNTAXIAD53_PASSWORD`
  - `MSSQL_TWNTAXIAD53_DRIVER`
  - `MSSQL_TWNTAXIAD53_PORT`
  - `MSSQL_TWNTAXIAD53_TRUST_SERVER_CERTIFICATE`
- Do not copy values from `TWNTaxiAD` or another profile.
- Before live verification, the user must fill all seven fields. In particular, a blank trust-certificate flag is invalid under existing behavior.

## Selector and Error Contract
- Supported preferred direct selectors add:
  - `GlobalBusiness`
  - `TWTaxiAD53`
- Resolver-compatible internal selectors add:
  - `global_business`
  - `twntaxiad53`
- Remove:
  - `secondary`
- `db="secondary"` must always return safe `CONFIG_INVALID` with `Unknown MSSQL DB selector.`
- Error details may contain normalized selector names, allowed display selectors, configured database names, and missing key names, but never values.
- Successful response `db` fields use:
  - `global_business`
  - `twntaxiad53`

## Tasks

### 1. Protect the Current Working State
- Inspect `git status` and preserve all existing uncommitted work.
- Do not reset, revert, or broadly rewrite files.
- Record the existing automated baseline: 46 passing tests.
- Use small patches and review diffs with line-ending-only changes ignored where practical.

### 2. Update Profile Metadata and Resolution
- File: `src/mssql_pyodbc_mcp/config.py`
- Remove `PROFILE_SECONDARY`.
- Add:
  - `PROFILE_GLOBAL_BUSINESS = "global_business"`
  - `PROFILE_TWNTAXIAD53 = "twntaxiad53"`
- Replace the secondary profile definition with:
  - `DatabaseProfileDefinition(PROFILE_GLOBAL_BUSINESS, "GlobalBusiness", "MSSQL_GLOBAL_BUSINESS")`
- Add:
  - `DatabaseProfileDefinition(PROFILE_TWNTAXIAD53, "TWTaxiAD53", "MSSQL_TWNTAXIAD53")`
- Keep `PROFILE_254GLOBAL` and all other current definitions.
- Add `RETIRED_DB_SELECTORS = {"secondary"}` or equivalent.
- In `resolve_profile()`:
  - normalize the input;
  - reject retired selectors before fixed selector and database-name resolution;
  - keep the existing safe `CONFIG_INVALID` shape.
- In `allowed_db_values()`:
  - never add retired selector values;
  - preserve current de-duplication and safe output.
- Do not read `MSSQL_SECONDARY_*` anywhere in production code.

### 3. Update Configuration Tests
- File: `tests/test_config.py`
- Replace `SECONDARY_ENV` with a Global Business fixture using `MSSQL_GLOBAL_BUSINESS_*`.
- Add complete `TWTaxiAD53` test data.
- Replace secondary profile tests with Global Business tests for:
  - direct display selector;
  - internal selector;
  - case-insensitive selection;
  - all seven environment keys;
  - configured database-name selection;
  - safe internal ID.
- Add `TWTaxiAD53` tests for:
  - direct display selector;
  - internal selector;
  - case-insensitive selection;
  - all seven environment keys;
  - configured database-name selection;
  - safe internal ID.
- Add negative and isolation tests:
  - `MSSQL_SECONDARY_*` alone does not configure Global Business.
  - `secondary` returns `CONFIG_INVALID`, not `CONFIG_MISSING`.
  - a configured database literally named `secondary` remains rejected.
  - the allowed list contains GlobalBusiness and `TWTaxiAD53`, excludes secondary, and retains all unaffected profiles.
  - blank/partial `TWTaxiAD53` returns safe new-prefixed missing keys only when selected.
  - blank/partial `TWTaxiAD53` does not affect default or another configured profile.
  - `TWNTaxiAD` and `TWTaxiAD53` resolve independently.
- Preserve default, Tend, ProjectWorkTracker, TWNTaxiAD, and 254global regression tests.

### 4. Update Service Routing Tests
- File: `tests/test_service.py`
- Replace the secondary fixture and routing assertions with Global Business.
- Verify the Global Business configured database-name selector.
- Add routing coverage for `TWTaxiAD53`.
- Across mock-backed tests, exercise:
  - `test_connection`
  - `list_tables`
  - `describe_table`
  - `query`
- Verify safe result metadata returns `global_business` or `twntaxiad53`.
- Verify `as_tool_response(..., db="secondary")` returns safe `CONFIG_INVALID`.
- Retain all existing default and named-profile tests.
- Production changes to `service.py`, `server.py`, and `db.py` are not expected; modify them only if tests prove a real gap.

### 5. Update Canonical Specifications and User Documentation
- Review the canonical specifications updated during PM planning and keep the implementation aligned:
  - `docs/specs/system-spec.md`
  - `docs/specs/api-spec.md`
  - `docs/specs/domain-model.md`
- Make only corrective spec edits if implementation uncovers a genuine mismatch; do not remove the retained 254global profile.
- Update `README.md`:
  - replace secondary setup with Global Business;
  - add `TWTaxiAD53` without conflating it with `TWNTaxiAD`;
  - document the breaking rename;
  - add selector and live-check examples;
  - do not add real credentials.
- Update `scripts/mssql-pyodbc-mcp.env.example`:
  - replace the secondary example with Global Business;
  - add a separate commented `TWTaxiAD53` group;
  - retain safe example values only.
- Do not rewrite historical CR-001 or CR-002 documents; they remain historical records.

### 6. Migrate the Runtime Env Safely
- Target: `/home/areat/.config/mssql-pyodbc-mcp/env`
- This file is outside the project workspace and contains secrets; obtain the required write approval before changing it.
- Preflight using key-name-only checks:
  - exactly seven expected `MSSQL_SECONDARY_*` keys exist;
  - no conflicting `MSSQL_GLOBAL_BUSINESS_*` keys exist;
  - no conflicting `MSSQL_TWNTAXIAD53_*` keys exist.
- Build and validate the complete replacement before replacing the original:
  - rename only the seven key names;
  - preserve every right-hand value and existing quoting exactly;
  - add the seven `MSSQL_TWNTAXIAD53_*` keys with blank values;
  - preserve file permissions;
  - do not print, diff, log, or include the values in tool output.
- Postflight using key-name-only checks:
  - `MSSQL_SECONDARY_*` count is 0;
  - `MSSQL_GLOBAL_BUSINESS_*` count is 7;
  - `MSSQL_TWNTAXIAD53_*` count is 7;
  - required Global Business keys are nonblank, without displaying values;
  - corresponding Global Business values are byte-equivalent to the former values, using an in-process comparison that emits only pass/fail.
- If preflight, value-equivalence, syntax, permission, or postflight validation fails, do not restart MCP and leave the original env file intact.

### 7. Automated Verification
- Run:
  - `python3 -m pytest`
  - `python3 -m compileall src tests`
- Confirm the full suite passes.
- Confirm no production or documentation reference to `MSSQL_SECONDARY_*` or active `db="secondary"` guidance remains, excluding historical CR documents and explicit retired-selector tests/docs.
- Confirm no real runtime values appear in git diff or generated project files.
- Review only intended files and preserve unrelated changes.

### 8. Coordinated Restart and Global Business Verification
- Update code and runtime env before restarting MCP.
- Restart or refresh the MCP process once both sides are ready.
- Verify:
  - `python scripts/check_mcp_tools.py GlobalBusiness`
  - the configured Global Business database name resolves correctly;
  - `secondary` returns safe `CONFIG_INVALID`;
  - default and `TWNTaxiAD` smoke checks still pass.
- Do not use `scripts/check_odbc_connection.py` as proof for named profiles because it validates the default profile only.

### 9. TWTaxiAD53 Live Verification
- Wait for the user to fill all seven `MSSQL_TWNTAXIAD53_*` runtime values.
- Restart or refresh MCP after the user update.
- Run:
  - `python scripts/check_mcp_tools.py TWTaxiAD53`
- The script must successfully exercise:
  - `test_connection`
  - `list_tables`
  - `describe_table` using a valid returned table
  - a harmless read-only `query`
- Verify the configured `MSSQL_TWNTAXIAD53_DATABASE` value also selects the profile.
- Record live verification as pending until these checks pass.

## Deployment and Rollback
- Treat code and runtime env as one coordinated breaking deployment.
- Do not restart between the code change and env migration.
- If Global Business verification fails:
  - stop further live checks;
  - restore the prior code/profile definition and old runtime key names together;
  - restart only after both sides again match;
  - do not retain a mixed old/new state.
- Rollback material must be protected as secret-bearing configuration and must not be committed or printed.
- The final accepted state must contain only `MSSQL_GLOBAL_BUSINESS_*`, not `MSSQL_SECONDARY_*`.

## Acceptance Criteria
- Profile registry contains exactly the required target profiles and retains 254global.
- `GlobalBusiness`, `global_business`, and case variants resolve to `global_business`.
- `TWTaxiAD53`, `twntaxiad53`, and case variants resolve to `twntaxiad53`.
- Both configured database names resolve to the correct profiles when unique.
- `secondary` always returns safe `CONFIG_INVALID` and is absent from allowed values.
- `MSSQL_SECONDARY_*` has no production runtime effect.
- Global Business uses only `MSSQL_GLOBAL_BUSINESS_*`.
- `TWTaxiAD53` uses only `MSSQL_TWNTAXIAD53_*`.
- Missing/partial optional configuration affects only the selected profile.
- All four tools route correctly to both profiles without signature changes.
- Successful response identities use the new internal IDs.
- Runtime env values for Global Business are preserved exactly under the new key names.
- Runtime env contains seven blank `TWTaxiAD53` fields for the user.
- All old runtime secondary keys are absent.
- README, env example, and canonical specs are updated without real credentials.
- Automated tests and compile checks pass.
- Global Business live verification passes after coordinated restart.
- `TWTaxiAD53` live verification passes after the user supplies values.
- Existing default, Tend, ProjectWorkTracker, TWNTaxiAD, 254global, SQL policy, row-limit, and serialization behavior remain unchanged.

## Ready for PG
- Yes

## Notes
- Live `TWTaxiAD53` verification is a post-implementation user-dependent gate, not a blocker to starting PG work.
- ProjectWorkTracker synchronization is disabled for CR-003.
- PM planning stops here and does not implement code or runtime configuration.
