# Job Search Assistant

A reusable agent skill that searches online jobs from a career goal or resume and organizes the results by company, with job recommendations and sourced company context.

[Start here](#use-the-skill) · [Example prompts](#more-prompts-to-try) · [Sample report](#sample-report-preview) · [Troubleshooting](#if-something-does-not-work) · [Source access](#employer-first-access)

## Use the skill

Follow these six steps in your agent's conversation. You do not need to run Python commands for normal use. The agent needs to support skills, read your supplied files, and have an authorized way to search and verify current jobs.

![Six steps: install the skill, share an optional resume and preferences, send a search request, read the report, refine the shortlist, and open job links to apply yourself.](assets/getting-started.svg)

### 1. Install the skill once

Already installed? Go to step 2. For a first installation in Codex, copy this into a conversation:

```text
Use $skill-installer to install job-search-assistant from
https://github.com/HuskyCanCode/job-search-assistant.
The skill is at the repository root, where SKILL.md is located.
If it is already installed, tell me where it is and preserve existing changes.
```

This repository is private, so your GitHub account must have access. Use your existing authenticated connection; do not paste passwords or access tokens into a prompt. Other users need repository access from the owner before they can install it.

The installer reports the installation location. In your next message, ask to use `$job-search-assistant`; Codex normally discovers new skills automatically. If it does not appear, restart Codex. The exact picker depends on the product: Codex CLI and IDE support `$` or `/skills`, while ChatGPT uses `@` to select an available skill. This standalone repository is not a published plugin. See the [official skill documentation](https://learn.chatgpt.com/docs/build-skills) for supported products and local setup.

For manual installation, copy the **whole repository folder**, including `SKILL.md`, `references/`, `scripts/`, and `assets/`, into a skill location supported by your agent and name it `job-search-assistant`. Use your agent's documented location or the installer's reported destination; avoid creating duplicate installations or overwriting local changes.

### 2. Share your background and preferences

Attach a readable PDF or DOCX resume if your app supports attachments, provide a local file the agent can read, or paste a professional summary. A resume is optional. Include your target country and preferred work arrangement so the agent can search the right market.

| Tell the skill | Example | When needed |
| --- | --- | --- |
| Country and locations | United States; open to relocation | Needed to define the search market |
| Work arrangement | On-site, hybrid, or remote | Needed; remote jobs can still restrict where you live |
| Roles or direction | Junior developer, QA, or technical support | Optional if you want roles suggested from your background |
| Experience | Resume, or relevant work, skills and projects | Needed for evidence-based personal match scores |
| Employment and salary | Full-time; prefer USD 60,000+ annual base pay | Optional; say whether it is a preference or a firm minimum |
| Hard limits | No travel; sponsorship required | Include any that apply; the skill will not infer them |

You can remove contact details before sharing your resume. Search queries use general skills, role titles and locations; using this skill does not authorize uploading your resume to job boards. Without a resume or sufficiently detailed profile, jobs can still be found, but personal and company match ratings remain **N/A**.

### 3. Send your first search request

Here is a complete example. Change the location and preferences to yours, and attach your resume if you refer to one:

```text
Use $job-search-assistant and my attached resume.

Find jobs in the United States. I prefer on-site work and am open to relocation.
Suggest suitable roles based on my experience, including related job titles.
I am looking for full-time work; salary is flexible.

Target 20 different companies. Show the company overview first, with:
- Each company name linked to its official website
- Company size and a resume-based match rating
- Recent workforce growth or decline and the latest reported layoff
- Up to three recommended job links per company

Then show job details grouped by company, with resume matches, evidence coverage,
eligibility, gaps and application priority. Include reusable search keywords.
Use permitted search tools and employer sources, and explain missing information
or any shortfall against the company target.
```

**What happens next:** the skill reads your background, expands role titles, searches permitted sources, checks original postings, compares requirements and researches companies. If an essential location or work preference is missing, it asks a short question and continues useful preparation. You do not need to choose every job board or approve each permitted read-only search.

Discovery uses parallel query batches, early duplicate removal and shared company research. Actual completion time depends on access and evidence; there is no fixed runtime. The [fast search workflow](references/search-strategy.md#fast-search-workflow) explains how it avoids repeated work.

### 4. Read the company overview, then the jobs

![Illustrated fictional report showing the company website, employee size, match rating, workforce trend, layoff context and recommended job links, with explanations of ratings and unknown values.](assets/reading-report.svg)

Start with companies that interest you, then read their detailed job rows. The [sample report preview](#sample-report-preview) shows the actual table layout.

| What you see | How to use it |
| --- | --- |
| Company size | Employee count or range, with date and scope; this is separate from fit |
| Company match rating | Average of the scored jobs among that company's up to three recommendations; not reputation or hiring odds |
| Job match and evidence coverage | Match shows demonstrated alignment; coverage shows how much of the assessment has known evidence, including known gaps |
| Priority and eligibility | Read these before deciding where to apply. **Review evidence** means the assessment needs checking; **Clarify eligibility** means a material requirement is unknown. A high score does not resolve either issue. |
| Workforce trend and layoffs | Read the dates and sources; employee growth is not inferred from job counts, and a layoff announcement date differs from its effective date |
| Unknown, N/A or provisional | Unknown means a fact is missing; N/A means a score cannot be supported; provisional means the assessment has stated limitations |
| Sources and check dates | See what was actually searched and how recently each posting was checked |

**20 companies means 20 distinct employers**, with up to three suitable recommended jobs each. It does not guarantee 60 jobs. When fewer employers can be substantiated, the report explains the shortfall. Closed, inaccessible or confirmed-ineligible listings do not fill the recommendation quota. “No layoff report found” describes only the sources and period checked.

### 5. Refine or save the shortlist

Reply in the same conversation so the skill can reuse your confirmed preferences. For example:

```text
Keep my location and work preferences. Focus the next search on QA and application
support roles. Exclude internships and roles requiring current student status.
Keep the 20-company target and explain the most important gaps in my best matches.
```

For a deliberately smaller follow-up:

```text
From this report, show only the five companies I should prioritize.
Explain why each one fits and which requirements I should confirm first.
```

For files you can save:

```text
Save this report as Markdown, plus separate company and job CSV files.
Keep my resume and personal report outside the distributable skill repository.
```

### 6. Open a job link and apply yourself

Select a verified job link, check that the employer is still accepting applications, and review the requirements before submitting. Company-name links open the official company site; job-title links open the specific posting. The report does not submit applications or contact employers.

You can ask for preparation help without sending anything. Replace the example title with an actual title or job link from your report:

```text
Compare my resume with the QA Analyst posting in the report.
Suggest truthful resume edits and a short application checklist for me to review.
Do not submit an application or contact the employer.
```

## More prompts to try

Copy one and replace its locations, roles and constraints with your own.

**No resume yet**

```text
Use $job-search-assistant. Find entry-level logistics jobs in Chicago, United States.
I want on-site, full-time work. Include related titles and target 20 companies.
I have not provided my background, so keep personal and company fit ratings N/A.
```

**Unsure which roles fit**

```text
Use $job-search-assistant and my attached resume. Suggest close, adjacent and stretch
roles, then search for suitable openings in the United States. I am open to on-site
work and relocation. Target 20 qualifying employers and show the company-first report.
```

**Explore roles before searching**

```text
Use $job-search-assistant with my resume. For now, suggest roles and reusable keywords
only. Explain how my experience transfers; do not search for live openings yet.
```

**Remote work or a career change**

```text
Use $job-search-assistant. I want to move from hospitality into customer operations.
Use my resume to find remote jobs that allow me to work from Canada. Target 20
companies, compare transferable skills, and flag location or eligibility restrictions.
```

**Include particular job resources**

```text
Use $job-search-assistant. Find junior frontend and software support jobs in New York,
United States, with on-site or hybrid work. Include permitted indexed discovery for
LinkedIn, Indeed and Wellfound, then verify original employer postings. Show which
sources were searched or limited, and keep restricted direct automation disabled.
```

A search runs when requested in the conversation. Background repetition requires a separately requested schedule and a host that supports scheduling; installing the skill alone does not start recurring searches.

## If something does not work

| Situation | What to do next |
| --- | --- |
| The skill is not found | Confirm installation completed and the folder contains `SKILL.md`; mention the skill in a new message. If needed, restart the app and check its documented skill locations. |
| GitHub installation is denied | Confirm your account has access to this private repository and reconnect using your normal authentication flow. Do not share secrets in chat. |
| The resume cannot be read | Supply a text-based PDF, DOCX, or pasted professional summary. A scanned image may need OCR that the host does not have. |
| Only a plan is returned | Check whether a permitted live-search and verification route is available. Without one, current openings cannot be verified; you can still compare supplied job descriptions. |
| Ratings show N/A | Supply enough professional evidence for matching and a complete, verifiable job description. Do not ask the skill to guess a score. |
| Fewer than 20 companies appear | Read the search limits. Broaden role titles, locations or other preferences you are willing to change; keep firm constraints intact. |
| A LinkedIn-only listing cannot be verified | Review it manually or ask for an equivalent employer posting. Restricted direct access stays disabled. |
| A formerly open job has closed | Ask for a fresh check and replacement openings; an earlier check is not a guarantee of current availability. |

## What it does

- Refines a broad search into useful roles, filters, and reusable search queries.
- Suggests close, adjacent, and stretch roles based on transferable experience.
- Uses authorized search tools and employer sources, with a discovery catalog covering LinkedIn, Indeed, ZipRecruiter, Built In, Y Combinator Jobs, Wellfound, HiringCafe, SimplyHired, Lensa, and Teal through permitted routes.
- Speeds discovery with parallel query batches, early deduplication, shared employer research, and limited retries of blocked sources.
- Collects published leads concurrently from observed Greenhouse, Lever, and Ashby employer boards through documented public APIs.
- Verifies original postings, merges syndicated duplicates, and preserves where each job was found.
- Reads a resume or detailed professional profile using available host tools.
- Compares job requirements with professional evidence and reports a 0–100 fit score, evidence coverage, eligibility, strengths, gaps, and application priority.
- Targets 20 distinct relevant companies by default, linking each company name to its official website and showing up to three recommended jobs before the detailed tables for that company.
- Adds a company match rating, employee size, recent workforce trend, and the latest publicly reported layoff date with sources and clear unknowns.
- Produces Markdown tables and optional CSV exports, with a source coverage table showing actual searches and access limitations.

Job scores measure documented fit. The company rating averages the available fit scores among its up to three recommended verified openings. These are not employer reputation ratings or hiring probabilities. Size, headcount trend, and layoffs are separate context and do not automatically change the score.

## Sample report preview

**Fictional example — no live search was performed.** This shortened preview shows two companies and six jobs; a full search targets **20 different employers**. Every company, job, salary, score, research finding and `example.com` link below is illustrative. The links demonstrate where official company websites, job posts and evidence sources appear in a real report.

Sample scope: United States, on-site, open to relocation. Illustrative check date: September 10, 2026. This preview assumes a fictional candidate profile, complete job descriptions, open applications and met eligibility constraints for all six roles. A real report establishes those facts before assigning recommendations.

### Company overview — shown first

| Company / official website | Company size | Company match rating | Recent workforce trend | Latest publicly reported layoff | Top 3 recommended jobs |
| --- | --- | --- | --- | --- | --- |
| [Example Tech](https://example.com/company-a) | 500 employees, company-wide; reported June 30, 2026 ([sample source](https://example.com/company-a/workforce)) | **80/100** · 3 scored jobs · 90% mean evidence coverage | +5% from June 30, 2025 to June 30, 2026 ([sample comparison](https://example.com/company-a/workforce-trend)) | May 12, 2026 — announcement date; latest found in the simulated review ([sample review](https://example.com/company-a/layoff-review)) | 1. [Junior Developer](https://example.com/jobs/a1)<br>2. [QA Analyst](https://example.com/jobs/a2)<br>3. [Application Support](https://example.com/jobs/a3) |
| [Example Services](https://example.com/company-b) | 1,000–2,000 employees, company-wide; range as of June 30, 2026 ([sample source](https://example.com/company-b/workforce)) | **72/100** · 3 scored jobs · 86.7% mean evidence coverage | **Unknown** — no comparable dated figures | No report found in the simulated sources and period checked ([sample review](https://example.com/company-b/layoff-review)); this does not establish that no layoffs occurred | 1. [Technical Support](https://example.com/jobs/b1)<br>2. [Implementation Associate](https://example.com/jobs/b2)<br>3. [Customer Success Associate](https://example.com/jobs/b3) |

Both fictional layoff reviews cover September 10, 2024 through September 10, 2026, plus a broader-history check. Real reports identify the actual sources, event scope and search window. Unknown company size appears as **Unknown**; a company with no scored recommendations shows **N/A** for its rating. Limited evidence or unknown eligibility can make a rating provisional.

### Jobs at Example Tech

All locations below are on-site; pay is annual base salary in USD. These are fictional full-time openings; posting dates are unknown, and the illustrative check date is September 10, 2026. In a real report, the short job-link identifiers are replaced by observed posting URLs and requisition IDs where available.

| Job | Location | Annual base pay (USD) | Resume match / evidence coverage | Eligibility | Priority | Matching evidence, gaps and next action |
| --- | --- | --- | --- | --- | --- | --- |
| [Junior Developer](https://example.com/jobs/a1) | Austin, TX | $65,000–$80,000 | **85/100** / 95% | Met | High | Web projects support the match; recent production experience is unclear. Add a truthful project example to the application. |
| [QA Analyst](https://example.com/jobs/a2) | Raleigh, NC | $55,000–$70,000 | **80/100** / 90% | Met | High | Technical foundation fits; formal testing experience is unclear. Describe a concrete debugging or test case. |
| [Application Support](https://example.com/jobs/a3) | Columbus, OH | Not listed | **75/100** / 85% | Met | Medium | Customer service and technical experience transfer; troubleshooting depth is unclear. Prepare a relevant support example. |

### Jobs at Example Services

| Job | Location | Annual base pay (USD) | Resume match / evidence coverage | Eligibility | Priority | Matching evidence, gaps and next action |
| --- | --- | --- | --- | --- | --- | --- |
| [Technical Support](https://example.com/jobs/b1) | Phoenix, AZ | $50,000–$65,000 | **78/100** / 90% | Met | Medium | Customer-facing experience fits; ticketing-tool experience is unclear. Confirm relevant tools and describe a resolved customer issue. |
| [Implementation Associate](https://example.com/jobs/b2) | Dallas, TX | Not listed | **72/100** / 85% | Met | Medium | Business and technology experience transfer; implementation experience is unclear. Highlight a relevant setup or handoff example. |
| [Customer Success Associate](https://example.com/jobs/b3) | Atlanta, GA | $48,000–$60,000 | **66/100** / 85% | Met | Medium | Sales experience transfers; software account-management experience is missing. Emphasize truthful customer follow-up achievements. |

The company ratings average the three displayed job scores: `(85 + 80 + 75) / 3 = 80` and `(78 + 72 + 66) / 3 = 72`. Evidence coverage measures how much of the weighted criteria has known evidence, including known gaps; it is separate from match strength. Priorities follow the [matching rules](references/report-format.md#score-coverage-and-priority), rather than predicting an interview or offer. The preview's illustrative scores are not assessments of a real candidate.

### Suggested search keywords

| Role family | Example reusable query |
| --- | --- |
| Development | `("junior developer" OR "software developer I") "United States" onsite` |
| Quality assurance | `("QA analyst" OR "manual tester") "entry level" "United States"` |
| Support | `("application support" OR "technical support specialist") "United States" onsite` |

Execute queries through an authorized search integration and verify originals through permitted employer sources. The full report also includes requirement-by-requirement evidence, dates, search coverage, and separate unverified or excluded leads. It states how many companies qualify and explains any shortfall; this two-company preview does not fulfill the 20-company target. The separate [complete fictional report](examples/sample-report.md) uses four companies and a Canada-based scenario to demonstrate those additional tables. See the [report contract](references/report-format.md) for the full field definitions.

## Employer-first access

Direct automated LinkedIn job, company and member browsing is disabled in the skill workflow. It uses authorized search discovery to find employers, then verifies openings through permitted employer career pages or documented public job APIs. LinkedIn-only leads can remain for manual review; they are not represented as verified openings. The same permission checks apply to other boards. Public visibility and search-engine indexing do not themselves authorize automated access or copying.

The skill does not replace LinkedIn automation with scraping Google results. It uses an authorized search integration under that provider's access and storage terms, keeps reports to concise job facts and comparisons, and prefers direct employer application links. Company size and workforce research prioritize official reports, announcements, government notices and credible reporting. Missing data stays unknown.

This preserves the 20-company target, up to three recommendations per company, resume matching, company context and table exports. Source restrictions can change the actual vacancies found or prevent reaching the target; the report states that honestly. This is a risk-reduction strategy, not legal clearance. See the [source access policy and catalog](references/job-sources.md).

The included public-API collector does **not** search LinkedIn or Indeed. Its built-in network requests are limited to supported public listing APIs; the host agent follows the skill's source policy separately. The skill is not a firewall over all host tools. See the [live discovery workflow](references/live-discovery.md) for the distinction.

## Public employer-board collection (optional advanced use)

After observing the board identifier in an actual employer career link, save a JSON list to `private/boards.json` with entries such as `{"provider": "greenhouse", "board": "OBSERVED_TOKEN"}`. `OBSERVED_TOKEN` is a placeholder, not an employer to query. Supported providers are `greenhouse`, `lever`, and `ashby`; Lever also supports `"region": "eu"` for observed European boards.

```sh
python3 scripts/discover_jobs.py --boards private/boards.json --output private/leads.json --keywords "customer success" onboarding support --workers 4
```

The collector requires Python 3.10+ and network access, with no third-party packages or API key. It uses four workers by default (configurable from 1–8); `--workers 1` runs sequentially. Keywords filter downloaded public descriptions locally. Its output contains **leads**, source timestamps, and failures; the agent verifies company identity, the full posting, application availability, and candidate eligibility before turning leads into recommendations. It does not discover all employers or submit applications. See [live-discovery.md](references/live-discovery.md) for limits, output fields, and certificate troubleshooting.

## Try the report generator

The included Python helper calculates scores from structured assessments and generates company-first tables from schema version 2. Version 1 job-only inputs continue to work. Python 3.10+ is sufficient; no third-party packages, API key, or network connection are needed for this helper.

```sh
python3 scripts/build_report.py examples/sample-input.json --output reports/sample-report.md --csv reports/sample-report.csv --companies-csv reports/sample-companies.csv
python3 -m unittest discover -s tests -v
```

The agent first reads the resume, searches, verifies postings, and fills the JSON evidence. This separate report helper does not parse raw resumes or discover jobs. Include `search_sources` and per-job `discovered_via` for live searches. See the [input contract and report format](references/report-format.md), [matching rubric](references/resume-matching.md), and [search strategy](references/search-strategy.md).

The [sample report](examples/sample-report.md) uses fictional companies, candidate information, and reserved example URLs. It demonstrates the output format; it is not a list of live vacancies. The [sample search plan](examples/sample-search-plan.md) demonstrates keyword expansion and related-role suggestions.

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
tests/                        Scoring, collection, failure handling, and export checks
```

To extend the skill, keep scoring changes synchronized with the rubric and tests. Add new role examples when they improve transferable search behavior rather than building a closed catalog of job titles.
