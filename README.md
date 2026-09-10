# Job Search Assistant

A reusable agent skill that automatically searches online job resources from a career goal or uploaded resume and returns a linked, evidence-based comparison table.

## What it does

- Refines a broad search into useful roles, filters, and reusable search queries.
- Suggests close, adjacent, and stretch roles based on transferable experience.
- Searches LinkedIn, Indeed, employer career pages, and relevant specialist, remote, regional, and public-sector sources using the host agent's live web tools.
- Collects published leads from observed Greenhouse, Lever, and Ashby employer boards through documented public APIs.
- Verifies original postings, merges syndicated duplicates, and preserves where each job was found.
- Reads a resume or detailed professional profile using available host tools.
- Compares job requirements with professional evidence and reports a 0–100 fit score, evidence coverage, eligibility, strengths, gaps, and application priority.
- Produces Markdown tables and optional CSV exports, with a source coverage table showing actual searches and access limitations.

The score measures documented fit. It does not predict hiring probability. The report explains what is known, what needs clarification, and where applying is most worthwhile.

## Use the skill

This repository's root is the skill folder. Place it in your agent's supported skills directory as `job-search-assistant`. In Codex, a user skill can live at `$CODEX_HOME/skills/job-search-assistant`, with `~/.codex/skills/job-search-assistant` as the default location. If a folder with that name already exists, review and preserve its contents before replacing it.

Invoke the skill and attach a resume to the conversation if you want resume-based matching:

> Use $job-search-assistant. Find customer success or operations roles in Toronto, hybrid or remote within Canada. Use my attached resume, suggest related titles and search keywords, and return 10 verified job posts in a table with fit scores, evidence, gaps, and application priorities.

You can also specify sources:

> Use $job-search-assistant. Search LinkedIn, Indeed, Wellfound, relevant remote boards, and employer career sites for junior frontend or software support jobs in New York. Include related job titles, deduplicate results, and show where each job was found and which sources were limited.

You do not have to name every board: the skill chooses sources based on the role and country. A request to find jobs runs the search in the current conversation. An older resume or missing recent projects changes the recommended level and evidence confidence; the skill still searches for suitable openings. Background searches require a separately requested schedule.

Without a resume:

> Use $job-search-assistant. Help me explore entry-level logistics roles in Chicago. Suggest related roles and keywords, then find current openings with direct links. Mark personal fit as N/A until I provide my background.

For a career change:

> Use $job-search-assistant. I want to move from hospitality into office operations. Use my resume to identify transferable skills, compare close and stretch roles, and show which job requirements need stronger evidence.

The host needs live web search or browser access to discover and verify current openings, and file-reading capability for the uploaded format. A scanned PDF may need OCR. If a capability is unavailable, the skill explains the limitation and can still plan searches or compare supplied descriptions.

LinkedIn and other boards may limit public access. The skill can use indexed discovery and original employer pages, labeling that coverage accurately; it cannot guarantee every posting or bypass sign-in restrictions. The included public-API collector does **not** search LinkedIn or Indeed. See the [source catalog](references/job-sources.md) and [live discovery workflow](references/live-discovery.md) for how the tools work together.

## Public employer-board collection

After observing the board identifier in an actual employer career link, save a JSON list to `private/boards.json` with entries such as `{"provider": "greenhouse", "board": "OBSERVED_TOKEN"}`. `OBSERVED_TOKEN` is a placeholder, not an employer to query. Supported providers are `greenhouse`, `lever`, and `ashby`; Lever also supports `"region": "eu"` for observed European boards.

```sh
python3 scripts/discover_jobs.py --boards private/boards.json --output private/leads.json --keywords "customer success" onboarding support
```

The collector requires Python 3.10+ and network access, with no third-party packages or API key. Keywords filter downloaded public descriptions locally. Its output contains **leads**, source timestamps, and failures; the agent verifies company identity, the full posting, application availability, and candidate eligibility before turning leads into recommendations. It does not discover all employers or submit applications. See [live-discovery.md](references/live-discovery.md) for limits, output fields, and certificate troubleshooting.

## Try the report generator

The included Python helper calculates scores from structured assessments and generates job tables. Python 3.10+ is sufficient; no third-party packages, API key, or network connection are needed for this helper.

```sh
python3 scripts/build_report.py examples/sample-input.json --output reports/sample-report.md --csv reports/sample-report.csv
python3 -m unittest discover -s tests -v
```

The agent first reads the resume, searches, verifies postings, and fills the JSON evidence. This separate report helper does not parse raw resumes or discover jobs. Include `search_sources` and per-job `discovered_via` for live searches. See the [input contract and report format](references/report-format.md), [matching rubric](references/resume-matching.md), and [search strategy](references/search-strategy.md).

The [sample report](examples/sample-report.md) uses fictional companies, candidate information, and reserved example URLs. It demonstrates the output format; it is not a list of live vacancies. The [sample search plan](examples/sample-search-plan.md) demonstrates keyword expansion and related-role suggestions.

## Report contents

| Table | Purpose |
| --- | --- |
| Job shortlist | Compare direct posting links, location, compensation, dates, fit, eligibility, and next action |
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
tests/                        Scoring, collection, failure handling, and export checks
```

To extend the skill, keep scoring changes synchronized with the rubric and tests. Add new role examples when they improve transferable search behavior rather than building a closed catalog of job titles.
