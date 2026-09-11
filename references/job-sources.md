# Active job sources and access rules

Use independent employer evidence and the conditional routes below. Restricted or unverified resources are excluded from this active catalog and from manual recommendations. Their names and policy evidence remain in the [source policy audit](source-policy-audit.md) so they are not accidentally reused. The audit's current exclusion policy takes precedence over older route findings. Follow [search-strategy.md](search-strategy.md) for query expansion, verification, and deduplication.

## Choose a route

1. **Discover employers.** Use an existing supported host search integration within its established terms for role, location, industry, and employer queries. Investigate official employer career sources only through a permitted method. Search-result visibility is not permission to retrieve, process, or save destination content.
2. **Establish scope once.** Before collection, record the provider/method, applicable policy URL and check date, intended purpose, third-party content rights, attribution/link conditions, rate limits, and retention rights. Retention includes tool transcripts, delegated messages, and reports. Reuse the decision while its terms and scope remain current; no repeated approval or policy research for every job. Actual employer/tenant terms must fit that scope.
3. **Keep exclusions in force.** Do not search, ingest, link to as recommendations, or offer manual instructions for excluded resources. A user naming a source, existing login, connector availability, paid access, public URL, or robots allowance does not re-enable it. Do not recover excluded content through targeted indexed searches, snippets, caches, mirrors, aliases, or user-pasted copies. Ignore incidental restricted results and continue with independently obtained evidence. Do not scrape consumer search-result pages.
4. **Honor the agreed search scope.** If the user names an excluded source, explain its exclusion and continue through allowed sources only where the request permits alternatives. An instruction to use only that source must not silently become a broader search. If no compatible live route remains, provide a generic role/keyword plan and state that vacancies were not verified; do not add excluded-site recommendations.
5. **Preserve the requested result.** Build breadth across relevant employers before adding second and third jobs. Retain the 20-company target, up to three recommendations per company, full matching evidence, and company context. Use other allowed routes when useful; report an actual shortfall when the scope cannot be substantiated. Do not relax hard constraints or fabricate jobs.

## Active candidates

Every route is conditional on the actual access and report use. Listing an API or feed here neither installs it nor establishes a blanket content license.

| Route | Scope and conditions |
| --- | --- |
| Official employer careers | Discover the employer independently through supported search. Establish official identity and permission for the access method and intended report use. Follow observed career links and requisitions only; do not guess tenant identifiers or private endpoints. Skip a route whose permission cannot be established. |
| [Greenhouse Job Board API](https://docs.greenhouse.io/job-board.html) | Documented unauthenticated GET routes for published jobs on known employer-linked boards. Establish applicable employer/content/storage rights; no Harvest or administrative API substitution. |
| [Lever Postings API](https://github.com/lever/postings-api) | Documented published postings for known employer-linked boards, with supported US/EU routes and pagination. Preserve applicable content, display, retention, and rate conditions. |
| [Ashby Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api) | Documented public postings for a known employer board. Use only listed public jobs within established rights; no private recruiting API fallback. |
| [Remote OK documented feeds](https://remoteok.com/faq) | Optional for compatible remote searches. Its documented feed grant requires Remote OK credit and original job links; check current notices, limits, and report compatibility before use. Keep those required links in every output. Feed access does not authorize HTML scraping or imply worldwide eligibility. |
| [USAJOBS registered API](https://developer.usajobs.gov/apirequest/index) | Optional for compatible U.S. federal searches through an existing authorized key and the actual accepted agreement. Preserve required displayed values, USAJOBS credit, and view/apply links. Follow purpose/storage/export restrictions and resolve conflicting terms before use. Do not create an account or request a key merely to fill the report. |

The [included collector](live-discovery.md) implements only Greenhouse, Lever, and Ashby listing routes. Its URL checks cannot verify contracts, employer rights, or the host's handling of data. Establish scope before fetching and saving descriptions; unauthenticated access is not unrestricted aggregation or republication permission. The other active candidates have no built-in adapter merely because they are listed here.

## Terminology resources

Use the [O*NET downloadable database](https://www.onetcenter.org/database.html) or [ESCO services](https://esco.ec.europa.eu/en/use-esco/use-esco-services-api) for role and keyword expansion under their dataset-specific licenses. Preserve required source credit, actual version, license links, and notices of changes. O*NET's registered API conditions differ from its database license; ESCO content rights differ from its API software license. See the [audit](source-policy-audit.md) for details. Neither resource supplies verified live vacancies.

## Verification and reporting

- Stop on login walls, CAPTCHAs, access controls, or restrictions on the intended use. Do not change accounts, tools, hosts, or hidden endpoints to bypass them.
- Treat collection as discovery. Verify each recommended job's full description, employer identity, location, eligibility, and current application availability through allowed evidence. A closed posting remains closed even if an application form loads.
- Preserve mandatory feed credit, original job links, and application routes when deduplicating. Prefer an independently sourced employer URL only when compatible with those obligations. If the report helper cannot meet a source's conditions, use a compliant manual rendering or omit that source's material.
- Record excluded or unresolved methods as `skipped`; an actually attempted permitted request that fails is `blocked`. Record independent host searches as `web_search`. Do not claim an excluded source was searched or equate an access failure with zero jobs.
- Include only permitted evidence and links in job records. Keep unverified leads separate without confident match scores; omit restricted content entirely. Report actual source coverage, unique verified openings, remaining unknowns, and any shortfall. These rules reduce risk but do not guarantee legal compliance or identical coverage.
