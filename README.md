# Personal Skill Collection

个人技能索引与可复用源码。盘点日期：2026-10-19。

共 **19 个用户安装的顶层技能**：本次收录 **12 个源码目录**，另 **7 个第三方技能仅记录用途**。嵌套子技能列在 [机器可读目录](catalog/skills.json)；它们不是额外的顶层安装。

| 分类 | 技能 | 负责什么 | 收录方式 |
| --- | --- | --- | --- |
| 协作规范 | `anti-sycophancy` | 基于证据回答，避免迎合与虚假确定性。 | 仅目录 |
| 游戏制作 | [boardgame-reskin-pipeline](skills/boardgame-reskin-pipeline/SKILL.md) | 桌游移植、换皮、生产素材与终局验收。 | 源码 |
| 云开发 | `cloudbase` | 腾讯云开发总入口，涵盖认证、数据库、云函数和部署。 | 仅目录 |
| 游戏制作 | `game-development` | 游戏开发总入口及引擎、平台、美术、音效等子技能。 | 仅目录 |
| 游戏制作 | [game-team](skills/game-team/SKILL.md) | 按需组织策划、程序、美术、UI、QA与审计职责。 | 源码 |
| 协作规范 | [github-pr-api](skills/github-pr-api/SKILL.md) | GitHub 提交、推送、PR及认证故障处理。 | 源码 |
| 游戏制作 | [godot](skills/godot/SKILL.md) | Godot 场景、脚本、资源、检查和导出工具链。 | 源码 |
| 素材生产 | [imaginarium-model-godot-creator](skills/imaginarium-model-godot-creator/SKILL.md) | Imaginarium 生成模型，经 Blender 处理后接入 Godot。 | 源码 |
| 文档设计 | `knowledge-cat-ppt-skill` | 演示稿故事结构、制作、评审和修复。 | 仅目录 |
| 文档设计 | [miro-read](skills/miro-read/SKILL.md) | 只读获取、总结和导出 Miro 白板。 | 源码 |
| 安全审查 | `security-best-practices` | Python、JS/TS、Go 安全最佳实践审查。 | 仅目录 |
| 安全审查 | `security-threat-model` | 根据仓库证据建立威胁模型。 | 仅目录 |
| 素材生产 | [ui-placeholder-replacement](skills/ui-placeholder-replacement/SKILL.md) | 把临时按钮、底板与框体替换为生产皮肤并验收。 | 源码 |
| 文档设计 | `ui-ux-pro-max` | UI/UX 风格、配色、字体、布局与交互检索。 | 仅目录 |
| 微信测试 | [wechat-multiactor-testing](skills/wechat-multiactor-testing/SKILL.md) | 微信开发者工具多账号、多实例隔离与通道验证。 | 源码 |
| 微信测试 | [wechat-package-slimming](skills/wechat-package-slimming/SKILL.md) | 微信小游戏素材和包体优化。 | 源码 |
| 协作规范 | [chatgpt-glm-communicate](skills/chatgpt-glm-communicate/SKILL.md) | 通过已登录的真实网页进行 ChatGPT 与 GLM 对话交接。 | 源码 |
| 微信测试 | [wechat-minigame-qa](skills/wechat-minigame-qa/SKILL.md) | 微信小游戏画布交互、完整对局、规则与卡死检查。 | 源码 |
| 素材生产 | [zcode-image-gen](skills/zcode-image-gen/SKILL.md) | 通过椒图网页或无头浏览器生成和下载图片。 | 源码 |

## 怎么选

- 游戏总体开发：`game-team` 负责分工与交付，`game-development` 负责技术路由；Godot 实现使用 `godot`。
- 桌游移植：`boardgame-reskin-pipeline` 串联规则、设计、素材生产与验收。
- 素材制作：`imaginarium-model-godot-creator` 负责模型，`zcode-image-gen` 负责图片，`ui-placeholder-replacement` 负责皮肤接入与自检。
- 微信验证：`wechat-minigame-qa` 负责游戏验收，`wechat-multiactor-testing` 负责多账号和实例隔离，`wechat-package-slimming` 负责包体。
- 协作与资料：`github-pr-api` 负责 GitHub 交付，`miro-read` 负责只读白板；其余工具按表中用途选择。

## 安装

克隆仓库，将需要的 `skills/<名称>` **整个文件夹**复制到自己的技能目录，例如 `~/.codex/skills/<名称>/`，确保 `SKILL.md` 直接在该目录中。已有安装先对比，不直接覆盖。

这些是技能说明和辅助脚本，不提供宿主工具、引擎、账号或云环境。脚本依赖和宿主 API 以各技能说明及本机可用能力为准。旧版 ZCode/IAB 接口不保证能在当前 Codex 直接调用；椒图脚本需自行安装 npm 依赖、配置浏览器并手动登录。免费额度、模型名与网站行为需要使用时重新核实。

## 导出范围与许可

- 仅盘点两个用户技能目录；`.system` 的内置技能和插件缓存不作为个人源码上传。
- 第三方大包仅保留目录：避免复制大型数据集、平台集成和独立更新链；安装时应从原安装渠道获取。此目录不是它们的可安装副本。
- `godot` 保留原作者 MIT 许可；上游来源见 [来源记录](catalog/skills.json)。其他现有许可文件原样保留，各目录的原许可优先于仓库总许可；不能把整个本机技能集合统一认定为 MIT。
- 不包含登录票据、cookies、密钥、浏览器会话、node_modules、缓存、截图、生成文档或下载的站点脚本。没有读取认证目录。项目专属配置已替换为说明占位，本机用户名路径已改为 `YOUR_USER` 示例。
- 本次检查覆盖导出文件、目录一致性、JSON和Python语法；未重新执行每个技能涉及的引擎、云端、生图和实机工作流。源码收录不等于这些工作流已经端到端验证。

## 内置技能补充

当前本机 `.system` 另有 `imagegen`（图像生成）、`openai-docs`（OpenAI产品资料）、`skill-creator`（技能创建）和 `skill-installer`（技能安装）。通过宿主提供，不在本仓库复制。
