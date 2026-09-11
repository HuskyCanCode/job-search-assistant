# Sample report preview

[Back to the README](../README.md) · [Usage guide](usage-guide.md)

## Open the HTML sample

The [fictional HTML report](../examples/sample-report.html) opens with compact recommended job rows and **View job** links; company research and evidence expand when needed. It uses the same four-company, Canada-based example as the [generated Markdown report](../examples/sample-report.md). The shorter two-company illustration below shows Markdown's company-first layout. Both examples are fictional and leave the 20-company target visibly unmet.

1. Open the HTML sample link. On GitHub, this opens the source/download page.
2. Download the raw file and keep the `.html` extension.
3. Open the downloaded file in your browser, using **Open File** if needed.
4. Search by company, role or location, choose **All postings** for other records, or expand **Why this match / details**. **Reset** returns to recommendations when available, otherwise all records.
5. Use **Print** for the whole report, including records hidden by your current filter; choose Save as PDF in the browser dialog for a PDF copy.

The report opens locally; no hosting or upload is needed. Filters only change the view, not scores or saved search preferences. Its company, job and evidence links are fictional examples. For your own results, ask: “Save my report as HTML I can open locally.” Keep personal reports private and share them only when their contents and source terms permit it.

## Short table illustration

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

The company ratings average the three displayed job scores: `(85 + 80 + 75) / 3 = 80` and `(78 + 72 + 66) / 3 = 72`. Evidence coverage measures how much of the weighted criteria has known evidence, including known gaps; it is separate from match strength. Priorities follow the [matching rules](../references/report-format.md#score-coverage-and-priority), rather than predicting an interview or offer. The preview's illustrative scores are not assessments of a real candidate.

### Suggested search keywords

| Role family | Example reusable query |
| --- | --- |
| Development | `("junior developer" OR "software developer I") "United States" onsite` |
| Quality assurance | `("QA analyst" OR "manual tester") "entry level" "United States"` |
| Support | `("application support" OR "technical support specialist") "United States" onsite` |

Execute queries through an authorized search integration and verify originals through permitted employer sources. The full report also includes requirement-by-requirement evidence, dates, search coverage, and separate unverified or excluded leads. It states how many companies qualify and explains any shortfall; this two-company preview does not fulfill the 20-company target. The separate [complete fictional report](../examples/sample-report.md) uses four companies and a Canada-based scenario to demonstrate those additional tables. See the [report contract](../references/report-format.md) for the full field definitions.
