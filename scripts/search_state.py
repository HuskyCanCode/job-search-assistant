#!/usr/bin/env python3
"""Private, offline search-effort planning; Python 3.10+, standard library only.

Metadata and attestations are not permission or current-job verification. This
module never searches, fetches URLs, reads resumes, or changes resume-fit scores.
"""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit


ROUTES = {"host_search", "employer_site", "greenhouse", "lever", "ashby",
          "remoteok_feed", "usajobs_api"}
PROVIDERS = {"greenhouse", "lever", "ashby"}
ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}\Z")
EXCLUDED_HOSTS = (
    "linkedin.com", "indeed.com", "simplyhired.com", "glassdoor.com",
    "ziprecruiter.com", "builtin.com", "builtinchicago.org", "ycombinator.com",
    "workatastartup.com", "wellfound.com", "hiringcafe.com", "hiring.cafe",
    "lensa.com", "tealhq.com", "welcometothejungle.com", "otta.com", "dice.com",
    "weworkremotely.com", "remotive.com", "idealist.org", "jobbank.gc.ca",
    "apprenticeship.gov", "findajob.dwp.gov.uk", "jobs.service.gov.uk",
    "jobapplyni.com", "eures.europa.eu", "myworkdayjobs.com", "applytojob.com",
    "icims.com", "avature.net",
)
MAX_FILE_BYTES = 2 * 1024 * 1024


def utc_now():
    return datetime.now(timezone.utc)


def instant(value):
    if not isinstance(value, str):
        raise ValueError("Dates must be ISO timestamps with a timezone")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Dates must be ISO timestamps with a timezone") from None
    if result.tzinfo is None:
        raise ValueError("Dates must include a timezone")
    return result.astimezone(timezone.utc)


def fields(value, names, label):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        raise ValueError(f"{label} has missing or unsupported fields")


def identifier(value, label="identifier"):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError(f"{label} must be a short identifier, not personal text")
    return value


def short_text(value, label, limit):
    if (not isinstance(value, str) or not value.strip() or len(value) > limit
            or any(ord(c) < 32 for c in value) or "@" in value
            or "://" in value or re.search(r"\b(?:api[_ -]?key|password|bearer|secret)\b", value, re.I)):
        raise ValueError(f"{label} must contain short, non-sensitive metadata only")


def public_url(value):
    if not isinstance(value, str) or any(c.isspace() for c in value):
        raise ValueError("URLs must be public HTTPS links")
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        if (parsed.scheme != "https" or not host or parsed.username or parsed.password
                or parsed.query or parsed.fragment or parsed.port not in (None, 443)
                or host == "localhost" or ":" in host or re.fullmatch(r"[\d.]+", host)
                or any(c in value for c in "\\<>\"{}|^`")):
            raise ValueError
    except ValueError:
        raise ValueError("URLs must be public HTTPS links without credentials, queries, or fragments") from None
    if any(host == item or host.endswith("." + item) for item in EXCLUDED_HOSTS):
        raise ValueError("Excluded sources cannot be registry evidence or destinations")
    return parsed


def checked_date(value, now):
    parsed = instant(value)
    if parsed > now:
        raise ValueError("checked_at cannot be in the future")
    return parsed


def new_state(profile_id, run_id, families):
    return validate_state({"version": 1, "profile_id": profile_id, "run_id": run_id,
                           "allowed_families": list(families), "attempts": [],
                           "employers": [], "feedback": []})


def validate_attempt(item, families, now):
    fields(item, "id family route query elapsed_seconds status qualified_employer_ids checked_at", "Attempt")
    identifier(item["id"])
    if item["family"] not in families or item["route"] not in ROUTES:
        raise ValueError("Attempt family or route is not allowed")
    short_text(item["query"], "query", 200)
    # State stores generic role/location keywords, never URLs, site operators,
    # pasted descriptions, or credentials. Query execution belongs to the host.
    if re.search(r"\bsite:|\.(?:com|org|net|gov|io)\b", item["query"], re.I):
        raise ValueError("query must contain generic keywords, not source targeting")
    elapsed = item["elapsed_seconds"]
    if (isinstance(elapsed, bool) or not isinstance(elapsed, (int, float))
            or not math.isfinite(elapsed) or elapsed <= 0):
        raise ValueError("elapsed_seconds must be positive and finite")
    if item["status"] not in ("pending", "complete"):
        raise ValueError("Attempt status must be pending or complete")
    employer_ids = item["qualified_employer_ids"]
    if not isinstance(employer_ids, list):
        raise ValueError("qualified_employer_ids must be a unique identifier list")
    for value in employer_ids:
        identifier(value, "employer ID")
    if len(employer_ids) != len(set(employer_ids)):
        raise ValueError("qualified_employer_ids must be a unique identifier list")
    if item["status"] == "pending" and employer_ids:
        raise ValueError("Only completed verification can record qualified employer IDs")
    checked_date(item["checked_at"], now)


def validate_employer(item, profile_id, now):
    fields(item, "employer_id career_url board provenance_url checked_at permission", "Employer")
    identifier(item["employer_id"], "employer ID")
    public_url(item["career_url"])
    public_url(item["provenance_url"])
    checked = checked_date(item["checked_at"], now)
    board = item["board"]
    fields(board, "provider board region observed_url observed", "Board")
    if board["provider"] not in PROVIDERS or board["observed"] is not True:
        raise ValueError("Registry requires an observed supported public ATS board")
    identifier(board["board"], "observed board token")
    if board["region"] not in ("global", "eu") or (board["region"] == "eu" and board["provider"] != "lever"):
        raise ValueError("Only Lever supports the eu board region")
    observed = public_url(board["observed_url"])
    paths = {
        "greenhouse": {"boards.greenhouse.io": "/", "job-boards.greenhouse.io": "/",
                       "boards-api.greenhouse.io": "/v1/boards/"},
        "lever": ({"jobs.eu.lever.co": "/", "api.eu.lever.co": "/v0/postings/"}
                  if board["region"] == "eu" else
                  {"jobs.lever.co": "/", "api.lever.co": "/v0/postings/"}),
        "ashby": {"jobs.ashbyhq.com": "/", "api.ashbyhq.com": "/posting-api/job-board/"},
    }[board["provider"]]
    prefix = paths.get(observed.hostname)
    if prefix is None or observed.path.removeprefix(prefix).split("/")[0] != board["board"] or not observed.path.startswith(prefix):
        raise ValueError("Observed URL must identify the recorded provider, region, and board token")
    permission = item["permission"]
    fields(permission, "policy_url scope profile_id checked_at review_due_at expires_at retention_covered retention_basis_url", "Permission")
    if permission["scope"] != "public_listings_and_private_report" or permission["profile_id"] != profile_id:
        raise ValueError("Registry permission must cover this profile and private-report scope")
    if permission["retention_covered"] is not True:
        raise ValueError("Establish minimal-metadata retention coverage before saving registry records")
    public_url(permission["policy_url"])
    public_url(permission["retention_basis_url"])
    permission_checked = checked_date(permission["checked_at"], now)
    if permission_checked > checked:
        raise ValueError("Employer checked_at must include the latest permission check")
    if instant(permission["review_due_at"]) <= permission_checked:
        raise ValueError("review_due_at must be after the permission check")
    if permission["expires_at"] is not None and instant(permission["expires_at"]) <= permission_checked:
        raise ValueError("expires_at must be after the permission check")


def validate_feedback(item, families, now):
    fields(item, "id source statement dimension family preference scope scope_id checked_at", "Feedback")
    identifier(item["id"])
    if item["source"] != "explicit_user":
        raise ValueError("Feedback requires an explicit user statement; ignored jobs are not feedback")
    short_text(item["statement"], "preference statement", 240)
    if item["dimension"] not in ("role", "function") or item["family"] not in families:
        raise ValueError("Feedback must identify an allowed role/function family")
    if item["preference"] not in ("prefer", "avoid", "exclude", "neutral"):
        raise ValueError("preference must be prefer, avoid, exclude, or neutral")
    if item["scope"] not in ("profile", "run"):
        raise ValueError("Feedback scope must be profile or run")
    identifier(item["scope_id"])
    checked_date(item["checked_at"], now)


def validate_state(state, now=None):
    now = now or utc_now()
    fields(state, "version profile_id run_id allowed_families attempts employers feedback", "State")
    if type(state["version"]) is not int or state["version"] != 1:
        raise ValueError("Unsupported state version")
    identifier(state["profile_id"], "profile_id")
    identifier(state["run_id"], "run_id")
    families = state["allowed_families"]
    if not isinstance(families, list) or not families:
        raise ValueError("allowed_families must be a nonempty identifier list")
    for family in families:
        identifier(family, "family")
    if len(set(families)) != len(families):
        raise ValueError("Family identifiers must be unique")
    validators = {
        "attempts": ("id", lambda x: validate_attempt(x, families, now)),
        "employers": ("employer_id", lambda x: validate_employer(x, state["profile_id"], now)),
        "feedback": ("id", lambda x: validate_feedback(x, families, now)),
    }
    for name, (key, validator) in validators.items():
        if not isinstance(state[name], list) or len(state[name]) > 5000:
            raise ValueError(f"{name} must contain at most 5000 records")
        seen = set()
        for item in state[name]:
            validator(item)
            if item[key] in seen:
                raise ValueError(f"Duplicate {name} identifier")
            seen.add(item[key])
    return deepcopy(state)


def record_attempt(state, attempt, now=None):
    result = deepcopy(state)
    prior = next((i for i, item in enumerate(result["attempts"]) if item["id"] == attempt.get("id")), None)
    if prior is None:
        result["attempts"].append(attempt)
    else:
        old = result["attempts"][prior]
        if (old["status"] != "pending" or attempt.get("status") != "complete"
                or any(old[key] != attempt.get(key) for key in ("family", "route", "query"))
                or instant(attempt["checked_at"]) < instant(old["checked_at"])):
            raise ValueError("Only a matching pending attempt can be completed")
        result["attempts"][prior] = attempt
    return validate_state(result, now)


def record_feedback(state, feedback, now=None):
    result = deepcopy(state)
    result["feedback"].append(feedback)
    return validate_state(result, now)


def record_employer(state, employer, now=None):
    result = deepcopy(state)
    old = next((item for item in result["employers"] if item["employer_id"] == employer.get("employer_id")), None)
    if old is not None and instant(employer["checked_at"]) < instant(old["checked_at"]):
        raise ValueError("Registry refresh cannot replace a newer check with an older one")
    result["employers"] = [item for item in result["employers"] if item["employer_id"] != employer.get("employer_id")]
    result["employers"].append(employer)
    return validate_state(result, now)


def effective_feedback(state):
    latest = {}
    for item in sorted(state["feedback"], key=lambda x: instant(x["checked_at"])):
        scope_id = state["profile_id"] if item["scope"] == "profile" else state["run_id"]
        if item["scope_id"] == scope_id:
            latest[(item["dimension"], item["family"])] = item
    return deepcopy(list(latest.values()))


def fresh_registry(state, now=None):
    now = now or utc_now()
    validate_state(state, now)
    usable = []
    for item in state["employers"]:
        permission = item["permission"]
        if instant(permission["review_due_at"]) <= now:
            continue
        if permission["expires_at"] is not None and instant(permission["expires_at"]) <= now:
            continue
        usable.append(deepcopy(item))
    return usable  # Bookkeeping candidates only; not authorization to fetch.


def suggest(state, slots=8, exploration=0.25, recent=3, now=None):
    state = validate_state(state, now)
    if type(slots) is not int or not 1 <= slots <= 100 or type(recent) is not int or not 1 <= recent <= 20:
        raise ValueError("slots must be 1–100 and recent must be 1–20")
    if isinstance(exploration, bool) or not isinstance(exploration, (int, float)) or not 0.1 <= exploration <= 1:
        raise ValueError("exploration must be 0.1–1")
    feedback = effective_feedback(state)
    excluded = {x["family"] for x in feedback if x["preference"] == "exclude"}
    families = [x for x in state["allowed_families"] if x not in excluded]
    history = {family: [] for family in families}
    attempts = {family: 0 for family in families}
    pending = {family: 0 for family in families}
    last_at = {family: datetime.min.replace(tzinfo=timezone.utc) for family in families}
    seen = set()
    for item in sorted(state["attempts"], key=lambda x: (instant(x["checked_at"]), x["id"])):
        family = item["family"]
        if family in history:
            attempts[family] += 1
            last_at[family] = instant(item["checked_at"])
        if item["status"] == "pending":
            if family in history:
                pending[family] += 1
            continue
        marginal = len(set(item["qualified_employer_ids"]) - seen)
        seen.update(item["qualified_employer_ids"])
        if family in history:
            history[family].append((marginal, item["elapsed_seconds"]))
    metrics = {}
    for family in families:
        window = history[family][-recent:]
        count = sum(item[0] for item in window)
        elapsed = sum(item[1] for item in window)
        metrics[family] = {"family": family, "completed_attempts": len(history[family]),
                           "pending_attempts": pending[family], "recent_completed": len(window),
                           "marginal_employers_per_query": count / len(window) if window else None,
                           "marginal_employers_per_minute": 60 * count / elapsed if window else None}
    allocations = {family: 0 for family in families}
    decisions = []
    # At least one exploratory slot; all-untried starts remain round-robin fair.
    explore_slots = min(slots, max(1, math.ceil(slots * exploration)))
    for index in range(slots):
        if not families:
            break
        untried = [family for family in families if attempts[family] + allocations[family] == 0]
        exploring = index < explore_slots or bool(untried) or not any(history.values())
        if exploring:
            family = min(families, key=lambda x: (attempts[x] + allocations[x], last_at[x], families.index(x)))
        else:
            family = max(families, key=lambda x: (
                (metrics[x]["marginal_employers_per_minute"] or 0) / (allocations[x] + 1),
                metrics[x]["marginal_employers_per_query"] or 0,
                -(attempts[x] + allocations[x]), -families.index(x)))
        allocations[family] += 1
        decisions.append({"family": family, "reason": "exploration" if exploring else "recent_verified_yield"})
    return {"allocations": [{"family": family, "slots": allocations[family], **metrics[family]}
                            for family in families],
            "order": decisions, "effective_feedback": feedback,
            "note": "Effort suggestions only; pending checks are not zero yield. Preferences never change resume-fit scores."}


def _load_bytes(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("State must be an existing regular file, not a symlink")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("State file exceeds 2 MiB")
    return path.read_bytes()


def load_state(path, now=None):
    data = _load_bytes(path)
    return validate_state(json.loads(data), now), hashlib.sha256(data).hexdigest()


def save_state(state, path, expected_sha=None, repo_root=None, now=None):
    state = validate_state(state, now)
    path = Path(path).absolute()
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parent.parent
    resolved = path.resolve()
    if path.is_symlink():
        raise ValueError("State must not replace a symlink")
    if path.is_relative_to(root) and not resolved.is_relative_to(root / "private"):
        raise ValueError("Repository state must not escape private/ through a symlink")
    if resolved.is_relative_to(root) and not resolved.is_relative_to(root / "private"):
        raise ValueError("Inside the repository, state must be saved under ignored private/")
    # Resolve intentional outside-directory aliases (e.g. macOS /var -> /private/var),
    # while refusing symlink output files and repository-private escapes above.
    path = resolved
    if expected_sha is not None and not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise ValueError("expected_sha must be the digest returned by load_state")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = path.with_name(path.name + ".lock")
    try:
        lock_fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise ValueError("Another state write is active; existing state was preserved") from None
    temporary = None
    try:
        os.close(lock_fd)
        exists = path.exists()
        if exists and expected_sha is None:
            raise ValueError("State already exists; load it and supply expected_sha to replace")
        if expected_sha is not None:
            if not exists or hashlib.sha256(_load_bytes(path)).hexdigest() != expected_sha:
                raise ValueError("State changed or disappeared; reload before replacing")
        data = (json.dumps(state, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
        if len(data) > MAX_FILE_BYTES:
            raise ValueError("State exceeds 2 MiB")
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".search-state-", delete=False) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if expected_sha is None:
            os.link(temporary, path)  # Atomic create, refuses a competing file.
            temporary.unlink()
        else:
            os.replace(temporary, path)
        temporary = None
        return hashlib.sha256(data).hexdigest()
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        lock.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Create empty private state; never overwrite")
    init.add_argument("state")
    init.add_argument("--profile", required=True)
    init.add_argument("--run", required=True)
    init.add_argument("--families", nargs="+", required=True)
    validate = commands.add_parser("validate", help="Validate a metadata-only JSON file")
    validate.add_argument("input")
    save = commands.add_parser("save", help="Validate and atomically save host-prepared state")
    save.add_argument("input")
    save.add_argument("--state", required=True)
    save.add_argument("--expected-sha")
    plan = commands.add_parser("suggest", help="Suggest family effort; never execute a query")
    plan.add_argument("state")
    plan.add_argument("--slots", type=int, default=8)
    plan.add_argument("--exploration", type=float, default=0.25)
    plan.add_argument("--recent", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            digest = save_state(new_state(args.profile, args.run, args.families), args.state)
            result = {"saved": str(Path(args.state).absolute()), "sha256": digest}
        elif args.command == "validate":
            _, digest = load_state(args.input)
            result = {"valid": True, "sha256": digest}
        elif args.command == "save":
            state, _ = load_state(args.input)
            result = {"sha256": save_state(state, args.state, args.expected_sha)}
        else:
            state, _ = load_state(args.state)
            result = suggest(state, args.slots, args.exploration, args.recent)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f"search_state: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
