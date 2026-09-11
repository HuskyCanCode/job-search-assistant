import contextlib
from copy import deepcopy
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "search_state.py"
SPEC = importlib.util.spec_from_file_location("search_state", MODULE_PATH)
state_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(state_module)
NOW = datetime(2026, 9, 10, 18, tzinfo=timezone.utc)


def sample_state():
    return state_module.new_state("candidate", "run-1", ["development", "qa", "support"])


def attempt(name, family, employers=(), seconds=60, status="complete", hour=10):
    return {"id": name, "family": family, "route": "host_search",
            "query": "entry level software support United States", "elapsed_seconds": seconds,
            "status": status, "qualified_employer_ids": list(employers),
            "checked_at": f"2026-09-10T{hour:02}:00:00Z"}


def feedback(name="preference-1", family="qa", preference="avoid", scope="run", scope_id="run-1", hour=10):
    statements = {"avoid": "I would prefer fewer QA roles.", "prefer": "I prefer QA roles.",
                  "exclude": "Exclude QA roles from this search.", "neutral": "Clear my QA role preference."}
    return {"id": name, "source": "explicit_user", "statement": statements[preference],
            "dimension": "role", "family": family, "preference": preference,
            "scope": scope, "scope_id": scope_id, "checked_at": f"2026-09-10T{hour:02}:00:00Z"}


def employer():
    return {"employer_id": "example", "career_url": "https://example.com/careers",
            "board": {"provider": "greenhouse", "board": "example", "region": "global",
                      "observed_url": "https://job-boards.greenhouse.io/example", "observed": True},
            "provenance_url": "https://example.com/careers", "checked_at": "2026-09-10T10:00:00Z",
            "permission": {"policy_url": "https://example.com/terms",
                           "scope": "public_listings_and_private_report", "profile_id": "candidate",
                           "checked_at": "2026-09-10T10:00:00Z", "review_due_at": "2026-09-11T10:00:00Z",
                           "expires_at": "2026-10-10T10:00:00Z", "retention_covered": True,
                           "retention_basis_url": "https://example.com/terms"}}


class PlanningTests(unittest.TestCase):
    def test_initial_exploration_covers_all_families(self):
        plan = state_module.suggest(sample_state(), slots=6, now=NOW)
        self.assertEqual({item["family"]: item["slots"] for item in plan["allocations"]},
                         {"development": 2, "qa": 2, "support": 2})
        self.assertTrue(all(item["reason"] == "exploration" for item in plan["order"]))

    def test_new_employers_deduplicated_across_families(self):
        state = sample_state()
        state["attempts"] = [attempt("first", "development", ["a", "b"], hour=9),
                             attempt("second", "qa", ["a", "b", "c"], hour=10)]
        plan = state_module.suggest(state, now=NOW)
        metric = {item["family"]: item for item in plan["allocations"]}
        self.assertEqual(metric["development"]["marginal_employers_per_query"], 2)
        self.assertEqual(metric["qa"]["marginal_employers_per_query"], 1)
        self.assertIsNone(metric["support"]["marginal_employers_per_query"])

    def test_pending_is_not_completed_zero(self):
        state = sample_state()
        state["attempts"] = [attempt("pending", "qa", status="pending"),
                             attempt("finished", "support")]
        plan = state_module.suggest(state, now=NOW)
        metric = {item["family"]: item for item in plan["allocations"]}
        self.assertEqual(metric["qa"]["pending_attempts"], 1)
        self.assertIsNone(metric["qa"]["marginal_employers_per_query"])
        self.assertEqual(metric["support"]["marginal_employers_per_query"], 0)

    def test_pending_requires_completed_verification_before_ids(self):
        state = sample_state()
        state["attempts"] = [attempt("pending", "qa", ["a"], status="pending")]
        with self.assertRaises(ValueError):
            state_module.validate_state(state, NOW)

    def test_exploration_remains_when_one_family_dominates(self):
        state = sample_state()
        state["attempts"] = [attempt("best", "development", ["a", "b", "c"]),
                             attempt("zero", "qa"), attempt("zero2", "support")]
        plan = state_module.suggest(state, slots=8, exploration=0.25, now=NOW)
        self.assertGreaterEqual(sum(item["reason"] == "exploration" for item in plan["order"]), 2)
        self.assertGreater(len(set(item["family"] for item in plan["order"])), 1)

    def test_recent_zero_yield_does_not_keep_old_winner_dominant(self):
        state = sample_state()
        state["attempts"] = [attempt("old", "development", [f"old-{i}" for i in range(40)], hour=8),
                             attempt("dev1", "development", hour=9),
                             attempt("dev2", "development", hour=10),
                             attempt("dev3", "development", hour=11),
                             attempt("qa", "qa", ["new"], hour=12),
                             attempt("support", "support", hour=13)]
        plan = state_module.suggest(state, slots=4, exploration=0.25, recent=3, now=NOW)
        exploited = [item for item in plan["order"] if item["reason"] == "recent_verified_yield"]
        self.assertTrue(exploited)
        self.assertTrue(all(item["family"] == "qa" for item in exploited))

    def test_elapsed_time_affects_effort_not_fit(self):
        state = sample_state()
        state["attempts"] = [attempt("slow", "development", ["a"], seconds=600),
                             attempt("fast", "qa", ["b"], seconds=10), attempt("zero", "support")]
        plan = state_module.suggest(state, slots=4, now=NOW)
        self.assertEqual(plan["order"][-1]["family"], "qa")
        self.assertNotIn("fit_score", json.dumps(plan))

    def test_only_allowed_families_and_routes(self):
        for field, value in [("family", "secret-family"), ("route", "linkedin")]:
            with self.subTest(field=field):
                state = sample_state()
                item = attempt("a", "qa")
                item[field] = value
                state["attempts"] = [item]
                with self.assertRaises(ValueError):
                    state_module.validate_state(state, NOW)

    def test_pending_completion_preserves_immutable_completed_history(self):
        original = sample_state()
        pending = state_module.record_attempt(original, attempt("a", "qa", status="pending"), NOW)
        complete = state_module.record_attempt(pending, attempt("a", "qa", ["new"], hour=11), NOW)
        self.assertEqual(len(original["attempts"]), 0)
        self.assertEqual(len(complete["attempts"]), 1)
        self.assertEqual(complete["attempts"][0]["qualified_employer_ids"], ["new"])
        with self.assertRaises(ValueError):
            state_module.record_attempt(complete, attempt("a", "qa", ["other"], hour=12), NOW)


class RegistryFeedbackTests(unittest.TestCase):
    def test_registry_fresh_expired_and_review_due(self):
        state = sample_state()
        state["employers"] = [employer()]
        self.assertEqual(len(state_module.fresh_registry(state, NOW)), 1)
        for field in ("review_due_at", "expires_at"):
            with self.subTest(field=field):
                changed = deepcopy(state)
                changed["employers"][0]["permission"][field] = "2026-09-10T17:00:00Z"
                self.assertEqual(state_module.fresh_registry(changed, NOW), [])

    def test_registry_requires_retention_and_profile_scope(self):
        for field, value in [("retention_covered", False), ("profile_id", "other"), ("scope", "any_use")]:
            with self.subTest(field=field):
                state = sample_state()
                row = employer()
                row["permission"][field] = value
                state["employers"] = [row]
                with self.assertRaises(ValueError):
                    state_module.validate_state(state, NOW)

    def test_registry_rejects_guessed_mismatched_or_excluded_boards(self):
        for changes in [{"observed": False}, {"board": "guessed"}, {"provider": "linkedin"},
                        {"observed_url": "https://www.linkedin.com/jobs"}, {"region": "eu"}]:
            with self.subTest(changes=changes):
                state = sample_state()
                row = employer()
                row["board"].update(changes)
                state["employers"] = [row]
                with self.assertRaises(ValueError):
                    state_module.validate_state(state, NOW)

    def test_registry_does_not_downgrade_latest_check(self):
        state = state_module.record_employer(sample_state(), employer(), NOW)
        older = employer()
        older["checked_at"] = "2026-09-10T09:00:00Z"
        with self.assertRaises(ValueError):
            state_module.record_employer(state, older, NOW)

    def test_only_explicit_current_scope_feedback_applies(self):
        state = sample_state()
        state["feedback"] = [feedback("profile", scope="profile", scope_id="candidate"),
                             feedback("other-profile", "support", "exclude", "profile", "someone-else"),
                             feedback("old-run", "development", "exclude", "run", "old-run")]
        self.assertEqual([item["id"] for item in state_module.effective_feedback(state)], ["profile"])
        plan = state_module.suggest(state, now=NOW)
        self.assertEqual(len(plan["allocations"]), 3)  # Soft avoid is not a hard exclusion.
        state["feedback"][0]["source"] = "ignored_job"
        with self.assertRaises(ValueError):
            state_module.validate_state(state, NOW)

    def test_latest_explicit_contradiction_replaces_exclusion(self):
        state = sample_state()
        state["feedback"] = [feedback("a", preference="exclude", scope="profile", scope_id="candidate", hour=9),
                             feedback("b", preference="prefer", hour=10)]
        plan = state_module.suggest(state, now=NOW)
        self.assertEqual(plan["effective_feedback"][0]["preference"], "prefer")
        self.assertIn("qa", [item["family"] for item in plan["allocations"]])

    def test_only_explicit_exclusion_removes_family(self):
        state = sample_state()
        state["feedback"] = [feedback(preference="exclude")]
        plan = state_module.suggest(state, now=NOW)
        self.assertNotIn("qa", [item["family"] for item in plan["allocations"]])

    def test_unknown_sensitive_fields_and_content_rejected(self):
        for collection, value in [(None, {"resume": "private"}),
                                  ("attempts", {"description": "private"}),
                                  ("employers", {"api_key": "private"}),
                                  ("feedback", {"job_description": "private"})]:
            with self.subTest(collection=collection):
                state = sample_state()
                if collection is None:
                    state.update(value)
                else:
                    row = {"attempts": attempt("a", "qa"), "employers": employer(), "feedback": feedback()}[collection]
                    row.update(value)
                    state[collection] = [row]
                with self.assertRaises(ValueError):
                    state_module.validate_state(state, NOW)
        for text in ("resume@example.com", "site:linkedin.com developer", "password abc", "line1\nline2"):
            state = sample_state()
            row = attempt("a", "qa")
            row["query"] = text
            state["attempts"] = [row]
            with self.assertRaises(ValueError):
                state_module.validate_state(state, NOW)

    def test_url_secrets_and_future_checks_rejected(self):
        for url in ("https://example.com/terms?api_key=secret", "https://user:password@example.com/terms"):
            row = employer()
            row["permission"]["policy_url"] = url
            state = sample_state()
            state["employers"] = [row]
            with self.assertRaises(ValueError):
                state_module.validate_state(state, NOW)
        state = sample_state()
        state["attempts"] = [attempt("future", "qa", hour=19)]
        with self.assertRaises(ValueError):
            state_module.validate_state(state, NOW)


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        self.path = self.repo / "private" / "search-state.json"

    def test_atomic_create_and_guarded_update(self):
        state = sample_state()
        digest = state_module.save_state(state, self.path, repo_root=self.repo, now=NOW)
        loaded, actual = state_module.load_state(self.path, NOW)
        self.assertEqual(digest, actual)
        self.assertEqual(loaded, state)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(ValueError):
            state_module.save_state(state, self.path, repo_root=self.repo, now=NOW)
        state["run_id"] = "run-2"
        updated = state_module.save_state(state, self.path, expected_sha=digest, repo_root=self.repo, now=NOW)
        self.assertNotEqual(updated, digest)
        with self.assertRaises(ValueError):
            state_module.save_state(state, self.path, expected_sha=digest, repo_root=self.repo, now=NOW)
        self.assertEqual(state_module.load_state(self.path, NOW)[0]["run_id"], "run-2")

    def test_refuses_repo_public_output_but_allows_explicit_outside(self):
        with self.assertRaises(ValueError):
            state_module.save_state(sample_state(), self.repo / "state.json", repo_root=self.repo, now=NOW)
        state_module.save_state(sample_state(), Path(self.temporary.name) / "outside.json", repo_root=self.repo, now=NOW)

    def test_symlink_and_concurrent_write_refused(self):
        self.path.parent.mkdir()
        target = Path(self.temporary.name) / "important.json"
        target.write_text("preserve", encoding="utf-8")
        self.path.symlink_to(target)
        with self.assertRaises(ValueError):
            state_module.save_state(sample_state(), self.path, repo_root=self.repo, now=NOW)
        self.assertEqual(target.read_text(encoding="utf-8"), "preserve")
        self.path.unlink()
        lock = self.path.with_name(self.path.name + ".lock")
        lock.write_text("other writer", encoding="utf-8")
        with self.assertRaises(ValueError):
            state_module.save_state(sample_state(), self.path, repo_root=self.repo, now=NOW)
        self.assertEqual(lock.read_text(encoding="utf-8"), "other writer")

    def test_failed_atomic_replace_preserves_existing_state(self):
        digest = state_module.save_state(sample_state(), self.path, repo_root=self.repo, now=NOW)
        old = self.path.read_bytes()
        changed = sample_state()
        changed["run_id"] = "run-2"
        with mock.patch.object(state_module.os, "replace", side_effect=OSError("simulated disk failure")):
            with self.assertRaises(OSError):
                state_module.save_state(changed, self.path, digest, self.repo, NOW)
        self.assertEqual(self.path.read_bytes(), old)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_cli_round_trip_and_no_query_execution(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(state_module.main(["init", str(self.path), "--profile", "candidate",
                                                "--run", "run-1", "--families", "qa", "support"]), 0)
            self.assertEqual(state_module.main(["suggest", str(self.path), "--slots", "2"]), 0)
        self.assertIn('"exploration"', output.getvalue())
        self.assertTrue(self.path.exists())


if __name__ == "__main__":
    unittest.main()
