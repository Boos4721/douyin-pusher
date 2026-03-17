"""
Video Editor Agent - 视频剪辑
"""

import os
import subprocess
from typing import List


class VideoEditor:
    """Video Editor - 负责视频剪辑和合成"""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg = ffmpeg_path

    def concat_videos(self, video_paths: List[str], output_path: str) -> str:
        """
        合并多个视频

        Args:
            video_paths: 视频文件路径列表
            output_path: 输出文件路径

        Returns:
            输出文件路径
        """
        if not video_paths:
            raise ValueError("没有视频文件可合并")

        if len(video_paths) == 1:
            # 只有一个视频，直接复制
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            import shutil
            shutil.copy(video_paths[0], output_path)
            return output_path

        # 创建临时文件列表
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        list_file = output_path + ".txt"

        with open(list_file, "w") as f:
            for path in video_paths:
                if os.path.exists(path):
                    f.write(f"file '{os.path.abspath(path)}'\n")

        # 使用 ffmpeg 合并
        cmd = [
            self.ffmpeg,
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            "-y",
            output_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                print(f"   警告: ffmpeg 合并失败: {result.stderr}")
                # 降级：复制第一个视频
                import shutil
                shutil.copy(video_paths[0], output_path)
        except FileNotFoundError:
            print("   警告: ffmpeg 未安装，复制第一个视频作为输出")
            import shutil
            shutil.copy(video_paths[0], output_path)
        except Exception as e:
            print(f"   警告: 视频合并失败: {e}")
            import shutil
            shutil.copy(video_paths[0], output_path)
        finally:
            # 清理临时文件
            if os.path.exists(list_file):
                os.remove(list_file)

        return output_path

    def add_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        fade_in: int = 0,
        fade_out: int = 0,
    ) -> str:
        """添加音频"""
        cmd = [
            self.ffmpeg,
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            "-y",
            output_path,
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except Exception as e:
            print(f"   警告: 添加音频失败: {e}")

        return output_path

    def add_subtitle(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str,
    ) -> str:
        """添加字幕"""
        cmd = [
            self.ffmpeg,
            "-i", video_path,
            "-vf", f"subtitles='{subtitle_path}'",
            "-c:a", "copy",
            "-y",
            output_path,
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except Exception as e:
            print(f"   警告: 添加字幕失败: {e}")

        return output_path