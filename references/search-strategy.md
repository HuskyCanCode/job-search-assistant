# Search expansion and live verification

This guide is for the host skill agent, using its available web search and browser tools. A request to find openings means execute searches and return actual job links, not just recommend websites or keywords. Use [job-sources.md](job-sources.md) to choose sources and routes; [live-discovery.md](live-discovery.md) explains the optional public ATS collection helper. That helper collects published employer-board data; the report script only formats supplied evidence. Neither replaces the agent's resume assessment, cross-source discovery, or final verification. No API subscription or scraping service is required. When live tools are unavailable, produce a clearly labeled search plan or compare user-supplied descriptions and state that availability was not checked.

## 1. Turn the request into a search brief

Record target roles or desired work, location, commute radius, work arrangement, employment type, seniority, pay expectations with currency and period, preferred industries, languages, and exclusions. Use only relevant resume facts. Mark each item as user-stated, resume-supported, or an assumption. If a missing detail materially changes eligibility, ask briefly while progressing with independent work.

Separate **hard constraints** from **soft preferences**. Preserve explicit requirements such as a minimum salary, remote-only work, an allowed country, hours, or excluded industries. Do not silently relax them to fill the table. When the user has not specified rigidity, state your working interpretation instead of inventing a requirement.

Work authorization, required licenses, clearance, location restrictions, and mandatory language ability need explicit evidence. Do not infer citizenship, age, disability, family situation, or other sensitive attributes from a name, address, graduation date, or resume. Missing information is unknown, not a confirmed mismatch. Do not send names, email addresses, phone numbers, or full resume passages to search engines.

## 2. Build a useful keyword map

Start with the user's words and demonstrated work, then expand across the dimensions below. This is a curated map of promising searches, not a promise to enumerate every possible title or keyword.

| Dimension | Expansion method | Guardrail |
| --- | --- | --- |
| Title synonyms | Common employer titles, abbreviations, spelling variants, regional labels | Similar titles can mean different duties; confirm in descriptions |
| Functions and transferable skills | Tasks performed, tools used, customers served, outcomes delivered | Explain the connection to actual evidence; do not invent experience |
| Industry | Current sector, similar workflows in another sector, relevant domain knowledge | Keep excluded industries excluded |
| Seniority | Individual contributor/manager track; trainee, junior, intermediate, senior where supported | Years alone do not prove level; inspect ownership and scope |
| Geography and language | Accepted cities, regions, commuting areas, local-language and English titles | Translation does not establish language proficiency or work authorization |
| Work arrangement | Remote, hybrid, on-site, field-based; explicit time-zone terms | Remote does not mean work from any country |
| Employment type | Full-time, part-time, contract, temporary, seasonal, internship, apprenticeship | Add only compatible types; distinguish schedule from employment status |
| Credentials | Confirmed licenses, certifications, degree equivalents, professional abbreviations | Never substitute a related certificate for a mandatory license |

Use occupation resources to discover terminology, then validate it against actual postings. O*NET keyword search incorporates alternate titles, descriptions, and tasks; it is a terminology source, not proof of a live vacancy. [O*NET search guidance](https://www.onetonline.org/help/online/search). For European multilingual terminology, ESCO provides occupation and skill concepts across languages. Preserve original titles beside translated explanations. [ESCO](https://esco.ec.europa.eu/es).

Label role families:

- **Close:** substantially the same function at compatible scope; strong overlap with demonstrated work.
- **Adjacent:** a credible move using transferable skills; name the additional domain or skill gap.
- **Stretch:** a larger responsibility or skill change; explain why it may be worth exploring and what is missing. Never relax hard eligibility requirements to make it appear suitable.

Illustrative expansions below are hypotheses to test, not automatic qualification claims:

| Starting experience | Close searches | Adjacent searches and bridge | Stretch searches and gap to verify |
| --- | --- | --- | --- |
| Retail supervisor | shift supervisor; department supervisor; store team lead | inventory coordinator; customer service team lead — scheduling, stock control, escalation handling | assistant store manager — hiring, budget, and store-wide responsibility |
| Administrative assistant | office assistant; administrative coordinator; team assistant | operations coordinator; scheduling coordinator — organization and stakeholder support | project coordinator — delivery tracking and project methods |
| Hospitality front desk | guest services agent; front desk associate; reservations agent | customer support specialist; patient access representative — service and scheduling, with sector requirements checked | customer success associate — account ownership and relevant product skills |
| Software developer using Python | Python developer; backend engineer; software engineer | test automation engineer; integration engineer — coding and debugging, with tooling gaps checked | data engineer — pipelines, data modeling, and production platform experience |
| Data analyst using SQL | reporting analyst; business intelligence analyst; data analyst | operations analyst; product analyst — analysis plus business context | analytics engineer — transformation tooling, modeling, and software practices |

For example, a Spanish-speaking user seeking administrative work in an accepted Spanish market might test `auxiliar administrativo`, `asistente administrativo`, and `administrative assistant`. Verify local usage, actual duties, and the posting's required languages. Do not automatically broaden to another country.

## 3. Execute and refine searches

Create a compact query table with role family, exact query text, source, purpose, and preserved filters. Include reusable searches even when they return no acceptable posts. Keep hard constraints in platform filters and verify them on each result; free-text keywords alone do not enforce them.

Begin with close roles. Automatically choose the source mix in [job-sources.md](job-sources.md): user-named sources, broad platforms, original employer pages, and suitable niche/local/remote/entry-level sources. For a broad search in a market they serve, attempt both LinkedIn and Indeed discovery without making the user request them individually. Respect narrower source choices and exclusions. Follow observed employer career and applicant-tracking-system (ATS) links; never guess an employer's ATS identifier or a posting URL.

Execute independent role/source queries in small parallel batches when host tools support it, then inspect the returned candidates before refining. Search a platform through an available supported connector or browser UI; otherwise use a domain-restricted web search. For example, `site:linkedin.com/jobs/view "junior frontend" "New York"` is **web discovery of LinkedIn-indexed pages**, not a completed LinkedIn platform search. Record that method honestly. A blocked platform page does not mean zero matching jobs; try indexed discovery and the identified employer's site, and preserve the limitation.

Examples of query text to adapt:

- `"inventory coordinator" "Chicago"` with the user's pay, distance, and employment filters.
- `"administrative coordinator" "nonprofit" "Boston"` when nonprofit is an allowed preference.
- `"Python developer" "remote" "Canada"` followed by checking province and work-authorization restrictions.
- `"customer support specialist" "bilingual" "Spanish"` only when the language is supported by user evidence.
- `site:<verified employer domain> "careers" "data analyst"` using a domain already verified for that employer.
- `site:indeed.com "application support" "Boston"`, then compare the observed result with the employer's posting.
- `site:jobs.ashbyhq.com "frontend" "junior" "Canada"`, then verify the employer-to-board relationship and the specific listing. This is discovery across indexed ATS pages, not a complete ATS inventory.

Use short variants when a platform treats Boolean syntax as literal text. Support for operators differs by source and can change; consult the current UI/help instead of copying one universal query. Indeed documents phrase, exclusion, title, company, and other search refinements. [Indeed search guidance](https://www.indeed.com/help/job-seekers/articles/204488950-improving-your-job-searches-tips-and-help?hl=en&co=US).

After an initial pass, record which titles and terms returned relevant results and which created noise. Add synonyms found in good descriptions. If an employer-specific search is sparse, remove speculative ATS-domain filters and find the employer's official Careers link: many employers use hosts outside the collector's three providers. If results are sparse, broaden one soft preference at a time: title wording, equivalent tools, related industry, then other user-permitted flexibility. Explain each expansion. If a hard constraint prevents useful results, report that finding and propose a possible change without applying it silently.

Search adjacent roles when evidence supports the transition; keep stretch roles visibly labeled. Refine based on actual relevant results rather than filling a title list with unsupported matches. Stop when further queries mostly repeat results, the selected source tiers and named sources have been attempted, or the agreed scope is reached. State any unattempted sources. Never label a generated query list as completed searching or promise all jobs on the internet.

## 4. Keep a source coverage ledger

Record each actual source/query attempt in `search_sources` using the contract in [report-format.md](report-format.md). Capture `source`, observed `url`, `method`, exact `query`, `status`, `checked_at`, `results_seen`, `verified_open`, and `notes`. Methods are `platform_search`, `web_search`, `employer_site`, and `public_api`. A homepage read without a role query is source setup, not a completed search.

| Status | Meaning |
| --- | --- |
| `searched` | The stated query/method ran and its returned results were inspected; no claim to the source's entire inventory |
| `limited` | Partial coverage: indexed-only access, truncated results, incomplete descriptions, or another stated restriction |
| `blocked` | This attempt could not retrieve usable results due to access or tool failure |
| `skipped` | Not attempted; explain market mismatch, user exclusion, scope/time limit, or another concrete reason |

`results_seen` counts candidate posting records actually inspected for that attempt, not a search engine's estimated hit count. A successful query with no candidates can record `0`; use `null` with `blocked` or `skipped`, with `verified_open: 0`. A blocked UI attempt and a successful web fallback are separate entries with separate methods. Record verification limitations even when the employer source succeeds. Counts of `verified_open` may overlap across sources; the report total is unique verified open requisitions after deduplication, never a sum of source counts.

## 5. Verify every reportable vacancy

Open the specific job page, preferably on the employer's official site or the ATS board linked from it. A search snippet, job-search landing page, or generic careers page is not a verified vacancy. Do not bypass login walls, CAPTCHAs, or access restrictions. If access fails, try the official employer source once discovered; otherwise retain only an explicitly unverified lead.

Capture the following evidence before scoring:

- Exact employer and title; direct observed URL; requisition ID when present; location and work arrangement.
- Full accessible description, required versus preferred qualifications, duties, and application conditions. Keep concise supporting excerpts or faithful paraphrases with their source.
- Remote country/state/province restrictions, time zone, on-site attendance, travel, schedule, sponsorship statements, and required credentials. Preserve unknowns. Federal remote and telework are distinct, and even remote roles can impose time-zone requirements. [USAJOBS remote guidance](https://help.usajobs.gov/how-to/search/filters/remote).
- Advertised compensation with currency, hourly/monthly/annual period, region, base versus total compensation, and any stated commission or bonus. Do not invent a salary from market estimates. If normalizing pay, show the original amount and explicit hours/weeks assumptions; do not treat annualized hourly estimates as advertised salary.
- The employer's posted date and closing date, if shown; separately record the actual verification timestamp with time zone. A date the agent checked the page is not the posting date. Preserve ambiguous relative dates as reported, with the check date as context.
- Observed status: open, closed/expired, or uncertain. An accessible page alone does not prove applications are still accepted; check status text and the actual application entry point where accessible without submitting.

Deduplicate first by employer plus requisition ID, then canonical observed URL, and finally employer/title/location with description comparison. Preserve materially different requisitions. Prefer the original employer listing as `url`, retaining observed syndicated links in `discovered_via: [{source, url}]`. List additional locations in one row when they belong to one requisition. Do not merge similar titles without identity evidence, and never claim several copies are several opportunities.

Only score jobs whose accessible descriptions provide enough evidence for comparison. Keep blocked, snippet-only, and otherwise unverified leads in a separate table with the reason and observed source link; do not give them confident match scores. Exclude confirmed closed jobs from current recommendations or show them separately as closed examples. If dates, pay, eligibility, or application status remain unknown, say so in the table.

## 6. Hand off evidence to the report

Give the deterministic report script only the structured observations and evidence-backed assessment defined by this repository, including `search_sources` and job `discovered_via` links. It cannot turn a supplied URL or imported ATS record into verification. Preserve source URLs and verification timestamps in the rendered table, and label hypothetical/demo rows explicitly.

Rank eligible, verified close and adjacent roles using the scoring rubric, then explain the strongest evidence and material gaps. Keep unknown eligibility visible rather than treating it as passed. A resume-to-description match score describes documented fit; it is not an interview or hiring probability. Do not convert search rank, keyword density, applicant counts, or a platform badge into a likelihood of receiving an offer.

Target 20 distinct relevant employers by default, honoring a user-requested different scope. Build employer breadth before spending the whole search on many postings at one company. Find up to three useful verified recommendations per employer; do not pad missing slots. Verify company identity and collect the sourced context in [company-research.md](company-research.md) while job checks run independently.

Finish with a linked company overview first, detailed job tables grouped by company second, then the reusable keyword/query and source coverage tables. Include unique employer and active-post counts, markets searched, check date, gaps and stopping reason. Label unverified, blocked and closed jobs separately within each company. When fewer than 20 companies or zero verified jobs remain, report the actual results; do not treat access failures as proof that no jobs exist. Live searching happens during the current run; recurring searches require a user-requested schedule. Do not apply, contact employers, upload resumes to external sites, or enable alerts without the user's authorization.
