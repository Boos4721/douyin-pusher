# Sora2-Pusher

🤖 AI 视频生成与社交媒体自动化发布助手。基于 [OpenClaw](https://github.com/openclaw/openclaw) 架构，集成 Seedance 2.0 / Sora 2 视频生成能力，并实现抖音等平台的自动化发布。

## ✨ 特性

- **全自动流水线**：从文本 Prompt 到视频生成，再到社交媒体发布。
- **Seedance 2.0 集成**：支持最新一代 2K 高画质视频 co-generation。
- **Browser-in-the-Loop**：利用 OpenClaw 的浏览器助手复用用户登录状态，安全稳定发布。
- **模块化设计**：支持快速扩展其他视频模型（如 Kling, Veo）或其他社交平台（如小红书、X）。

## 📦 安装

1. 确保已安装并配置好 [OpenClaw](https://docs.openclaw.ai)。
2. 将本项目克隆到 OpenClaw 的技能目录：
   ```bash
   git clone git@github.com:Boos4721/sora2-pusher.git ~/.openclaw/skills/sora-pusher
   ```
3. 配置 API Key：
   在环境变量或 `openclaw configure` 中设置 `SEEDANCE_API_KEY`。

## 🚀 使用方法

在对话框中直接下达指令：
- "帮我生成一段[描述]的视频并发布到抖音，标题是：[标题]"
- "用 Seedance 生成视频，参考这张图[附件图片]，完成后发抖音"

## 📁 目录结构

- `SKILL.md`: 技能核心定义文件。
- `scripts/video_gen.py`: 视频生成逻辑（基于 Atlas Cloud API）。
- `references/douyin_publish.md`: 抖音自动化发布操作指南。

## 🤝 鸣谢

- 流程参考 [social-push](https://github.com/jihe520/social-push)
- 理念参考 [page-agent](https://github.com/alibaba/page-agent)
