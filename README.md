# Job Search Assistant

A reusable agent skill that turns a career goal or uploaded resume into better searches and a linked, evidence-based job comparison table.

## What it does

- Refines a broad search into useful roles, filters, and reusable search queries.
- Suggests close, adjacent, and stretch roles based on transferable experience.
- Uses the host agent's web tools to find and verify job posts.
- Reads a resume or detailed professional profile using available host tools.
- Compares job requirements with professional evidence and reports a 0–100 fit score, evidence coverage, eligibility, strengths, gaps, and application priority.
- Produces Markdown tables and optional CSV exports.

The score measures documented fit. It does not predict hiring probability. The report explains what is known, what needs clarification, and where applying is most worthwhile.

## Use the skill

This repository's root is the skill folder. Place it in your agent's supported skills directory as `job-search-assistant`. In Codex, a user skill can live at `$CODEX_HOME/skills/job-search-assistant`, with `~/.codex/skills/job-search-assistant` as the default location. If a folder with that name already exists, review and preserve its contents before replacing it.

Invoke the skill and attach a resume to the conversation if you want resume-based matching:

> Use $job-search-assistant. Find customer success or operations roles in Toronto, hybrid or remote within Canada. Use my attached resume, suggest related titles and search keywords, and return 10 verified job posts in a table with fit scores, evidence, gaps, and application priorities.

Without a resume:

> Use $job-search-assistant. Help me explore entry-level logistics roles in Chicago. Suggest related roles and keywords, then find current openings with direct links. Mark personal fit as N/A until I provide my background.

For a career change:

> Use $job-search-assistant. I want to move from hospitality into office operations. Use my resume to identify transferable skills, compare close and stretch roles, and show which job requirements need stronger evidence.

The host needs live web search or browser access to verify current openings, and file-reading capability for the uploaded format. A scanned PDF may need OCR. If either capability is unavailable, the skill explains the limitation and can still plan searches or compare supplied job descriptions. There is no bundled scraper, background monitor, account sign-in service, or application submission service.

## Try the report generator

The included Python helper calculates scores from structured assessments and generates job tables. Python 3.10+ is sufficient; no third-party packages, API key, or network connection are needed for this helper.

```sh
python3 scripts/build_report.py examples/sample-input.json --output reports/sample-report.md --csv reports/sample-report.csv
python3 -m unittest discover -s tests -v
```

The agent first reads the resume, searches, verifies postings, and fills the JSON evidence. The helper does not parse raw resumes or discover jobs. See the [input contract and report format](references/report-format.md), [matching rubric](references/resume-matching.md), and [search strategy](references/search-strategy.md).

The [sample report](examples/sample-report.md) uses fictional companies, candidate information, and reserved example URLs. It demonstrates the output format; it is not a list of live vacancies. The [sample search plan](examples/sample-search-plan.md) demonstrates keyword expansion and related-role suggestions.

## Report contents

| Table | Purpose |
| --- | --- |
| Job shortlist | Compare direct posting links, location, compensation, dates, fit, eligibility, and next action |
| Search keywords | Reuse grouped title, function, skill, industry, and location queries |
| Requirement evidence | See exactly which resume evidence supports each match and which details are unknown |
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
examples/                     Fictional input and reports
tests/                        Scoring and output checks
```

To extend the skill, keep scoring changes synchronized with the rubric and tests. Add new role examples when they improve transferable search behavior rather than building a closed catalog of job titles.
