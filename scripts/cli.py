#!/usr/bin/env python3
"""
CLI 命令行入口

支持自然语言命令:
- python scripts/cli.py gen "生成视频: 提示词"
- python scripts/cli.py movie "生成短剧: 风格xxx 内容xxx"
- python scripts/cli.py publish video.mp4
- python scripts/cli.py login
- python scripts/cli.py schedule "video.mp4" "2024-01-01 12:00"
- python scripts/cli.py tasks
- python scripts/cli.py comments
- python scripts/cli.py auto-reply on
"""

import argparse
import sys
from typing import Optional


def cmd_gen(args):
    """生成视频"""
    from video.generator import VideoGenerator

    gen = VideoGenerator(model=args.model)
    output = args.output or "output.mp4"

    image = args.image if hasattr(args, "image") else None
    duration = args.duration if hasattr(args, "duration") else 5

    path = gen.generate_and_download(
        prompt=args.prompt,
        image=image,
        duration=duration,
        aspect_ratio=args.aspect,
        output=output,
    )
    print(f"\n✅ 视频已生成: {path}")
    return path


def cmd_movie(args):
    """生成短剧"""
    from video.moviegen.main import MovieGenerator

    gen = MovieGenerator()
    result = gen.generate(
        style=args.style,
        content=args.content,
        num_shots=args.shots,
    )
    print(f"\n✅ 短剧已生成: {result}")
    return result


def cmd_publish(args):
    """发布视频"""
    from douyin.publish import publish_video

    result = publish_video(args.video, args.title or "")
    if result.get("success"):
        print("✅ 发布成功!")
    else:
        print(f"❌ 发布失败: {result.get('message')}")
        sys.exit(1)


def cmd_login(args):
    """登录抖音"""
    from douyin.login import check_and_login, check_login_via_pincli

    if args.check:
        status = check_login_via_pincli()
        if status.get("logged_in"):
            print("✅ 已登录")
        else:
            print("❌ 未登录")
        return

    result = check_and_login()
    if result.get("success"):
        print("✅ 登录成功")
    else:
        print(f"❌ 登录失败: {result.get('message')}")
        sys.exit(1)


def cmd_schedule(args):
    """定时发布"""
    from video.scheduler import schedule_task, list_tasks

    if args.list:
        tasks = list_tasks()
        if not tasks:
            print("暂无定时任务")
        else:
            print(f"共有 {len(tasks)} 个定时任务:")
            for task in tasks:
                print(f"  - {task}")
        return

    if args.cancel:
        from video.scheduler import cancel_task
        cancel_task(args.cancel)
        print(f"✅ 已取消任务: {args.cancel}")
        return

    # 创建定时任务
    task_id = schedule_task(args.video, args.time, args.title)
    print(f"✅ 已创建定时任务: {task_id}")


def cmd_tasks(args):
    """查看任务列表"""
    from storage import get_storage

    storage = get_storage()
    tasks = storage.list_tasks(status=args.status, limit=args.limit)
    if not tasks:
        print("暂无任务")
        return

    for task in tasks:
        status_icon = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌"}.get(task.status, "❓")
        print(f"{status_icon} {task.id[:8]}... | {task.model} | {task.status}")


def cmd_comments(args):
    """查看评论"""
    from storage import get_storage

    storage = get_storage()
    comments = storage.list_comments(replied=args.unreplied, limit=args.limit)

    if not comments:
        print("暂无评论")
        return

    for c in comments:
        replied_mark = "✅" if c.replied else "❌"
        print(f"{replied_mark} [{c.user}] {c.text}")
        if c.reply_text:
            print(f"   → 回复: {c.reply_text}")


def cmd_auto_reply(args):
    """自动回复开关"""
    from douyin.comment import auto_reply_loop

    if args.enable:
        print("⏳ 开启自动回复模式 (Ctrl+C 停止)...")
        auto_reply_loop()
    else:
        print("❌ 自动回复功能需要使用 --enable 开启")


def main():
    parser = argparse.ArgumentParser(
        description="Sora2-Pusher - AI 视频生成与发布工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # gen - 生成视频
    gen_parser = subparsers.add_parser("gen", help="生成视频")
    gen_parser.add_argument("prompt", nargs="?", help="视频提示词")
    gen_parser.add_argument("-m", "--model", default="auto", help="模型 (jimeng-pro, seedance, sora, auto)")
    gen_parser.add_argument("-i", "--image", help="图片路径 (图生视频)")
    gen_parser.add_argument("-d", "--duration", type=int, default=5, help="视频时长 (秒)")
    gen_parser.add_argument("-a", "--aspect", default="16:9", help="宽高比")
    gen_parser.add_argument("-o", "--output", help="输出文件")
    gen_parser.set_defaults(func=cmd_gen)

    # movie - 生成短剧
    movie_parser = subparsers.add_parser("movie", help="生成短剧")
    movie_parser.add_argument("prompt", nargs="?", help="短剧提示词")
    movie_parser.add_argument("-s", "--style", default="电影", help="风格")
    movie_parser.add_argument("-n", "--shots", type=int, default=6, help="镜头数")
    movie_parser.add_argument("-o", "--output", help="输出目录")
    movie_parser.set_defaults(func=cmd_movie)

    # publish - 发布视频
    pub_parser = subparsers.add_parser("publish", help="发布视频到抖音")
    pub_parser.add_argument("video", help="视频文件路径")
    pub_parser.add_argument("-t", "--title", help="视频标题")
    pub_parser.set_defaults(func=cmd_publish)

    # login - 抖音登录
    login_parser = subparsers.add_parser("login", help="抖音扫码登录")
    login_parser.add_argument("--check", action="store_true", help="仅检查登录状态")
    login_parser.set_defaults(func=cmd_login)

    # schedule - 定时任务
    sched_parser = subparsers.add_parser("schedule", help="定时发布任务")
    sched_parser.add_argument("video", nargs="?", help="视频文件路径")
    sched_parser.add_argument("time", nargs="?", help="发布时间 (格式: YYYY-MM-DD HH:MM)")
    sched_parser.add_argument("-t", "--title", help="视频标题")
    sched_parser.add_argument("--list", action="store_true", help="列出所有定时任务")
    sched_parser.add_argument("--cancel", help="取消定时任务")
    sched_parser.set_defaults(func=cmd_schedule)

    # tasks - 任务列表
    tasks_parser = subparsers.add_parser("tasks", help="查看任务列表")
    tasks_parser.add_argument("-s", "--status", help="按状态筛选")
    tasks_parser.add_argument("-l", "--limit", type=int, default=20, help="显示数量")
    tasks_parser.set_defaults(func=cmd_tasks)

    # comments - 评论列表
    comm_parser = subparsers.add_parser("comments", help="查看评论")
    comm_parser.add_argument("-u", "--unreplied", action="store_const", const=False, help="仅显示未回复")
    comm_parser.add_argument("-l", "--limit", type=int, default=20, help="显示数量")
    comm_parser.set_defaults(func=cmd_comments)

    # auto-reply - 自动回复
    ar_parser = subparsers.add_parser("auto-reply", help="自动回复评论")
    ar_parser.add_argument("--enable", action="store_true", help="开启自动回复")
    ar_parser.set_defaults(func=cmd_auto_reply)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 调用对应的命令处理函数
    args.func(args)


if __name__ == "__main__":
    main()