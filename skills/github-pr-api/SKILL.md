---
name: github-pr-api
description: Use when a user asks to push code, submit or update a GitHub PR through the API, replace an older PR, or recover submission when the GitHub connector cannot access a repository.
---

# GitHub 提交与 PR API

代码通过标准 Git 推送，PR 通过 GitHub REST API 操作。用户仅要求解释、排查或创建 skill 时，不因此推送代码或修改 PR。创建 PR 不代表合入或发布。

## 认证与诊断

- 复用可用的标准认证：已登录的 `gh api`，或本 skill 的 [API helper](scripts/github_api.py) 读取用户明确配置的 `GH_TOKEN` / `GITHUB_TOKEN`。不要让用户把 token 发到聊天里。
- 不读取 Git credential helper、浏览器 cookie、密码库或其他应用的认证文件来提取 token；不在 URL、参数、源码、日志或返回消息中写 token。不要用卸载插件、修改全局权限或反复重新登录代替诊断。
- helper 使用 Python 3 标准库，无第三方依赖。运行 `python <skill目录>/scripts/github_api.py --help` 查看参数；JSON 请求体通过 UTF-8 文件传入，不能把 Markdown 拼成 shell 命令。
- 先 GET `/repos/OWNER/REPO`；需要核对账号时 GET `/user`。网页、Git、插件、REST API 的认证彼此不同：其中一路成功不证明另一路成功，插件 404 也不能证明用户本人无仓库权限。
- 401：认证无效；403：检查响应是否为权限、SSO 或速率限制；404：资源不存在或当前认证看不到，二者不能凭错误码区分；422：检查字段或重复 PR。对同一认证错误停止重复调用，明确缺少的凭据或权限。
- 只有用户已经配置 token，或标准 `gh auth status` 成功，才宣称 API 已可用。没有凭据时仍可完成本地整理和 PR 描述，最后明确阻塞。用户自己完成登录、令牌创建和仓库授权。
- 配置 token 前核对[官方 PAT 限制](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)。协作他人仓库时，不假定 fine-grained PAT 能选择该仓库；若当前限制不支持，应使用适用的标准登录或经用户配置的其他受支持凭据。只申请任务所需权限与有效期。

## 推送与提交

1. 遵守目标仓库的 AGENTS、PR 模板、测试与分支约定；核对 cwd、远端和实际仓库。先查看未提交修改与未完成的 merge/rebase，保留其他人的工作树。Git 所有权检查失败时只对已核对的目录使用单次 `-c safe.directory=绝对路径`，不写全局 `safe.directory=*`。
2. 检查当前分支及完整待交付差异。已有用户授权就执行同步、验证、显式暂存和提交；不要重复询问同一权限。不要强推、丢弃未知修改、自动 stash 或自动合入 main。
3. 成功 fetch 后在任务分支整合最新主干；读取冲突双方和共同基线。能保留双方已确认行为的局部冲突直接整合；玩法、布局或接口含义矛盾时给人具体选项。自动合并后也要检查调用方对已删除成员的引用。
4. 按实际改动跑必要检查；没有新改动或疑点不重复整套测试。报告真实失败，不能只看退出码忽略脚本错误。GUI 与人工 Smoke 分开记录。
5. 普通 `git push -u origin HEAD` 后，使用 `git ls-remote` 核对远端任务分支 SHA。推送失败不宣称已上传。不要只依赖本地 remote-tracking ref；单分支 clone 可能不会建立它。

## 创建或更新 PR

先保存按仓库模板写好的 PR 描述。先查重，再写入：

```text
GET /repos/OWNER/REPO/pulls?state=open&head=HEAD_OWNER%3ABRANCH&base=BASE
GET /repos/OWNER/REPO/pulls/NUMBER
POST /repos/OWNER/REPO/pulls
PATCH /repos/OWNER/REPO/pulls/NUMBER
```

对查询值做 URL 编码。`HEAD_OWNER` 是分支所在仓库的所有者，不是分支名中斜杠之前的字符串。例如同仓库分支 `TonyGuan530/hud-ui-optimization` 位于 `fyh828/MushroomDetective`，过滤 head 应为 `fyh828:TonyGuan530/hud-ui-optimization`。

- 若用户给了现有编号，先读该 PR，核对 head/base，不再创建重复 PR。查重存在一个相符 PR 时按授权更新；有多个或目标矛盾时解释并让用户决定。
- POST 请求体示例：`{"title":"中文标题","head":"任务分支","base":"main","body":"完整描述","draft":true}`。draft 状态按用户意图和真实交付状态选择，不自动修改已存在 PR 的状态。
- POST/PATCH 超时或断连，结果为未知：先 GET 查重或核对目标字段再决定后续动作，不能盲重放写请求。helper 不自动重试任何请求。
- 恢复未知创建结果时用 `state=all` 并处理分页，避免遗漏请求期间已关闭/合入的 PR；核对本次请求时间窗、head SHA、head/base 和标题，不能把旧的同分支 PR 当作本次创建结果。无法唯一判断就停止重放，报告结果未知。
- 成功后核对返回的编号、URL、head SHA、base 和状态；若有 `attach_artifact` 工具，把真实 PR URL 附到当前任务。只有 GitHub 返回真实编号或可靠页面证据时才称 PR 已创建；`pull/new`、compare 链接和预填页面不是 PR。
- 不自动发送 review 请求、评论或通知；用户明确授权时才发送。PR 创建/更新授权不自动包含合并、关闭其他 PR 或删除分支。

## 替代旧 PR

只有用户明确要求替代/关闭旧 PR 才做。先 GET 旧 PR 的**当前最新 head SHA**，不能只用历史缓存。fetch 该提交，用 `git merge-base --is-ancestor OLD_HEAD NEW_HEAD` 验证完整包含；失败就保留旧 PR，说明差异或按任务授权整合后再验证。

新 PR 成功建立且确认内容、编号、远端 SHA 后，再 GET 旧 PR 复核 head 未变化、仍未合入。若它在此期间推进，重新核对包含关系。满足这些条件才 PATCH `{"state":"closed"}`，最后 GET 确认状态。新 PR 创建失败时保留旧 PR。已经关闭/合入则如实报告，不为改状态而重开。

GET 与关闭 PATCH 不是原子操作：关闭后再次核对旧 head。若此时出现未被替代 PR 包含的新提交，且旧 PR 是本次操作关闭、尚未合入，则撤回本次关闭并报告竞态；不要重开操作前已关闭或已合入的 PR，也不要宣称完整替代。

## 完成说明

中文报告分支、提交、实际检查、人类验收状态、真实 PR 编号/链接及旧 PR 的实际状态。不能将“已提交”“已推送”“已提 PR”“已合入”混为一谈。凭据问题只要求本机配置，不要求在聊天粘贴秘密。

官方接口：[PR REST API](https://docs.github.com/en/rest/pulls/pulls)、[REST 认证](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api)、[GitHub App 的权限交集](https://docs.github.com/en/apps/using-github-apps/authorizing-github-apps#about-github-apps-acting-on-your-behalf)。
