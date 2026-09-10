# Resume analysis and job matching

## Build the candidate profile

Extract professional experience into an evidence ledger: fact, source section/page, and certainty. Keep the user's aspirations separate from demonstrated experience. Preserve employment dates as stated; do not double-count overlapping jobs or assume a skill was used throughout an entire tenure. A skills-list mention can establish familiarity but does not prove duration, proficiency, ownership, or business results.

Use accomplishments, scope, responsibilities, and recency to interpret transferable experience. Accept equivalent tools or credentials when the job allows equivalence; explain partial matches instead of silently treating related tools as identical. A resume omission is **unknown**, not proof the person lacks a skill. Use **absent** only for an explicit mismatch supported by the profile or a user statement. Do not invent resume achievements to improve a score.

If the user's description conflicts with the resume, identify the discrepancy and ask when it changes the recommendation. Use a sufficiently detailed user-provided professional profile in place of a resume only when the report labels that source clearly. Otherwise return N/A for personal fit.

## Requirement evidence

Extract distinct substantive criteria from the job description. Split compound requirements where each part affects qualification. Do not split one competency into many redundant entries to increase its influence. For “A or B,” assess the allowed alternative; for “A and B,” evaluate both. Distinguish employer requirements from preferences and boilerplate.

Every non-unknown assessment needs an evidence string that identifies both the JD clause and the resume section/page or user statement. Quote only short necessary fragments and paraphrase the rest. For example: `JD asks for customer onboarding; resume, Experience > Client Associate, bullet 2 describes onboarding 25 clients.`

| Status | Meaning | Credit |
| --- | --- | ---: |
| met | Evidence satisfies the criterion at the requested scope | 1 |
| partial | Relevant evidence covers only part of the criterion or scope | 0.5 |
| absent | An explicit, evidenced mismatch | 0 |
| unknown | Insufficient information in the resume/profile or JD | 0 |

Unknown receives no documented-fit credit but must be reported separately from a confirmed gap. Describe low scores with low coverage as incomplete evidence, not a negative judgment about ability.

## Weighted rubric

| Category key | What it measures | Weight |
| --- | --- | ---: |
| required_skills | Required technical, operational, interpersonal, or credential-related competencies | 35 |
| responsibilities | Evidence of performing the role's core work | 25 |
| seniority | Relevant depth, scope, ownership, and leadership | 20 |
| preferred | Employer-stated optional qualifications | 10 |
| domain | Relevant industry or subject-matter experience when relevant to the JD | 10 |

Within each category, criteria have equal weight. Category credit is the average of its requirement credits. Documented fit is `100 × sum(category weight × category credit) / sum(applicable category weights)`.

A category with missing evidence keeps its weight and contributes zero points and zero evidence coverage. A category can be declared not applicable only after reading a complete JD and recording a substantive reason; it cannot be excluded because the candidate lacks evidence. For example, a JD with no preferred qualifications may justify excluding `preferred`. Remove explicitly excluded weights from the denominator and disclose exclusions. Do not compare scores as if they used identical requirements when the jobs differ. An empty requirement set or no applicable categories yields N/A.

Evidence coverage uses the same category weights and the fraction of criteria whose status is not unknown. Confidence describes the completeness of evidence, not the chance of getting hired. The helper applies the fixed confidence and priority rules documented in [report-format.md](report-format.md). Incomplete descriptions make a score provisional; insufficient evidence can suppress the score. Keep full calculations available for inspection.

## Eligibility and application priority

Check relevant hard constraints separately: location, remote jurisdiction, schedule, travel, employment type, user-defined salary floor, mandatory license, and work authorization/sponsorship only where explicitly provided or required. Label each met, unmet, or unknown, with its source. Never infer authorization from citizenship assumptions, a name, or a university. Do not count an eligibility-only requirement again as a skill just to penalize it twice.

One confirmed hard blocker prevents a top application recommendation regardless of fit. An unknown material constraint means “clarify first.” A remote label alone does not establish geographic eligibility. “Salary not posted” does not establish that a pay floor is met or unmet.

Use application priority to describe where to focus effort. Explain the largest demonstrated strengths, gaps, unknowns, and a practical next action: tailor a truthful accomplishment, verify sponsorship, prepare a portfolio example, or pursue a more suitable adjacent role. No score is an ATS score or an interview/offer probability. Hiring likelihood cannot be estimated reliably from these inputs.
