"""
即梦AI (Jimeng) 视频生成器

支持模型:
- jimeng-pro: 图生视频 + 文生视频
- jimeng-720p: 文生视频 720p
- jimeng-1080p: 文生视频 1080p
"""

import base64
import os
from typing import Optional

from volcengine.visual.VisualService import VisualService


class JimengGenerator:
    """即梦AI 视频生成器"""

    MODEL_MAP = {
        "jimeng-pro": "jimeng_ti2v_v30_pro",
        "jimeng-720p": "jimeng_t2v_v30",
        "jimeng-1080p": "jimeng_t2v_v30_1080p",
    }

    def __init__(self, ak: Optional[str] = None, sk: Optional[str] = None, model: str = "jimeng-pro"):
        self.ak = ak or os.getenv("VOLC_ACCESSKEY")
        self.sk = sk or os.getenv("VOLC_SECRETKEY")

        if not self.ak or not self.sk:
            raise ValueError("VOLC_ACCESSKEY and VOLC_SECRETKEY must be provided")

        self.visual_service = VisualService()
        self.visual_service.set_ak(self.ak)
        self.visual_service.set_sk(self.sk)

        self.model = model
        self.req_key = self.MODEL_MAP.get(model, "jimeng_ti2v_v30_pro")

    def generate(
        self,
        prompt: str,
        image: Optional[str] = None,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        **kwargs,
    ) -> str:
        """提交视频生成任务"""
        print(f"🚀 [即梦AI] 发起视频生成任务: {prompt[:50]}...")

        # 帧数 = 24 * n + 1
        frames = 121 if duration <= 5 else 241

        formdata = {
            "req_key": self.req_key,
            "prompt": prompt,
        }

        if self.req_key == "jimeng_ti2v_v30_pro":
            formdata["frames"] = frames
            formdata["aspect_ratio"] = aspect_ratio
            if image:
                if os.path.exists(image):
                    with open(image, "rb") as f:
                        image_data = f.read()
                    formdata["binary_data_base64"] = [base64.b64encode(image_data).decode("utf-8")]
                else:
                    formdata["image_urls"] = [image]
        else:
            if image:
                print(f"⚠️ 警告: 模型 {self.req_key} 仅支持文生视频")

        try:
            resp = self.visual_service.cv_sync2async_submit_task(formdata)
            if "code" in resp and resp["code"] != 10000:
                raise Exception(f"API Error: {resp.get('message')} (Code: {resp['code']})")

            data = resp.get("data", {})
            task_id = data.get("task_id")
            if not task_id:
                raise Exception(f"Failed to get task_id: {resp}")
            return task_id
        except Exception as e:
            raise Exception(f"Jimeng API Submit failed: {str(e)}")

    def poll(self, task_id: str, interval: int = 15, timeout: int = 900) -> str:
        """轮询任务状态"""
        import time
        start_time = time.time()

        formdata = {"req_key": self.req_key, "task_id": task_id}

        while time.time() - start_time < timeout:
            try:
                resp = self.visual_service.cv_sync2async_get_result(formdata)
                if "code" in resp and resp["code"] != 10000:
                    raise Exception(f"API Error: {resp.get('message')} (Code: {resp['code']})")

                data = resp.get("data", {})
                status = data.get("status")

                if status == "done":
                    video_url = data.get("video_url")
                    if not video_url:
                        raise Exception(f"Success but no video_url found")
                    print("\n✅ 视频生成成功!")
                    return video_url
                elif status in ["failed", "not_found", "expired"]:
                    raise Exception(f"❌ 视频生成失败: Status {status}")

                elapsed = int(time.time() - start_time)
                print(f"⏳ 任务状态: {status} ({elapsed}s)", end="\r")
                time.sleep(interval)
            except Exception as e:
                print(f"\n⚠️ 轮询异常: {e}，正在重试...")
                time.sleep(5)

        raise TimeoutError(f"❌ 任务 {task_id} 超时")

    def download(self, url: str, filename: str = "output.mp4") -> str:
        """下载视频"""
        import requests
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