---
name: wechat-multiactor-testing
description: Configure and verify WeChat DevTools multi-account automation for mini games and mini programs. Use for desktop multiplayer test setup, CLI/MCP routing, actor isolation, and repeatable testing. Distinguishes Canvas input, virtual accounts, real cloud identity, and phone evidence.
metadata:
  version: "1.0.2"
---

# 微信多账号与自动化测试

把“多个账号”“多个可单独控制的运行实例”“服务端不同玩家”和“手机体验”分别证明。先完成工具链预检，再做授权范围内的测试；已有项目暂停指令不能由安装技能默默解除。

## 路由与预检

读实际项目的AGENTS、Git状态、project.config.json、测试环境及当前任务。compileType=game/gamePlugin使用Canvas坐标；miniprogram使用页面/selector。检查本机官方CLI帮助与随安装包的wechatide-skill，旧版SDK限制不推广成所有新版本不支持小游戏。本机RC 2.02.2609231的“工具→自动化测试”菜单明确以`!isGameProject`为启用条件，所以小游戏里变灰是该菜单的产品条件；不代表CLI/Canvas通道不存在。版本细节见[来源](references/sources.md)。

运行 [只读预检脚本](scripts/probe_wechat.py)：

```text
python scripts/probe_wechat.py --install-dir <微信工具安装目录> --project <项目绝对目录> --accounts
```

脚本只查版本、帮助、登录/令牌需求和测试账号数量，不输出账号、昵称或ticket，不启动对局、不部署。默认不列账号，--accounts才查询。--output指定一个不存在的JSON文件保存脱敏结果。异常/超时记录为工具状态，不能算游戏失败。

优先官方cli.bat管理自动化启动（auto-port/auto-account），内置wechatide命令驱动Canvas输入和截图。bridge按路径找不到CLI快照窗口时，使用[端口脚本](scripts/automator_port.cjs)连接本机官方Automator协议：默认只读，显式授权后才发送触摸；脚本只断言输入已由驱动接受，实际UI变化要以随后截图和游戏自己的只读状态核对。MCP只是同类接口的另一种传输；没有CLI缺失能力时不额外安装第三方MCP。安装新MCP前核查许可证、版本、权限和真实Canvas/账号路由，不能由名称判断功能。具体命令、脚本示例和已核限制见 [工具接口](references/tooling.md)。

## 多账号落地

1. 用`automation_testaccount --action list`查询**该接口的测试号列表**；本机实现只读`accountMap`中的已添加账号，而内置虚拟用户来自独立的`TestUserMap`，所以返回空列表不证明“工具→多账号调试”没有已打开的虚拟窗口。不要为消除这个差异让用户重复添加账号，也不要伪造openid、读取登录缓存或抓ticket。实际ID仅留本机运行配置或环境变量，报告用player-a/player-b别名；账号类别及云身份另证。
2. 冻结同一候选源码/资源。每个角色有独立账号、连接端口、运行上下文/存储和视角。原生auto使用--auto-account；不要臆造wechatide的--account/--window参数。当前bridge的Canvas命令只按project寻址，同项目多个账号窗口**不能据此保证**分别命中。
3. 用 [会话规划器](scripts/plan_sessions.py)校验角色配置（格式见[模板](assets/actors.example.json)）。它只输出命令参数数组，不执行、不创建工作树、不打开窗口、不预填PASS。账号从环境变量解析，不出现在输出。bridge-project路线要求两个不同的项目快照目录；sdk-port路线可同目录但必须验证SDK按端口绑定，Canvas能力另查。端口不同不等于实例不同；目录不同不等于账号不同。
4. 先确认每个现有窗口可独立寻址；没有账号/窗口/端口的可靠绑定时，停止在只读证据，不向某个未知窗口发触摸。本机`cli auto`实现会先关闭**同一项目路径**的窗口，故在共享IDE中只对新建的隔离项目快照启动它；不要把共享项目路径传给`auto`。每份快照冻结同一源码/资源并占用独立端口，启动响应仅证明端口建立。此版本的bridge按项目路径没有识别这些CLI自动化窗口；改用该端口绑定的官方Automator协议作只读探测（方法和界限见[工具接口](references/tooling.md)）。通道明确后分别截图、读取当前运行版本/视角，再对A做一次无业务写的本地UI动作，确认只有A变化，然后B同验。若第四个端口只响应版本而画布黑屏/超时，标记该角色BLOCKED，不能把四个监听端口当成四个可用玩家；不修补IDE或全局重启。
5. 接云之前验证两个角色经正式登录链取得**服务端可信的不同身份**；使用获准测试环境/测试数据，日志只记别名及不含原ID的等异比较。客户端改昵称、mock WXContext/本地多座位不算真实身份。没有测试环境或账号资格时保留BLOCKED，先完成可独立的工具与隔离测试。

## 执行与证据

Canvas触摸走官方automation_game_action，或已核实绑定目标角色的Automator端口`Tool.invokeGameMethod`；截图坐标带原图宽高，或用逻辑画布坐标，不重复乘DPR。已核安装包把`touchstart/touchend`转成`Driver.game.touchstart/touchend`；端口脚本记录唯一请求ID、事件序号、映射后的逻辑坐标和截图哈希。工具返回`status=0`只证明事件交给驱动，游戏状态和画面仍需独立验证。evaluate用于只读诊断；直接调用规则dispatch/onTap不能替代输入证据。小程序WXML自动化不能作为小游戏支持证明。端口探测可用本地`showToast`做初步隔离，但完整UI输入证据应采用真实画布触摸。

已有wechat-minigame-qa可承担完整对局、外部超时监督和规则验证；本技能负责账号/通道/多角色运行前提，不复制另一套规则驱动。无该技能也可按[多人验收矩阵](references/scenarios.md)记录输入→权威状态→双方画面。测试脚本设有限步数、墙钟期限和停滞阈值，只停自己的worker，不全局quit或清缓存。

报告至少列：候选、工具/基础库、角色数/身份类别、路由/隔离证据、真实或虚拟时钟、输入方法、环境类别、正常终局、失败复现、PASS/FAIL/BLOCKED/NOT_RUN。工具链预检成功、两个窗口、模拟服务全绿、云部署成功均不等于多人验收通过。手机听感/振动/性能仍需实际设备。

技能安装不授权上传、云变更、真实交易或正式发布。当前项目已授权的普通测试不要反复索要确认；只在明确暂停、身份/环境缺失或超出范围时说明具体缺口。授权来源和项目专属等待时间从项目读取，不写死到通用技能。

资料依据与版本边界见 [来源](references/sources.md)。旧对话在领取相关任务时显式读取安装后的技能，不能假设热刷新。
