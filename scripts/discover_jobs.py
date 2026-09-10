#!/usr/bin/env python3
"""Collect public employer-board leads; Python 3.10+, standard library only.

This is a discovery input to the skill, not the scored-report input. The host
agent also searches LinkedIn, Indeed, other boards and employer career pages.
Board tokens must come from observed career-page links, never guessed names.
Docs checked 2026-09-10: docs.greenhouse.io/job-board.html,
github.com/lever/postings-api, developers.ashbyhq.com/docs/public-job-posting-api.
"""

import argparse
from datetime import datetime, timezone
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import ssl
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

PAGE_SIZE = 100
MAX_BYTES = 16 * 1024 * 1024
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}\Z")
API_PATHS = {
    "boards-api.greenhouse.io": re.compile(r"/v1/boards/[A-Za-z0-9_-]+/jobs\Z"),
    "api.lever.co": re.compile(r"/v0/postings/[A-Za-z0-9_-]+\Z"),
    "api.eu.lever.co": re.compile(r"/v0/postings/[A-Za-z0-9_-]+\Z"),
    "api.ashbyhq.com": re.compile(r"/posting-api/job-board/[A-Za-z0-9_-]+\Z"),
}


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def string(value):
    return value.strip() if isinstance(value, str) else ""


class PlainHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        elif not self.hidden:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)
        elif not self.hidden:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_html(value):
    # Greenhouse may encode tags twice; strip them only after entity decoding.
    content = string(value)
    for _ in range(2):
        content = unescape(content)
    parser = PlainHTML()
    parser.feed(content)
    parser.close()
    return " ".join("".join(parser.parts).split())


def valid_link(value):
    if not isinstance(value, str) or any(char.isspace() or ord(char) < 32 or char == "\\" for char in value):
        return None
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        parsed.port  # Reject malformed/out-of-range ports without connecting.
        if (parsed.scheme in ("http", "https") and hostname
                and parsed.username is None and parsed.password is None
                and not any(char in hostname for char in '<>"{}|^`%')):
            return value
    except ValueError:
        pass
    return None


def canonical_link(value):
    parsed = urlsplit(value)
    query = [(key, val) for key, val in parse_qsl(parsed.query)
             if not key.lower().startswith("utm_") and key not in ("gh_src", "lever-origin")]
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(),
                       parsed.path.rstrip("/"), urlencode(sorted(query)), ""))


def validate_board(raw):
    if not isinstance(raw, dict):
        raise ValueError("Each board must be an object")
    provider, board = raw.get("provider"), raw.get("board")
    if provider not in ("greenhouse", "lever", "ashby"):
        raise ValueError("provider must be greenhouse, lever, or ashby")
    if not isinstance(board, str) or not TOKEN.fullmatch(board):
        raise ValueError("board must be an observed 1–100 character token (letters, digits, _ or -)")
    region = raw.get("region", "global")
    if region not in ("global", "eu") or (provider != "lever" and region != "global"):
        raise ValueError("region may be global or eu; eu is supported only for Lever")
    return {"provider": provider, "board": board, "region": region}


def endpoint(board, page=0):
    provider, token = board["provider"], board["board"]
    if provider == "greenhouse":
        return f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    if provider == "ashby":
        return f"https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true"
    host = "api.eu.lever.co" if board["region"] == "eu" else "api.lever.co"
    return f"https://{host}/v0/postings/{token}?mode=json&skip={page * PAGE_SIZE}&limit={PAGE_SIZE}"


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HTTPError(req.full_url, code, "Redirect refused; inspect source manually", headers, fp)


def fetch_json(url, timeout):
    parsed = urlsplit(url)
    path_pattern = API_PATHS.get(parsed.netloc)
    if parsed.scheme != "https" or not path_pattern or not path_pattern.fullmatch(parsed.path):
        raise ValueError("Only documented public listing API endpoints may be requested")
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "job-search-assistant/1.0"})
    with build_opener(NoRedirects()).open(request, timeout=timeout) as response:
        content = response.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise ValueError("Response exceeded 16 MiB; source needs manual review")
    return json.loads(content.decode("utf-8"))


def normalize(raw, board, api_url, checked_at):
    if not isinstance(raw, dict):
        raise ValueError("Job entry is not an object")
    provider = board["provider"]
    if provider == "ashby" and raw.get("isListed") is False:
        return None  # Direct-link-only postings must not be exposed in discovery.
    if provider == "greenhouse" and "internal_job_id" in raw and raw["internal_job_id"] is None:
        return None  # Prospect/talent-pool posts are not an advertised job vacancy.
    title = string(raw.get("text" if provider == "lever" else "title"))
    link_key = {"greenhouse": "absolute_url", "lever": "hostedUrl", "ashby": "jobUrl"}[provider]
    source_url = valid_link(raw.get(link_key))
    if not title or not source_url:
        raise ValueError("Job lacks a title or safe HTTP(S) posting link")
    job_id = raw.get("id")
    if not isinstance(job_id, (str, int)) or isinstance(job_id, bool) or not str(job_id):
        job_id = hashlib.sha256(canonical_link(source_url).encode()).hexdigest()[:20]
    location = workplace = employment = salary = None
    description = ""
    if provider == "greenhouse":
        loc = raw.get("location")
        location = string(loc.get("name")) if isinstance(loc, dict) else ""
        description = plain_html(raw.get("content"))
    elif provider == "lever":
        categories = raw.get("categories")
        categories = categories if isinstance(categories, dict) else {}
        location = string(categories.get("location"))
        employment = string(categories.get("commitment"))
        workplace = string(raw.get("workplaceType"))
        if workplace == "unspecified":
            workplace = None
        parts = [string(raw.get("descriptionPlain")) or plain_html(raw.get("description"))]
        extra = raw.get("lists")
        for item in extra if isinstance(extra, list) else []:
            if isinstance(item, dict):
                parts.extend([string(item.get("text")), plain_html(item.get("content"))])
        parts.append(string(raw.get("additionalPlain")) or plain_html(raw.get("additional")))
        description = "\n".join(part for part in parts if part)
        pay = raw.get("salaryRange")
        if isinstance(pay, dict):
            salary = {key: pay.get(key) for key in ("currency", "interval", "min", "max")}
            if all(value is None for value in salary.values()):
                salary = None
    else:
        location = string(raw.get("location"))
        employment = string(raw.get("employmentType"))
        workplace = string(raw.get("workplaceType"))
        if not workplace and raw.get("isRemote") is True:
            workplace = "Remote"
        description = string(raw.get("descriptionPlain")) or plain_html(raw.get("descriptionHtml"))
        pay = raw.get("compensation")
        if isinstance(pay, dict):
            salary = string(pay.get("scrapeableCompensationSalarySummary")) or None
    return {
        "id": f"{provider}:{board['region']}:{board['board']}:{job_id}",
        "title": title, "company": None, "company_board": board["board"],
        "location": location or None, "workplace": workplace or None,
        "employment_type": employment or None, "salary": salary,
        "source_url": source_url, "apply_url": valid_link(raw.get("applyUrl")),
        "description": description or None,
        "published_at": string(raw.get("publishedAt")) or None,
        "source": {**board, "api_url": api_url, "checked_at": checked_at},
        "discovered_via": [{**board, "api_url": api_url, "checked_at": checked_at,
                            "source_url": source_url}],
        "status": "published_in_api",
        "verification": "needs_description_and_application_check",
    }


def discover(boards, keywords=(), timeout=15, max_pages=10, fetcher=None):
    """Return deduplicated leads. Source count means newly retained unique leads."""
    if not isinstance(boards, list) or not 1 <= len(boards) <= 100:
        raise ValueError("boards must be a list of 1–100 board objects")
    if not 1 <= timeout <= 60 or not 1 <= max_pages <= 20:
        raise ValueError("timeout must be 1–60 seconds and max_pages 1–20")
    checked = timestamp()
    terms = [term.strip().casefold() for term in keywords if isinstance(term, str) and term.strip()]
    result = {"generated_at": checked, "keywords": terms, "jobs": [], "sources": []}
    seen_boards, seen_ids, seen_urls = set(), {}, {}
    fetcher = fetcher or fetch_json
    for raw_board in boards:
        source = {"provider": None, "board": None, "region": None, "status": "blocked",
                  "count": 0, "fetched_count": 0, "errors": [], "truncated": False,
                  "checked_at": checked}
        result["sources"].append(source)
        try:
            board = validate_board(raw_board)
        except ValueError as exc:
            source["errors"].append(str(exc))
            continue
        source.update(board)
        board_key = (board["provider"], board["board"], board["region"])
        if board_key in seen_boards:
            source.update(status="limited", errors=["Duplicate board skipped; see earlier source"])
            continue
        seen_boards.add(board_key)
        source["status"] = "searched"
        successful_pages, page_signatures = 0, set()
        for page in range(max_pages if board["provider"] == "lever" else 1):
            url = endpoint(board, page)
            try:
                payload = fetcher(url, timeout)
                rows = payload if board["provider"] == "lever" else payload.get("jobs") if isinstance(payload, dict) else None
                if not isinstance(rows, list):
                    raise ValueError("Unexpected response: job list missing")
                successful_pages += 1
                source["fetched_count"] += len(rows)
                signature = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
                repeated_page = bool(rows and signature in page_signatures)
                if repeated_page:
                    source.update(status="limited", truncated=True)
                    source["errors"].append("Repeated page; stopped to avoid a pagination loop")
                page_signatures.add(signature)
                malformed = 0
                for raw in rows:
                    try:
                        job = normalize(raw, board, url, checked)
                    except (ValueError, TypeError):
                        malformed += 1
                        continue
                    if job is None:
                        continue
                    link = canonical_link(job["source_url"])
                    # Provider IDs identify the posting across a provider's boards.
                    identity = (board["provider"], board["region"], job["id"].split(":", 3)[3])
                    existing = seen_ids.get(identity) or seen_urls.get(link)
                    if existing is not None:
                        origin = job["discovered_via"][0]
                        if origin not in existing["discovered_via"]:
                            existing["discovered_via"].append(origin)
                        seen_ids[identity], seen_urls[link] = existing, existing
                        continue
                    text = f"{job['title']} {job['description'] or ''}".casefold()
                    if terms and not any(term in text for term in terms):
                        continue
                    seen_ids[identity], seen_urls[link] = job, job
                    result["jobs"].append(job)
                    source["count"] += 1
                if malformed:
                    source["status"] = "limited"
                    source["errors"].append(f"Skipped {malformed} malformed job entries on page {page + 1}")
                if board["provider"] == "greenhouse":
                    meta = payload.get("meta")
                    total = meta.get("total") if isinstance(meta, dict) else None
                    if isinstance(total, int) and total > len(rows):
                        source.update(status="limited", truncated=True)
                        source["errors"].append("API returned fewer jobs than its reported total")
                if repeated_page or board["provider"] != "lever" or len(rows) < PAGE_SIZE:
                    break
                if page + 1 == max_pages:
                    source.update(status="limited", truncated=True)
                    source["errors"].append("Page cap reached; more postings may exist")
            except (HTTPError, URLError, OSError, ValueError) as exc:
                source["status"] = "limited" if successful_pages else "blocked"
                if isinstance(exc, HTTPError):
                    message = f"HTTP {exc.code}; no retry or access bypass attempted"
                elif isinstance(getattr(exc, "reason", exc), ssl.SSLCertVerificationError):
                    message = "TLS certificate verification failed; configure a trusted CA bundle with SSL_CERT_FILE"
                elif isinstance(exc, (URLError, OSError)):
                    message = "Network request failed or timed out; inspect this source manually"
                else:
                    message = str(exc)
                source["errors"].append(message)
                break
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boards", required=True, type=Path, help="JSON list of observed employer boards")
    parser.add_argument("--output", required=True, type=Path, help="Discovery JSON destination")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing discovery output")
    parser.add_argument("--keywords", nargs="+", default=[], help="Local OR substring filter on title and description")
    parser.add_argument("--timeout", type=int, default=15, help="Per-request seconds (1–60; default 15)")
    parser.add_argument("--max-pages", type=int, default=10, help="Lever page cap (1–20; 100 jobs/page)")
    args = parser.parse_args(argv)
    try:
        if (args.boards.resolve() == args.output.resolve()
                or (args.output.exists() and args.boards.samefile(args.output))):
            raise ValueError("Output must not overwrite the boards input (including file aliases)")
        if args.output.exists() and not args.overwrite:
            raise ValueError("Output already exists; use --overwrite to replace it")
        boards = json.loads(args.boards.read_text(encoding="utf-8"))
        result = discover(boards, args.keywords, args.timeout, args.max_pages)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w" if args.overwrite else "x", encoding="utf-8") as destination:
            destination.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(f"Saved {len(result['jobs'])} leads; check sources for access or coverage limits.")
    return 0 if all(source["status"] == "searched" for source in result["sources"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
