// Source-file estimate; WeChat build/upload receipts remain authoritative.
const fs = require('node:fs');
const path = require('node:path');
const DEFAULT_BUDGET = require('../config/package-budget.json');
const posix = value => value.replace(/\\/g, '/').replace(/^\/+|\/+$/g, '');

function canonicalOutput(value) {
  let existing = path.resolve(value);
  const missing = [];
  while (!fs.existsSync(existing)) {
    const parent = path.dirname(existing);
    if (parent === existing) throw new Error('Invalid report output root');
    missing.unshift(path.basename(existing));
    existing = parent;
  }
  return path.join(fs.realpathSync(existing), ...missing);
}

function checkedRelative(value, label) {
  if (typeof value !== 'string' || !value || path.isAbsolute(value)
    || value.replace(/\\/g, '/').split('/').some(part => part === '..' || part === '.')) {
    throw new Error(`Invalid ${label} path: ${value}`);
  }
  return posix(value);
}

function measureProject(projectRoot, budget = DEFAULT_BUDGET) {
  for (const key of ['mainLimitBytes', 'totalLimitBytes', 'mainTargetBytes', 'totalTargetBytes', 'plannedGames', 'existingGames']) {
    if (!Number.isSafeInteger(budget[key]) || budget[key] < (key.endsWith('Games') ? 0 : 1)) {
      throw new Error(`Invalid package budget: ${key}`);
    }
  }
  if (budget.mainTargetBytes > budget.mainLimitBytes || budget.totalTargetBytes > budget.totalLimitBytes
    || budget.plannedGames < budget.existingGames) throw new Error('Invalid package budget targets');
  const root = path.resolve(projectRoot);
  const project = JSON.parse(fs.readFileSync(path.join(root, 'project.config.json'), 'utf8'));
  const sourceRoot = path.join(root, checkedRelative(project.miniprogramRoot || 'minigame', 'source'));
  const game = JSON.parse(fs.readFileSync(path.join(sourceRoot, 'game.json'), 'utf8'));
  const subpackages = (game.subpackages || []).map(item => ({
    root: checkedRelative(item.root, 'subpackage'), name: item.name || item.root, bytes: 0, fileCount: 0,
  }));
  if (subpackages.some(item => typeof item.name !== 'string' || !item.name || item.name === 'main')) {
    throw new Error('Invalid or reserved subpackage name');
  }
  for (let i = 0; i < subpackages.length; i++) {
    for (let j = 0; j < i; j++) {
      const a = subpackages[i], b = subpackages[j];
      if (a.root === b.root || a.root.startsWith(b.root + '/') || b.root.startsWith(a.root + '/') || a.name === b.name) {
        throw new Error(`Overlapping or duplicate subpackage: ${a.root}`);
      }
    }
  }
  const main = { name: 'main', root: '', bytes: 0, fileCount: 0 };
  const packages = [main, ...subpackages];
  const files = [];
  const rules = project.packOptions?.ignore || [];
  function ignored(relative) {
    return relative.split('/').some(part => part === 'node_modules' || part.startsWith('.'))
      || rules.some(rule => {
        const value = posix(rule.value || '');
        if (!value) return false;
        if (rule.type === 'suffix') return relative.endsWith(value);
        if (rule.type === 'file') return relative === value;
        if (rule.type === 'folder') return relative === value || relative.startsWith(value + '/');
        if (rule.type === 'prefix') return relative.startsWith(value);
        if (rule.type === 'regexp') return new RegExp(rule.value).test(relative);
        throw new Error(`Unsupported pack exclusion: ${rule.type}`);
      });
  }
  if ((project.packOptions?.include || []).length) throw new Error('Explicit pack includes require platform build sizing');
  function walk(folder) {
    for (const entry of fs.readdirSync(folder, { withFileTypes: true })) {
      const full = path.join(folder, entry.name);
      const relative = path.relative(sourceRoot, full).replace(/\\/g, '/');
      if (ignored(relative)) continue;
      if (entry.isSymbolicLink()) throw new Error(`Symbolic link in package: ${relative}`);
      if (entry.isDirectory()) { walk(full); continue; }
      if (!entry.isFile()) continue;
      const owner = subpackages.find(item => relative.startsWith(item.root + '/')) || main;
      const bytes = fs.statSync(full).size;
      owner.bytes += bytes; owner.fileCount++;
      files.push({ path: relative, bytes, package: owner.name });
    }
  }
  walk(sourceRoot);
  const totalBytes = packages.reduce((sum, item) => sum + item.bytes, 0);
  const remainingBytes = budget.totalLimitBytes - totalBytes;
  const upcoming = Math.max(0, budget.plannedGames - budget.existingGames);
  const warnings = [];
  if (main.bytes > budget.mainTargetBytes) warnings.push('Main package exceeds development target');
  if (totalBytes > budget.totalTargetBytes) warnings.push('Total package exceeds development target');
  const withinLimits = main.bytes <= budget.mainLimitBytes && totalBytes <= budget.totalLimitBytes;
  return { measurement: 'source files after exclusions; platform build can differ', packages, totalBytes,
    remainingBytes, remainingMainBytes: budget.mainLimitBytes - main.bytes,
    budgetPerUpcomingGameBytes: upcoming ? Math.floor(Math.max(0, remainingBytes) / upcoming) : null,
    withinLimits, warnings, budget, files: files.sort((a, b) => b.bytes - a.bytes) };
}

if (require.main === module) {
  try {
    const args = process.argv.slice(2);
    const option = name => { const i = args.indexOf(name); return i < 0 ? null : args[i + 1]; };
    const budget = option('--budget') ? JSON.parse(fs.readFileSync(option('--budget'), 'utf8')) : DEFAULT_BUDGET;
    const projectRoot = path.resolve(option('--project') || path.resolve(__dirname, '..'));
    const result = measureProject(projectRoot, budget);
    const output = JSON.stringify(result, null, 2) + '\n';
    if (option('--output')) {
      const target = canonicalOutput(option('--output'));
      const configPath = path.join(projectRoot, 'project.config.json');
      const project = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      const shipping = fs.realpathSync(path.resolve(projectRoot, project.miniprogramRoot || 'minigame'));
      const relative = path.relative(shipping, target);
      const inside = !path.isAbsolute(relative) && relative !== '..' && !relative.startsWith('..' + path.sep);
      if (inside || target === fs.realpathSync(configPath)
        || (option('--budget') && target === fs.realpathSync(option('--budget')))) {
        throw new Error('Report must not overwrite shipping files or config');
      }
      if (fs.existsSync(target) && fs.lstatSync(target).isSymbolicLink()) throw new Error('Report cannot be a symbolic link');
      fs.writeFileSync(target, output);
    }
    process.stdout.write(output);
    if (!result.withinLimits || (args.includes('--strict-target') && result.warnings.length)) process.exitCode = 1;
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = { measureProject };
