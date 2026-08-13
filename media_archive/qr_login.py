from __future__ import annotations

import time
from typing import Any

import requests


# ── Netease QR Login ───────────────────────────────────────────────────

NETEASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://music.163.com/",
    "Origin": "https://music.163.com",
    "Content-Type": "application/x-www-form-urlencoded",
}


def netease_qr_login(console_display_callback=None) -> dict[str, Any]:
    """
    Login to Netease via QR code.

    Args:
        console_display_callback: function(qr_url) to display QR code in terminal

    Returns:
        dict with 'success', 'cookie', 'message'
    """
    session = requests.Session()
    session.headers.update(NETEASE_HEADERS)

    # Step 1: Get QR key
    try:
        r = session.get(
            f"https://music.163.com/weapi/login/qrcode/unikey?csrf_token=&timestamp={int(time.time()*1000)}",
            data={"type": "1"},
            timeout=10,
        )
        key_data = r.json()
        unikey = key_data.get("unikey")
        if not unikey:
            return {"success": False, "message": f"Failed to get QR key: {key_data}"}
    except Exception as e:
        return {"success": False, "message": f"Get QR key error: {e}"}

    # QR code content URL (user scans this with Netease app)
    qr_url = f"https://music.163.com/login?codekey={unikey}"

    # Display QR code
    if console_display_callback:
        console_display_callback(qr_url)
    else:
        print(f"\n请用网易云音乐 APP 扫描以下二维码：\n{qr_url}\n")

    # Step 2: Poll for login status
    print("等待扫码登录...")
    start = time.time()
    while time.time() - start < 180:  # 3 minute timeout
        try:
            r = session.post(
                f"https://music.163.com/weapi/login/qrcode/client/login?csrf_token=&timestamp={int(time.time()*1000)}",
                data={"key": unikey, "type": "1", "csrf_token": ""},
                timeout=10,
            )
            data = r.json()

            code = data.get("code")
            if code == 803:  # Login success
                # Extract cookie from session
                cookies = session.cookies.get_dict()
                if not cookies.get("MUSIC_U"):
                    return {"success": False, "message": "Login succeeded but no MUSIC_U cookie"}

                # Build cookie string
                cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
                return {
                    "success": True,
                    "cookie": cookie_str,
                    "message": "Login successful",
                    "user_id": data.get("account", {}).get("id"),
                    "nickname": data.get("account", {}).get("userName") or data.get("profile", {}).get("nickname"),
                }
            elif code == 800:
                return {"success": False, "message": "QR code expired"}
            elif code == 801:
                pass  # Waiting for scan
            elif code == 802:
                print(".", end="", flush=True)  # Scanned, waiting for confirm
        except Exception as e:
            print(f"\nPoll error: {e}")

        time.sleep(2)

    return {"success": False, "message": "Login timeout (3 minutes)"}


# ── Bilibili QR Login ───────────────────────────────────────────────────

BILI_QR_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}


def bilibili_qr_login(console_display_callback=None) -> dict[str, Any]:
    """
    Login to Bilibili via QR code.

    Args:
        console_display_callback: function(qr_url) to display QR code in terminal
    """
    session = requests.Session()
    session.headers.update(BILI_QR_HEADERS)

    # Step 1: Generate QR code
    try:
        r = session.get("https://passport.bilibili.com/x/passport-login/web/qrcode/generate", timeout=10)
        data = r.json()
        if data.get("code") != 0:
            return {"success": False, "message": f"Generate QR failed: {data}"}

        qrcode_key = data["data"]["qrcode_key"]
        qr_url = data["data"]["url"]
    except Exception as e:
        return {"success": False, "message": f"Generate QR error: {e}"}

    if console_display_callback:
        console_display_callback(qr_url)
    else:
        print(f"\n请用哔哩哔哩 APP 扫描以下二维码：\n{qr_url}\n")

    print("等待扫码登录...")
    start = time.time()
    while time.time() - start < 180:
        try:
            r = session.get(
                "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
                params={"qrcode_key": qrcode_key},
                timeout=10,
            )
            data = r.json()
            poll_code = data.get("data", {}).get("code")

            if poll_code == 0:  # Success
                cookies = session.cookies.get_dict()
                # Need SESSDATA and bili_jct
                if not cookies.get("SESSDATA"):
                    # Check if in response URL
                    url = data["data"].get("url", "")
                    if url:
                        # Parse cookies from URL fragment
                        from urllib.parse import urlparse, parse_qs
                        parsed = urlparse(url)
                        qs = parse_qs(parsed.fragment)
                        for key in ["SESSDATA", "bili_jct", "DedeUserID"]:
                            if key in qs:
                                cookies[key] = qs[key][0]

                if not cookies.get("SESSDATA"):
                    return {"success": False, "message": "Login succeeded but no SESSDATA"}

                cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
                return {
                    "success": True,
                    "cookie": cookie_str,
                    "message": "Login successful",
                    "user_id": cookies.get("DedeUserID"),
                }
            elif poll_code == 86038:
                return {"success": False, "message": "QR code expired"}
            elif poll_code == 86090:
                print(".", end="", flush=True)  # Scanned, waiting confirm
            elif poll_code == 86101:
                pass  # Not scanned
        except Exception as e:
            print(f"\nPoll error: {e}")

        time.sleep(2)

    return {"success": False, "message": "Login timeout (3 minutes)"}


# ── Helper: Display QR in terminal ──────────────────────────────────────

def display_qr_in_terminal(qr_url: str) -> None:
    """Display QR code in terminal using qrcode library."""
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except ImportError:
        print(f"\n请手动复制链接到二维码生成器：\n{qr_url}\n")
