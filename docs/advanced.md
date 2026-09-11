# Advanced usage and reference

[Back to the README](../README.md) · [Usage guide](usage-guide.md)

The scripts below are optional. Run their commands from the **repository root**. Normal searches run through the skill in your conversation.

## What it does

- Refines a broad search into useful roles, filters, and reusable search queries.
- Suggests close, adjacent, and stretch roles based on transferable experience.
- Uses supported search tools and permitted employer sources, with a catalog that distinguishes manual resources from conditional feeds and APIs.
- Speeds discovery with parallel query batches, early deduplication, shared employer research, and limited retries of blocked sources.
- Can collect published leads concurrently from observed Greenhouse, Lever, and Ashby boards when the documented API and intended report use are permitted.
- Verifies original postings, merges syndicated duplicates, and preserves where each job was found.
- Reads a resume or detailed professional profile using available host tools.
- Compares job requirements with professional evidence and reports a 0–100 fit score, evidence coverage, eligibility, strengths, gaps, and application priority.
- Targets 20 distinct relevant companies by default, linking each company name to its official website and showing up to three recommended jobs before the detailed tables for that company.
- Adds a company match rating, employee size, recent workforce trend, and the latest publicly reported layoff date with sources and clear unknowns.
- Produces Markdown tables and optional CSV exports, with a source coverage table showing actual searches and access limitations.

Job scores measure documented fit. The company rating averages the available fit scores among its up to three recommended verified openings. These are not employer reputation ratings or hiring probabilities. Size, headcount trend, and layoffs are separate context and do not automatically change the score.

## Employer-first access

LinkedIn, Indeed, SimplyHired and the catalog's other restricted or unverified websites remain manual resources. Automated collection is disabled by default, including targeted indexed queries that would collect their content indirectly. The skill uses supported search discovery within its allowed scope to find independent employer evidence, then checks openings through permitted career pages or documented APIs. Public visibility, low request volume and search-engine indexing do not establish permission to copy, process or retain content.

The skill does not scrape Google, Bing, DuckDuckGo or other consumer search results. Search API terms vary by product and plan, including rules for saved reports and conversation transcripts. Required attribution and application routes must survive report generation; employer links are preferred only when compatible with those conditions. Company research prioritizes permitted official reports, announcements, government notices and credible reporting. Missing data stays unknown.

The [dated source-by-source audit](../references/source-policy-audit.md) links official policies and marks unresolved permissions. Provider/method decisions are established during setup and reused while current; no separate approval is needed for each permitted job check. Unavailable routes are skipped while the search continues through allowed sources. A provider's documented connector or feed is not automatically installed or covered by the included collector.

This preserves the 20-company target, up to three recommendations per company, resume matching, company context and tables. Source restrictions can change the vacancies found or prevent reaching the target; the report states that honestly. This reduces risk but cannot certify legal compliance for every employer, account or future policy change. See the [routing policy and catalog](../references/job-sources.md).

The included public-API collector does **not** search LinkedIn or Indeed. Its built-in network requests are limited to supported public listing APIs; the host agent follows the skill's source policy separately. The skill is not a firewall over all host tools. See the [live discovery workflow](../references/live-discovery.md) for the distinction.

## Public employer-board collection (optional advanced use)

After establishing that the API access and saved-report use are permitted, observe the board identifier in an actual employer career link and save a JSON list to `private/boards.json` with entries such as `{"provider": "greenhouse", "board": "OBSERVED_TOKEN"}`. `OBSERVED_TOKEN` is a placeholder, not an employer to query. Supported providers are `greenhouse`, `lever`, and `ashby`; Lever also supports `"region": "eu"` for observed European boards. No-key access is a technical property, not a blanket reuse license.

```sh
python3 scripts/discover_jobs.py --boards private/boards.json --output private/leads.json --keywords "customer success" onboarding support --workers 4
```

The collector requires Python 3.10+ and network access, with no third-party packages or API key. It uses four workers by default (configurable from 1–8); `--workers 1` runs sequentially. Keywords filter downloaded public descriptions locally. Its output contains **leads**, source timestamps, and failures; the agent verifies company identity, the full posting, application availability, and candidate eligibility before turning leads into recommendations. It does not discover all employers or submit applications. See [live-discovery.md](../references/live-discovery.md) for limits, output fields, and certificate troubleshooting.

## Try the report generator

The included Python helper calculates scores from structured assessments and generates company-first tables from schema version 2. Version 1 job-only inputs continue to work. Python 3.10+ is sufficient; no third-party packages, API key, or network connection are needed for this helper.

```sh
python3 scripts/build_report.py examples/sample-input.json --output reports/sample-report.md --csv reports/sample-report.csv --companies-csv reports/sample-companies.csv
python3 -m unittest discover -s tests -v
```

The agent first reads the resume, searches, verifies postings, and fills the JSON evidence. This separate report helper does not parse raw resumes or discover jobs. Include `search_sources` and per-job `discovered_via` for live searches. See the [input contract and report format](../references/report-format.md), [matching rubric](../references/resume-matching.md), and [search strategy](../references/search-strategy.md).

The [sample report](../examples/sample-report.md) uses fictional companies, candidate information, and reserved example URLs. It demonstrates the output format; it is not a list of live vacancies. The [sample search plan](../examples/sample-search-plan.md) demonstrates keyword expansion and related-role suggestions.

## Report contents

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

## Repository structure

```text
SKILL.md                      Agent instructions
agents/openai.yaml            Skill display metadata
references/                   Search, matching, and report guidance
scripts/build_report.py       Deterministic scoring and table export
scripts/discover_jobs.py      Public Greenhouse, Lever, and Ashby lead collection
examples/                     Fictional input and reports
assets/                       Illustrated usage and report guides
docs/                         Detailed reader guides and examples
tests/                        Scoring, collection, failure handling, and export checks
```

To extend the skill, keep scoring changes synchronized with the rubric and tests. Add new role examples when they improve transferable search behavior rather than building a closed catalog of job titles.
