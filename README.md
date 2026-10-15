# Personal Skill Collection

Reusable, open-source agent skills. Each skill is self-contained and uses the installer's own accounts and authorization.

| Skill | Purpose | Documentation |
| --- | --- | --- |
| [miro-read](skills/miro-read/SKILL.md) | Read and summarize your own Miro boards, with JSON/Markdown export and optional image inspection. Read-only; Python standard library. | [Install and use](skills/miro-read/README.md) |

## Install

Download a skill ZIP from this repository's **Releases** section and extract its skill folder into your agent's skill directory. For Codex, install `miro-read` at `~/.codex/skills/miro-read`, with `SKILL.md` directly inside. Other Agent Skills-compatible tools can use their documented skill directories.

Alternatively, clone this repository and copy only the desired folder from `skills/`. The source folders include their own instructions, license, helper scripts and synthetic tests. Existing installations should be preserved until differences have been reviewed.

Miro access requires your own connected Miro read tool or your own authorized `MIRO_ACCESS_TOKEN`. See the [setup guide](skills/miro-read/references/setup.md). No credentials, board exports, private project material or machine-specific paths are bundled. Board exports remain local unless you explicitly choose to share them.

## 中文

通用开源 skill 集合。当前提供 **Miro 只读阅读**：使用你自己的账号授权和看板链接，可分页读取、导出 Markdown/JSON，并按需查看图片。

从 **Releases** 下载 ZIP，解压后把 `miro-read` 文件夹放进你的 skill 目录；也可以克隆仓库，复制 `skills/miro-read`。不包含预置账号、看板、项目资料或个人配置。详细步骤见 [miro-read 使用说明](skills/miro-read/README.md)。

Licensed under [MIT](LICENSE).
