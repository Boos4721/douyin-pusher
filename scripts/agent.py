#!/usr/bin/env python3
"""
OpenClaw 主入口 - 统一调度所有功能

支持自然语言命令处理和智能任务分发
"""

import re
import sys
from typing import Optional, Dict, Any

from video.generator import VideoGenerator
from video.scheduler import schedule_task, list_tasks
from storage import get_storage


class Agent:
    """OpenClaw 智能代理"""

    COMMAND_PATTERNS = {
        # 视频生成
        r"生成视频[:：]\s*(.+)": ("gen_video", "prompt"),
        r"生成\s*(.+)视频": ("gen_video", "prompt"),
        r"gen\s+(.+)": ("gen_video", "prompt"),
        # 短剧生成
        r"生成短剧[:：]\s*(.+)": ("gen_movie", "content"),
        r"movie\s+(.+)": ("gen_movie", "content"),
        # 发布视频
        r"发布视频(?:\s+(.+))?": ("publish", "video"),
        r"publish\s+(.+)": ("publish", "video"),
        # 登录
        r"登录抖音": ("login", None),
        r"login": ("login", None),
        # 定时发布
        r"定时发布[:：]\s*(.+?)(?:\s+时间[:：]\s*(.+))?": ("schedule", "video_time"),
        r"schedule\s+(.+)": ("schedule", "video_time"),
        # 查看任务
        r"查看定时任务": ("list_schedule", None),
        r"tasks": ("list_tasks", None),
        # 评论
        r"开启自动回复": ("auto_reply", None),
        r"auto[- ]?reply": ("auto_reply", None),
        r"查看评论": ("list_comments", None),
        r"comments": ("list_comments", None),
    }

    def __init__(self):
        self.storage = get_storage()

    def parse_command(self, text: str) -> tuple[Optional[str], Dict[str, Any]]:
        """解析自然语言命令"""
        text = text.strip()

        for pattern, (cmd, param_key) in self.COMMAND_PATTERNS.items():
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                params = {}
                if param_key:
                    groups = match.groups()
                    if len(groups) == 1:
                        params[param_key] = groups[0]
                    elif len(groups) > 1:
                        # 处理多个参数的情况
                        if cmd == "schedule":
                            # 定时发布: video.mp4 时间: xxx
                            video_time = groups[0].strip() if groups[0] else ""
                            time_str = groups[1].strip() if groups[1] else ""
                            # 尝试分割视频和时间
                            if " " in video_time:
                                parts = video_time.split(" ", 1)
                                params["video"] = parts[0]
                                params["time"] = parts[1] if len(parts) > 1 else time_str
                            else:
                                params["video"] = video_time
                                params["time"] = time_str
                return cmd, params

        return None, {"raw": text}

    def execute(self, command: str, **params) -> Any:
        """执行命令"""
        if command == "gen_video":
            return self._gen_video(params.get("prompt", ""))
        elif command == "gen_movie":
            return self._gen_movie(params.get("content", ""))
        elif command == "publish":
            return self._publish(params.get("video", ""))
        elif command == "login":
            return self._login()
        elif command == "schedule":
            return self._schedule(params.get("video", ""), params.get("time", ""))
        elif command == "list_schedule":
            return self._list_schedule()
        elif command == "list_tasks":
            return self._list_tasks()
        elif command == "list_comments":
            return self._list_comments()
        elif command == "auto_reply":
            return self._auto_reply()
        else:
            return {"error": f"Unknown command: {command}"}

    def _gen_video(self, prompt: str) -> Dict[str, Any]:
        """生成视频"""
        if not prompt:
            return {"error": "请提供视频提示词"}

        print(f"🎬 正在生成视频: {prompt}")

        gen = VideoGenerator(model="auto")
        output = "output.mp4"

        path = gen.generate_and_download(prompt=prompt, output=output)
        return {"success": True, "path": path}

    def _gen_movie(self, content: str) -> Dict[str, Any]:
        """生成短剧"""
        from video.moviegen.main import MovieGenerator

        print(f"🎬 正在生成短剧: {content}")

        gen = MovieGenerator()
        result = gen.generate(content=content)
        return {"success": True, "result": result}

    def _publish(self, video: str) -> Dict[str, Any]:
        """发布视频"""
        from douyin.publish import publish_video

        if not video:
            return {"error": "请提供视频文件路径"}

        result = publish_video(video, "")
        return result

    def _login(self) -> Dict[str, Any]:
        """登录抖音"""
        from douyin.login import check_and_login

        result = check_and_login()
        return result

    def _schedule(self, video: str, time_str: str) -> Dict[str, Any]:
        """定时发布"""
        if not video or not time_str:
            return {"error": "请提供视频文件路径和发布时间"}

        task_id = schedule_task(video, time_str)
        return {"success": True, "task_id": task_id}

    def _list_schedule(self) -> Dict[str, Any]:
        """列出定时任务"""
        tasks = list_tasks()
        return {"tasks": tasks}

    def _list_tasks(self) -> Dict[str, Any]:
        """列出任务"""
        tasks = self.storage.list_tasks()
        return {"tasks": [str(t) for t in tasks]}

    def _list_comments(self) -> Dict[str, Any]:
        """列出评论"""
        comments = self.storage.list_comments()
        return {"comments": [c.text for c in comments]}

    def _auto_reply(self) -> Dict[str, Any]:
        """开启自动回复"""
        from douyin.comment import auto_reply_loop

        print("⏳ 开启自动回复模式 (Ctrl+C 停止)...")
        auto_reply_loop()
        return {"running": True}

    def run(self, input_text: Optional[str] = None):
        """运行代理"""
        if input_text is None:
            # 交互模式
            print("🤖 OpenClaw 智能代理 (输入 'exit' 退出)")
            print("支持命令: 生成视频、生成短剧、发布视频、登录抖音、定时发布、查看定时任务、开启自动回复、查看评论")
            print()

            while True:
                try:
                    text = input(">>> ").strip()
                    if text.lower() in ("exit", "quit", "q"):
                        break

                    if not text:
                        continue

                    cmd, params = self.parse_command(text)
                    if cmd:
                        result = self.execute(cmd, **params)
                        print(f"结果: {result}")
                    else:
                        print(f"⚠️ 无法理解命令: {text}")

                except KeyboardInterrupt:
                    print("\n退出")
                    break
                except Exception as e:
                    print(f"❌ 错误: {e}")
        else:
            # 单次执行模式
            cmd, params = self.parse_command(input_text)
            if cmd:
                return self.execute(cmd, **params)
            else:
                return {"error": f"无法理解命令: {input_text}"}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="OpenClaw 智能代理")
    parser.add_argument("command", nargs="?", help="自然语言命令")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")

    args = parser.parse_args()

    agent = Agent()

    if args.interactive or not args.command:
        agent.run()
    else:
        result = agent.run(args.command)
        print(result)


if __name__ == "__main__":
    main()