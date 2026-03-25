"""
dy comment-bot — 评论自动回复命令组
"""
from __future__ import annotations

import click

from dy_cli.services.comment_reply import auto_reply_batch, auto_reply_loop, list_comments
from dy_cli.utils.config import load_config
from dy_cli.utils.output import console, error, info, success


@click.group(name="comment-bot")
def comment_bot_group():
    """评论自动回复命令组"""
    pass


@comment_bot_group.command(name="run")
@click.option("--video-id", "-v", default=None, help="视频ID")
@click.option("--limit", "-l", default=10, type=int, help="最大处理数量")
@click.option("--policy", "-p", type=click.Choice(["whitelist", "all"]), default=None,
              help="回复策略")
@click.option("--provider", default=None, help="LLM provider")
def run(video_id, limit, policy, provider):
    """执行单次评论自动回复"""
    config = load_config()
    comment_cfg = config.get("comment_bot", {})

    if not comment_cfg.get("enabled", False):
        info("评论机器人未启用，请在配置中设置 comment_bot.enabled = true")
        info("运行以下命令启用:")
        info("  dy config set comment_bot.enabled true")
        return

    # 使用配置中的默认值
    if policy is None:
        policy = comment_cfg.get("policy", "whitelist")

    info(f"开始处理评论 (video_id={video_id or 'all'}, policy={policy})")

    results = auto_reply_batch(
        video_id=video_id,
        limit=limit,
        policy=policy,
        llm_provider=provider,
    )

    replied_count = sum(1 for r in results if r["status"] == "replied")
    skipped_count = sum(1 for r in results if r["status"] == "skipped")

    console.print()
    success(f"处理完成: 回复 {replied_count} 条，跳过 {skipped_count} 条")

    for result in results:
        if result["status"] == "replied":
            console.print(f"  ✅ [{result.get('user', result['id'])}] {result['reply_text']}")
        elif result["status"] == "skipped":
            console.print(f"  ⏭️ [{result['id']}] 原因: {result['reason']}")


@comment_bot_group.command(name="loop")
@click.option("--policy", "-p", type=click.Choice(["whitelist", "all"]), default=None,
              help="回复策略")
@click.option("--provider", default=None, help="LLM provider")
def loop(policy, provider):
    """启动评论自动回复循环"""
    config = load_config()
    comment_cfg = config.get("comment_bot", {})

    if not comment_cfg.get("enabled", False):
        info("评论机器人未启用，请在配置中设置 comment_bot.enabled = true")
        info("运行以下命令启用:")
        info("  dy config set comment_bot.enabled true")
        return

    if policy is None:
        policy = comment_cfg.get("policy", "whitelist")

    auto_reply_loop(
        policy=policy,
        llm_provider=provider,
    )


@comment_bot_group.command(name="list")
@click.option("--unreplied-only", "-u", is_flag=True, help="仅显示未回复")
@click.option("--limit", "-l", default=20, type=int, help="显示数量")
def list_comments_cmd(unreplied_only, limit):
    """列出评论"""
    comments = list_comments(unreplied_only=unreplied_only, limit=limit)

    if not comments:
        info("暂无评论")
        return

    console.print()
    console.print(f"[bold]评论列表 (共 {len(comments)} 条)[/bold]")
    console.print()

    for comment in comments:
        status_icon = "✅" if comment.get("replied") else "⏳"
        console.print(f"  {status_icon} [bold]{comment.get('user', 'Unknown')}[/bold]")
        console.print(f"      内容: {comment.get('text', '')[:60]}...")
        if comment.get("reply_text"):
            console.print(f"      回复: {comment['reply_text']}")
        console.print()


@comment_bot_group.command(name="status")
def status():
    """查看评论机器人状态"""
    config = load_config()
    comment_cfg = config.get("comment_bot", {})

    console.print()
    console.print("[bold]评论机器人状态[/bold]")
    console.print()

    enabled = comment_cfg.get("enabled", False)
    console.print(f"  启用状态: {'✅ 已启用' if enabled else '❌ 未启用'}")
    console.print(f"  检查间隔: {comment_cfg.get('check_interval', 60)} 秒")
    console.print(f"  每轮最大回复: {comment_cfg.get('max_replies_per_run', 10)} 条")
    console.print(f"  回复策略: {comment_cfg.get('policy', 'whitelist')}")

    if not enabled:
        console.print()
        info("启用评论机器人:")
        info("  dy config set comment_bot.enabled true")

    console.print()


@comment_bot_group.command(name="enable")
def enable():
    """启用评论机器人"""
    from dy_cli.utils.config import set_value
    set_value("comment_bot.enabled", True)
    success("评论机器人已启用")


@comment_bot_group.command(name="disable")
def disable():
    """禁用评论机器人"""
    from dy_cli.utils.config import set_value
    set_value("comment_bot.enabled", False)
    info("评论机器人已禁用")