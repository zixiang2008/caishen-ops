#!/usr/bin/env python3
"""YouTube subscription radar.

Reads data/channels.txt (channel_id<TAB>title), fetches each channel's RSS feed,
collects videos published within the lookback window that haven't been seen
before, writes radar.md + data/radar-latest.json, and updates data/radar-state.json.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHANNELS = os.path.join(HERE, "data", "channels.txt")
STATE = os.path.join(HERE, "data", "radar-state.json")
LATEST = os.path.join(HERE, "data", "radar-latest.json")
REPORT = os.path.join(HERE, "radar.md")
FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
UA = {"User-Agent": "caishen-ops/1.0"}


def load_state() -> dict:
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def fetch_feed(cid: str) -> list[dict]:
    try:
        req = urllib.request.Request(FEED.format(cid=cid), headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            root = ET.fromstring(r.read())
        out = []
        for entry in root.findall("a:entry", NS):
            vid = entry.findtext("yt:videoId", "", NS)
            title = (entry.findtext("a:title", "", NS) or "").strip()
            published = entry.findtext("a:published", "", NS) or ""
            author = entry.findtext("a:author/a:name", "", NS) or ""
            if vid:
                out.append({"id": vid, "title": title, "published": published, "channel": author})
        return out
    except Exception:
        return []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", default="24")
    args = ap.parse_args()
    window = timedelta(hours=float(args.hours))
    now = datetime.now(timezone.utc)
    cutoff = now - window

    channels: list[tuple[str, str]] = []
    with open(CHANNELS, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 2 and parts[0]:
                channels.append((parts[0], parts[1]))

    state = load_state()
    seen = state.get("seen", {})
    fresh: list[dict] = []
    ok = 0
    with cf.ThreadPoolExecutor(max_workers=32) as pool:
        for vids in pool.map(lambda c: fetch_feed(c[0]), channels):
            if vids:
                ok += 1
            for v in vids:
                try:
                    pub = datetime.fromisoformat(v["published"].replace("Z", "+00:00"))
                except ValueError:
                    continue
                if pub >= cutoff and v["id"] not in seen:
                    v["_pub"] = pub.isoformat()
                    fresh.append(v)

    fresh.sort(key=lambda v: v["_pub"], reverse=True)
    # cap report size
    fresh = fresh[:300]
    for v in fresh:
        seen[v["id"]] = v["_pub"][:10]
    # prune state to entries from last 45 days
    keep_before = (now - timedelta(days=45)).date().isoformat()
    state["seen"] = {k: d for k, d in seen.items() if d >= keep_before}
    state["updated"] = now.isoformat()

    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)
    with open(LATEST, "w", encoding="utf-8") as f:
        json.dump({"generated": now.isoformat(), "window_hours": float(args.hours),
                   "channels_ok": ok, "channels_total": len(channels),
                   "new_videos": [{k: v[k] for k in ("id", "title", "published", "channel")} for v in fresh]},
                  f, ensure_ascii=False, indent=1)

    lines = [f"# 订阅雷达 {now.date()}（回看 {args.hours} 小时）",
             f"频道 {ok}/{len(channels)} 抓取成功 · 新视频 {len(fresh)} 条", ""]
    by_ch: dict[str, list[dict]] = {}
    for v in fresh:
        by_ch.setdefault(v["channel"] or "?", []).append(v)
    for ch, vids in sorted(by_ch.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"## {ch}（{len(vids)}）")
        for v in vids:
            lines.append(f"- [{v['title']}]({'https://youtu.be/' + v['id']}) · {v['published'][:16]}")
        lines.append("")
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"new videos: {len(fresh)}; channels ok: {ok}/{len(channels)}; report -> radar.md")


if __name__ == "__main__":
    main()
