"""Render a validated report as a self-contained, offline HTML document.

Assessment and ordering come from build_report; this module only presents them.
No network calls, external assets, persisted browser state, or client-side scoring.
"""

from html import escape
from pathlib import Path
import re
from urllib.parse import urlsplit


TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "report-template.html"
TOKENS = {"META", "SCOPE", "STATS", "FILTERS", "COMPANIES", "JOBS", "SOURCES", "METHOD"}
TOKEN_PATTERN = re.compile(r"@@REPORT_([A-Za-z0-9_]+)@@")


def text(value):
    return escape(str(value), quote=True)


def link(url, label, css=""):
    """Validate destinations again at the rendering boundary, then escape them."""
    if not isinstance(url, str) or any(c.isspace() or ord(c) < 32 or c == "\\" for c in url):
        raise ValueError("HTML links require a safe HTTP(S) URL")
    try:
        parsed = urlsplit(url)
        parsed.port
        if (parsed.scheme not in ("http", "https") or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or any(c in parsed.hostname for c in '<>"{}|^`%')):
            raise ValueError
    except ValueError as error:
        raise ValueError("HTML links require a safe HTTP(S) URL") from error
    return f'<a href="{text(url)}" class="{text(css)}" target="_blank" rel="noreferrer noopener">{text(label)}</a>'


def badge(label, tone="neutral"):
    return f'<span class="badge {tone}">{text(label)}</span>'


def paragraph(value, css=""):
    return f'<p class="prose {css}">{text(value)}</p>'


def source_links(sources, label_key="label"):
    if not sources:
        return '<p class="muted">No supporting sources supplied.</p>'
    return '<ul class="source-list">' + ''.join(
        f'<li>{link(source["url"], source[label_key])}</li>' for source in sources) + '</ul>'


def table(headers, rows, caption, css="evidence-table", job_keys=None):
    heading = ''.join(f'<th scope="col">{text(header)}</th>' for header in headers)
    body = ''.join(('<tr' + (f' data-compared-job="{text(job_keys[index])}"' if job_keys else '') + '>')
                   + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>' for index, row in enumerate(rows))
    return (f'<div class="table-scroll" role="region" aria-label="{text(caption)}" tabindex="0">'
            f'<table class="{css}"><caption class="sr-only">{text(caption)}</caption>'
            f'<thead><tr>{heading}</tr></thead><tbody>{body}</tbody></table></div>')


def score_markup(result, company=False):
    if result["score"] is None:
        label = "No scored recommendations" if company else result["assessment"].capitalize()
        score = '<strong class="score-value">N/A</strong>'
    else:
        label = result["assessment"].capitalize()
        score = f'<strong class="score-value">{result["score"]:.1f}<span>/100</span></strong>'
    coverage = f'{result["coverage"]:.1f}%' if result["coverage"] is not None else "N/A"
    return (score + f'<span class="score-label">{text(label)}</span>'
            f'<span class="small muted">Evidence coverage {coverage}</span>')


def company_facts(company, result, api):
    facts = api.company_fact_texts(company)
    sections = []
    for heading, fact, key in zip(("Company size", "Headcount trend", "Latest reported layoff"),
                                   facts, ("size", "headcount_trend", "latest_layoff")):
        sections.append(f'<section><h4>{heading}</h4>{paragraph(fact)}'
                        + source_links(company[key]["sources"]) + '</section>')
    components = ", ".join(result["component_job_ids"]) or "None"
    sections.append('<section><h4>Company match calculation</h4>'
                    + paragraph(f'Scored components: {components}. {result["scored_count"]} scored of '
                                f'{len(result["recommendations"])} recommended jobs. '
                                f'{result["eligible_job_count"]} complete, recorded-open postings without a confirmed blocker.')
                    + paragraph(f'Company research checked: {company["checked_at"]}.', "muted") + '</section>')
    return '<div class="company-facts">' + ''.join(sections) + '</div>'


def job_evidence(job, result, resume, api):
    rows = []
    for row in job["requirements"]:
        rows.append([text(api.LABELS[row["category"]]), text(row["requirement"]),
                     text(row["status"] if resume else "not assessed"),
                     text((row["evidence"] or "No evidence supplied") if resume else "No resume/profile supplied")])
    if not rows:
        rows = [["—", "No requirements supplied", "Insufficient evidence", "—"]]
    parts = []
    if not resume:
        parts.append(paragraph("No resume/profile supplied: personal-fit evidence is not assessed.", "notice-inline"))
    parts.append(table(("Category", "Job requirement", "Assessment", "Job / résumé evidence"), rows,
                       "Requirement evidence for " + job["title"]))
    constraints = [[text(row[key]) for key in ("constraint", "status", "evidence")]
                   for row in job["hard_constraints"]]
    if not constraints:
        constraints = [["No constraints supplied", "Unknown", "Eligibility has not been established"]]
    parts.append('<h4>Hard constraints</h4>' + table(("Constraint", "Status", "Evidence"), constraints,
                                                    "Hard constraints for " + job["title"]))
    categories = []
    for row in result["categories"]:
        categories.append([text(api.LABELS[row["category"]]), "Excluded" if row["excluded"] else str(row["weight"]),
                           str(row["count"]), "N/A" if row["excluded"] or not resume else f'{row["credit"] * 100:.1f}%',
                           "N/A" if row["excluded"] or not resume else f'{row["coverage"] * 100:.1f}%'])
    parts.append('<h4>Calculation details</h4>' + table(("Category", "Weight", "Criteria", "Credit", "Known evidence"),
                                                       categories, "Calculation details for " + job["title"]))
    parts.append(paragraph(f'Applicable weight denominator: {result["denominator"]}.', "small"))
    for category, reason in job.get("not_applicable_categories", {}).items():
        parts.append(paragraph(f'Excluded {api.LABELS[category]}: {reason}', "small"))
    if job.get("notes"):
        parts.append('<h4>Researcher notes</h4>' + paragraph(job["notes"]))
    if job.get("discovered_via"):
        parts.append('<h4>Discovery sources & original links</h4>' + source_links(job["discovered_via"], "source"))
    parts.append('<p class="small">Record ID: ' + text(job["id"]) + ' · '
                 + link(job["url"], "Original job posting") + '</p>')
    return ''.join(parts)


def job_card(job, result, resume, recommended, key, api):
    group = api.job_group(job, result)
    review = group in ("open", "unverified") and result["priority"] in (
        "Clarify eligibility", "Review evidence", "Not scored", "Lead only")
    search = " ".join((job["company"], job["title"], job["location"]))
    attrs = (f'data-job data-search="{text(search)}" data-recommended="{str(recommended).lower()}" '
             f'data-review="{str(review).lower()}" data-nonactive="{str(group != "open").lower()}"')
    status_label = {"open": "Open posting", "blocked": "Eligibility blocker", "unverified": "Unverified lead", "closed": "Closed posting"}[group]
    tone = "good" if group == "open" else "caution" if group in ("blocked", "unverified") else "neutral"
    markers = (badge("Recommended", "good") if recommended else "") + badge(status_label, tone)
    markers += badge(result["priority"])
    facts = (("Location", job["location"]), ("Pay", job["salary"] or "Not posted / unknown"),
             ("Posted", job["posted_at"] or "Unknown"), ("Checked", job["checked_at"]),
             ("Full description", "Complete" if job["job_description_complete"] else "Incomplete / unavailable"))
    meta = '<dl class="job-meta">' + ''.join(f'<div><dt>{label}</dt><dd>{text(value)}</dd></div>' for label, value in facts) + '</dl>'
    strengths = result["strengths"]
    gaps = result["constraint_issues"] + result["gaps"] + ["Unknown: " + item for item in result["unknowns"]]
    highlights = []
    for label, values, empty in (("Documented strengths", strengths, "Not established"),
                                 ("Gaps & questions", gaps, "None documented")):
        summary = "; ".join(values[:3]) or empty
        if len(values) > 3:
            summary += f"; {len(values) - 3} more in evidence"
        highlights.append('<div><h4>' + label + '</h4>' + paragraph(summary) + '</div>')
    return (f'<article class="job-card" id="{key}" {attrs}>'
            '<div class="job-top"><div><div class="badges">' + markers + '</div>'
            '<h3>' + link(job["url"], job["title"]) + '</h3><p class="company-byline">' + text(job["company"]) + '</p></div>'
            '<div class="job-score">' + score_markup(result) + f'<span class="small">{text(result["confidence"])} confidence</span></div></div>'
            + meta + '<div class="job-highlights">' + ''.join(highlights) + '</div>'
            + '<p class="next-action"><strong>Next action</strong> ' + text(result["next_action"]) + '</p>'
            + '<div class="eligibility-line">Eligibility: <strong>' + text(result["eligibility"]) + '</strong>'
            + ' · Recorded status: ' + text(job["posting_status"]) + '</div>'
            + '<details class="evidence"><summary>Evidence, constraints & sources <span aria-hidden="true">↗</span></summary>'
            + '<div class="details-body">' + job_evidence(job, result, resume, api) + '</div></details></article>')


def company_overview(companies, results, keys, resume, api):
    rows = []
    for rank, company in enumerate(companies, 1):
        result = results[company["id"]]
        key = keys[company["id"]]
        size, trend, layoff = company["size"], company["headcount_trend"], company["latest_layoff"]
        name = link(company["url"], company["name"], "company-name") if company["url"] else text(company["name"])
        company_cell = f'<span class="row-number">{rank:02d}</span><strong>{name}</strong>'
        if not company["url"]:
            company_cell += '<span class="small muted">Website unknown</span>'
        company_cell += f'<span class="small muted">Checked {text(company["checked_at"])}</span>'
        company_cell += f'<a class="detail-link" href="#{key}">Explore company <span aria-hidden="true">↘</span></a>'
        size_cell = '<strong>' + text(size["value"] or "Unknown") + '</strong>'
        size_cell += f'<span class="small muted">{text(size["basis"].capitalize())} · as of {text(size["as_of"] or "unknown")}</span>'
        size_cell += f'<a class="small" href="#{key}-facts">Scope & sources</a>'
        trend_cell = badge(trend["direction"].capitalize(), "good" if trend["direction"] == "growing" else "neutral")
        trend_cell += '<span class="small muted">' + text(
            f'{trend["period_start"]} to {trend["period_end"]}' if trend["period_start"] else "Period unknown") + '</span>'
        if layoff["status"] == "reported":
            date_type = layoff["date_type"]
            if date_type == "effective" and layoff["event_date"] > company["checked_at"]:
                date_type = "scheduled effective"
            layoff_cell = '<strong>' + text(layoff["event_date"] or "Date unknown") + '</strong>'
            layoff_cell += '<span class="small muted">Latest reported · ' + text(date_type) + '</span>'
        elif layoff["status"] == "none_found":
            layoff_cell = '<strong>None found in checked sources</strong><span class="small muted">Not proof of no layoffs</span>'
        else:
            layoff_cell = '<strong>Unknown</strong><span class="small muted">No conclusion established</span>'
        if layoff["searched_from"]:
            layoff_cell += '<span class="small muted">Checked window: ' + text(
                f'{layoff["searched_from"]} to {layoff["searched_through"]}') + '</span>'
        layoff_cell += f'<a class="small" href="#{key}-facts">Research & sources</a>'
        recommendations = []
        for job in result["recommendations"]:
            assessment = api.assess(job, resume)
            recommendations.append('<li>' + link(job["url"], job["title"]) + '<span class="small muted">'
                                   + text(f'{assessment["priority"]} · Eligibility {assessment["eligibility"]}') + '</span></li>')
        rec_cell = '<ol class="recommended-list">' + ''.join(recommendations) + '</ol>' if recommendations else '<span class="muted">No recommended openings</span>'
        score = score_markup(result, company=True)
        score += f'<span class="small muted">{result["scored_count"]}/{len(result["recommendations"])} recommended jobs scored</span>'
        cells = (company_cell, score, size_cell, trend_cell, layoff_cell, rec_cell)
        rows.append(f'<tr data-company-row data-company-key="{key}">' + ''.join(f'<td>{cell}</td>' for cell in cells) + '</tr>')
    if not rows:
        rows = ['<tr><td colspan="6" class="empty-cell">No companies supplied.</td></tr>']
    return ('<section id="company-overview" class="report-section"><div class="section-heading"><div>'
            '<span class="eyebrow">01 / The shortlist</span><h2>Company overview</h2></div>'
            '<span class="section-note">Company websites · up to 3 recommended roles</span></div>'
            '<div class="table-scroll company-table-wrap" role="region" aria-label="Company overview; scroll to see all columns" tabindex="0">'
            '<table class="company-table"><caption class="sr-only">Company overview with match, size, trend, reported layoffs and recommended jobs</caption>'
            '<thead><tr><th scope="col">Company</th><th scope="col">Company match</th><th scope="col">Company size</th>'
            '<th scope="col">Headcount trend</th><th scope="col">Latest reported layoff</th><th scope="col">Recommended jobs</th></tr></thead>'
            '<tbody>' + ''.join(rows) + '</tbody></table></div></section>')


def source_audit(data):
    sources = data.get("search_sources", [])
    rows = []
    for source in sources:
        rows.append([link(source["url"], source["source"]) + '<span class="small muted">' + text(source["method"]) + '</span>',
                     text(source["query"]), badge(source["status"].capitalize()), text(source["checked_at"]),
                     text(source["results_seen"] if source["results_seen"] is not None else "Unknown"),
                     text(source["verified_open"]), text(source["notes"])])
    content = table(("Source / method", "Query or request", "Status", "Checked", "Results seen", "Verified open", "Notes"),
                    rows, "Sources checked") if rows else paragraph("No source checks were supplied.", "muted")
    return ('<section id="source-audit" class="report-section"><details class="audit-disclosure"><summary>'
            f'Search coverage & source audit <span class="small">{len(sources)} recorded checks</span></summary>'
            '<div class="details-body">' + paragraph(
                "Counts describe records actually inspected, not all available vacancies. The same job can appear in several checks; "
                "do not sum source counts as unique jobs. Blocked or skipped sources have unknown availability, not zero vacancies.")
            + content + '</div></details></section>')


def job_comparison(jobs, assessments, keys):
    """Keep a compact tabular comparison beside the expanded reading view."""
    if not jobs:
        return ""
    rows = []
    for job in jobs:
        result = assessments[job["id"]]
        rows.append([
            link(job["url"], job["title"]) + f'<br><a href="#{keys[job["id"]]}">View details</a>',
            text(job["location"]), text(job["salary"] or "Not posted / unknown"),
            score_markup(result), text(result["eligibility"]) + " · " + text(result["priority"]),
            text(job["posting_status"]), text(result["next_action"]),
        ])
    return ('<details class="comparison"><summary>Compare openings in a table</summary><div class="details-body">'
            + table(("Role / posting", "Location", "Pay", "Fit / coverage", "Eligibility / priority", "Status", "Next action"),
                    rows, "Job comparison", "evidence-table job-comparison", [keys[job["id"]] for job in jobs])
            + '</div></details>')


def render_html(data, report_api):
    """Present a validated v1/v2 report using the existing report assessment API."""
    api = report_api
    resume = data["resume_provided"]
    jobs = api.ordered_jobs(data)
    assessments = {job["id"]: api.assess(job, resume) for job in jobs}
    version_two = data["schema_version"] == 2
    results = api.company_assessments(data) if version_two else {}
    companies = api.ordered_companies(data, results) if version_two else []
    keys = {company["id"]: f'company-{index}' for index, company in enumerate(companies, 1)}
    job_keys = {job["id"]: f'job-{index}' for index, job in enumerate(jobs, 1)}
    recommended = {job_id for result in results.values() for job_id in result["recommended_job_ids"]}
    qualifying = sum(bool(result["recommendations"]) for result in results.values())
    opened = sum(job["posting_status"] == "open" for job in jobs)
    target = data.get("company_target", 20)
    dates = ([job["checked_at"] for job in jobs] + [company["checked_at"] for company in companies]
             + [source["checked_at"] for source in data.get("search_sources", [])])
    latest = max(dates) if dates else None
    meta = '<span>Job search assistant</span><span>' + text("Latest evidence check: " + latest if latest else "Research dates unavailable") + '</span>'
    scope = paragraph(data.get("search_summary") or "No search scope was supplied. Review the recorded evidence and source limits before taking action.")
    scope += paragraph("Posting status and research were supplied by the researcher. This offline report does not verify links or read your résumé.", "small muted")
    if not version_two:
        scope += paragraph("Legacy job-only report: company research, company ratings, company target coverage and top-three company recommendations were not supplied.", "notice-inline")
    stats = []
    if version_two:
        stats.extend(((str(len(companies)), "Companies researched", "Distinct company records"),
                      (f'{qualifying}<span> / {target}</span>', "Qualifying companies", f'{max(0, target - qualifying)} below the target')))
    stats.append((str(opened), "Recorded open postings", "Researcher-verified status; includes blockers"))
    stats.append((str(len(recommended)) if version_two else str(len(jobs)),
                  "Recommended jobs" if version_two else "Job records", "Up to 3 per company" if version_two else "No company recommendations supplied"))
    stats_html = ''.join('<div class="stat"><strong>' + value + '</strong><span>' + label + '</span><small>' + note + '</small></div>'
                         for value, label, note in stats)
    filters = '<option value="all">All postings</option>'
    if version_two:
        filters += '<option value="recommended">Recommended</option>'
    filters += '<option value="review">Needs review</option><option value="nonactive">Blocked / unverified / closed</option>'
    company_html = ""
    if version_two:
        company_html = company_overview(companies, results, keys, resume, api)
    sections = []
    if version_two:
        for company in companies:
            key, result = keys[company["id"]], results[company["id"]]
            cards = ''.join(job_card(job, assessments[job["id"]], resume, job["id"] in recommended,
                                     job_keys[job["id"]], api) for job in result["jobs"])
            title = link(company["url"], company["name"]) if company["url"] else text(company["name"])
            sections.append(f'<section class="company-section" id="{key}" data-company-section data-company-key="{key}" '
                            f'data-company-name="{text(company["name"])}"><div class="company-heading"><h2>{title}</h2>'
                            f'<span>{len(result["jobs"])} job records · {len(result["recommendations"])} recommended</span></div>'
                            f'<details class="company-research" id="{key}-facts"><summary>Company research & rating sources</summary>'
                            + company_facts(company, result, api) + '</details>'
                            + job_comparison(result["jobs"], assessments, job_keys)
                            + (cards or '<p class="empty-cell">No job records supplied for this company.</p>') + '</section>')
    else:
        sections = [job_comparison(jobs, assessments, job_keys)]
        sections.extend(job_card(job, assessments[job["id"]], resume, False, job_keys[job["id"]], api) for job in jobs)
    jobs_html = ('<section id="job-details" class="report-section"><div class="section-heading"><div><span class="eyebrow">'
                 + ('02 / A closer look' if version_two else '01 / A closer look') + '</span><h2>'
                 + ('Jobs by company' if version_two else 'Job details') + '</h2></div><span class="section-note">Documented fit · evidence · next steps</span></div>'
                 + ''.join(sections) + ('' if jobs else '<p class="empty-cell">No jobs were supplied. No job fit scores or recommendations were generated.</p>') + '</section>')
    method = ('<details id="methodology" class="audit-disclosure"><summary>How to read the scores & recommendations</summary><div class="details-body methodology">'
              + paragraph("Fit measures documented alignment, not employer quality, an ATS score, or the probability of an interview, offer or hiring. "
                          "Company size, headcount trends and layoffs do not change fit. Unknown evidence is distinct from a confirmed mismatch.")
              + paragraph("Company match is the mean fit of scored jobs among that company's top three recommendations. Coverage is the mean evidence coverage of those scored components. "
                          "Fewer than three scored jobs, provisional evidence, unknown eligibility or an unscored recommendation makes the company rating provisional. "
                          "Only complete, recorded-open postings without a confirmed blocker count toward the company target; recommendations may still need eligibility or evidence review.")
              + paragraph("Weights: required skills 35, responsibilities 25, seniority 20, preferred 10, domain 10. Criteria within each category have equal weight: met 1, partial 0.5, absent 0, unknown 0. "
                          "Missing undeclared categories keep their weight and receive no credit or coverage. Only justified exclusions from a complete description leave the denominator. "
                          "Fit = 100 × weighted credit / applicable weight; coverage uses the fraction of criteria with known evidence. Entirely unknown or empty evidence yields N/A.")
              + paragraph("High confidence requires a complete description and at least 90% coverage; medium requires a complete description and at least 60%; otherwise confidence is low. "
                          "Scores are provisional for incomplete descriptions or coverage below 80%. High / Medium / Explore / Low use 80 / 60 / 40 thresholds only for assessed, open postings with met constraints. "
                          "Closed postings are inactive; confirmed blockers override fit; unverified postings remain leads; missing evidence or unknown constraints need review.")
              + paragraph("An unknown company fact is not zero or evidence of stability. 'None found' means a bounded source review, not proof that no layoffs occurred. "
                          "Posted dates and checked dates are separate. Follow the original posting and confirm current status before applying.") + '</div></details>')
    replacements = {"META": meta, "SCOPE": scope, "STATS": stats_html, "FILTERS": filters,
                    "COMPANIES": company_html, "JOBS": jobs_html, "SOURCES": source_audit(data), "METHOD": method}
    template = TEMPLATE.read_text(encoding="utf-8")
    found = TOKEN_PATTERN.findall(template)
    if (set(found) != TOKENS or len(found) != len(TOKENS)
            or template.count("@@REPORT_") != len(found)):
        raise ValueError("HTML template must contain each supported report token exactly once")
    return TOKEN_PATTERN.sub(lambda match: replacements[match.group(1)], template)
