"""Read official WeChat capabilities; never start a game or expose account values."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess


def command(install, entry, args):
    """Same bootstrap as official .cmd, with shell-free argument passing."""
    excluded = {'node.exe', 'node-18.exe', 'wxfilewatcher.exe',
                'wxfilewatcher_x64.exe', 'notification_helper.exe', 'wechatdevtools.exe'}
    executables = [p for p in install.glob('*.exe')
                   if p.name.lower() not in excluded and p.stat().st_size > 50_000_000]
    script = install / 'resources/app.asar.unpacked/js/common/cli' / entry
    if len(executables) != 1 or not script.is_file():
        raise ValueError('Official CLI layout changed or Electron executable ambiguous; inspect wrapper first')
    prefix = "process.execPath,e,'--electron'" if entry == 'skill-index.js' else "process.execPath,'--ms-enable-electron-run-as-node',e,'--electron'"
    bootstrap = "const e=process.argv[1],a=process.argv.slice(2);process.argv=[" + prefix + "].concat(a);require(e)"
    return [str(executables[0]), '-e', bootstrap, str(script), *args]


def run(install, entry, args):
    env = {**os.environ, 'ELECTRON_RUN_AS_NODE': '1', 'cwd': str(Path.cwd())}
    try:
        p = subprocess.run(command(install, entry, args), cwd=install, env=env,
                           shell=False, capture_output=True, timeout=25)
        return {'exit': p.returncode, 'stdout': p.stdout.decode('utf-8', errors='replace')}
    except subprocess.TimeoutExpired:
        return {'exit': None, 'error': 'TIMEOUT'}
    except OSError:
        return {'exit': None, 'error': 'PROCESS_UNAVAILABLE'}


def parse_reply(result):
    raw = result.get('stdout', '')
    decoder = json.JSONDecoder()
    for match in re.finditer(r'\{', raw):
        try:
            obj, _ = decoder.raw_decode(raw[match.start():])
            if isinstance(obj, dict) and 'ok' in obj:
                return obj
        except ValueError:
            pass
    return {}


def summarize_accounts(reply):
    result = reply.get('result', {})
    if not isinstance(result, dict):
        result = {}
    accounts = result.get('accounts')
    success = reply.get('ok') is True and result.get('success') is True
    count = len(accounts) if isinstance(accounts, list) else None
    return {'ok': success,
            'count': count,
            'interpretation': 'API_LIST_ONLY; not a count of open multi-account debugger windows',
            'identityValuesExported': False}


def probe(install, project, client, accounts=False):
    package = json.loads((install / 'resources/app.asar.unpacked/package.json').read_text(encoding='utf-8'))
    skill = (install / 'resources/app.asar.unpacked/wechatide-skill/SKILL.md').read_text(encoding='utf-8')
    match = re.search(r'^version:\s*([\w.\-]+)', skill, re.M)
    if not match:
        raise ValueError('Cannot identify installed official skill version')
    version = match.group(1)
    native = run(install, 'index.js', ['auto', '--help'])
    canvas = run(install, 'skill-index.js', ['-c', client, 'automation_game_action', '--help'])
    status = parse_reply(run(install, 'skill-index.js', ['-c', client, 'check_wechatide_status', '--skill-version', version]))
    r = status.get('result', {})
    if not isinstance(r, dict):
        r = {}
    report = {'schemaVersion': 1, 'ideVersion': package.get('version'), 'skillVersion': version,
              'compileType': json.loads((project / 'project.config.json').read_text(encoding='utf-8-sig')).get('compileType'),
              'autoAccountFlag': native.get('exit') == 0 and '--auto-account' in native.get('stdout', ''),
              'autoPortFlag': native.get('exit') == 0 and '--auto-port' in native.get('stdout', ''),
              'canvasTouchTool': canvas.get('exit') == 0 and 'touchstart' in canvas.get('stdout', ''),
              'statusOk': status.get('ok') is True and r.get('success') is True,
              'loginExpired': r.get('loginExpired') if isinstance(r.get('loginExpired'), bool) else None,
              'cliTokenRequired': r.get('cliTokenRequired') if isinstance(r.get('cliTokenRequired'), bool) else None,
              'mcpTokenRequired': r.get('mcpTokenRequired') if isinstance(r.get('mcpTokenRequired'), bool) else None,
              'accounts': {'status': 'NOT_REQUESTED'}, 'multiActorRouting': 'NOT_RUN', 'gameQA': 'NOT_RUN'}
    if accounts and report['statusOk'] and report['loginExpired'] is False:
        reply = parse_reply(run(install, 'skill-index.js', ['-c', client, 'automation_testaccount', '--project', str(project), '--action', 'list']))
        report['accounts'] = summarize_accounts(reply)
    elif accounts:
        report['accounts'] = {'status': 'BLOCKED_STATUS_OR_LOGIN'}
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--install-dir', type=Path, required=True)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--client', default='zcode')
    p.add_argument('--accounts', action='store_true')
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    try:
        if a.output and a.output.exists():
            raise ValueError('Output exists; use a new evidence filename')
        report = probe(a.install_dir.resolve(strict=True), a.project.resolve(strict=True), a.client, a.accounts)
        text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
        if a.output:
            with a.output.open('x', encoding='utf-8', newline='\n') as f:
                f.write(text)
        print(text, end='')
        return 0 if report['statusOk'] else 2
    except (OSError, ValueError) as e:
        p.error(str(e))


if __name__ == '__main__':
    raise SystemExit(main())
