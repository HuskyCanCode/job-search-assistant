"""Offline HTML parity, hostile-input safety, and output transaction checks."""

import contextlib
from html.parser import HTMLParser
import importlib.util
import io
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_report.py"
SPEC = importlib.util.spec_from_file_location("html_test_report_api", SCRIPT)
report = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = report
SPEC.loader.exec_module(report)


class Node:
    def __init__(self, tag="root", attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def text(self):
        return "".join(child.text() if isinstance(child, Node) else child for child in self.children)

    def links(self):
        return [node.attrs["href"] for node in self.walk() if node.tag == "a" and "href" in node.attrs]


class Document(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, value):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(value)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                self.stack = self.stack[:index]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def nodes(self, tag=None, attribute=None):
        return [node for node in self.root.walk()
                if (tag is None or node.tag == tag) and (attribute is None or attribute in node.attrs)]

    def by_id(self, identifier):
        return next(node for node in self.root.walk() if node.attrs.get("id") == identifier)


def job(identifier="best", company_id="example", company="Example", **changes):
    result = {
        "id": identifier, "company_id": company_id, "title": "Role " + identifier,
        "company": company, "url": "https://example.com/jobs/" + identifier,
        "location": "Austin, TX · Onsite", "salary": None, "posted_at": "2026-08-25",
        "checked_at": "2026-09-10", "posting_status": "open", "job_description_complete": True,
        "requirements": [{"category": category, "requirement": category + " criterion",
                          "status": "met", "evidence": "Evidence for " + category}
                         for category in report.WEIGHTS],
        "hard_constraints": [{"constraint": "Work arrangement", "status": "met",
                              "evidence": "Posting is onsite; user explicitly requested onsite."}],
    }
    result.update(changes)
    return result


def company(identifier="example", name="Example", url="https://example.com"):
    return {"id": identifier, "name": name, "url": url, "checked_at": "2026-09-10",
            "size": {"value": None, "as_of": None, "scope": "Company-wide", "basis": "unknown", "sources": []},
            "headcount_trend": {"direction": "unknown", "period_start": None, "period_end": None,
                               "summary": "No comparable dated headcount evidence.", "sources": []},
            "latest_layoff": {"status": "unknown", "event_date": None, "date_type": "unspecified",
                              "summary": "Layoff history not established.", "sources": [],
                              "searched_from": None, "searched_through": None}}


def sample(version=2):
    data = {"schema_version": version, "resume_provided": True,
            "search_summary": "Synthetic fixture only; not live recommendations.", "jobs": [job()]}
    if version == 2:
        data["companies"] = [company()]
    else:
        del data["jobs"][0]["company_id"]
    return data


def render(data):
    report.validate(data)
    html = report.render_html(data)
    return html, Document(html)


def assert_score(test, node, result):
    expected = "N/A" if result["score"] is None else f'{result["score"]:.1f}/100'
    test.assertIn(expected, node.text())
    if result["score"] is not None:
        test.assertIn(result["assessment"].lower(), node.text().lower())


class HtmlContentTests(unittest.TestCase):
    def test_recommended_is_default_only_when_company_recommendations_exist(self):
        no_recommendations = sample()
        blocked = job("blocked")
        blocked["hard_constraints"][0]["status"] = "unmet"
        no_recommendations["jobs"] = [blocked, job("closed", posting_status="closed"),
                                      job("unverified", posting_status="unverified"),
                                      job("incomplete", job_description_complete=False)]
        empty = sample()
        empty["jobs"] = []
        for label, data, expected in (("company recommendations", sample(), "recommended"),
                                      ("no eligible recommendations", no_recommendations, "all"),
                                      ("empty report", empty, "all"),
                                      ("legacy report", sample(1), "all")):
            with self.subTest(case=label):
                _, document = render(data)
                selected = [node.attrs["value"] for node in document.by_id("report-status").walk()
                            if node.tag == "option" and "selected" in node.attrs]
                self.assertEqual(selected, [expected])
                cards = document.nodes(attribute="data-job")
                self.assertEqual(len(cards), len(data["jobs"]))
                self.assertTrue(all("hidden" not in card.attrs for card in cards))

    def test_compact_rows_keep_fit_cautions_visible_and_details_available(self):
        data = sample()
        record = data["jobs"][0]
        record["requirements"][0].update(status="unknown", evidence="")
        record["hard_constraints"] = []
        record["notes"] = "Research detail retained after simplifying the row."
        record["discovered_via"] = [{"source": "Original discovery", "url": "https://example.com/origin"}]
        _, document = render(data)
        card = document.nodes(attribute="data-job")[0]
        details = next(node for node in card.walk() if node.tag == "details"
                       and "evidence" in node.attrs.get("class", "").split())
        self.assertNotIn("open", details.attrs)

        visible_links = []

        def outside_details(node):
            if node.tag == "details":
                return ""
            if node.tag == "a" and "href" in node.attrs:
                visible_links.append(node.attrs["href"])
            return "".join(outside_details(child) if isinstance(child, Node) else child for child in node.children)

        visible = outside_details(card)
        result = report.assess(record, True)
        self.assertIn(f'{result["score"]:.1f}/100', visible)
        for caution in (result["assessment"], result["eligibility"], result["priority"]):
            self.assertIn(caution.lower(), visible.lower())
        self.assertIn(record["title"], visible)
        self.assertIn(record["url"], visible_links)
        self.assertIn(record["discovered_via"][0]["url"], details.links())
        for detail in (record["posted_at"], record["checked_at"], record["notes"],
                       record["requirements"][1]["evidence"], "No constraints supplied"):
            self.assertIn(detail, details.text())

    def test_v1_and_v2_comparison_rows_link_to_matching_cards_and_preserve_status(self):
        for version in (1, 2):
            with self.subTest(version=version):
                data = sample(version)
                blocked = job("blocked")
                blocked["hard_constraints"][0]["status"] = "unmet"
                data["jobs"] += [blocked, job("unverified", posting_status="unverified"),
                                 job("closed", "second", "Second company", posting_status="closed")]
                if version == 2:
                    data["companies"].append(company("second", "Second company"))
                else:
                    for record in data["jobs"]:
                        record.pop("company_id", None)
                _, document = render(data)
                cards = {card.attrs["id"]: card for card in document.nodes(attribute="data-job")}
                rows = document.nodes("tr", "data-compared-job")
                self.assertEqual(len(rows), len(data["jobs"]))
                self.assertCountEqual([row.attrs["data-compared-job"] for row in rows], cards)
                for row in rows:
                    target = row.attrs["data-compared-job"]
                    self.assertIn("#" + target, row.links())
                    posting = next(record for record in data["jobs"] if record["url"] in row.links())
                    self.assertIn(posting["url"], cards[target].links())
                    self.assertIn(posting["title"], row.text())
                    cells = [child for child in row.children if isinstance(child, Node) and child.tag == "td"]
                    self.assertEqual(cells[5].text(), posting["posting_status"])
                    result = report.assess(posting, data["resume_provided"])
                    self.assertIn(result["eligibility"], cells[4].text())
                    self.assertIn(result["priority"], cells[4].text())
                    assert_score(self, row, result)
                    self.assertNotIn("hidden", row.attrs)

    def test_v1_and_v2_render_static_job_evidence_with_existing_scores(self):
        for version in (1, 2):
            with self.subTest(version=version):
                data = sample(version)
                data["jobs"][0]["requirements"][0]["status"] = "partial"
                html, document = render(data)
                self.assertIn("<!doctype html", html.lower())
                cards = document.nodes(attribute="data-job")
                self.assertEqual(len(cards), 1)
                card = cards[0]
                self.assertNotIn("hidden", card.attrs)
                if version == 1:
                    self.assertFalse(document.nodes(attribute="data-company-row"))
                    self.assertNotIn('value="recommended"', html)
                result = report.assess(data["jobs"][0], True)
                assert_score(self, card, result)
                for value in (data["jobs"][0]["title"], result["priority"],
                              result["eligibility"], "Evidence for responsibilities", "2026-08-25", "2026-09-10"):
                    self.assertIn(value, card.text())
                self.assertIn(data["jobs"][0]["url"], card.links())
                self.assertTrue(document.nodes("details"))
                self.assertIn("probability", document.root.text().lower())
                self.assertIn("offline", document.root.text().lower())

    def test_company_top_three_and_order_match_existing_assessment(self):
        data = sample()
        medium, explore = job("medium"), job("explore")
        medium["requirements"][0]["status"] = "absent"
        explore["requirements"][0]["status"] = "absent"
        explore["requirements"][2]["status"] = "absent"
        blocked = job("blocked")
        blocked["hard_constraints"][0]["status"] = "unmet"
        data["jobs"] += [job("unverified", posting_status="unverified"), blocked,
                         job("incomplete", job_description_complete=False),
                         job("closed", posting_status="closed"), explore, medium,
                         job("clarify", hard_constraints=[])]
        data["companies"].append(company("empty", "Empty company", None))
        html, document = render(data)
        self.assertLess(html.index('id="job-details"'), html.index('id="company-overview"'))
        results = report.company_assessments(data)
        rows = document.nodes(attribute="data-company-row")
        self.assertEqual(len(rows), len(data["companies"]))
        all_job_urls = {item["url"] for item in data["jobs"]}
        for row, company_row in zip(rows, report.ordered_companies(data, results)):
            assessment = results[company_row["id"]]
            self.assertIn(company_row["name"], row.text())
            assert_score(self, row, assessment)
            recommendations = [url for url in row.links() if url in all_job_urls]
            self.assertEqual(recommendations, [item["url"] for item in assessment["recommendations"]])
        expected_jobs = [item for company_row in report.ordered_companies(data, results)
                         for item in results[company_row["id"]]["jobs"]]
        cards = document.nodes(attribute="data-job")
        self.assertEqual(len(cards), len(expected_jobs))
        for card, item in zip(cards, expected_jobs):
            self.assertIn(item["title"], card.text())
            self.assertEqual(card.attrs["data-recommended"], str(item["id"] in ("best", "medium", "explore")).lower())
            self.assertEqual(card.attrs["data-nonactive"], str(item["id"] in ("blocked", "unverified", "closed")).lower())
            self.assertEqual(card.attrs["data-review"], str(item["id"] in ("clarify", "unverified", "incomplete")).lower())
        overview = document.by_id("company-overview").text()
        self.assertIn("70.0/100", overview)
        for item in ("Role blocked", "Role incomplete", "Role unverified", "Role closed", "Role clarify"):
            self.assertNotIn(item, overview)
        self.assertIn("Empty company", document.root.text())
        self.assertIn("website unknown", document.root.text().lower())

    def test_shuffled_input_does_not_change_rendered_order_or_scores(self):
        data = sample()
        data["companies"].append(company("second", "Second company", "https://second.example.com"))
        data["jobs"] += [job("z"), job("second", "second", "Second company")]
        before, _ = render(data)
        data["jobs"].reverse()
        data["companies"].reverse()
        after, _ = render(data)
        self.assertEqual(before, after)

    def test_all_links_dates_research_notes_and_unknowns_survive(self):
        data = sample()
        entry = data["companies"][0]
        entry["size"].update(value="1,500 employees", as_of="2026-06-30", basis="reported",
                             sources=[{"label": "Headcount source", "url": "https://example.com/headcount?a=1&b=2"}])
        entry["headcount_trend"].update(direction="declining", period_start="2025-06-30", period_end="2026-06-30",
                                       summary="Comparable dated headcount declined.",
                                       sources=[{"label": "Trend source", "url": "https://example.com/trend"}])
        entry["latest_layoff"].update(status="reported", event_date="2026-10-01", date_type="effective",
                                     summary="Future effective date was announced.", searched_from="2025-09-10",
                                     searched_through="2026-09-10",
                                     sources=[{"label": "Official notice", "url": "https://example.com/notice"}])
        record = data["jobs"][0]
        record["notes"] = "Researcher-note sentinel: verify the stated shift."
        record["requirements"][2].update(status="unknown", evidence="")
        record["hard_constraints"] = []
        record["discovered_via"] = [{"source": "Permitted origin", "url": "https://example.com/origin?a=1&b=2"}]
        data["search_sources"] = [
            {"source": "Permitted board", "url": "https://example.com/board", "method": "public_api",
             "query": "application support", "status": "searched", "checked_at": "2026-09-09",
             "results_seen": 1, "verified_open": 1, "notes": "One completed source check."},
            {"source": "Unavailable source", "url": "https://example.com/unavailable", "method": "employer_site",
             "query": "support", "status": "blocked", "checked_at": "2026-09-08",
             "results_seen": None, "verified_open": 0, "notes": "Access unavailable; vacancy count unknown."},
        ]
        _, document = render(data)
        links = document.root.links()
        for url in [record["url"], entry["url"], record["discovered_via"][0]["url"],
                    *(source["url"] for field in ("size", "headcount_trend", "latest_layoff") for source in entry[field]["sources"]),
                    *(source["url"] for source in data["search_sources"])]:
            self.assertIn(url, links)
        text = document.root.text()
        for expected in ("2026-10-01", "2025-06-30", "2026-06-30", "2025-09-10", "2026-09-10",
                         "2026-09-09", "2026-09-08", "scheduled effective", record["notes"],
                         "seniority criterion", "Unknown", "Clarify eligibility", "Headcount source",
                         "Trend source", "Official notice", "Permitted origin", "vacancy count unknown"):
            self.assertIn(expected, text)
        self.assertIn("do not sum", document.by_id("source-audit").text().lower())

    def test_no_resume_suppresses_personal_fit_evidence_and_scores(self):
        for version in (1, 2):
            with self.subTest(version=version):
                data = sample(version)
                data["resume_provided"] = False
                data["jobs"][0]["requirements"][0]["evidence"] = "PRIVATE_RESUME_EVIDENCE_DO_NOT_RENDER"
                html, document = render(data)
                self.assertNotIn("PRIVATE_RESUME_EVIDENCE_DO_NOT_RENDER", html)
                self.assertIn("No resume/profile supplied", document.root.text())
                self.assertIn("N/A", document.nodes(attribute="data-job")[0].text())
                self.assertNotIn("100.0/100", document.root.text())

    def test_empty_inputs_preserve_company_research_without_fake_jobs(self):
        for version in (1, 2):
            with self.subTest(version=version):
                data = sample(version)
                data["jobs"] = []
                _, document = render(data)
                self.assertEqual(document.nodes(attribute="data-job"), [])
                self.assertIn("No jobs", document.root.text())
                if version == 2:
                    self.assertIn("Example", document.by_id("company-overview").text())
                    self.assertIn("Unknown", document.by_id("company-overview").text())

    def test_justified_category_exclusions_keep_denominator_and_reason(self):
        data = sample()
        record = data["jobs"][0]
        record["requirements"] = record["requirements"][:1]
        record["not_applicable_categories"] = {
            category: "Complete JD establishes no criterion here: " + category
            for category in list(report.WEIGHTS)[1:]}
        _, document = render(data)
        card = document.nodes(attribute="data-job")[0]
        self.assertIn("100.0/100", card.text())
        self.assertIn("35", card.text())
        for reason in record["not_applicable_categories"].values():
            self.assertIn(reason, card.text())


class HtmlSafetyTests(unittest.TestCase):
    def test_untrusted_text_attributes_and_template_tokens_cannot_create_markup_or_script(self):
        baseline, baseline_doc = render(sample())
        data = sample()
        attack = '</script><script>alert("SENTINEL")</script><img src=x onerror=alert(1)> @@REPORT_JS@@'
        attr_attack = '\" autofocus onfocus=alert(1) data-attacked=\"yes'
        data["search_summary"] = attack
        data["companies"][0]["name"] = data["jobs"][0]["company"] = attack
        data["jobs"][0]["id"] = attr_attack
        data["jobs"][0]["title"] = attack + attr_attack
        data["jobs"][0]["notes"] = attack
        data["jobs"][0]["requirements"][0]["evidence"] = attack
        data["jobs"][0]["url"] = 'https://example.com/a?label=\"><svg/onload=alert(1)>'
        html, document = render(data)
        self.assertIn(attack, document.root.text())
        self.assertIn("&lt;/script&gt;", html)
        self.assertNotIn("<img src=x", html)
        self.assertEqual([node.text() for node in document.nodes("script")],
                         [node.text() for node in baseline_doc.nodes("script")])
        self.assertEqual(len(document.nodes("img")), len(baseline_doc.nodes("img")))
        self.assertEqual(len(document.nodes("svg")), len(baseline_doc.nodes("svg")))
        for node in document.root.walk():
            self.assertFalse(any(name.startswith("on") for name in node.attrs), (node.tag, node.attrs))
            self.assertNotIn("data-attacked", node.attrs)
        self.assertIn(data["jobs"][0]["url"], document.root.links())
        ids = [node.attrs["id"] for node in document.nodes(attribute="id")]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn(attr_attack, ids)

    def test_no_external_executable_resources_and_no_remote_storage_or_fetch(self):
        html, document = render(sample())
        self.assertFalse(document.nodes("iframe"))
        self.assertFalse(document.nodes("object"))
        self.assertFalse(document.nodes("embed"))
        self.assertFalse(document.nodes("base"))
        for node in document.nodes("script"):
            self.assertNotIn("src", node.attrs)
            self.assertNotRegex(node.text(), r"\b(?:fetch|XMLHttpRequest|WebSocket|sendBeacon|localStorage|sessionStorage)\b")
        for node in document.nodes("link"):
            self.assertNotIn("stylesheet", node.attrs.get("rel", ""))
        for node in document.nodes("style"):
            self.assertNotRegex(node.text(), r"(?i)@import|url\(\s*['\"]?https?:")
        for node in document.root.walk():
            if "src" in node.attrs:
                self.assertFalse(node.attrs["src"].startswith(("http:", "https:", "//")))
        for identifier in ("report-search", "report-status", "filter-reset", "print-report", "no-results"):
            self.assertIsNotNone(document.by_id(identifier))
        self.assertIn("@media print", html)
        self.assertTrue(document.nodes(attribute="data-job"))  # Content exists before JavaScript runs.

    def test_invalid_schemes_rejected_before_rendering(self):
        for key, value in (("url", "javascript:alert(1)"), ("url", "data:text/html,evil")):
            data = sample()
            data["jobs"][0][key] = value
            with self.assertRaises(report.ValidationError):
                report.render_html(data)


class HtmlCliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.folder = Path(self.directory.name)
        self.source = self.folder / "input.json"
        self.source.write_text(json.dumps(sample()), encoding="utf-8")
        self.outputs = {"--output": self.folder / "report.md", "--csv": self.folder / "report.csv",
                        "--companies-csv": self.folder / "companies.csv", "--html": self.folder / "report.html"}

    def arguments(self, outputs=None, source=None):
        args = [str(source or self.source)]
        for flag, path in (outputs or self.outputs).items():
            args += [flag, str(path)]
        return args

    def test_cli_writes_html_with_existing_formats_and_output_alias(self):
        run = subprocess.run([sys.executable, str(SCRIPT), *self.arguments()], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        for flag, path in self.outputs.items():
            self.assertTrue(path.is_file(), flag)
            self.assertTrue(path.read_text(encoding="utf-8"))
        expected = report.render_html(sample())
        self.assertEqual(self.outputs["--html"].read_text(encoding="utf-8"), expected)
        before = {path: path.read_bytes() for path in self.outputs.values()}
        refusal = subprocess.run([sys.executable, str(SCRIPT), *self.arguments()], capture_output=True, text=True)
        self.assertEqual(refusal.returncode, 2)
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)
        alias_args = self.arguments({"--markdown": self.outputs["--output"], "--html": self.outputs["--html"]}) + ["--overwrite"]
        alias_run = subprocess.run([sys.executable, str(SCRIPT), *alias_args], capture_output=True, text=True)
        self.assertEqual(alias_run.returncode, 0, alias_run.stderr)

    def test_all_input_output_path_alias_pairs_refused(self):
        flags = ["input", *self.outputs]
        for first, second in itertools.combinations(flags, 2):
            with self.subTest(first=first, second=second):
                paths = {"input": self.source, **self.outputs}
                paths[second] = paths[first]
                for path in self.outputs.values():
                    path.write_text("preserve " + path.name, encoding="utf-8")
                before = {path: path.read_bytes() for path in {self.source, *self.outputs.values()}}
                args = self.arguments({key: value for key, value in paths.items() if key != "input"}, paths["input"]) + ["--overwrite"]
                with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(report.main(args), 2)
                for path, content in before.items():
                    self.assertEqual(path.read_bytes(), content)

    def test_all_input_output_hardlink_alias_pairs_refused(self):
        self.check_all_link_aliases("hardlink")

    def test_all_input_output_symlink_alias_pairs_refused(self):
        self.check_all_link_aliases("symlink")

    def check_all_link_aliases(self, kind):
        flags = ["input", *self.outputs]
        for index, (first, second) in enumerate(itertools.combinations(flags, 2)):
            with self.subTest(first=first, second=second):
                folder = self.folder / str(index)
                folder.mkdir()
                paths = {"input": folder / "input.json",
                         **{flag: folder / path.name for flag, path in self.outputs.items()}}
                paths["input"].write_bytes(self.source.read_bytes())
                for flag in self.outputs:
                    paths[flag].write_text("preserve " + flag, encoding="utf-8")
                paths[second].unlink()
                if kind == "hardlink":
                    os.link(paths[first], paths[second])
                else:
                    paths[second].symlink_to(paths[first])
                before = {path: path.read_bytes() for path in paths.values()}
                args = self.arguments({key: value for key, value in paths.items() if key != "input"}, paths["input"]) + ["--overwrite"]
                with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(report.main(args), 2)
                for path, content in before.items():
                    self.assertEqual(path.read_bytes(), content)

    def test_invalid_html_destination_does_not_write_other_outputs(self):
        for case in ("directory", "parent_is_file", "output_is_ancestor"):
            with self.subTest(case=case):
                outputs = dict(self.outputs)
                if case == "directory":
                    destination = self.folder / "directory"
                    destination.mkdir()
                    outputs["--html"] = destination
                elif case == "parent_is_file":
                    parent = self.folder / "file-parent"
                    parent.write_text("Keep parent", encoding="utf-8")
                    outputs["--html"] = parent / "report.html"
                else:
                    outputs["--html"] = outputs["--output"] / "report.html"
                with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(report.main(self.arguments(outputs) + ["--overwrite"]), 2)
                for path in self.outputs.values():
                    self.assertFalse(path.exists())
                self.assertEqual(json.loads(self.source.read_text()), sample())

    def test_render_failure_does_not_create_or_overwrite_any_report(self):
        for existing in (False, True):
            with self.subTest(existing=existing):
                if existing:
                    for path in self.outputs.values():
                        path.write_text("preserve " + path.name, encoding="utf-8")
                before = {path: path.read_bytes() if path.exists() else None for path in self.outputs.values()}
                with mock.patch.object(report, "render_html", side_effect=report.ValidationError("Synthetic render failure")):
                    with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(report.main(self.arguments() + ["--overwrite"]), 2)
                for path, content in before.items():
                    if content is None:
                        self.assertFalse(path.exists())
                    else:
                        self.assertEqual(path.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
