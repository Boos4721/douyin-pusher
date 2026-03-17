"""
Video Generator Agent - 生成视频
"""

from typing import Optional

from ...generator import VideoGenerator


class VideoGenerator:
    """Video Generator - 负责调用统一视频生成器生成视频"""

    def __init__(self, model: str = "auto", **kwargs):
        # 使用项目统一的 VideoGenerator
        self._generator = VideoGenerator(model=model, **kwargs)

    def generate(
        self,
        prompt: str,
        image: Optional[str] = None,
        duration: int = 5,
        aspect_ratio: str = "16:9",
    ) -> str:
        """生成视频并返回视频 URL"""
        return self._generator.generate(
            prompt=prompt,
            image=image,
            duration=duration,
            aspect_ratio=aspect_ratio,
        )

    def poll(self, task_id: str, interval: int = 15, timeout: int = 900) -> str:
        """轮询任务状态"""
        return self._generator.poll(task_id, interval, timeout)

    def download(self, url: str, filename: str = "output.mp4") -> str:
        """下载视频"""
        return self._generator.download(url, filename)

    def generate_and_download(
        self,
        prompt: str,
        image: Optional[str] = None,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        output: str = "output.mp4",
    ) -> str:
        """生成视频并下载"""
        task_id = self.generate(prompt, image, duration, aspect_ratio)
        video_url = self.poll(task_id)
        return self.download(video_url, output)