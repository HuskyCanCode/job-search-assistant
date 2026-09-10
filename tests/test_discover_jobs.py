"""Network-free behavior tests for public-board discovery."""

import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

SPEC = importlib.util.spec_from_file_location(
    "discover_jobs", Path(__file__).resolve().parents[1] / "scripts" / "discover_jobs.py")
d = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d)


def gh(job_id=1, title="React Developer", **extra):
    return {"id": job_id, "title": title, "absolute_url": f"https://boards.greenhouse.io/acme/jobs/{job_id}",
            "location": {"name": "New York"}, "content": "&lt;p&gt;Build React apps&lt;/p&gt;", **extra}


def lever(job_id=1, **extra):
    return {"id": str(job_id), "text": "Support Engineer", "hostedUrl": f"https://jobs.lever.co/acme/{job_id}",
            "categories": {"location": "Remote", "commitment": "Full-time"},
            "descriptionPlain": "Troubleshoot APIs.", **extra}


class DiscoveryTests(unittest.TestCase):
    def test_greenhouse_normalization_and_unknowns(self):
        result = d.discover([{"provider": "greenhouse", "board": "acme"}],
                            fetcher=lambda *_: {"jobs": [gh()], "meta": {"total": 1}})
        job = result["jobs"][0]
        self.assertEqual(job["description"], "Build React apps")
        self.assertEqual(job["location"], "New York")
        self.assertIsNone(job["company"])
        self.assertIsNone(job["salary"])
        self.assertIsNone(job["workplace"])
        self.assertEqual(job["status"], "published_in_api")
        self.assertEqual(job["verification"], "needs_description_and_application_check")
        self.assertNotIn("fit_score", job)
        self.assertEqual(result["sources"][0]["status"], "searched")

    def test_lever_preserves_requirements_compensation_and_eu(self):
        fetcher = Mock(return_value=[lever(workplaceType="hybrid", salaryRange={
            "currency": "USD", "interval": "year", "min": 60000, "max": 80000},
            lists=[{"text": "Requirements", "content": "<ul><li>SQL</li><li>APIs</li></ul>"}],
            additional="<p>Training provided</p>")])
        result = d.discover([{"provider": "lever", "board": "acme", "region": "eu"}], fetcher=fetcher)
        job = result["jobs"][0]
        self.assertIn("SQL APIs", job["description"])
        self.assertIn("Training provided", job["description"])
        self.assertEqual(job["salary"]["min"], 60000)
        self.assertEqual(job["workplace"], "hybrid")
        self.assertIn("https://api.eu.lever.co/", fetcher.call_args.args[0])

    def test_ashby_omits_unlisted_and_uses_documented_fields(self):
        row = {"title": "Analyst", "jobUrl": "https://jobs.ashbyhq.com/acme/123",
               "location": "London", "isRemote": True, "isListed": True,
               "employmentType": "FullTime", "descriptionHtml": "<p>Analyze data</p>",
               "compensation": {"scrapeableCompensationSalarySummary": "£40K–£50K"}}
        fetcher = Mock(return_value={"jobs": [row, {**row, "isListed": False}]})
        result = d.discover([{"provider": "ashby", "board": "acme"}], fetcher=fetcher)
        self.assertEqual(len(result["jobs"]), 1)
        self.assertEqual(result["jobs"][0]["salary"], "£40K–£50K")
        self.assertEqual(result["jobs"][0]["workplace"], "Remote")
        self.assertIn("includeCompensation=true", fetcher.call_args.args[0])

    def test_duplicate_jobs_urls_and_boards_not_repeated(self):
        fetcher = Mock(return_value={"jobs": [gh(), gh(), gh(2,
            absolute_url="https://boards.greenhouse.io/acme/jobs/1?utm_source=search")]})
        result = d.discover([{"provider": "greenhouse", "board": "acme"}] * 2, fetcher=fetcher)
        self.assertEqual(len(result["jobs"]), 1)
        self.assertEqual(fetcher.call_count, 1)
        self.assertEqual(result["sources"][1]["status"], "limited")
        self.assertEqual(len(result["jobs"][0]["discovered_via"]), 2)

    def test_duplicate_ids_across_boards_and_urls_across_providers_keep_origins(self):
        first = gh()
        second = gh(absolute_url="https://boards.greenhouse.io/another/jobs/1")
        third = {"id": "different", "title": "React Developer", "isListed": True,
                 "jobUrl": first["absolute_url"] + "?utm_source=other-board"}
        fetcher = Mock(side_effect=[{"jobs": [first, first]}, {"jobs": [second]}, {"jobs": [third]}])
        result = d.discover([{"provider": "greenhouse", "board": "acme"},
                            {"provider": "greenhouse", "board": "another"},
                            {"provider": "ashby", "board": "partner"}], fetcher=fetcher)
        self.assertEqual(len(result["jobs"]), 1)
        job = result["jobs"][0]
        self.assertEqual(job["source_url"], first["absolute_url"])
        self.assertEqual([source["count"] for source in result["sources"]], [1, 0, 0])
        self.assertEqual([origin["board"] for origin in job["discovered_via"]], ["acme", "another", "partner"])
        self.assertTrue(all(set(origin) == {"provider", "board", "region", "api_url", "checked_at", "source_url"}
                            for origin in job["discovered_via"]))

    def test_local_keywords_are_case_insensitive_or_and_not_sent(self):
        fetcher = Mock(return_value={"jobs": [gh(), gh(2, "Analyst", content="Uses SQL"),
                                              gh(3, "Designer", content="Draws logos")]})
        result = d.discover([{"provider": "greenhouse", "board": "acme"}],
                            ["REACT", "sql"], fetcher=fetcher)
        self.assertEqual([job["title"] for job in result["jobs"]], ["React Developer", "Analyst"])
        self.assertNotIn("sql", fetcher.call_args.args[0])
        self.assertNotIn("REACT", fetcher.call_args.args[0])

    def test_partial_failure_keeps_success_and_reports_access_block(self):
        fetcher = Mock(side_effect=[{"jobs": [gh()]}, HTTPError("https://api.lever.co", 429, "rate", {}, None)])
        result = d.discover([{"provider": "greenhouse", "board": "acme"},
                            {"provider": "lever", "board": "other"}], fetcher=fetcher)
        self.assertEqual(len(result["jobs"]), 1)
        self.assertEqual(result["sources"][1]["status"], "blocked")
        self.assertIn("HTTP 429", result["sources"][1]["errors"][0])
        self.assertEqual(fetcher.call_count, 2)

    def test_partial_lever_page_failure_keeps_prior_results(self):
        fetcher = Mock(side_effect=[[lever(i) for i in range(d.PAGE_SIZE)], URLError("offline")])
        result = d.discover([{"provider": "lever", "board": "acme"}], fetcher=fetcher)
        self.assertEqual(len(result["jobs"]), d.PAGE_SIZE)
        self.assertEqual(result["sources"][0]["status"], "limited")
        self.assertIn("skip=100", fetcher.call_args.args[0])

    def test_lever_page_cap_and_repeated_page(self):
        rows = [lever(i) for i in range(d.PAGE_SIZE)]
        capped = d.discover([{"provider": "lever", "board": "acme"}], max_pages=1,
                            fetcher=lambda *_: rows)
        self.assertTrue(capped["sources"][0]["truncated"])
        repeated = d.discover([{"provider": "lever", "board": "acme"}], fetcher=lambda *_: rows)
        self.assertEqual(len(repeated["jobs"]), d.PAGE_SIZE)
        self.assertIn("Repeated page", repeated["sources"][0]["errors"][0])
        origins = repeated["jobs"][0]["discovered_via"]
        self.assertEqual(len(origins), 2)
        self.assertIn("skip=0&", origins[0]["api_url"])
        self.assertIn("skip=100&", origins[1]["api_url"])

    def test_greenhouse_inconsistent_total_is_limited(self):
        result = d.discover([{"provider": "greenhouse", "board": "acme"}],
                            fetcher=lambda *_: {"jobs": [gh()], "meta": {"total": 2}})
        self.assertTrue(result["sources"][0]["truncated"])

    def test_malformed_payload_rows_and_prospect_posts(self):
        fetcher = Mock(side_effect=[{"jobs": [gh(), None, {}, gh(2, internal_job_id=None)]}, {"no_jobs": []}])
        result = d.discover([{"provider": "greenhouse", "board": "acme"},
                            {"provider": "ashby", "board": "other"}], fetcher=fetcher)
        self.assertEqual(len(result["jobs"]), 1)
        self.assertEqual(result["sources"][0]["status"], "limited")
        self.assertEqual(result["sources"][1]["status"], "blocked")

    def test_invalid_tokens_providers_and_regions_never_fetch(self):
        invalid = [None, {"provider": "linkedin", "board": "acme"},
                   *[{"provider": "lever", "board": token} for token in
                     ("../private", "https://evil.test", "a?url=x", "a/b", "a%2fb", "@127.0.0.1", "")],
                   {"provider": "ashby", "board": "acme", "region": "eu"}]
        fetcher = Mock()
        result = d.discover(invalid, fetcher=fetcher)
        fetcher.assert_not_called()
        self.assertTrue(all(source["status"] == "blocked" for source in result["sources"]))

    def test_fetch_guard_never_opens_arbitrary_host_or_unsupported_path(self):
        with patch.object(d, "build_opener") as opener:
            for url in ("https://evil.test/jobs", "https://api.lever.co.evil.test/v0/postings/acme",
                        "https://user@api.lever.co/v0/postings/acme", "http://api.lever.co/v0/postings/acme",
                        "https://api.lever.co/private", "https://127.0.0.1/v0/postings/acme"):
                with self.subTest(url=url), self.assertRaises(ValueError):
                    d.fetch_json(url, 1)
            opener.assert_not_called()

    def test_redirects_refused_even_if_location_is_external(self):
        with self.assertRaises(HTTPError):
            d.NoRedirects().redirect_request(Request("https://api.lever.co/v0/postings/acme"),
                                            None, 302, "redirect", {}, "https://evil.test")

    def test_fetch_rejects_oversize_and_malformed_json(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        with patch.object(d, "build_opener") as opener:
            opener.return_value.open.return_value = response
            for content in (b"not JSON", b"x" * (d.MAX_BYTES + 1)):
                response.read.return_value = content
                with self.assertRaises(ValueError):
                    d.fetch_json("https://api.lever.co/v0/postings/acme", 1)

    def test_html_entities_script_text_and_unsafe_links(self):
        self.assertEqual(d.plain_html("&amp;lt;p&amp;gt;React &amp;amp; Rails&amp;lt;/p&amp;gt;"), "React & Rails")
        self.assertEqual(d.plain_html("<p>First</p><script>alert(1)</script><style>secret</style><p>Last</p>"),
                         "First Last")
        self.assertIsNone(d.valid_link("javascript:alert(1)"))
        self.assertIsNone(d.valid_link("https://user:password@example.com"))

    def test_links_reject_whitespace_credentials_invalid_hosts_and_ports(self):
        invalid = (None, " https://example.com/jobs", "https://example.com/jobs ",
                   "https://example.com/a b", "https://example.com/\\evil", "https://@example.com/jobs",
                   "https://:secret@example.com", "https://example.com:abc/jobs", "https://example.com:70000",
                   "https://example.com\n/jobs", "https://example%2ecom/jobs", "https://ex<ample.com/jobs",
                   "https://[invalid]/jobs")
        for url in invalid:
            with self.subTest(url=url):
                self.assertIsNone(d.valid_link(url))
        self.assertEqual(d.valid_link("https://example.com:443/a%20b"), "https://example.com:443/a%20b")

    def test_cli_existing_output_requires_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            boards, output = Path(tmp) / "boards.json", Path(tmp) / "output.json"
            boards.write_text('[{"provider":"lever","board":"acme"}]')
            output.write_text("keep this report")
            args = ["--boards", str(boards), "--output", str(output)]
            with patch.object(d, "fetch_json") as fetcher, patch("sys.stderr", io.StringIO()):
                self.assertEqual(d.main(args), 2)
                fetcher.assert_not_called()
            self.assertEqual(output.read_text(), "keep this report")
            with patch.object(d, "fetch_json", return_value=[]), patch("sys.stdout", io.StringIO()):
                self.assertEqual(d.main(args + ["--overwrite"]), 0)
            self.assertEqual(json.loads(output.read_text())["jobs"], [])

    def test_cli_alias_protection_and_partial_output_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            boards = Path(tmp) / "boards.json"
            output = Path(tmp) / "output.json"
            boards.write_text('[{"provider":"lever","board":"acme"}]')
            output.symlink_to(boards)
            with patch.object(d, "fetch_json") as fetcher, patch("sys.stderr", io.StringIO()):
                self.assertEqual(d.main(["--boards", str(boards), "--output", str(output)]), 2)
                self.assertEqual(d.main(["--boards", str(boards), "--output", str(output), "--overwrite"]), 2)
                fetcher.assert_not_called()
            output.unlink()
            with patch.object(d, "fetch_json", side_effect=URLError("offline")), patch("sys.stdout", io.StringIO()):
                self.assertEqual(d.main(["--boards", str(boards), "--output", str(output)]), 1)
            self.assertEqual(json.loads(output.read_text())["sources"][0]["status"], "blocked")
            self.assertIn("lever", boards.read_text())


if __name__ == "__main__":
    unittest.main()
