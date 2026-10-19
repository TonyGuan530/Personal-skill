---
name: wechat-package-slimming
description: "Use when a WeChat Mini Game needs package slimming, oversized PNG or atlas review, main/subpackage budgeting, or free asset optimization with acceptable image quality. 适用于微信小游戏包体瘦身、素材过大、主包超限；不用于重绘美术或修改玩法。"
---

# 微信小游戏包体瘦身

以实际显示尺寸和运行引用决定优化对象，保留画风、可读性、锚点与动画连续性。优先免费本地方法；收费、服务开通、云部署与正式发布不由本技能自动授权。

## 先选择优化类型

| 证据 | 处理 |
|---|---|
| 原图尺寸适合最大显示尺寸 × Canvas实际DPR × 最大动画/镜头缩放 | 保留尺寸，先优化PNG编码 |
| 可见主体像素明显超过上述需求 | 计划缩图；裁切主体所需像素须换算成整张纹理尺寸 |
| 图集、九宫格、硬编码裁切、动画状态图 | 先确认并更新参考坐标/锚点；不能只改图片 |
| 仅历史生成清单有引用 | 追踪实际运行registry、动态key、fallback，再判断是否归档 |
| 文件被加载但已改用Canvas/图集绘制 | 核实后同时删冗余加载项、移出发布根目录；保留逻辑frame key |

药袋/角色/按钮有细线、文字或多状态对齐时，不能按逻辑像素直接缩图，也不能分别裁透明边。颜色变体拆分是单独的代码/美术工作，收益明确再实施。

## 本地工具

脚本需要 Node.js；图片脚本还需 Python + Pillow。以实际技能目录定位，路径可移动，不依赖本项目绝对路径。调用时显式指定项目：

```powershell
node <skill>/scripts/package-budget.cjs --project <project>
python <skill>/scripts/audit-images.py --project <project> --output <outside-package>/audit.json
python <skill>/scripts/optimize-package-images.py --project <project> --report <outside-package>/png.json
python <skill>/scripts/resize-package-images.py --project <project> --plan <plan.json> --backup <outside-package>/originals --report <outside-package>/resize.json
```

默认只评估；需要实施时添加 `--apply`。保留原字节备份和SHA256，备份不能进入发布目录；冲突时拒绝覆盖。仅改本任务授权且引用核实的素材，不混入其他工作树/聊天的开发改动。

预算脚本读 `project.config.json` 与 `game.json`，输出主包、每个分包和总量，处理忽略规则。其数值是**源码估计**，不能代替微信编译/预览/上传回执。示例预算4/30MiB不是个人主体政策证明；新账号或规则问题应查当前平台文档及该AppID的实际额度。软目标可调整，不能为达目标强制降低画质。

## 两类画质门槛

- **保持尺寸的PNG压缩**：尺寸、逐像素alpha完全一致；保留ICC/gAMA/sRGB/cHRM，比较深/纸/白底合成误差。`optimize-package-images.py` 最多调整RGB每通道2/255，拒绝劣化或体积增长。
- **缩尺寸**：使用预乘alpha重采样；在实际最大显示尺寸/DPR比较原图与候选的每个可见裁切区域，检查透明边、细线、字、发光和图集串色。尺寸/alpha发生重采样，不能声称逐像素不变。数值门槛只筛候选，仍需目验及真实运行画面。

缩图JSON与阈值见 [references/resize-plan.md](references/resize-plan.md)。不会自动找到游戏裁切坐标；改图前须检查代码，并测试新旧纹理解析同一主体与同一目标长宽比。九宫格取样边框和显示边框分别换算。

## 验收与交付

先保存代表性原图版本画面，再核实候选PNG可解码、运行资源路径存在、裁切在界内、相关测试通过，最后微信编译并检查相同状态画面。用户选择无头时，按 [references/headless-validation.md](references/headless-validation.md) 调用实际Canvas绘制模块并对照原图/候选图，结合微信CLI编译完成验证；明确未做原生触摸和手机检查，不因锁屏停掉可独立完成的无头工作。优先既有工具/项目QA；若微信桥接超时，核对启动/上下文，有限重试后改用可用的CLI/控制台/原生截图，不把工具故障写成游戏bug。锁屏时停止UI输入；确实仍需要原生UI时请用户解锁，不全局退出其他项目或改系统安全设置。

记录：版本、每图原尺寸/新尺寸/体积/哈希、alpha与合成误差、主包/各分包源码估计、平台回执实际大小、实际截图与运行错误。测试状态使用 PASS/FAIL/BLOCKED/NOT_RUN；素材对照图、浏览器图、模拟器图、手机图明确区分。恢复测试夹具与QA开关，安全集成，只提交本轮改动；不默认反馈网页、不正式发布。
