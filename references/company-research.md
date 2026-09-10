# Company research for a job search

Use this reference with [search-strategy.md](search-strategy.md), [resume-matching.md](resume-matching.md), and [report-format.md](report-format.md). Research live sources during each run; do not reuse old company facts without checking their dates and scope.

## Company-first scope

- Target **20 distinct employers**, unless the user sets another number. This is a research target, not permission to invent companies, relax hard constraints, or pad the report.
- Present a linked company name and company summary, followed by **up to three recommended open jobs** at that employer. Link every job to its verified original posting; provide an application entry link when separately available.
- Select jobs using the existing application-priority and documented-fit rules. Do not recommend a known hard blocker just to supply three rows. Show material unknown eligibility beside a conditional recommendation.
- Fewer than three suitable jobs is valid. State how many were verified and why fewer were retained. Keep unverified leads separate and unscored.
- Count employers with retained verified open opportunities separately from companies inspected or listed only as leads. If fewer than 20 qualify, state the achieved count, coverage, and stopping reason.
- Deduplicate parent/brand aliases and mirrored boards. One requisition advertised in several cities is one job; preserve all offered locations. Do not create separate company entries for its cities.

## Establish the employer and reporting scope

Open the official company website and follow its careers links. Confirm that the employer, brand, recruiting agency, ATS board and job posting refer to the same organization. A familiar ATS hostname alone does not establish identity.

Record the company display name, official website, relevant legal entity when identifiable, parent/brand relationship, and geography covered by the company facts. If a staffing agency recruits for an unnamed client, identify the agency and the undisclosed-client limitation; do not assign the agency's workforce facts to the client.

Default to one company entry for a parent and its aliases. A subsidiary may be distinct only when evidence establishes a separate recruiting employer and separate opportunities; disclose the parent relationship and avoid presenting several aliases as additional employers. Use parent-level facts only with an explicit parent-level label. Do not silently substitute group headcount or layoffs for a subsidiary's facts.

## Evidence and freshness

Prefer sources in this order, while choosing the source that actually covers the claim:

1. Official filings, annual reports, company statements, and employer career pages.
2. Official public notices, including applicable regional WARN notices for a specific layoff event.
3. Credible journalism that attributes dates, affected workforce and entity scope.
4. Clearly labeled third-party estimates or platform company profiles when better evidence is unavailable.

For each fact retain a direct source URL, source publication date when known, the fact's **as-of date**, actual check date, entity/geographic scope, and whether the value is reported, estimated or derived. A current page can contain an old fact. A crawl date is neither its publication date nor its measurement date.

Use short paraphrases and keep source provenance for disputed facts. When sources conflict, compare dates, definitions and scope before selecting a value. If they remain incompatible, report the disagreement or unknown rather than silently choosing a convenient number.

## Company size

Report an exact employee count, a stated range, or a labeled estimate according to the evidence. Include the source and as-of date, plus geography and entity scope. Preserve qualifiers such as full-time employees, employees and contractors, or consolidated group.

- Do not convert an employee range into an exact count or midpoint presented as fact.
- LinkedIn's employee-size band and the number of profiles associated with a company are different metrics. Neither becomes an official workforce count because it is displayed on LinkedIn.
- If only associated-profile counts are available, label that metric and platform explicitly. Do not present it as total employees.
- Funding, revenue, open jobs and office count do not establish employee count.
- Use **Unknown — no usable workforce figure found** when evidence is missing. An access failure should say **Unknown — source access limited**, not zero employees.

## Employee headcount trend

Interpret a requested company “population trend” as **employee headcount trend** unless the user clarifies a different metric. State this assumption. Use the last **12 months** by default, or the user's chosen period.

Seek two dated observations with comparable entity scope, geography, worker definition and measurement method. Annual official figures may support a nearby reporting period; label its actual endpoints instead of calling it the last 12 months. Do not mix an official employee count with a platform associated-profile count.

With comparable exact counts, show the endpoints and derive:

`change = later_count - earlier_count`

`percent_change = 100 * change / earlier_count`, only when the earlier count is greater than zero.

Label this a calculated change in the reported metric. Use growing, shrinking or unchanged **reported count** according to those observations. Do not infer future hiring or individual job security from it.

- Overlapping size ranges generally do not establish a direction. Preserve the ranges and mark the trend unknown unless other evidence supports the direction.
- A single current count cannot establish a trend. “We are growing” is a company statement, not a measured headcount series.
- Hiring advertisements are not evidence of net employee growth; replacement hiring can coexist with cuts.
- Acquisitions, divestitures and reorganizations can change reporting scope. Disclose these when established; do not imply organic growth from an incomparable series.
- Use **Mixed** only when sourced segments or comparable measures show different directions; explain which. Use **Unknown** for missing or incomparable evidence.
- A third-party trend can be reported as an attributed estimate with its period and methodology limits; do not upgrade it to an official result.

## Latest publicly reported layoff

Research the **latest publicly reported layoff found**, not the unknowable date of every layoff. Default to a **24-month search window**, plus a broad latest/history query without that date restriction so an older report can be identified. Honor a user-specified period and disclose the actual period searched.

Search the established employer name and relevant parent/brand aliases with layoff, workforce reduction, job cuts and restructuring terms. Inspect company statements/filings, credible news, and relevant public notices. Record the actual queries, sources checked, dates and access limits. Do not claim to have searched a source that was only listed as a possible resource.

For each retained event distinguish:

| Field | What to record |
| --- | --- |
| Announcement date | Date the employer announced the event, if established |
| Report date | Publication date of the source reporting it |
| Effective date or range | When the workforce reduction occurred or is planned to occur |
| Date type displayed | Label the displayed event date announcement or effective; retain a source publication date in the summary without substituting it for the event date |
| Status | Announced/planned, in progress, completed, cancelled or unknown as supported |
| Affected count | Reported count/range and location/entity; unknown if undisclosed |
| Scope | Whole company, parent group, subsidiary, region, office or other reported scope |
| Source and window | Direct supporting link, actual check date, searched period and limitations |

Deduplicate articles and notices describing the same event. A later article repeating an old reduction does not make it a new layoff. Identify the most recent distinct announcement/event found; preserve both its reporting and effective dates. If a newly reported historical event and a future announced reduction differ, show that distinction instead of forcing one ambiguous date.

Keep these outcomes distinct:

- **Reported event found:** give the supported dates and scope; an older event may be labeled as the latest found outside the default window.
- **No report found in the searched window:** searches were completed but found no supported event. This does **not** mean no layoffs occurred. State whether broader history found an older event.
- **Unknown / research incomplete:** access limitations, unresolved entity identity or inadequate event evidence prevent a conclusion. A supported event with no exact date remains **reported**, with an unknown event date; a missing date alone does not erase the event. Do not substitute “no report found” for a blocked search.

A regional WARN notice supports its stated employer, facility, dates and affected workers. Absence from a particular notice list does not establish that the company had no layoffs globally. Do not treat announced restructuring, attrition, a hiring freeze or unfilled positions as completed layoffs without evidence. Do not use layoffs to infer anything about protected personal attributes.

## Company match rating

The company rating is an aggregation of the user's **documented job fit**, not a reputation, financial stability, employer quality, layoff-risk or hiring-probability rating.

Compute it as the arithmetic mean of the available numeric fit scores for **up to three recommended, verified open jobs** at that company, using the existing rubric. Exclude closed/unverified jobs, incomplete descriptions, known hard blockers and N/A scores. Use the underlying scores before display rounding; disclose the contributing job IDs and count. Do not substitute lower-ranked roles just to fill missing scores.

If fewer than three recommended jobs have a score, average only those available and label the sample size. If none have a score, the company rating is **N/A**. Without readable resume/profile evidence, a personal company match rating is also N/A.

Retain each job's coverage, provisional status and eligibility notes. Mark the company rating provisional if fewer than three recommendations are scored, any job score is provisional, any recommended job has unknown eligibility, or any recommended job is unscored. Keep the specific eligibility questions visible. Comparisons across companies use different jobs and requirements; the aggregate is a prioritization aid, not a validated prediction.

Do not add bonuses or penalties for company size, growth, layoffs, missing company data, prestige or personal protected attributes. Present workforce facts beside the rating so the user can make their own decision. Any user-requested company preferences belong in an explicitly separate comparison, not hidden changes to the job-fit formula.

## Delivery check

For every company entry, provide its official link, rating and contributing count, size with date/source, headcount trend with period/source, and latest publicly reported layoff result with date type/scope/source. Follow it with up to three linked job rows containing location/work style, pay, employment type, fit/coverage, strengths, gaps, eligibility and a useful next action. Keep missing facts visible as unknown, and report fewer companies or jobs when the evidence does not support the target.
