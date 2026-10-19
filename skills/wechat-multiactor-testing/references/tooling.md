# 官方工具接口与选择

本地核验基线：Windows微信开发者工具RC 2.02.2609231，内置wechatide-skill 0.3.11（2026-10-15）。版本会变化，实际--help及随包文档优先。官方CLI与wechatide CLI是两个入口，后者和MCP共用工具能力，不是第三方插件。

|能力|推荐通道|限制|
|---|---|---|
|启动自动化、指定账号/端口|cli.bat auto|本机help有--auto-port、--auto-account；本机实现先关闭**同一项目路径**的窗口。共享项目只能通过不同路径的隔离快照测试；启动返回不证明画布已加载|
|查测试号|wechatide automation_testaccount --action list|本机只读已添加账号的`accountMap`；内置虚拟用户来自另一`TestUserMap`，所以不是已开的多账号调试窗口数。动作仅list/getTicket/setTicket/refreshTicket|
|小游戏真实画布触摸|wechatide automation_game_action|tap/swipe/touchstart/touchmove/touchend；仅project寻址，无账号/窗口参数|
|端口绑定的小游戏画布/截图|本机官方Automator WebSocket协议|本机RC用`Tool.getInfo`、`Tool.invokeGameMethod`和`Tool.captureSimulatorScreenshot`验证A/B/C；这些是随包协议方法，版本升级先复核。内置bridge无法按路径找到CLI自动化快照窗口|
|截图和只读状态|simulator_screenshot / automation_evaluate|仅适用于bridge识别的项目窗口；证据须绑定同一角色，不依赖WXML/page stack|
|小程序页面自动化|miniprogram-automator或内置页面工具|官方随包类型有launch({account,port,projectPath})、connect({wsEndpoint})、testAccounts()；本机SDK的`App.captureScreenshot`对CLI启动的小游戏超时，不能照搬WXML截图方法|
|MCP|仅可调用且有额外价值时|本机MCP独立token必需；CLI token仅配置要求时必需，不为CLI工作去额外配置MCP|

### 已核端口脚本（Node 24）

[`scripts/automator_port.cjs`](../scripts/automator_port.cjs)仅连接调用者指定的`127.0.0.1:<auto-port>`，不会启动/关闭IDE、安装依赖或读取账号。命令须在已确认角色端口对应关系后执行，输出目录用每轮新目录（旧证据拒绝覆盖）：

```text
node scripts/automator_port.cjs --port 9431 --alias actor-a --output-dir C:/qa/run-a
node scripts/automator_port.cjs --port 9431 --alias actor-a-open --output-dir C:/qa/run-a --action touch --authorize-local-input --scope local-ui --image-x 75 --image-y 150 --after-ms 1000
```

默认`inspect`只取工具/基础库版本、`getCanvasSize`和PNG截图。`touch`先取当前截图，按`截图像素×逻辑画布/截图尺寸`换算，依次发送`touchstart`和`touchend`；必须明确目标别名/端口、坐标及`--authorize-local-input --scope local-ui`。脚本保留请求ID、输入顺序与前后截图哈希，但只输出脱敏JSON路径，不dump原始响应/base64/账号；单次RPC最长20秒，断开传输不关闭窗口。确认按钮不会触发云业务写之后才可用输入模式。截图失败则脚本停止输入，不能绕过当前画面确认。

本机同源快照A/B实测：390×844画布、149×321截图，截图坐标(75,150)换成逻辑(196,394)。先开本地头像库，A只读运行时`avatarLibraryOpen`由false变true、B仍false；后来A触摸“返回”变false时B仍true，B关闭后A仍false，B再次打开后A仍false。运行时状态来自游戏自身的只读调试对象；通用脚本不假设其它游戏也有同名字段。个别打开头像库后的截图调用超时，但后来两角色各自取到头像库/引导层画面；把该截图工具故障单列，不把输入驱动的`status=0`当成截图/交互通过。R2原始脱敏记录在本项目`docs/project-governance/qa/t-wx-multiactor-tooling/r2/`。

PowerShell示意（路径/账号来自已核实本机配置，不能照抄占位值运行）：

```powershell
& '<install>/cli.bat' auto --help
& '<install>/wechatide.cmd' -c <registered-client> check_wechatide_status --skill-version <loaded-version>
& '<install>/wechatide.cmd' -c <registered-client> automation_testaccount --project '<project>' --action list
& '<install>/cli.bat' auto --project '<actor-project>' --auto-port <free-port> --auto-account $env:WX_ACTOR_A
& '<install>/wechatide.cmd' -c <registered-client> simulator_screenshot --project '<actor-project>' --path '<new-output.jpg>'
& '<install>/wechatide.cmd' -c <registered-client> automation_game_action --project '<actor-project>' --action tap --x 120 --y 340
```

状态返回pending时查询原taskId，禁止反复提交；ticket、token、session_key、账号原ID不写GitHub/报告。现成登录可复用，不读取凭据缓存；CLI或MCP许可不等于游戏业务登录。

本机实测：将同一干净提交的`minigame/`和`project.config.json`复制到四个独立路径，各以不同内置虚拟用户/端口执行`cli auto`。A/B/C三个端口的`Tool.getInfo`、`Tool.invokeGameMethod(method=getCanvasSize)`和`Tool.captureSimulatorScreenshot`返回正常；A端口通过`Tool.invokeGameMethod(method=callWxMethod, data.method=showToast)`出现本地提示，B端口截图字节完全未变，证明至少两个端口具有独立本地UI状态。D端口可握手并返回版本，但`getCanvasSize`持续超时且截图黑屏；四角色并发仍为BLOCKED，原因未定。所有自建窗口已通过各自端口的`Tool.close`关闭，共享项目窗口随后仍能截图。该结果只适用于RC 2.02.2609231，不把内置虚拟用户等同于可信云身份。

端口协议请求采用`ws://127.0.0.1:<auto-port>`，JSON结构`{"id":"<unique>","method":"Tool.getInfo","params":{}}`；响应以相同id关联。画布尺寸用`Tool.invokeGameMethod`的`{"method":"getCanvasSize","data":{}}`；截图用`Tool.captureSimulatorScreenshot`返回的`data:image/png;base64,...`。非业务写隔离试验可在**明确绑定的角色端口**调用`Tool.invokeGameMethod`的`callWxMethod`→`showToast`，随后分别截图。`Tool.getInfo`只给工具/基础库版本，不给候选包Git提交；候选一致性须从隔离快照逐文件核验。不要将内部协议当作跨版本稳定的公开API；升级后先只读重验。未经授权或未确认角色绑定，不发触摸/写入。

不要默认复制整个IDE安装、修改app.asar、换全局端口/强退共享IDE。新装第三方多实例补丁不是前置条件。

四个虚拟调试窗口已打开而`automation_testaccount list`仍为0时，先记录接口差异。`--auto-account`会经本机代码查找`accountMap`或`TestUserMap`并给新窗口设置对应用户信息，但不会自动附着到用户已打开的原窗口，也不证明云服务端身份不同。没有可验证的每角色端口/窗口映射，不做A/B触摸试验，也不把主窗口截图复用为四份角色证据。

本包脚本在Windows直接以随官方.cmd相同的Electron Node引导调用官方CLI JS入口，参数数组shell=false，避免将项目路径/账号拼成shell代码；未修改IDE。若发行包改变入口，脚本报BLOCKED，重新检查官方包装器后更新，不猜内部路径。脚本不安装npm、不启自动化、不写项目配置。
