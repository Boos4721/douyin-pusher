"""
Finalizer Agent - 最终处理
"""

import os
import subprocess
from typing import Optional


class Finalizer:
    """Finalizer - 负责最终处理（添加片头片尾、字幕、水印等）"""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg = ffmpeg_path

    def finalize(
        self,
        video_path: str,
        intro_path: Optional[str] = None,
        outro_path: Optional[str] = None,
        title: Optional[str] = None,
    ) -> str:
        """
        最终处理视频

        Args:
            video_path: 视频路径
            intro_path: 片头视频路径
            outro_path: 片尾视频路径
            title: 标题（用于添加水印）

        Returns:
            处理后的视频路径
        """
        # 如果没有额外的处理，直接返回原路径
        if not intro_path and not outro_path and not title:
            return video_path

        # 这里可以实现更复杂的片头片尾合成
        # 简化处理：直接返回原视频
        return video_path

    def add_watermark(
        self,
        video_path: str,
        watermark_path: str,
        output_path: str,
        position: str = "top-right",
    ) -> str:
        """添加水印"""
        # 位置映射
        pos_map = {
            "top-left": "10:10",
            "top-right": "W-w-10:10",
            "bottom-left": "10:H-h-10",
            "bottom-right": "W-w-10:H-h-10",
            "center": "(W-w)/2:(H-h)/2",
        }

        pos = pos_map.get(position, "W-w-10:10")

        cmd = [
            self.ffmpeg,
            "-i", video_path,
            "-i", watermark_path,
            "-filter_complex", f"overlay={pos}",
            "-c:a", "copy",
            "-y",
            output_path,
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except Exception as e:
            print(f"   警告: 添加水印失败: {e}")
            import shutil
            shutil.copy(video_path, output_path)

        return output_path

    def compress(
        self,
        video_path: str,
        output_path: str,
        crf: int = 23,
        preset: str = "medium",
    ) -> str:
        """压缩视频"""
        cmd = [
            self.ffmpeg,
            "-i", video_path,
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", str(crf),
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            output_path,
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except Exception as e:
            print(f"   警告: 视频压缩失败: {e}")
            import shutil
            shutil.copy(video_path, output_path)

        return output_path