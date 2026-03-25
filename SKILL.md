---
name: douyin
description: |
  抖音全能 Skill：搜索、下载、发布、互动、热榜、直播、数据看板。
  支持 AI 视频生成（即梦AI、小云雀、Atlas Sora）。
metadata:
  trigger: 抖音相关操作（搜索、下载、发布、热榜、直播、数据、评论、AI视频生成）
---

# 抖音统一 Skill

本 Skill 整合多套引擎：
- **API Client**（httpx 逆向 API）：搜索、下载、评论、热榜、直播、用户 — 即时响应
- **Playwright**（浏览器自动化）：发布、登录、数据看板、通知、AI视频生成 — 按需启动
- **火山引擎 API**：即梦AI视频生成

## 目录结构

```
douyin/
├── SKILL.md
├── src/dy_cli/
│   ├── main.py
│   ├── engines/
│   │   ├── api_client.py
│   │   └── playwright_client.py
│   ├── video_backends/        # AI 视频生成后端
│   │   ├── jimeng.py          # 即梦AI网页版
│   │   ├── seedance.py        # 即梦API (火山引擎)
│   │   ├── xyq.py             # 小云雀网页版
│   │   └── sora.py            # Atlas Sora API
│   ├── services/              # 业务服务
│   │   ├── storage.py         # 任务存储
│   │   ├── prompt_opt.py      # LLM 提示词优化
│   │   ├── scheduler.py       # 定时发布
│   │   └── comment_reply.py   # 评论自动回复
│   ├── commands/
│   │   ├── search.py, download.py, publish.py
│   │   ├── trending.py, live.py, analytics.py
│   │   ├── auth.py, profile.py, interact.py
│   │   ├── gen.py              # AI 视频生成
│   │   ├── jobs.py             # 任务管理
│   │   └── comment_bot.py      # 评论机器人
│   └── utils/
│       ├── config.py, output.py, signature.py
└── config/
    └── accounts.json.example
```

## 工具选择指南

| 操作 | 用哪个 | 命令 |
|------|--------|------|
| 搜索视频 | API | `dy search "关键词"` |
| 无水印下载 | API | `dy download URL` |
| 热榜 | API | `dy trending` |
| 视频详情 | API | `dy detail AWEME_ID` |
| 评论列表 | API | `dy comments AWEME_ID` |
| 用户资料 | API | `dy profile SEC_USER_ID` |
| 直播信息 | API | `dy live info ROOM_ID` |
| 直播录制 | API + ffmpeg | `dy live record ROOM_ID` |
| **发布视频/图文** | Playwright | `dy publish -t 标题 -c 描述 -v 视频` |
| **扫码登录** | Playwright | `dy login` |
| **数据看板** | Playwright | `dy analytics` |
| **AI 视频生成** | Playwright/API | `dy gen create ...` |
| **评论自动回复** | 定时任务 | `dy comment-bot run` |

---

## Part 1: API 工具（搜索/下载/采集）

### 搜索

```bash
dy search "AI创业"
dy search "咖啡" --sort 最多点赞 --time 一天内
dy search "科技" --type video --count 50 --json-output
```

参数:
- `--sort`: 综合 | 最多点赞 | 最新发布
- `--time`: 不限 | 一天内 | 一周内 | 半年内
- `--type`: general | video | user

### 下载

```bash
dy download https://v.douyin.com/xxxxx/
dy download 1234567890
dy download URL --music --output-dir ~/Videos
dy download URL --json-output    # 仅输出链接
```

### 热榜

```bash
dy trending
dy trending --count 20
dy trending --watch              # 每 5 分钟刷新
dy trending --json-output
```

### 视频详情

```bash
dy detail AWEME_ID
dy detail AWEME_ID --comments
dy detail AWEME_ID --json-output
```

### 评论

```bash
dy comments AWEME_ID
dy comments AWEME_ID --count 50 --json-output
```

### 用户

```bash
dy profile SEC_USER_ID
dy profile SEC_USER_ID --posts --post-count 30
dy me
```

### 直播

```bash
dy live info ROOM_ID
dy live info ROOM_ID --json-output
dy live record ROOM_ID                   # 需要 ffmpeg
dy live record ROOM_ID --quality HD1
```

---

## Part 2: Playwright 工具（发布/登录/数据）

### 前置条件

```bash
pip install playwright
playwright install chromium
```

### 登录

```bash
dy login                        # 打开浏览器扫码
dy status                       # 检查登录状态
dy logout                       # 退出登录
```

Cookie 存储位置: `~/.dy/cookies/{account}.json`

### 发布

```bash
# 视频
dy publish -t "标题" -c "描述" -v video.mp4
dy publish -t "标题" -c "描述" -v video.mp4 --tags 旅行 --tags 美食

# 图文
dy publish -t "标题" -c "描述" -i img1.jpg -i img2.jpg

# 选项
dy publish ... --visibility 仅自己可见     # 私密
dy publish ... --schedule "2026-03-16T08:00:00+08:00"  # 定时
dy publish ... --thumbnail cover.jpg       # 封面
dy publish ... --headless                  # 无头模式
dy publish ... --dry-run                   # 预览不发布
```

### 数据看板

```bash
dy analytics
dy analytics --csv data.csv
dy analytics --json-output
```

### 通知

```bash
dy notifications
dy notifications --json-output
```

---

## Part 3: AI 视频生成

### 支持的后端

| 后端 | 名称 | 来源 | 认证方式 | 模型 |
|------|------|------|----------|------|
| **jimeng** | 即梦AI网页版 | https://jimeng.jianying.com | cookies | seedance-2.0, seedance-2.0-fast |
| **seedance** | 即梦API | 火山引擎 | VOLC_ACCESSKEY/SECRETKEY | jimeng-pro, jimeng-720p, jimeng-1080p |
| **xyq** | 小云雀 | https://xyq.jianying.com | cookies | seedance-2.0, seedance-2.0-fast |
| **sora** | Atlas Sora | API | ATLAS_API_KEY | sora-2 |

### 前置条件

1. **导出 Cookies**（jimeng/xyq 网页版）:
   - 在浏览器中登录 jimeng.jianying.com 或 xyq.jianying.com
   - 使用 EditThisCookie 插件导出 cookies
   - 保存到 `~/.dy/cookies/jimeng.json` 或 `~/.dy/cookies/xyq.json`

2. **设置环境变量**（seedance/sora API）:
   ```bash
   export VOLC_ACCESSKEY="your-access-key"
   export VOLC_SECRETKEY="your-secret-key"
   export ATLAS_API_KEY="your-atlas-api-key"
   ```

### 提示词优化

```bash
# 使用 LLM 优化提示词
dy gen prompt-opt -p "一只猫在跑"

# 指定 provider (openai/claude/rule)
dy gen prompt-opt -p "一只猫在跑" --provider openai
```

优化原则：**主体 + 动作 + 风格 + 镜头 + 环境**

### 创建生成任务

```bash
# 即梦AI网页版
dy gen create -b jimeng -m seedance-2.0 -p "一只猫在草地上奔跑"

# 即梦API (火山引擎)
dy gen create -b seedance -m jimeng-pro -p "一只猫在草地上奔跑"

# 小云雀
dy gen create -b xyq -m seedance-2.0 -p "一只猫在草地上奔跑"

# Atlas Sora
dy gen create -b sora -m sora-2 -p "一只猫在草地上奔跑"

# 常用选项
dy gen create -b jimeng -m seedance-2.0 -p "..." --run-now      # 立即生成
dy gen create -b jimeng -m seedance-2.0 -p "..." -t "标题"      # 视频标题
dy gen create -b jimeng -m seedance-2.0 -p "..." -d "描述"      # 视频描述
dy gen create -b jimeng -m seedance-2.0 -p "..." -s "2026-03-30 10:00"  # 定时发布
```

### 任务管理

```bash
# 列出任务
dy jobs list
dy jobs list --status generated

# 查看任务详情
dy jobs show JOB_ID

# 设置定时发布
dy jobs schedule JOB_ID -t "2026-03-30 10:00" -t "视频标题"

# 列出定时任务
dy jobs schedules

# 取消定时任务
dy jobs cancel-schedule SCHEDULE_ID

# 执行待处理任务 (适合 cron 调用)
dy jobs run-pending

# 删除任务
dy jobs delete JOB_ID
```

### 视频生成列表

```bash
dy gen list
dy gen list --status generating
dy gen show JOB_ID
```

---

## Part 4: 评论自动回复

### 前置条件

```bash
# 启用评论机器人
dy comment-bot enable

# 配置
dy config set comment_bot.check_interval 60    # 检查间隔(秒)
dy config set comment_bot.max_replies_per_run 10  # 每轮最大回复数
dy config set comment_bot.policy whitelist     # 策略: whitelist / all
```

### 使用

```bash
# 单次执行
dy comment-bot run
dy comment-bot run --limit 5

# 启动循环模式
dy comment-bot loop

# 查看状态
dy comment-bot status

# 列出评论
dy comment-bot list
dy comment-bot list --unreplied-only

# 启用/禁用
dy comment-bot enable
dy comment-bot disable
```

---

## Part 5: 配置与运维

### 配置文件

`~/.dy/config.json`:

```bash
# 查看配置
dy config show

# API 配置
dy config set api.proxy http://127.0.0.1:7897
dy config set api.timeout 60

# Playwright 配置
dy config set playwright.headless true

# 下载目录
dy config set default.download_dir ~/Videos

# LLM 配置 (提示词优化)
dy config set llm.provider openai       # openai / claude / rule
dy config set llm.model gpt-4o

# 视频后端配置
dy config set video_backends.jimeng.cookies_path ~/.dy/cookies/jimeng.json
dy config set video_backends.seedance.ak_env VOLC_ACCESSKEY
dy config set video_backends.seedance.sk_env VOLC_SECRETKEY
dy config set video_backends.xyq.cookies_path ~/.dy/cookies/xyq.json

# 评论机器人配置
dy config set comment_bot.enabled true
dy config set comment_bot.check_interval 60
dy config set comment_bot.policy whitelist
```

### 多账号

```bash
dy account list
dy account add work
dy account default work
dy login --account work
dy search "关键词" --account work
```

### 登录态维护
- Cookie 存储在 `~/.dy/cookies/`
- 过期后需重新 `dy login` 扫码
- 不同账号 Cookie 文件独立

### 积分优化策略 (Seedance)

| 阶段 | 命令 | 积分 |
|------|------|------|
| 测试 | `--model seedance-2.0-fast --duration 5s` | 15积分/次 |
| 正式 | `--model seedance-2.0 --duration 10s` | 50积分/次 |

### 常用描述词

- **景别**: 特写、近景、中景、远景、全景、鸟瞰
- **运镜**: 推镜、拉镜、升镜头、降镜头、环绕镜头
- **光线**: 自然光、电影级光影、霓虹灯光、月光
- **氛围**: 烟雾弥漫、雾气弥漫、背景虚化、水下摄影

### 注意事项
- 抖音签名算法 (a-bogus) 频繁更新，搜索/下载功能可能需要定期适配
- 创作者中心 UI 也会更新，发布功能可能需要调整选择器
- 批量操作建议加 2-5 秒延时，避免触发风控
- AI 视频生成需要 cookies 保持登录状态，过期后需重新导出
- 所有命令支持 `--json-output` 输出机器可读格式
- 所有命令支持 `--account` 指定账号