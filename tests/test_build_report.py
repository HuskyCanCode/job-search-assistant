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


if __name__ == "__main__":
    unittest.main()
