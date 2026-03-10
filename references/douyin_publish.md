# 抖音视频发布流程 (Browser 驱动版)

基于 `browser` 助手实现的抖音自动发布流程。

## 🚀 发布步骤

1. **登录抖音**:
   - `browser(action="open", url="https://creator.douyin.com/")`
   - 手动或自动扫描登录。登录成功后，OpenClaw 会通过 `profile` 自动持久化。

2. **点击上传**:
   - `browser(action="act", kind="click", ref="上传视频")`
   - 选择本地生成的 `output.mp4` 文件。

3. **配置参数**:
   - `browser(action="act", kind="type", ref="标题", text="[自定义标题]")`
   - 设置可见范围、定时发布等。

4. **确认发布**:
   - `browser(action="act", kind="click", ref="发布")`

## 🛠️ 注意事项
- 视频上传期间不要关闭浏览器。
- 如果提示“需要扫码”，OpenClaw 会自动截图发回，请在手机端配合完成。
