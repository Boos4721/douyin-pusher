<p align="center">
  <h1 align="center">🎬 dy-cli</h1>
  <p align="center">Douyin (抖音/TikTok China) CLI — search, download, publish, trending, live, AIGC generation, and more.</p>
</p>

<p align="center">
  <a href="https://pypi.org/project/dy-cli/"><img src="https://img.shields.io/pypi/v/dy-cli.svg" alt="PyPI"></a>
  <a href="https://github.com/Boos4721/douyin-pusher/actions"><img src="https://github.com/Youhai020616/douyin/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/dy-cli/"><img src="https://img.shields.io/badge/python-≥3.10-blue.svg" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
</p>

<p align="center">
  <a href="#install">Install</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#commands">Commands</a> •
  <a href="#features">Features</a> •
  <a href="./LICENSE">License</a>
</p>

---

<p align="center">
  <img src="./demo.gif" alt="dy-cli demo" width="800">
</p>

## Install

```bash
pip install dy-cli
```

Or from source:

```bash
git clone https://github.com/Boos4721/douyin-pusher.git
cd douyin-pusher && bash setup.sh
```

## Quick Start

```bash
dy login                                # QR scan login (one time)
dy search "美食"                         # Search → results cached
dy read 1                               # Read 1st result (short index)
dy dl 1                                 # Download 1st result (no watermark)
dy like 1                               # Like 1st result
dy trending                             # Hot trending Top 50
dy publish -t "标题" -c "描述" -v video.mp4   # Publish video
dy dreamina text2image -p "a cat"       # AI image generation
```

## Features

- 🔍 **Search** — keyword search with sort/time/type filters, user search
- 📥 **Download** — no-watermark video/image with progress bar, batch user download
- 📝 **Publish** — video & image posts with tags, cover, scheduling, visibility
- 🔥 **Trending** — real-time hot search Top 50 with watch mode
- 📺 **Live** — stream info, URL extraction, ffmpeg recording
- 💬 **Interact** — like, favorite, comment, follow (Playwright)
- 📊 **Analytics** — creator dashboard via XHR interception
- 👤 **Profile** — user info, posts listing
- 🔢 **Short Index** — `dy search → dy read 1 → dy like 1 → dy dl 1`
- 📦 **Export** — `dy search "AI" -o results.csv` (JSON/CSV/YAML)
- 🎨 **Dreamina** — 即梦 AIGC image/video generation (text2image, text2video, image2video)
- 💡 **Prompt Optimization** — LLM-powered prompt enhancement for better generation results
- 📜 **History Management** — local SQLite/JSON storage for search and generation history
- 🔐 **Login** — QR scan + browser cookie auto-extraction
- 👥 **Multi-Account** — isolated cookie storage
- 🛡️ **Anti-Detection** — Gaussian jitter, exponential backoff, captcha cooldown

## Commands

### Search & Read

```bash
dy search "关键词"                        # Search videos
dy search "咖啡" --sort 最多点赞          # Sort by likes
dy search "日食记" --type user            # Search users
dy search "AI" -o results.csv            # Export to CSV
dy read 1                                # Read 1st result (short index)
dy detail AWEME_ID                       # Detail by ID
dy comments 1                            # View comments (Playwright)
```

### Download

```bash
dy dl 1                                  # Download by short index
dy download https://v.douyin.com/xxx     # Download by URL
dy download 1234567890 --music           # Also download BGM
dy dl SEC_USER_ID --user --limit 20      # Batch download user posts
```

### Trending & Live

```bash
dy trending                              # Top 50
dy trending --count 10 -o hot.json       # Export top 10
dy trending --watch                      # Auto-refresh every 5 min
dy live info ROOM_ID                     # Live stream info
dy live record ROOM_ID                   # Record with ffmpeg
```

### Publish

```bash
dy publish -t "标题" -c "描述" -v video.mp4                         # Video
dy publish -t "标题" -c "描述" -i img1.jpg -i img2.jpg              # Image post
dy publish -t "标题" -v v.mp4 --tags AI --visibility 仅自己可见      # Private + tags
dy publish -t "标题" -v v.mp4 --schedule "2026-03-20T08:00:00+08:00" # Scheduled
dy pub -t "标题" -v v.mp4 --dry-run                                  # Preview only
```

### Interact

```bash
dy like 1                                # Like (short index)
dy like 1 --unlike                       # Unlike
dy fav 1                                 # Favorite
dy comment 1 -c "好看!"                  # Comment
dy follow SEC_USER_ID                    # Follow user
```

### Profile & Analytics

```bash
dy me                                    # My login info
dy profile SEC_USER_ID --posts           # User profile + posts
dy analytics                             # Creator dashboard
dy notifications                         # Messages
```

### Account & Config

```bash
dy login                                 # QR scan login
dy login --browser                       # Extract cookies from browser
dy status                                # Login status
dy account list                          # List accounts
dy config show                           # Show config
dy config set api.proxy http://...       # Set proxy
```

### Dreamina (即梦 AIGC)

```bash
dy dreamina install                      # Install/update dreamina CLI
dy dreamina uninstall                    # Uninstall dreamina CLI
dy dreamina login                        # Login to Dreamina
dy dreamina login --headless            # Headless mode (for agents)
dy dreamina logout                       # Logout
dy dreamina credit                       # Check credit balance
dy dreamina text2image -p "a cat"       # Text to image
dy dreamina text2video -p "a cat"       # Text to video
dy dreamina image2video -i img.jpg -p "camera move"  # Image to video
dy dreamina tasks                        # List saved tasks
dy dreamina query SUBMIT_ID              # Query async task result
dy dreamina raw -- ...                   # Pass-through to dreamina CLI
```

详细使用指南请参考 [docs/dreamina.md](./docs/dreamina.md)。

### Prompt Optimization (提示词优化)

```bash
dy prompt optimize "一只猫"              # Optimize prompt (for OpenClaw LLM)
dy prompt optimize "一只猫" --style anime  # Specify style
dy prompt optimize "一只猫" --auto-apply  # Auto-apply to dreamina
dy prompt templates                     # Show prompt templates and styles
dy prompt save "my-prompt" "..."       # Save prompt
dy prompt list                          # List saved prompts
```

### History Management (历史记录)

```bash
dy history search                         # View search history
dy history search --keyword "AI"         # Filter by keyword
dy history gen                            # View generation history
dy history gen --task-type text2image   # Filter by task type
dy history gen --status success          # Filter by status
dy history clear --search --yes          # Clear search history
dy history clear --gen --yes             # Clear generation history
```

### Aliases

| Short | Command | | Short | Command |
|-------|---------|---|-------|---------|
| `dy s` | `search` | | `dy r` | `detail` (read) |
| `dy dl` | `download` | | `dy t` | `trending` |
| `dy pub` | `publish` | | `dy fav` | `favorite` |
| `dy cfg` | `config` | | `dy acc` | `account` |

## Architecture

| Engine | Used for | Technology |
|--------|----------|------------|
| **API Client** | Search, download, trending, live, profile | httpx + reverse-engineered API |
| **Playwright** | Publish, login, analytics, like, comment | Chromium browser automation |
| **dreamina CLI** | AIGC image/video generation | Official ByteDance Dreamina CLI |
| **Local Storage** | History, saved prompts | SQLite + JSON file storage |

## Platform Support

macOS ✅ &nbsp; Linux ✅ &nbsp; Windows ✅

## OpenClaw Integration

This project is designed for seamless use with OpenClaw:

- **SKILL.md** - Comprehensive skill documentation for OpenClaw
- **.openclaw/skills/dreamina/** - Dreamina sub-skill for AIGC generation
- **Prompt Optimization** - Built for LLM-powered prompt enhancement
- **Auto-install** - Dreamina CLI auto-installs in non-interactive environments

See [SKILL.md](./SKILL.md) for complete OpenClaw workflow examples.

## License

[MIT](./LICENSE)

## 🔗 Ecosystem

| Project | Description |
|---------|-------------|
| [AgentMind](https://github.com/Youhai020616/Agentmind) | Self-learning memory system for AI agents |
| [stealth-cli](https://github.com/Youhai020616/stealth-cli) | Anti-detection browser CLI powered by Camoufox |
| [stealth-x](https://github.com/Youhai020616/stealth-x) | Stealth X/Twitter automation |
| [xiaohongshu](https://github.com/Youhai020616/xiaohongshu) | Xiaohongshu automation |
| [freepost](https://github.com/Youhai020616/freepost-saas) | AI social media management |
