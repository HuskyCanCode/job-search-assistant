# Job Search Assistant

Turn a resume or career goal into a current, company-by-company job report with direct posting links and transparent match scores.

The skill searches permitted employer sources, recommends up to three jobs per company, compares each description with the candidate's experience, and creates a private illustrated HTML report with a Markdown companion.

## Quick start

### 1. Install once

In Codex chat, copy and send:

```text
Use $skill-installer to install job-search-assistant from
https://github.com/HuskyCanCode/job-search-assistant.
SKILL.md is at the repository root. Preserve any existing installation changes.
```

Or install from a terminal:

```sh
# Codex
mkdir -p ~/.codex/skills
git clone git@github.com:HuskyCanCode/job-search-assistant.git ~/.codex/skills/job-search-assistant

# Claude Code
mkdir -p ~/.claude/skills
git clone git@github.com:HuskyCanCode/job-search-assistant.git ~/.claude/skills/job-search-assistant
```

This is a private repository, so GitHub access is required. Use the HTTPS repository URL if your GitHub account is configured for HTTPS instead of SSH. Restart Codex if the newly installed skill does not appear.

### 2. Run a search

Attach a resume, then copy and adjust this prompt:

```text
Use $job-search-assistant with my attached resume.
Find frontend jobs in the United States. I prefer on-site work,
I am open to relocation, and I do not need visa sponsorship.
Target 20 companies and create the HTML report.
```

A resume is optional. You can instead describe your experience, target roles, location, work arrangement, and other limits. Without enough professional evidence, personal match scores appear as **N/A**.

### 3. Open the report

The HTML report puts recommended jobs first. Each company name and job title is a link. Expand a company to review its size, workforce trend, recent reported layoffs, resume evidence, gaps, and source details.

| Report section | What it shows |
| --- | --- |
| Recommended jobs | Direct job links, location, pay, fit score, eligibility and next action |
| Company overview | Linked company name, company match, size, workforce trend and latest reported layoff |
| Full evidence | Requirement-by-requirement resume comparison, reusable search keywords and sources checked |

[Open the fictional sample report](examples/sample-report.html) or see [preview help](docs/report-preview.md).

<details open>
<summary>See the illustrated walkthrough</summary>

![Six steps: install, share preferences, request a search, read the report, refine the shortlist, and open job links to apply yourself.](assets/getting-started.svg)

</details>

## How results are selected

- The default target is **20 distinct companies**, with up to **3 recommended jobs per company**. The report shows the actual count when fewer suitable, current openings can be verified.
- A job fit score measures documented alignment between the job description and the candidate's evidence. It is not a probability of receiving an interview or offer.
- A company match is the average fit of that company's scored recommendations. It is not a reputation, stability, or employer-quality rating.
- Unknown facts remain **Unknown**. Unsupported scores remain **N/A**.
- Searches use employer pages and other routes whose policies cover the method and report. LinkedIn, Indeed, and similarly restricted or unresolved sources are excluded rather than scraped or reconstructed.
- The skill creates reports and recommendations. It does not submit applications, contact employers, create accounts, or schedule recurring searches unless the user explicitly requests those actions.

To refine a result, reply with a simple instruction such as:

> Focus on the five strongest frontend roles, keep my location preferences, and explain which resume changes would improve each match.

## More help

- [Detailed usage guide](docs/usage-guide.md)
- [Active job sources](references/job-sources.md)
- [Source-policy audit](references/source-policy-audit.md)
- [Privacy and advanced options](docs/advanced.md)
