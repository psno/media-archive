from __future__ import annotations

import click
import json
from pathlib import Path

from media_archive import (
    get_cred, save_cred, remove_cred,
    crawl_douban_movies, crawl_bilibili_bangumi,
    crawl_netease_liked, crawl_netease_playhistory,
    save_to_db, export_json, export_csv, get_stats,
    DB_DIR, CRED_FILE,
)
from media_archive.qr_login import netease_qr_login, bilibili_qr_login, display_qr_in_terminal


PLATFORMS = ["douban", "bilibili", "netease"]


@click.group()
@click.option("--output-dir", default=None, help="Output directory for exports")
@click.pass_context
def cli(ctx, output_dir):
    """Media Archive - CLI tool to archive media data from Douban, Bilibili, Netease."""
    ctx.ensure_object(dict)
    ctx.obj["output_dir"] = Path(output_dir) if output_dir else None
    ctx.obj["stats"] = get_stats()


@cli.command()
@click.option("--platform", required=True, type=click.Choice(PLATFORMS), help="Platform to configure")
@click.option("--cookie", prompt=f"Enter {PLATFORMS[0]} cookie", hide_input=True, help="Cookie string")
@click.pass_context
def cred(ctx, platform, cookie):
    """Manage credentials for each platform."""
    key = f"{platform}_cookie"
    save_cred(key, cookie)
    click.echo(f"✓ {platform} credential saved to {CRED_FILE}")


@cli.command()
@click.option("--platform", type=click.Choice(PLATFORMS), default=None, help="Show specific platform or all")
@click.pass_context
def show(ctx, platform):
    """Show configured credentials (masked)."""
    import subprocess
    result = subprocess.run(["cat", str(CRED_FILE)], capture_output=True, text=True)
    if result.returncode != 0:
        click.echo("No credentials configured yet.")
        return

    creds = json.loads(result.stdout)
    for key, val in creds.items():
        if platform and not key.startswith(platform):
            continue
        masked = val[:8] + "..." + val[-4:] if len(val) > 12 else "***"
        click.echo(f"  {key}: {masked}")


@cli.command()
@click.pass_context
def status(ctx):
    """Show archive statistics."""
    stats = get_stats()
    click.echo(f"Total records: {stats['total']}")
    for platform, types in stats["by_platform"].items():
        click.echo(f"  {platform}:")
        for ptype, count in types.items():
            click.echo(f"    {ptype}: {count}")


@cli.command()
@click.option("--platform", required=True, type=click.Choice(["netease", "bilibili"]), help="Platform for QR login")
@click.pass_context
def login(ctx, platform):
    """Login via QR code (Netease/Bilibili only)."""
    click.echo(f"\n=== {platform} 二维码登录 ===\n")

    if platform == "netease":
        result = netease_qr_login(console_display_callback=display_qr_in_terminal)
    elif platform == "bilibili":
        result = bilibili_qr_login(console_display_callback=display_qr_in_terminal)
    else:
        click.echo("该平台不支持二维码登录，请使用 cred 命令手动配置")
        return

    if result["success"]:
        save_cred(f"{platform}_cookie", result["cookie"])
        click.echo(f"\n✓ 登录成功！")
        if "nickname" in result:
            click.echo(f"  用户: {result['nickname']}")
        if "user_id" in result:
            click.echo(f"  ID: {result['user_id']}")
        click.echo(f"  Cookie 已保存到 {CRED_FILE}")
    else:
        click.echo(f"\n✗ 登录失败: {result['message']}")


@cli.command()
@click.option("--limit", default=0, help="Max records (0 = all)")
@click.pass_context
def fetch(ctx, limit):
    """Fetch data from all configured platforms."""
    ctx.invoke(fetch_douban, limit=limit)
    ctx.invoke(fetch_bilibili, limit=limit)
    ctx.invoke(fetch_netease, limit=limit)
    click.echo("\n✓ Fetch complete!")
    ctx.invoke(status)


@cli.command()
@click.option("--limit", default=0, help="Max records (0 = all)")
@click.pass_context
def fetch_douban(ctx, limit):
    """Fetch watched movies from Douban."""
    cookie = get_cred("douban_cookie")
    if not cookie:
        click.echo("✗ No Douban credential configured. Run: media-archive cred --platform douban")
        return

    click.echo("Fetching Douban watched movies...")
    records = crawl_douban_movies(cookie, limit=limit)
    if records:
        saved = save_to_db(records)
        click.echo(f"✓ Saved {saved} records from Douban")
    else:
        click.echo("  No records found or failed to fetch")


@cli.command()
@click.option("--limit", default=0, help="Max records (0 = all)")
@click.pass_context
def fetch_bilibili(ctx, limit):
    """Fetch watched anime from Bilibili."""
    cookie = get_cred("bilibili_cookie")
    if not cookie:
        click.echo("✗ No Bilibili credential configured. Run: media-archive cred --platform bilibili")
        return

    click.echo("Fetching Bilibili watched anime...")
    records = crawl_bilibili_bangumi(cookie, limit=limit)
    if records:
        saved = save_to_db(records)
        click.echo(f"✓ Saved {saved} records from Bilibili")
    else:
        click.echo("  No records found or failed to fetch")


@cli.command()
@click.option("--limit", default=0, help="Max records (0 = all)")
@click.pass_context
def fetch_netease(ctx, limit):
    """Fetch liked songs and play history from Netease."""
    cookie = get_cred("netease_cookie")
    if not cookie:
        click.echo("✗ No Netease credential configured. Run: media-archive cred --platform netease")
        return

    click.echo("Fetching Netease liked songs...")
    liked = crawl_netease_liked(cookie, limit=limit)
    if liked:
        saved = save_to_db(liked)
        click.echo(f"✓ Saved {saved} liked songs from Netease")
    else:
        click.echo("  No liked songs found or failed to fetch")

    click.echo("Fetching Netease play history...")
    history = crawl_netease_playhistory(cookie, limit=limit)
    if history:
        saved = save_to_db(history)
        click.echo(f"✓ Saved {saved} play history records from Netease")
    else:
        click.echo("  No play history found or failed to fetch")


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["json", "csv"]), default="json", help="Export format")
@click.option("--output-dir", default=None, help="Output directory")
@click.pass_context
def export(ctx, fmt, output_dir):
    """Export archive data to JSON or CSV."""
    output_path = Path(output_dir) if output_dir else DB_DIR
    if fmt == "json":
        path = export_json(output_path)
    else:
        path = export_csv(output_path)
    click.echo(f"✓ Exported to {path}")


@cli.command()
@click.option("--platform", type=click.Choice(PLATFORMS), help="Remove specific platform credential")
@click.pass_context
def clear(ctx, platform):
    """Clear credentials or specific platform."""
    if platform:
        remove_cred(f"{platform}_cookie")
        click.echo(f"✓ Removed {platform} credential")
    else:
        from media_archive import CRED_FILE
        if CRED_FILE.exists():
            CRED_FILE.unlink()
            click.echo(f"✓ Cleared all credentials")
        else:
            click.echo("No credentials to clear")


def main():
    cli()
