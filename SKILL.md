# Sora Pusher Skill

AI 视频生成与社交媒体自动化发布技能。

## 🚀 功能
- **视频生成**：调用 Seedance 2.0 / Sora 2 API 生成高画质视频。
- **自动发布**：基于 `browser` 助手将生成的视频发布到抖音等平台。
- **任务流水线**：从 Prompt 到 视频，再到 发布的全流程自动化。

## 📁 目录结构
- `SKILL.md`: 技能定义。
- `scripts/`: 核心逻辑脚本（Python/Node.js）。
- `references/`: 平台发布流程说明（Playwright/Browser 流程建议）。

## 🛠️ 配置要求
- `SEEDANCE_API_KEY`: Seedance 2.0 访问密钥。
- `DOUYIN_COOKIE`: 抖音登录状态（建议通过 `browser` 登录后自动复用）。

## 📖 使用示例
- "帮我用 Seedance 生成一段赛博朋克风格的视频并发布到抖音，标题是：未来已来"
- "把这段文字转成视频发抖音"
