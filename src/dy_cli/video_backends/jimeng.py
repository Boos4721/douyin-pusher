"""
即梦AI (Jimeng) 视频生成后端 - 网页版自动化

支持的模型 (与 xyq 小云雀相同):
- seedance-2.0: Seedance 2.0
- seedance-2.0-fast: Seedance 2.0 Fast

网址: https://jimeng.jianying.com
"""
import asyncio
import json
import os
import re
import uuid
from typing import Optional

from dy_cli.utils.config import load_config


def _run_async(coro):
    """在同步上下文中运行异步函数。"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


class JimengBackend:
    """即梦AI网页版自动化后端"""

    BASE_URL = "https://jimeng.jianying.com"

    # 模型映射 - 与 xyq 小云雀相同
    MODEL_MAP = {
        "seedance-2.0": "Seedance 2.0",
        "seedance-2.0-fast": "Seedance 2.0 Fast",
    }

    DURATION_OPTIONS = ["5s", "10s", "15s"]
    RATIO_OPTIONS = ["横屏", "竖屏", "方屏"]

    def __init__(self):
        config = load_config()
        jimeng_cfg = config.get("video_backends", {}).get("jimeng", {})

        self.cookies_path = os.path.expanduser(jimeng_cfg.get(
            "cookies_path",
            "~/.dy/cookies/jimeng.json"
        ))

        self.output_dir = os.path.expanduser("~/Downloads/douyin/videos")
        os.makedirs(self.output_dir, exist_ok=True)

    def _load_cookies(self):
        """加载 cookies"""
        if not os.path.exists(self.cookies_path):
            raise FileNotFoundError(f"Cookies not found: {self.cookies_path}")

        with open(self.cookies_path, encoding="utf-8") as f:
            raw = json.load(f)

        cleaned = []
        allowed = ['name', 'value', 'domain', 'path', 'expires', 'httpOnly', 'secure']
        for c in raw:
            clean = {}
            for key in allowed:
                if key == 'expires':
                    val = c.get('expirationDate') or c.get('expires')
                    if val is not None:
                        clean['expires'] = val
                    continue
                if key in c and c[key] is not None:
                    clean[key] = c[key]
            cleaned.append(clean)
        return cleaned

    async def _safe_click(self, page, locator_or_selector, label, timeout=5000):
        """安全点击"""
        try:
            if isinstance(locator_or_selector, str):
                loc = page.locator(locator_or_selector).first
            else:
                loc = locator_or_selector
            await loc.click(timeout=timeout)
            print(f"  ✅ {label}: clicked")
            return True
        except Exception as e:
            print(f"  ❌ {label}: {e}")
            return False

    async def _generate_async(
        self,
        prompt: str,
        model: str = "seedance-2.0",
        duration: str = "10s",
        ratio: str = "横屏",
        ref_video: Optional[str] = None,
        ref_image: Optional[str] = None,
    ) -> str:
        """异步生成视频"""
        from playwright.async_api import async_playwright

        model_name = self.MODEL_MAP.get(model, "Seedance 2.0")
        want_fast = "Fast" in model_name

        if ref_image:
            mode_label = "I2V (图生视频)"
        elif ref_video:
            mode_label = "V2V (参考视频)"
        else:
            mode_label = "T2V (文生视频)"

        print(f"[即梦AI] 发起视频生成任务: {prompt[:50]}...")
        print(f"  模式: {mode_label}, 模型: {model_name}, 时长: {duration}, 比例: {ratio}")

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})

            cookies = self._load_cookies()
            await context.add_cookies(cookies)
            print(f"  已注入 {len(cookies)} 个 cookies")

            page = await context.new_page()

            # 导航
            print("  导航到即梦AI...")
            await page.goto(f"{self.BASE_URL}/home", wait_until="domcontentloaded")
            await page.wait_for_timeout(8000)

            # 检查登录
            page_content = await page.content()
            is_logged_in = '小云雀助你' in page_content or '新对话' in page_content or 'AI' in page_content
            if not is_logged_in:
                print("  请先在浏览器中登录即梦AI")
                await browser.close()
                raise Exception("未登录，请先导出 jimeng.jianying.com 的 cookies")

            print("  ✅ 登录成功")

            # 选择 "沉浸式短片" 模式
            print("  选择模式...")
            try:
                mode_dropdown = await self._safe_click(
                    page, page.locator('text=Agent 模式').first, 'Agent 模式', timeout=8000
                )
                await page.wait_for_timeout(2000)

                if mode_dropdown:
                    await self._safe_click(
                        page, page.locator('text=沉浸式短片').first, '沉浸式短片', timeout=5000
                    )
            except Exception as e:
                print(f"  模式选择: {e}")

            await page.wait_for_timeout(3000)

            # 选择模型
            print("  选择模型...")
            try:
                model_click = await page.evaluate('''([wantFast]) => {
                    const items = Array.from(document.querySelectorAll('*'));
                    const btn = items.find(el => {
                        const text = el.innerText && el.innerText.trim();
                        if (!text || !text.includes('2.0')) return false;
                        if (text.length > 15) return false;
                        const rect = el.getBoundingClientRect();
                        return rect.top > 400 && rect.top < 700 && rect.left > 800 &&
                               el.offsetHeight < 50 && el.offsetHeight > 15;
                    });
                    if (btn) {
                        btn.click();
                        return 'opened: ' + btn.innerText.trim();
                    }
                    return 'NOT_FOUND';
                }''', [want_fast])
                print(f"    {model_click}")

                # 在下拉菜单中选择模型
                await page.wait_for_timeout(1500)
                model_select = await page.evaluate('''([wantFast]) => {
                    const items = Array.from(document.querySelectorAll('*'));
                    const candidates = items.filter(el => {
                        const text = el.innerText && el.innerText.trim();
                        if (!text) return false;
                        if (!/^Seedance/.test(text)) return false;
                        if (/[\u4e00-\u9fff]/.test(text)) return false;
                        if (el.offsetHeight > 40 || el.offsetHeight < 10) return false;
                        const rect = el.getBoundingClientRect();
                        return rect.left > 900 && rect.left < 1100 && rect.top > 350 && rect.top < 850;
                    });
                    for (const el of candidates) {
                        const text = el.innerText.trim();
                        const isFast = text.includes('Fast');
                        if (wantFast === isFast) {
                            el.click();
                            return 'selected: ' + text;
                        }
                    }
                    return 'NOT_FOUND';
                }''', [want_fast])
                print(f"    {model_select}")
            except Exception as e:
                print(f"  模型选择: {e}")

            await page.wait_for_timeout(1500)

            # 选择时长
            print("  选择时长...")
            try:
                dur_btn = page.locator('text=/^\\d+s$/').first
                await self._safe_click(page, dur_btn, '时长按钮')
                await page.wait_for_timeout(1500)

                dur_item = page.locator(f'text=/^{duration}$/').first
                await dur_item.click(timeout=3000)
                print(f"    已选择: {duration}")
            except Exception as e:
                print(f"  时长选择: {e}")

            await page.wait_for_timeout(1000)

            # 输入提示词
            print("  输入提示词...")
            inject_result = await page.evaluate('''([text]) => {
                const el = document.querySelector('div[contenteditable="true"]');
                if (el) {
                    el.innerText = text;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    return 'OK: ' + el.innerText.substring(0, 30);
                }
                return 'FAILED';
            }''', [prompt])
            print(f"    {inject_result}")

            await page.wait_for_timeout(1000)

            # 提交任务
            print("  提交任务...")
            thread_id = None

            async def sniff_thread(response):
                nonlocal thread_id
                if thread_id:
                    return
                try:
                    text = await response.text()
                    if 'thread_id' in text:
                        data = json.loads(text)
                        tid = data.get('thread_id') or data.get('data', {}).get('thread_id')
                        if tid:
                            thread_id = tid
                            print(f"    获取到 thread_id: {tid}")
                except Exception:
                    pass

            page.on('response', sniff_thread)

            await self._safe_click(
                page, page.locator('button:has(svg.lucide-arrow-up)').first, '发送', timeout=5000
            )
            await page.wait_for_timeout(5000)

            # 等待 thread_id
            for _ in range(10):
                if thread_id:
                    break
                await page.wait_for_timeout(2000)

            if not thread_id:
                page_html = await page.content()
                m = re.search(r'thread_id["\s:=]+([0-9a-f-]{36})', page_html)
                if m:
                    thread_id = m.group(1)
                    print(f"    从HTML获取 thread_id: {thread_id}")

            if not thread_id:
                raise Exception("无法获取 thread_id")

            # 轮询视频
            print("  等待视频生成...")
            detail_url = f"{self.BASE_URL}/home?tab_name=integrated-agent&thread_id={thread_id}"
            await page.goto(detail_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(8000)

            mp4_url = None
            for i in range(240):  # 最多20分钟
                await page.wait_for_timeout(5000)

                mp4_url = await page.evaluate(r'''() => {
                    const v = document.querySelector('video');
                    if (v && v.src && v.src.includes('.mp4')) return v.src;
                    const s = document.querySelector('video source');
                    if (s && s.src && s.src.includes('.mp4')) return s.src;
                    const html = document.documentElement.innerHTML;
                    const m = html.match(/https?:\/\/[^"'\\s\\\\]+\.mp4[^"'\\s\\\\]*/);
                    return m ? m[0] : null;
                }''')

                if mp4_url:
                    break

                if i % 12 == 0 and i > 0:
                    print(f"    等待中... ({i*5}s)")
                    await page.reload(wait_until="domcontentloaded")
                    await page.wait_for_timeout(5000)

            await browser.close()

            if not mp4_url:
                raise Exception("视频生成超时")

            print(f"  视频生成成功!")
            return mp4_url

    def generate(
        self,
        prompt: str,
        model: str = "seedance-2.0",
        duration: str = "10s",
        ratio: str = "横屏",
        ref_video: Optional[str] = None,
        ref_image: Optional[str] = None,
        **opts,
    ) -> str:
        """提交视频生成任务"""
        if duration not in self.DURATION_OPTIONS:
            raise ValueError(f"Invalid duration: {duration}")
        if ratio not in self.RATIO_OPTIONS:
            raise ValueError(f"Invalid ratio: {ratio}")

        job_id = str(uuid.uuid4())[:8]

        task_info = {
            "job_id": job_id,
            "prompt": prompt,
            "model": model,
            "model_name": self.MODEL_MAP.get(model),
            "duration": duration,
            "ratio": ratio,
            "ref_video": ref_video,
            "ref_image": ref_image,
            "output_dir": self.output_dir,
            "cookies_path": self.cookies_path,
        }

        task_file = os.path.join(self.output_dir, f".task_{job_id}.json")
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_info, f, ensure_ascii=False)

        try:
            video_url = _run_async(self._generate_async(
                prompt, model, duration, ratio, ref_video, ref_image
            ))

            task_info["status"] = "done"
            task_info["video_url"] = video_url
            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(task_info, f, ensure_ascii=False)

            return job_id
        except Exception as e:
            task_info["status"] = "failed"
            task_info["error"] = str(e)
            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(task_info, f, ensure_ascii=False)
            raise

    def poll(self, job_id: str, interval: int = 10, timeout: int = 1200) -> str:
        """轮询任务状态"""
        task_file = os.path.join(self.output_dir, f".task_{job_id}.json")

        if not os.path.exists(task_file):
            raise FileNotFoundError(f"Task not found: {job_id}")

        with open(task_file, encoding="utf-8") as f:
            task_info = json.load(f)

        if task_info.get("status") == "done":
            video_url = task_info.get("video_url")
            if video_url:
                return video_url
            raise Exception("Video URL not found")

        if task_info.get("status") == "failed":
            raise Exception(task_info.get("error", "Generation failed"))

        raise Exception(f"Unknown status: {task_info.get('status')}")

    def download(self, url: str, path: str = "output.mp4") -> str:
        """下载视频"""
        print(f"下载视频: {url}")
        import requests

        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            save_path = os.path.abspath(path)
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            size_mb = os.path.getsize(save_path) / (1024 * 1024)
            print(f"视频已保存: {save_path} ({size_mb:.1f}MB)")
            return save_path
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")