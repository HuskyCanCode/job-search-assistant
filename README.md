# Job Search Assistant

Find jobs from your resume or career goals, compare your fit, and get a report organized by company.

Use it in an AI assistant that supports skills, file reading and permitted live search. No Python commands are needed for normal use.

## Use the skill

### 1. Install once

Already installed? Skip to step 2. Otherwise, paste this into Codex:

```text
Use $skill-installer to install job-search-assistant from
https://github.com/HuskyCanCode/job-search-assistant.
SKILL.md is at the repository root. Preserve any existing installation changes.
```

This repository is private, so your GitHub account needs access. If the installed skill does not appear, restart Codex. [Installation help](docs/usage-guide.md#1-install-the-skill-once).

### 2. Start a search

Attach your resume or paste a professional summary. A resume is optional. Change the location and preferences in this example to yours:

```text
Use $job-search-assistant and my attached resume.
Find on-site jobs in the United States; I am open to relocation.
Suggest suitable roles and target 20 different companies.
Show the company overview first, then jobs grouped by company,
with direct job links, match scores and reusable search keywords.
```

Without a resume or detailed profile, remove “and my attached resume” and name the roles you want. The search can still run, with personal match ratings marked N/A.

### 3. Review and refine

Read the company overview, check each job's requirements, and open the posting when ready to apply. To narrow the results, reply:

> Focus on QA and application support. Keep my location preferences and show the five companies I should prioritize.

The skill does not submit applications or contact employers automatically.

<details>
<summary>See the illustrated walkthrough</summary>

![Six steps: install, share preferences, request a search, read the report, refine the shortlist, and open job links to apply yourself.](assets/getting-started.svg)

</details>

## What you get

| Report section | Includes |
| --- | --- |
| Company overview | Linked company names, **company size**, **match ratings**, workforce trends, latest reported layoffs, and up to **3 recommended job links** each |
| Jobs by company | Location, pay, resume fit, eligibility, gaps and application priority |
| Search details | Related keywords, sources checked, dates and limitations |

The target is **20 distinct companies**; fewer may qualify. Company ratings average the scored recommended jobs and measure resume fit, not hiring probability. Missing facts show **Unknown**; unsupported scores show **N/A**.

Searches use permitted discovery tools and employer sources. Direct LinkedIn automation is disabled.

## Sample report preview

[See the fictional sample tables](docs/report-preview.md) or the [illustrated report guide](assets/reading-report.svg).

## More help

- [Step-by-step guide, prompts and troubleshooting](docs/usage-guide.md)
- [Source access and privacy](docs/advanced.md#employer-first-access)
- [Optional scripts and exports](docs/advanced.md#public-employer-board-collection-optional-advanced-use)
