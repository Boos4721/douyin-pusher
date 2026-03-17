---
name: sora2-pusher
description: >
  AI 视频生成与社交媒体自动化发布技能。支持通过 OpenAI Sora 2、火山引擎 Seedance 2.0 以及即梦AI视频生成3.0 生成高质量视频，并利用 PinchTab 自动发布到抖音创作者中心。
  使用触发词："用火山引擎生成视频", "用即梦生成视频", "把这段文字生成视频发抖音", "生成视频并发布"。
  支持：(1) 文生视频，(2) 图生视频，(3) 视频自动发布到抖音。
metadata:
  openclaw:
    homepage: https://github.com/Boos4721/sora2-pusher
    init: "pip3 install requests volcengine --break-system-packages && curl -fsSL https://pinchtab.com/install.sh | bash"
---

# Sora Pusher Skill

AI 视频生成与社交媒体自动化发布技能。集成火山引擎 Seedance / 即梦AI 与 PinchTab 浏览器控制引擎。

## 🚀 功能
- **视频生成**：调用 **火山引擎 Ark (Seedance 2.0)** 或 **即梦AI 3.0** 生成视频（支持文生视频与图生视频）。
- **自动发布**：驱动 `pinchtab` 命令将生成的视频发布到抖音（Douyin）创作者中心。
- **任务流水线**：从生成、状态轮询到文件下载与上传的全流程自动化。

## 📁 目录结构
- `SKILL.md`: 技能核心定义与规范。
- `scripts/`: 核心逻辑脚本。
  - `video/`: 视频生成模块（推荐使用）
    - `generator.py`: 统一视频生成器入口，支持多模型切换
    - `jimeng.py`: 即梦AI 3.0 生成器
    - `volc.py`: 火山引擎 Seedance 生成器
    - `atlas.py`: Atlas Cloud Sora 生成器
    - `optimizer.py`: 提示词优化器
    - `scheduler.py`: 定时任务调度
  - `douyin/`: 抖音自动化模块
    - `comment.py`: 评论管理
  - `cli.py`: 命令行工具
  - `agent.py`: OpenClaw 智能代理
  - `storage.py`: 数据持久化（Cookie、任务、评论）
  - `jimeng_gen.py`: 即梦AI 独立脚本（兼容旧版）
  - `volc_gen.py`: 火山引擎独立脚本（兼容旧版）
  - `video_gen.py`: Sora 独立脚本（兼容旧版）
- `references/`: 平台发布流程指南。

## 🛠️ 配置要求
- **火山引擎 Ark (Seedance)**: `VOLC_API_KEY` (API 密钥) 及 `VOLC_MODEL_ENDPOINT` (推理终端 ID)。
- **即梦AI**: `VOLC_ACCESSKEY` (AK) 及 `VOLC_SECRETKEY` (SK)。
- **Atlas Cloud Sora**: `ATLAS_API_KEY` (API 密钥)
- 登录状态：如果系统尚未登录抖音，Agent 需要访问创作者中心，获取登录二维码的截图并回传给用户（如在飞书/TG中发回），等待用户扫码完成后再执行后续发布。PinchTab 会持久化保存 profile。

## 🎯 推荐用法（使用统一模块）
推荐使用统一的 `VideoGenerator` 接口，支持自动模型选择：

```python
from video.generator import VideoGenerator

gen = VideoGenerator(model="auto")  # 自动选择最佳模型
# 或指定模型: jimeng-pro, jimeng-720p, jimeng-1080p, seedance, sora

# 生成视频
task_id = gen.generate(prompt="提示词", image="可选图片路径", duration=5)
video_url = gen.poll(task_id)
local_path = gen.download(video_url, "output.mp4")
```

或使用 CLI：
```bash
python scripts/cli.py gen "视频提示词" -m jimeng-pro -d 5 -o output.mp4
```

## 📝 核心规则 (Rules)
1. **模型与参数选择**：
   - 用户可用自然语言指定模型（如“用即梦3.0”、“用豆包Seedance”、“用Sora”等）。如果用户没有指定，默认推荐使用“即梦AI 3.0 Pro”。
   - **非常重要**：在执行生成任务前，务必检查对话历史中是否已经提供了对应的 API 凭证。如果对话中已经有 API Key 或 AK/SK，请直接提取并在命令行中传入，**不要**再向用户询问。只有在对话历史和环境变量中都找不到所需凭证时，才向用户索要。
2. **处理用户上传的图片 (多模态适配)**：
   - 核心系统 (如 OpenClaw) 接收飞书、Telegram 等渠道的用户消息时，可能会包含图片附件。
   - **非常重要**：如果用户随消息上传了图片附件，Agent 需要读取该附件的本地路径，并将此路径作为 `--image_path` 传入生成脚本，从而触发图生视频逻辑。
3. **统一生成流程（推荐）**：
   使用 `video.generator.VideoGenerator` 统一接口：
   ```python
   from video.generator import VideoGenerator

   gen = VideoGenerator(model="auto")  # 自动选择
   # 指定模型: jimeng-pro, jimeng-720p, jimeng-1080p, seedance, sora

   # 文生视频
   path = gen.generate_and_download(
       prompt="提示词",
       duration=5,
       aspect_ratio="16:9",
       output="output.mp4"
   )

   # 图生视频（仅 jimeng-pro, seedance 支持）
   path = gen.generate_and_download(
       prompt="提示词",
       image="图片路径或URL",
       duration=5,
       output="output.mp4"
   )
   ```
4. **兼容旧版脚本**：
   - **即梦AI**：`python3 scripts/jimeng_gen.py --model [pro|720p|1080p] --ak "[AK]" --sk "[SK]" --prompt "[提示词]"`
   - **火山引擎 Seedance**：`python3 scripts/volc_gen.py --api_key "[API_KEY]" --endpoint "[终端ID]" --prompt "[提示词]"`
   - **Sora (Atlas)**：`python3 scripts/video_gen.py --prompt "[提示词]"`
5. **发布流程**：生成成功并下载后（脚本输出 `RESULT_PATH:[路径]`），自动调用 `pinchtab` 命令行或 API 闭环执行上传与发布指令 (见 `references/douyin_publish.md`)。
6. **超时与重试**：默认超时 900 秒，自动处理异步状态轮询。

## 📖 使用示例
- "用即梦3.0 Pro生成一段赛博朋克风格的视频并发布到抖音，标题是：AI 浪潮"
- "用这张图片作为首帧，通过即梦生成一段无人机视角的飞行视频：[图片链接]"
- "用火山引擎Seedance生成视频并发抖音：[描述词]"

## 🤝 鸣谢
- 流程参考 [social-push](https://github.com/jihe520/social-push)
- 理念参考 [page-agent](https://github.com/alibaba/page-agent)
