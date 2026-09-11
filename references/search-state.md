# Private search state and effort suggestions

Use `scripts/search_state.py` to keep minimal permitted metadata between batches. It is an offline planner: it does not execute searches, fetch URLs, add sources, verify permissions, read resumes, or change match scores. Current source exclusions override saved records and route labels.

Store state in the skill repository's ignored `private/` directory or at an explicitly chosen private path outside that repository. Never commit it. Use pseudonymous profile/run/employer IDs. Do not include names, contact details, resumes, job descriptions, snippets, raw search outputs, cookies, API keys, tokens used as credentials, or account secrets. Observed public ATS board identifiers are allowed; credentials are not.

## Start and use

From the skill directory, create one state file for a profile and current run:

```bash
python3 scripts/search_state.py init private/search-state.json --profile candidate --run run-01 --families development qa support
python3 scripts/search_state.py suggest private/search-state.json --slots 8
```

The host prepares updated JSON using the schema below, records only actual observations, and validates it before saving:

```bash
python3 scripts/search_state.py validate private/search-state.json
python3 scripts/search_state.py validate private/proposed-state.json
python3 scripts/search_state.py save private/proposed-state.json --state private/search-state.json --expected-sha SHA_FROM_THE_FIRST_VALIDATE
```

Use the real 64-character `sha256` from validation of the current destination. The placeholder above is not executable unchanged. Saving without `--expected-sha` is create-only. A changed destination refuses replacement; reload and merge deliberately. Saving is atomic, creates files with owner-only permissions, uses an exclusive writer lock, refuses output-file symlinks and escapes from repository `private/`, and preserves an existing file if replacement fails. These guards coordinate this helper's writes; they are not a filesystem security boundary against unrelated external writers. A preexisting lock is never removed automatically.

Importable helpers are `new_state`, `validate_state`, `record_attempt`, `record_employer`, `record_feedback`, `effective_feedback`, `fresh_registry`, `suggest`, `load_state`, and `save_state`. Record helpers return validated copies without changing their input. `load_state` returns `(state, sha256)`; `save_state` returns the saved digest. `suggest` defaults to eight slots, 25% exploration, and the latest three completed attempts per family. CLI overrides are `--slots`, `--exploration` (0.1–1), and `--recent` (1–20).

## State schema

Version 1 accepts exactly these top-level fields:

```json
{
  "version": 1,
  "profile_id": "candidate",
  "run_id": "run-01",
  "allowed_families": ["development", "qa", "support"],
  "attempts": [],
  "employers": [],
  "feedback": []
}
```

Identifiers contain letters, digits, `_`, or `-`, up to 100 characters. Keep family IDs consistent when mapping explicit user role/function preferences. Timestamps must include a timezone, reflect real checks, and not be in the future. All records reject unknown fields. URLs must be public HTTPS links without credentials, query strings, or fragments; store a suitable public canonical policy/evidence URL rather than a signed or tracking link. The checks catch common sensitive structures, not every possible personal detail hidden in text: the host must keep content minimal.

### Query attempts

An illustrative completed record, not evidence of a real search:

```json
{
  "id": "query-01",
  "family": "support",
  "route": "host_search",
  "query": "entry level application support United States",
  "elapsed_seconds": 45,
  "status": "complete",
  "qualified_employer_ids": ["employer-a", "employer-b"],
  "checked_at": "2026-09-10T15:00:00Z"
}
```

Allowed routes are `host_search`, `employer_site`, `greenhouse`, `lever`, `ashby`, `remoteok_feed`, and `usajobs_api`. A route label does not authorize its execution. Store generic keywords only, with no URLs, site operators, copied snippets, or private resume details. Include the actual elapsed effort for that query and its completed verification, not an estimate presented as measured time.

`complete` means permitted results were inspected and verification finished. Record unique qualified employer IDs only after at least one current, genuinely suitable opening at that employer passed the skill's required checks. A completed empty list means verified zero yield. Do not relabel blocked or excluded routes as completed zero: keep those in the source coverage ledger. `pending` means verification remains unfinished and requires an empty ID list; it contributes no yield score and is not a zero-yield finding. `record_attempt` can replace a matching pending record with its later completed result, but cannot silently rewrite completed history.

The planner sorts completed records by check time, deduplicates employer IDs across queries and families, and credits only marginal new employers. It calculates both marginal employers per query and per minute from each family's recent completed attempts. Exploitation favors recent verified employers per minute, distributing planned effort with diminishing priority for repeated slots. At least the configured share goes to exploration; untried families receive initial coverage and all-untried starts rotate fairly. Old successes fall out of the recent window, so exhausted families cannot dominate solely on historical yield. Pending attempts count toward exploration effort but do not lower yield metrics. These metrics allocate effort; they are neither job quality nor hiring probability.

Keep one coherent search-history scope. For a new run with substantially different geography, eligibility, role goals, or profile evidence, start a new state instead of carrying incomparable yield. For a continued run with the same scope, stable employer IDs prevent duplicate discoveries being counted again. A fresh run may intentionally reset attempt history; preserve only profile feedback and registry metadata whose reuse and retention scope still applies.

### Employer registry

This limited registry supports observed Greenhouse, Lever, and Ashby public boards, not arbitrary providers or guessed tokens. Illustrative schema only:

```json
{
  "employer_id": "example",
  "career_url": "https://example.com/careers",
  "board": {
    "provider": "greenhouse",
    "board": "example",
    "region": "global",
    "observed_url": "https://job-boards.greenhouse.io/example",
    "observed": true
  },
  "provenance_url": "https://example.com/careers",
  "checked_at": "2026-09-10T15:00:00Z",
  "permission": {
    "policy_url": "https://example.com/terms",
    "scope": "public_listings_and_private_report",
    "profile_id": "candidate",
    "checked_at": "2026-09-10T15:00:00Z",
    "review_due_at": "2026-09-11T15:00:00Z",
    "expires_at": null,
    "retention_covered": true,
    "retention_basis_url": "https://example.com/terms"
  }
}
```

Do not copy the illustrative permission statements into a real search. Record them only after establishing the actual access and minimal-metadata retention basis. `scope` must be `public_listings_and_private_report`, and the permission profile must match the state. `review_due_at` is a real review deadline chosen from the applicable policy/scope; an optional `expires_at` records a known expiry, not an invented grant period. Neither may precede the permission check. Set the employer check after all recorded checks. `region` is `global`, or `eu` for Lever only. The observed URL must identify the same supported provider, region, and exact board token. The host must actually observe that link; matching its shape cannot prove observation or authorization.

`fresh_registry` filters out entries whose review deadline or expiry has arrived. Its output is a list of candidates for scope checking, never automatic fetch permission or proof that jobs remain open. Before reuse, apply current exclusions, changed terms, current run/profile scope, permission revocation, and any earlier retention deadline. Refresh jobs and required posting evidence in the current search. Review stale records through permitted policy evidence or leave them unused. Do not retain expired metadata when the applicable retention terms require deletion. No registry entry can enable an excluded source.

### Explicit user feedback

An illustrative preference record:

```json
{
  "id": "feedback-01",
  "source": "explicit_user",
  "statement": "For this search, I would prefer fewer QA roles.",
  "dimension": "role",
  "family": "qa",
  "preference": "avoid",
  "scope": "run",
  "scope_id": "run-01",
  "checked_at": "2026-09-10T15:00:00Z"
}
```

Allowed dimensions are `role` and `function`. `prefer` and `avoid` are soft preferences, `exclude` requires an explicit hard exclusion, and `neutral` records an explicit reset. Preserve a short user statement limited to the preference itself. Never infer feedback from skipped jobs, clicks, silence, or an assistant's assessment. Default to the current run unless the user explicitly expresses a continuing preference; do not silently create a profile-wide hard exclusion. Show the effective preference to the user when recording it so an incorrect interpretation can be corrected.

`effective_feedback` selects records matching the current profile or run. The latest applicable explicit statement wins for the same dimension/family; a later soft preference or reset replaces an earlier exclusion rather than inheriting its hardness. `suggest` removes only families with an effective explicit `exclude`. Soft preferences are returned for the host to reflect transparently in recommendations, with no hidden fit-score adjustment. Hard eligibility constraints remain separate and cannot be relaxed by positive feedback.
