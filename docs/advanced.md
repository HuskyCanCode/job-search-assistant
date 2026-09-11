# Advanced usage and reference

[Back to the README](../README.md) · [Usage guide](usage-guide.md)

The scripts below are optional. Run their commands from the **repository root**. Normal searches run through the skill in your conversation.

## What it does

- Refines a broad search into useful roles, filters, and reusable search queries.
- Suggests close, adjacent, and stretch roles based on transferable experience.
- Uses supported search tools and permitted employer sources, with a short catalog of conditional feeds and APIs. Restricted and unverified boards are excluded.
- Orders review with structured local preferences, keeps uncertain candidates, preserves multiple locations, and adapts query effort to observed useful results.
- Uses parallel batches, early deduplication, permitted employer-link reuse, explicit feedback and limited retries to reduce repeated work.
- Can collect published leads concurrently from observed Greenhouse, Lever, and Ashby boards when the documented API and intended report use are permitted.
- Verifies original postings, merges syndicated duplicates, and preserves where each job was found.
- Reads a resume or detailed professional profile using available host tools.
- Compares job requirements with professional evidence and reports a 0–100 fit score, evidence coverage, eligibility, strengths, gaps, and application priority.
- Shows the first five verified companies as an interim update, then continues toward 20 distinct relevant companies with up to three recommended jobs each.
- Adds a company match rating, employee size, recent workforce trend, and the latest publicly reported layoff date. Workforce research starts after a company has a viable verified job; interim pending fields stay unknown.
- Delivers the compact HTML report by default for completed job searches, with a Markdown companion and optional CSV exports, including actual search coverage and access limitations.

Job scores measure documented fit. The company rating averages the available fit scores among its up to three recommended verified openings. These are not employer reputation ratings or hiring probabilities. Size, headcount trend, and layoffs are separate context and do not automatically change the score.

## Employer-first access

Restricted and unverified job boards are removed from the active resource list, example prompts and recommendations, including manual alternatives. The [policy audit](../references/source-policy-audit.md) retains their names and official evidence so future changes do not accidentally restore them. The skill uses supported search discovery within its allowed scope to find independent employer evidence, then checks openings through permitted career pages or documented APIs. Public visibility, low request volume and search-engine indexing do not establish permission to copy, process or retain content.

The skill does not scrape Google, Bing, DuckDuckGo or other consumer search results. Search API terms vary by product and plan, including rules for saved reports and conversation transcripts. Required attribution and application routes must survive report generation; employer links are preferred only when compatible with those conditions. Company research prioritizes permitted official reports, announcements, government notices and credible reporting. Missing data stays unknown.

Provider/method decisions are established during setup and reused while current; no separate approval is needed for each permitted job check. Unavailable routes are skipped while the search continues through allowed sources within the user's requested scope. A request limited to excluded sources does not authorize searching elsewhere. Finding a provider connector does not automatically restore an excluded source; adding one requires a deliberate policy revision and verified permission for the intended use.

This preserves the 20-company target, up to three recommendations per company, resume matching, company context and tables. Source restrictions can change the vacancies found or prevent reaching the target; the report states that honestly. This reduces risk but cannot certify legal compliance for every employer, account or future policy change. See the [routing policy and catalog](../references/job-sources.md).

The included public-API collector's network requests are limited to its three supported public listing APIs; the host agent follows the skill's source policy separately. The skill is not a firewall over all host tools. See the [live discovery workflow](../references/live-discovery.md) for the distinction.

Local triage, progress files, transcripts and reusable employer metadata still need compatible processing and storage rights. Completion events can contain job descriptions, so they have the same source-use limits as saved leads. A private registry holds only permitted minimal employer/board metadata and dated permission evidence, never a permanent permission grant or current-vacancy guarantee. Exclusions remain in force. See the [scoped review](../references/source-policy-audit.md#local-filtering-progress-and-registry-review).

## Public employer-board collection (optional advanced use)

After establishing that the API access and saved-report use are permitted, observe the board identifier in an actual employer career link and save a JSON list to `private/boards.json` with entries such as `{"provider": "greenhouse", "board": "OBSERVED_TOKEN"}`. `OBSERVED_TOKEN` is a placeholder, not an employer to query. Supported providers are `greenhouse`, `lever`, and `ashby`; Lever also supports `"region": "eu"` for observed European boards. No-key access is a technical property, not a blanket reuse license.

```sh
python3 scripts/discover_jobs.py --boards private/boards.json --output private/leads.json --keywords "customer success" onboarding support --workers 4
```

The collector requires Python 3.10+ and network access, with no third-party packages or API key. It uses four workers by default (configurable from 1–8); `--workers 1` runs sequentially. Legacy keywords filter downloaded public descriptions locally. Structured profile mode instead retains candidates and orders review without treating triage as a fit score. Its output contains **leads**, source timestamps, and failures; the agent verifies company identity, the full posting, application availability, and candidate eligibility before turning leads into recommendations. It does not discover all employers or submit applications. See [live-discovery.md](../references/live-discovery.md) for limits, output fields, and certificate troubleshooting.

For structured review, adapt the fictional [profile example](../examples/triage-profile.json) to the user's confirmed limits and save it as `private/profile.json`:

```sh
python3 scripts/discover_jobs.py --boards private/boards.json --output private/leads.json --profile private/profile.json --events private/events.jsonl --workers 4
```

Use either `--profile` or `--keywords`, never both. Profile mode retains uncertain and conflicting candidates for review; title and level preferences are not hard exclusions. Optional events expose completed boards before collection ends, but are still unverified leads and may contain duplicates. The host checks them before showing five verified employers and continues to the full target. The final leads file preserves stable input-board ordering. Both output files need compatible source-retention rights.

## Adaptive search state and explicit feedback

The [local search-state helper](../references/search-state.md) records bounded query outcomes, explicit feedback and minimal permitted employer/board metadata. For example:

```sh
python3 scripts/search_state.py init private/search-state.json --profile candidate --run run-01 --families development qa support
python3 scripts/search_state.py suggest private/search-state.json --slots 8 --exploration .25 --recent 3
```

The first command creates empty local state; it does not find jobs. After the host records permitted observations using the documented state contract, `suggest` allocates a batch across the allowed role families, including exploration. It records routes but does not allocate route-specific slots; the host chooses permitted routes using the source coverage ledger. Its output is a plan, not performed searches or a new candidate-fit score. Follow [search-state.md](../references/search-state.md) for registry rights, explicit-feedback scope, validation and updates. No new provider accounts or requests are made by this helper.

## Try the report generator

The included Python helper calculates scores from structured assessments and generates company-first Markdown tables from schema version 2. Version 1 job-only inputs continue to work. Python 3.10+ is sufficient; no third-party packages, API key, or network connection are needed for this helper.

```sh
python3 scripts/build_report.py examples/sample-input.json --output reports/sample-report.md --html reports/sample-report.html --csv reports/sample-report.csv --companies-csv reports/sample-companies.csv
python3 -m unittest discover -s tests -v
```

The agent first reads the resume, searches, verifies postings, and fills the JSON evidence. This separate report helper does not parse raw resumes or discover jobs. Include `search_sources` and per-job `discovered_via` for live searches. See the [input contract and report format](../references/report-format.md), [matching rubric](../references/resume-matching.md), and [search strategy](../references/search-strategy.md).

The skill includes `--html` by default for completed job-search reports; users do not need to request it separately. The flag remains optional when calling the CLI directly, and `--output` remains required for the Markdown companion. Honor explicit format choices; role or keyword planning alone does not trigger report generation. Use `--overwrite` for intentional replacement of existing outputs. The HTML uses the same validated input, derived scores, source evidence and actual company shortfall as the other formats. It starts with compact grouped job rows and **View job** links, with company research, scope and evidence kept in expandable sections. Version 1 remains job-only and does not invent company research fields.

The HTML is a self-contained local file with no external assets, automatic network requests or browser storage. Open it directly in a browser; company, job and evidence links visit their destinations only when you choose them. Exporting a report does not publish it, refresh vacancies or upload candidate information. Viewing an export does not update the search profile or record feedback; request refinements in the skill conversation. Source attribution, display and retention requirements still apply to the HTML; use a compatible rendering or omit incompatible source material as the report contract requires.

Search matches company, title or location. **Show postings** defaults to **Recommended** when version 2 has recommendations, otherwise **All postings**; other options cover review, blocked, unverified and closed records. **Reset** returns to that initial view. Report totals remain complete, with a separate visible-record count. Expand **Why this match / details**, company research or **Compare openings in a table** for more context. **Print** includes all records and comparison rows, regardless of filters, and expands disclosures before restoring their previous state. Without JavaScript, controls stay hidden, all records are visible and native disclosures still work. Version 1 omits the company overview and **Recommended** filter.

The fictional sample is available as [HTML](../examples/sample-report.html) and [Markdown](../examples/sample-report.md). It uses synthetic companies, candidate information and reserved example URLs; it is not a list of live vacancies or a completed 20-company search. GitHub shows HTML as source/download, so download it and open the saved file locally to see the rendered layout. The [sample search plan](../examples/sample-search-plan.md) demonstrates keyword expansion and related-role suggestions.

To customize the appearance, edit the CSS or layout in [assets/report-template.html](../assets/report-template.html), preserving its named placeholders and the markup needed by its controls. [scripts/render_html.py](../scripts/render_html.py) fills the template; each generated report includes its styles and script locally. The sample report is rendered output, not the template source. Change evidence in the report input and regenerate all formats so scores and sources stay consistent.

## Report contents

Markdown uses the order below; HTML puts job rows first and keeps research and evidence expandable.

| Table | Purpose |
| --- | --- |
| Company overview — first | Linked company names, derived match ratings, size, workforce trends, reported layoffs and up to three recommended job links |
| Jobs by company — second | Direct posting links, location, compensation, dates, job fit, eligibility and next action, grouped under each employer |
| Search keywords | Reuse grouped title, function, skill, industry, and location queries |
| Requirement evidence | See exactly which resume evidence supports each match and which details are unknown |
| Sources checked | See the actual source, method/query, date, observed results, verified count, and access limits |
| Leads and exclusions | Keep inaccessible, closed, or blocked results separate from active opportunities |

## Candidate privacy

Use synthetic information in repository examples and tests. Save personal resumes, extracted profiles, and generated search reports outside this repository or inside its ignored `private/` directory. The ignored `reports/` directory is intended for local output. Git ignore rules do not protect files you explicitly force-add or data copied into a tracked file.

The skill uses generalized keywords for web searches. It does not authorize uploading a resume to a job board, sending applications, or contacting employers. Those actions require the user's request.

Keep structured profiles, explicit feedback, registry metadata, query observations and progress files private too. Feedback affects only the scope the user stated; one dismissed job does not exclude an employer or create a new hard requirement. A registry entry must be checked for current employer identity, route and rights before reuse, and every job receives a fresh check for a new report.

## Evaluate speed and quality

Compare like-for-like runs using time to the first five verified employers, total time, requests, new unique viable employers, duplicate counts and unresolved evidence. Review missed relevant jobs as well as top results when evaluating triage. Label synthetic request benchmarks separately from live end-to-end research. More raw leads, fewer checks or an unfinished five-company preview do not establish improved quality or a completed 20-company search.

## Repository structure

```text
SKILL.md                      Agent instructions
agents/openai.yaml            Skill display metadata
references/                   Search, matching, and report guidance
scripts/build_report.py       Deterministic scoring and table export
scripts/render_html.py        HTML rendering from validated report evidence
scripts/discover_jobs.py      Public Greenhouse, Lever, and Ashby lead collection
scripts/triage_jobs.py        Local structured review signals for collected leads
scripts/search_state.py       Private query allocation, registry and explicit feedback
examples/                     Fictional input and reports
assets/                       Illustrated usage and report guides
assets/report-template.html   Reusable HTML layout, local styles and controls
docs/                         Detailed reader guides and examples
tests/                        Scoring, collection, failure handling, and export checks
```

To extend the skill, keep scoring changes synchronized with the rubric and tests. Add new role examples when they improve transferable search behavior rather than building a closed catalog of job titles.
