// 椒图AI 无头出图客户端（最终版）——固定分辨率 1280×1080 DPR=1，Edge 无头
//
// 命令：
//   node jiaotu-headless.cjs login-check
//   node jiaotu-headless.cjs gen --prompt <文件|"文字"> [--image <png>] [--ratio 9:16]
//                               [--res 1K] [--out out.png] [--wait 300000] [--attempts 3]
//
// 硬规则：
//   * 默认模型=最新图片V2 Pro（localStorage model 键在每次导航注入时强制覆盖）
//   * 单次 ≤6 花椒粒：仅允许 1K 档，2K/4K/高质 直接拒绝
//   * 图生图：提示词先进输入框，图片用合成 paste 事件附上，
//     等"附件缩略图变成 cdn 域名"（服务器上传完成）再点发送
//   * 结果收割：只认当天 09/28 的新 CDN 图（差集+已知旧图排除）
//   * 下载必须页面内 fetch（curl 直连 cdn 会 SSL 失败）
const fs = require('fs');
const path = require('path');
const { chromium } = require(path.join(__dirname, '..', 'node_modules', 'playwright-core'));

const AUTH = path.join(__dirname, '..', 'auth', 'jiaotu-auth.json');
const EDGE = [
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
].find(p => fs.existsSync(p));

function parseArgs(argv) {
  const o = { ratio: null, res: '1K', quality: null, image: null, out: 'jiaotu-out.png', wait: 300000, attempts: 3, cmd: null, promptText: null, promptFile: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === 'login-check') o.cmd = 'login-check';
    else if (a === 'gen') o.cmd = 'gen';
    else if (a === '--prompt') o.promptFile = argv[++i];
    else if (a === '--image') o.image = argv[++i];
    else if (a === '--ratio') o.ratio = argv[++i];
    else if (a === '--res') o.res = argv[++i];
    else if (a === '--quality') o.quality = argv[++i];
    else if (a === '--out') o.out = argv[++i];
    else if (a === '--wait') o.wait = +argv[++i];
    else if (a === '--attempts') o.attempts = +argv[++i];
    else if (!o.promptText && !a.startsWith('--')) o.promptText = a;
  }
  return o;
}

(async () => {
  const args = parseArgs(process.argv.slice(2));
  if (!EDGE) throw new Error('未找到 Edge/Chrome');
  if (args.cmd === 'gen' && ((args.res && args.res !== '1K') || (args.quality && args.quality === '高质'))) {
    throw new Error('skill 限制：单次 ≤6 积分，仅允许 1K 档（2K/4K/高质 需用户明确批准后临时放开）');
  }
  const auth = JSON.parse(fs.readFileSync(AUTH, 'utf8'));
  const browser = await chromium.launch({ executablePath: EDGE, headless: true, args: ['--window-size=1280,1080', '--force-device-scale-factor=1'] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 1080 }, deviceScaleFactor: 1 });
  await ctx.grantPermissions(['clipboard-read', 'clipboard-write']);
  const pre = await ctx.newPage();
  await ctx.addInitScript((ls) => { for (const [k, v] of Object.entries(ls)) { try { localStorage.setItem(k, v); } catch (e) {} } }, auth.localStorage);
  await pre.goto('https://jiaotu.ai/', { waitUntil: 'domcontentloaded' });
  await pre.waitForTimeout(2500);
  const v2pro = await pre.evaluate(async () => {
    const r = await fetch('https://api.jiaotuai.cn/api/v1/ai/queryModels');
    const j = await r.json();
    return (j.data || []).find(x => x.showModelName === '最新图片V2 Pro') || null;
  });
  if (!v2pro) throw new Error('V2 Pro not found');
  const lsForce = { ...auth.localStorage, __v2pro: v2pro };
  await pre.close();
  // 每次导航注入时强制 model=V2 Pro（验证过的可靠方法）
  const page = await ctx.newPage();
  await ctx.addInitScript((ls) => {
    for (const [k, v] of Object.entries(ls)) { try { localStorage.setItem(k, v); } catch (e) {} }
    try { localStorage.setItem('model', JSON.stringify({ data: ls.__v2pro })); } catch (e) {}
  }, lsForce);
  page.setDefaultTimeout(20000);

  // —— 登录（重注 + reload 最多 3 次）——
  await page.goto('https://jiaotu.ai/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2500);
  let loggedIn = await page.evaluate(() => /限时特惠/.test(document.body.innerText));
  for (let i = 0; i < 3 && !loggedIn; i++) {
    await page.evaluate((ls) => { for (const [k, v] of Object.entries(ls)) { try { localStorage.setItem(k, v); } catch (e) {} } }, auth.localStorage);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3500);
    loggedIn = await page.evaluate(() => /限时特惠/.test(document.body.innerText));
  }
  if (!loggedIn) {
    await page.screenshot({ path: path.join(__dirname, 'debug-not-login.png') });
    throw new Error('未登录：请打开 jiaotu.ai 扫码后更新 auth/jiaotu-auth.json');
  }
  if (args.cmd === 'login-check') {
    const balance = await page.evaluate(() => (document.body.innerText.match(/(\d{3,5})\s*\n?\s*限时特惠/) || [])[1] || '?');
    console.log(JSON.stringify({ ok: true, balance }));
    await browser.close();
    return;
  }
  if (args.cmd !== 'gen') throw new Error('未知命令');

  const PROMPT = args.promptFile ? fs.readFileSync(args.promptFile, 'utf8').trim() : (args.promptText || '').trim();
  if (!PROMPT) throw new Error('提示词为空');

  // —— 工具函数 ——
  const clickText = async (text) => {
    const r = await page.evaluate((t) => {
      for (const el of document.querySelectorAll('*')) {
        if ((el.textContent || '').trim() === t) {
          const r = el.getBoundingClientRect();
          if (r.width > 20 && r.y > 100 && r.y < 1000) return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
        }
      }
      return null;
    }, text);
    if (r) { await page.mouse.click(r.x, r.y); await page.waitForTimeout(500); }
    return !!r;
  };
  const modelLabel = () => page.evaluate(() => {
    for (const b of document.querySelectorAll('button, [role=button]')) {
      const s = (b.textContent || '').replace(/\s+/g, '');
      if (/^(全能图片V2|最新图片V2Pro|最新图片V2|最新2\.5SunburstPro|最新2\.5FlarePro|Seedream5\.0Pro|Seedream5\.0lite|全能图片Pro)$/.test(s)) {
        const r = b.getBoundingClientRect();
        if (r.width > 60 && r.y > 200 && r.y < 1080) return s;
      }
    }
    return '?';
  });

  // —— 主尝试循环 ——
  for (let attempt = 1; attempt <= args.attempts; attempt++) {
    try {
      console.error(`[attempt ${attempt}/${args.attempts}]`);
      await page.goto('https://jiaotu.ai/', { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(3000);

      // 快速模式
      await clickText('快速');

      // 模型：init 注入已强制 V2 Pro，这里只校验
      console.error('[model]', await modelLabel());
      if ((await modelLabel()) !== '最新图片V2Pro') console.error('[warn] 模型标签非 V2 Pro，继续（init 注入应已生效）');
      // 可选尺寸（默认不切：智能 1K 基础 = 5 积分）
      if (args.ratio) {
        if (await clickText(args.ratio)) {
          if (args.quality) await clickText(args.quality);
          await page.keyboard.press('Escape');
          await page.mouse.click(640, 250);
          await page.waitForTimeout(400);
        }
      }

      const before = await page.evaluate(() => Array.from(document.images).map(i => i.src.split('?')[0]));

      // 填提示词（主 composer 的 placeholder 前缀稳定）
      const ta = page.locator('textarea[placeholder^="试试输入"]').first();
      await ta.fill(PROMPT);
      await page.waitForTimeout(400);

      // 图生图：即测即点 filechooser 上传（验证过）+ 盲等 8s 服务器上传
      // 文生图必须整体跳过：否则会点到附件钮、setFiles(null) 直接炸 null.buffer
      if (args.image) {
      let uploaded = false;
      for (let round = 0; round < 3 && !uploaded; round++) {
        const pos = await page.evaluate(() => {
          const t = document.querySelector('textarea[placeholder^="试试输入"]');
          if (!t) return null;
          const tr = t.getBoundingClientRect();
          let host = t.parentElement;
          for (let i = 0; i < 4 && host; i++) {
            for (const el of host.querySelectorAll('div, button, label, img')) {
              const r = el.getBoundingClientRect();
              if (r.width >= 40 && r.width <= 90 && r.height >= 40 && r.height <= 90 && r.right <= tr.left + 10 && r.top > tr.top - 120 && r.bottom < tr.bottom + 120) {
                return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
              }
            }
            host = host.parentElement;
          }
          return null;
        });
        if (!pos) { await page.waitForTimeout(800); continue; }
        const chooserP = page.waitForEvent('filechooser', { timeout: 5000 }).catch(() => null);
        await page.mouse.click(pos.x, pos.y);
        const chooser = await chooserP;
        if (chooser) {
          await chooser.setFiles(args.image);
          uploaded = true;
          console.error('[upload] filechooser ok', Math.round(pos.x), Math.round(pos.y));
          break;
        }
      }
      if (!uploaded) throw new Error('上传失败（filechooser 未触发）');
      await page.waitForTimeout(8000);
      }
      // 发送（最下圆钮 ×3 + Enter 兜底）
      for (let k = 0; k < 3; k++) {
        const send = await page.evaluate(() => {
          let best = null;
          for (const b of document.querySelectorAll('button, [role=button]')) {
            const r = b.getBoundingClientRect();
            if (r.width >= 34 && r.width <= 64 && r.height >= 34 && r.height <= 64 && r.x > 900 && r.y > 400) {
              if (!best || r.y > best.y) best = { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
            }
          }
          return best;
        });
        if (send) await page.mouse.click(send.x, send.y);
        await page.waitForTimeout(2000);
        const cleared = await page.evaluate(() => {
          const tas = Array.from(document.querySelectorAll('textarea')).filter(t => t.getBoundingClientRect().width > 50);
          return tas.length > 0 && tas.every(t => !((t.value || '').trim()));
        });
        if (cleared) break;
        if (k === 2) { await page.locator('textarea[placeholder^="试试输入"]').first().click(); await page.keyboard.press('Enter'); await page.waitForTimeout(2000); }
      }
      const submitted = await page.evaluate(() => {
        const tas = Array.from(document.querySelectorAll('textarea')).filter(t => t.getBoundingClientRect().width > 50);
        return tas.length > 0 && tas.every(t => !((t.value || '').trim()));
      });
      console.error('[submit] cleared =', submitted);
      if (!submitted) throw new Error('提交未生效');

      // —— 轮询结果（只认当日新图）——
      const beforeSnap = await page.evaluate(() => Array.from(document.images).map(i => i.src.split('?')[0]));
      const t0 = Date.now();
      let resultUrl = null;
      while (Date.now() - t0 < args.wait) {
        await page.waitForTimeout(7000);
        const found = await page.evaluate(({ b4 }) => {
          const _d = new Date();
          const _day = `${_d.getFullYear()}\/${String(_d.getMonth() + 1).padStart(2, '0')}\/${String(_d.getDate()).padStart(2, '0')}`;
          const today = new RegExp(`cdn\.jiaotuai\.cn\/[^/]+\/${_day}\/`);
          const known = /46b7c090|d9711ab6|c6fd2f8e|0054f818/;
          const urls = [];
          for (const i of document.images) {
            const s = i.src.split('?')[0];
            if (today.test(s) && !known.test(s) && i.getBoundingClientRect().width > 150 && !b4.includes(s)) urls.push(s);
          }
          return urls;
        }, { b4: beforeSnap });
        if (found.length) { resultUrl = found[found.length - 1]; break; }
        process.stdout.write('.');
      }
      if (!resultUrl) throw new Error('等待结果超时');
      console.log('\n[result]', resultUrl);
      const buf = await page.evaluate(async (u) => new Uint8Array(await (await fetch(u, { cache: 'force-cache' })).arrayBuffer()), resultUrl);
      fs.writeFileSync(args.out, Buffer.from(buf));
      console.log(JSON.stringify({ ok: true, out: path.resolve(args.out), bytes: buf.length, url: resultUrl }));
      await browser.close();
      return;
    } catch (e) {
      console.error(`[attempt ${attempt} failed]`, e.message);
      await page.screenshot({ path: path.join(__dirname, `debug-attempt-${attempt}.png`) }).catch(() => {});
      await page.waitForTimeout(1500);
    }
  }
  throw new Error(`全部 ${args.attempts} 次尝试失败（详见 scripts/debug-attempt-*.png）`);
})().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
