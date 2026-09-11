"""Local discovery triage, not resume fit, eligibility proof, or hiring odds.

Only explicit conflicting metadata produces a conflict. Missing metadata and
weak keyword overlap remain reviewable; the host verifies duties and criteria.
This module makes no requests and writes no candidate data.
"""

import re
import unicodedata


PROFILE_FIELDS = {
    "version", "title_keywords", "function_keywords", "preferred_levels",
    "excluded_title_phrases", "allowed_countries", "workplace_types",
    "employment_types", "excluded_employment_types",
}
WORKPLACES = {"onsite", "hybrid", "remote"}
EMPLOYMENT = {"fulltime", "parttime", "contract", "temporary", "intern"}
# Explicit country/area codes; location names are never geocoded by this helper.
# Reference: https://unstats.un.org/unsd/methodology/m49/overview/
COUNTRY_CODES = set("""
AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM
BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX
CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG
GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR
IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV
LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE
NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO
RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF
TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF
WS YE YT ZA ZM ZW
""".split())
COUNTRY_ALIASES = {
    "USA": "US", "UNITED STATES": "US", "UNITED STATES OF AMERICA": "US",
    "CAN": "CA", "CANADA": "CA", "GBR": "GB", "UK": "GB",
    "UNITED KINGDOM": "GB", "AUS": "AU", "NZL": "NZ", "IRL": "IE",
    "DEU": "DE", "FRA": "FR", "ESP": "ES", "ITA": "IT", "NLD": "NL",
    "IND": "IN", "SGP": "SG", "JPN": "JP", "MEX": "MX", "BRA": "BR",
}


def clean(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def country(value):
    """Normalize explicit provider country data; never infer it from a city."""
    if not isinstance(value, str):
        return None
    value = value.strip().upper()
    value = COUNTRY_ALIASES.get(value, value)
    return value if value in COUNTRY_CODES else None


def workplace(value):
    if not isinstance(value, str):
        return None
    key = re.sub(r"[\s_-]", "", value.casefold())
    return key if key in WORKPLACES else None


def employment(value):
    if not isinstance(value, str):
        return None
    key = re.sub(r"[\s_-]", "", value.casefold())
    key = {"internship": "intern", "temp": "temporary"}.get(key, key)
    return key if key in EMPLOYMENT else None


def validate_profile(profile):
    if not isinstance(profile, dict) or set(profile) - PROFILE_FIELDS:
        raise ValueError("Profile must be an object using only documented triage fields")
    if type(profile.get("version")) is not int or profile["version"] != 1:
        raise ValueError("Profile version must be 1")
    normalized = {"version": 1}
    for field in sorted(PROFILE_FIELDS - {"version"}):
        values = profile.get(field, [])
        if (not isinstance(values, list) or len(values) > 50
                or any(not isinstance(v, str) or not v.strip() or len(v) > 120
                       or any(ord(c) < 32 for c in v) for v in values)):
            raise ValueError(f"{field} must be a list of up to 50 short nonempty strings")
        result = []
        for value in values:
            if field == "allowed_countries":
                item = country(value)
                if item is None:
                    raise ValueError("Use explicit two-letter country codes in allowed_countries")
            elif field == "workplace_types":
                item = workplace(value)
                if item is None:
                    raise ValueError("workplace_types must use onsite, hybrid, or remote")
            elif field in ("employment_types", "excluded_employment_types"):
                item = employment(value)
                if item is None:
                    raise ValueError("Use fulltime, parttime, contract, temporary, or intern")
            else:
                item = clean(value)
            if item not in result:
                result.append(item)
        normalized[field] = result
    if set(normalized["employment_types"]) & set(normalized["excluded_employment_types"]):
        raise ValueError("Employment type cannot be both requested and excluded")
    return normalized


def matches(text, terms):
    # Keep short terms such as QA, C++, C#, and SQL from matching inside words.
    return [term for term in terms
            if re.search(r"(?<![\w+#])" + re.escape(term) + r"(?![\w+#])", text)]


def triage_job(job, profile):
    profile = validate_profile(profile)
    if not isinstance(job, dict):
        raise ValueError("Job must be a normalized discovery object")
    reasons, unknowns, conflicts = [], [], []
    title = clean(job["title"]) if isinstance(job.get("title"), str) else ""
    description = clean(job["description"]) if isinstance(job.get("description"), str) else ""
    if not title:
        unknowns.append("Job title unavailable")
    title_hits = matches(title, profile["title_keywords"])
    function_hits = matches(description, profile["function_keywords"])
    if title_hits:
        reasons.append("Title signals: " + ", ".join(title_hits))
    if function_hits:
        reasons.append("Description signals to verify: " + ", ".join(function_hits))
    if not title_hits and len(function_hits) < 2:
        unknowns.append("Role relevance needs review; wording alone does not establish duties")
    if not description:
        unknowns.append("Full description unavailable")
    excluded = matches(title, profile["excluded_title_phrases"])
    if excluded:
        conflicts.append("Title matches an explicit user exclusion: " + ", ".join(excluded))

    arrangement = workplace(job.get("workplace"))
    wanted_workplace = profile["workplace_types"]
    if wanted_workplace:
        if arrangement is None:
            unknowns.append("Work arrangement not established")
        elif arrangement not in wanted_workplace:
            conflicts.append("Stated work arrangement conflicts with the requested arrangement")

    wanted_countries = set(profile["allowed_countries"])
    if wanted_countries:
        locations = job.get("locations")
        countries = [country(item.get("country")) if isinstance(item, dict) else None
                     for item in locations] if isinstance(locations, list) else []
        if arrangement not in ("onsite", "hybrid"):
            unknowns.append("Hiring jurisdiction needs verification; office country is not eligibility")
        elif any(item in wanted_countries for item in countries):
            reasons.append("At least one stated office country matches; verify the specific location")
        elif countries and all(item is not None for item in countries):
            conflicts.append("All stated office countries fall outside the requested countries")
        else:
            unknowns.append("One or more office countries are unknown; retain for location review")

    commitment = employment(job.get("employment_type"))
    wanted_employment = profile["employment_types"]
    excluded_employment = profile["excluded_employment_types"]
    if commitment and commitment in excluded_employment:
        conflicts.append("Stated employment type matches an explicit user exclusion")
    elif excluded_employment and commitment is not None:
        if any({commitment, excluded} != {"fulltime", "parttime"}
               for excluded in excluded_employment):
            unknowns.append("Employment exclusions need verification; one label does not establish all contract terms")
    if commitment is None and (wanted_employment or excluded_employment):
        unknowns.append("Employment type not established")
    if wanted_employment and commitment is not None:
        if commitment in wanted_employment:
            reasons.append("Stated employment type matches the requested label")
        elif (set(wanted_employment) <= {"fulltime", "parttime"}
              and commitment in {"fulltime", "parttime"}):
            conflicts.append("Stated full-time/part-time schedule conflicts with the request")
        else:
            # Contract/temporary/intern work can also be full-time or part-time.
            unknowns.append("Employment labels differ; verify duration, schedule and contract terms")

    if profile["preferred_levels"]:
        level = job.get("level")
        if isinstance(level, str) and level.strip():
            if matches(clean(level), profile["preferred_levels"]):
                reasons.append("Structured level matches a preference; verify responsibility scope")
            else:
                unknowns.append("Structured level differs from preference; verify responsibility scope")
        else:
            unknowns.append("Seniority requires review of responsibility scope")
    priority = "conflict" if conflicts else "review_first" if title_hits or len(function_hits) >= 2 else "review"
    return {"priority": priority, "reasons": conflicts + reasons, "unknowns": unknowns}
