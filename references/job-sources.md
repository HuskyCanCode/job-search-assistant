# Job source selection and access routes

Use this catalog when executing a live job search. It is a maintained starting set, not a claim to cover every job site or vacancy. The official routes and documentation below were checked on 2026-09-10; inspect the current page during a run because access and controls change. Follow [search-strategy.md](search-strategy.md) for query expansion, verification, deduplication, and the coverage ledger.

## Choose sources automatically

1. **User choices:** attempt each user-named resource, including LinkedIn. Preserve explicit source exclusions or an instruction to search only certain sites. Report blocked or out-of-scope sources by name instead of silently replacing them.
2. **Core coverage:** for a broad search in a market they serve, attempt LinkedIn and Indeed discovery, plus employer career pages. Prefer the employer's original listing for verification. If a major platform does not serve the requested country, record that reason and use an appropriate national source.
3. **Relevant additions:** choose a few distinct sources for the role and country from the tables below. A technology search could add Built In/Dice or Wellfound/Welcome to the Jungle; remote work could add suitable remote boards; entry-level searches could add public apprenticeship and employer trainee pages.
4. **Expand when useful:** add Glassdoor, ZipRecruiter, local staffing agencies, professional-association boards, or other relevant boards when early results lack coverage or the user asks for a wider search. Test adjacent titles while preserving hard constraints. Stop after diminishing returns or the agreed scope; report what was and was not searched.

Do not search every board worldwide or collect irrelevant roles to inflate counts. A source appearing here does not count as searched. The default mix is adaptable guidance, not a fixed quota.

## Broad and specialist discovery

All query fragments below are **web-search examples**. Replace `ROLE` and `PLACE` with approved role and location terms; execute them using the host's actual search tool. They are not API endpoints, direct post links, or proof of current openings.

| Source / official entry | When useful | Platform route and web fallback |
| --- | --- | --- |
| [LinkedIn Jobs](https://www.linkedin.com/jobs/) · [filter help](https://www.linkedin.com/help/linkedin/answer/a507443) | Broad professional and company discovery | Use Jobs title/location controls and available filters. Fallback: `site:linkedin.com/jobs/view ROLE PLACE`. Mark indexed discovery as `web_search`/`limited`; verify discovered employer posts separately. |
| [Indeed](https://www.indeed.com/) · [search help](https://www.indeed.com/help/job-seekers/articles/204488950-improving-your-job-searches-tips-and-help?hl=en&co=US) | Broad roles, local work, and country-specific markets | Use the relevant country site, title/location fields and current filters. Fallback: `site:indeed.com ROLE PLACE`, adapting to the observed country domain. |
| [Glassdoor Jobs](https://www.glassdoor.com/Job/index.htm) | Additional job discovery and company research | Use job and location search when available; fallback: `site:glassdoor.com/Job ROLE PLACE`. Reviews or estimated salaries are context, not employer job requirements or advertised pay. |
| [ZipRecruiter](https://www.ziprecruiter.com/Search-Jobs-Near-Me) | Additional broad/local coverage in markets served | Use job title and location fields. Fallback: `site:ziprecruiter.com ROLE PLACE`. Treat aggregate search/category pages as discovery only. |
| [Wellfound](https://wellfound.com/jobs) | Startups, including technical and business roles | Use title/location and observed categories; fallback: `site:wellfound.com/jobs ROLE PLACE`. Check employment type, pay/equity distinction, and required experience. |
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

The optional collector in [live-discovery.md](live-discovery.md) helps retrieve public Greenhouse, Lever, and Ashby postings from **observed, employer-linked boards**. It does not search LinkedIn, Indeed, all employers, or the whole web. Record the public API method separately and verify imported candidates before calling them open recommendations or assigning resume-match scores. Follow current provider terms, pagination, and documented limits; do not call private authenticated employer APIs or invented endpoints.

## Access failures and honest reporting

- Prefer available supported connectors, then ordinary browser access or public web search. Using a named source does not require a new account, a paid service, resume upload, or enabling alerts.
- If the UI requires login or presents a CAPTCHA/access block, do not bypass it. Continue using accessible indexed pages and discovered employer pages. An already available authorized session may help through its normal UI; do not extract credentials or tokens.
- Record an inaccessible platform attempt as `blocked`, then record any web fallback separately as `web_search` with `limited` coverage. A successful fallback does not retroactively mean the platform search ran.
- If only snippets or inaccessible URLs remain, keep them in an unverified-leads table with no confident match score. An original employer page can verify a vacancy even when the discovery board remains inaccessible; preserve both URLs and the source limitation.
- Show the actual source coverage table, including user-named resources and reasons for limited/blocked/skipped coverage. Count inspected candidates and deduplicated verified open jobs; do not imply exhaustive access, treat approximate hit counts as inspected jobs, or interpret a blocked request as no openings.
