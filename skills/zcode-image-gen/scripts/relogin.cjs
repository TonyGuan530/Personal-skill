// 重新扫码登录：弹可见窗口 → 用户扫码 → 捕获新票据存档 → 校验余额
const fs = require('fs');
const path = require('path');
const { chromium } = require(path.join(__dirname, '..', 'node_modules', 'playwright-core'));

(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: false, args: ['--window-size=1280,1080', '--force-device-scale-factor=1'] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 1080 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  await page.goto('https://jiaotu.ai/', { waitUntil: 'domcontentloaded' });
  await page.bringToFront();
  // 尝试点登录按钮（弹出二维码）
  await page.waitForTimeout(2500);
  try {
    const r = await page.evaluate(() => {
      for (const b of document.querySelectorAll('button, [role=button], div, span')) {
        if ((b.textContent || '').trim() === '登录') {
          const r = b.getBoundingClientRect();
          if (r.width > 5 && r.y > 0) return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
        }
      }
      return null;
    });
    if (r) await page.mouse.click(r.x, r.y);
  } catch (e) {}
  console.log('窗口已置顶：请微信扫码登录（最长等 10 分钟）…');
  // 轮询登录态：出现积分数字
  const t0 = Date.now();
  let ok = false;
  while (Date.now() - t0 < 600000) {
    await page.waitForTimeout(3000);
    if (page.isClosed()) { console.error('窗口被手动关闭'); process.exit(1); }
    ok = await page.evaluate(() => /\d{3,5}\s*\n?\s*限时特惠/.test(document.body.innerText));
    if (ok) break;
  }
  if (!ok) { console.error('登录超时'); await browser.close(); process.exit(1); }
  const balance = await page.evaluate(() => (document.body.innerText.match(/(\d{3,5})\s*\n?\s*限时特惠/) || [])[1] || '?');
  // 存档票据
  const ls = await page.evaluate(() => JSON.stringify({ url: location.origin, at: new Date().toISOString(), localStorage: Object.fromEntries(Object.entries({ ...localStorage })), cookie: document.cookie }));
  fs.writeFileSync(path.join(__dirname, '..', 'auth', 'jiaotu-auth.json'), ls);
  console.log(JSON.stringify({ ok: true, balance, saved: true }));
  await page.waitForTimeout(1000);
  await browser.close();
})().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
