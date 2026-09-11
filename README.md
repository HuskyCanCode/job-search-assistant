# Job Search Assistant

Find jobs from your resume or career goals, compare your fit, and get a report organized by company.

Use it in an AI assistant that supports skills, file reading and permitted live search. No Python commands are needed for normal use.

## Use the skill

### 1. Install once

Already installed? Skip to step 2. Otherwise, use one of these copy-and-paste options.

**Codex chat**

```text
Use $skill-installer to install job-search-assistant from
https://github.com/HuskyCanCode/job-search-assistant.
SKILL.md is at the repository root. Preserve any existing installation changes.
```

**Codex terminal (macOS/Linux)**

```sh
mkdir -p ~/.codex/skills
git clone git@github.com:HuskyCanCode/job-search-assistant.git ~/.codex/skills/job-search-assistant
```

**Claude Code terminal (macOS/Linux)**

```sh
mkdir -p ~/.claude/skills
git clone git@github.com:HuskyCanCode/job-search-assistant.git ~/.claude/skills/job-search-assistant
```

After either terminal command, invoke `$job-search-assistant` in Codex or `/job-search-assistant` in Claude Code. A clone stops if its destination already exists, so it does not overwrite an existing installation. This private repository requires GitHub access and an existing SSH key (use the HTTPS repository URL if that is how your GitHub authentication is configured). If a newly installed skill does not appear in Codex, restart Codex; Claude Code watches personal skill folders and can pick up changes in the current session. [Installation details and update instructions](docs/usage-guide.md#1-install-the-skill-once).

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

Review the jobs and company details, check each job's requirements, and open the posting when ready to apply. To narrow the results, reply:

> Focus on QA and application support. Keep my location preferences and show the five companies I should prioritize.

For compact job rows with expandable company details, ask: “Save this as an HTML report I can open locally.” The skill does not submit applications or contact employers automatically.

<details open>
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

The skill prioritizes relevant openings, adjusts searches using verified results, and can show the first five verified companies while continuing the full search. Tell it “more like this” or give an explicit exclusion to refine the next results.

Searches use permitted employer sources and documented APIs or feeds within their terms. Restricted and unverified job boards are excluded from the resource list and recommendations. See the [active sources](references/job-sources.md) and [policy audit](references/source-policy-audit.md).

## Sample report preview

Download the [fictional HTML sample](examples/sample-report.html) and open it in your browser. GitHub shows the file's source; see [preview help and sample tables](docs/report-preview.md) or the [illustrated report guide](assets/reading-report.svg).

## More help

- [Step-by-step guide, prompts and troubleshooting](docs/usage-guide.md)
- [Source access and privacy](docs/advanced.md#employer-first-access)
- [Optional scripts and exports](docs/advanced.md#public-employer-board-collection-optional-advanced-use)
