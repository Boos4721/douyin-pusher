"""
火山引擎 Seedance 视频生成器
"""

import base64
import os
import time
from typing import Optional

import requests
import mimetypes


class VolcengineSeedanceGenerator:
    """火山引擎 Seedance 视频生成器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
    ):
        self.api_key = api_key or os.getenv("VOLC_API_KEY")
        self.endpoint = endpoint or os.getenv("VOLC_ENDPOINT")
        self.base_url = base_url

        if not self.api_key:
            raise ValueError("VOLC_API_KEY must be provided")

    def generate(
        self,
        prompt: str,
        image: Optional[str] = None,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        **kwargs,
    ) -> str:
        """提交视频生成任务"""
        print(f"🚀 [Seedance] 发起视频生成任务: {prompt[:50]}...")

        # 追加配置参数
        full_prompt = f"{prompt} --duration {duration} --watermark false"

        content = [{"type": "text", "text": full_prompt}]

        # 图生视频
        if image:
            if os.path.exists(image):
                mime_type, _ = mimetypes.guess_type(image)
                mime_type = mime_type or "image/jpeg"
                with open(image, "rb") as f:
                    base64_data = base64.b64encode(f.read()).decode("utf-8")
                data_uri = f"data:{mime_type};base64,{base64_data}"
                content.append({"type": "image_url", "image_url": {"url": data_uri}})
            else:
                content.append({"type": "image_url", "image_url": {"url": image}})

        payload = {
            "model": self.endpoint,
            "content": content,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/contents/generations/tasks"

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            task_id = data.get("id") or data.get("task_id")
            if not task_id:
                raise Exception(f"Failed to get task_id: {data}")
            return task_id
        except requests.exceptions.RequestException as e:
            raise Exception(f"Volcengine API Request failed: {str(e)}")

    def poll(self, task_id: str, interval: int = 15, timeout: int = 900) -> str:
        """轮询任务状态"""
        start_time = time.time()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/contents/generations/tasks/{task_id}"

        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                result = response.json()

                status = result.get("status")

                if status in ["succeeded", "completed"]:
                    video_url = result.get("content", {}).get("video_url") or result.get("video_url")
                    if not video_url:
                        raise Exception(f"Success but no video_url found: {result}")
                    print("\n✅ 视频生成成功!")
                    return video_url
                elif status in ["failed", "error"]:
                    error_msg = result.get("error", {}).get("message") or result.get("error_message") or "Unknown error"
                    raise Exception(f"❌ 视频生成失败: {error_msg}")

                elapsed = int(time.time() - start_time)
                print(f"⏳ 任务状态: {status} ({elapsed}s)", end="\r")
                time.sleep(interval)
            except requests.exceptions.RequestException as e:
                print(f"\n⚠️ 轮询异常: {e}，正在重试...")
                time.sleep(5)

        raise TimeoutError(f"❌ 任务 {task_id} 超时")

    def download(self, url: str, filename: str = "output.mp4") -> str:
        """下载视频"""
        print(f"📥 下载视频: {url}")
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            save_path = os.path.abspath(filename)
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return save_path
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")