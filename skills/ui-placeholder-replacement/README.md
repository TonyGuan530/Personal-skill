# UI Placeholder Replacement

A portable Agent Skill for replacing programmatically drawn wireframe buttons, temporary panel backgrounds and plain UI frames with production skins: decide what needs replacement, generate or reuse suitable assets, integrate them, then inspect visuals and interaction in context.

Supports WeChat Mini Programs (WXML), Mini Games (Canvas), Godot, web apps, and equivalent UI systems. No project, theme, image provider, account or machine path is bundled. It preserves native semantics and existing behavior; a flat control is not automatically a placeholder.

## Install and use

Copy this entire `ui-placeholder-replacement` folder into your agent's skill directory, with `SKILL.md` directly inside. For Codex use `~/.codex/skills/ui-placeholder-replacement/`. For other Agent Skills-compatible tools use their documented skill directory. Review existing installations before replacing them.

Invoke `$ui-placeholder-replacement`, then provide screenshots, the project/component location and the intended scope. Example:

> 使用 $ui-placeholder-replacement，把这页明显占位的按钮和面板按现有画风成品化。先判断该保留/代码调整/生成什么，接入后自检小屏、状态、特效轮廓和点击。

Image generation, file editing and platform testing use tools available in the host environment and the user's own authorization. This skill supplies the decisions and checks; it does not supply an image service, credentials or runtime automation. Missing tools must be reported honestly.

## 中文

将本文件夹整体放入技能目录。主要处理程序化生成、仍像临时线框的按钮、底板和框体。核心流程是 **判断 → 生成或复用 → 接入 → 自检 → 定点返修**。支持微信小程序/小游戏、Godot和网页，不限定古风、某个项目或生图工具。

包含平台接入要点、生产素材与布局检查、透明边缘/轮廓/状态/输入自检，以及8个维护者行为验证场景。保留原生控件语义和动态文字；不把整屏概念图冒充可用UI。没有目标平台或真机证据时明确标记未测。

Licensed under [MIT](LICENSE).
