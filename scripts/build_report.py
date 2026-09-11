#!/usr/bin/env python3
"""Validate researcher-supplied evidence and render offline job-search reports.

Only the Python standard library is required. This script neither reads resumes
nor visits job URLs. The agent/researcher supplies sourced requirement assessments.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import re
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote, urlsplit


WEIGHTS = {"required_skills": 35, "responsibilities": 25, "seniority": 20,
           "preferred": 10, "domain": 10}
CREDIT = {"met": 1.0, "partial": 0.5, "absent": 0.0, "unknown": 0.0}
LABELS = {"required_skills": "Required skills", "responsibilities": "Responsibilities",
          "seniority": "Seniority", "preferred": "Preferred", "domain": "Domain"}


class ValidationError(ValueError):
    """Input does not meet the report schema."""


def fail(path, message):
    raise ValidationError(f"{path}: {message}")


def fields(value, required, optional, path):
    if not isinstance(value, dict):
        fail(path, "expected an object")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing:
        fail(path, "missing fields: " + ", ".join(sorted(missing)))
    if extra:
        fail(path, "unknown fields: " + ", ".join(sorted(extra)))


def string(value, path, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()):
        fail(path, "expected " + ("a string" if empty else "a nonempty string"))
    if len(value) > 20000:
        fail(path, "text exceeds 20,000 characters")
    if any(ord(c) < 32 and c not in "\n\r\t" for c in value):
        fail(path, "unsupported control character")


def enum(value, choices, path):
    if not isinstance(value, str) or value not in choices:
        fail(path, "expected one of: " + ", ".join(choices))


def calendar_date(value, path, nullable=False):
    if value is None and nullable:
        return
    string(value, path)
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError
        date.fromisoformat(value)
    except ValueError:
        fail(path, "expected a valid YYYY-MM-DD date")


def web_url(value, path):
    string(value, path)
    if any(c.isspace() or ord(c) < 32 or c == "\\" for c in value):
        fail(path, "URL must not contain whitespace, controls, or backslashes")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        parsed.port  # Validate invalid ports even though no connection is made.
        if (parsed.scheme not in ("http", "https") or not hostname
                or parsed.username is not None or parsed.password is not None
                or any(c in hostname for c in '<>"{}|^`')
                or '%' in hostname):
            raise ValueError
    except ValueError:
        fail(path, "expected an absolute HTTP(S) URL without credentials")


def validate(data):
    if not isinstance(data, dict):
        fail("input", "expected an object")
    version = data.get("schema_version")
    if type(version) is not int or version not in (1, 2):
        fail("schema_version", "must be integer 1 or 2")
    fields(data, ("schema_version", "resume_provided", "jobs") + (("companies",) if version == 2 else ()),
           ("search_summary", "search_sources") + (("company_target",) if version == 2 else ()), "input")
    companies = validate_companies(data) if version == 2 else {}
    if type(data["resume_provided"]) is not bool:
        fail("resume_provided", "must be a boolean")
    if "search_summary" in data:
        string(data["search_summary"], "search_summary", empty=True)
    sources = data.get("search_sources", [])
    if not isinstance(sources, list) or len(sources) > 1000:
        fail("search_sources", "expected an array with at most 1,000 source checks")
    for index, source in enumerate(sources):
        path = f"search_sources[{index}]"
        fields(source, ("source", "url", "method", "query", "status", "checked_at",
                        "results_seen", "verified_open", "notes"), (), path)
        for key in ("source", "query"):
            string(source[key], f"{path}.{key}")
        string(source["notes"], path + ".notes", empty=source["status"] == "searched")
        web_url(source["url"], path + ".url")
        calendar_date(source["checked_at"], path + ".checked_at")
        enum(source["method"], ("platform_search", "web_search", "employer_site", "public_api"), path + ".method")
        enum(source["status"], ("searched", "limited", "blocked", "skipped"), path + ".status")
        for key in ("results_seen", "verified_open"):
            value = source[key]
            if key == "results_seen" and value is None:
                continue
            if type(value) is not int or value < 0:
                fail(f"{path}.{key}", "expected a nonnegative integer" + (" or null" if key == "results_seen" else ""))
        if source["results_seen"] is not None and source["verified_open"] > source["results_seen"]:
            fail(path + ".verified_open", "cannot exceed results_seen")
        if source["status"] in ("blocked", "skipped"):
            if source["results_seen"] is not None or source["verified_open"] != 0:
                fail(path, "blocked/skipped checks require results_seen null and verified_open 0")
        elif source["results_seen"] is None:
            fail(path + ".results_seen", "searched/limited checks require the count actually observed")
    if not isinstance(data["jobs"], list) or len(data["jobs"]) > 1000:
        fail("jobs", "expected an array with at most 1,000 jobs")
    seen = set()
    required = ("id", "title", "company", "url", "location", "salary", "posted_at",
                "checked_at", "posting_status", "job_description_complete", "requirements", "hard_constraints")
    if version == 2:
        required += ("company_id",)
    for index, job in enumerate(data["jobs"]):
        path = f"jobs[{index}]"
        fields(job, required, ("notes", "not_applicable_categories", "discovered_via"), path)
        for key in ("id", "title", "company", "location"):
            string(job[key], f"{path}.{key}")
        if version == 2:
            string(job["company_id"], path + ".company_id")
            if job["company_id"] not in companies:
                fail(path + ".company_id", "does not reference a supplied company")
            if job["company"] != companies[job["company_id"]]["name"]:
                fail(path + ".company", "must match the referenced company name exactly")
        if job["id"] in seen:
            fail(path + ".id", "duplicate job identifier")
        seen.add(job["id"])
        web_url(job["url"], path + ".url")
        discovered = job.get("discovered_via", [])
        if not isinstance(discovered, list) or len(discovered) > 100:
            fail(path + ".discovered_via", "expected an array with at most 100 discovery sources")
        for source_index, source in enumerate(discovered):
            source_path = f"{path}.discovered_via[{source_index}]"
            fields(source, ("source", "url"), (), source_path)
            string(source["source"], source_path + ".source")
            web_url(source["url"], source_path + ".url")
        if job["salary"] is not None:
            string(job["salary"], path + ".salary")
        calendar_date(job["posted_at"], path + ".posted_at", nullable=True)
        calendar_date(job["checked_at"], path + ".checked_at")
        enum(job["posting_status"], ("open", "closed", "unverified"), path + ".posting_status")
        if type(job["job_description_complete"]) is not bool:
            fail(path + ".job_description_complete", "must be a boolean")
        if "notes" in job:
            string(job["notes"], path + ".notes", empty=True)
        for array_name, label, choices in (("requirements", "requirement", CREDIT),
                                            ("hard_constraints", "constraint", ("met", "unmet", "unknown"))):
            rows = job[array_name]
            if not isinstance(rows, list) or len(rows) > 1000:
                fail(path + "." + array_name, "expected an array with at most 1,000 items")
            for row_index, row in enumerate(rows):
                row_path = f"{path}.{array_name}[{row_index}]"
                row_required = (label, "status", "evidence") + (("category",) if label == "requirement" else ())
                fields(row, row_required, (), row_path)
                string(row[label], row_path + "." + label)
                enum(row["status"], choices, row_path + ".status")
                string(row["evidence"], row_path + ".evidence", empty=row["status"] == "unknown")
                if label == "requirement":
                    enum(row["category"], WEIGHTS, row_path + ".category")
        excluded = job.get("not_applicable_categories", {})
        if not isinstance(excluded, dict):
            fail(path + ".not_applicable_categories", "expected category-to-reason object")
        for category, reason in excluded.items():
            enum(category, WEIGHTS, path + ".not_applicable_categories")
            string(reason, path + ".not_applicable_categories." + category)
            if not job["job_description_complete"]:
                fail(path + ".not_applicable_categories", "exclusions require a complete job description")
            if any(row["category"] == category for row in job["requirements"]):
                fail(path + ".not_applicable_categories", "excluded category cannot also have requirements")
    return data


def validate_company_sources(value, path, required=False):
    if not isinstance(value, list) or len(value) > 100:
        fail(path, "expected an array with at most 100 sources")
    if required and not value:
        fail(path, "known claims and none_found checks require supporting sources")
    for index, source in enumerate(value):
        item_path = f"{path}[{index}]"
        fields(source, ("label", "url"), (), item_path)
        string(source["label"], item_path + ".label")
        web_url(source["url"], item_path + ".url")


def validate_period(value, start_key, end_key, path, checked_at, required=False):
    start, end = value[start_key], value[end_key]
    for key in (start_key, end_key):
        calendar_date(value[key], path + "." + key, nullable=True)
    if (start is None) != (end is None) or (required and start is None):
        fail(path, "period requires both start and end dates")
    if start is not None and (start > end or end > checked_at):
        fail(path, "period must be ordered and end no later than checked_at")


def validate_companies(data):
    target = data.get("company_target", 20)
    if type(target) is not int or not 1 <= target <= 100:
        fail("company_target", "expected an integer from 1 through 100")
    if not isinstance(data["companies"], list) or len(data["companies"]) > 1000:
        fail("companies", "expected an array with at most 1,000 companies")
    companies = {}
    for index, company in enumerate(data["companies"]):
        path = f"companies[{index}]"
        fields(company, ("id", "name", "url", "checked_at", "size", "headcount_trend", "latest_layoff"), (), path)
        for key in ("id", "name"):
            string(company[key], path + "." + key)
        if company["id"] in companies:
            fail(path + ".id", "duplicate company identifier")
        companies[company["id"]] = company
        if company["url"] is not None:
            web_url(company["url"], path + ".url")
        calendar_date(company["checked_at"], path + ".checked_at")

        size, size_path = company["size"], path + ".size"
        fields(size, ("value", "as_of", "scope", "basis", "sources"), (), size_path)
        string(size["scope"], size_path + ".scope")
        enum(size["basis"], ("reported", "estimate", "range", "unknown"), size_path + ".basis")
        calendar_date(size["as_of"], size_path + ".as_of", nullable=True)
        if size["basis"] == "unknown":
            if size["value"] is not None or size["as_of"] is not None:
                fail(size_path, "unknown size requires null value and as_of")
        else:
            string(size["value"], size_path + ".value")
        if size["as_of"] is not None and size["as_of"] > company["checked_at"]:
            fail(size_path + ".as_of", "cannot be later than checked_at")
        validate_company_sources(size["sources"], size_path + ".sources", size["basis"] != "unknown")

        trend, trend_path = company["headcount_trend"], path + ".headcount_trend"
        fields(trend, ("direction", "period_start", "period_end", "summary", "sources"), (), trend_path)
        enum(trend["direction"], ("growing", "stable", "declining", "mixed", "unknown"), trend_path + ".direction")
        string(trend["summary"], trend_path + ".summary")
        validate_period(trend, "period_start", "period_end", trend_path, company["checked_at"],
                        required=trend["direction"] != "unknown")
        validate_company_sources(trend["sources"], trend_path + ".sources", trend["direction"] != "unknown")

        layoff, layoff_path = company["latest_layoff"], path + ".latest_layoff"
        fields(layoff, ("status", "event_date", "date_type", "summary", "sources", "searched_from", "searched_through"), (), layoff_path)
        enum(layoff["status"], ("reported", "none_found", "unknown"), layoff_path + ".status")
        enum(layoff["date_type"], ("announcement", "effective", "unspecified"), layoff_path + ".date_type")
        string(layoff["summary"], layoff_path + ".summary")
        calendar_date(layoff["event_date"], layoff_path + ".event_date", nullable=True)
        validate_period(layoff, "searched_from", "searched_through", layoff_path, company["checked_at"],
                        required=layoff["status"] == "none_found")
        if layoff["status"] != "reported":
            if layoff["event_date"] is not None or layoff["date_type"] != "unspecified":
                fail(layoff_path, "unreported layoff requires null event_date and unspecified date_type")
        elif layoff["event_date"] is None and layoff["date_type"] != "unspecified":
            fail(layoff_path, "a specified date type requires event_date")
        elif layoff["event_date"] is not None and layoff["date_type"] == "unspecified":
            fail(layoff_path, "an exact event_date requires announcement or effective date_type")
        if (layoff["date_type"] == "announcement" and layoff["event_date"] is not None
                and layoff["event_date"] > company["checked_at"]):
            fail(layoff_path + ".event_date", "announcement cannot be later than checked_at")
        validate_company_sources(layoff["sources"], layoff_path + ".sources", layoff["status"] != "unknown")
    return companies


def assess(job, resume_provided):
    """Return score, weighted evidence coverage, and deterministic priority labels."""
    excluded = job.get("not_applicable_categories", {})
    denominator = sum(weight for category, weight in WEIGHTS.items() if category not in excluded)
    points = known = 0.0
    categories = []
    for category, weight in WEIGHTS.items():
        rows = [row for row in job["requirements"] if row["category"] == category]
        credit = sum(CREDIT[row["status"]] for row in rows) / len(rows) if rows and resume_provided else 0.0
        coverage = sum(row["status"] != "unknown" for row in rows) / len(rows) if rows and resume_provided else 0.0
        if category not in excluded:
            points += weight * credit
            known += weight * coverage
        categories.append({"category": category, "weight": weight, "count": len(rows),
                           "credit": credit, "coverage": coverage, "excluded": category in excluded})
    coverage = 100.0 * known / denominator if denominator else 0.0
    if not resume_provided:
        state, score, confidence = "not assessed", None, "Not assessed"
    elif not job["requirements"] or denominator == 0 or known == 0:
        state, score, confidence = "insufficient evidence", None, "Low"
    else:
        score = 100.0 * points / denominator
        state = "provisional" if not job["job_description_complete"] or coverage < 80 else "assessed"
        confidence = "High" if job["job_description_complete"] and coverage >= 90 else (
            "Medium" if job["job_description_complete"] and coverage >= 60 else "Low")
    constraints = job["hard_constraints"]
    eligibility = "Unmet" if any(row["status"] == "unmet" for row in constraints) else (
        "Unknown" if not constraints or any(row["status"] == "unknown" for row in constraints) else "Met")
    if job["posting_status"] == "closed":
        priority, action = "Inactive", "Do not apply to this closed posting; find an active equivalent."
    elif eligibility == "Unmet":
        priority, action = "Blocked", "Resolve the explicit hard blocker or find an eligible equivalent."
    elif job["posting_status"] == "unverified":
        priority, action = "Lead only", "Verify the employer posting, open status, and full job description."
    elif not resume_provided:
        priority, action = "Not scored", "Add a resume or clearly sourced professional profile to assess fit."
    elif state != "assessed":
        priority, action = "Review evidence", "Read the full job description and clarify missing profile evidence."
    elif eligibility == "Unknown":
        priority, action = "Clarify eligibility", "Confirm unknown or unassessed hard constraints before prioritizing."
    elif score >= 80:
        priority, action = "High", "Tailor truthful accomplishments to the strongest relevant requirements."
    elif score >= 60:
        priority, action = "Medium", "Address material partial matches with specific, truthful examples."
    elif score >= 40:
        priority, action = "Explore", "Review the major gaps and consider an adjacent role."
    else:
        priority, action = "Low", "Prioritize roles closer to the documented experience."
    strengths = [row["requirement"] for row in job["requirements"] if row["status"] == "met"] if resume_provided else []
    gaps = [f"{row['status'].capitalize()}: {row['requirement']}" for row in job["requirements"]
            if row["status"] in ("partial", "absent")] if resume_provided else []
    unknowns = [row["requirement"] for row in job["requirements"] if row["status"] == "unknown"] if resume_provided else []
    constraint_issues = [f"Eligibility {row['status']}: {row['constraint']}" for row in constraints
                         if row["status"] != "met"]
    if not constraints:
        constraint_issues.append("Eligibility not assessed")
    return {"score": round(score, 1) if score is not None else None, "coverage": round(coverage, 1),
            "confidence": confidence, "assessment": state, "eligibility": eligibility,
            "priority": priority, "next_action": action, "strengths": strengths, "gaps": gaps,
            "unknowns": unknowns, "constraint_issues": constraint_issues,
            "categories": categories, "denominator": denominator}


def md(value):
    """Escape untrusted content for Markdown text and table cells."""
    text = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"([\\`*_{}\[\]()#+.!|~\-])", r"\\\1", text)
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>").replace("\t", " ")


def markdown_url(url):
    return quote(url, safe="/:?=&%#@+;,!$'*[]~.-_")


def csv_safe(value):
    text = "" if value is None else str(value)
    if text.startswith(("\t", "\r", "\n")) or text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def score_text(result):
    if result["score"] is None:
        return "N/A — " + result["assessment"]
    return f"{result['score']:.1f}/100" + (" (provisional)" if result["assessment"] == "provisional" else "")


def job_group(job, result):
    if job["posting_status"] == "open" and result["eligibility"] == "Unmet":
        return "blocked"
    return job["posting_status"]


def ordered_jobs(data):
    """Rank active jobs by actionability, then evidence fit; isolate nonactive rows.

    Active priority order is High, Medium, Explore, Low, Clarify eligibility,
    Review evidence, Not scored. Ties use descending score, descending coverage,
    then job ID so a shuffled input produces the same report ordering.
    """
    groups = {"open": 0, "blocked": 1, "unverified": 2, "closed": 3}
    priorities = {name: index for index, name in enumerate((
        "High", "Medium", "Explore", "Low", "Clarify eligibility", "Review evidence", "Not scored"))}

    def key(job):
        result = assess(job, data["resume_provided"])
        score = result["score"] if result["score"] is not None else -1
        return (groups[job_group(job, result)], priorities.get(result["priority"], 99),
                -score, -result["coverage"], job["id"])

    return sorted(data["jobs"], key=key)


def company_assessments(data):
    """Aggregate existing fit scores; company business metadata never affects fit.

    Recommendations follow the existing actionable-job ordering, capped at three.
    Only complete, recorded-open postings without a confirmed blocker qualify.
    Coverage is the mean coverage of scored components, not company-research coverage.
    """
    grouped = {company["id"]: [] for company in data["companies"]}
    for job in ordered_jobs(data):
        grouped[job["company_id"]].append(job)
    results = {}
    for company in data["companies"]:
        jobs = grouped[company["id"]]
        eligible = [job for job in jobs if job["posting_status"] == "open"
                    and job["job_description_complete"]
                    and assess(job, data["resume_provided"])["eligibility"] != "Unmet"]
        recommendations = eligible[:3]
        assessed = [(job, assess(job, data["resume_provided"])) for job in recommendations]
        scored = [(job, result) for job, result in assessed if result["score"] is not None]
        score = round(sum(result["score"] for _, result in scored) / len(scored), 1) if scored else None
        coverage = round(sum(result["coverage"] for _, result in scored) / len(scored), 1) if scored else None
        provisional = (len(scored) < 3 or len(scored) < len(assessed)
                       or any(result["assessment"] == "provisional" or result["eligibility"] == "Unknown"
                              for _, result in assessed))
        results[company["id"]] = {
            "score": score, "coverage": coverage,
            "assessment": "not assessed" if score is None else ("provisional" if provisional else "assessed"),
            "component_job_ids": [job["id"] for job, _ in scored], "scored_count": len(scored),
            "recommended_job_ids": [job["id"] for job in recommendations],
            "recommendations": recommendations, "eligible_job_count": len(eligible),
            "open_job_count": sum(job["posting_status"] == "open" for job in jobs), "jobs": jobs,
        }
    return results


def ordered_companies(data, results=None):
    results = results if results is not None else company_assessments(data)

    def key(company):
        result = results[company["id"]]
        return (not result["recommendations"], result["score"] is None,
                -(result["score"] if result["score"] is not None else -1),
                result["assessment"] == "provisional",
                -(result["coverage"] if result["coverage"] is not None else -1),
                company["name"].casefold(), company["id"])

    return sorted(data["companies"], key=key)


def company_link(company):
    name = md(company["name"])
    return f"[{name}](<{markdown_url(company['url'])}>)" if company["url"] else name + " (website unknown)"


def claim_sources(sources):
    return "; ".join(f"[{md(source['label'])}](<{markdown_url(source['url'])}>)" for source in sources)


def sourced_cell(text, sources):
    return md(text) + ("<br>" + claim_sources(sources) if sources else "")


def company_fact_texts(company):
    """Plain text facts shared by Markdown and spreadsheet exports."""
    size, trend, layoff = company["size"], company["headcount_trend"], company["latest_layoff"]
    size_text = "Unknown" if size["basis"] == "unknown" else f"{size['value']} ({size['basis']})"
    size_text += f"; scope: {size['scope']}; as of: {size['as_of'] or 'unknown'}"
    trend_text = trend["direction"].capitalize()
    if trend["period_start"]:
        trend_text += f" ({trend['period_start']} to {trend['period_end']})"
    trend_text += "; " + trend["summary"]
    if layoff["status"] == "reported":
        date_type = layoff["date_type"]
        if date_type == "effective" and layoff["event_date"] > company["checked_at"]:
            date_type = "scheduled effective"
        layoff_text = f"Latest reported: {layoff['event_date'] or 'date unknown'} ({date_type})"
    elif layoff["status"] == "none_found":
        layoff_text = (f"None found in checked sources, {layoff['searched_from']} to {layoff['searched_through']}; "
                       "not proof that no layoffs occurred")
    else:
        layoff_text = "Unknown"
    layoff_text += "; " + layoff["summary"]
    if layoff["status"] in ("reported", "unknown") and layoff["searched_from"]:
        layoff_text += f"; searched {layoff['searched_from']} to {layoff['searched_through']}"
    return size_text, trend_text, layoff_text


def company_score_text(result):
    if result["score"] is None:
        return "N/A — no scored eligible recommendations"
    suffix = " (provisional)" if result["assessment"] == "provisional" else ""
    return f"{result['score']:.1f}/100{suffix}"


def render_company_markdown(data):
    results = company_assessments(data)
    companies = ordered_companies(data, results)
    open_companies = sum(result["open_job_count"] > 0 for result in results.values())
    recommendable = sum(bool(result["recommendations"]) for result in results.values())
    target = data.get("company_target", 20)
    lines = ["# Job search report", ""]
    if data.get("search_summary"):
        lines.extend([md(data["search_summary"]), ""])
    lines.extend(["## Company overview", "",
             f"Company target: {target}. Companies researched: {len(companies)}. "
             f"Distinct companies with researcher-verified open postings: {open_companies}. "
             f"Companies with recommendable postings: {recommendable}. "
             f"Shortfall from the recommendable-company target: {max(0, target - recommendable)}. "
             "A company with only blocked, incomplete or unverified jobs does not count toward that target; "
             "repeated jobs do not add companies.", "",
             "Company match is the mean documented fit of the scored jobs among each company's top three recommendations. "
             "It is not an employer-quality rating, ATS score, or hiring probability. Company size, headcount trend and layoffs do not affect it. "
             "Coverage is the mean evidence coverage of scored component jobs. Fewer than three scored jobs, provisional job evidence, "
             "unknown eligibility or an unscored recommendation makes the company rating provisional. "
             "An unknown fact is not zero or evidence of stability.", "",
             "Posting status, company facts and dates were supplied by the researcher. This offline helper does not verify links or read resumes.", "",
             "| Company | Company match / evidence | Company size | Recent headcount trend | Latest reported layoff | Top recommended jobs (up to 3) | Checked |",
             "| --- | --- | --- | --- | --- | --- | --- |"])
    for company in companies:
        result = results[company["id"]]
        facts = company_fact_texts(company)
        rating = md(company_score_text(result)) + f"<br>Scored: {result['scored_count']}/{len(result['recommendations'])} recommended"
        rating += "<br>Evidence coverage: " + (f"{result['coverage']:.1f}%" if result["coverage"] is not None else "N/A")
        rating += "<br>Components: " + md(", ".join(result["component_job_ids"]) or "None")
        recommended_links = []
        for index, job in enumerate(result["recommendations"], 1):
            job_result = assess(job, data["resume_provided"])
            caution = md(f"{job_result['priority']}; eligibility {job_result['eligibility']}")
            recommended_links.append(f"{index}. [{md(job['title'])}](<{markdown_url(job['url'])}>) — {caution}")
        recommendations = "<br>".join(recommended_links) or "No eligible verified recommendations"
        cells = [company_link(company), rating,
                 sourced_cell(facts[0], company["size"]["sources"]),
                 sourced_cell(facts[1], company["headcount_trend"]["sources"]),
                 sourced_cell(facts[2], company["latest_layoff"]["sources"]),
                 recommendations, md(company["checked_at"])]
        lines.append("| " + " | ".join(cells) + " |")
    if not companies:
        lines.append("| No companies supplied | N/A | Unknown | Unknown | Unknown | None | — |")
    lines.append("")
    lines.extend(["## All jobs by company", ""])
    groups = (("Open postings", "open"), ("Blocked postings", "blocked"),
              ("Unverified discovery leads", "unverified"), ("Inactive postings", "closed"))
    grouped_jobs = []
    for company in companies:
        jobs = results[company["id"]]["jobs"]
        grouped_jobs.extend(jobs)
        lines.extend(["### " + company_link(company), ""])
        if not jobs:
            lines.extend(["No job records supplied for this company.", ""])
        for label, status in groups:
            selected = [job for job in jobs if job_group(job, assess(job, data["resume_provided"])) == status]
            if not selected:
                continue
            lines.extend(["#### " + label, "",
                          "| Role | Location / pay | Fit / coverage | Eligibility | Priority | Strengths | Gaps / unknowns | Next action |",
                          "| --- | --- | --- | --- | --- | --- | --- | --- |"])
            for job in selected:
                result = assess(job, data["resume_provided"])
                gaps = result["constraint_issues"] + result["gaps"] + ["Unknown: " + item for item in result["unknowns"]]
                cells = [f"[{md(job['title'])}](<{markdown_url(job['url'])}>)",
                         md(job["location"]) + "<br>" + md(job["salary"] or "Pay unknown"),
                         md(score_text(result)) + "<br>" + md(f"{result['confidence']} / {result['coverage']:.1f}%"),
                         md(result["eligibility"]), md(result["priority"]),
                         md("; ".join(result["strengths"][:3]) or "Not established"),
                         md("; ".join(gaps[:4]) or "None documented"), md(result["next_action"])]
                lines.append("| " + " | ".join(cells) + " |")
            lines.append("")
    if not data["jobs"]:
        lines.extend(["No jobs were supplied. No fit scores or recommendations were generated.", ""])
    lines.extend(source_lines(data))
    lines.extend(evidence_lines(data, grouped_jobs))
    return "\n".join(lines)


def render_markdown(data):
    if data["schema_version"] == 2:
        return render_company_markdown(data)
    sorted_jobs = ordered_jobs(data)
    lines = ["# Job search report", "",
             "Fit measures documented alignment, not an ATS score or a probability of interview, offer, or hiring. "
             "Confidence measures evidence completeness. Unknown evidence receives no fit credit and is distinct from an explicit mismatch.", "",
             "Posting status and dates were supplied by the researcher. This offline helper does not verify links or read resumes.", ""]
    if data.get("search_summary"):
        lines.extend([md(data["search_summary"]), ""])
    lines.extend(source_lines(data))
    groups = (("Open postings", "open"), ("Blocked postings", "blocked"),
              ("Unverified discovery leads", "unverified"), ("Inactive postings", "closed"))
    if not data["jobs"]:
        lines.extend(["No jobs were supplied. No fit scores or recommendations were generated.", ""])
    for label, status in groups:
        jobs = [job for job in sorted_jobs if job_group(job, assess(job, data["resume_provided"])) == status]
        if not jobs:
            continue
        lines.extend(["## " + label, "", "| Role / company | Fit | Confidence / coverage | Eligibility | Priority | Strengths | Gaps / unknowns | Next action |",
                      "| --- | --- | --- | --- | --- | --- | --- | --- |"])
        for job in jobs:
            result = assess(job, data["resume_provided"])
            link = f"[{md(job['title'])}](<{markdown_url(job['url'])}>)<br>{md(job['company'])}"
            if job.get("discovered_via"):
                link += "<br>Found via: " + md(", ".join(dict.fromkeys(source["source"] for source in job["discovered_via"])))
            gaps = result["constraint_issues"] + result["gaps"] + ["Unknown: " + item for item in result["unknowns"]]
            cells = [link, md(score_text(result)),
                     md(f"{result['confidence']} / {result['coverage']:.1f}%"), md(result["eligibility"]), md(result["priority"]),
                     md("; ".join(result["strengths"][:3]) or "Not established"), md("; ".join(gaps[:4]) or "None documented"), md(result["next_action"])]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    lines.extend(evidence_lines(data, sorted_jobs))
    return "\n".join(lines)


def source_lines(data):
    lines = []
    if data.get("search_sources"):
        open_count = sum(job["posting_status"] == "open" for job in data["jobs"])
        lines.extend(["## Sources checked", "",
                      f"Unique job records in this report: {len(data['jobs'])}; recorded open: {open_count} (including any eligibility blockers). "
                      "Source counts describe results actually inspected, not all vacancies on a platform. "
                      "The same job may appear in several source checks; do not sum these counts as unique jobs. "
                      "Blocked or skipped sources have unknown availability, not zero vacancies.", "",
                      "| Source / method | Query or API request | Status | Checked | Results seen | Verified open | Notes |",
                      "| --- | --- | --- | --- | ---: | ---: | --- |"])
        for source in data["search_sources"]:
            link = f"[{md(source['source'])}](<{markdown_url(source['url'])}>)<br>{md(source['method'])}"
            cells = [link] + [md(value) for value in (source["query"], source["status"], source["checked_at"],
                     source["results_seen"] if source["results_seen"] is not None else "Unknown", source["verified_open"], source["notes"])]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    return lines


def evidence_lines(data, sorted_jobs):
    lines = []
    lines.extend(["## Evidence and calculation details", "",
                  "Weights: required skills 35, responsibilities 25, seniority 20, preferred 10, domain 10. "
                  "Within each category, criteria have equal weight: met 1, partial 0.5, absent 0, unknown 0. "
                  "Missing undeclared categories retain their weight and receive zero credit and coverage. "
                  "Only explicitly justified categories excluded from a complete JD leave the denominator. "
                  "Fit = 100 × weighted credit / applicable weight; coverage uses the fraction of criteria with known evidence. "
                  "An empty or entirely unknown requirement set yields N/A.", "",
                  "High confidence requires a complete JD and at least 90% coverage; medium requires a complete JD and at least 60%; "
                  "otherwise confidence is low. A score is provisional for an incomplete JD or coverage below 80%. "
                  "High / medium / explore / low priority use 80 / 60 / 40 score thresholds only for assessed, open postings with met hard constraints. "
                  "Closed postings are inactive; blockers override fit; unverified postings remain leads; missing evidence or unknown constraints require review.", ""])
    for job in sorted_jobs:
        result = assess(job, data["resume_provided"])
        lines.extend([f"### {md(job['id'])}: {md(job['title'])} — {md(job['company'])}", "",
                      f"[Direct posting](<{markdown_url(job['url'])}>) · {md(job['posting_status'])} · {md(score_text(result))}", ""])
        lines.extend(["| Location | Salary | Posted | Checked | Status |", "| --- | --- | --- | --- | --- |",
                      "| " + " | ".join(md(value) for value in (job["location"], job["salary"] or "Not posted / unknown",
                                                               job["posted_at"] or "Unknown", job["checked_at"], job["posting_status"])) + " |", ""])
        if job.get("notes"):
            lines.extend(["Researcher notes: " + md(job["notes"]), ""])
        if job.get("discovered_via"):
            lines.extend(["| Discovery source | Observed link |", "| --- | --- |"])
            for source in job["discovered_via"]:
                lines.append(f"| {md(source['source'])} | [Discovery link](<{markdown_url(source['url'])}>) |")
            lines.append("")
        if not data["resume_provided"]:
            lines.extend(["No resume/profile supplied: personal-fit evidence is not assessed.", ""])
        lines.extend(["| Category | JD requirement | Assessment | JD / résumé evidence |", "| --- | --- | --- | --- |"])
        for row in job["requirements"]:
            status = row["status"] if data["resume_provided"] else "not assessed"
            evidence = row["evidence"] if data["resume_provided"] else "No resume/profile supplied"
            lines.append("| " + " | ".join(md(v) for v in (LABELS[row["category"]], row["requirement"], status, evidence or "No evidence supplied")) + " |")
        if not job["requirements"]:
            lines.append("| — | No requirements supplied | Insufficient evidence | — |")
        lines.extend(["", "| Category | Weight | Criteria | Credit | Known evidence |", "| --- | ---: | ---: | ---: | ---: |"])
        for row in result["categories"]:
            if row["excluded"]:
                lines.append(f"| {LABELS[row['category']]} | Excluded | 0 | N/A | N/A |")
            else:
                credit = f"{row['credit'] * 100:.1f}%" if data["resume_provided"] else "N/A"
                coverage = f"{row['coverage'] * 100:.1f}%" if data["resume_provided"] else "N/A"
                lines.append(f"| {LABELS[row['category']]} | {row['weight']} | {row['count']} | {credit} | {coverage} |")
        lines.extend(["", f"Applicable weight denominator: {result['denominator']}.", ""])
        for category, reason in job.get("not_applicable_categories", {}).items():
            lines.extend([f"Excluded {LABELS[category]}: {md(reason)}", ""])
        lines.extend(["| Hard constraint | Status | Evidence |", "| --- | --- | --- |"])
        for row in job["hard_constraints"]:
            lines.append("| " + " | ".join(md(row[key]) for key in ("constraint", "status", "evidence")) + " |")
        if not job["hard_constraints"]:
            lines.append("| No constraints supplied | Unknown | Eligibility has not been established |")
        lines.extend(["", "Next action: " + md(result["next_action"]), ""])
    return lines


COMPANY_CSV_COLUMNS = (
    "company_id", "company_name", "company_url", "company_checked_at", "company_fit_score",
    "company_assessment", "company_component_job_ids", "company_scored_count",
    "company_recommended_count", "company_evidence_coverage_percent", "company_open_job_count",
    "company_recommended_job_ids", "company_recommended_job_urls", "company_size", "company_size_basis",
    "company_size_as_of", "company_size_scope", "company_size_sources", "company_headcount_direction",
    "company_headcount_period_start", "company_headcount_period_end", "company_headcount_summary",
    "company_headcount_sources", "company_layoff_status", "company_layoff_event_date",
    "company_layoff_date_type", "company_layoff_summary", "company_layoff_searched_from",
    "company_layoff_searched_through", "company_layoff_sources",
)


def company_csv_values(company, result):
    size, trend, layoff = company["size"], company["headcount_trend"], company["latest_layoff"]

    def sources_text(sources):
        return "; ".join(source["label"] + ": " + source["url"] for source in sources)

    return [company["id"], company["name"], company["url"], company["checked_at"],
            result["score"] if result["score"] is not None else "N/A", result["assessment"],
            "; ".join(result["component_job_ids"]), result["scored_count"], len(result["recommendations"]),
            result["coverage"] if result["coverage"] is not None else "N/A", result["open_job_count"],
            "; ".join(result["recommended_job_ids"]), "; ".join(job["url"] for job in result["recommendations"]),
            size["value"], size["basis"], size["as_of"], size["scope"], sources_text(size["sources"]),
            trend["direction"], trend["period_start"], trend["period_end"], trend["summary"], sources_text(trend["sources"]),
            layoff["status"], layoff["event_date"], layoff["date_type"], layoff["summary"],
            layoff["searched_from"], layoff["searched_through"], sources_text(layoff["sources"])]


def render_companies_csv(data):
    if data["schema_version"] != 2:
        fail("companies-csv", "company summary export requires schema version 2")
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(COMPANY_CSV_COLUMNS)
    results = company_assessments(data)
    for company in ordered_companies(data, results):
        writer.writerow([csv_safe(value) for value in company_csv_values(company, results[company["id"]])])
    return output.getvalue()


def render_csv(data):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    columns = ("id", "title", "company", "url", "location", "salary", "posted_at", "checked_at", "posting_status",
                     "fit_score", "assessment", "confidence", "evidence_coverage_percent", "eligibility", "application_priority",
                     "strengths", "gaps", "unknowns", "eligibility_details", "next_action", "notes",
                     "discovery_sources", "discovery_urls")
    company_results = company_assessments(data) if data["schema_version"] == 2 else {}
    companies = {company["id"]: company for company in data.get("companies", [])}
    jobs = ordered_jobs(data)
    if data["schema_version"] == 2:
        columns += COMPANY_CSV_COLUMNS
        jobs = [job for company in ordered_companies(data, company_results)
                for job in company_results[company["id"]]["jobs"]]
    writer.writerow(columns)
    for job in jobs:
        result = assess(job, data["resume_provided"])
        values = [job[key] for key in ("id", "title", "company", "url", "location", "salary", "posted_at", "checked_at", "posting_status")]
        values += [result["score"] if result["score"] is not None else "N/A", result["assessment"], result["confidence"],
                   result["coverage"], result["eligibility"], result["priority"], "; ".join(result["strengths"]),
                   "; ".join(result["gaps"]), "; ".join(result["unknowns"]), "; ".join(result["constraint_issues"]),
                   result["next_action"], job.get("notes", ""),
                   "; ".join(source["source"] for source in job.get("discovered_via", [])),
                   "; ".join(source["url"] for source in job.get("discovered_via", []))]
        if data["schema_version"] == 2:
            values += company_csv_values(companies[job["company_id"]], company_results[job["company_id"]])
        writer.writerow([csv_safe(value) for value in values])
    return output.getvalue()


def render_html(data):
    """Render a portable HTML report with the same validated evidence and scores."""
    validate(data)
    spec = importlib.util.spec_from_file_location(
        "job_search_report_html", Path(__file__).with_name("render_html.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report_api = SimpleNamespace(
        assess=assess, ordered_jobs=ordered_jobs, company_assessments=company_assessments,
        ordered_companies=ordered_companies, job_group=job_group,
        company_fact_texts=company_fact_texts, LABELS=LABELS, WEIGHTS=WEIGHTS)
    return module.render_html(data, report_api)


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail("JSON", "duplicate object key: " + key)
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Evidence JSON input (schema version 1 or 2)")
    parser.add_argument("--output", "--markdown", required=True, dest="output", type=Path, help="Markdown report path")
    parser.add_argument("--csv", type=Path, help="Optional spreadsheet-safe CSV summary path")
    parser.add_argument("--companies-csv", type=Path, help="Optional company summary CSV path (schema version 2)")
    parser.add_argument("--html", type=Path, help="Optional self-contained HTML report path")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing existing report files")
    args = parser.parse_args(argv)
    try:
        data = validate(json.loads(args.input.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates,
                                   parse_constant=lambda value: fail("JSON", "non-finite number " + value)))
        destinations = [path for path in (args.output, args.csv, args.companies_csv, args.html) if path is not None]
        paths = [args.input] + destinations
        for index, path in enumerate(paths):
            for other in paths[index + 1:]:
                if (path.resolve() == other.resolve()
                        or (path.exists() and other.exists() and path.samefile(other))):
                    fail("output", "input and output paths must be distinct, including file aliases")
                if path.resolve() in other.resolve().parents or other.resolve() in path.resolve().parents:
                    fail("output", "a report file cannot also be another file's parent directory")
        for path in destinations:
            if (path.exists() or path.is_symlink()) and not args.overwrite:
                fail("output", f"file exists: {path}; use --overwrite to replace it")
            if path.exists() and not path.is_file():
                fail("output", f"not a regular file: {path}")
            if any(parent.exists() and not parent.is_dir() for parent in path.parents):
                fail("output", f"parent path is not a directory: {path}")
        reports = [(args.output, render_markdown(data))]
        if args.csv:
            reports.append((args.csv, render_csv(data)))
        if args.companies_csv:
            reports.append((args.companies_csv, render_companies_csv(data)))
        if args.html:
            reports.append((args.html, render_html(data)))
        for path, contents in reports:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8", newline="")
        print(f"Wrote {len(data['jobs'])} job(s) to " + ", ".join(str(path) for path in destinations))
        return 0
    except (ValueError, OSError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
