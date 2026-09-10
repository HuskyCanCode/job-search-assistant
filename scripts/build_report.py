#!/usr/bin/env python3
"""Validate researcher-supplied evidence and render offline job-search reports.

Only the Python standard library is required. This script neither reads resumes
nor visits job URLs. The agent/researcher supplies sourced requirement assessments.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from datetime import date
from pathlib import Path
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
    fields(data, ("schema_version", "resume_provided", "jobs"), ("search_summary",), "input")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        fail("schema_version", "must be integer 1")
    if type(data["resume_provided"]) is not bool:
        fail("resume_provided", "must be a boolean")
    if "search_summary" in data:
        string(data["search_summary"], "search_summary", empty=True)
    if not isinstance(data["jobs"], list) or len(data["jobs"]) > 1000:
        fail("jobs", "expected an array with at most 1,000 jobs")
    seen = set()
    required = ("id", "title", "company", "url", "location", "salary", "posted_at",
                "checked_at", "posting_status", "job_description_complete", "requirements", "hard_constraints")
    for index, job in enumerate(data["jobs"]):
        path = f"jobs[{index}]"
        fields(job, required, ("notes", "not_applicable_categories"), path)
        for key in ("id", "title", "company", "location"):
            string(job[key], f"{path}.{key}")
        if job["id"] in seen:
            fail(path + ".id", "duplicate job identifier")
        seen.add(job["id"])
        web_url(job["url"], path + ".url")
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


def render_markdown(data):
    sorted_jobs = ordered_jobs(data)
    lines = ["# Job search report", "",
             "Fit measures documented alignment, not an ATS score or a probability of interview, offer, or hiring. "
             "Confidence measures evidence completeness. Unknown evidence receives no fit credit and is distinct from an explicit mismatch.", "",
             "Posting status and dates were supplied by the researcher. This offline helper does not verify links or read resumes.", ""]
    if data.get("search_summary"):
        lines.extend([md(data["search_summary"]), ""])
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
            gaps = result["constraint_issues"] + result["gaps"] + ["Unknown: " + item for item in result["unknowns"]]
            cells = [link, md(score_text(result)),
                     md(f"{result['confidence']} / {result['coverage']:.1f}%"), md(result["eligibility"]), md(result["priority"]),
                     md("; ".join(result["strengths"][:3]) or "Not established"), md("; ".join(gaps[:4]) or "None documented"), md(result["next_action"])]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
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
    return "\n".join(lines)


def render_csv(data):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(("id", "title", "company", "url", "location", "salary", "posted_at", "checked_at", "posting_status",
                     "fit_score", "assessment", "confidence", "evidence_coverage_percent", "eligibility", "application_priority",
                     "strengths", "gaps", "unknowns", "eligibility_details", "next_action", "notes"))
    for job in ordered_jobs(data):
        result = assess(job, data["resume_provided"])
        values = [job[key] for key in ("id", "title", "company", "url", "location", "salary", "posted_at", "checked_at", "posting_status")]
        values += [result["score"] if result["score"] is not None else "N/A", result["assessment"], result["confidence"],
                   result["coverage"], result["eligibility"], result["priority"], "; ".join(result["strengths"]),
                   "; ".join(result["gaps"]), "; ".join(result["unknowns"]), "; ".join(result["constraint_issues"]),
                   result["next_action"], job.get("notes", "")]
        writer.writerow([csv_safe(value) for value in values])
    return output.getvalue()


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail("JSON", "duplicate object key: " + key)
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Evidence JSON input (schema version 1)")
    parser.add_argument("--output", "--markdown", required=True, dest="output", type=Path, help="Markdown report path")
    parser.add_argument("--csv", type=Path, help="Optional spreadsheet-safe CSV summary path")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing existing report files")
    args = parser.parse_args(argv)
    try:
        data = validate(json.loads(args.input.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates,
                                   parse_constant=lambda value: fail("JSON", "non-finite number " + value)))
        destinations = [args.output] + ([args.csv] if args.csv else [])
        paths = [args.input.resolve()] + [path.resolve() for path in destinations]
        if len(set(paths)) != len(paths):
            fail("output", "input and output paths must be distinct")
        for path in destinations:
            if path.exists() and not args.overwrite:
                fail("output", f"file exists: {path}; use --overwrite to replace it")
            if path.exists() and not path.is_file():
                fail("output", f"not a regular file: {path}")
        reports = [(args.output, render_markdown(data))]
        if args.csv:
            reports.append((args.csv, render_csv(data)))
        for path, contents in reports:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8", newline="")
        print(f"Wrote {len(data['jobs'])} job(s) to " + ", ".join(str(path) for path in destinations))
        return 0
    except (ValidationError, json.JSONDecodeError, OSError, UnicodeError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
