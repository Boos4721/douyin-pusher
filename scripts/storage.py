"""
本地存储模块 - Cookie、任务、评论持久化
"""

import json
import os
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# 存储目录
STORAGE_DIR = Path.home() / ".sora2-pusher"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Task:
    """视频生成任务"""
    id: str
    prompt: str
    model: str
    status: str  # pending, running, completed, failed
    video_url: Optional[str] = None
    local_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Comment:
    """评论"""
    id: str
    video_id: str
    user: str
    text: str
    timestamp: str
    replied: bool = False
    reply_text: Optional[str] = None


class Storage:
    """本地存储类"""

    def __init__(self, name: str = "default"):
        self.name = name
        self._lock = threading.Lock()
        self._cookies_path = STORAGE_DIR / "cookies" / f"{name}.json"
        self._tasks_path = STORAGE_DIR / "tasks.json"
        self._comments_path = STORAGE_DIR / "comments.json"
        self._comments_path.parent.mkdir(parents=True, exist_ok=True)

    # ========== Cookie 管理 ==========

    def save_cookies(self, cookies: Dict[str, Any]) -> None:
        """保存 Cookie"""
        self._cookies_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._cookies_path, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

    def load_cookies(self) -> Optional[Dict[str, Any]]:
        """加载 Cookie"""
        if not self._cookies_path.exists():
            return None
        with self._lock:
            with open(self._cookies_path, encoding="utf-8") as f:
                return json.load(f)

    def delete_cookies(self) -> None:
        """删除 Cookie"""
        with self._lock:
            if self._cookies_path.exists():
                self._cookies_path.unlink()

    # ========== 任务管理 ==========

    def save_task(self, task: Task) -> None:
        """保存任务"""
        tasks = self.load_tasks()
        tasks[task.id] = asdict(task)
        with self._lock:
            with open(self._tasks_path, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)

    def load_task(self, task_id: str) -> Optional[Task]:
        """加载任务"""
        tasks = self.load_tasks()
        if task_id not in tasks:
            return None
        return Task(**tasks[task_id])

    def load_tasks(self) -> Dict[str, Dict]:
        """加载所有任务"""
        if not self._tasks_path.exists():
            return {}
        with self._lock:
            with open(self._tasks_path, encoding="utf-8") as f:
                return json.load(f)

    def list_tasks(self, status: Optional[str] = None, limit: int = 50) -> List[Task]:
        """列出任务"""
        tasks = self.load_tasks()
        result = []
        for task_data in tasks.values():
            if status and task_data.get("status") != status:
                continue
            result.append(Task(**task_data))
        result.sort(key=lambda x: x.created_at, reverse=True)
        return result[:limit]

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        tasks = self.load_tasks()
        if task_id in tasks:
            del tasks[task_id]
            with self._lock:
                with open(self._tasks_path, "w", encoding="utf-8") as f:
                    json.dump(tasks, f, ensure_ascii=False, indent=2)
            return True
        return False

    # ========== 评论管理 ==========

    def save_comment(self, comment: Comment) -> None:
        """保存评论"""
        comments = self.load_comments()
        comments[comment.id] = asdict(comment)
        with self._lock:
            with open(self._comments_path, "w", encoding="utf-8") as f:
                json.dump(comments, f, ensure_ascii=False, indent=2)

    def load_comment(self, comment_id: str) -> Optional[Comment]:
        """加载评论"""
        comments = self.load_comments()
        if comment_id not in comments:
            return None
        return Comment(**comments[comment_id])

    def load_comments(self) -> Dict[str, Dict]:
        """加载所有评论"""
        if not self._comments_path.exists():
            return {}
        with self._lock:
            with open(self._comments_path, encoding="utf-8") as f:
                return json.load(f)

    def list_comments(self, video_id: Optional[str] = None, replied: Optional[bool] = None, limit: int = 50) -> List[Comment]:
        """列出评论"""
        comments = self.load_comments()
        result = []
        for comment_data in comments.values():
            if video_id and comment_data.get("video_id") != video_id:
                continue
            if replied is not None and comment_data.get("replied") != replied:
                continue
            result.append(Comment(**comment_data))
        result.sort(key=lambda x: x.timestamp, reverse=True)
        return result[:limit]

    def mark_replied(self, comment_id: str, reply_text: str) -> bool:
        """标记评论已回复"""
        comments = self.load_comments()
        if comment_id not in comments:
            return False
        comments[comment_id]["replied"] = True
        comments[comment_id]["reply_text"] = reply_text
        with self._lock:
            with open(self._comments_path, "w", encoding="utf-8") as f:
                json.dump(comments, f, ensure_ascii=False, indent=2)
        return True


# 全局存储实例
_default_storage: Optional[Storage] = None


def get_storage(name: str = "default") -> Storage:
    """获取存储实例"""
    global _default_storage
    if _default_storage is None or _default_storage.name != name:
        _default_storage = Storage(name)
    return _default_storage