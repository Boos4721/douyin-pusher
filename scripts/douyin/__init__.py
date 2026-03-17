"""抖音模块"""

from .comment import fetch_comments, reply_comment, auto_reply_loop, list_comments

__all__ = [
    "fetch_comments",
    "reply_comment",
    "auto_reply_loop",
    "list_comments",
]