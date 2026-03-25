"""
dy jobs — 任务管理命令组
"""
from __future__ import annotations

import os

import click

from dy_cli.services.scheduler import cancel_schedule, list_schedules, run_pending_tasks
from dy_cli.services.storage import get_storage
from dy_cli.utils.output import console, error, info, success


@click.group(name="jobs")
def jobs_group():
    """任务管理命令组"""
    pass


@jobs_group.command(name="run-pending")
def run_pending():
    """执行待处理的定时任务"""
    info("检查待处理任务...")
    run_pending_tasks()
    success("执行完成")


@jobs_group.command(name="list")
@click.option("--status", "-s", default=None, help="过滤状态")
@click.option("--limit", "-l", default=20, type=int, help="显示数量")
def list_all_jobs(status, limit):
    """列出所有任务"""
    storage = get_storage()
    jobs = storage.list_jobs(status=status, limit=limit)

    if not jobs:
        info("暂无任务")
        return

    console.print()
    console.print(f"[bold]任务列表 (共 {len(jobs)} 个)[/bold]")
    console.print()

    for job in jobs:
        status_emoji = {
            "pending": "⏳",
            "generating": "🔄",
            "generated": "✅",
            "publishing": "📤",
            "published": "🎉",
            "failed": "❌",
            "scheduled": "⏰",
        }.get(job.status, "❓")

        console.print(f"  {status_emoji} [bold]{job.id}[/bold] - {job.status}")
        console.print(f"      后端: {job.backend}/{job.model}")
        console.print(f"      提示词: {job.prompt[:40]}...")
        console.print()


@jobs_group.command(name="show")
@click.argument("job_id")
def show_job(job_id):
    """显示任务详情"""
    storage = get_storage()
    job = storage.load_job(job_id)

    if not job:
        error(f"任务不存在: {job_id}")
        raise SystemExit(1)

    console.print()
    console.print(f"[bold]任务详情: {job.id}[/bold]")
    console.print()
    console.print(f"  状态: {job.status}")
    console.print(f"  后端: {job.backend}")
    console.print(f"  模型: {job.model}")
    console.print(f"  提示词: {job.prompt}")
    if job.optimized_prompt:
        console.print(f"  优化提示词: {job.optimized_prompt}")
    if job.generated_video_path:
        console.print(f"  视频路径: {job.generated_video_path}")
    if job.generated_video_url:
        console.print(f"  视频URL: {job.generated_video_url}")
    if job.schedule_time:
        console.print(f"  定时: {job.schedule_time}")
    if job.douyin_aweme_id:
        console.print(f"  抖音ID: {job.douyin_aweme_id}")
    if job.title:
        console.print(f"  标题: {job.title}")
    if job.description:
        console.print(f"  描述: {job.description}")
    if job.error:
        console.print(f"  错误: {job.error}")
    console.print(f"  创建时间: {job.created_at}")
    if job.completed_at:
        console.print(f"  完成时间: {job.completed_at}")
    console.print()


@jobs_group.command(name="schedule")
@click.argument("job_id")
@click.option("--time", "-t", required=True, help="定时发布时间 (YYYY-MM-DD HH:MM)")
@click.option("--title", default="", help="视频标题")
@click.option("--description", "-d", default="", help="视频描述")
def schedule_job(job_id, time, title, description):
    """设置定时发布"""
    from dy_cli.services.scheduler import schedule_job as do_schedule

    storage = get_storage()
    job = storage.load_job(job_id)

    if not job:
        error(f"任务不存在: {job_id}")
        raise SystemExit(1)

    if job.status not in ("generated", "pending"):
        error(f"任务状态不正确: {job.status}，需要为 generated 或 pending")
        raise SystemExit(1)

    try:
        schedule_id = do_schedule(job_id, time, title, description)
        success(f"定时任务已创建: {schedule_id}")
        info(f"  任务ID: {job_id}")
        info(f"  发布时间: {time}")
    except Exception as e:
        error(f"设置定时失败: {e}")
        raise SystemExit(1)


@jobs_group.command(name="schedules")
def list_schedules_cmd():
    """列出定时任务"""
    schedules = list_schedules()

    if not schedules:
        info("暂无定时任务")
        return

    console.print()
    console.print(f"[bold]定时任务 (共 {len(schedules)} 个)[/bold]")
    console.print()

    for sch in schedules:
        status_emoji = {
            "pending": "⏳",
            "retrying": "🔄",
            "executed": "✅",
            "failed": "❌",
        }.get(sch.get("status"), "❓")

        console.print(f"  {status_emoji} [bold]{sch['id']}[/bold] - {sch.get('status')}")
        console.print(f"      任务: {sch.get('job_id')}")
        console.print(f"      时间: {sch.get('schedule_time')}")
        if sch.get("title"):
            console.print(f"      标题: {sch.get('title')}")
        console.print()


@jobs_group.command(name="cancel-schedule")
@click.argument("schedule_id")
def cancel_schedule_cmd(schedule_id):
    """取消定时任务"""
    success = cancel_schedule(schedule_id)
    if success:
        success(f"定时任务已取消: {schedule_id}")
    else:
        error(f"定时任务不存在: {schedule_id}")
        raise SystemExit(1)


@jobs_group.command(name="delete")
@click.argument("job_id")
def delete_job(job_id):
    """删除任务"""
    storage = get_storage()
    success = storage.delete_job(job_id)

    if success:
        success(f"任务已删除: {job_id}")
    else:
        error(f"任务不存在: {job_id}")
        raise SystemExit(1)