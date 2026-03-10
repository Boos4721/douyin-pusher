import os
import time
import requests
import json

class VideoGenerator:
    """Seedance 2.0 / Sora 2 视频生成核心类"""
    def __init__(self, api_key=None, base_url="https://api.atlascloud.ai/v1"):
        self.api_key = api_key or os.getenv("SEEDANCE_API_KEY")
        self.base_url = base_url
        if not self.api_key:
            raise ValueError("SEEDANCE_API_KEY is not set.")

    def generate(self, prompt, model="bytedance/seedance-v1.5-pro/text-to-video", duration=10, resolution="1080p"):
        """提交视频生成任务"""
        print(f"🚀 发起视频生成任务: {prompt[:30]}...")
        payload = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(f"{self.base_url}/model/generateVideo", headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("request_id")

    def poll(self, request_id, interval=10, timeout=300):
        """轮询生成结果"""
        start_time = time.time()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        while time.time() - start_time < timeout:
            response = requests.get(f"{self.base_url}/model/prediction/{request_id}/get", headers=headers)
            result = response.json()
            status = result.get("status")
            
            if status == "succeeded":
                print("✅ 视频生成成功!")
                return result.get("output_url")
            elif status == "failed":
                raise Exception(f"❌ 视频生成失败: {result.get('error')}")
            
            print(f"⏳ 正在生成中... (已耗时 {int(time.time() - start_time)}s)")
            time.sleep(interval)
        
        raise TimeoutError("❌ 视频生成任务超时。")

    def download(self, url, filename="output.mp4"):
        """下载视频到本地"""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"📥 视频已保存至: {filename}")
        return os.path.abspath(filename)
