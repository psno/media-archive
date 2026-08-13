from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

CRED_FILE = Path.home() / ".media_archive_creds.json"
DB_DIR = Path.home() / ".media_archive"
DB_FILE = DB_DIR / "archive.db"


# ── Credential Management ──────────────────────────────────────────────

def load_creds() -> dict[str, Any]:
    if CRED_FILE.exists():
        with open(CRED_FILE) as f:
            return json.load(f)
    return {}


def save_cred(key: str, value: str) -> None:
    creds = load_creds()
    creds[key] = value
    with open(CRED_FILE, "w") as f:
        json.dump(creds, f, ensure_ascii=False, indent=2)
    os.chmod(CRED_FILE, 0o600)


def remove_cred(key: str) -> None:
    creds = load_creds()
    creds.pop(key, None)
    with open(CRED_FILE, "w") as f:
        json.dump(creds, f, ensure_ascii=False, indent=2)


def get_cred(key: str) -> str | None:
    return load_creds().get(key)


# ── Douban ─────────────────────────────────────────────────────────────

def get_douban_user_id(cookie: str) -> str | None:
    m = re.search(r'dbcl2="([^"]+)"', cookie)
    if m:
        return m.group(1).split(":")[0]
    return None


def crawl_douban_movies(cookie: str, limit: int = 0) -> list[dict]:
    """Crawl user's watched movies from douban using Frodo/Rexxar API."""
    uid = get_douban_user_id(cookie)
    if not uid:
        return []

    all_items = []
    start = 0
    page_size = 50  # Douban API default is 20, use 50 to reduce requests
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Referer": "https://m.douban.com/",
    })
    for part in cookie.split(';'):
        part = part.strip()
        if '=' in part:
            k, v = part.split('=', 1)
            session.cookies.set(k.strip(), v.strip(), domain='.douban.com')

    while True:
        try:
            r = session.get(
                f"https://m.douban.com/rexxar/api/v2/user/{uid}/interests",
                params={"type": "movie", "status": "done", "start": start, "count": page_size},
                timeout=15,
            )
        except Exception as e:
            print(f"[douban] Request error at start={start}: {e}")
            break

        if r.status_code != 200:
            print(f"[douban] HTTP {r.status_code} at start={start}, resp={r.text[:200]}")
            break

        try:
            data = r.json()
        except Exception as e:
            print(f"[douban] JSON parse error: {e}")
            break

        items = data.get("interests", [])
        if not items:
            break

        for item in items:
            # Frodo API fields
            subject = item.get("subject", {})
            title = subject.get("title", "") or item.get("title", "")
            url = subject.get("url", "") or item.get("url", "")
            cover_el = subject.get("cover", {}) or item.get("cover", {})
            cover = cover_el.get("url", "") if isinstance(cover_el, dict) else ""
            rating_el = subject.get("rating", {}) or item.get("rating", {})
            avg_rating = rating_el.get("value", "") if isinstance(rating_el, dict) else ""
            user_rating = rating_el.get("star_count", "") if isinstance(rating_el, dict) else ""
            # star_count: 1-5 stars mapped to rating
            date = item.get("create_time", "")
            tags = []
            for tag in (item.get("tags") or []):
                if isinstance(tag, dict):
                    tags.append(tag.get("name", ""))
                else:
                    tags.append(str(tag))
            comment = item.get("comment", "")

            all_items.append({
                "title": title,
                "url": url,
                "cover": cover,
                "rating": str(user_rating) if user_rating else "",
                "avg_rating": avg_rating,
                "date": date,
                "tags": ",".join(tags),
                "comment": comment,
                "platform": "douban",
                "type": "movie",
                "status": "watched",
            })

        start += page_size
        time.sleep(1.5)

        if limit and len(all_items) >= limit:
            all_items = all_items[:limit]
            break
        if len(items) < page_size:
            break

    return all_items


# ── Bilibili ───────────────────────────────────────────────────────────

def get_bili_uid(cookie_str: str) -> str | None:
    for part in cookie_str.split(";"):
        part = part.strip()
        if part.startswith("DedeUserID=") or part.startswith("dedeuserid="):
            return part.split("=", 1)[1]
    return None


def crawl_bilibili_bangumi(cookie_str: str, limit: int = 0) -> list[dict]:
    """Crawl user's watched anime and drama (追番+追剧) from Bilibili."""
    uid = get_bili_uid(cookie_str)
    if not uid:
        return []

    all_items = []
    pn = 1
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com/",
        "Accept": "application/json",
    })
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            session.cookies.set(k.strip(), v.strip(), domain=".bilibili.com")

    # Type 1 = anime (追番), Type 2 = drama (追剧)
    for btype, type_name in [(1, "anime"), (2, "drama")]:
        pn = 1
        while True:
            try:
                r = session.get(
                    "https://api.bilibili.com/x/space/bangumi/follow/list",
                    params={"vmid": uid, "type": str(btype), "follow_status": "0", "pn": pn, "ps": "20"},
                    timeout=15,
                )
            except Exception as e:
                print(f"[bilibili] Request error ({type_name}) page={pn}: {e}")
                break

            if r.status_code != 200:
                print(f"[bilibili] HTTP {r.status_code} ({type_name}) page={pn}")
                break

            data = r.json()
            if data.get("code") != 0:
                print(f"[bilibili] API error ({type_name}): {data.get('message')}")
                break

            items = data.get("data", {}).get("list", [])
            if not items:
                break

            for item in items:
                season_id = item.get("season_id")
                follow_status = item.get("follow_status", 0)
                # Status mapping: 1=追更中, 2=看过, 3=搁置
                status_map = {1: "watching", 2: "watched", 3: "on_hold"}
                status = status_map.get(follow_status, "watching")

                all_items.append({
                    "title": item.get("title", ""),
                    "url": f"https://www.bilibili.com/bangumi/play/ss{season_id}",
                    "cover": item.get("cover", ""),
                    "subtitle": item.get("evaluate", ""),
                    "latest_episode": item.get("new_ep", {}).get("index_show", ""),
                    "follow_status": follow_status,
                    "platform": "bilibili",
                    "type": type_name,
                    "status": status,
                })

            total = data.get("data", {}).get("total", 0)
            pn += 1
            time.sleep(1)

            if len(all_items) >= total or len(items) < 20:
                break
            if limit and len(all_items) >= limit:
                all_items = all_items[:limit]
                break

    return all_items


# ── Netease Cloud Music ────────────────────────────────────────────────

def parse_netease_cookie(cookie_str: str) -> dict:
    result = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def get_netease_uid(cookie_str: str) -> str | None:
    """Get user ID via Netease user/info API."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://music.163.com/",
    })
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            session.cookies.set(k.strip(), v.strip(), domain="music.163.com")

    try:
        r = session.get("https://music.163.com/api/v1/user/info", timeout=10)
        data = r.json()
        # userId is nested in userPoint
        user_point = data.get("userPoint", {})
        uid = user_point.get("userId")
        if uid:
            return str(uid)
        # Fallback: check top level
        uid = data.get("userId") or data.get("code")
        if uid:
            return str(uid)
    except Exception as e:
        print(f"[netease] Get UID error: {e}")
    return None


def _netease_get(session: requests.Session, url: str, params: dict) -> dict | None:
    try:
        r = session.get(url, params=params, timeout=15)
        return r.json()
    except Exception as e:
        print(f"[netease] GET error: {e}")
        return None


def _netease_post(session: requests.Session, url: str, data: dict) -> dict | None:
    try:
        r = session.post(url, data=data, timeout=15)
        return r.json()
    except Exception as e:
        print(f"[netease] POST error: {e}")
        return None


def crawl_netease_liked(cookie_str: str, limit: int = 0) -> list[dict]:
    """Crawl user's 'I like' playlist from Netease using GET APIs."""
    uid = get_netease_uid(cookie_str)
    if not uid:
        print("[netease] Cannot find user ID")
        return []

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://music.163.com/",
    })
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            session.cookies.set(k.strip(), v.strip(), domain="music.163.com")

    # Get user playlists via GET API
    resp = _netease_get(session, "https://music.163.com/api/user/playlist",
                        {"uid": uid, "limit": 36, "offset": 0})

    if not resp or resp.get("code") != 200:
        print("[netease] Failed to get user playlists")
        return []

    # First playlist is usually "我喜欢的音乐"
    playlists = resp.get("playlist", [])
    liked_id = None
    if playlists:
        # Try to find by name
        for pl in playlists:
            if "喜欢" in pl.get("name", "") or pl.get("defaultOrder") is True:
                liked_id = pl.get("id")
                break
        # Fallback to first playlist
        if not liked_id:
            liked_id = playlists[0].get("id")
    if not liked_id:
        print("[netease] Cannot find 'I like' playlist")
        return []

    # Fetch all tracks - API returns all tracks regardless of offset,
    # so we use trackCount from playlist metadata to know the total
    all_tracks = []
    page_size = 2000  # Large enough to get all tracks in one request

    data = _netease_get(session, "https://music.163.com/api/v6/playlist/detail",
                        {"id": str(liked_id), "n": page_size, "s": 0})

    if not data or data.get("code") != 200:
        print(f"[netease] Playlist fetch error, code={data.get('code') if data else 'none'}")
        return []

    tracks = data.get("playlist", {}).get("tracks", [])
    total_count = data.get("playlist", {}).get("trackCount", 0)

    for track in tracks:
        all_tracks.append({
            "title": track.get("name", ""),
            "artists": "/".join(a.get("name", "") for a in track.get("artists", [])),
            "album": track.get("album", {}).get("name", "") if track.get("album") else "",
            "duration_ms": track.get("duration", 0),
            "url": f"https://music.163.com/#/song?id={track.get('id')}",
            "platform": "netease",
            "type": "song",
            "status": "liked",
        })

    # If API returned fewer tracks than trackCount, pagination may be needed
    # but for most cases one request is enough
    if len(all_tracks) < total_count and total_count > 0:
        # Try fetching with larger page size
        remaining = total_count - len(all_tracks)
        data2 = _netease_get(session, "https://music.163.com/api/v6/playlist/detail",
                             {"id": str(liked_id), "n": remaining, "s": len(all_tracks)})
        if data2 and data2.get("code") == 200:
            more_tracks = data2.get("playlist", {}).get("tracks", [])
            for track in more_tracks:
                all_tracks.append({
                    "title": track.get("name", ""),
                    "artists": "/".join(a.get("name", "") for a in track.get("artists", [])),
                    "album": track.get("album", {}).get("name", "") if track.get("album") else "",
                    "duration_ms": track.get("duration", 0),
                    "url": f"https://music.163.com/#/song?id={track.get('id')}",
                    "platform": "netease",
                    "type": "song",
                    "status": "liked",
                })

    if limit and len(all_tracks) > limit:
        all_tracks = all_tracks[:limit]

    return all_tracks


def crawl_netease_playhistory(cookie_str: str, limit: int = 0) -> list[dict]:
    """Crawl user's play history from Netease."""
    uid = get_netease_uid(cookie_str)
    if not uid:
        print("[netease] Cannot find user ID")
        return []

    all_records = []
    offset = 0
    page_size = 1000

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://music.163.com/",
    })
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            session.cookies.set(k.strip(), v.strip(), domain="music.163.com")

    while True:
        data = _netease_get(session, "https://music.163.com/api/v1/play/record",
                            {"uid": uid, "type": "-1", "limit": page_size, "offset": offset})

        if not data or data.get("code") != 200:
            print(f"[netease] Play history error at offset={offset}, code={data.get('code') if data else 'none'}")
            break

        all_data = data.get("allData", [])
        if not all_data:
            break

        for record in all_data:
            song = record.get("song", {})
            all_records.append({
                "title": song.get("name", ""),
                "artists": "/".join(a.get("name", "") for a in song.get("artists", [])),
                "album": song.get("album", {}).get("name", "") if song.get("album") else "",
                "play_count": record.get("playCount", 0),
                "score": record.get("score", 0),
                "url": f"https://music.163.com/#/song?id={song.get('id')}",
                "platform": "netease",
                "type": "song",
                "status": "play_history",
            })

        offset += page_size
        time.sleep(2)  # Increased delay

        if len(all_data) < page_size:
            break
        if limit and len(all_records) >= limit:
            all_records = all_records[:limit]
            break

    return all_records


# ── Database & Export ──────────────────────────────────────────────────

def init_db() -> sqlite3.Connection:
    DB_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_FILE))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT,
            status TEXT,
            rating TEXT,
            date TEXT,
            data_json TEXT,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_platform ON archive(platform)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON archive(type)")
    conn.commit()
    return conn


def save_to_db(records: list[dict]) -> int:
    conn = init_db()
    saved = 0
    for rec in records:
        conn.execute(
            """INSERT INTO archive (platform, type, title, url, status, data_json, crawled_at)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
            (rec.get("platform", ""), rec.get("type", ""), rec.get("title", ""),
             rec.get("url", ""), rec.get("status", ""), json.dumps(rec, ensure_ascii=False)),
        )
        saved += 1
    conn.commit()
    conn.close()
    return saved


def export_json(output_dir: Path) -> Path:
    conn = init_db()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = conn.execute("SELECT * FROM archive ORDER BY platform, type").fetchall()
    result: dict[str, list[dict]] = {}
    for row in rows:
        platform = row[1]
        if platform not in result:
            result[platform] = []
        rec = json.loads(row[8]) if row[8] else {}
        rec["_id"] = row[0]
        rec["_crawled_at"] = row[9]
        result[platform].append(rec)

    out_path = output_dir / "media_archive.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    conn.close()
    return out_path


def export_csv(output_dir: Path) -> Path:
    conn = init_db()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = conn.execute("SELECT * FROM archive ORDER BY platform, type").fetchall()
    if not rows:
        conn.close()
        return output_dir / "media_archive.csv"

    headers = ["id", "platform", "type", "title", "url", "status", "rating", "date", "data_json", "crawled_at"]
    out_path = output_dir / "media_archive.csv"
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        for row in rows:
            vals = [str(v) if v is not None else "" for v in row]
            writer.writerow(vals)

    conn.close()
    return out_path


def get_stats() -> dict:
    conn = init_db()
    rows = conn.execute("SELECT platform, type, COUNT(*) FROM archive GROUP BY platform, type").fetchall()
    stats = {}
    for platform, ptype, count in rows:
        if platform not in stats:
            stats[platform] = {}
        stats[platform][ptype] = count
    total = conn.execute("SELECT COUNT(*) FROM archive").fetchone()[0]
    conn.close()
    return {"total": total, "by_platform": stats}
