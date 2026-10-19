---
name: zcode-image-gen
description: ZCode 所有生图任务的优先方案：无头浏览器 CLI（固定分辨率，稳定）驱动免费 AI 生图网站出图并下载到本地，支持文生图与图生图（传参考图）。凡用户要求生成图片/插画/海报/横幅/游戏素材/图标/立绘（如"生成一张xx""生图""画一张""出几张贴图"），或提到 zcode-image-gen、jiaotu、椒图、生图，一律优先使用本 skill，而不是手绘 SVG 或图片搜索。子方法：jiaotu（椒图AI jiaotu.ai，无头 CLI，微信扫码登录一次后 ticket 复用）。
---

# zcode-image-gen

ZCode 全局生图方案。**主路径：ZCode 内置浏览器（IAB）+ 固定视口 1280×1080 DPR=1**，通过免费生图网站椒图AI出图 → 取 CDN 原图 → 下载落盘。无头 CLI 为备选（仅文生图稳定）。
**所有生图需求默认走本 skill**；手绘 SVG 仅用于小图标/版式装饰这类矢量活。

方法注册表：

| 子方法 | 站点 | 定位 |
|---|---|---|
| `jiaotu`（IAB 固定视口） | https://jiaotu.ai/ （椒图AI） | 主力。文生图/图生图（修图），积分制 |
| `jiaotu`（无头 CLI 备选） | 同上 | 仅文生图（图生图发送不稳） |

## 主路径：IAB 固定视口（2026-09-28 起，默认且推荐）

**每次都固定视口 1280×1080 DPR=1**（`tab.setViewportSize` 在建 tab 后立即设置）。IAB 的提交点击实测可靠（多次成功），无头的带图发送会被站点吞掉。

### 依赖（一次性，已就位）

- IAB（ZCode 内置浏览器，browser-use 驱动）
- 登录票据：`~/.agents/skills/zcode-image-gen/auth/jiaotu-auth.json`（微信扫码一次后复用；**过期症状**：余额 0、项目列表空、提交静默失败 → 跑 `scripts/relogin.cjs` 弹窗扫码换票）
- 模型强制：goto 后注入 localStorage 时**覆盖 model 键为 最新图片V2 Pro**（queryModels 里 id=20），或下拉键盘导航 ↓×4+Enter

### IAB 稳定交互管线（在会话内按序执行）

1. **建 tab** → `setViewportSize({width:1280,height:1080})` → `goto https://jiaotu.ai/`（addInitScript 注入 auth localStorage，**model 键覆盖为 V2 Pro**）→ 等 3s。
2. **切快速**：evaluate 找「快速」文本元素中心 → `tab.cua.click`（DOM click 被拦截）。
3. **V2 Pro 校验**：读模型钮标签；不符则点开下拉 → `[data-state]` 行（文本以模型名开头）中心 cua 点击。
4. **填提示词**：`locator('textarea[placeholder^="试试输入"]').first().fill(prompt)`（React 友好）。
5. **图生图附图**：合成 paste 事件（DataTransfer + File → ClipboardEvent('paste') 派发到 textarea）——实测附件缩略图出现。
6. **发送**：textarea 右缘外 ~140px、同带高 ±320px 内**最下的 w30-64 圆钮** mouse 点击 → 2s 后校验 textarea 清空；未清空换下一候选；3 次后 Enter 兜底。
7. **收图**：只认当日 `cdn.jiaotuai.cn/.../2026/09/28/` 新图（差集+排除已知 hash）→ 页面内 fetch → base64 分块落盘。

### 积分与归档

- **单次 ≤6 花椒粒**：仅 1K 档（智能 1K 基础=5粒）；2K/4K/高质 拒绝。
- **归档：门塔特相关生成一律进「ZCODE」项目**（用户指定），除非用户要求更换。

### 出图后必 QC

Read 图片核对内容对题；带文字的图逐行核对文案。

## 出图提示词约定（门塔特桌游项目）

- **项目归档（2026-09-28 用户指定）：所有门塔特相关生成的图都放进椒图项目「ZCODE」**，除非用户要求更换。新建项目后在其项目内 composer 提交即可归档；首页直接提交会按提示词自动命名项目（需手动整理）。
- 通用：`中国古代商路桌游插画，<主体>，深棕木色+米色宣纸+鎏金配色，扁平桌游美术风格，无文字，干净背景<构图>`
- 3D/手游风：`微信小游戏 3D 界面概念图，Q版卡通渲染，色彩明亮干净，柔和光照，圆润造型，手游美术风格，无文字`
- 与 minigame UI 同色系：#2B1A12 / #F1E2C4 / #D8A84F / #F5D37A / #A6422B
- 游戏素材落 `art/<项目>/incoming/<用途>-<序号>.png`

## 备用路径：无头 CLI（仅文生图；图生图发送不稳）

以下为无头流程要点，仅在 IAB 不可用时应急：

1. IAB bootstrap → 找/开 jiaotu.ai 标签 → 视口 1280×1080 → 注入 auth localStorage。
2. 模式/模型/尺寸切换：evaluate 取矩形中心 → `tab.cua.click`；选中态用 snapshot/标签文字确认。
3. 提交：evaluate 强制 setter 填 textarea → cua 点 textarea 给焦点 → 找发送钮（w30-64、textarea 右缘外）cua 点击 → 校验清空。
4. 收割：KNOWN URL 集合差集轮询；下载用页面内 fetch→base64 分块拉回（IAB 截图/录像表面常超时，别依赖）。

## 已知坑（无头与 IAB 通用）

- 站点自定义按钮/下拉/选项拦截 DOM click——必须坐标点击（无头用 page.mouse，IAB 用 cua）。
- 隐藏的重复同名元素多：按 textContent 精确匹配 + rect 宽高/y 可见性过滤。
- 「固定 prompt」等小圆钮与发送钮相邻：发送钮=设置行最右、w30-64、仅在有输入内容时可见。
- 尺寸面板 Escape 关不掉，会遮挡发送钮。
- 队列异步：结果可能晚一拍落地；按 URL 差集取新图并 QC 对题。
- **图生图（--image）：✅ 端到端已验证**（filechooser 即测即点 + 盲等 8s + 发送重试；V2 Pro 下 "P掉人物与国旗" 完美通过）。此前失败根源是**旧票据过期**（症状：余额 0、项目列表空、提交静默失败）→ 跑 scripts/relogin.cjs 扫码换票即恢复。
- **项目页自动化慎用（2026-09-28）**：用户可能正在自己的 jiaotu 会话里操作——自动化打开/点击项目页会与真人互相干扰。需要进项目页时先跟用户确认，或只在用户明示后操作。新建项目的命名弹层自动化未跑通（项目以「未命名」创建，可后续经卡片「…」菜单重命名）。
