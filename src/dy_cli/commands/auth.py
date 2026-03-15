"""
dy login / logout / status — 认证命令。

支持两种登录方式:
1. 浏览器 Cookie 自动提取 (默认, 零摩擦)
2. Playwright 扫码 (--qrcode)
"""
from __future__ import annotations

import json
import os

import click

from dy_cli.engines.playwright_client import PlaywrightClient, PlaywrightError
from dy_cli.utils import config
from dy_cli.utils.output import success, error, info, warning, status, console


def _extract_browser_cookies(account: str | None = None) -> bool:
    """从浏览器自动提取抖音 Cookie。"""
    try:
        import browser_cookie3 as bc3
    except ImportError:
        return False

    browsers = ["chrome", "firefox", "edge", "brave", "opera", "chromium", "safari"]
    for browser_name in browsers:
        loader = getattr(bc3, browser_name, None)
        if not loader:
            continue
        try:
            jar = loader(domain_name=".douyin.com")
            cookies = {c.name: c.value for c in jar if "douyin" in (c.domain or "")}
            if cookies and any(k in cookies for k in ("sessionid", "passport_csrf_token", "ttwid")):
                # Save as playwright storage_state format
                cookie_file = config.get_cookie_file(account)
                os.makedirs(os.path.dirname(cookie_file), exist_ok=True)
                storage = {
                    "cookies": [
                        {"name": k, "value": v, "domain": ".douyin.com", "path": "/"}
                        for k, v in cookies.items()
                    ],
                    "origins": [],
                }
                with open(cookie_file, "w", encoding="utf-8") as f:
                    json.dump(storage, f, ensure_ascii=False, indent=2)
                info(f"从 {browser_name} 提取了 {len(cookies)} 个 cookie")
                return True
        except Exception:
            continue
    return False


@click.command("login", help="登录抖音 (自动提取浏览器 Cookie 或扫码)")
@click.option("--account", default=None, help="账号名")
@click.option("--qrcode", is_flag=True, help="强制使用扫码登录 (Playwright)")
@click.option("--cookie-source", default="auto", help="指定浏览器 (chrome/firefox/safari/auto)")
def login(account, qrcode, cookie_source):
    """登录抖音。默认从浏览器提取 Cookie，--qrcode 使用扫码。"""
    cfg = config.load_config()

    # 已登录检查
    client = PlaywrightClient(account=account, headless=True)
    if client.cookie_exists() and client.check_login():
        success("已登录抖音")
        if not click.confirm("是否重新登录?", default=False):
            return

    # 方式 1: 从浏览器自动提取 Cookie (无需打开浏览器)
    if not qrcode:
        info("正在从浏览器提取 Cookie...")
        if _extract_browser_cookies(account):
            # Verify
            client2 = PlaywrightClient(account=account, headless=True)
            if client2.check_login():
                success("登录成功! 🎉 (从浏览器提取)")
                return
            else:
                warning("提取的 Cookie 无效，切换到扫码模式")

    # 方式 2: Playwright 扫码
    info("正在打开浏览器，请使用抖音 App 扫码...")
    pw_client = PlaywrightClient(
        account=account,
        headless=False,
        slow_mo=cfg["playwright"].get("slow_mo", 0),
    )
    try:
        ok = pw_client.login()
        if ok:
            success("登录成功! 🎉")
        else:
            error("登录超时或失败")
            raise SystemExit(1)
    except PlaywrightError as e:
        error(f"登录失败: {e}")
        raise SystemExit(1)


@click.command("logout", help="退出登录")
@click.option("--account", default=None, help="账号名")
def logout(account):
    """退出登录（删除 Cookie）。"""
    client = PlaywrightClient(account=account)
    if client.logout():
        success("已退出登录，Cookie 已删除")
    else:
        info("未找到登录凭据")


@click.command("status", help="查看登录状态")
@click.option("--account", default=None, help="账号名")
def auth_status(account):
    """检查登录状态。"""
    console.print()
    client = PlaywrightClient(account=account)

    if not client.cookie_exists():
        status("登录状态", "未登录 (无 Cookie 文件)", "red")
        info("使用 [bold]dy login[/] 登录")
    else:
        info("正在验证 Cookie...")
        try:
            logged_in = client.check_login()
            if logged_in:
                status("登录状态", "已登录", "green")
                status("Cookie", client.cookie_file, "dim")
            else:
                status("登录状态", "Cookie 已失效", "yellow")
                info("使用 [bold]dy login[/] 重新登录")
        except Exception as e:
            status("登录状态", f"检查失败: {e}", "red")

    console.print()
