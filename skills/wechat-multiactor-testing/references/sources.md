# 来源与核验边界

2026-10-15核验。原创流程/脚本；没有复制第三方MCP实现或修改微信工具。

## 官方一手依据

- 本机官方发行包resources/app.asar.unpacked/package.json：RC 2.02.2609231。
- 随包wechatide-skill/SKILL.md及skills/automator/SKILL.md：0.3.11，明确区分小游戏Canvas与小程序WXML；小游戏支持automation_game_action、evaluate、截图、testaccount，不使用页面栈。
- 本机cli.bat auto --help：auto-port/auto-account；wechatide命令help：测试号动作和Canvas坐标参数；check_wechatide_status：CLI可选token、MCP独立token。
- 官方发行包app.asar内js/common/automator/out/Launcher.d.ts及MiniProgram.d.ts：account/port/projectPath、connect(wsEndpoint)、testAccounts等签名。只读核验，没有改写安装文件。类型存在不证明当前npm或多账号并行实测通过。
- 同一`app.asar`的实装代码（只读）：`js/69f7fe3bf8efa8f13e8b4aa32d756f84.js`菜单`openAutoTestWindow`包含`!isGameProject`；`js/87c5c70c5e933242a21d6b3c9de3c85e.js`的`Tool.getTestAccounts`只枚举`accountMap`；`js/de49eebdc8e597c86bf4307b7b5ebe9a.js`另定义内置`TestUserMap`。没有输出、上传其中的模拟ticket。
- `js/3f4b5a7224d7b710a48a9b753d705048.js`的`auto`先按目标项目路径执行`closeProjectWindow`，再打开lite项目窗口并在该路径启动端口；账号查`accountMap`或`TestUserMap`。`js/f0afd74c78c61722682f4039e8917151.js`的协议用唯一id关联WebSocket请求/响应；`js/87c5...`提供`Tool.getInfo`、`Tool.invokeGameMethod`、`Tool.captureSimulatorScreenshot`，小游戏方法由`js/257b1bb62992666dda5c22bd010ff68a.js`调用。只读分析安装包，不改发行文件。
- `js/3e3a290bbfd0ed98177212909bd0e0e0.js`明示小游戏`touchstart/touchend`映射`Driver.game.touchstart/touchend`，并校验有限坐标；`js/1f543778895179c15185b3a3abf97d9f.js`的SDK`screenshot()`使用`App.captureScreenshot`，与小游戏端口另有的`Tool.captureSimulatorScreenshot`不同。MentatBG的`docs/project-governance/qa/t-wx-multiactor-tooling/r2/manifest.json`列出准确ASAR路径、每文件SHA-256、标志字符串偏移与行号、安装包SHA-256，供版本回归。
- 官方文档入口：[命令行](https://developers.weixin.qq.com/miniprogram/dev/devtools/cli.html)、[自动化快速开始](https://developers.weixin.qq.com/miniprogram/dev/devtools/auto/quick-start.html)、[自动化FAQ](https://developers.weixin.qq.com/miniprogram/dev/devtools/auto/faq.html)、[调试功能](https://developers.weixin.qq.com/miniprogram/dev/devtools/debug.html)。本次网页抓取失败，不将网页未读内容当作已核条款；结论以安装包/实际帮助/只读接口为据。后续版本再查官方文档。

## 已实际验证与未验证

本次安装环境登录未过期、官方CLI可访问、skill版本equal、CLI不要求token、MCP要求独立token。用户报告已打开四个官方虚拟调试窗口；在同一项目上`automation_testaccount list`仍success且accounts=0。官方实现解释了为何该接口不会列出内置虚拟用户。`project_list`只列出一个已导入项目；按原项目路径的bridge可截图。

后续同一RC的隔离实验：源`C:/WechatGame/MentatBG`干净HEAD `d28496e93e0d237e0452d86ae1e755395994c7f8`；四份快照的393个`minigame/`文件具有同一内容摘要。`cli auto`按不同快照、内置虚拟用户和9431–9434端口启动，四端口均监听。官方端口协议对A/B/C返回SDKVersion 3.17.3、390×844画布及截图；D只返回版本，画布超时、截图黑屏。A本地`showToast`后截图变化，B截图SHA-256与前一张完全相同，证明A/B本地视角隔离。桥接按项目路径找不到这些CLI自动化快照窗口；SDK`App.captureScreenshot`在A/B超时，而`Tool.captureSimulatorScreenshot`成功。实验后四个自建窗口各自`Tool.close`，原共享项目仍可截图。没有获取ticket、调用云游戏动作或验证可信openid。

R2复用现有A/B快照和同一工具版本，实际通过`Tool.invokeGameMethod`的`touchstart/touchend`对小游戏本地头像库进行双向打开/返回：有事件请求ID、画布逻辑坐标、截图尺寸/哈希和游戏自身`avatarLibraryOpen`只读状态。A/B状态隔离已证。个别截图在打开头像库后返回超时，稍后可再取；脚本将输入接受与画面验证分开。通用端口脚本和Node行为测试在本技能`scripts/`，项目专属原始状态/截图/失败回执在上述R2目录。云端可信身份、多人房间和四角色同时运行仍未验。

当前可交付是可安装技能、只读探针、会话规划器、端口实验记录和矩阵。用户原有四窗口到四个自动化通道的映射、四个**同时可用**的CLI角色、虚拟账号云身份、真实两人游戏、手机验证尚未证实。此本机事实是版本记录，不是所有项目永远账号为空或必须人工完成QA。
