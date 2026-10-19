# 生产素材的可复用合同

只在拆图/生成/接入时读取。本文件不规定固定数量、分辨率或某一种画风。

## 分批依据

| 类型 | 处理 | 验收关键 |
|---|---|---|
| 木桌、主棋盘、大背景、大立绘 | 逐件生成或复用已认可单图 | 中心可读留白，透视/比例符合现有风格，无动态地名数值 |
| 地点/牌面插画 | 相近用途与画幅成组，可用不透明图集 | 无动态文字；身份与数量来自规则，生成后逐格检查 |
| 棋子、货物、图标、纹饰 | 相近风格与透明要求成组，真实alpha | 不能漏件；小尺寸可辨；锚点和角色体量保留 |
| 控件底板/展示面板 | 按主动作、次要、数值展示等语义成组 | 无烘焙文字；边缘不拉扯；源/显示边框分开 |
| 文案、数值、骰点、选中/禁用状态、简单线条 | 代码动态绘制 | 不能掩盖主要插画缺失；控件与展示身份明确 |

“合适一起生产”由比例、渲染方式、透明要求与风格决定，不是把所有UI塞进一张图。同一风格参考贯穿批次；个别大图仍可以复用已认可原图，无需重新生成。

上表是默认拆分。项目明确认可的固定牌名/说明可烘焙，但要记录规则版本、语言与改字成本；价格、数量、状态等动态内容仍独立渲染，不能因例外把所有卡面信息做死。

## 清单示例

优先适配项目已有manifest/atlas schema。首次使用可建立一个 asset-plan.json：

```json
{
  "game": "new-game",
  "assets": [
    {"id":"table","role":"background","concept":"concept-01.png","decision":"generate","batch":"large-table","transparent":false,"displaySize":[390,844],"anchor":[0,0],"sourceFile":"sources/table.png","runtimeFile":"minigame/new-game/images/table.jpg","frame":null,"status":"verified"},
    {"id":"tea","role":"goods-icon","concept":"concept-01.png","decision":"generate","batch":"goods-icons","transparent":true,"displaySize":[28,28],"anchor":[0.5,0.5],"sourceFile":"sources/icons.png","runtimeFile":"minigame/new-game/images/icons.png","frame":[36,48,96,100],"status":"verified"},
    {"id":"score-text","role":"dynamic-value","decision":"code","reason":"计分随局面变化","status":"implemented"}
  ]
}
```

这些示例数值不是项目规范。frame只在最终运行图上取样；缩放、拼接、裁切后需重新计算。正在生产的项标planned/generating/review，不能先写verified。复用项记录真实source/runtime和依据，程序绘制项记录理由；当批不可用先列缺口，不重复生成整个已有图集。

## 生成与处理

提示词说明：已认可参考、视角、木/纸/墨等色板、用途、显示尺寸、大图留白或图集逻辑ID顺序、间隔、安全边、是否真实透明、无文字数值。各生图工具按其实际接口设置透明背景与参考图；不把PNG后缀当alpha证据。

保存原图，另输出运行压缩图和处理脚本。生成网格的不等距空隙、错位、重复、缺件、拼字都需逐件核验；出现不合格格子时只修相关组件或批次。主要画面与控件不能直接以整张概念图入包替代动态场景。

必要检查：

- 文件能真实解码；HTML错误页即使叫.jpg也不是图片。
- 每个逻辑ID有唯一runtime去向，frame在最终图片边界内；透明边/阴影不侵入相邻格。
- 透明对象在实际深色底上无白角；需硬边的素材按项目规则处理。背景不强行透明。
- 同一角色的体量、可见轮廓、foot anchor与玩法一致；不把全部角色轮廓各自拉满同一框。
- 九宫格只延展适当中段，超宽窄条按现有规范使用代码或合适的专用材质。
- 用真实游戏中的显示尺寸查看识别与字距；素材contact sheet只是开发检查。
- 压缩前后解码/颜色/alpha/坐标复查，预算统计整个运行分包，避免概念/源图误入运行包。
