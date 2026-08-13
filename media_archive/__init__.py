from __future__ import annotations

import csv
import json
import os
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

DOUBAN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://movie.douban.com/",
}


def get_douban_user_id(cookie: str) -> str | None:
    """Extract user id from douban cookie (dbcl2 field)."""
    import re
    m = re.search(r'dbcl2="([^"]+)"', cookie)
    if m:
        uid = m.group(1).split(":")[0]
        return uid
    return None


def crawl_douban_movies(cookie: str, limit: int = 0) -> list[dict]:
    """Crawl user's watched movies from douban."""
    uid = get_douban_user_id(cookie)
    if not uid:
        return []

    url = f"https://movie.douban.com/people/{uid}/collect"
    all_items = []
    start = 0
    session = requests.Session()
    session.headers.update(DOUBAN_HEADERS)
    session.cookies.set_string(cookie)

    while True:
        try:
            r = session.get(url, params={"start": start, "sort": "time", "rating": "all", "filter": "all"},
                           timeout=15)
        except Exception as e:
            print(f"[douban] Request error at start={start}: {e}")
            break

        if r.status_code == 403 or r.status_code == 412:
            print(f"[douban] Blocked at start={start}, status={r.status_code}")
            break
        if r.status_code != 200:
            print(f"[douban] HTTP {r.status_code} at start={start}")
            break

        soup = BeautifulSoup(r.text, "lxml")
        items = soup.select("div.grid-container div.item")
        if not items:
            break

        for item in items:
            link_el = item.select_one("a")
            title_el = item.select_one("span.title")
            rating_el = item.select_one("span.rating")
            date_el = item.select_one("span.collect-time")

            if not link_el or not title_el:
                continue

            href = link_el.get("href", "")
            title = title_el.get_text(strip=True)
            rating = rating_el.get_text(strip=True) if rating_el else ""
            date = date_el.get_text(strip=True) if date_el else ""

            all_items.append({
                "title": title,
                "url": href,
                "rating": rating,
                "date": date,
                "platform": "douban",
                "type": "movie",
                "status": "watched",
            })

        start += 20
        time.sleep(1.5)

        if limit and len(all_items) >= limit:
            all_items = all_items[:limit]
            break

        if len(items) < 20:
            break

    return all_items


# ── Bilibili ───────────────────────────────────────────────────────────

BILI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Accept": "application/json, text/plain, */*",
}


def parse_bili_cookie(cookie_str: str) -> dict:
    """Parse bilibili cookie string into dict."""
    result = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def get_bili_uid(cookie_str: str) -> str | None:
    """Extract DedeUserID from bilibili cookie."""
    cookies = parse_bili_cookie(cookie_str)
    return cookies.get("DedeUserID") or cookies.get("dedeuserid")


def crawl_bilibili_bangumi(cookie_str: str, limit: int = 0) -> list[dict]:
    """Crawl user's watched anime (追番-看过) from Bilibili."""
    uid = get_bili_uid(cookie_str)
    if not uid:
        return []

    all_items = []
    pn = 1
    session = requests.Session()
    session.headers.update(BILI_HEADERS)
    session.cookies.set_string(cookie_str)

    while True:
        try:
            r = session.get(
                "https://api.bilibili.com/x/space/bangumi/follow/list",
                params={"vmid": uid, "type": "1", "follow_status": "0", "pn": pn, "ps": "20"},
                timeout=15,
            )
        except Exception as e:
            print(f"[bilibili] Request error at page={pn}: {e}")
            break

        if r.status_code != 200:
            print(f"[bilibili] HTTP {r.status_code} at page={pn}")
            break

        data = r.json()
        if data.get("code") != 0:
            print(f"[bilibili] API error: {data.get('message')}")
            break

        items = data.get("data", {}).get("list", [])
        if not items:
            break

        for item in items:
            season_id = item.get("season_id")
            season_title = item.get("title", "")
            cover = item.get("cover", "")
            evaluate = item.get("evaluate", "")
            new_ep = item.get("new_ep", {})
            index_show = new_ep.get("index_show", "")
            follow_status = item.get("follow_status", "")

            all_items.append({
                "title": season_title,
                "url": f"https://www.bilibili.com/bangumi/play/ss{season_id}",
                "cover": cover,
                "subtitle": evaluate,
                "latest_episode": index_show,
                "follow_status": follow_status,
                "platform": "bilibili",
                "type": "anime",
                "status": "watched" if follow_status == "2" else "watching",
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

NETEASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://music.163.com/",
    "Origin": "https://music.163.com",
    "Content-Type": "application/x-www-form-urlencoded",
}


def parse_netease_cookie(cookie_str: str) -> dict:
    result = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def get_netease_uid(cookie_str: str) -> str | None:
    cookies = parse_netease_cookie(cookie_str)
    music_u = cookies.get("MUSIC_U")
    if music_u:
        # Decode base64 to get user ID
        import base64
        try:
            decoded = base64.b64decode(music_u)
            return decoded.decode("utf-8")
        except Exception:
            return None
    return cookies.get("userId")


def _netease_post(session: requests.Session, url: str, data: dict) -> dict | None:
    """POST to Netease weapi."""
    try:
        r = session.post(url, data=data, timeout=15)
        return r.json()
    except Exception as e:
        print(f"[netease] POST error: {e}")
        return None


def crawl_netease_liked(cookie_str: str, limit: int = 0) -> list[dict]:
    """Crawl user's 'I like' playlist from Netease."""
    cookies = parse_netease_cookie(cookie_str)
    csrf = cookies.get("__csrf", "")

    session = requests.Session()
    session.headers.update(NETEASE_HEADERS)
    session.cookies.set_string(cookie_str)

    # Get user playlists to find the 'I like' playlist
    resp = _netease_post(session,
                         "https://music.163.com/weapi/user/playlist",
                         {"uid": "", "limit": "36", "offset": "0", "total": "true", "csrf_token": csrf})

    if not resp or resp.get("code") != 200:
        print("[netease] Failed to get user playlists")
        return []

    playlists = resp.get("playlist", [])
    liked_id = None
    for pl in playlists:
        if pl.get("name") == "我喜欢的音乐" or pl.get("defaultOrder") is True:
            liked_id = pl.get("id")
            break

    if not liked_id and playlists:
        liked_id = playlists[0].get("id")

    if not liked_id:
        print("[netease] Cannot find '我喜欢的音乐' playlist")
        return []

    # Fetch all tracks with pagination
    all_tracks = []
    offset = 0
    page_size = 1000

    while True:
        post_data = {
            "id": str(liked_id),
            "limit": str(page_size),
            "offset": str(offset),
            "total": "true",
            "csrf_token": csrf,
        }
        data = _netease_post(session, "https://music.163.com/weapi/v3/playlist/detail", post_data)

        if not data or data.get("code") != 200:
            print(f"[netease] Playlist fetch error at offset={offset}")
            break

        tracks = data.get("songs", [])
        if not tracks:
            break

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

        offset += page_size
        time.sleep(1)

        if len(tracks) < page_size:
            break
        if limit and len(all_tracks) >= limit:
            all_tracks = all_tracks[:limit]
            break

    return all_tracks


def crawl_netease_playhistory(cookie_str: str, limit: int = 0) -> list[dict]:
    """Crawl user's play history (听歌排行) from Netease."""
    uid = get_netease_uid(cookie_str)
    cookies = parse_netease_cookie(cookie_str)
    csrf = cookies.get("__csrf", "")

    if not uid:
        print("[netease] Cannot find user ID")
        return []

    all_records = []
    offset = 0
    page_size = 1000

    session = requests.Session()
    session.headers.update(NETEASE_HEADERS)
    session.cookies.set_string(cookie_str)

    while True:
        post_data = {
            "uid": uid,
            "type": "-1",
            "limit": str(page_size),
            "offset": str(offset),
            "total": "true",
            "csrf_token": csrf,
        }
        data = _netease_post(session, "https://music.163.com/weapi/v1/play/record", post_data)

        if not data or data.get("code") != 200:
            print(f"[netease] Play history error at offset={offset}")
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
        time.sleep(1)

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
