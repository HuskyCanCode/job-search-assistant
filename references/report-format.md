# Report and input contract

## Finished report

Begin with a short date/scope/profile note and explain that match ratings measure documented fit, not hiring probability or employer reputation. Apply [source-policy-audit.md](source-policy-audit.md) to every source and delivered format. The first table must be a company overview; target 20 distinct relevant companies unless the user specifies another scope. Link each company name to its verified official website where permitted; if the website cannot be established, keep it unlinked and mark it unknown.

| Company / official website | Company match | Size / as of | Recent workforce trend | Latest publicly reported layoff | Up to 3 recommended jobs |
| --- | --- | --- | --- | --- | --- |
| Verified company link | Derived 0–100 or N/A; evidence/provisional status | Reported count, range or estimate with scope/source | Direction, actual comparison period and source | Date + announcement/effective label, source and limits | Direct links to actual qualifying job posts; fewer than 3 is valid |

Twenty is a company target, not a promise of 60 vacancies. State the number of researched companies, the number with verified open jobs, the number with recommendable verified jobs and any shortfall against the last count. Employers represented only by inaccessible leads or confirmed-ineligible jobs do not fulfill the recommendation target. Do not repeat parents, aliases or city variants to inflate the count.

After that overview, show jobs grouped under each company in the same order. Within each company separate open recommendations, confirmed eligibility blockers, unverified leads and inactive jobs. Use these tables, splitting wide tables if needed:

| Priority | Role and direct job link | Company | Location / remote limits | Pay | Fit / coverage | Eligibility | Evidence, gaps, next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Application priority | [Verified title](https://example.com/replace-with-verified-post) | Employer | As stated | Currency + period, or unknown | Score or N/A + coverage | Met / unknown / unmet | Concise explanation |

The example URL is only a format illustration. Replace it with an observed posting. Record posted and checked dates in job details; unknown posting dates stay unknown. Include employment type and requisition ID in notes. Company facts use their own as-of dates and sources, not the job's posting date. Follow [company-research.md](company-research.md) for size, headcount and layoff evidence.

| Role group | Keywords / titles | Why relevant | Reusable query | Suggested source |
| --- | --- | --- | --- | --- |
| Close / adjacent / stretch | User-relevant terms | Link to transferable evidence or goal | Actual query text | Employer site, job board, or search engine |

| Job requirement | Category | Match | Resume / profile evidence | Gap or clarification |
| --- | --- | --- | --- | --- |
| Distinct JD criterion | Rubric category | met / partial / absent / unknown | Specific source section or user statement | Action supported by the evidence |

Provide evidence details for the strongest opportunities and any recommendation that hinges on a disputed or missing requirement. Keep permitted inaccessible leads, known hard blockers, and closed postings separate from active recommendations. Show a short search log with queries/sources used, check date, coverage, and why the search stopped. Policy-disabled routes use `skipped`, while actual permitted requests that fail use `blocked`. Independent host discovery is `web_search`; do not imply that it searched a restricted board. Restricted/unverified boards are manual by default, including targeted collection through a search engine. Ignore incidental restricted snippets rather than quoting, scoring or reconstructing them, and do not ingest Lensa content into AI outputs. User-pasted copies are not an exception.

Prefer independently verified employer facts and direct employer job links where compatible with their terms. Provider terms may restrict content use, deep links, retaining snippets or raw responses: preserve only allowed attribution and note resulting evidence limits. Glassdoor, Dice and US Welcome to the Jungle default to permitted homepage/manual-query guidance outside the job table, not deep-linked job records. Do not evade restrictions by copying responses into this schema or a checkpoint. Preserve a permitted feed's mandatory source credit, original job links and application routes even when a different employer URL exists. If zero active matches remain, report zero and suggest specific changes to soft preferences; do not fabricate replacements.

## Repeatable helper

Run from the skill repository root:

```sh
python3 scripts/build_report.py private/search-input.json --output private/job-report.md --csv private/job-report.csv --companies-csv private/company-report.csv
```

`--output` writes Markdown (`--markdown` is an alias); `--csv` writes an optional job summary, with company fields appended in version 2. `--companies-csv` writes a separate optional company summary and requires version 2. The helper uses Python 3.10+ and the standard library. It validates input, computes the rubric and renders tables without network requests. The agent must verify facts and classify evidence first. It cannot determine whether evidence is truthful or a job is actually open.

Use `--overwrite` when deliberately regenerating existing output files. Input and output paths must be distinct. Jobs with established eligibility are ordered High, Medium, Explore, then Low, followed by Clarify eligibility, Review evidence, and Not scored. Within each priority, sort by descending fit and coverage, then identifier. Blocked, unverified, and closed records stay in their separate groups. This order places assessed opportunities before records that need more research; it is not a forecast of outcomes.

The helper renders the comparison and `search_sources` coverage tables, and preserves `discovered_via` links in details and CSV. It does not enforce source licenses, deep-link permission, required link attributes, credit placement, application routes or retention limits. Check that every delivered format can satisfy a source's conditions before supplying its material. If the helper cannot, use a suitable manually assembled report that preserves the same table/scoring contract, or omit that source and continue with compatible evidence. Do not silently drop required conditions or invent schema fields the helper rejects. Add the keyword/query table and search conclusion to the final report. The runnable [sample input](../examples/sample-input.json) demonstrates the JSON shape with synthetic data.

## JSON versions and company fields

Use schema version 2 for all new company-first searches. Version 1 is retained for legacy job-only reports and does not require or invent company metadata. Both versions keep the job rubric unchanged.

| Root field | Type | Meaning |
| --- | --- | --- |
| schema_version | integer, 1 or 2 | Use 2 for company-first reports; 1 retains existing job-only behavior |
| resume_provided | boolean | True only when readable resume evidence or a sufficiently detailed candidate profile was actually used |
| search_summary | string, optional | Scope, profile source, and material assumptions; never include unnecessary personal details |
| search_sources | array, optional for older inputs; include for every live search | Actual source/query checks, defined below; access failure is not zero vacancies |
| jobs | array | Unique job records; an empty array is a valid zero-results report |
| companies | array, required in version 2 | Unique employer records below; empty allowed for zero results |
| company_target | integer 1–100, optional in version 2 | Default 20; target only, never manufacture records to satisfy it |

If a detailed profile substitutes for a resume, make this explicit in `search_summary`. When `resume_provided` is false, do not create inferred personal requirement assessments; use an empty requirements array or unknown statuses. Personal fit is N/A.

Each version 2 company has these required fields. Nested evidence links use `{label, url}` with a nonempty label and an absolute HTTP(S) URL; include the source publication date in the label or fact summary when known. Exact values and known claims require sources; source text remains researcher-supplied evidence, not automatic verification.

| Company field | Type / meaning |
| --- | --- |
| id | Nonempty unique stable employer identifier |
| name | Nonempty verified employer name; matches each linked job's `company` |
| url | Official company HTTP(S) URL, or null if unverified; do not substitute a job board or guessed domain |
| checked_at | Actual YYYY-MM-DD company research date |
| size | `{value, as_of, scope, basis, sources}`: value is a count/range description or null; as_of is date or null; scope identifies entity/geography; basis is `reported`, `estimate`, `range`, or `unknown`; sources is an evidence-link array |
| headcount_trend | `{direction, period_start, period_end, summary, sources}`: direction is `growing`, `stable`, `declining`, `mixed`, or `unknown`; dates are YYYY-MM-DD or null; summary explains comparable observations or why no conclusion is possible |
| latest_layoff | `{status, event_date, date_type, summary, sources, searched_from, searched_through}`: status is `reported`, `none_found`, or `unknown`; dates are YYYY-MM-DD or null; date_type is `announcement`, `effective`, or `unspecified`; summary includes entity/geographic limits |

Known size needs a non-null value, non-unknown basis and at least one source; unknown size uses null and unknown. A size as-of date can remain unknown if the source is undated; the company check date still records when it was read. A known headcount direction needs comparable dated evidence and sources; use `unknown` if endpoints are not comparable or available. Preserve a known period even when direction is unknown, but do not invent exact endpoints from approximate source periods. Start/end dates must both be supplied or both be null, ordered, and no later than the check date.

`reported` layoffs require evidence sources; event_date can be null with unspecified date_type if the source does not establish an exact date. An exact date must identify announcement versus effective date. A future effective date is a scheduled event, not proof it already occurred. `none_found` requires the actual bounded search period, sources checked and a clear scope statement; event_date stays null and date_type is unspecified. `unknown` is for insufficient/blocked/unsearched evidence, not a claim that no layoffs happened. Preserve the attempted search period if known even when research is incomplete; otherwise use null dates. Neither condition becomes a fictitious last-layoff date.

Do not supply a company score. The helper derives it from job evidence, and rejects unsupported fields. Duplicate company IDs, orphan job references and company-name mismatches are invalid. Company aliases and subsidiaries still need researcher deduplication; validation cannot decide legal identity.

## Job fields

| Job field | Type | Meaning |
| --- | --- | --- |
| id | nonempty string | Unique stable identifier, preferably original requisition ID |
| company_id | nonempty string, required in version 2 | Reference to the parent company record; version 1 does not use this field |
| title, company, location | nonempty strings | Verified values, or explicit Unknown where appropriate |
| url | HTTP(S) URL | Permitted direct posting URL, respecting required source/application routes; retain an inaccessible lead's URL only when linking and content use are allowed |
| salary | string or null | Stated range, currency, and period; null when unknown |
| posted_at | YYYY-MM-DD or null | Employer posting date, not crawl/check date |
| checked_at | YYYY-MM-DD | Actual verification/check date |
| posting_status | open / closed / unverified | What the source supports at check time |
| job_description_complete | boolean | Whether a complete substantive description was available |
| requirements | array | Evidence assessments, defined below |
| hard_constraints | array | Applicable material constraints, defined below; empty means eligibility was not established |
| not_applicable_categories | object, optional | Category key to substantive exclusion reason; allowed only with complete JD, with no requirements in the excluded category |
| notes | string, optional | Employment type, requisition/source detail, limitations, or candidate next-step context |
| discovered_via | array, optional | Allowed observed discovery links as `{source, url}` objects; retain all permitted distinct origins and required attribution when merging duplicate postings |

Each discovery source has a nonempty `source` name and an absolute HTTP(S) `url`. Keep the employer's preferred original posting as the job `url` only where compatible with applicable source terms, and allowed board or search-result links in `discovered_via`. Never replace a required feed job link or application route without preserving the obligation. This is provenance, not proof of verification or permission. If a job cannot be represented with permitted content and its required direct link, omit that job record; add permissible homepage/manual-query guidance separately rather than passing a homepage off as a vacancy. The CSV appends `discovery_sources` and `discovery_urls` columns; the source coverage ledger is in Markdown. Assess each output's attribution requirements separately.

## Source coverage fields

Each `search_sources` entry represents one actual source/query/method check, or an explicitly skipped route. Multiple permitted queries or a failed route followed by a separate permitted employer search can have separate entries. Do not target a restricted board through another engine as a fallback. The fields are required for each entry; the array itself stays optional for older input files and comparisons without discovery.

| Field | Type / meaning |
| --- | --- |
| source | Nonempty source name, including employer/board where relevant |
| url | Permitted observed HTTP(S) search URL, source entry point, or public API request URL; use an allowed homepage for skipped/manual routes where deep linking is restricted |
| method | `platform_search`, `web_search`, `employer_site`, or `public_api` |
| query | Exact query/filter description or API request; for skipped sources describe the intended query |
| status | `searched`, `limited`, `blocked`, or `skipped`, as defined in the search strategy |
| checked_at | Actual YYYY-MM-DD check date; include finer timestamps in notes if useful |
| results_seen | Nonnegative integer count of candidate records actually inspected; `null` for blocked/skipped checks |
| verified_open | Nonnegative integer count of those candidates subsequently verified open; at most results_seen when known |
| notes | Limits, filter details, pages inspected, and context; must be nonempty for limited/blocked/skipped checks |

`searched` and `limited` checks require an observed count (possibly zero). `blocked` and `skipped` require `results_seen: null` and `verified_open: 0`; explain why availability remains unknown. A successful query returning no candidates is different from a blocked source. Use `web_search` for actual permitted host searches and `limited` where coverage was partial; do not count ignored restricted snippets as inspected jobs or board coverage. Record a source permission decision once and reuse it rather than repeating an approval or review for each job.

Counts may overlap across checks because one requisition can appear on several boards. Do not sum them into a unique job count. The helper separately counts unique job records supplied and those marked open, including any with candidate eligibility blockers. The researcher must deduplicate requisitions before rendering; validation only prevents duplicate record IDs. Source counts may include inspected jobs not retained in the shortlist. A collector's retrieved count is not its verified-open count; see [live-discovery.md](live-discovery.md).

## Evidence fields

Each requirement has four fields:

| Field | Allowed value |
| --- | --- |
| category | required_skills / responsibilities / seniority / preferred / domain |
| requirement | Nonempty description of a distinct substantive criterion |
| status | met / partial / absent / unknown |
| evidence | String identifying the JD clause and resume/profile source; nonempty for every non-unknown assessment |

Each hard constraint has `constraint` (nonempty string), `status` (`met`, `unmet`, or `unknown`), and `evidence` (nonempty when status is not unknown). Do not insert “no restrictions” as a met constraint to manufacture eligibility certainty. Assess the user's and employer's material constraints, including remote jurisdiction where relevant.

## Score, coverage, and priority

The [matching rubric](resume-matching.md) defines category weights, evidence credit, and exclusions. Weighted coverage measures how much of the applicable rubric has an assessment other than unknown. A partial match contributes half fit credit and full evidence coverage; confidence is evidence completeness, not match quality.

| Assessment state | Rule |
| --- | --- |
| Not assessed | No readable resume or sufficiently detailed profile |
| Insufficient | No criteria, no applicable weights, or zero evidence coverage; score N/A |
| Provisional | Incomplete JD or evidence coverage below 80%; any numeric score is labeled provisional |
| Assessed | Complete JD and evidence coverage at least 80% |

| Evidence confidence | Rule |
| --- | --- |
| High | Complete JD and weighted coverage at least 90% |
| Medium | Complete JD and weighted coverage at least 60% |
| Low | Other scored evidence states, including incomplete descriptions |
| Not assessed | No candidate evidence source |

Application priority follows this order; the first applicable rule wins:

| Condition | Priority |
| --- | --- |
| Posting closed | Inactive |
| Any hard constraint explicitly unmet | Blocked |
| Posting unverified | Lead only |
| No resume/profile | Not scored |
| Evidence insufficient or assessment provisional | Review evidence |
| No hard constraints assessed or any material constraint unknown | Clarify eligibility |
| Assessed, verified open, eligible, score at least 80 | High |
| Same conditions, score 60–79.9 | Medium |
| Same conditions, score 40–59.9 | Explore |
| Same conditions, score below 40 | Low |

Report all material issues even when another rule controls the label. For example, a provisional job with unknown sponsorship needs both evidence review and sponsorship clarification. The thresholds are heuristic workflow choices, not a validated employment prediction model.

## Company recommendations and rating

For each company, use the existing job priority order to select up to 3 open jobs with complete permitted descriptions and no confirmed unmet hard constraints. Unknown constraints remain visible and require confirmation. Permitted unverified, closed, incomplete-description and blocked jobs stay in the detailed company tables but cannot appear in the recommended top3 or contribute to its rating. Restricted source material is omitted, not given a provisional score.

The company match rating is the arithmetic mean of available job-fit scores among those recommendations. Show component job IDs, how many recommendations were scored, and their mean evidence coverage. No scored recommendations, including a search without a resume/profile, means N/A. Fewer than 3 scored recommendations, any provisional job score, unknown eligibility, or an unscored recommended job makes the company rating provisional. A small sample is a limitation, not a reason to invent additional jobs.

Do not add an arbitrary bonus for company size, headcount growth or brand familiarity, and do not subtract an automatic layoff penalty. Those facts support the user's separate decision about the employer; the rating represents only the candidate's documented alignment with researched openings. It is not an assessment of company culture, financial health or the likelihood of being hired.
