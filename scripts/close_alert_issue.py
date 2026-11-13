#!/usr/bin/env python3
"""Close the open 'Uptime alert' issue when everything recovered."""
import json
import os
import urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "zixiang2008/caishen-ops")
TOKEN = os.environ["GH_TOKEN"]
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
    issues = api("GET", "/issues?state=open&labels=uptime&per_page=5")
    for issue in issues:
        if "pull_request" in issue:
            continue
        api("POST", f"/issues/{issue['number']}/comments",
            {"body": "✅ 全部端点已恢复，自动关闭本 issue。"})
        api("PATCH", f"/issues/{issue['number']}", {"state": "closed"})
        print(f"closed issue #{issue['number']}")


if __name__ == "__main__":
    main()
