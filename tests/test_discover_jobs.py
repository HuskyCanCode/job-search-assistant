"""Network-free behavior tests for public-board discovery."""

import importlib.util
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from urllib.request import Request
from urllib.parse import parse_qs, urlsplit

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
    def test_lever_multi_location_country_and_level_are_observed_not_inferred(self):
        row = lever(country="US", categories={"location": "New York", "allLocations": [
            "New York", "London", "New York", "London"], "level": "Entry", "commitment": "Full-time",
            "custom": {"private": "not needed"}})
        result = d.discover([{"provider": "lever", "board": "acme"}], fetcher=lambda *_: [row])
        job = result["jobs"][0]
        self.assertEqual(job["location"], "New York")
        self.assertEqual(job["locations"], [{"name": "New York", "country": "US"},
                                             {"name": "London", "country": None}])
        self.assertEqual(job["level"], "Entry")
        self.assertEqual(job["employment_type"], "Full-time")
        self.assertNotIn("custom", job["observed_metadata"]["categories"])
        row["categories"]["allLocations"].append("Elsewhere")
        self.assertNotIn("Elsewhere", job["observed_metadata"]["categories"]["allLocations"])

    def test_ashby_location_addresses_preserve_each_country_and_unknowns(self):
        row = {"id": "one", "title": "Support Engineer", "jobUrl": "https://jobs.ashbyhq.com/acme/one",
               "location": "London", "workplaceType": "OnSite", "publishedAt": "2026-09-01T00:00:00Z",
               "address": {"postalAddress": {"addressCountry": "GB", "addressLocality": "London"}},
               "secondaryLocations": [
                   {"location": "Austin", "address": {"addressCountry": "US", "addressRegion": "Texas"}},
                   {"location": "Austin", "address": {"addressCountry": "US"}},
                   {"location": "Tokyo", "address": {}},
                   {"location": "No inferred country", "country": "US"}]}
        result = d.discover([{"provider": "ashby", "board": "acme"}], fetcher=lambda *_: {"jobs": [row]},
                            profile={"version": 1, "title_keywords": ["support"], "allowed_countries": ["US"]})
        job = result["jobs"][0]
        self.assertEqual(job["location"], "London")
        self.assertEqual(job["locations"], [{"name": "London", "country": "GB"},
            {"name": "Austin", "country": "US"}, {"name": "Tokyo", "country": None},
            {"name": "No inferred country", "country": None}])
        self.assertEqual(job["published_at"], row["publishedAt"])
        self.assertIsNone(job["updated_at"])
        self.assertEqual(job["triage"]["priority"], "review_first")
        self.assertEqual(job["observed_metadata"]["address"], row["address"])

    def test_greenhouse_updates_and_offices_are_not_publication_or_offered_locations(self):
        row = gh(updated_at="2026-09-09T00:00:00Z", offices=[
            {"id": 1, "name": "Americas", "child_ids": [2]},
            {"id": 2, "name": "Austin", "parent_id": 1}], metadata=[{"private": "omit"}])
        job = d.discover([{"provider": "greenhouse", "board": "acme"}],
                         fetcher=lambda *_: {"jobs": [row]})["jobs"][0]
        self.assertIsNone(job["published_at"])
        self.assertEqual(job["updated_at"], row["updated_at"])
        self.assertEqual(job["locations"], [{"name": "New York", "country": None}])
        self.assertEqual(job["observed_metadata"]["offices"], row["offices"])
        self.assertNotIn("metadata", job["observed_metadata"])
        self.assertIsNone(job["level"])

    def test_profile_keeps_conflicts_and_unknown_relevance_for_audit(self):
        profile = {"version": 1, "title_keywords": ["support"], "excluded_title_phrases": ["senior"]}
        original = deepcopy(profile)
        result = d.discover([{"provider": "greenhouse", "board": "acme"}], profile=profile,
                            fetcher=lambda *_: {"jobs": [gh(1, "Support Engineer"),
                                gh(2, "Senior Support Engineer"), gh(3, "Technical Associate")]})
        self.assertEqual([job["triage"]["priority"] for job in result["jobs"]],
                         ["review_first", "conflict", "review"])
        self.assertEqual(result["sources"][0]["count"], 3)
        self.assertEqual(profile, original)
        self.assertEqual(result["keywords"], [])

    def test_invalid_profile_or_combined_keywords_or_callback_never_fetches(self):
        fetcher = Mock()
        for options in ({"profile": []}, {"profile": {"version": 2}},
                        {"profile": {"version": 1, "title_keywords": "support"}},
                        {"profile": {"version": 1}, "keywords": ["support"]},
                        {"profile": {"version": 1}, "keywords": [""]},
                        {"on_board": "not a function"}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                d.discover([{"provider": "greenhouse", "board": "acme"}], fetcher=fetcher, **options)
        fetcher.assert_not_called()

    def test_duplicate_constraint_disagreement_stays_reviewable_in_either_order(self):
        profile = {"version": 1, "title_keywords": ["support"], "allowed_countries": ["US"]}
        for order in (("ca", "us"), ("us", "ca"), ("ca", "us", "ca-again")):
            with self.subTest(order=order):
                boards = [{"provider": "lever", "board": name} for name in order]

                def fetcher(url, _timeout):
                    name = urlsplit(url).path.rsplit("/", 1)[1]
                    is_us = name == "us"
                    return [lever(country="US" if is_us else "CA", workplaceType="onsite",
                                  hostedUrl=f"https://jobs.lever.co/{name}/1",
                                  categories={"location": "Austin" if is_us else "Toronto"})]

                with patch.object(d, "timestamp", return_value="2026-09-10T12:00:00+00:00"):
                    sequential = d.discover(boards, fetcher=fetcher, profile=profile, workers=1)
                    parallel = d.discover(boards, fetcher=fetcher, profile=profile, workers=3)
                self.assertEqual(parallel, sequential)
                self.assertEqual(len(parallel["jobs"]), 1)
                job = parallel["jobs"][0]
                self.assertEqual(job["company_board"], order[0])
                self.assertEqual(job["locations"][0]["country"], order[0].upper())
                self.assertEqual(job["triage"]["priority"], "review")
                self.assertEqual(sum("Duplicate source records disagree" in item
                                     for item in job["triage"]["unknowns"]), 1)
                self.assertEqual([origin["board"] for origin in job["discovered_via"]], list(order))
                self.assertEqual([source["count"] for source in parallel["sources"]], [1] + [0] * (len(order) - 1))

    def test_completed_board_events_unlock_a_slow_first_board_and_are_isolated(self):
        slow_released = threading.Event()
        events = []
        calling_thread = threading.get_ident()
        boards = [{"provider": "greenhouse", "board": "slow"},
                  {"provider": "greenhouse", "board": "fast"}]

        def fetcher(url, _timeout):
            if "/slow/" in url:
                if not slow_released.wait(5):
                    raise AssertionError("Fast board was not emitted while first board was still running")
                return {"jobs": [gh(1, "Support original")]}
            return {"jobs": [gh(1, "Support duplicate"), gh(2, "Support second")]}

        def on_board(event):
            self.assertEqual(threading.get_ident(), calling_thread)
            events.append(deepcopy(event))
            self.assertTrue(event["provisional"])
            self.assertNotIn("count", event["source"])
            self.assertGreaterEqual(event["elapsed_seconds"], 0)
            self.assertTrue(all(job["verification"] == "needs_description_and_application_check"
                                for job in event["jobs"]))
            event["jobs"][0]["title"] = "MUTATED CALLBACK COPY"
            event["jobs"][0]["discovered_via"][0]["board"] = "changed"
            event["jobs"][0]["triage"]["reasons"].append("mutated")
            event["source"]["errors"].append("mutated")
            if event["source"]["board"] == "fast":
                slow_released.set()

        try:
            result = d.discover(boards, fetcher=fetcher, workers=2,
                                profile={"version": 1, "title_keywords": ["support"]}, on_board=on_board)
        finally:
            slow_released.set()
        self.assertEqual([event["board_index"] for event in events], [1, 0])
        self.assertEqual([event["candidate_count"] for event in events], [2, 1])
        self.assertEqual([job["title"] for job in result["jobs"]], ["Support original", "Support second"])
        self.assertEqual([source["count"] for source in result["sources"]], [1, 1])
        self.assertEqual([origin["board"] for origin in result["jobs"][0]["discovered_via"]], ["slow", "fast"])
        self.assertNotIn("mutated", json.dumps(result))

    def test_events_do_not_change_final_output_and_are_bounded_to_collected_boards(self):
        boards = [{"provider": "greenhouse", "board": "first"},
                  {"provider": "greenhouse", "board": "second"},
                  {"provider": "greenhouse", "board": "first"},
                  {"provider": "linkedin", "board": "excluded"}]
        events = []
        fetcher = lambda *_: {"jobs": [gh(), gh(2, "No keyword", content="None")]}
        with patch.object(d, "timestamp", return_value="2026-09-10T12:00:00+00:00"):
            baseline = d.discover(boards, ["react"], fetcher=fetcher, workers=1)
            streamed = d.discover(boards, ["react"], fetcher=fetcher, workers=2, on_board=events.append)
        self.assertEqual(streamed, baseline)
        self.assertEqual(len(events), 2)
        self.assertEqual(sorted(event["board_index"] for event in events), [0, 1])
        self.assertTrue(all(event["candidate_count"] == 1 for event in events))
        self.assertTrue(all(event["jobs"][0]["title"] == "React Developer" for event in events))

    def test_blocked_board_emits_empty_provisional_event_without_retry(self):
        events = []
        fetcher = Mock(side_effect=HTTPError("https://api.lever.co", 403, "blocked", {}, None))
        result = d.discover([{"provider": "lever", "board": "acme"}], fetcher=fetcher, on_board=events.append)
        self.assertEqual(fetcher.call_count, 1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["jobs"], [])
        self.assertEqual(events[0]["source"]["status"], "blocked")
        self.assertEqual(result["sources"][0]["count"], 0)

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
        def fetcher(url, _timeout):
            return {"jobs": {"acme": [first, first], "another": [second], "partner": [third]}[
                urlsplit(url).path.split("/")[-2] if "greenhouse" in url else "partner"]}
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
                            {"provider": "lever", "board": "other"}], fetcher=fetcher, workers=1)
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
                            {"provider": "ashby", "board": "other"}], fetcher=fetcher, workers=1)
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

    def test_board_requests_overlap_without_exceeding_worker_bound(self):
        # A barrier requires real simultaneous requests; no elapsed-time threshold.
        for workers in (1, 2, 4, 8):
            with self.subTest(workers=workers):
                barrier = threading.Barrier(workers, timeout=5)
                lock = threading.Lock()
                active = peak = 0
                calls = []

                def fetcher(url, _timeout):
                    nonlocal active, peak
                    with lock:
                        active += 1
                        peak = max(peak, active)
                        calls.append(url)
                    try:
                        barrier.wait()
                        return {"jobs": []}
                    finally:
                        with lock:
                            active -= 1

                boards = [{"provider": "greenhouse", "board": f"board{i}"}
                          for i in range(workers * 2)]
                # Omitting the option exercises the default of four workers.
                options = {} if workers == 4 else {"workers": workers}
                result = d.discover(boards + [boards[0], None], fetcher=fetcher, **options)
                self.assertEqual(peak, workers)
                self.assertEqual(len(calls), len(boards))
                self.assertEqual(len(set(calls)), len(boards))
                self.assertEqual([source["status"] for source in result["sources"]],
                                 ["searched"] * len(boards) + ["limited", "blocked"])

    def test_parallel_completion_order_does_not_change_duplicate_winners(self):
        boards = [{"provider": "greenhouse", "board": "first"},
                  {"provider": "greenhouse", "board": "second"},
                  {"provider": "ashby", "board": "partner"}]
        first = gh(title="React original")
        second = gh(title="Different duplicate", absolute_url="https://example.com/alternate/1")
        third = {"id": "partner-id", "title": "Another duplicate", "isListed": True,
                 "jobUrl": first["absolute_url"] + "?utm_source=partner"}
        payloads = {"first": {"jobs": [first, gh(2, "Unrelated", content="No match")]},
                    "second": {"jobs": [second, gh(3, "React later")]},
                    "partner": {"jobs": [third]}}
        completed = {name: threading.Event() for name in payloads}
        order = []

        def fetcher(url, _timeout, reverse=False):
            token = urlsplit(url).path.split("/")[-2] if "greenhouse" in url else "partner"
            dependency = {"first": "second", "second": "partner"}.get(token)
            if reverse and dependency:
                if not completed[dependency].wait(5):
                    raise AssertionError("Independent boards did not overlap")
            order.append(token)
            completed[token].set()
            return payloads[token]

        with patch.object(d, "timestamp", return_value="2026-09-10T12:00:00+00:00"):
            sequential = d.discover(boards, ["react"], fetcher=fetcher, workers=1)
            order.clear()
            for event in completed.values():
                event.clear()
            parallel = d.discover(boards, ["react"],
                                  fetcher=lambda *args: fetcher(*args, reverse=True), workers=3)
        self.assertEqual(order, ["partner", "second", "first"])
        self.assertEqual(parallel, sequential)
        self.assertEqual([job["title"] for job in parallel["jobs"]], ["React original", "React later"])
        self.assertEqual([source["count"] for source in parallel["sources"]], [1, 1, 0])
        self.assertEqual([origin["board"] for origin in parallel["jobs"][0]["discovered_via"]],
                         ["first", "second", "partner"])

    def test_parallel_errors_are_isolated_and_lever_pages_remain_sequential(self):
        boards = [{"provider": "greenhouse", "board": "healthy"},
                  {"provider": "lever", "board": "partial"},
                  {"provider": "ashby", "board": "malformed"},
                  {"provider": "greenhouse", "board": "rate-limited"}]
        page_zero_finished = threading.Event()
        calls = []
        lock = threading.Lock()

        def fetcher(url, _timeout):
            with lock:
                calls.append(url)
            if "partial" in url:
                page = int(parse_qs(urlsplit(url).query)["skip"][0])
                if page == 0:
                    page_zero_finished.set()
                    return [lever(i) for i in range(d.PAGE_SIZE)]
                self.assertTrue(page_zero_finished.is_set())
                self.assertEqual(page, d.PAGE_SIZE)
                raise URLError("offline")
            if "rate-limited" in url:
                raise HTTPError(url, 429, "rate", {}, None)
            if "malformed" in url:
                return {"not-jobs": []}
            return {"jobs": [gh()]}

        result = d.discover(boards, fetcher=fetcher)
        self.assertEqual(len(result["jobs"]), d.PAGE_SIZE + 1)
        self.assertEqual([source["status"] for source in result["sources"]],
                         ["searched", "limited", "blocked", "blocked"])
        self.assertEqual([source["count"] for source in result["sources"]], [1, d.PAGE_SIZE, 0, 0])
        self.assertEqual([source["fetched_count"] for source in result["sources"]],
                         [1, d.PAGE_SIZE, 0, 0])
        self.assertIn("HTTP 429", result["sources"][3]["errors"][0])
        self.assertEqual(len(calls), 5)  # No retries after any failure.

    def test_lever_full_pages_are_sequential_within_parallel_boards(self):
        barrier = threading.Barrier(2, timeout=5)
        lock = threading.Lock()
        active_boards = set()
        offsets = {"one": [], "two": []}

        def fetcher(url, _timeout):
            parsed = urlsplit(url)
            token = parsed.path.rsplit("/", 1)[1]
            offset = int(parse_qs(parsed.query)["skip"][0])
            with lock:
                self.assertNotIn(token, active_boards)
                active_boards.add(token)
                offsets[token].append(offset)
            try:
                barrier.wait()
                # Different provider IDs preserve both boards' records.
                return [lever(f"{token}-{i}") for i in range(offset, offset + (d.PAGE_SIZE if offset == 0 else 1))]
            finally:
                with lock:
                    active_boards.remove(token)

        result = d.discover([{"provider": "lever", "board": token} for token in offsets],
                            fetcher=fetcher, workers=2)
        self.assertEqual(offsets, {"one": [0, d.PAGE_SIZE], "two": [0, d.PAGE_SIZE]})
        self.assertEqual(len(result["jobs"]), (d.PAGE_SIZE + 1) * 2)
        self.assertTrue(all(source["status"] == "searched" for source in result["sources"]))

    def test_sequential_mode_preserves_call_order_and_positional_fetcher(self):
        calls = []

        def fetcher(url, timeout):
            calls.append((url, timeout, threading.get_ident()))
            if "lever" in url:
                offset = int(parse_qs(urlsplit(url).query)["skip"][0])
                return [lever(i) for i in range(d.PAGE_SIZE)] if offset == 0 else []
            return {"jobs": [gh()]}

        boards = [{"provider": "lever", "board": "first"},
                  {"provider": "greenhouse", "board": "second"}]
        result = d.discover(boards, (), 7, 3, fetcher, workers=1)
        self.assertEqual([url for url, _, _ in calls],
                         [d.endpoint(d.validate_board(boards[0]), page) for page in (0, 1)] +
                         [d.endpoint(d.validate_board(boards[1]))])
        self.assertTrue(all(timeout == 7 and thread == threading.get_ident()
                            for _, timeout, thread in calls))
        self.assertEqual([source["count"] for source in result["sources"]], [d.PAGE_SIZE, 1])

    def test_invalid_workers_do_not_fetch(self):
        fetcher = Mock()
        for workers in (0, 9, -1, True, False, 1.5, "4", None):
            with self.subTest(workers=workers), self.assertRaises(ValueError):
                d.discover([{"provider": "greenhouse", "board": "acme"}],
                           fetcher=fetcher, workers=workers)
        fetcher.assert_not_called()

    def test_cli_workers_forwarded_and_invalid_range_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            boards, output = Path(tmp) / "boards.json", Path(tmp) / "output.json"
            boards.write_text('[{"provider":"greenhouse","board":"acme"}]')
            args = ["--boards", str(boards), "--output", str(output)]
            with patch.object(d, "discover", wraps=d.discover) as discover, \
                    patch.object(d, "fetch_json", return_value={"jobs": []}), \
                    patch("sys.stdout", io.StringIO()), patch("sys.stderr", io.StringIO()):
                self.assertEqual(d.main(args + ["--workers", "2"]), 0)
                self.assertEqual(discover.call_args.kwargs["workers"], 2)
                output.unlink()
                self.assertEqual(d.main(args + ["--workers", "9"]), 2)
                self.assertFalse(output.exists())

    def test_cli_events_are_flushed_before_the_final_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            boards, output = Path(tmp) / "boards.json", Path(tmp) / "output.json"
            events, profile = Path(tmp) / "events.ndjson", Path(tmp) / "profile.json"
            boards.write_text(json.dumps([{"provider": "greenhouse", "board": name} for name in ("one", "two")]))
            profile.write_text(json.dumps({"version": 1, "title_keywords": ["react"]}))
            observed = []

            def fetcher(url, _timeout):
                self.assertFalse(output.exists())
                if "/two/" in url:
                    # The first line is complete and visible without closing the stream.
                    observed.extend(json.loads(line) for line in events.read_text().splitlines())
                    self.assertEqual(len(observed), 1)
                    self.assertEqual(observed[0]["source"]["board"], "one")
                return {"jobs": [gh(1 if "/one/" in url else 2)]}

            with patch.object(d, "fetch_json", side_effect=fetcher), patch("sys.stdout", io.StringIO()):
                self.assertEqual(d.main(["--boards", str(boards), "--output", str(output),
                                         "--events", str(events), "--profile", str(profile), "--workers", "1"]), 0)
            lines = [json.loads(line) for line in events.read_text().splitlines()]
            self.assertEqual([line["board_index"] for line in lines], [0, 1])
            self.assertTrue(all(line["jobs"][0]["triage"]["priority"] == "review_first" for line in lines))
            self.assertEqual(len(json.loads(output.read_text())["jobs"]), 2)
            self.assertEqual(json.loads(profile.read_text()), {"version": 1, "title_keywords": ["react"]})

    def test_cli_guards_every_input_and_output_alias_even_with_overwrite(self):
        pairs = (("boards", "output"), ("boards", "events"), ("profile", "output"),
                 ("profile", "events"), ("output", "events"), ("boards", "profile"))
        for first, second in pairs:
            for alias in ("same", "symlink", "hardlink"):
                with self.subTest(pair=(first, second), alias=alias), tempfile.TemporaryDirectory() as tmp:
                    paths = {name: Path(tmp) / f"{name}.json" for name in ("boards", "profile", "output", "events")}
                    paths["boards"].write_text('[{"provider":"lever","board":"acme"}]')
                    paths["profile"].write_text('{"version":1}')
                    if not paths[first].exists():
                        paths[first].write_text("keep existing destination")
                    original = paths[first].read_text()
                    if paths[second].exists():
                        paths[second].unlink()
                    if alias == "same":
                        paths[second] = paths[first]
                    elif alias == "symlink":
                        paths[second].symlink_to(paths[first])
                    else:
                        paths[second].hardlink_to(paths[first])
                    args = [arg for name, path in paths.items() for arg in (f"--{name}", str(path))]
                    with patch.object(d, "fetch_json") as fetcher, patch("sys.stderr", io.StringIO()):
                        self.assertEqual(d.main(args + ["--overwrite"]), 2)
                        fetcher.assert_not_called()
                    self.assertEqual(paths[first].read_text(), original)

    def test_cli_nonexistent_output_alias_is_rejected_before_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            boards, output = Path(tmp) / "boards.json", Path(tmp) / "new.json"
            boards.write_text('[{"provider":"lever","board":"acme"}]')
            with patch.object(d, "fetch_json") as fetcher, patch("sys.stderr", io.StringIO()):
                self.assertEqual(d.main(["--boards", str(boards), "--output", str(output),
                                         "--events", str(output), "--overwrite"]), 2)
                fetcher.assert_not_called()
            self.assertFalse(output.exists())

    def test_cli_invalid_profile_and_options_do_not_touch_events_or_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = {name: Path(tmp) / f"{name}.json" for name in ("boards", "profile", "output", "events")}
            paths["boards"].write_text('[{"provider":"lever","board":"acme"}]')
            paths["events"].write_text("keep previous events")
            args = [arg for name, path in paths.items() for arg in (f"--{name}", str(path))]
            cases = ((None, []), ({"version": 2}, []), ({"version": 1}, ["--keywords", "react"]),
                     ({"version": 1}, ["--workers", "9"]), ({"version": 1}, ["--max-pages", "0"]))
            for profile, extra in cases:
                with self.subTest(profile=profile, extra=extra):
                    paths["profile"].write_text(json.dumps(profile))
                    with patch.object(d, "fetch_json") as fetcher, patch("sys.stderr", io.StringIO()):
                        self.assertEqual(d.main(args + ["--overwrite"] + extra), 2)
                        fetcher.assert_not_called()
                    self.assertEqual(paths["events"].read_text(), "keep previous events")
                    self.assertFalse(paths["output"].exists())

    def test_cli_events_overwrite_guard_and_empty_event_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            boards, output, events = (Path(tmp) / name for name in ("boards.json", "output.json", "events.ndjson"))
            boards.write_text('[{"provider":"indeed","board":"excluded"}]')
            events.write_text("keep existing events")
            args = ["--boards", str(boards), "--output", str(output), "--events", str(events)]
            with patch.object(d, "fetch_json") as fetcher, patch("sys.stderr", io.StringIO()), \
                    patch("sys.stdout", io.StringIO()):
                self.assertEqual(d.main(args), 2)
                self.assertEqual(events.read_text(), "keep existing events")
                self.assertFalse(output.exists())
                self.assertEqual(d.main(args + ["--overwrite"]), 1)
                fetcher.assert_not_called()
            self.assertEqual(events.read_text(), "")
            self.assertEqual(json.loads(output.read_text())["sources"][0]["status"], "blocked")

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
