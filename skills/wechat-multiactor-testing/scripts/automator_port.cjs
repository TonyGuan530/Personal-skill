#!/usr/bin/env node
'use strict';

// Version-bound adapter for the Automator WebSocket bundled with WeChat DevTools.
// Default mode is read-only. It never opens/closes an IDE project or prints payloads.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const METHODS = Object.freeze({
  info: 'Tool.getInfo',
  game: 'Tool.invokeGameMethod',
  screenshot: 'Tool.captureSimulatorScreenshot',
});

function options(argv) {
  const o = {};
  const flags = new Set(['authorize-local-input']);
  const allowed = new Set(['port', 'alias', 'output-dir', 'action', 'image-x', 'image-y', 'after-ms', 'timeout-ms', 'scope']);
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (token === '--help') return { help: true };
    if (!token.startsWith('--')) throw Error('unknown positional argument');
    const key = token.slice(2);
    if (flags.has(key)) { o[key] = true; continue; }
    if (!allowed.has(key) || i + 1 >= argv.length) throw Error('unknown or incomplete option: ' + key);
    if (Object.hasOwn(o, key)) throw Error('duplicate option: ' + key);
    o[key] = argv[++i];
  }
  const port = Number(o.port);
  if (!Number.isInteger(port) || port < 1024 || port > 65535) throw Error('port must be 1024..65535');
  if (!/^[a-z][a-z0-9-]{0,39}$/.test(o.alias || '')) throw Error('alias must be a safe lowercase name');
  if (!o['output-dir'] || !path.isAbsolute(o['output-dir'])) throw Error('output-dir must be absolute');
  const action = o.action || 'inspect';
  if (!['inspect', 'touch'].includes(action)) throw Error('action must be inspect or touch');
  const timeoutMs = o['timeout-ms'] === undefined ? 12000 : Number(o['timeout-ms']);
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1000 || timeoutMs > 20000) throw Error('timeout-ms must be 1000..20000');
  const afterMs = o['after-ms'] === undefined ? 350 : Number(o['after-ms']);
  if (!Number.isInteger(afterMs) || afterMs < 0 || afterMs > 3000) throw Error('after-ms must be 0..3000');
  if (action === 'touch') {
    if (!o['authorize-local-input'] || o.scope !== 'local-ui') throw Error('touch requires --authorize-local-input --scope local-ui');
    if (![o['image-x'], o['image-y']].every(v => v !== undefined && Number.isFinite(Number(v)))) throw Error('touch requires finite image-x/image-y');
  } else if (o['authorize-local-input'] || o['image-x'] !== undefined || o['image-y'] !== undefined || o.scope) {
    throw Error('input flags require --action touch');
  }
  return { port, alias: o.alias, outputDir: path.resolve(o['output-dir']), action,
    timeoutMs, afterMs, imageX: Number(o['image-x']), imageY: Number(o['image-y']) };
}

function pngSize(data) {
  if (data.length < 24 || data.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a' || data.toString('ascii', 12, 16) !== 'IHDR') {
    throw Error('screenshot is not PNG');
  }
  const width = data.readUInt32BE(16), height = data.readUInt32BE(20);
  if (!width || !height || width > 10000 || height > 10000) throw Error('invalid PNG dimensions');
  return { width, height };
}

function mapPoint(imageX, imageY, image, canvas) {
  if (!Number.isFinite(imageX) || !Number.isFinite(imageY) || imageX < 0 || imageY < 0 || imageX >= image.width || imageY >= image.height) {
    throw Error('image point outside screenshot');
  }
  if (![canvas.width, canvas.height].every(v => Number.isFinite(v) && v > 0)) throw Error('invalid canvas dimensions');
  return { x: Math.round(imageX * canvas.width / image.width), y: Math.round(imageY * canvas.height / image.height) };
}

function safeName(error) {
  const msg = String(error && error.message || '');
  if (msg.startsWith('RPC_TIMEOUT')) return 'RPC_TIMEOUT';
  if (msg.startsWith('REMOTE_ERROR')) return 'REMOTE_ERROR';
  if (msg.startsWith('CONNECT_TIMEOUT')) return 'CONNECT_TIMEOUT';
  if (msg.startsWith('CONNECT_ERROR')) return 'CONNECT_ERROR';
  if (msg.startsWith('SOCKET_CLOSED')) return 'SOCKET_CLOSED';
  return 'INVALID_RESPONSE';
}

function connect(port, timeoutMs) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket('ws://127.0.0.1:' + port);
    const timer = setTimeout(() => { ws.close(); reject(Error('CONNECT_TIMEOUT')); }, timeoutMs);
    ws.addEventListener('open', () => { clearTimeout(timer); resolve(ws); }, { once: true });
    ws.addEventListener('error', () => { clearTimeout(timer); reject(Error('CONNECT_ERROR')); }, { once: true });
  });
}

function rpc(ws, method, params, timeoutMs) {
  const id = crypto.randomUUID();
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { ws.removeEventListener('message', onMessage); reject(Error('RPC_TIMEOUT')); }, timeoutMs);
    function onMessage(event) {
      let message;
      try { message = JSON.parse(event.data); } catch { return; }
      if (message.id !== id) return;
      clearTimeout(timer); ws.removeEventListener('message', onMessage);
      if (message.error) reject(Error('REMOTE_ERROR'));
      else resolve({ id, result: message.result });
    }
    ws.addEventListener('message', onMessage);
    try { ws.send(JSON.stringify({ id, method, params })); }
    catch { clearTimeout(timer); ws.removeEventListener('message', onMessage); reject(Error('SOCKET_CLOSED')); }
  });
}

async function attempt(summary, key, work) {
  try { summary.steps[key] = { ok: true, ...(await work()) }; return summary.steps[key]; }
  catch (error) { summary.steps[key] = { ok: false, error: safeName(error) }; return null; }
}

async function capture(ws, target, timeoutMs) {
  const reply = await rpc(ws, METHODS.screenshot, {}, timeoutMs);
  const uri = reply.result && reply.result.data;
  if (typeof uri !== 'string' || !uri.startsWith('data:image/png;base64,')) throw Error('invalid screenshot payload');
  const bytes = Buffer.from(uri.slice('data:image/png;base64,'.length), 'base64');
  const dimensions = pngSize(bytes);
  fs.writeFileSync(target, bytes, { flag: 'wx' });
  return { requestId: reply.id, file: target, bytes: bytes.length, sha256: crypto.createHash('sha256').update(bytes).digest('hex'), ...dimensions };
}

async function run(o) {
  fs.mkdirSync(o.outputDir, { recursive: true });
  const evidencePath = path.join(o.outputDir, o.alias + '-evidence.json');
  if (fs.existsSync(evidencePath)) throw Error('evidence file already exists; choose a new output directory');
  const summary = { schemaVersion: 1, alias: o.alias, port: o.port, action: o.action, startedAt: new Date().toISOString(),
    protocol: 'WeChat DevTools Automator (version-bound)', steps: {}, input: null, outcome: 'BLOCKED' };
  let ws;
  try {
    ws = await connect(o.port, o.timeoutMs);
    const info = await attempt(summary, 'info', async () => {
      const { id, result } = await rpc(ws, METHODS.info, {}, o.timeoutMs);
      return { requestId: id, toolVersion: String(result?.version || ''), SDKVersion: String(result?.SDKVersion || '') };
    });
    const canvasStep = await attempt(summary, 'canvas', async () => {
      const { id, result } = await rpc(ws, METHODS.game, { method: 'getCanvasSize', data: {} }, o.timeoutMs);
      if (result?.status !== 0 || !Number.isFinite(Number(result?.value?.width)) || !Number.isFinite(Number(result?.value?.height))) throw Error('invalid canvas');
      return { requestId: id, width: Number(result.value.width), height: Number(result.value.height) };
    });
    const baseline = await attempt(summary, 'baseline', () => capture(ws, path.join(o.outputDir, o.alias + '-baseline.png'), o.timeoutMs));
    if (o.action === 'inspect') summary.outcome = info && canvasStep && baseline ? 'PASS' : 'BLOCKED';
    if (o.action === 'touch' && info && canvasStep && baseline) {
      const point = mapPoint(o.imageX, o.imageY, baseline, canvasStep);
      summary.input = { sequence: ['touchstart', 'touchend'], scope: 'local-ui', imagePoint: { x: o.imageX, y: o.imageY },
        imageSize: { width: baseline.width, height: baseline.height }, canvasSize: { width: canvasStep.width, height: canvasStep.height }, canvasPoint: point };
      let allSent = true;
      for (const [index, method] of ['touchstart', 'touchend'].entries()) {
        const result = await attempt(summary, method, async () => {
          const { id, result } = await rpc(ws, METHODS.game, { method, data: point }, o.timeoutMs);
          if (result?.status !== 0) throw Error('game input failed');
          return { requestId: id, sequenceNumber: index + 1, gameStatus: result.status };
        });
        if (!result) { allSent = false; break; }
      }
      if (allSent) {
        await new Promise(resolve => setTimeout(resolve, o.afterMs));
        const after = await attempt(summary, 'after', () => capture(ws, path.join(o.outputDir, o.alias + '-after.png'), o.timeoutMs));
        summary.outcome = after ? 'INPUT_DELIVERED' : 'INPUT_DELIVERED_CAPTURE_BLOCKED';
      }
    }
  } catch (error) {
    summary.steps.connection = { ok: false, error: safeName(error) };
  } finally {
    if (ws) try { ws.close(); } catch { /* transport only; never close IDE */ }
    summary.finishedAt = new Date().toISOString();
    fs.writeFileSync(evidencePath, JSON.stringify(summary, null, 2) + '\n', { flag: 'wx' });
  }
  return summary;
}

if (require.main === module) {
  try {
    const o = options(process.argv.slice(2));
    if (o.help) {
      console.log('node automator_port.cjs --port 9431 --alias actor-a --output-dir C:/qa/run-a [--action inspect]');
      console.log('Input: --action touch --authorize-local-input --scope local-ui --image-x 75 --image-y 150 [--after-ms 350]');
    } else run(o).then(s => { console.log(JSON.stringify({ outcome: s.outcome, evidence: path.join(o.outputDir, o.alias + '-evidence.json') })); if (s.outcome === 'BLOCKED' || s.outcome === 'INPUT_DELIVERED_CAPTURE_BLOCKED') process.exitCode = 2; })
      .catch(() => { console.error('Probe failed before evidence could be written'); process.exitCode = 2; });
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}

module.exports = { options, pngSize, mapPoint, connect, rpc, run };
