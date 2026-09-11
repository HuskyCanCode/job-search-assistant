import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location(
    "triage_jobs", Path(__file__).resolve().parents[1] / "scripts" / "triage_jobs.py")
triage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(triage)


class TriageTests(unittest.TestCase):
    def profile(self, **extra):
        return {"version": 1, "title_keywords": ["QA", "application support"],
                "function_keywords": ["testing", "troubleshooting"], **extra}

    def job(self, **extra):
        return {"title": "QA Analyst", "description": "Test applications.",
                "workplace": "OnSite", "employment_type": "FullTime",
                "locations": [{"name": "Boston", "country": "USA"}], **extra}

    def test_short_keyword_does_not_match_inside_word_or_language_name(self):
        self.assertEqual(triage.matches("equal tools: c++ c# sql", ["qa", "c", "c++", "sql"]), ["c++", "sql"])

    def test_boilerplate_single_keyword_stays_reviewable_but_not_promoted(self):
        result = triage.triage_job(self.job(title="Account Executive", description="We support customers."),
                                   self.profile(title_keywords=["support"], function_keywords=["support"]))
        self.assertEqual(result["priority"], "review")

    def test_function_synonyms_can_surface_adjacent_role(self):
        result = triage.triage_job(self.job(title="Product Specialist", description="Testing and troubleshooting."), self.profile())
        self.assertEqual(result["priority"], "review_first")
        self.assertFalse(any("score" in key for key in result))

    def test_no_overlap_is_not_rejection(self):
        result = triage.triage_job(self.job(title="Customer Engineer", description="Resolve incidents."), self.profile())
        self.assertEqual(result["priority"], "review")

    def test_malformed_text_stays_unknown_without_guessing_content(self):
        result = triage.triage_job(self.job(title=["QA"], description={"testing": True}), self.profile())
        self.assertEqual(result["priority"], "review")
        self.assertIn("Job title unavailable", result["unknowns"])
        self.assertIn("Full description unavailable", result["unknowns"])

    def test_employment_exclusion_remains_unresolved_from_schedule_alone(self):
        profile = self.profile(excluded_employment_types=["contract"])
        for value in (None, "FullTime"):
            result = triage.triage_job(self.job(employment_type=value), profile)
            self.assertNotEqual(result["priority"], "conflict")
            self.assertTrue(any("Employment" in reason for reason in result["unknowns"]))
        result = triage.triage_job(self.job(employment_type="Contract"), profile)
        self.assertEqual(result["priority"], "conflict")
        result = triage.triage_job(self.job(employment_type="FullTime"),
                                   self.profile(excluded_employment_types=["parttime"]))
        self.assertFalse(any("Employment" in reason for reason in result["unknowns"]))

    def test_secondary_allowed_location_prevents_false_conflict(self):
        result = triage.triage_job(self.job(locations=[{"name": "Toronto", "country": "CAN"},
                                                      {"name": "Boston", "country": "US"}]),
                                   self.profile(allowed_countries=["US"]))
        self.assertNotEqual(result["priority"], "conflict")

    def test_unknown_secondary_country_keeps_candidate(self):
        result = triage.triage_job(self.job(locations=[{"name": "Toronto", "country": "CA"},
                                                      {"name": "Other office", "country": None}]),
                                   self.profile(allowed_countries=["US"]))
        self.assertNotEqual(result["priority"], "conflict")
        self.assertTrue(result["unknowns"])

    def test_explicit_onsite_country_conflict(self):
        result = triage.triage_job(self.job(locations=[{"name": "Toronto", "country": "CAN"}]),
                                   self.profile(allowed_countries=["US"]))
        self.assertEqual(result["priority"], "conflict")

    def test_remote_office_country_is_not_hiring_restriction(self):
        result = triage.triage_job(self.job(workplace="Remote", locations=[{"name": "Toronto", "country": "CA"}]),
                                   self.profile(allowed_countries=["US"]))
        self.assertNotEqual(result["priority"], "conflict")
        self.assertTrue(any("jurisdiction" in s for s in result["unknowns"]))

    def test_country_not_inferred_from_location_text(self):
        result = triage.triage_job(self.job(locations=[{"name": "Boston, USA", "country": None}]),
                                   self.profile(allowed_countries=["US"]))
        self.assertTrue(any("unknown" in s for s in result["unknowns"]))

    def test_invalid_country_codes_are_unknown_not_false_conflicts(self):
        for value in ("NY", "ZZ", "XYZ"):
            self.assertIsNone(triage.country(value))
            result = triage.triage_job(self.job(locations=[{"name": "Unknown office", "country": value}]),
                                       self.profile(allowed_countries=["US"]))
            self.assertNotEqual(result["priority"], "conflict")
            with self.assertRaises(ValueError):
                triage.validate_profile(self.profile(allowed_countries=[value]))

    def test_explicit_arrangement_and_excluded_title_conflicts(self):
        for profile, job in [(self.profile(workplace_types=["remote"]), self.job()),
                             (self.profile(excluded_title_phrases=["account executive"]), self.job(title="Senior Account Executive"))]:
            with self.subTest(profile=profile):
                self.assertEqual(triage.triage_job(job, profile)["priority"], "conflict")

    def test_missing_metadata_is_unknown_not_conflict(self):
        result = triage.triage_job(self.job(workplace=None, employment_type=None, locations=[]),
                                   self.profile(workplace_types=["onsite"], employment_types=["fulltime"], allowed_countries=["US"]))
        self.assertNotEqual(result["priority"], "conflict")
        self.assertGreaterEqual(len(result["unknowns"]), 3)

    def test_contract_can_be_fulltime(self):
        result = triage.triage_job(self.job(employment_type="Contract"), self.profile(employment_types=["fulltime"]))
        self.assertNotEqual(result["priority"], "conflict")
        explicit = triage.triage_job(self.job(employment_type="Contract"), self.profile(excluded_employment_types=["contract"]))
        self.assertEqual(explicit["priority"], "conflict")

    def test_parttime_is_confirmed_schedule_conflict(self):
        result = triage.triage_job(self.job(employment_type="PartTime"), self.profile(employment_types=["fulltime"]))
        self.assertEqual(result["priority"], "conflict")

    def test_seniority_preference_never_becomes_hard_exclusion(self):
        result = triage.triage_job(self.job(level="Senior"), self.profile(preferred_levels=["junior"]))
        self.assertNotEqual(result["priority"], "conflict")

    def test_strict_profile_and_no_profile_mutation(self):
        profile = self.profile(title_keywords=[" QA ", "qa"])
        original = repr(profile)
        self.assertEqual(triage.validate_profile(profile)["title_keywords"], ["qa"])
        self.assertEqual(repr(profile), original)
        invalid = [{"version": True}, {"version": 1, "resume": "private"},
                   {"version": 1, "title_keywords": "QA"},
                   {"version": 1, "workplace_types": ["anywhere"]},
                   {"version": 1, "employment_types": ["contract"], "excluded_employment_types": ["contract"]}]
        for item in invalid:
            with self.subTest(item=item), self.assertRaises(ValueError):
                triage.validate_profile(item)


if __name__ == "__main__":
    unittest.main()
