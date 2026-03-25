"""
视频后端统一接口定义
"""
from typing import Protocol, Optional


class VideoBackend(Protocol):
    """视频生成后端协议"""

    def generate(self, prompt: str, model: str, **opts) -> str:
        """
        提交视频生成任务
        返回: task_id
        """
        ...

    def poll(self, task_id: str, interval: int = 10, timeout: int = 600) -> str:
        """
        轮询任务状态
        返回: video_url
        """
        ...

    def download(self, url: str, path: str) -> str:
        """
        下载视频到本地
        返回: local_path
        """
        ...


def get_backend(backend: str) -> VideoBackend:
    """获取视频后端实例"""
    backend = backend.lower()
    if backend == "jimeng":
        from dy_cli.video_backends.jimeng import JimengBackend
        return JimengBackend()
    elif backend == "seedance":
        from dy_cli.video_backends.seedance import SeedanceAPIBackend
        return SeedanceAPIBackend()
    elif backend == "xyq":
        from dy_cli.video_backends.xyq import XyqBackend
        return XyqBackend()
    elif backend == "sora":
        from dy_cli.video_backends.sora import SoraBackend
        return SoraBackend()
    else:
        raise ValueError(f"Unknown backend: {backend}")


# 支持的后端列表
BACKENDS = ["jimeng", "seedance", "xyq", "sora"]

# 后端对应的模型
# jimeng: 即梦AI网页版
# seedance: 即梦API (火山引擎)
# xyq: 小云雀网页版
# sora: Atlas Sora API
BACKEND_MODELS = {
    "jimeng": ["seedance-2.0", "seedance-2.0-fast"],      # 即梦AI网页版
    "seedance": ["jimeng-pro", "jimeng-720p", "jimeng-1080p"],  # 即梦API
    "xyq": ["seedance-2.0", "seedance-2.0-fast"],         # 小云雀
    "sora": ["sora-2"],
}