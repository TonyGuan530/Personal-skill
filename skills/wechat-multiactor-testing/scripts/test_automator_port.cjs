'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { options, pngSize, mapPoint } = require('./automator_port.cjs');

const base = ['--port', '9431', '--alias', 'actor-a', '--output-dir', 'C:/qa/actor-a'];

test('read-only is the default and input requires explicit local UI scope', () => {
  assert.equal(options(base).action, 'inspect');
  assert.throws(() => options([...base, '--action', 'touch', '--image-x', '75', '--image-y', '150']), /authorize-local-input/);
  assert.throws(() => options([...base, '--action', 'touch', '--authorize-local-input', '--scope', 'cloud', '--image-x', '75', '--image-y', '150']), /local-ui/);
  assert.equal(options([...base, '--action', 'touch', '--authorize-local-input', '--scope', 'local-ui', '--image-x', '75', '--image-y', '150']).action, 'touch');
});

test('screenshot point maps from actual PNG to reported canvas without DPR multiplication', () => {
  const png = Buffer.alloc(24); Buffer.from('89504e470d0a1a0a', 'hex').copy(png); png.write('IHDR', 12); png.writeUInt32BE(149, 16); png.writeUInt32BE(321, 20);
  const image = pngSize(png);
  assert.deepEqual(image, { width: 149, height: 321 });
  assert.deepEqual(mapPoint(75, 150, image, { width: 390, height: 844 }), { x: 196, y: 394 });
  assert.throws(() => mapPoint(149, 150, image, { width: 390, height: 844 }), /outside screenshot/);
  assert.throws(() => pngSize(Buffer.alloc(24)), /not PNG/);
});
