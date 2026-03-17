"""
抖音视频发布模块 (基于 PinchTab)
"""

import os
import subprocess
import time
from typing import Optional


def navigate_to_upload() -> bool:
    """导航到上传页面"""
    try:
        subprocess.run(
            ["pinchtab", "nav", "https://creator.douyin.com/creator-micro/content/upload"],
            capture_output=True,
            timeout=30
        )
        time.sleep(3)
        return True
    except Exception as e:
        print(f"导航失败: {e}")
        return False


def get_page_elements() -> dict:
    """获取页面元素"""
    result = subprocess.run(
        ["pinchtab", "snap", "-i"],
        capture_output=True,
        text=True,
        timeout=15
    )

    try:
        import json
        data = json.loads(result.stdout)
        nodes = data.get("nodes", [])

        elements = {}
        for node in nodes:
            name = node.get("name", "")
            ref = node.get("ref", "")

            if "选择文件" in name or "上传" in name:
                elements["upload_btn"] = ref
            elif "发布" in name:
                elements["publish_btn"] = ref
            elif "标题" in name:
                elements["title_input"] = ref

        return elements
    except Exception as e:
        print(f"解析页面元素失败: {e}")
        return {}


def upload_video(video_path: str) -> bool:
    """上传视频文件"""
    if not os.path.exists(video_path):
        print(f"视频文件不存在: {video_path}")
        return False

    abs_path = os.path.abspath(video_path)

    try:
        result = subprocess.run(
            ["pinchtab", "upload", abs_path, "--selector", "input[type=file]"],
            capture_output=True,
            text=True,
            timeout=60
        )
        print(f"上传命令输出: {result.stdout}")
        return result.returncode == 0
    except Exception as e:
        print(f"上传失败: {e}")
        return False


def fill_title(title: str) -> bool:
    """填写视频标题"""
    try:
        result = subprocess.run(
            ["pinchtab", "snap", "-i"],
            capture_output=True,
            text=True,
            timeout=15
        )

        import json
        data = json.loads(result.stdout)
        nodes = data.get("nodes", [])

        title_ref = None
        for node in nodes:
            if "标题" in node.get("name", "") or "描述" in node.get("name", ""):
                title_ref = node.get("ref")
                break

        if not title_ref:
            print("未找到标题输入框")
            return False

        subprocess.run(
            ["pinchtab", "fill", title_ref, title],
            capture_output=True,
            timeout=15
        )
        return True
    except Exception as e:
        print(f"填写标题失败: {e}")
        return False


def click_publish() -> bool:
    """点击发布按钮"""
    try:
        result = subprocess.run(
            ["pinchtab", "snap", "-i"],
            capture_output=True,
            text=True,
            timeout=15
        )

        import json
        data = json.loads(result.stdout)
        nodes = data.get("nodes", [])

        publish_ref = None
        for node in nodes:
            if "发布" in node.get("name", ""):
                publish_ref = node.get("ref")
                break

        if not publish_ref:
            print("未找到发布按钮")
            return False

        subprocess.run(
            ["pinchtab", "click", publish_ref],
            capture_output=True,
            timeout=15
        )
        time.sleep(5)
        return True
    except Exception as e:
        print(f"点击发布按钮失败: {e}")
        return False


def wait_for_upload_complete(timeout: int = 300) -> bool:
    """等待视频上传完成"""
    print("[发布] 等待视频上传完成...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        result = subprocess.run(
            ["pinchtab", "text"],
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout

        if "上传成功" in output or "发布成功" in output:
            print("[发布] 视频上传完成")
            return True

        if "发布" in output and "选择文件" not in output:
            return True

        time.sleep(5)

    return False


def publish_video(video_path: str, title: str = "") -> dict:
    """发布视频的完整流程"""
    print(f"[发布] 开始发布视频: {video_path}")

    if not navigate_to_upload():
        return {"success": False, "message": "导航到上传页面失败"}

    print("[发布] 上传视频中...")
    if not upload_video(video_path):
        return {"success": False, "message": "视频上传失败"}

    if not wait_for_upload_complete():
        return {"success": False, "message": "等待上传超时"}

    if title:
        print(f"[发布] 填写标题: {title}")
        fill_title(title)

    print("[发布] 点击发布按钮...")
    if not click_publish():
        return {"success": False, "message": "点击发布按钮失败"}

    return {"success": True, "message": "发布成功"}