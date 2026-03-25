"""
即梦AI Seedance API - 火山引擎调用

支持模型:
- jimeng-pro: 即梦AI Pro (jimeng_ti2v_v30_pro) - 图生视频+文生视频
- jimeng-720p: 即梦AI 720P (jimeng_t2v_v30) - 文生视频
- jimeng-1080p: 即梦AI 1080P (jimeng_t2v_v30_1080p) - 文生视频

需要环境变量: VOLC_ACCESSKEY, VOLC_SECRETKEY
"""
import base64
import os
from typing import Optional

from dy_cli.utils.config import load_config

try:
    from volcengine.visual.VisualService import VisualService
    VOLC_SDK_AVAILABLE = True
except ImportError:
    VOLC_SDK_AVAILABLE = False


class SeedanceAPIBackend:
    """即梦AI Seedance API 后端 (火山引擎)"""

    # 模型映射 - req_key 对应火山引擎API
    MODEL_MAP = {
        "jimeng-pro": "jimeng_ti2v_v30_pro",
        "jimeng-720p": "jimeng_t2v_v30",
        "jimeng-1080p": "jimeng_t2v_v30_1080p",
    }

    def __init__(self):
        if not VOLC_SDK_AVAILABLE:
            raise ImportError("volcengine SDK not installed. Run: pip install volcengine")

        config = load_config()
        seedance_cfg = config.get("video_backends", {}).get("seedance", {})

        ak_env = seedance_cfg.get("ak_env", "VOLC_ACCESSKEY")
        sk_env = seedance_cfg.get("sk_env", "VOLC_SECRETKEY")

        self.ak = os.getenv(ak_env)
        self.sk = os.getenv(sk_env)

        if not self.ak or not self.sk:
            raise ValueError(f"{ak_env} and {sk_env} must be provided")

        self.visual_service = VisualService()
        self.visual_service.set_ak(self.ak)
        self.visual_service.set_sk(self.sk)

    def generate(
        self,
        prompt: str,
        model: str = "jimeng-pro",
        image: Optional[str] = None,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        **opts,
    ) -> str:
        """提交视频生成任务"""
        print(f"[Seedance API] 发起视频生成任务: {prompt[:50]}...")

        req_key = self.MODEL_MAP.get(model, "jimeng_ti2v_v30_pro")

        # 帧数 = 24 * n + 1
        frames = 121 if duration <= 5 else 241

        formdata = {
            "req_key": req_key,
            "prompt": prompt,
        }

        # jimeng-pro 支持图生视频
        if req_key == "jimeng_ti2v_v30_pro":
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
                print(f"警告: 模型 {req_key} 仅支持文生视频")

        try:
            resp = self.visual_service.cv_sync2async_submit_task(formdata)
            if "code" in resp and resp["code"] != 10000:
                raise Exception(f"API Error: {resp.get('message')} (Code: {resp['code']})")

            data = resp.get("data", {})
            task_id = data.get("task_id")
            if not task_id:
                raise Exception(f"Failed to get task_id: {resp}")
            print(f"  任务ID: {task_id}")
            return task_id
        except Exception as e:
            raise Exception(f"Seedance API Submit failed: {str(e)}")

    def poll(self, task_id: str, interval: int = 15, timeout: int = 900) -> str:
        """轮询任务状态"""
        import time
        start_time = time.time()

        formdata = {"req_key": "jimeng_ti2v_v30_pro", "task_id": task_id}

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
                    print("视频生成成功!")
                    return video_url
                elif status in ["failed", "not_found", "expired"]:
                    raise Exception(f"视频生成失败: Status {status}")

                elapsed = int(time.time() - start_time)
                print(f"任务状态: {status} ({elapsed}s)", end="\r")
                time.sleep(interval)
            except Exception as e:
                print(f"\n轮询异常: {e}，正在重试...")
                time.sleep(5)

        raise TimeoutError(f"任务 {task_id} 超时")

    def download(self, url: str, path: str = "output.mp4") -> str:
        """下载视频"""
        import requests
        print(f"下载视频: {url}")
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            save_path = os.path.abspath(path)
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return save_path
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")