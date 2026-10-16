# Personal Skill Collection

Reusable, open-source agent skills. Each skill is self-contained and uses the installer's own accounts and authorization.

| Skill | Purpose | Documentation |
| --- | --- | --- |
| [ui-placeholder-replacement](skills/ui-placeholder-replacement/SKILL.md) | Replace programmatic wireframe buttons and temporary UI panels with production skins; integrate and self-check across WeChat, Godot and web. | [Install and use](skills/ui-placeholder-replacement/README.md) |
| [miro-read](skills/miro-read/SKILL.md) | Read and summarize your own Miro boards, with JSON/Markdown export and optional image inspection. Read-only; Python standard library. | [Install and use](skills/miro-read/README.md) |

## Install

Download a skill ZIP from this repository's **Releases** section and extract its skill folder into your agent's skill directory. For Codex, install a folder such as `ui-placeholder-replacement` at `~/.codex/skills/ui-placeholder-replacement`, with `SKILL.md` directly inside. Other Agent Skills-compatible tools can use their documented skill directories.

Alternatively, clone this repository and copy only the desired folder from `skills/`. The source folders include their own instructions, license, helper scripts and synthetic tests. Existing installations should be preserved until differences have been reviewed.

Miro access requires your own connected Miro read tool or your own authorized `MIRO_ACCESS_TOKEN`. See the [setup guide](skills/miro-read/references/setup.md). No credentials, board exports, private project material or machine-specific paths are bundled. Board exports remain local unless you explicitly choose to share them.

## 中文

通用开源 skill 集合：

- **Placeholder UI 成品化**：针对程序化线框按钮、底板和框体，判断哪些需要替换，生成或复用成品皮肤，接入后自检。支持微信小程序/小游戏、Godot和网页，不限定画风或生图工具。
- **Miro 只读阅读**：使用你自己的账号授权和看板链接，可分页读取、导出 Markdown/JSON，并按需查看图片。

从 **Releases** 下载已发布的 ZIP，或克隆仓库并将需要的 `skills/<技能名>` 文件夹放入你的 skill 目录。不包含预置账号、看板、项目资料或个人配置。详细步骤见 [miro-read 使用说明](skills/miro-read/README.md)。

Licensed under [MIT](LICENSE).
