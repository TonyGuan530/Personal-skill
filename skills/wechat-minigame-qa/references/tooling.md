# 工具与 SDK 适配

## 微信桥

读本机 wechatide-skill 的版本与 automator/debugger 文档，查工具 --help。2026-10-12 本机 v0.3.11 支持小游戏画布触摸、求值和截图；旧 automator 超时经验不能推广为所有版本不支持小游戏。

```powershell
& '<install>/wechatide.cmd' -c <client> check_wechatide_status --skill-version <version>
& '<install>/wechatide.cmd' -c <client> open_project_window --project '<absolute-project>'
& '<install>/wechatide.cmd' -c <client> simulator_screenshot --project '<absolute-project>' --path '<shot.jpg>'
& '<install>/wechatide.cmd' -c <client> automation_game_action --project '<absolute-project>' --action tap --x 120 --y 340
& '<install>/wechatide.cmd' -c <client> automation_evaluate --project '<absolute-project>' --fn-source 'function(){return wx.getSystemInfoSync()}'
```

从截图定位时用 coordinateSpace=image 并传该图真实 imageWidth/imageHeight；工具自动换算，勿二次缩放。画布空间用逻辑尺寸，不用 DPR 后物理像素。截图文件生成/API success 不证明内容或被测版本正确。

只打开本任务项目。simulator_refresh 成功不是编译通过；CLI auto 成功不代替实际画面或应用初始化。RPC 失败后保存日志，换可用通道，不无期限重试。RPC 成功但游戏对象 undefined 时先核对上下文：本机桥的真实游戏对象可能在 GameGlobal.__gameContextWindow 内，不能只查外层 GameGlobal。截图黑屏仍需独立诊断。IDE 主进程日志一般在 %LOCALAPPDATA%/微信开发者工具/User Data/<hash>/WeappLog/logs，并非完整游戏 console。

## Airtest / Poco SDK

[网易微信测试专题](https://airtest.doc.io.netease.com/en/tutorial/8_test_of_minigame/)：小游戏可用 Airtest 图像识别；Egret Poco 示例要求 SDK。该文版本示例较旧，当前兼容性需要实测。[Poco 官方实现指南](https://poco.readthedocs.io/en/latest/source/doc/implementation_guide.html)和 [SDK 仓库](https://github.com/AirtestProject/Poco-SDK)给出 JS 等接口。

自制 Canvas 适配：从真实 hitbox 导出稳定 name、enabled/visible、text、位置/尺寸，实现 Dump 树；Click/Swipe/LongClick 走真实触摸，不能直接 dispatch 引擎。Poco 坐标为归一化比例，转换至逻辑画布。微信需客户端 websocket/RPC，不能照搬应用内绑定 TCP 服务例子；本机成功不代表真机域名/通讯成功。

接入开发/QA 环境门禁，正式包不启动测试服务、不暴露秘密状态；验证安装/清理与诊断开销。若 SDK 与宿主不兼容，可选微信桥 + 项目 hitbox/调试接口作为 QA 适配器，明确不能声称 Poco 已安装通过。

## 状态机与监督器

沿用已有 node:test 与确定性矩阵；需要随机轨迹与缩减反例时参考 [fast-check 模型测试](https://fast-check.dev/docs/advanced/model-based-testing/)、[竞态](https://fast-check.dev/docs/advanced/race-conditions/)、[超时](https://fast-check.dev/docs/configuration/timeouts/)。同步死循环仍需外部监督。

run-bounded.cjs 直接调用 executable、shell=false，适合 node/python。Windows .cmd/.bat 应用专门受控包装或直接可执行入口，不拼接不可信 shell 参数。超时 timedOut=true，退出码 124；错误非零。只终止直属 worker，不退出共享 IDE；worker 不应启动脱管孙进程。
