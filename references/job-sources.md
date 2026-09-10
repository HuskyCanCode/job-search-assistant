# Job source selection and access routes

Use this catalog when executing a live job search. It is a maintained starting set, not a claim to cover every job site or vacancy. The official routes and documentation below were checked on 2026-09-10; inspect the current page during a run because access and controls change. Follow [search-strategy.md](search-strategy.md) for query expansion, verification, deduplication, and the coverage ledger.

## Choose sources automatically

1. **User choices:** attempt each user-named resource, including LinkedIn. Preserve explicit source exclusions or an instruction to search only certain sites. Report blocked or out-of-scope sources by name instead of silently replacing them.
2. **Default broad-search catalog:** LinkedIn Jobs, Indeed, ZipRecruiter, Built In, Y Combinator Jobs, Wellfound, HiringCafe, SimplyHired, Lensa, and Teal Jobs. Attempt an initial role/location query on each relevant site, plus original employer pages, using the parallel batches in the [fast search workflow](search-strategy.md#fast-search-workflow). Broad boards cover varied work; Built In, YC and Wellfound are especially useful for technology/startup roles and related business functions. Skip unrelated trades or roles outside a specialist board's coverage unless the user explicitly requested that source. Record concrete market/role mismatches, exclusions or a user-imposed time limit as skipped.
3. **Market and specialty coverage:** use appropriate national, regional, professional, remote or entry-level sources when they improve coverage. A technology search could add Dice or Welcome to the Jungle; entry-level searches could add public apprenticeship and employer trainee pages. A source listed in the catalog may not serve every country.
4. **Expand when useful:** add Glassdoor, local staffing agencies, professional-association boards, or other relevant boards when early results lack coverage or the user asks for a wider search. Test adjacent titles while preserving hard constraints. Stop using the fast workflow's diminishing-return guidance or when the requested scope and source coverage are met; report what was and was not searched.

Do not search every board worldwide or collect irrelevant roles to inflate counts. Catalog inclusion is not a completed search or a built-in API integration. The host executes actual source-specific queries with its available live tools. Start with a short query per relevant source instead of running every title on every website.

## Broad and specialist discovery

All query fragments below are **web-search examples**. Replace `ROLE` and `PLACE` with approved role and location terms; execute them using the host's actual search tool. They are not API endpoints, direct post links, or proof of current openings.

| Source / official entry | When useful | Platform route and web fallback |
| --- | --- | --- |
| [LinkedIn Jobs](https://www.linkedin.com/jobs/) · [filter help](https://www.linkedin.com/help/linkedin/answer/a507443) | Broad professional and company discovery | Use Jobs title/location controls and available filters. Fallback: `site:linkedin.com/jobs/view ROLE PLACE`. Mark indexed discovery as `web_search`/`limited`; verify discovered employer posts separately. |
| [Indeed](https://www.indeed.com/) · [search help](https://www.indeed.com/help/job-seekers/articles/204488950-improving-your-job-searches-tips-and-help?hl=en&co=US) | Broad roles, local work, and country-specific markets | Use the relevant country site, title/location fields and current filters. Fallback: `site:indeed.com ROLE PLACE`, adapting to the observed country domain. |
| [Glassdoor Jobs](https://www.glassdoor.com/Job/index.htm) | Additional job discovery and company research | Use job and location search when available; fallback: `site:glassdoor.com/Job ROLE PLACE`. Reviews or estimated salaries are context, not employer job requirements or advertised pay. |
| [ZipRecruiter](https://www.ziprecruiter.com/Search-Jobs-Near-Me) | Additional broad/local coverage in markets served | Use job title and location fields. Fallback: `site:ziprecruiter.com ROLE PLACE`. Treat aggregate search/category pages as discovery only. |
| [Wellfound](https://wellfound.com/jobs) | Startups, including technical and business roles | Use title/location and observed categories; fallback: `site:wellfound.com/jobs ROLE PLACE`. Check employment type, pay/equity distinction, and required experience. |
| [Y Combinator Jobs](https://www.ycombinator.com/jobs) / [Work at a Startup](https://www.workatastartup.com/jobs) | YC startup roles in engineering, operations, sales and other functions | Follow public company/job pages. Fallback: `site:ycombinator.com/companies ROLE PLACE jobs` or `site:workatastartup.com/jobs ROLE PLACE`. Treat the two routes as one source; profile/application features may require sign-in. |
| [HiringCafe](https://hiringcafe.com/) | Broad employer discovery with role, location and work-arrangement filters | Use public search filters; fallback: `site:hiringcafe.com ROLE PLACE`. Observed individual paths use `/job/` and category paths `/jobs/`. `hiring.cafe` redirects here as checked on 2026-09-10; count the aliases once. Verify extracted summaries and company facts on original sources. |
| [SimplyHired](https://www.simplyhired.com/) | Broad and local roles, including customer/IT support | Use title/location and current filters. Fallback: `site:simplyhired.com/job ROLE PLACE`, broadening to the domain if needed. The site identifies itself as part of Indeed with shared accounts; preserve source attribution but merge duplicate vacancies. |
| [Lensa](https://lensa.com/) / [Search Jobs](https://lensa.com/talent/job-opportunities) | Additional broad/local discovery and support roles | Use public title/location controls; fallback: `site:lensa.com ROLE PLACE` (individual paths can use `/job-v1/`). Separate employer JD text from generic occupational, demographic or interview material appended to pages. An empty unfiltered page is not proof of zero openings. |
| [Teal Jobs](https://www.tealhq.com/jobs) | Additional technology, operations, support and QA leads | Use public search/filters; fallback: `site:tealhq.com/job ROLE PLACE`. Resume matching and tracking features are separate account-based products and unnecessary for discovery. If an Apply destination is not readable, follow an observed employer route or inspect it in an ordinary browser. |
| [Welcome to the Jungle](https://www.welcometothejungle.com/en) | Company-led discovery, startup and professional roles in supported markets | Follow Find a job and accessible company job pages. Fallback: `site:welcometothejungle.com ROLE PLACE`. Otta is now Welcome to the Jungle, confirmed by its [official announcement](https://solutions.welcometothejungle.com/en/otta-is-now-welcome-to-the-jungle); do not count both as distinct sources. |
| [Built In](https://builtin.com/jobs) | Technology companies and related business functions | Search current jobs with role/location filters. Fallback: `site:builtin.com/job ROLE PLACE`; inspect result paths because board URLs can vary. |
| [Dice](https://www.dice.com/jobs) | Technology roles and contract discovery where relevant | Use title/location and current employment filters. Fallback: `site:dice.com/job-detail ROLE PLACE`. Confirm actual employer versus staffing agency and contract terms. |
| [We Work Remotely](https://weworkremotely.com/) | Remote programming, design, support, sales, and other listed categories | Search or follow relevant category pages; fallback: `site:weworkremotely.com/remote-jobs ROLE`. Verify permitted countries and time zones on each post. |
| [Remote OK](https://remoteok.com/) | Additional remote-role discovery | Use currently visible search/category controls; fallback: `site:remoteok.com/remote-jobs ROLE`. A remote board label does not establish worldwide eligibility. |
| [Remotive](https://remotive.com/) · [remote jobs index](https://remotive.com/remote-jobs-index) | Remote roles by function, location, and career level | Inspect public listings or an authorized available session; fallback: `site:remotive.com/remote-jobs ROLE PLACE`. Some results/features require membership; record public-only coverage and do not treat hidden details as inspected. |

Use employer and niche sites to broaden actual coverage; several broad boards may syndicate the same requisition. Do not repeat a large Boolean expression everywhere: each source may interpret operators differently. Inspect its UI/help and use short alternate titles when needed.

## Country, industry, and entry-level routes

Select the user's market first; discover additional local boards through official government, employer, school, union, or professional-association pages. Search local-language titles when useful without inferring the user's language proficiency.

| Market / need | Starting resource | What to check |
| --- | --- | --- |
| U.S. federal work | [USAJOBS search](https://help.usajobs.gov/how-to/search) | Hiring paths, who may apply, grade/series, closing date, and required qualifications. Remote and telework differ. |
| U.S. entry-level / apprenticeships | [Apprenticeship.gov finder](https://www.apprenticeship.gov/apprenticeship-job-finder), plus employers' observed trainee/apprentice pages | Distinguish an open vacancy from a program directory or general interest form; verify application window and eligibility. |
| Canada | [Job Bank search](https://www.jobbank.gc.ca/jobsearch/jobsearch?lang=en) | Province, advertised salary period, language requirements, and who may apply. If access fails, use indexed discovery and the employer source. |
| Great Britain / Northern Ireland | [GOV.UK Find a job](https://www.gov.uk/find-a-job) | Follow the current Start now link for England, Scotland and Wales; use its separate Northern Ireland service link when applicable. |
| Europe | [EURES](https://eures.europa.eu/index_en) and the requested country's official employment service | Follow Find a job; retain the original national posting, required language, location, and eligibility restrictions. |
| Local public work | City, state/province, school district, university, hospital, and transit employer career pages | Establish official domains; verify requisition, examination/licensing requirements, and closing dates. |
| Nonprofit / social impact | [Idealist jobs](https://www.idealist.org/en/jobs) and nonprofit employer pages | Distinguish paid jobs, internships, and volunteer listings; preserve pay and schedule unknowns. |
| Regulated professions / trades / other industries | Relevant professional association, union, licensing body, or employer-linked career board | Choose based on demonstrated skills and target market. Required credentials remain hard constraints; board inclusion does not establish eligibility. |
| Students / graduates / career returners | Employer early-career pages and institution or program job boards the user can access | Do not assume enrollment, graduation-window eligibility, or returner-program eligibility. Keep program resources separate from actual openings. |

## Original employer and ATS postings

Search employer names from relevant results, establish their official career pages, and follow the actual job-board links. ATS-hosted jobs can be the employer's original source. A familiar ATS domain alone does not prove the employer identity or that an application remains open.

| Hosting route | Discovery and verification approach |
| --- | --- |
| Employer career site | Use the observed career link or `site:<verified employer domain> careers ROLE`; follow the returned vacancy URL and application entry point. |
| Greenhouse | Discover `site:job-boards.greenhouse.io ROLE PLACE` or `site:boards.greenhouse.io ROLE PLACE`; confirm the employer-linked board. Its documented [Job Board API](https://docs.greenhouse.io/job-board.html) exposes published jobs through public GET requests. |
| Lever | Discover `site:jobs.lever.co ROLE PLACE` and, where appropriate, `site:jobs.eu.lever.co ROLE PLACE`; confirm the employer-linked board. Use the [official Postings API documentation](https://github.com/lever/postings-api) only for its supported public routes. |
| Ashby | Discover `site:jobs.ashbyhq.com ROLE PLACE`; confirm the employer-linked board. The [public Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api) supports published jobs for a known board. |
| Workday | Follow the employer's observed Workday job link, often on a `myworkdayjobs.com` subdomain. Web discovery can use `site:myworkdayjobs.com ROLE PLACE`; navigate the public board UI. For example, [Workday's own career page](https://www.workday.com/en-us/company/careers/overview.html) links its real board. Never guess tenant or internal endpoint URLs. |
| JazzHR | Follow an employer-linked `applytojob.com` posting; discovery can use `site:applytojob.com ROLE PLACE`. Inspect the full original description and embedded application entry. A form alone does not override a closed/expired status. |
| iCIMS | Follow an employer's actual career link to its `icims.com` board; discovery can use `site:icims.com/jobs ROLE PLACE`. Check the specific requisition and available application entry; do not infer availability from a general registration page. |
| Avature and other employer hosts | Follow the observed employer career link and exact requisition, including `avature.net` where applicable. Use the public web/browser route when no documented collector integration exists. Employers can use hosts outside this catalog; never restrict original verification to the collector's three providers. |

The optional collector in [live-discovery.md](live-discovery.md) helps retrieve public Greenhouse, Lever, and Ashby postings from **observed, employer-linked boards**. It does not search LinkedIn, Indeed, all employers, or the whole web. Record the public API method separately and verify imported candidates before calling them open recommendations or assigning resume-match scores. Follow current provider terms, pagination, and documented limits; do not call private authenticated employer APIs or invented endpoints.

## Access failures and honest reporting

- Prefer available supported connectors, then ordinary browser access or public web search. Using a named source does not require a new account, a paid service, resume upload, or enabling alerts.
- If the UI requires login or presents a CAPTCHA/access block, do not bypass it. Continue using accessible indexed pages and discovered employer pages. An already available authorized session may help through its normal UI; do not extract credentials or tokens.
- Record an inaccessible platform attempt as `blocked`, then record any web fallback separately as `web_search` with `limited` coverage. A successful fallback does not retroactively mean the platform search ran.
- If only snippets or inaccessible URLs remain, keep them in an unverified-leads table with no confident match score. An original employer page can verify a vacancy even when the discovery board remains inaccessible; preserve both URLs and the source limitation.
- Show the actual source coverage table, including user-named resources and reasons for limited/blocked/skipped coverage. Count inspected candidates and deduplicated verified open jobs; do not imply exhaustive access, treat approximate hit counts as inspected jobs, or interpret a blocked request as no openings.
