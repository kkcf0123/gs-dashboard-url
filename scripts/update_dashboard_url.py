import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


QUICK_TUNNEL_HOST_RE = re.compile(r"^[a-z0-9-]+\.trycloudflare\.com$", re.IGNORECASE)


def normalize_dashboard_url(value):
    raw = str(value or "").strip()
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("URL must be an https:// address.")
    if parsed.username or parsed.password or parsed.port:
        raise ValueError("URL must not include credentials or a custom port.")
    if not QUICK_TUNNEL_HOST_RE.fullmatch(parsed.hostname):
        raise ValueError("URL must be a *.trycloudflare.com Quick Tunnel address.")
    if parsed.query or parsed.fragment:
        raise ValueError("URL must not include a query string or fragment.")
    if parsed.path not in ("", "/"):
        raise ValueError("URL must point to the dashboard root.")
    return f"https://{parsed.hostname.lower()}"


def dashboard_payload(url, now=None):
    timestamp = now or datetime.now(timezone.utc)
    return {
        "schema_version": 1,
        "url": normalize_dashboard_url(url),
        "updated_at": timestamp.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": "gs-ops-bot",
    }


def github_request(url, token, method="GET", payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "gs-ops-bot-dashboard-url-updater",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def update_dashboard_file(repository, branch, token, url):
    quoted_branch = urllib.parse.quote(branch, safe="")
    api_url = f"https://api.github.com/repos/{repository}/contents/dashboard.json"
    current = github_request(f"{api_url}?ref={quoted_branch}", token)
    content = json.dumps(dashboard_payload(url), ensure_ascii=False, indent=2) + "\n"
    payload = {
        "message": "Update GS Dashboard Quick Tunnel URL",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "sha": current["sha"],
        "branch": branch,
    }
    return github_request(api_url, token, method="PUT", payload=payload)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Update dashboard.json with the active Quick Tunnel URL.")
    parser.add_argument("url", help="Active https://*.trycloudflare.com URL")
    parser.add_argument(
        "--repository",
        default=os.getenv("GITHUB_REPOSITORY", ""),
        help="GitHub owner/repository (or set GITHUB_REPOSITORY)",
    )
    parser.add_argument(
        "--branch",
        default=os.getenv("GITHUB_CONFIG_BRANCH", "main"),
        help="Target branch (default: main)",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN or GH_TOKEN is required.")
    if not args.repository or "/" not in args.repository:
        raise RuntimeError("GITHUB_REPOSITORY must use owner/repository format.")

    try:
        update_dashboard_file(args.repository, args.branch, token, args.url)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API update failed: HTTP {error.code}: {detail}") from error

    normalized = normalize_dashboard_url(args.url)
    print(f"Updated {args.repository}/dashboard.json to {normalized}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
