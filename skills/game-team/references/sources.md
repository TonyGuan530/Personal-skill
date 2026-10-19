# 参考依据与取舍

查阅日期：2026-09-22。本技能是针对用户七角色框架的实践综合，不是任何组织发布的“游戏 Vibe Coding 行业标准”。仅提炼短小原则，不复制外部指令。来源里的推广、引擎偏好、版本价格、模型成绩不作为通用规则。

| 来源 | 借鉴内容 | 在本技能中的落点与限制 |
|---|---|---|
| [OpenAI：Build skills](https://learn.chatgpt.com/docs/build-skills) | 技能入口、参考文件、按需加载 | 一个主技能，细节分参考文件；不是七个永久运行的代理 |
| [OpenAI：AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | 持久项目上下文和分层指令 | 将通用工作流与项目事实分开；规则模板只按需合并 |
| [OpenAI：Rules](https://learn.chatgpt.com/docs/agent-configuration/rules) | 命令执行规则的用途 | 团队职责不写入 `.rules` |
| [Pirate Software：Develop Games](https://develop.games/) | 从小项目获得反馈，持续维护设计范围，按游戏选工具 | 最小可玩循环与范围控制；不沿用作者对具体引擎的推荐 |
| [GitHub：Custom instructions for code review](https://docs.github.com/en/copilot/tutorials/customize-code-review) | 指令要具体，从小集合开始，用实际结果迭代 | 短入口、具体交接字段、场景验证；Copilot 专有机制不照搬到 Codex |
| [GameDevBench 研究摘要](https://arxiv.org/abs/2602.11103) | 游戏开发涉及多模态任务，视觉反馈值得纳入验证 | 运行与视听证据并重；摘要不是本技能可靠性证明，研究结果不外推所有引擎 |
| [Game Accessibility Guidelines：Basic](https://gameaccessibilityguidelines.com/basic/) | 输入、可读性、色彩／声音信息和基础设置的可访问性考虑 | 按玩法与交付范围选择检查，避免把整份指南变成每次强制新增功能 |

七角色映射、任务交接字段、单一场景写入者、集成证据绑定和流程分级是本技能的设计选择，并非上述来源共同规定的标准。新项目使用时仍需根据真实限制调整。
