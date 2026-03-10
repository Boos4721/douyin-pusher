# Sora Pusher Skill

AI 视频生成与社交媒体自动化发布技能。基于 OpenClaw 的浏览器能力实现。

## 🚀 功能
- **视频生成**：调用 Seedance 2.0 / Sora 2 API 生成高画质视频。
- **自动发布**：基于 `browser` 助手将生成的视频发布到抖音（Douyin）等平台。
- **任务流水线**：实现从文本 Prompt 到视频文件，再到社交媒体发布的端到端自动化。

## 📁 目录结构
- `SKILL.md`: 技能核心定义。
- `scripts/`: 核心逻辑脚本（包含 `video_gen.py` 生成逻辑）。
- `references/`: 平台发布流程说明。

## 🛠️ 配置要求
- `SEEDANCE_API_KEY`: Seedance 2.0 访问密钥（获取自 [Atlas Cloud](https://api.atlascloud.ai) 或对应服务商）。
- 抖音登录状态：建议先使用 `browser` 助手手动登录一次 `https://creator.douyin.com/`，OpenClaw 会自动保持 Session。

## 📝 核心规则 (Rules)
1. **生成流程**：使用 `python3 ~/.openclaw/skills/sora-pusher/scripts/video_gen.py --prompt "[提示词]"` 生成视频。
2. **发布流程**：生成后，需调用 `browser` 助手前往抖音创作者中心上传。
3. **超时处理**：生成任务默认超时时间为 600 秒，若超过此时间需提醒用户。
4. **异常重试**：网络请求失败时应自动重试 3 次。

## 📖 使用示例
- "帮我用 Seedance 生成一段赛博朋克风格的视频并发布到抖音，标题是：未来已来"
- "把这段描述转成 1080p 视频发抖音，提示词是：[具体描述]"

## 🤝 鸣谢
- 流程参考 [social-push](https://github.com/jihe520/social-push)
- 理念参考 [page-agent](https://github.com/alibaba/page-agent)
