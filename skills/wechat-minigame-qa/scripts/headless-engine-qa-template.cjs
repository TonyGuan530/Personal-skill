// 无头规则引擎 QA 模板（微信小游戏通用）
// 用法：适配下方 [ADAPT] 标记的四处后，node headless-engine-qa-template.cjs [局数]
// 思路：游戏规则引擎是纯 JS 模块（无 wx/canvas 依赖），在 node 里直接驱动完整流程，
//       用不变量校验 + 双看门狗找逻辑 bug；时间快进让"等待窗口"秒级流逝。
//
// 实战原型见 MentatBG 仓库 tools/qa-jiuzhou-fullgame.cjs（九州商局 3 局 QA）。

const fs = require('fs');
const path = require('path');

// [ADAPT 1/4] 引擎模块路径：找到项目里"纯逻辑"的规则引擎（无 wx 引用的 .js）
const engine = require(process.env.QA_ENGINE_PATH || path.join(__dirname, 'ENGINE_PLACEHOLDER'));

// [ADAPT 2/4] 开一局/一个流程：传项目的开局参数（人数/难度/模式等）
function startSession() {
  return engine.createGame({ mode: 'ai', countdownMode: 'normal' }); // ← 换成项目的创建函数
}

// [ADAPT 3/4] 客户端动作驱动：模拟真实客户端会话层会发的动作序列。
// 原则：对被拒动作静默继续（客户端就是如此）；AI 到点的动作靠 tick 心跳驱动。
function pickAction(state) {
  const roll = Math.random();
  if (roll < 0.5) return { type: 'TICK' };                    // 心跳：推进 AI/计时
  return { type: 'PRIMARY_ACTION', playerId: state.localPlayerId }; // ← 换成项目的主行动
}

// [ADAPT 4/4] 时间快进 + 不变量校验：
// - 快进：把引擎里所有 Date.now() 比较的时间戳拨到已过期（等价"时间流逝"）
// - 不变量：终局到达、进度完整、资源守恒（注意保留牌之类的既有设计）、货币非负、榜序正确
function fastForward(state) {
  const t = state.timers || {};
  Object.keys(t).forEach((k) => { if (t[k] > Date.now()) t[k] = Date.now() - 1; });
}

function validate(state) {
  const problems = [];
  if (state.phase !== 'GAME_END') problems.push(`未到达终局（${state.phase}）`);
  state.players.forEach((p) => {
    if (!Number.isInteger(p.money) || p.money < 0) problems.push(`${p.name} 资源非法：${p.money}`);
  });
  return problems;
}

// —— 跑批骨架（一般无需改动）——
const MAX_SUBMITS = 30000;
const WATCHDOG_MS = 2000;   // 单次引擎调用上限：超过即死循环嫌疑
const STALL_LIMIT = 5000;   // 同一状态快照连续 N 次提交无变化：卡死嫌疑

function snapshot(state) {
  return JSON.stringify({ phase: state.phase, turn: state.turn, version: state.version });
}

function runSession(index) {
  const state = startSession();
  let submits = 0;
  let lastKey = '';
  let stall = 0;

  while (state.phase !== 'GAME_END') {
    submits += 1;
    if (submits > MAX_SUBMITS) {
      return { ok: false, problems: [`超过 ${MAX_SUBMITS} 次提交未终局（卡在 ${snapshot(state)}）`], state };
    }
    fastForward(state);
    const key = snapshot(state);
    stall = key === lastKey ? stall + 1 : 0;
    lastKey = key;
    if (stall >= STALL_LIMIT) {
      return { ok: false, problems: [`连续 ${stall} 次提交无进展（卡死 @ ${key}）`], state };
    }

    const action = pickAction(state);
    const t0 = Date.now();
    try {
      engine.submitAction(state, action); // ← 换成项目的动作入口
    } catch (error) {
      // 被拒动作（如超时出价）静默继续，与真实客户端一致
    }
    if (Date.now() - t0 > WATCHDOG_MS) {
      return { ok: false, problems: [`单次 ${action.type} 耗时 ${Date.now() - t0}ms（同步死循环嫌疑）`], state };
    }
  }
  const problems = validate(state);
  return { ok: problems.length === 0, problems, stats: { submits }, state };
}

const count = Number(process.argv[2]) || 3;
let failures = 0;
const lines = [`# 无头引擎 QA 报告`, `- 时间：${new Date().toLocaleString('zh-CN')}`, `- 局数：${count}`, ``];
for (let i = 0; i < count; i += 1) {
  const result = runSession(i);
  if (result.ok) {
    lines.push(`## 第 ${i + 1} 局 —— ✅ PASS`, `- ${result.stats.submits} 次提交`, ``);
    console.log(`✔ [${i + 1}] PASS · ${result.stats.submits} 次提交`);
  } else {
    failures += 1;
    lines.push(`## 第 ${i + 1} 局 —— ❌ FAIL`, '', ...result.problems.map((p) => `- ${p}`), '');
    console.log(`✖ [${i + 1}] FAIL: ${result.problems.join('；')}`);
    fs.writeFileSync(path.join(__dirname, `qa-dump-${i}.json`), JSON.stringify(result.state, null, 2));
  }
}
lines.push(failures === 0 ? '**结论：全部通过**' : `**结论：${failures} 局失败，现场见 qa-dump-*.json**`);
const report = path.join(process.cwd(), 'qa-report.md');
fs.writeFileSync(report, lines.join('\n'));
console.log(`\n报告：${report}`);
process.exit(failures === 0 ? 0 : 1);
