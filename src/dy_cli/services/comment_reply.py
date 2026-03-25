"""
评论自动回复服务
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from dy_cli.services.prompt_opt import generate_comment_reply, get_provider
from dy_cli.services.storage import get_storage
from dy_cli.utils.config import load_config


SENSITIVE_KEYWORDS = [
    "引流",
    "私信",
    "微信",
    "vx",
    "赌博",
    "政治",
    "色情",
    "辱骂",
]


def _is_safe_for_auto_reply(comment_text: str, policy: str = "whitelist") -> bool:
    """检查评论是否适合自动回复"""
    text = (comment_text or "").strip().lower()
    if not text:
        return False

    if policy != "whitelist":
        return True

    # 白名单模式：过滤敏感词
    if any(kw in text for kw in SENSITIVE_KEYWORDS):
        return False

    # 包含这些关键词的可以回复
    if any(kw in text for kw in ("?", "？", "怎么", "如何", "谢谢", "喜欢", "赞", "棒")):
        return True

    return False


def fetch_comments(video_id: Optional[str] = None, limit: int = 20) -> list:
    """
    获取视频评论
    当前实现：从存储中获取已同步的评论
    """
    storage = get_storage()
    # TODO: 后续可实现从抖音API实时获取评论
    # 当前直接从本地存储返回
    comments = storage.load_comments()
    result = []

    for comment_data in comments.values():
        if video_id and comment_data.get("video_id") != video_id:
            continue
        result.append(comment_data)

    result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return result[:limit]


def reply_comment(comment_id: str, reply_text: str) -> bool:
    """标记评论已回复"""
    storage = get_storage()
    # TODO: 实现实际的回复API调用
    # 当前仅标记已回复
    return True


def auto_reply_batch(
    video_id: Optional[str] = None,
    limit: int = 20,
    policy: str = "whitelist",
    llm_provider: Optional[str] = None,
) -> List[dict]:
    """执行单次自动回复批处理"""
    config = load_config()
    comment_cfg = config.get("comment_bot", {})

    if not comment_cfg.get("enabled", False):
        print("评论机器人未启用，请在配置中设置 comment_bot.enabled = true")
        return []

    storage = get_storage()
    comments = fetch_comments(video_id=video_id, limit=limit)
    results: List[dict] = []

    for comment in comments:
        comment_id = comment.get("id")
        comment_text = comment.get("text", "")

        # 检查是否已回复
        if comment.get("replied"):
            continue

        # 检查策略
        if not _is_safe_for_auto_reply(comment_text, policy=policy):
            results.append({
                "id": comment_id,
                "status": "skipped",
                "reason": f"policy={policy}"
            })
            continue

        # 生成回复
        auto_reply = generate_comment_reply(comment_text, provider=llm_provider)
        if not auto_reply:
            results.append({
                "id": comment_id,
                "status": "skipped",
                "reason": "empty_reply"
            })
            continue

        # 存储回复
        storage.mark_replied(comment_id, auto_reply)

        # TODO: 调用抖音API实际发送回复

        results.append({
            "id": comment_id,
            "user": comment.get("user", ""),
            "status": "replied",
            "reply_text": auto_reply,
        })

    return results


def auto_reply_loop(
    interval: int = 60,
    policy: str = "whitelist",
    llm_provider: Optional[str] = None,
) -> None:
    """自动回复评论循环"""
    config = load_config()
    comment_cfg = config.get("comment_bot", {})

    check_interval = comment_cfg.get("check_interval", interval)
    max_replies = comment_cfg.get("max_replies_per_run", 10)

    print(f"启动自动回复模式 (轮询间隔: {check_interval}s, policy={policy}, llm={llm_provider})")
    print("按 Ctrl+C 停止")

    try:
        while True:
            results = auto_reply_batch(
                limit=max_replies,
                policy=policy,
                llm_provider=llm_provider,
            )
            for result in results:
                if result["status"] == "replied":
                    print(f"自动回复 [{result.get('user', result['id'])}]: {result['reply_text']}")
                elif result["status"] == "skipped":
                    print(f"跳过评论 [{result['id']}]，原因: {result['reason']}")
            import time
            time.sleep(check_interval)
    except KeyboardInterrupt:
        print("\n自动回复已停止")


def list_comments(unreplied_only: bool = False, limit: int = 20) -> List[dict]:
    """列出评论"""
    storage = get_storage()
    comments = storage.load_comments()

    result = []
    for comment_data in comments.values():
        if unreplied_only and comment_data.get("replied"):
            continue
        result.append({
            "id": comment_data.get("id"),
            "user": comment_data.get("user"),
            "text": comment_data.get("text"),
            "replied": comment_data.get("replied"),
            "reply_text": comment_data.get("reply_text"),
        })

    result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return result[:limit]