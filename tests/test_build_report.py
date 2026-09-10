"""Behavioral tests for conservative scoring, eligibility, validation, and exports."""

import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_report.py"
spec = importlib.util.spec_from_file_location("build_report", SCRIPT)
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def sample():
    return {"schema_version": 1, "resume_provided": True, "jobs": [{
        "id": "test-1", "title": "Analyst", "company": "Example", "url": "https://example.com/jobs/1",
        "location": "Remote, Canada", "salary": None, "posted_at": None, "checked_at": "2026-09-10",
        "posting_status": "open", "job_description_complete": True,
        "requirements": [{"category": category, "requirement": category + " criterion", "status": "met",
                          "evidence": "JD clause matches resume Experience section."} for category in report.WEIGHTS],
        "hard_constraints": [{"constraint": "Remote within Canada", "status": "met",
                              "evidence": "JD permits Canada; user explicitly resides in Canada."}]}]}


def company_record(identifier="example", name="Example", url="https://example.com"):
    return {"id": identifier, "name": name, "url": url, "checked_at": "2026-09-10",
            "size": {"value": None, "as_of": None, "scope": "Company-wide", "basis": "unknown", "sources": []},
            "headcount_trend": {"direction": "unknown", "period_start": None, "period_end": None,
                               "summary": "No comparable dated headcount evidence.", "sources": []},
            "latest_layoff": {"status": "unknown", "event_date": None, "date_type": "unspecified",
                              "summary": "Layoff history not established.", "sources": [],
                              "searched_from": None, "searched_through": None}}


def company_sample():
    data = sample()
    data["schema_version"] = 2
    data["companies"] = [company_record()]
    data["jobs"][0]["company_id"] = "example"
    return data


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.data = sample()
        self.job = self.data["jobs"][0]

    def test_weighted_fit_and_coverage_are_distinct(self):
        self.job["requirements"][0]["status"] = "partial"
        self.job["requirements"][1]["status"] = "absent"
        self.job["requirements"][2]["status"] = "unknown"
        result = report.assess(self.job, True)
        self.assertEqual(result["score"], 37.5)  # 17.5 + 0 + 0 + 10 + 10
        self.assertEqual(result["coverage"], 80.0)
        self.assertEqual(result["confidence"], "Medium")
        self.assertEqual(result["priority"], "Low")

    def test_unknown_never_boosts_credit_and_is_not_a_confirmed_gap(self):
        self.job["requirements"][-1]["status"] = "unknown"
        result = report.assess(self.job, True)
        self.assertEqual(result["score"], 90)
        self.assertEqual(result["coverage"], 90)
        self.assertEqual(result["gaps"], [])
        self.assertEqual(result["unknowns"], ["domain criterion"])

    def test_no_resume_no_requirements_and_all_unknown_are_not_scores(self):
        self.assertIsNone(report.assess(self.job, False)["score"])
        self.assertEqual(report.assess(self.job, False)["priority"], "Not scored")
        for row in self.job["requirements"]:
            row["status"] = "unknown"
        self.assertIsNone(report.assess(self.job, True)["score"])
        self.job["requirements"] = []
        self.assertIsNone(report.assess(self.job, True)["score"])

    def test_no_resume_does_not_display_supplied_personal_evidence(self):
        self.data["resume_provided"] = False
        self.assertNotIn("JD clause matches resume Experience section.", report.render_markdown(self.data))
        self.assertIn("No resume/profile supplied", report.render_markdown(self.data))

    def test_unmet_or_unknown_constraints_prevent_high_priority(self):
        self.job["hard_constraints"][0]["status"] = "unmet"
        result = report.assess(self.job, True)
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["priority"], "Blocked")
        self.job["hard_constraints"][0]["status"] = "unknown"
        self.assertEqual(report.assess(self.job, True)["priority"], "Clarify eligibility")
        self.job["hard_constraints"] = []
        self.assertEqual(report.assess(self.job, True)["priority"], "Clarify eligibility")

    def test_incomplete_description_always_provisional(self):
        self.job["job_description_complete"] = False
        result = report.assess(self.job, True)
        self.assertEqual(result["assessment"], "provisional")
        self.assertEqual(result["confidence"], "Low")
        self.assertEqual(result["priority"], "Review evidence")

    def test_missing_categories_are_not_renormalized(self):
        self.job["requirements"] = self.job["requirements"][:1]
        result = report.assess(self.job, True)
        self.assertEqual(result["score"], 35)
        self.assertEqual(result["coverage"], 35)
        self.assertEqual(result["assessment"], "provisional")

    def test_justified_exclusions_change_denominator(self):
        self.job["requirements"] = self.job["requirements"][:1]
        self.job["not_applicable_categories"] = {key: "Complete JD specifies no criteria in this category."
                                                  for key in list(report.WEIGHTS)[1:]}
        report.validate(self.data)
        result = report.assess(self.job, True)
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["denominator"], 35)
        self.assertEqual(result["coverage"], 100)
        self.job["requirements"] = []
        self.job["not_applicable_categories"]["required_skills"] = "No skills criteria in full JD."
        report.validate(self.data)
        self.assertIsNone(report.assess(self.job, True)["score"])

    def test_closed_and_unverified_are_separate_from_applications(self):
        self.job["posting_status"] = "closed"
        self.assertEqual(report.assess(self.job, True)["priority"], "Inactive")
        self.assertIn("## Inactive postings", report.render_markdown(self.data))
        self.job["posting_status"] = "unverified"
        self.assertEqual(report.assess(self.job, True)["priority"], "Lead only")
        self.assertIn("## Unverified discovery leads", report.render_markdown(self.data))

    def test_equal_weight_within_category(self):
        extra = copy.deepcopy(self.job["requirements"][0])
        extra["status"] = "absent"
        self.job["requirements"].append(extra)
        self.assertEqual(report.assess(self.job, True)["score"], 82.5)

    def test_shuffled_input_has_same_ranked_overview_and_csv_order(self):
        high_a = copy.deepcopy(self.job)
        high_a.update(id="a", title="High A")
        high_b = copy.deepcopy(high_a)
        high_b.update(id="b", title="High B")
        medium = copy.deepcopy(high_a)
        medium.update(id="c", title="Medium C")
        medium["requirements"][0]["status"] = "absent"  # 65 fit, fully known.
        clarify = copy.deepcopy(high_a)
        clarify.update(id="d", title="Clarify D")
        clarify["hard_constraints"] = []
        blocked = copy.deepcopy(high_a)
        blocked.update(id="e", title="Blocked E")
        blocked["hard_constraints"][0]["status"] = "unmet"
        self.data["jobs"] = [blocked, clarify, high_b, medium, high_a]
        expected = ["a", "b", "c", "d", "e"]
        self.assertEqual([job["id"] for job in report.ordered_jobs(self.data)], expected)
        first_markdown = report.render_markdown(self.data)
        first_csv = report.render_csv(self.data)
        self.data["jobs"].reverse()
        self.assertEqual(first_markdown, report.render_markdown(self.data))
        self.assertEqual(first_csv, report.render_csv(self.data))
        self.assertEqual([row["id"] for row in csv.DictReader(io.StringIO(first_csv))], expected)
        self.assertLess(first_markdown.index("[High A]"), first_markdown.index("[High B]"))
        self.assertLess(first_markdown.index("[High B]"), first_markdown.index("[Medium C]"))
        self.assertLess(first_markdown.index("[Medium C]"), first_markdown.index("[Clarify D]"))
        self.assertLess(first_markdown.index("## Blocked postings"), first_markdown.index("[Blocked E]"))


class ValidationAndExportTests(unittest.TestCase):
    def source(self, **changes):
        value = {"source": "Example board", "url": "https://example.com/jobs", "method": "web_search",
                 "query": 'site:example.com "support"', "status": "searched", "checked_at": "2026-09-10",
                 "results_seen": 3, "verified_open": 1, "notes": "Three results inspected; one verified on employer site."}
        value.update(changes)
        return value

    def test_source_coverage_distinguishes_access_failure_from_zero_matches(self):
        data = sample()
        data["search_sources"] = [self.source(results_seen=0, verified_open=0),
                                  self.source(status="blocked", results_seen=None, verified_open=0, notes="Sign-in required.")]
        report.validate(data)
        rendered = report.render_markdown(data)
        self.assertIn("## Sources checked", rendered)
        self.assertIn("| 0 | 0 |", rendered)
        self.assertIn("| Unknown | 0 |", rendered)
        self.assertIn("do not sum these counts", rendered)
        self.assertIn("Unique job records in this report: 1", rendered)

    def test_source_counts_status_and_metadata_must_be_consistent(self):
        cases = [{"results_seen": -1}, {"results_seen": True}, {"results_seen": None},
                 {"verified_open": 4}, {"verified_open": False}, {"method": "scrape_private_api"},
                 {"status": "all_jobs_searched"}, {"checked_at": "2026-02-30"}, {"url": "file:///etc/passwd"},
                 {"status": "blocked", "results_seen": 0, "verified_open": 0},
                 {"status": "skipped", "results_seen": None, "verified_open": 1},
                 {"status": "limited", "notes": ""}]
        for changes in cases:
            with self.subTest(changes=changes):
                data = sample()
                data["search_sources"] = [self.source(**changes)]
                with self.assertRaises(report.ValidationError):
                    report.validate(data)

    def test_discovery_links_survive_deduplication_and_escape_exports(self):
        data = sample()
        data["jobs"][0]["discovered_via"] = [
            {"source": "=Formula|<tag>", "url": "https://example.com/board/a(b)"},
            {"source": "Employer", "url": "https://example.com/jobs/original"}]
        data["search_sources"] = [self.source(source="<bad>|[link](evil)", query="find | jobs\n<script>")]
        report.validate(data)
        rendered = report.render_markdown(data)
        self.assertIn("Found via:", rendered)
        self.assertIn("a%28b%29", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<tag>", rendered)
        self.assertNotIn("[link](evil)", rendered)
        row = next(csv.DictReader(io.StringIO(report.render_csv(data))))
        self.assertTrue(row["discovery_sources"].startswith("'="))
        self.assertEqual(row["discovery_urls"], "https://example.com/board/a(b); https://example.com/jobs/original")
        data["jobs"][0]["discovered_via"][0]["url"] = "javascript:evil"
        with self.assertRaises(report.ValidationError):
            report.validate(data)

    def test_source_extensions_are_optional_for_existing_inputs(self):
        data = sample()
        report.validate(data)
        self.assertNotIn("## Sources checked", report.render_markdown(data))
        self.assertEqual(next(csv.DictReader(io.StringIO(report.render_csv(data))))["discovery_sources"], "")

    def test_reject_malformed_url_dates_types_and_claims(self):
        changes = [("url", "javascript:alert(1)"), ("url", "https://example.com/a b"),
                   ("url", "https://user:pass@example.com"), ("url", "https://example.com:bad/a"),
                   ("checked_at", "2026-02-30"), ("job_description_complete", "true"),
                   ("requirements", {}), ("title", "")]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                data = sample()
                data["jobs"][0][key] = value
                with self.assertRaises(report.ValidationError):
                    report.validate(data)
        data = sample()
        data["jobs"][0]["requirements"][0]["evidence"] = ""
        with self.assertRaises(report.ValidationError):
            report.validate(data)
        data["jobs"][0]["requirements"][0]["status"] = "unknown"
        report.validate(data)

    def test_reject_conflicting_or_unjustified_exclusions(self):
        data = sample()
        job = data["jobs"][0]
        job["not_applicable_categories"] = {"domain": "Not relevant in the complete JD."}
        with self.assertRaises(report.ValidationError):
            report.validate(data)
        job["requirements"].pop()
        job["job_description_complete"] = False
        with self.assertRaises(report.ValidationError):
            report.validate(data)
        job["job_description_complete"] = True
        job["not_applicable_categories"]["domain"] = ""
        with self.assertRaises(report.ValidationError):
            report.validate(data)

    def test_reject_duplicate_ids_unknown_fields_and_duplicate_json_keys(self):
        data = sample()
        data["jobs"].append(copy.deepcopy(data["jobs"][0]))
        with self.assertRaises(report.ValidationError):
            report.validate(data)
        data = sample()
        data["jobs"][0]["hiring_probability"] = 0.9
        with self.assertRaises(report.ValidationError):
            report.validate(data)
        with self.assertRaises(report.ValidationError):
            json.loads('{"x":1,"x":2}', object_pairs_hook=report.reject_duplicates)

    def test_markdown_escapes_html_links_and_table_injection(self):
        data = sample()
        data["jobs"][0]["title"] = '<script>alert(1)</script>|[Click](javascript:evil)\n# heading'
        data["jobs"][0]["url"] = 'https://example.com/a(b)>"'
        report.validate(data)
        rendered = report.render_markdown(data)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("[Click](javascript:evil)", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn(r"\|", rendered)
        self.assertIn("a%28b%29%3E%22", rendered)

    def test_csv_formula_injection_is_neutralized_and_quotes_round_trip(self):
        for malicious in ("=SUM(1,2)", "+1+2", "-1+2", "@SUM(A1)", "  =1+1", "\t=1+1", "\n=1+1"):
            data = sample()
            data["jobs"][0]["title"] = malicious
            row = list(csv.DictReader(io.StringIO(report.render_csv(data))))[0]
            self.assertTrue(row["title"].startswith("'"))
        data["jobs"][0]["title"] = 'Analyst, "Planning"\nRemote'
        row = list(csv.DictReader(io.StringIO(report.render_csv(data))))[0]
        self.assertEqual(row["title"], data["jobs"][0]["title"])

    def test_cli_writes_outputs_and_refuses_accidental_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            output = Path(directory) / "report.md"
            csv_output = Path(directory) / "report.csv"
            source.write_text(json.dumps(sample()), encoding="utf-8")
            command = [sys.executable, str(SCRIPT), str(source), "--output", str(output), "--csv", str(csv_output)]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn(r"100\.0/100", output.read_text())
            self.assertEqual(len(list(csv.DictReader(io.StringIO(csv_output.read_text())))), 1)
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            self.assertEqual(subprocess.run(command + ["--overwrite"], capture_output=True).returncode, 0)
            source_before = source.read_bytes()
            conflicting = [sys.executable, str(SCRIPT), str(source), "--output", str(source), "--overwrite"]
            self.assertEqual(subprocess.run(conflicting, capture_output=True).returncode, 2)
            self.assertEqual(source.read_bytes(), source_before)


class CompanyReportTests(unittest.TestCase):
    def setUp(self):
        self.data = company_sample()
        self.company = self.data["companies"][0]
        self.job = self.data["jobs"][0]

    def add_job(self, identifier, **changes):
        job = copy.deepcopy(self.job)
        job.update(id=identifier, title=identifier, url="https://example.com/jobs/" + identifier, **changes)
        self.data["jobs"].append(job)
        return job

    def result(self):
        report.validate(self.data)
        return report.company_assessments(self.data)["example"]

    def test_top_three_follow_job_priority_and_exclude_incomplete_or_nonactionable(self):
        self.job.update(id="a", title="Best")
        medium = self.add_job("b")
        medium["requirements"][0]["status"] = "absent"  # 65
        explore = self.add_job("c")
        explore["requirements"][0]["status"] = "absent"
        explore["requirements"][2]["status"] = "absent"  # 45
        self.add_job("d-unknown", hard_constraints=[])  # 100, but clarify eligibility comes later.
        self.add_job("incomplete", job_description_complete=False)
        self.add_job("closed", posting_status="closed")
        self.add_job("unverified", posting_status="unverified")
        blocked = self.add_job("blocked")
        blocked["hard_constraints"][0]["status"] = "unmet"
        result = self.result()
        self.assertEqual(result["recommended_job_ids"], ["a", "b", "c"])
        self.assertEqual(result["component_job_ids"], ["a", "b", "c"])
        self.assertEqual(result["score"], 70.0)
        self.assertEqual(result["coverage"], 100)
        self.assertEqual(result["assessment"], "assessed")
        self.assertEqual(result["eligible_job_count"], 4)
        rendered = report.render_markdown(self.data)
        overview = rendered.split("## All jobs by company")[0]
        for title in ("incomplete", "closed", "unverified", "blocked", "d-unknown"):
            self.assertNotIn("[" + title, overview)
        self.assertIn("#### Blocked postings", rendered)
        self.assertIn("#### Unverified discovery leads", rendered)
        self.assertIn("#### Inactive postings", rendered)
        self.assertIn("[incomplete]", rendered)  # Retained below, never recommended.

    def test_provisional_rules_and_unscored_recommendations(self):
        self.assertEqual(self.result()["assessment"], "provisional")
        self.add_job("two")
        third = self.add_job("three")
        self.assertEqual(self.result()["assessment"], "assessed")
        third["hard_constraints"] = []
        self.assertEqual(self.result()["assessment"], "provisional")
        overview = report.render_markdown(self.data).split("## All jobs by company")[0]
        self.assertIn("Clarify eligibility; eligibility Unknown", overview)
        third["hard_constraints"] = copy.deepcopy(self.job["hard_constraints"])
        third["requirements"][0]["status"] = "unknown"  # 65% known, provisional job.
        result = self.result()
        self.assertEqual(result["assessment"], "provisional")
        self.assertEqual(result["coverage"], 88.3)
        third["requirements"] = []
        result = self.result()
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["scored_count"], 2)
        self.assertEqual(len(result["recommended_job_ids"]), 3)
        self.assertEqual(result["assessment"], "provisional")
        self.assertNotIn("three", result["component_job_ids"])

    def test_unknown_and_missing_resume_are_na_not_zero(self):
        for row in self.job["requirements"]:
            row["status"] = "unknown"
        result = self.result()
        self.assertIsNone(result["score"])
        self.assertIsNone(result["coverage"])
        self.assertEqual(result["component_job_ids"], [])
        self.data["resume_provided"] = False
        self.assertIsNone(self.result()["score"])
        rendered = report.render_markdown(self.data)
        self.assertNotIn("JD clause matches resume Experience section.", rendered)
        self.assertIn("No resume/profile supplied", rendered)
        self.assertIn("N/A", rendered)
        self.data["resume_provided"] = True
        for row in self.job["requirements"]:
            row["status"] = "absent"
        self.assertEqual(self.result()["score"], 0)  # Known mismatch is a real zero.

    def test_company_facts_do_not_change_fit_and_unknowns_are_explicit(self):
        before = self.result()["score"]
        sources = [{"label": "Company announcement", "url": "https://example.com/news"}]
        self.company["size"].update(value="10,000 employees", as_of="2026-06-30", basis="reported", sources=sources)
        self.company["headcount_trend"].update(direction="declining", period_start="2025-06-30",
                                                period_end="2026-06-30", summary="Comparable headcount fell.", sources=sources)
        self.company["latest_layoff"].update(status="reported", event_date="2026-10-01", date_type="effective",
                                              summary="Announced reduction takes effect in October.", sources=sources)
        self.assertEqual(self.result()["score"], before)
        rendered = report.render_markdown(self.data)
        self.assertIn("scheduled effective", rendered)
        self.assertIn("Company announcement", rendered)
        self.assertIn("headcount trend and layoffs do not affect it", rendered)
        unknown_data = company_sample()
        unknown_rendered = report.render_markdown(unknown_data)
        self.assertIn("Unknown; scope:", unknown_rendered)
        self.assertNotIn("No layoffs", unknown_rendered)

    def test_overview_first_grouped_jobs_and_target_counts_do_not_pad(self):
        self.data["search_sources"] = [ValidationAndExportTests().source()]
        self.data["search_summary"] = "Synthetic fixture, checked September 2026; no live recommendations."
        self.data["companies"].append(company_record("empty", "Empty Co", None))
        inactive = company_record("inactive", "Inactive Co")
        self.data["companies"].append(inactive)
        self.add_job("old", company_id="inactive", company="Inactive Co", posting_status="closed")
        self.add_job("another")
        report.validate(self.data)
        rendered = report.render_markdown(self.data)
        self.assertLess(rendered.index("## Company overview"), rendered.index("## All jobs by company"))
        self.assertLess(rendered.index("Synthetic fixture"), rendered.index("| Company |"))
        self.assertLess(rendered.index("## All jobs by company"), rendered.index("## Sources checked"))
        self.assertLess(rendered.index("## Sources checked"), rendered.index("## Evidence and calculation details"))
        self.assertIn("Company target: 20", rendered)
        self.assertIn("Companies researched: 3", rendered)
        self.assertIn("researcher-verified open postings: 1", rendered)
        self.assertIn("Shortfall from the recommendable-company target: 19", rendered)
        self.assertIn("No job records supplied for this company.", rendered)
        self.assertIn("### Empty Co (website unknown)", rendered)
        self.assertNotIn("[Empty Co]", rendered)
        self.assertIn("[Example](<https://example.com>)", rendered)
        before = (rendered, report.render_csv(self.data), report.render_companies_csv(self.data))
        self.data["jobs"].reverse()
        self.data["companies"].reverse()
        self.assertEqual(before, (report.render_markdown(self.data), report.render_csv(self.data),
                                  report.render_companies_csv(self.data)))

    def test_blocked_only_company_does_not_satisfy_target(self):
        self.job["hard_constraints"][0]["status"] = "unmet"
        report.validate(self.data)
        rendered = report.render_markdown(self.data)
        self.assertIn("researcher-verified open postings: 1", rendered)
        self.assertIn("Companies with recommendable postings: 0", rendered)
        self.assertIn("Shortfall from the recommendable-company target: 20", rendered)

    def test_safe_company_markdown_csv_and_original_job_columns(self):
        name = '=SUM(1,2)|[evil](javascript:bad)<script>'
        self.company["name"] = self.job["company"] = name
        self.company["url"] = 'https://example.com/a(b)>"'
        self.company["size"].update(value="=1+1", as_of="2026-01-01", basis="estimate",
                                    sources=[{"label": "<img>|[bad](evil)", "url": "https://example.com/a(b)"}])
        self.company["headcount_trend"]["summary"] = "@SUM(A1)\n|<script>"
        report.validate(self.data)
        rendered = report.render_markdown(self.data)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<img>", rendered)
        self.assertNotIn("[evil](javascript:bad)", rendered)
        self.assertIn("a%28b%29%3E%22", rendered)
        original_fields = next(csv.reader(io.StringIO(report.render_csv(sample()))))
        csv_rows = list(csv.DictReader(io.StringIO(report.render_csv(self.data))))
        self.assertEqual(list(csv_rows[0])[:len(original_fields)], original_fields)
        self.assertTrue(csv_rows[0]["company_name"].startswith("'="))
        self.assertTrue(csv_rows[0]["company_size"].startswith("'="))
        self.assertTrue(csv_rows[0]["company_headcount_summary"].startswith("'@"))
        summary_row = next(csv.DictReader(io.StringIO(report.render_companies_csv(self.data))))
        self.assertEqual(summary_row["company_recommended_job_ids"], self.job["id"])
        self.assertEqual(summary_row["company_fit_score"], "100.0")
        self.assertEqual(summary_row["company_size_sources"], "<img>|[bad](evil): https://example.com/a(b)")

    def test_no_jobs_still_exports_company_research(self):
        self.data["jobs"] = []
        report.validate(self.data)
        result = self.result()
        self.assertEqual(result["scored_count"], 0)
        self.assertEqual(result["open_job_count"], 0)
        self.assertEqual(len(list(csv.DictReader(io.StringIO(report.render_csv(self.data))))), 0)
        self.assertEqual(len(list(csv.DictReader(io.StringIO(report.render_companies_csv(self.data))))), 1)
        self.assertIn("No job records supplied", report.render_markdown(self.data))

    def test_cli_company_export_and_all_destination_alias_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output, csv_output = (Path(directory) / name for name in ("in.json", "out.md", "companies.csv"))
            source.write_text(json.dumps(self.data), encoding="utf-8")
            command = [sys.executable, str(SCRIPT), str(source), "--output", str(output), "--companies-csv", str(csv_output)]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(len(list(csv.DictReader(io.StringIO(csv_output.read_text())))), 1)
            before = output.read_bytes()
            conflict = command[:-1] + [str(output), "--overwrite"]
            self.assertEqual(subprocess.run(conflict, capture_output=True).returncode, 2)
            self.assertEqual(output.read_bytes(), before)
            old_schema = sample()
            source.write_text(json.dumps(old_schema), encoding="utf-8")
            self.assertEqual(subprocess.run(command + ["--overwrite"], capture_output=True).returncode, 2)
            self.assertEqual(output.read_bytes(), before)


class CompanyValidationTests(unittest.TestCase):
    def assert_invalid(self, modify):
        data = company_sample()
        modify(data)
        with self.assertRaises(report.ValidationError):
            report.validate(data)

    def test_versions_targets_identity_and_supplied_ratings(self):
        for version in (True, 2.0, 0, 3, "2"):
            with self.subTest(version=version):
                self.assert_invalid(lambda data: data.update(schema_version=version))
        for target in (True, 0, 101, 2.5, "20", None):
            with self.subTest(target=target):
                self.assert_invalid(lambda data: data.update(company_target=target))
        for modify in (
            lambda data: data.pop("companies"),
            lambda data: data.update(companies={}),
            lambda data: data["jobs"][0].pop("company_id"),
            lambda data: data["jobs"][0].update(company_id="missing"),
            lambda data: data["jobs"][0].update(company="Different name"),
            lambda data: data["companies"].append(copy.deepcopy(data["companies"][0])),
            lambda data: data["companies"][0].update(company_score=99),
            lambda data: data["companies"][0].update(url="javascript:evil"),
            lambda data: data["companies"][0].update(checked_at="2026-02-30"),
        ):
            self.assert_invalid(modify)
        for target in (1, 20, 100):
            data = company_sample()
            data["company_target"] = target
            report.validate(data)

    def test_size_claims_need_evidence_and_consistent_dates(self):
        invalid = [
            {"value": "500", "basis": "unknown"},
            {"value": None, "basis": "reported"},
            {"value": "500", "basis": "reported", "sources": []},
            {"as_of": "2026-09-10"},
            {"basis": "exact"},
            {"scope": ""},
            {"sources": [{"label": "Source", "url": "file:///secret"}]},
        ]
        for changes in invalid:
            with self.subTest(changes=changes):
                self.assert_invalid(lambda data: data["companies"][0]["size"].update(changes))
        data = company_sample()
        size = data["companies"][0]["size"]
        size.update(value="100–200", basis="range", sources=[{"label": "Directory estimate", "url": "https://example.com/profile"}])
        report.validate(data)  # Source date can be unknown; displayed as unknown.
        size["as_of"] = "2026-09-11"
        with self.assertRaises(report.ValidationError):
            report.validate(data)

    def test_trend_requires_comparable_period_and_sources_not_invented_stability(self):
        sources = [{"label": "Dated headcounts", "url": "https://example.com/headcount"}]
        for changes in (
            {"direction": "stable"},
            {"direction": "growing", "period_start": "2025-09-10", "period_end": "2026-09-10"},
            {"direction": "growing", "period_start": None, "period_end": "2026-09-10", "sources": sources},
            {"direction": "growing", "period_start": "2026-09-10", "period_end": "2025-09-10", "sources": sources},
            {"direction": "growing", "period_start": "2026-09-10", "period_end": "2026-09-11", "sources": sources},
        ):
            with self.subTest(changes=changes):
                self.assert_invalid(lambda data: data["companies"][0]["headcount_trend"].update(changes))
        data = company_sample()
        data["companies"][0]["headcount_trend"].update(direction="mixed", period_start="2025-09-10",
                                                     period_end="2026-09-10", sources=sources)
        report.validate(data)
        data["companies"][0]["headcount_trend"]["direction"] = "unknown"
        report.validate(data)  # A searched period is known even if the trend remains unresolved.
        self.assertIn("2025\\-09\\-10 to 2026\\-09\\-10", report.render_markdown(data))

    def test_none_found_requires_bounded_sourced_search_and_does_not_mean_none(self):
        data = company_sample()
        layoff = data["companies"][0]["latest_layoff"]
        layoff.update(status="none_found", searched_from="2025-01-01", searched_through="2026-09-10",
                      summary="No relevant notice in checked company news and state notices.")
        with self.assertRaises(report.ValidationError):
            report.validate(data)
        layoff["sources"] = [{"label": "Checked notices", "url": "https://example.com/notices"}]
        report.validate(data)
        self.assertIn("not proof that no layoffs occurred", report.render_markdown(data))
        for changes in ({"event_date": "2026-01-01"}, {"date_type": "announcement"}, {"searched_from": None},
                        {"searched_from": "2026-09-11"}, {"searched_through": "2026-09-11"}):
            changed = copy.deepcopy(data)
            changed["companies"][0]["latest_layoff"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(report.ValidationError):
                report.validate(changed)

    def test_reported_layoff_date_semantics_and_unknown_nulls(self):
        sources = [{"label": "Announcement", "url": "https://example.com/news"}]
        for changes in ({"status": "reported"}, {"event_date": "2026-01-01"}, {"date_type": "effective"},
                        {"searched_from": "2025-01-01", "searched_through": None},
                        {"status": "reported", "date_type": "announcement", "sources": sources},
                        {"status": "reported", "event_date": "2026-01-01", "date_type": "unspecified", "sources": sources},
                        {"status": "reported", "event_date": "2026-09-11", "date_type": "announcement", "sources": sources}):
            with self.subTest(changes=changes):
                self.assert_invalid(lambda data: data["companies"][0]["latest_layoff"].update(changes))
        data = company_sample()
        data["companies"][0]["latest_layoff"].update(status="reported", sources=sources)
        report.validate(data)  # A sourced report with an unspecified date remains date unknown.
        self.assertIn("date unknown", report.render_markdown(data))
        data = company_sample()
        data["companies"][0]["latest_layoff"].update(searched_from="2025-01-01", searched_through="2026-01-01")
        report.validate(data)  # Limited source access can leave the outcome unknown for a real check window.
        self.assertIn("searched 2025\\-01\\-01 to 2026\\-01\\-01", report.render_markdown(data))


if __name__ == "__main__":
    unittest.main()
