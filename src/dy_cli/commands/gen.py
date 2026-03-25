"""
dy gen — 视频生成命令组
"""
from __future__ import annotations

import os
import uuid

import click

from dy_cli.services.prompt_opt import get_provider_registry
from dy_cli.services.storage import VideoJob, get_storage
from dy_cli.utils.output import console, error, info, success
from dy_cli.video_backends import BACKENDS, BACKEND_MODELS, get_backend


@click.group(name="gen")
def gen_group():
    """视频生成命令组"""
    pass


@gen_group.command(name="prompt-opt")
@click.option("--backend", "-b", type=click.Choice(BACKENDS), default="jimeng",
              help="视频后端")
@click.option("--prompt", "-p", required=True, help="原始提示词")
@click.option("--provider", default=None, help="LLM provider (openai/claude/rule)")
def prompt_opt(backend, prompt, provider):
    """优化提示词"""
    info(f"原始提示词: {prompt}")

    from dy_cli.services import prompt_opt as prompt_opt_module
    optimized = prompt_opt_module.optimize_prompt(prompt, provider=provider)

    console.print()
    success("优化后的提示词:")
    console.print(f"  [bold cyan]{optimized}[/bold cyan]")
    console.print()


@gen_group.command(name="create")
@click.option("--backend", "-b", type=click.Choice(BACKENDS), required=True,
              help="视频后端")
@click.option("--model", "-m", required=True, help="模型名称")
@click.option("--prompt", "-p", required=True, help="生成提示词")
@click.option("--title", "-t", default="", help="视频标题 (用于发布)")
@click.option("--description", "-d", default="", help="视频描述 (用于发布)")
@click.option("--schedule", "-s", default=None, help="定时发布 (YYYY-MM-DD HH:MM)")
@click.option("--run-now", is_flag=True, help="立即生成视频")
@click.option("--duration", default=5, type=int, help="视频时长 (秒)")
@click.option("--aspect-ratio", default="16:9", help="视频比例")
def create(backend, model, prompt, title, description, schedule, run_now, duration, aspect_ratio):
    """创建视频生成任务"""
    # 验证模型
    valid_models = BACKEND_MODELS.get(backend, [])
    if model not in valid_models:
        error(f"无效的模型: {model}, 可用模型: {', '.join(valid_models)}")
        raise SystemExit(1)

    # 创建任务
    job_id = str(uuid.uuid4())[:8]
    storage = get_storage()

    job = VideoJob(
        id=job_id,
        backend=backend,
        model=model,
        prompt=prompt,
        status="pending",
        title=title,
        description=description,
    )

    if schedule:
        job.schedule_time = schedule
        job.status = "scheduled"

    storage.save_job(job)

    success(f"任务已创建: {job_id}")
    info(f"  后端: {backend}")
    info(f"  模型: {model}")
    info(f"  提示词: {prompt[:50]}...")
    if schedule:
        info(f"  定时: {schedule}")

    if run_now:
        info("开始生成视频...")
        _run_job(job_id, backend, model, prompt, duration, aspect_ratio)


@gen_group.command(name="list")
@click.option("--status", "-s", default=None, help="过滤状态")
@click.option("--limit", "-l", default=20, type=int, help="显示数量")
def list_jobs(status, limit):
    """列出视频生成任务"""
    storage = get_storage()
    jobs = storage.list_jobs(status=status, limit=limit)

    if not jobs:
        info("暂无任务")
        return

    console.print()
    console.print(f"[bold]视频生成任务 (共 {len(jobs)} 个)[/bold]")
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
        if job.generated_video_path:
            console.print(f"      视频: {os.path.basename(job.generated_video_path)}")
        console.print()


@gen_group.command(name="show")
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
    if job.error:
        console.print(f"  错误: {job.error}")
    console.print(f"  创建时间: {job.created_at}")
    console.print()


def _run_job(job_id: str, backend: str, model: str, prompt: str, duration: int, aspect_ratio: str):
    """执行任务"""
    storage = get_storage()
    backend_instance = get_backend(backend)

    # 更新状态
    storage.update_job(job_id, status="generating")

    try:
        # 生成视频
        task_id = backend_instance.generate(
            prompt=prompt,
            model=model,
            duration=duration,
            aspect_ratio=aspect_ratio,
        )

        # 对于异步后端，轮询结果
        if backend in ("jimeng", "sora"):
            info("等待视频生成...")
            video_url = backend_instance.poll(task_id)

            # 下载视频
            output_dir = os.path.expanduser("~/Downloads/douyin/videos")
            os.makedirs(output_dir, exist_ok=True)
            video_filename = f"{job_id}_{backend}.mp4"
            video_path = backend_instance.download(video_url, os.path.join(output_dir, video_filename))

            storage.update_job(
                job_id,
                status="generated",
                generated_video_url=video_url,
                generated_video_path=video_path,
            )
        else:
            # Seedance 同步完成
            video_path = backend_instance.poll(task_id)
            storage.update_job(
                job_id,
                status="generated",
                generated_video_path=video_path,
            )

        success(f"视频生成完成: {video_path}")

    except Exception as e:
        storage.update_job(job_id, status="failed", error=str(e))
        error(f"生成失败: {e}")
        raise SystemExit(1)