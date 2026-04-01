# Dreamina (即梦) 集成指南

即梦是字节跳动的 AIGC 图像和视频生成平台，已集成到 dy-cli 中。

## 安装 dreamina CLI

### 快速安装

```bash
curl -fsSL https://jimeng.jianying.com/cli | bash
```

安装后，`dreamina` 命令将位于 `~/.local/bin/dreamina`。

### 验证安装

```bash
dreamina -h
```

## 在 dy-cli 中使用

### 登录

```bash
# 交互式登录（打开浏览器）
dy dreamina login

# 无头模式登录（适合 agent/远程使用）
dy dreamina login --headless
```

### 账号管理

```bash
# 查看账户余额
dy dreamina credit

# 查看余额（JSON 格式）
dy dreamina credit --json-output

# 退出登录
dy dreamina logout

# 重新登录
dy dreamina relogin
```

### 文生图 (text2image)

```bash
# 基本用法
dy dreamina text2image -p "一只可爱的猫咪"

# 指定比例
dy dreamina text2image -p "风景" --ratio 16:9

# 指定分辨率和模型
dy dreamina text2image -p "肖像" --resolution 4k --model 5.0

# 轮询等待结果
dy dreamina text2image -p "猫咪" --poll 60
```

**支持的比例**: 21:9, 16:9, 3:2, 4:3, 1:1, 3:4, 2:3, 9:16

**支持的分辨率**:
- 3.0/3.1: 1k, 2k
- 4.0/4.1/4.5/4.6/5.0/lab: 2k, 4k

**支持的模型**: 3.0, 3.1, 4.0, 4.1, 4.5, 4.6, 5.0, lab

### 文生视频 (text2video)

```bash
# 基本用法
dy dreamina text2video -p "猫咪在草地上奔跑"

# 指定时长
dy dreamina text2video -p "海浪" --duration 10

# 使用高质量模型
dy dreamina text2video -p "城市夜景" --model seedance2.0
```

**支持的时长**: 4-15 秒

**支持的模型**:
- seedance2.0fast (默认，速度优先)
- seedance2.0 (质量优先)

### 图生视频 (image2video)

```bash
# 基本用法
dy dreamina image2video -i photo.jpg -p "镜头缓慢推进"

# 指定时长和模型
dy dreamina image2video -i photo.jpg -p "相机移动" --duration 8 --model 3.5pro
```

**支持的模型**: 3.0, 3.0fast, 3.0pro, 3.5pro, seedance2.0, seedance2.0fast

### 多帧图生视频 (multiframe2video)

多张图片生成连贯的视频故事：

```bash
# 查看完整帮助
dy dreamina multiframe2video --help
```

### 多模态生视频 (multimodal2video)

旗舰模式，支持图片、视频、音频等多种参考：

```bash
# 查看完整帮助
dy dreamina multimodal2video --help
```

### 其他生成命令

```bash
# 图生图
dy dreamina image2image --help

# 图片超分
dy dreamina upscale --help

# 首尾帧生视频
dy dreamina frames2video --help
```

### 任务管理

```bash
# 列出所有任务
dy dreamina tasks

# 按状态筛选
dy dreamina tasks --gen-status success

# 查询特定任务结果
dy dreamina query <submit_id>

# JSON 输出
dy dreamina query <submit_id> --json-output
```

### 透传模式

直接使用 dreamina CLI 的所有功能：

```bash
# 透传任意参数
dy dreamina raw -- text2image --help
dy dreamina raw -- user_credit
dy dreamina raw -- list_task --gen_status=querying
```

## 作为 OpenClaw Skill 使用

项目已包含 dreamina skill，位于 `.openclaw/skills/dreamina/SKILL.md`。

当你需要使用即梦的 AI 生成功能时，OpenClaw 会自动识别并使用该 skill。

你也可以将 skill 链接到 OpenClaw 的 skills 目录：

```bash
ln -s $(pwd)/.openclaw/skills/dreamina ~/.openclaw/skills/dreamina
```

## 注意事项

1. **额度消费**: 所有生成操作都会消耗即梦账户额度
2. **异步任务**: 大部分生成任务是异步的，需要使用 `query` 命令查询结果
3. **模型授权**: 部分高内容安全风险模型在首次使用前，可能需要先在 Dreamina Web 端完成授权确认
4. **Seedance 2.0**: 旗舰视频生成模型，质量最高但可能需要更长时间
5. **权限**: 确保 `dreamina` 命令在 PATH 中，或者使用完整路径

## 故障排查

### "dreamina CLI 未安装"

确保已运行安装脚本：

```bash
curl -fsSL https://jimeng.jianying.com/cli | bash
```

并且 `~/.local/bin` 在 PATH 中。

### "AigcComplianceConfirmationRequired"

需要先在 Dreamina Web 端完成授权确认，然后重试。

### 登录问题

使用 `--headless` 模式适合无头环境，或者使用 `relogin` 重新登录。
