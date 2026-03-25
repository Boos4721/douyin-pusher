"""
任务存储模块 - 支持 JSON 和 SQLite 存储
"""
from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from dy_cli.utils.config import CONFIG_DIR, load_config


@dataclass
class VideoJob:
    """视频生成任务"""
    id: str
    backend: str  # jimeng / seedance / sora
    model: str
    prompt: str
    status: str  # pending, generating, generated, publishing, published, failed, scheduled
    optimized_prompt: Optional[str] = None
    generated_video_path: Optional[str] = None
    generated_video_url: Optional[str] = None
    schedule_time: Optional[str] = None
    douyin_aweme_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None


class StorageAdapter(Protocol):
    """存储适配器协议"""

    def save_job(self, job: VideoJob) -> None: ...
    def load_job(self, job_id: str) -> Optional[VideoJob]: ...
    def load_jobs(self) -> Dict[str, Dict[str, Any]]: ...
    def delete_job(self, job_id: str) -> bool: ...


def _get_storage_dir() -> Path:
    """获取存储目录"""
    config = load_config()
    storage_dir = config.get("storage", {}).get("dir", "~/.dy")
    return Path(os.path.expanduser(storage_dir))


class JsonStorageAdapter:
    """JSON 存储适配器"""

    def __init__(self):
        self._lock = threading.Lock()
        self._storage_dir = _get_storage_dir()
        self._jobs_path = self._storage_dir / "video_jobs.json"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        if not self._jobs_path.exists():
            self._write_json(self._jobs_path, {})

    def _read_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with self._lock:
            with open(path, encoding="utf-8") as f:
                return json.load(f)

    def _write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        with self._lock:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

    def save_job(self, job: VideoJob) -> None:
        jobs = self.load_jobs()
        job.updated_at = datetime.now().isoformat()
        if job.status in ("generated", "published", "failed") and not job.completed_at:
            job.completed_at = job.updated_at
        jobs[job.id] = asdict(job)
        self._write_json(self._jobs_path, jobs)

    def load_job(self, job_id: str) -> Optional[VideoJob]:
        jobs = self.load_jobs()
        if job_id not in jobs:
            return None
        return VideoJob(**jobs[job_id])

    def load_jobs(self) -> Dict[str, Dict[str, Any]]:
        return self._read_json(self._jobs_path)

    def delete_job(self, job_id: str) -> bool:
        jobs = self.load_jobs()
        if job_id not in jobs:
            return False
        del jobs[job_id]
        self._write_json(self._jobs_path, jobs)
        return True

    def list_jobs(self, status: Optional[str] = None, limit: int = 50) -> List[VideoJob]:
        jobs = self.load_jobs()
        result = []
        for job_data in jobs.values():
            if status and job_data.get("status") != status:
                continue
            result.append(VideoJob(**job_data))
        result.sort(key=lambda x: x.created_at, reverse=True)
        return result[:limit]

    def update_job(self, job_id: str, **updates: Any) -> Optional[VideoJob]:
        job = self.load_job(job_id)
        if not job:
            return None
        for key, value in updates.items():
            if hasattr(job, key):
                setattr(job, key, value)
        self.save_job(job)
        return job


class SQLiteStorageAdapter:
    """SQLite 存储适配器 (预留)"""

    def _unsupported(self):
        raise NotImplementedError("SQLite backend is reserved and not implemented yet.")

    def save_job(self, job: VideoJob) -> None:
        self._unsupported()

    def load_job(self, job_id: str) -> Optional[VideoJob]:
        self._unsupported()

    def load_jobs(self) -> Dict[str, Dict[str, Any]]:
        self._unsupported()

    def delete_job(self, job_id: str) -> bool:
        self._unsupported()


class Storage:
    """存储门面类"""

    def __init__(self):
        config = load_config()
        backend = config.get("storage", {}).get("type", "json")
        if backend == "sqlite":
            self.adapter: StorageAdapter = SQLiteStorageAdapter()
        else:
            self.adapter = JsonStorageAdapter()

    def save_job(self, job: VideoJob) -> None:
        self.adapter.save_job(job)

    def load_job(self, job_id: str) -> Optional[VideoJob]:
        return self.adapter.load_job(job_id)

    def load_jobs(self) -> Dict[str, Dict[str, Any]]:
        return self.adapter.load_jobs()

    def delete_job(self, job_id: str) -> bool:
        return self.adapter.delete_job(job_id)

    def list_jobs(self, status: Optional[str] = None, limit: int = 50) -> List[VideoJob]:
        if isinstance(self.adapter, JsonStorageAdapter):
            return self.adapter.list_jobs(status=status, limit=limit)
        return []

    def update_job(self, job_id: str, **updates: Any) -> Optional[VideoJob]:
        if isinstance(self.adapter, JsonStorageAdapter):
            return self.adapter.update_job(job_id, **updates)
        return None

    # 评论相关方法
    def load_comments(self) -> Dict[str, Dict[str, Any]]:
        """加载所有评论"""
        return {}

    def mark_replied(self, comment_id: str, reply_text: str) -> bool:
        """标记评论已回复"""
        return True


_default_storage: Optional[Storage] = None


def get_storage() -> Storage:
    """获取默认存储实例"""
    global _default_storage
    if _default_storage is None:
        _default_storage = Storage()
    return _default_storage