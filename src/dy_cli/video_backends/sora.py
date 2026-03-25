"""
Atlas Cloud Sora 视频生成后端
"""
import os
import time
from typing import Optional

import requests

from dy_cli.utils.config import load_config


class SoraBackend:
    """Atlas Cloud Sora 视频生成后端"""

    def __init__(self):
        config = load_config()
        sora_cfg = config.get("video_backends", {}).get("sora", {})

        api_key_env = sora_cfg.get("api_key_env", "ATLAS_API_KEY")
        self.api_key = os.getenv(api_key_env)
        self.base_url = sora_cfg.get("base_url", "https://api.atlascloud.ai/v1")

        if not self.api_key:
            raise ValueError(f"{api_key_env} must be provided")

    def generate(
        self,
        prompt: str,
        model: str = "sora-2",
        duration: int = 10,
        resolution: str = "1080p",
        image: Optional[str] = None,
        **opts,
    ) -> str:
        """
        提交视频生成任务
        返回: task_id (request_id)
        """
        print(f"[Sora] 发起视频生成任务: {prompt[:50]}...")

        if image:
            print("警告: Sora 模型不支持图生视频，将忽略图片")

        payload = {
            "model": "openai/sora-2",
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "no_watermark": True,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                f"{self.base_url}/model/generateVideo",
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            request_id = response.json().get("request_id")
            if not request_id:
                raise Exception(f"Failed to get request_id: {response.text}")
            return request_id
        except requests.exceptions.RequestException as e:
            raise Exception(f"API Request failed: {str(e)}")

    def poll(self, task_id: str, interval: int = 10, timeout: int = 600) -> str:
        """轮询任务状态"""
        start_time = time.time()
        headers = {"Authorization": f"Bearer {self.api_key}"}

        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{self.base_url}/model/prediction/{task_id}/get",
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()
                result = response.json()
                status = result.get("status")

                if status == "succeeded":
                    output_url = result.get("output_url") or result.get("output", {}).get("url")
                    if not output_url:
                        raise Exception(f"Success but no output_url found")
                    print("视频生成成功!")
                    return output_url
                elif status == "failed":
                    error_msg = result.get("error", "Unknown error")
                    raise Exception(f"视频生成失败: {error_msg}")

                elapsed = int(time.time() - start_time)
                print(f"正在生成中... ({elapsed}s)", end="\r")
                time.sleep(interval)
            except requests.exceptions.RequestException as e:
                print(f"\n轮询连接异常: {e}，5秒后重试...")
                time.sleep(5)

        raise TimeoutError(f"视频生成任务超时 (超过 {timeout}s)")

    def download(self, url: str, path: str = "output.mp4") -> str:
        """下载视频到本地"""
        print(f"下载视频: {url}")
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            save_path = os.path.abspath(path)
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"视频已保存至: {save_path}")
            return save_path
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")