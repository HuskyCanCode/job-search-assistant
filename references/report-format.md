# Report and input contract

## Finished report

Begin with the date checked, the candidate's stated search scope, the resume/profile used, and the main recommendation. State that fit is a heuristic based on documented professional evidence, not a hiring probability. Include the limits that materially affect this search, such as inaccessible descriptions or unknown sponsorship.

Use these tables, splitting large tables when needed for readability:

| Priority | Role and direct job link | Company | Location / remote limits | Pay | Fit / coverage | Eligibility | Evidence, gaps, next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Application priority | [Verified title](https://example.com/replace-with-verified-post) | Employer | As stated | Currency + period, or unknown | Score or N/A + coverage | Met / unknown / unmet | Concise explanation |

The example URL above is a format illustration only. Replace it with a link actually opened during the search. Record posted and checked dates in the job details table; an unknown posted date remains unknown. Include employment type and requisition ID in notes when available. State what search count means: unique verified open postings after deduplication, not raw search results.

| Role group | Keywords / titles | Why relevant | Reusable query | Suggested source |
| --- | --- | --- | --- | --- |
| Close / adjacent / stretch | User-relevant terms | Link to transferable evidence or goal | Actual query text | Employer site, job board, or search engine |

| Job requirement | Category | Match | Resume / profile evidence | Gap or clarification |
| --- | --- | --- | --- | --- |
| Distinct JD criterion | Rubric category | met / partial / absent / unknown | Specific source section or user statement | Action supported by the evidence |

Provide evidence details for the strongest opportunities and any recommendation that hinges on a disputed or missing requirement. Keep inaccessible leads, known hard blockers, and closed postings separate from active recommendations. Show a short search log with queries/sources used, check date, coverage, and why the search stopped. If zero active matches remain, report zero and suggest specific changes to soft preferences; do not fabricate replacements.

## Repeatable helper

Run from the skill repository root:

```sh
python3 scripts/build_report.py private/search-input.json --output private/job-report.md --csv private/job-report.csv
```

`--output` writes Markdown (`--markdown` is an alias); `--csv` optionally writes a spreadsheet-friendly job summary. The helper uses Python 3.10+ and the standard library. It validates the input, computes the rubric, and renders evidence and job tables without network requests. The agent must verify facts and classify evidence before running it. It cannot determine whether an evidence string is truthful or a job is actually open.

Use `--overwrite` when deliberately regenerating existing output files. Input and output paths must be distinct. Jobs with established eligibility are ordered High, Medium, Explore, then Low, followed by Clarify eligibility, Review evidence, and Not scored. Within each priority, sort by descending fit and coverage, then identifier. Blocked, unverified, and closed records stay in their separate groups. This order places assessed opportunities before records that need more research; it is not a forecast of outcomes.

Use the helper for the comparison portion. Add the keyword/query table and search log above to the final report. The runnable [sample input](../examples/sample-input.json) demonstrates the JSON shape with synthetic data.

## JSON schema version 1

| Root field | Type | Meaning |
| --- | --- | --- |
| schema_version | integer, exactly 1 | Contract version |
| resume_provided | boolean | True only when readable resume evidence or a sufficiently detailed candidate profile was actually used |
| search_summary | string, optional | Scope, profile source, and material assumptions; never include unnecessary personal details |
| jobs | array | Unique job records; an empty array is a valid zero-results report |

If a detailed profile substitutes for a resume, make this explicit in `search_summary`. When `resume_provided` is false, do not create inferred personal requirement assessments; use an empty requirements array or unknown statuses. Personal fit is N/A.

| Job field | Type | Meaning |
| --- | --- | --- |
| id | nonempty string | Unique stable identifier, preferably original requisition ID |
| title, company, location | nonempty strings | Verified values, or explicit Unknown where appropriate |
| url | HTTP(S) URL | Direct posting URL; inaccessible leads may retain their discovered URL with unverified status |
| salary | string or null | Stated range, currency, and period; null when unknown |
| posted_at | YYYY-MM-DD or null | Employer posting date, not crawl/check date |
| checked_at | YYYY-MM-DD | Actual verification/check date |
| posting_status | open / closed / unverified | What the source supports at check time |
| job_description_complete | boolean | Whether a complete substantive description was available |
| requirements | array | Evidence assessments, defined below |
| hard_constraints | array | Applicable material constraints, defined below; empty means eligibility was not established |
| not_applicable_categories | object, optional | Category key to substantive exclusion reason; allowed only with complete JD, with no requirements in the excluded category |
| notes | string, optional | Employment type, requisition/source detail, limitations, or candidate next-step context |

Each requirement has four fields:

| Field | Allowed value |
| --- | --- |
| category | required_skills / responsibilities / seniority / preferred / domain |
| requirement | Nonempty description of a distinct substantive criterion |
| status | met / partial / absent / unknown |
| evidence | String identifying the JD clause and resume/profile source; nonempty for every non-unknown assessment |

Each hard constraint has `constraint` (nonempty string), `status` (`met`, `unmet`, or `unknown`), and `evidence` (nonempty when status is not unknown). Do not insert “no restrictions” as a met constraint to manufacture eligibility certainty. Assess the user's and employer's material constraints, including remote jurisdiction where relevant.

## Score, coverage, and priority

The [matching rubric](resume-matching.md) defines category weights, evidence credit, and exclusions. Weighted coverage measures how much of the applicable rubric has an assessment other than unknown. A partial match contributes half fit credit and full evidence coverage; confidence is evidence completeness, not match quality.

| Assessment state | Rule |
| --- | --- |
| Not assessed | No readable resume or sufficiently detailed profile |
| Insufficient | No criteria, no applicable weights, or zero evidence coverage; score N/A |
| Provisional | Incomplete JD or evidence coverage below 80%; any numeric score is labeled provisional |
| Assessed | Complete JD and evidence coverage at least 80% |

| Evidence confidence | Rule |
| --- | --- |
| High | Complete JD and weighted coverage at least 90% |
| Medium | Complete JD and weighted coverage at least 60% |
| Low | Other scored evidence states, including incomplete descriptions |
| Not assessed | No candidate evidence source |

Application priority follows this order; the first applicable rule wins:

| Condition | Priority |
| --- | --- |
| Posting closed | Inactive |
| Any hard constraint explicitly unmet | Blocked |
| Posting unverified | Lead only |
| No resume/profile | Not scored |
| Evidence insufficient or assessment provisional | Review evidence |
| No hard constraints assessed or any material constraint unknown | Clarify eligibility |
| Assessed, verified open, eligible, score at least 80 | High |
| Same conditions, score 60–79.9 | Medium |
| Same conditions, score 40–59.9 | Explore |
| Same conditions, score below 40 | Low |

Report all material issues even when another rule controls the label. For example, a provisional job with unknown sponsorship needs both evidence review and sponsorship clarification. The thresholds are heuristic workflow choices, not a validated employment prediction model.
