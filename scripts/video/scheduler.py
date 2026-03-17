"""
定时任务调度模块
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

STORAGE_DIR = Path.home() / ".douyin-pusher"
SCHEDULE_FILE = STORAGE_DIR / "schedule.json"


def load_schedule() -> dict:
    """加载定时任务"""
    if not SCHEDULE_FILE.exists():
        return {}
    with open(SCHEDULE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_schedule(data: dict) -> None:
    """保存定时任务"""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def schedule_task(video_path: str, time_str: str, title: str = "") -> str:
    """创建定时发布任务"""
    try:
        # 解析时间
        schedule_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            # 尝试简化的日期格式
            schedule_time = datetime.strptime(time_str, "%Y-%m-%d")
            schedule_time = schedule_time.replace(hour=12, minute=0)
        except ValueError:
            raise ValueError(f"时间格式错误，请使用 YYYY-MM-DD HH:MM 格式")

    if schedule_time <= datetime.now():
        raise ValueError("定时发布时间必须晚于当前时间")

    task_id = str(uuid.uuid4())[:8]

    schedule = load_schedule()
    schedule[task_id] = {
        "video_path": video_path,
        "title": title,
        "schedule_time": schedule_time.isoformat(),
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    save_schedule(schedule)

    return task_id


def cancel_task(task_id: str) -> bool:
    """取消定时任务"""
    schedule = load_schedule()
    if task_id in schedule:
        del schedule[task_id]
        save_schedule(schedule)
        return True
    return False


def list_tasks() -> List[dict]:
    """列出所有定时任务"""
    schedule = load_schedule()
    return [
        {
            "id": task_id,
            "video": data.get("video_path", ""),
            "time": data.get("schedule_time", ""),
            "status": data.get("status", "pending"),
        }
        for task_id, data in schedule.items()
    ]


def get_pending_tasks() -> List[dict]:
    """获取待执行的定时任务"""
    schedule = load_schedule()
    now = datetime.now()
    pending = []

    for task_id, data in schedule.items():
        if data.get("status") != "pending":
            continue
        schedule_time = datetime.fromisoformat(data["schedule_time"])
        if schedule_time <= now:
            pending.append({"task_id": task_id, **data})

    return pending


def mark_executed(task_id: str) -> None:
    """标记任务已执行"""
    schedule = load_schedule()
    if task_id in schedule:
        schedule[task_id]["status"] = "executed"
        schedule[task_id]["executed_at"] = datetime.now().isoformat()
        save_schedule(schedule)


def run_pending_tasks():
    """执行待处理的定时任务"""
    from douyin.publish import publish_video

    pending = get_pending_tasks()
    for task in pending:
        try:
            video_path = task["video_path"]
            title = task.get("title", "")
            result = publish_video(video_path, title)
            if result.get("success"):
                mark_executed(task["task_id"])
                print(f"✅ 定时任务 {task['task_id']} 执行成功")
            else:
                print(f"❌ 定时任务 {task['task_id']} 执行失败: {result.get('message')}")
        except Exception as e:
            print(f"❌ 定时任务 {task['task_id']} 执行异常: {e}")