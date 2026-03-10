# Sora Pusher Skill

AI 视频生成与社交媒体自动化发布技能。集成火山引擎 Seedance 2.0 与 OpenClaw 浏览器引擎。

## 🚀 功能
- **视频生成**：调用 **火山引擎 (Volcengine) Ark** 下的 Seedance 2.0 / Sora 2 模型生成视频。
- **自动发布**：驱动 `browser` 助手将生成的视频发布到抖音（Douyin）创作者中心。
- **任务流水线**：从生成、状态轮询到文件下载与上传的全流程自动化。

## 📁 目录结构
- `SKILL.md`: 技能核心定义。
- `scripts/`: 核心逻辑脚本。
  - `volc_gen.py`: 火山引擎 Seedance 2.0 专用生成脚本。
  - `video_gen.py`: 基于 Atlas Cloud 的备选生成脚本。
- `references/`: 平台发布流程。

## 🛠️ 配置要求
- `VOLC_API_KEY`: 火山引擎 Ark API 密钥。
- `VOLC_MODEL_ENDPOINT`: 火山引擎中 Seedance 2.0 的 **推理终端 ID**。
- 登录状态：需通过 `browser` 助手手动登录一次 `https://creator.douyin.com/`。

## 📝 核心规则 (Rules)
1. **生成流程**：使用 `python3 ~/.openclaw/skills/sora-pusher/scripts/volc_gen.py --prompt "[提示词]" --endpoint "[推理终端ID]"`。
2. **发布流程**：生成后自动调用 `browser` 助手执行上传与发布指令。
3. **超时与重试**：默认超时 900 秒，自动处理火山引擎 API 的异步状态。

## 📖 使用示例
- "用火山引擎生成一段赛博朋克风格的视频并发布到抖音，标题是：AI 浪潮"
- "把这段文字生成视频发抖音：[描述词]"

## 🤝 鸣谢
- 流程参考 [social-push](https://github.com/jihe520/social-push)
- 理念参考 [page-agent](https://github.com/alibaba/page-agent)
