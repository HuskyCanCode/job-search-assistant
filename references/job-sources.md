# Job resources and permitted access routes

This catalog includes human-use resources and conditional integrations; it is not an automatic search list. Policy findings were checked on 2026-09-10. See the [source policy audit](source-policy-audit.md) for official evidence, dates, and unresolved scope. Follow [search-strategy.md](search-strategy.md) for expansion, verification, deduplication, and coverage reporting.

## Routing rules

1. **Start with employers.** Use an existing supported host search integration within its terms to discover employers and their official career sources. Use role, location, and industry queries, then investigate relevant employers through permitted methods. Do not require a query against every catalog website or treat restricted-board snippets as a default discovery feed.
2. **Establish access and reuse together.** During source setup, record the provider, applicable terms/policy link, check date, allowed method and purpose, third-party content rights, attribution/link requirements, rate limits, and retention scope. Retention includes tool transcripts and delegated messages as well as report files. Reuse that decision for the run; recheck only when terms, method, intended use, or applicable tenant scope changes. No repeated per-job approval or policy research is required for an established scope.
3. **Default to manual when permission is missing.** A public page, user login, API key, robots allowance, or paid search/scraper service is not by itself an access or reuse license. Manual means guidance for the human user, not agent-operated browser navigation. Use an integration only when its documented permission covers this task. Continue through other permitted sources when scope is unknown; do not create accounts or seek paid/platform access merely to fill the report.
4. **Keep restrictions across tools.** LinkedIn, Indeed, and SimplyHired website automation is off by default, including browser, web-open, scripts, and scraper services. Lensa output must not be ingested into the AI workflow by default. Do not use indexed snippets, search APIs, caches, mirrors, alternative domains, logged-in sessions, or user-pasted restricted content to evade source restrictions. A search-engine indexing exception does not grant this skill extraction or reuse rights. Do not scrape consumer search-result pages.
5. **Preserve required links and attribution.** Independently verified employer facts may be used within their applicable permissions. A feed-derived result must retain the feed's required source credit and job/application link. Attribution does not independently create permission. For Glassdoor, Dice, and Welcome to the Jungle's US service, use homepage guidance and reusable query text by default; do not retain restricted deep links in reports.

The skill cannot certify compliance with every future employer or a user's private provider agreement. Unverified permission means skip that automated route, not assume approval. See the audit for the distinction between provider website terms, customer contracts, and an employer tenant's applicable rules.

## Select sources for the user's search

- Preserve the user's markets, preferences, and source exclusions. For a named resource, use an established permitted integration if available; otherwise list a manual resource and mark automated coverage `skipped`, explaining why. Naming a source does not supply its permission.
- Select resources by role and market. The ten broad-search resources remain LinkedIn, Indeed, ZipRecruiter, Built In, Y Combinator Jobs, Wellfound, HiringCafe, SimplyHired, Lensa, and Teal. Their inclusion does not mean each was queried or has a built-in integration.
- Expand employer breadth, adjacent titles, local public employers, and relevant specialist resources when useful. Parallelize only permitted requests. Keep the 20-company target and up to three recommended jobs per company; access restrictions may produce an honest shortfall, not fabricated jobs or unauthorized access.

## Broad and specialist resources

The manual entries below are for the user's own navigation. Supply short title/location keywords, not automatic `site:` queries targeting restricted boards. Conditional integrations are optional and are not installed simply because they appear here.

| Resource | Useful coverage | Default route and conditions |
| --- | --- | --- |
| [LinkedIn Jobs](https://www.linkedin.com/jobs/) | Professional roles and company discovery | **Manual website.** User uses title/location filters. Automated job, company, and member retrieval stays off; only a separately authorized integration with known data/use scope can change this. |
| [Indeed](https://www.indeed.com/) | Broad roles and local/country markets | **Manual website.** Use country and title/location controls personally. Do not automate searches or copy results without the required explicit permission. |
| [ZipRecruiter](https://www.ziprecruiter.com/) | Broad/local roles in supported markets | **Manual website; conditional official integration.** Its [Job Search MCP documentation](https://api.ziprecruiter.com/mcp/docs) describes a provider-supported AI connector. Use only when available through its documented setup and applicable access, output, attribution, and retention scope is established. Publisher/campaign APIs are not interchangeable permissions. |
| [Built In](https://builtin.com/) | Technology companies and related business roles | **Manual website.** Current automation permission remains unverified; use personal role/location controls. Do not derive permission from its editorial articles about scraping. |
| [Y Combinator Jobs](https://www.ycombinator.com/jobs) / [Work at a Startup](https://www.workatastartup.com/) | Startup technical and business roles | **Manual websites; one source.** YC restricts extraction and copying. Discover employers independently through permitted routes; the second domain is not a bypass. |
| [Wellfound](https://wellfound.com/) | Startup roles, pay/equity context | **Manual website.** Copying/harvesting restrictions remain even at human request speed. Employer ATS synchronization is not a third-party collection license. |
| [HiringCafe](https://hiringcafe.com/) | Broad role/location/work-arrangement filters | **Manual website.** Terms restrict copying and redistribution; no general job-search API permission was established. Count `hiring.cafe` and `hiringcafe.com` once. |
| [SimplyHired](https://www.simplyhired.com/) | Broad and local roles | **Manual website, governed by Indeed terms.** No alternate automated route through this domain. Deduplicate vacancies if independently found elsewhere. |
| [Lensa](https://lensa.com/) | Broad/local roles | **Manual website; no AI ingestion by default.** Terms restrict copying/extraction and entering service output into models that may retain it for analysis or other purposes. Do not request Lensa snippets or pasted output as a workaround. |
| [Teal](https://www.tealhq.com/) | Technology, operations, support, and QA | **Manual website.** Retrieval, indexing, copying, and competing-service restrictions require an expressly permitted scope before integration. Account-based tracking and resume products are separate. |
| [Glassdoor](https://www.glassdoor.com/) | Jobs and company context | **Manual homepage guidance.** No automated job/company/review collection or default deep links. Reviews and estimated pay never become employer requirements or advertised salaries. |
| [Dice](https://www.dice.com/) | Technology and contract roles | **Manual homepage guidance.** No default automated navigation, extraction, AI-data reuse, or deep links. Confirm agency versus employer and contract terms independently. |
| [Welcome to the Jungle](https://www.welcometothejungle.com/) / [US service](https://us.welcometothejungle.com/) | Company and professional/startup discovery | **Manual homepage guidance.** Resolve applicable regional terms for any integration; US terms restrict deep links. Otta is the same brand/resource, not separate coverage. |
| [We Work Remotely](https://weworkremotely.com/) | Remote technical and business roles | **Manual unless RSS scope is established.** Its [RSS permission](https://weworkremotely.com/remote-job-rss-feed) requires WWR attribution, while broader service/API rules restrict replacement job-search products and preserve WWR application routes. Resolve applicable scope before this reusable skill uses a feed; no HTML scraping. |
| [Remote OK](https://remoteok.com/) | Remote roles | **Conditional documented feed.** [Official FAQ](https://remoteok.com/faq) describes JSON/RSS reuse with Remote OK credit and original job links. Check current notices/limits and retain required hyperlinks. This permits the documented feed scope, not HTML scraping; no built-in adapter is implied. |
| [Remotive](https://remotive.com/) | Remote roles by function/location | **Manual pending scope resolution.** [API documentation](https://github.com/remotive-com/remote-jobs-api) has a sharing grant with attribution, source links, freshness/rate limits, and display restrictions; broader current terms restrict automation/reuse. Resolve scope before collection rather than silently enabling the API. |

Remote sources remain subject to the user's work-arrangement constraints. A remote label does not establish worldwide eligibility. Multiple boards may syndicate one employer requisition; source breadth and unique vacancy counts are different.

## Country, industry, and entry-level resources

| Market / need | Starting resource | Route and checks |
| --- | --- | --- |
| U.S. federal work | [USAJOBS](https://www.usajobs.gov/) | Manual, or an existing registered API within the actual accepted terms. API output must preserve required values, credit, and USAJOBS view/apply links; storage/export conditions must fit the agreement. Check hiring path, grade, closing date, and eligibility. |
| U.S. apprenticeships | [Apprenticeship.gov](https://www.apprenticeship.gov/) | Manual finder or specifically permitted dataset/API. Government information-page reuse does not license every third-party vacancy or hidden endpoint. Distinguish programs from open jobs. |
| Canada | [Job Bank](https://www.jobbank.gc.ca/) | **Manual only by default:** terms explicitly restrict automated queries, AI, bots, and scripts. Do not use login or indexed-result ingestion as a substitute permission route. |
| Great Britain | [GOV.UK Find a job](https://www.gov.uk/find-a-job) | Manual guidance through the current service link. Service automation scope was not established; GOV.UK guidance licensing does not cover all vacancy content. |
| Northern Ireland | [JobApplyNI](https://www.jobapplyni.com/) | Manual; retrieval/reuse permission unverified. Apply the separate service's rules, not another UK service's terms. |
| Europe | [EURES](https://eures.europa.eu/index_en) and official national employment services | Covered ELA information may allow attributed reuse; automated vacancy access and external national/employer content require their own permission. No blanket job-feed license. |
| Local public work | Official city, state/province, school, university, hospital, and transit careers | Establish the actual domain and permitted method. Check requisition, exams/licenses, and deadlines; public ownership does not automatically license every listing. |
| Nonprofits | [Idealist](https://www.idealist.org/) and nonprofit employers | Idealist is **manual by default**; APIs/widgets/RSS need a separate applicable agreement. Seek permitted employer originals; separate jobs from volunteer roles. |
| Other professions, trades, students, graduates, and returners | Official associations, unions, employer programs, and institution boards | Use established permitted methods or manual guidance. Do not infer credentials, enrollment, graduation-window, or returner eligibility. Program directories are not vacancies. |

For terminology expansion, the [O*NET database](https://www.onetcenter.org/database.html) and [ESCO services](https://esco.ec.europa.eu/en/use-esco/use-esco-services-api) offer licensed resources. Follow their dataset/API-specific terms, attribution, version, and modification requirements in the [audit](source-policy-audit.md). Occupational classifications are not current job posts.

## Original employer and ATS sources

Employer-original verification still requires permission for the method and intended use. Establish official identity and follow actual employer-linked boards; do not infer rights from a familiar host or guess tenants/endpoints. A provider decision may be reused across its established scope, but it does not automatically govern every customer's separate agreement.

| Route | Permitted use and default |
| --- | --- |
| Employer careers | Discover the official career source through the supported host search route; retrieve only with an established permitted method. Otherwise provide manual guidance and find other employers. |
| Greenhouse | **Conditional documented API:** [Job Board API](https://docs.greenhouse.io/job-board.html) provides unauthenticated published-job GET routes for known boards. Confirm employer linkage and report/storage scope; no Harvest/admin access. |
| Lever | **Conditional documented API:** [Postings API](https://github.com/lever/postings-api) supplies published postings from known boards. Follow supported US/EU routes, pagination, limits, and applicable reuse terms. |
| Ashby | **Conditional documented API:** [Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api) supplies a known organization's published jobs. Establish permitted output use; no private recruiting API fallback. |
| Workday | **Automation off unless separately authorized.** Workday site terms restrict extraction; employer tenant terms may differ. Check actual scope, use an authorized feed where available, and do not reverse-engineer browser endpoints or presume `myworkdayjobs.com` is permitted. |
| JazzHR / applytojob | **Automation off unless applicable permission is established.** A public employer posting or another Employ brand's API does not license retrieval. Use an authorized employer feed/integration or manual guidance. |
| iCIMS | **Authorized integration only; site automation off by default.** Its Job Portal API requires authorization and customer/portal context. It is not a no-key public collector route. |
| Avature / other hosts | **Manual unless the exact method is permitted.** Tenant/service terms can differ; use an observed employer link and documented authorization. Never limit employer research solely to the three collector providers. |

The optional [collector](live-discovery.md) implements only documented Greenhouse, Lever, and Ashby listing routes for observed employer-linked boards. Technical support and unauthenticated access are not general aggregation, copyright, retention, or republication licenses. Establish permitted scope before fetching and saving descriptions. A new permission category in this catalog does not add a collector adapter.

## Access failures and reporting

- Stop on login walls, CAPTCHAs, access blocks, or instructions restricting the intended use. Do not switch accounts, tools, mirrors, or hidden endpoints to bypass them. Continue with independently permitted employers and sources.
- Record policy-disabled or unresolved routes as `skipped`; record an actually attempted request that failed access as `blocked`. A separately permitted search is its own `web_search` entry and cannot retroactively turn a manual/skipped board into a completed platform search.
- Store and display only permitted evidence and links. If manual deep-link or AI-ingestion restrictions apply, provide permissible homepage/query guidance instead of preserving the restricted job URL or snippet. An inaccessible lead receives no confident match score.
- Verify current original descriptions and application availability within permitted access before recommendations. A closed posting remains closed even if its application form loads. Clearly separate unverified leads from verified jobs.
- Show actual source coverage, exclusions, policy limitations, inspected candidates, and deduplicated verified openings. Do not equate a blocked route with zero vacancies or claim all listed resources were searched. Preserve the requested report format and explain any shortfall.
