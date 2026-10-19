const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
async function run(executable, args, timeoutMs, cwd = process.cwd()) {
  if (!Number.isSafeInteger(timeoutMs) || timeoutMs <= 0) throw new Error('timeoutMs must be a positive integer');
  if (/\.(cmd|bat)$/i.test(executable)) throw new Error('Use a direct executable, not a shell batch wrapper');
  const began = Date.now();
  return new Promise(resolve => {
    let stdout = '', stderr = '', timedOut = false, error = null;
    const child = spawn(executable, args, { cwd, shell: false, windowsHide: true });
    const append = (old, chunk) => (old + chunk.toString()).slice(-512000);
    child.stdout.on('data', chunk => { stdout = append(stdout, chunk); });
    child.stderr.on('data', chunk => { stderr = append(stderr, chunk); });
    child.on('error', e => { error = e.message; });
    const timer = setTimeout(() => { timedOut = true; child.kill(); }, timeoutMs);
    child.on('close', (code, signal) => {
      clearTimeout(timer);
      resolve({ executable, args, cwd, timeoutMs, elapsedMs: Date.now() - began,
        timedOut, code, signal, error, stdout, stderr, ok: !timedOut && !error && code === 0 });
    });
  });
}
module.exports = { run };
if (require.main === module) {
  const [ms, reportPath, executable, ...args] = process.argv.slice(2);
  if (!reportPath || !executable) { console.error('timeoutMs report.json executable [...args]'); process.exit(2); }
  run(executable, args, Number(ms)).then(result => {
    fs.mkdirSync(path.dirname(path.resolve(reportPath)), { recursive: true });
    fs.writeFileSync(reportPath, JSON.stringify(result, null, 2));
    console.log(JSON.stringify({ ok: result.ok, timedOut: result.timedOut, code: result.code, elapsedMs: result.elapsedMs, reportPath }));
    process.exitCode = result.timedOut ? 124 : result.ok ? 0 : result.error ? 1 : result.code > 0 && result.code < 256 ? result.code : 1;
  }).catch(e => { console.error(e.message); process.exitCode = 2; });
}
