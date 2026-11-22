#!/usr/bin/env python3
"""Polite HTTP health checks for textweb.

One request per URL (HEAD, with a single short GET only when the server
rejects HEAD). Concurrency is bounded, each request has a timeout, and a
short pause plus a per-host lock keeps the check from hammering anyone.
Non-HTTP URLs (Gopher, Gemini) are not contacted.

Running this file starts a full nightly update, same as scripts/nightly.py,
so the historical workflow command still refreshes exports and snapshots.
"""

from __future__ import annotations

import socket
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

from common import USER_AGENT, is_http_url

OUTAGE_MIN_SAMPLE = 5
GET_READ_LIMIT = 512

Probe = Callable[[str, int], dict]


class _HttpOnlyRedirect(urllib.request.HTTPRedirectHandler):
    """Follow redirects only when they stay on HTTP or HTTPS."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlparse(newurl).scheme not in ("http", "https"):
            raise urllib.error.HTTPError(newurl, code, "redirect blocked", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_HttpOnlyRedirect)
_HOST_GUARD = threading.Lock()
_HOST_LOCKS: dict[str, threading.Lock] = {}


def _lock_for(host: str) -> threading.Lock:
    with _HOST_GUARD:
        lock = _HOST_LOCKS.get(host)
        if lock is None:
            lock = threading.Lock()
            _HOST_LOCKS[host] = lock
        return lock


def split_content_type(value: str | None) -> tuple[str | None, str | None]:
    """Return a stable media type without charset parameters.

    Parameter order and charset case change between servers and would make
    nightly diffs noisy, so both media_type and mime_type store the lowercase
    type/subtype only.
    """
    if not value:
        return None, None
    mime = value.split(";", 1)[0].strip().lower()
    if not mime or "/" not in mime:
        return None, None
    return mime, mime


def parse_content_length(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        size = int(str(value).strip())
    except ValueError:
        return None
    if size < 0:
        return None
    return size


def http_result(code: int, media: str | None, mime: str | None, size: int | None) -> dict:
    ok = 200 <= code < 400
    return {
        "status": "ok" if ok else "down",
        "health": "verified" if ok else "broken",
        "http_status": code,
        "media_type": media,
        "mime_type": mime,
        "size_bytes": size,
    }


def down_result() -> dict:
    return {
        "status": "down",
        "health": "broken",
        "http_status": None,
        "media_type": None,
        "mime_type": None,
        "size_bytes": None,
    }


def skipped_result() -> dict:
    return {
        "status": "skipped",
        "health": "unchecked",
        "http_status": None,
        "media_type": None,
        "mime_type": None,
        "size_bytes": None,
    }


def _open(req: urllib.request.Request, timeout: int):
    return _OPENER.open(req, timeout=timeout)


def _request(url: str, method: str, timeout: int, read_limit: int) -> dict:
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,text/plain,application/json;q=0.8,*/*;q=0.5",
            "Connection": "close",
        },
    )
    try:
        with _open(req, timeout) as resp:
            code = int(getattr(resp, "status", None) or resp.getcode())
            headers = resp.headers
            media, mime = split_content_type(headers.get("Content-Type"))
            size = parse_content_length(headers.get("Content-Length"))
            if read_limit:
                resp.read(read_limit)
            return http_result(code, media, mime, size)
    except urllib.error.HTTPError as exc:
        headers = exc.headers
        media, mime = split_content_type(headers.get("Content-Type") if headers else None)
        size = parse_content_length(headers.get("Content-Length") if headers else None)
        return http_result(int(exc.code), media, mime, size)
    except (TimeoutError, socket.timeout, urllib.error.URLError, OSError):
        return down_result()


def probe_url(url: str, timeout: int = 10) -> dict:
    """HEAD the URL. GET a few bytes only when HEAD is not implemented."""
    if not is_http_url(url):
        return skipped_result()
    head = _request(url, "HEAD", timeout, read_limit=0)
    if head.get("http_status") in (405, 501):
        return _request(url, "GET", timeout, read_limit=GET_READ_LIMIT)
    return head


def check_urls(
    urls: Iterable[str],
    *,
    workers: int = 4,
    timeout: int = 10,
    limit: int | None = None,
    pause: float = 0.25,
    probe: Probe | None = None,
) -> dict[str, dict]:
    """Probe unique HTTP(S) URLs in first-seen order.

    `limit` stops after that many unique HTTP(S) URLs. Callers should pass
    sites.json URLs before catalog URLs so a sample prefers the curated index.
    """
    probe_fn = probe or probe_url
    selected: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if not url or url in seen:
            continue
        seen.add(url)
        if not is_http_url(url):
            continue
        selected.append(url)
        if limit is not None and len(selected) >= limit:
            break
    results: dict[str, dict] = {}
    if not selected:
        return results

    def run_one(url: str) -> dict:
        if pause > 0:
            time.sleep(pause)
        host = urlparse(url).hostname or url
        with _lock_for(host):
            return probe_fn(url, timeout)

    pool_size = max(1, min(workers, len(selected)))
    with ThreadPoolExecutor(max_workers=pool_size) as pool:
        futures = {pool.submit(run_one, url): url for url in selected}
        for future in as_completed(futures):
            url = futures[future]
            try:
                results[url] = future.result()
            except Exception:
                results[url] = down_result()
    return results


def outage_suspected(results: Mapping[str, Mapping], *, full_run: bool) -> bool:
    """True when an unattended full run saw only failures.

    A bounded sample (`--limit`) is allowed to record downs. A full run that
    cannot reach anybody is treated as a local network failure so it cannot
    replace known-good statuses.
    """
    if not full_run or len(results) < OUTAGE_MIN_SAMPLE:
        return False
    return all(item.get("status") != "ok" for item in results.values())


def main(argv: list[str] | None = None) -> int:
    import nightly

    return nightly.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
