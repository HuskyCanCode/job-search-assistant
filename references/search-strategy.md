# Search expansion and live verification

This guide is for the host skill agent, using permitted search and employer-access tools. A request to find openings means execute searches and return actual job links, not just recommend websites or keywords. Apply [source-policy-audit.md](source-policy-audit.md) and the access policy in [job-sources.md](job-sources.md) before choosing routes; [live-discovery.md](live-discovery.md) explains the optional public ATS collection helper. That helper collects published employer-board data; the report script only formats supplied evidence. Neither replaces the agent's resume assessment, cross-source discovery, or final verification. Use the supported host search integration within its scope for independent employer discovery, without adding a subscription or scraping service. When no permitted live route is available, produce a clearly labeled search plan or compare descriptions whose use is permitted and state that availability was not checked. A user-pasted description or URL does not override the originating source's restrictions.

Sources excluded by [job-sources.md](job-sources.md) are absent from active discovery and recommendations. Do not fetch, target through another search engine, ingest, or recommend them as manual alternatives. Their names and policy links belong only in exclusion explanations and the audit. A newly available integration does not reactivate an excluded source. If the user names one, record it as skipped and continue only with other sources already within the user's authorized scope. If that excluded source is the entire requested scope, explain that limitation instead of silently searching elsewhere.

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

Use licensed occupation resources to discover terminology, then validate it against permitted actual postings. Prefer the [O*NET downloadable database](https://www.onetcenter.org/database.html): credit its actual version and USDOL/ETA, link the [content license](https://www.onetcenter.org/license_db.html), identify changes and honor identified exceptions. O*NET Web Services have separate registration, attribution and service conditions; an open database license does not waive them. For European multilingual terminology, [ESCO](https://esco.ec.europa.eu/en/use-esco/use-esco-services-api) provides occupation and skill concepts through official APIs/downloads. Preserve content attribution, version and changes, and distinguish data rights from API software licenses. These resources supply terminology, not live vacancies. Preserve original titles beside translated explanations.

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

### Fast search workflow

Use this workflow by default. Optimize repeated work and unnecessary waiting while preserving the user's requested scope, usually 20 distinct companies and up to three suitable jobs each. A user-requested time limit or smaller quick shortlist overrides the default scope; label a partial result and its shortfall. Do not promise a fixed runtime or silently reduce the company target to make the search appear faster.

1. **Prepare once.** Reuse the user's confirmed constraints and an already-read, unchanged resume. Start with a few productive role families and short title variants; expand from real results. Keep source queries free of personal identifiers.
2. **Discover in parallel.** Check permitted access, use and storage for each active provider/method once, reuse that decision, and batch queries within provider and host limits. Start with independent employer discovery and supported public boards whose relevant rights are established. The active catalog is not a required query checklist, and excluded boards are never fallback or manual recommendations. Record an excluded user-named source as skipped; continue only within the user's remaining authorized scope. Spread role variants across permitted routes rather than every keyword across every board. Different queries on one source are not coverage of other sites.
3. **Deduplicate before deeper work.** Keep one shared queue keyed by employer/requisition and canonical URL, retaining all permitted discovery origins and required attribution. Screen obvious closed listings and confirmed hard mismatches early. Unknown attendance or eligibility stays unknown and can justify a verification check. When delegating, assign disjoint employers or role/source groups and reconcile newly discovered employers before a second worker researches them.
4. **Build employer breadth first.** Verify one promising vacancy per distinct employer before spending time on second and third recommendations. Prioritize direct evidence of compatible duties, level and location; discovery rank is not a fit score. Once the company shortlist is established, inspect additional suitable openings up to the requested per-company count. Do not fill empty slots with unrelated roles.
5. **Bound access recovery.** Prefer permitted originals or documented public board APIs with established use rights. For an inaccessible posting, try one other permitted employer route; do not target the restricted board through a search engine, cache or mirror. An ordinary browser may resolve JavaScript rendering or contradictory status only where that automated access is permitted; it is not an exception for LinkedIn, Indeed or another restricted source. Stop at sign-in/CAPTCHA blocks. Do not use accounts, user-pasted copies or scraper resellers to restore restricted access. Do not repeat unchanged failing URLs or queries. Retry only when new evidence or a changed permitted access condition makes it useful; otherwise record the limit and move to another candidate.
6. **Reuse permitted evidence within the run.** Share completed job checks, employer facts, failed routes and exclusion reasons within their permitted retention terms. Do not persist restricted search-provider responses or snippets. Re-fetching an unchanged description or re-reading the resume for another worker wastes time. Check a job again when status conflicts, the source changes, or a later run needs fresh verification. Saved historical facts may be reused with their real dates and sources, but cached listings are never current verification for a later run.
7. **Research shortlisted employers once.** Run independent size/trend and layoff queries alongside other job checks. Use one company record across all its jobs; follow the dated-source rules in `company-research.md`, including the bounded layoff window and an unrestricted history check. Follow up on useful primary sources or material contradictions, then preserve unknowns when evidence is insufficient. Do not keep searching for a missing headcount number while the job report is otherwise ready.
8. **Checkpoint and stop transparently.** Save independently verified employer facts and permitted source attribution incrementally outside the distributable skill. After two successive refinement batches produce no new viable employers, reassess titles or other permitted soft preferences once. If the next useful expansion also adds none, deliver the substantiated results with the shortfall and limits. Otherwise continue toward the requested scope. Finish once the scope and permitted source coverage are satisfied; report actual source attempts and recommendable employers, not raw URLs collected. Restricted routes remain disabled even when the target is short.

The collector can retrieve several observed employer boards concurrently (`--workers`, default 4; use 1 for sequential requests). The host handles authorized search discovery and permitted original verification separately; it does not automate LinkedIn pages. Collecting leads, checking complete descriptions and application availability, comparing resume evidence, and researching companies remain distinct steps. Full verification is required for each recommendation regardless of the execution speed.

### Queries and refinement

Create a compact query table with role family, exact query text, source, purpose, and preserved filters. Include reusable searches even when they return no acceptable posts. Keep hard constraints in platform filters and verify them on each result; free-text keywords alone do not enforce them.

Begin with close roles. Choose active permitted routes using [job-sources.md](job-sources.md) and [source-policy-audit.md](source-policy-audit.md), prioritizing independent employer discovery and employer pages. Niche, local, remote and entry-level sources are eligible only when not excluded and within established scope. Do not query every catalog site or reactivate an excluded source because the user named it. Respect narrower source choices and exclusions. Follow observed permitted employer career and applicant-tracking-system (ATS) links; never guess an employer's ATS identifier or a posting URL.

Execute independent role/employer queries in small parallel batches through the supported host search integration within its scope. Inspect and use only permitted result data from active sources. Use direct board APIs or automated browser access only when the source is not excluded and its policy permits the actual method and downstream report use. Incidental excluded or restricted snippets are not evidence: do not quote, score, copy or reconstruct them, including extracting details to recreate the listing elsewhere. Ignore them and continue independent employer discovery from the user's goals and permitted evidence within the authorized scope. Do not ingest Lensa content into AI outputs. A user-pasted copy is not a workaround for these restrictions. Excluded sources receive a skipped explanation, not links or queries recommending their manual use.

Examples of query text to adapt:

- `"inventory coordinator" "Chicago"` with the user's pay, distance, and employment filters.
- `"administrative coordinator" "nonprofit" "Boston"` when nonprofit is an allowed preference.
- `"Python developer" "remote" "Canada"` followed by checking province and work-authorization restrictions.
- `"customer support specialist" "bilingual" "Spanish"` only when the language is supported by user evidence.
- `site:<verified employer domain> "careers" "data analyst"` using a domain already verified for that employer.
- `site:jobs.ashbyhq.com "frontend" "junior" "Canada"`, then verify the employer-to-board relationship and the specific listing. This is discovery across indexed ATS pages, not a complete ATS inventory.

Use short variants when a permitted search route treats Boolean syntax as literal text. Support for operators differs by source and can change; consult its current permitted documentation instead of copying one universal query. Manual next steps may concern permitted active sources only; do not reintroduce excluded boards in keyword or follow-up recommendations.

After an initial pass, record which titles and terms returned relevant results and which created noise. Add synonyms found in good descriptions. If an employer-specific search is sparse, remove speculative ATS-domain filters and find the employer's official Careers link: many employers use hosts outside the collector's three providers. If results are sparse, broaden one soft preference at a time: title wording, equivalent tools, related industry, then other user-permitted flexibility. Explain each expansion. If a hard constraint prevents useful results, report that finding and propose a possible change without applying it silently.

Search adjacent roles when evidence supports the transition; keep stretch roles visibly labeled. Refine based on actual relevant results rather than filling a title list with unsupported matches. Follow the fast workflow's stopping conditions: reaching the requested scope and source coverage, a user-imposed limit, or diminishing returns after useful refinement. Merely finishing the initial source pass does not end a search that still has promising routes toward the company target. State any unattempted sources. Never label a generated query list as completed searching or promise all jobs on the internet.

## 4. Keep a source coverage ledger

Record each actual source/query attempt in `search_sources` using the contract in [report-format.md](report-format.md). Capture `source`, permitted observed `url`, `method`, exact `query`, `status`, `checked_at`, `results_seen`, `verified_open`, and `notes`, subject to access and retention terms. Methods are `platform_search`, `web_search`, `employer_site`, and `public_api`. A homepage read without a role query is source setup, not a completed search. Record excluded access as `skipped` with its reason, not `blocked` unless an actual permitted request failed. An independent host web search is a `web_search` row; do not count incidental excluded or restricted snippets as a board search or verified job. Keep excluded source names and policy links only in skipped/exclusion explanations, never job or manual-source recommendations.

| Status | Meaning |
| --- | --- |
| `searched` | The stated query/method ran and its returned results were inspected; no claim to the source's entire inventory |
| `limited` | Partial coverage: indexed-only access, truncated results, incomplete descriptions, or another stated restriction |
| `blocked` | This attempt could not retrieve usable results due to access or tool failure |
| `skipped` | Not attempted; explain market mismatch, user exclusion, scope/time limit, or another concrete reason |

`results_seen` counts candidate posting records permissibly inspected for that attempt, not a search engine's estimated hit count or ignored restricted snippets. A successful query with no candidates can record `0`; use `null` with `blocked` or `skipped`, with `verified_open: 0`. A failed permitted request and a successful independent employer search are separate entries with separate methods. Record verification limitations even when the employer source succeeds. Counts of `verified_open` may overlap across sources; the report total is unique verified open requisitions after deduplication, never a sum of source counts.

## 5. Verify every reportable vacancy

Inspect the specific original vacancy through a permitted active employer page or employer-linked ATS route. Finding a public URL, using a familiar browser, or receiving a search snippet does not authorize restricted destination access or report reuse. A snippet, job-search landing page or generic careers page is not a verified vacancy. Do not bypass login walls, CAPTCHAs or automation restrictions. If no permitted route confirms the full description and current application availability, retain an explicitly unverified/manual-review lead only from a non-excluded source whose content and links may be used. Excluded sources such as Glassdoor, Dice and Welcome to the Jungle receive no job or homepage recommendations. Continue with another employer only within the user's authorized scope.

Preserve any licensed feed's required source credit, original job link and application route. Prefer an employer original only when that choice is compatible with the source's conditions; never strip required provenance when deduplicating. An independently found employer vacancy can use its own permitted evidence. Public ATS documentation establishes an access route, not unrestricted storage or redistribution rights. If the report helper cannot preserve a source's required terms, use a suitable manually assembled report or omit that source rather than silently dropping them; see [report-format.md](report-format.md).

Capture the following evidence before scoring:

- Exact employer and title; direct observed URL; requisition ID when present; location and work arrangement.
- Full description available under permitted use, required versus preferred qualifications, duties, and application conditions. Keep concise supporting excerpts or faithful paraphrases only where use and retention are allowed, with required attribution.
- Remote country/state/province restrictions, time zone, on-site attendance, travel, schedule, sponsorship statements, and required credentials. Preserve unknowns. Federal remote and telework are distinct, and even remote roles can impose time-zone requirements. [USAJOBS remote guidance](https://help.usajobs.gov/how-to/search/filters/remote).
- Advertised compensation with currency, hourly/monthly/annual period, region, base versus total compensation, and any stated commission or bonus. Do not invent a salary from market estimates. If normalizing pay, show the original amount and explicit hours/weeks assumptions; do not treat annualized hourly estimates as advertised salary.
- The employer's posted date and closing date, if shown; separately record the actual verification timestamp with time zone. A date the agent checked the page is not the posting date. Preserve ambiguous relative dates as reported, with the check date as context.
- Observed status: open, closed/expired, or uncertain. An accessible page alone does not prove applications are still accepted; check status text and the actual application entry point where accessible without submitting. A surviving form never overrides an explicit closed or expired status on the original posting, regardless of hosting provider.

Deduplicate first by employer plus requisition ID, then canonical observed URL, and finally employer/title/location with description comparison. Preserve materially different requisitions. Prefer the original employer listing as `url` where licensing permits, retaining allowed and required syndicated attribution in `discovered_via: [{source, url}]`. List additional locations in one row when they belong to one requisition. Do not merge similar titles without identity evidence, and never claim several copies are several opportunities.

Only score jobs whose permitted descriptions provide enough evidence for comparison. Keep permitted but blocked, snippet-only or otherwise unverified leads from active sources separate with the reason and an allowed source link, unscored. Excluded or restricted snippets are ignored, not retained as leads. Omit content and links that cannot be used; do not replace them with excluded-board manual recommendations. Exclude confirmed closed jobs from current recommendations or show them separately as closed examples when their reuse is allowed. If dates, pay, eligibility, or application status remain unknown, say so in the table.

## 6. Hand off evidence to the report

Give the deterministic report script only permitted structured observations and evidence-backed assessments defined by this repository, including allowed `search_sources` and job `discovered_via` links. It cannot turn a supplied URL or imported ATS record into verification or authorize its use. Preserve required attribution, permitted source URLs and verification timestamps in the rendered table, and label hypothetical/demo rows explicitly. Check every delivered format against applicable use conditions; use a suitable manual rendering or omit incompatible source material when the helper cannot preserve them.

Rank eligible, verified close and adjacent roles using the scoring rubric, then explain the strongest evidence and material gaps. Keep unknown eligibility visible rather than treating it as passed. A resume-to-description match score describes documented fit; it is not an interview or hiring probability. Do not convert search rank, keyword density, applicant counts, or a platform badge into a likelihood of receiving an offer.

Target 20 distinct relevant employers by default, honoring a user-requested different scope. Build employer breadth before spending the whole search on many postings at one company. Find up to three useful verified recommendations per employer; do not pad missing slots. Verify company identity and collect the sourced context in [company-research.md](company-research.md) while job checks run independently.

Finish with a linked company overview first, detailed job tables grouped by company second, then the reusable keyword/query and source coverage tables. Include unique employer and active-post counts, markets searched, check date, gaps and stopping reason. Label unverified, blocked and closed jobs separately within each company. When fewer than 20 companies or zero verified jobs remain, report the actual results; do not treat access failures as proof that no jobs exist. Live searching happens during the current run; recurring searches require a user-requested schedule. Do not apply, contact employers, upload resumes to external sites, or enable alerts without the user's authorization.
