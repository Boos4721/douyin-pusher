"""
抖音评论管理模块
"""

import time
from typing import Optional, List

from storage import get_storage


def fetch_comments(video_id: Optional[str] = None) -> List[dict]:
    """获取视频评论"""
    # TODO: 通过 pinchtab 或 API 获取评论
    # 这里是一个占位实现
    storage = get_storage()
    return storage.list_comments(video_id=video_id)


def reply_comment(comment_id: str, reply_text: str) -> bool:
    """回复评论"""
    # TODO: 通过 pinchtab 或 API 回复评论
    storage = get_storage()
    return storage.mark_replied(comment_id, reply_text)


def auto_reply_loop(interval: int = 60):
    """自动回复评论循环"""
    print(f"🔄 启动自动回复模式 (轮询间隔: {interval}s)")
    print("按 Ctrl+C 停止")

    storage = get_storage()

    try:
        while True:
            # 获取未回复的评论
            comments = storage.list_comments(replied=False, limit=20)

            for comment in comments:
                # TODO: 使用 AI 生成回复内容
                auto_reply = generate_auto_reply(comment.text)
                if auto_reply:
                    print(f"🤖 自动回复 [{comment.user}]: {auto_reply}")
                    reply_comment(comment.id, auto_reply)

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n⏹️ 自动回复已停止")


def generate_auto_reply(comment_text: str) -> str:
    """使用 AI 生成自动回复"""
    # 简单的自动回复逻辑
    # TODO: 可以集成 OpenAI 等生成更智能的回复
    replies = [
        "感谢您的支持！",
        "谢谢您的评论！",
        "喜欢的话记得点赞哦～",
        "感谢您的关注！",
    ]

    # 简单关键词匹配
    if any(kw in comment_text for kw in ["好", "棒", "赞", "喜欢"]):
        return "感谢您的认可！"
    elif any(kw in comment_text for kw in ["?", "？", "怎么", "如何"]):
        return "有问题可以私信咨询哦～"

    return ""


def list_comments(unreplied_only: bool = False, limit: int = 20) -> List[dict]:
    """列出评论"""
    storage = get_storage()
    comments = storage.list_comments(replied=not unreplied_only if unreplied_only else None, limit=limit)

    return [
        {
            "id": c.id,
            "user": c.user,
            "text": c.text,
            "replied": c.replied,
            "reply_text": c.reply_text,
        }
        for c in comments
    ]