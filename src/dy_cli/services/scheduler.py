"""
定时发布服务
"""
from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from dy_cli.services.storage import VideoJob, get_storage
from dy_cli.utils.config import load_config


def _get_schedule_file() -> Path:
    """获取定时任务文件路径"""
    config = load_config()
    storage_dir = config.get("storage", {}).get("dir", "~/.dy")
    storage_path = Path(os.path.expanduser(storage_dir))
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path / "schedule.json"


def load_schedule() -> dict:
    """加载定时任务"""
    schedule_file = _get_schedule_file()
    if not schedule_file.exists():
        return {}
    with open(schedule_file, encoding="utf-8") as f:
        return json.load(f)


def save_schedule(data: dict) -> None:
    """保存定时任务"""
    schedule_file = _get_schedule_file()
    with open(schedule_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _parse_time(time_str: str) -> datetime:
    """解析时间字符串"""
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%d")
            return dt.replace(hour=12, minute=0)
        except ValueError as exc:
            raise ValueError("时间格式错误，请使用 YYYY-MM-DD HH:MM") from exc


def schedule_job(
    job_id: str,
    schedule_time: str,
    title: str = "",
    description: str = "",
) -> str:
    """定时发布任务"""
    schedule_datetime = _parse_time(schedule_time)

    if schedule_datetime <= datetime.now():
        raise ValueError("定时发布时间必须晚于当前时间")

    schedule_id = str(uuid.uuid4())[:8]
    schedule = load_schedule()

    schedule[schedule_id] = {
        "job_id": job_id,
        "schedule_time": schedule_datetime.isoformat(),
        "next_run_at": schedule_datetime.isoformat(),
        "status": "pending",
        "attempts": 0,
        "max_retries": 2,
        "title": title,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "last_error": "",
    }

    save_schedule(schedule)

    # 更新任务状态
    storage = get_storage()
    storage.update_job(
        job_id,
        status="scheduled",
        schedule_time=schedule_datetime.isoformat(),
    )

    return schedule_id


def cancel_schedule(schedule_id: str) -> bool:
    """取消定时任务"""
    schedule = load_schedule()
    if schedule_id not in schedule:
        return False

    job_id = schedule[schedule_id].get("job_id")
    del schedule[schedule_id]
    save_schedule(schedule)

    if job_id:
        storage = get_storage()
        storage.update_job(job_id, status="pending", schedule_time=None)

    return True


def list_schedules() -> List[dict]:
    """列出所有定时任务"""
    schedule = load_schedule()
    rows = []
    for schedule_id, data in schedule.items():
        rows.append({
            "id": schedule_id,
            "job_id": data.get("job_id"),
            "title": data.get("title", ""),
            "schedule_time": data.get("schedule_time", ""),
            "status": data.get("status", "pending"),
            "attempts": data.get("attempts", 0),
            "last_error": data.get("last_error", ""),
        })
    return rows


def _get_due_tasks() -> List[dict]:
    """获取到期的任务"""
    schedule = load_schedule()
    now = datetime.now()
    due = []

    for schedule_id, data in schedule.items():
        if data.get("status") not in {"pending", "retrying"}:
            continue
        next_run = data.get("next_run_at") or data.get("schedule_time")
        if datetime.fromisoformat(next_run) <= now:
            due.append({"schedule_id": schedule_id, **data})

    return due


def _mark_success(schedule_id: str) -> None:
    """标记任务成功"""
    schedule = load_schedule()
    if schedule_id not in schedule:
        return

    schedule[schedule_id]["status"] = "executed"
    schedule[schedule_id]["executed_at"] = datetime.now().isoformat()
    schedule[schedule_id]["updated_at"] = datetime.now().isoformat()
    save_schedule(schedule)

    job_id = schedule[schedule_id].get("job_id")
    if job_id:
        storage = get_storage()
        storage.update_job(job_id, status="published")


def _mark_failure(schedule_id: str, message: str) -> None:
    """标记任务失败"""
    schedule = load_schedule()
    if schedule_id not in schedule:
        return

    task = schedule[schedule_id]
    attempts = int(task.get("attempts", 0)) + 1
    max_retries = int(task.get("max_retries", 2))

    task["attempts"] = attempts
    task["last_error"] = message
    task["updated_at"] = datetime.now().isoformat()

    if attempts > max_retries:
        task["status"] = "failed"
    else:
        task["status"] = "retrying"
        delay_minutes = 2 ** min(attempts, 4)
        task["next_run_at"] = (datetime.now() + timedelta(minutes=delay_minutes)).isoformat()

    save_schedule(schedule)

    job_id = task.get("job_id")
    if job_id:
        storage = get_storage()
        storage.update_job(
            job_id,
            status="failed" if attempts > max_retries else "scheduled",
            error=message,
        )


def run_pending_tasks() -> None:
    """执行到期的定时任务"""
    from dy_cli.commands.publish import publish

    due_tasks = _get_due_tasks()

    for task in due_tasks:
        schedule_id = task["schedule_id"]
        job_id = task.get("job_id")

        if not job_id:
            _mark_failure(schedule_id, "No job_id found")
            continue

        try:
            storage = get_storage()
            job = storage.load_job(job_id)

            if not job:
                _mark_failure(schedule_id, f"Job not found: {job_id}")
                continue

            video_path = job.generated_video_path
            if not video_path or not os.path.exists(video_path):
                _mark_failure(schedule_id, f"Video file not found: {video_path}")
                continue

            # 发布视频
            result = publish(
                video_path,
                task.get("title", ""),
                description=task.get("description", ""),
            )

            if result.get("success"):
                _mark_success(schedule_id)
                # 更新 job 的 aweme_id
                aweme_id = result.get("aweme_id")
                if aweme_id:
                    storage.update_job(job_id, douyin_aweme_id=aweme_id)
                print(f"定时任务 {schedule_id} 发布成功")
            else:
                _mark_failure(schedule_id, result.get("message", "publish failed"))
                print(f"定时任务 {schedule_id} 发布失败")

        except Exception as exc:
            _mark_failure(schedule_id, str(exc))
            print(f"定时任务 {schedule_id} 异常: {exc}")


def run_scheduler_loop(interval_seconds: int = 30) -> None:
    """调度器循环"""
    print(f"调度器启动，轮询间隔 {interval_seconds}s")
    while True:
        run_pending_tasks()
        time.sleep(interval_seconds)