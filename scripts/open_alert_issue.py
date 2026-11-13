#!/usr/bin/env python3
"""Open or update a single 'Uptime alert' issue with the latest failure report."""
import json
import os
import sys
import urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "zixiang2008/caishen-ops")
TOKEN = os.environ["GH_TOKEN"]
TITLE = "🚨 Uptime alert: 服务不可用"
API = f"https://api.github.com/repos/{REPO}"


def api(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        return json.loads(data) if data else {}


def main() -> None:
    report = sys.stdin.read()
    stamp = report.strip().splitlines()[-1] if report.strip() else "unknown"
    body = f"自动生成于 {report}\n\n---\n下次自动恢复后本 issue 会被关闭。\n"
    # find existing open alert issue
    issues = api("GET", f"/issues?state=open&labels=uptime&per_page=1")
    if issues:
        issue = issues[0]
        api("POST", f"/issues/{issue['number']}/comments", {"body": body})
        print(f"commented on issue #{issue['number']}")
    else:
        issue = api("POST", "/issues", {"title": TITLE, "body": body, "labels": ["uptime"]})
        print(f"created issue #{issue['number']}")


if __name__ == "__main__":
    main()
