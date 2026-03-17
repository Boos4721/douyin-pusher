"""
抖音登录模块 (基于 PinchTab)
"""

import time
from pathlib import Path
from typing import Optional

COOKIE_DIR = Path.home() / ".douyin-pusher" / "cookies"
COOKIE_DIR.mkdir(parents=True, exist_ok=True)


def get_cookie_path(account: str = "default") -> Path:
    return COOKIE_DIR / f"{account}.json"


def check_login_via_pincli() -> dict:
    """通过 pinchtab CLI 检查登录状态"""
    import subprocess

    try:
        result = subprocess.run(
            ["pinchtab", "nav", "https://creator.douyin.com/creator-micro/home"],
            capture_output=True,
            text=True,
            timeout=30
        )
        time.sleep(3)

        result = subprocess.run(
            ["pinchtab", "text"],
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout
        if "扫码登录" in output or "登录" in output:
            return {"logged_in": False, "user": None}

        return {"logged_in": True, "user": {"nickname": "已登录用户"}}
    except Exception as e:
        return {"logged_in": False, "user": None, "error": str(e)}


def get_qrcode_screenshot() -> Optional[str]:
    """获取二维码截图并保存"""
    import subprocess

    try:
        result = subprocess.run(
            ["pinchtab", "screenshot", "-o", str(COOKIE_DIR / "qrcode.png")],
            capture_output=True,
            text=True,
            timeout=15
        )
        qr_path = COOKIE_DIR / "qrcode.png"
        if qr_path.exists():
            return str(qr_path)
        return None
    except Exception as e:
        print(f"Failed to capture QR code: {e}")
        return None


def wait_for_login(timeout: int = 120) -> dict:
    """等待用户扫码登录"""
    import subprocess

    print("[登录] 等待用户扫码登录...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        result = subprocess.run(
            ["pinchtab", "text"],
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout
        if "扫码登录" not in output and "登录" not in output:
            print("[登录] 登录成功!")
            return {"success": True, "message": "Login successful"}

        time.sleep(3)

    return {"success": False, "message": f"Login timeout ({timeout}s)"}


def login_with_qrcode() -> dict:
    """扫码登录流程"""
    import subprocess

    print("[登录] 导航到抖音创作者中心...")
    subprocess.run(
        ["pinchtab", "nav", "https://creator.douyin.com/"],
        capture_output=True,
        timeout=30
    )
    time.sleep(3)

    qr_path = get_qrcode_screenshot()
    if qr_path:
        print(f"[登录] 二维码已保存到: {qr_path}")
        print("[登录] 请使用抖音APP扫码登录...")
    else:
        print("[登录] 警告: 未能获取二维码截图")

    result = wait_for_login()
    return result


def check_and_login() -> dict:
    """检查登录状态，如果未登录则进行扫码登录"""
    print("[登录] 检查抖音登录状态...")

    status = check_login_via_pincli()

    if status.get("logged_in"):
        print("[登录] 已登录")
        return {"success": True, "message": "Already logged in", "user": status.get("user")}

    print("[登录] 未登录，开始扫码登录流程...")
    return login_with_qrcode()