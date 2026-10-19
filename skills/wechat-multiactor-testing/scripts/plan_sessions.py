"""Validate actor bindings and print a non-executing, credential-free launch plan."""
import argparse
import json
import os
from pathlib import Path
import re


def plan(config, install, environ):
    route = config.get('route')
    if route not in ('bridge-project', 'sdk-port'):
        raise ValueError('route must be bridge-project or sdk-port')
    if not isinstance(config.get('candidate'), str) or not re.fullmatch(r'[0-9a-fA-F]{40}', config['candidate']):
        raise ValueError('Record a fixed 40-character Git commit before planning')
    if not (install / 'cli.bat').is_file():
        raise ValueError('Official cli.bat is missing from install-dir')
    actors = config.get('actors', [])
    if len(actors) < 2:
        raise ValueError('At least two actors required')
    seen = {k: set() for k in ('alias', 'port', 'env', 'project', 'account')}
    result = []
    for a in actors:
        alias, port, env_name = a['alias'], a['port'], a['accountEnv']
        if not re.fullmatch(r'[a-z][a-z0-9-]{0,39}', alias):
            raise ValueError('Invalid actor alias')
        if type(port) is not int or not 1024 <= port <= 65535:
            raise ValueError('Port must be an integer in 1024..65535')
        if not re.fullmatch(r'[A-Z][A-Z0-9_]*', env_name):
            raise ValueError('accountEnv must name an environment variable')
        project = Path(a['project'])
        if not project.is_absolute():
            raise ValueError('Actor project must be an absolute path')
        project = project.resolve(strict=True)
        if not (project / 'project.config.json').is_file():
            raise ValueError('Actor project lacks project.config.json')
        values = {'alias': alias, 'port': port, 'env': env_name}
        if route == 'bridge-project':
            values['project'] = os.path.normcase(str(project))
        account = environ.get(env_name)
        if account:
            values['account'] = account
        for key, value in values.items():
            if value in seen[key]:
                raise ValueError('Duplicate actor ' + key + '; isolation is not established')
            seen[key].add(value)
        result.append({'alias': alias, 'project': str(project), 'port': port,
                       'accountEnv': env_name, 'accountConfigured': bool(account),
                       'argvTemplate': [str(install / 'cli.bat'), 'auto', '--project', str(project),
                                        '--auto-port', str(port), '--auto-account', '<env:' + env_name + '>'],
                       'routingVerified': False, 'serverIdentityVerified': False})
    return {'schemaVersion': 1, 'candidate': config['candidate'], 'route': route, 'executed': False,
            'sourceEquality': 'NOT_VERIFIED', 'portAvailability': 'NOT_VERIFIED',
            'actors': result, 'next': 'Resolve accounts locally, verify free ports and fixed sources, then validate each actor route in an authorized window'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--install-dir', type=Path, required=True)
    a = p.parse_args()
    try:
        result = plan(json.loads(a.config.read_text(encoding='utf-8-sig')), a.install_dir.resolve(strict=True), os.environ)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (KeyError, TypeError, OSError, ValueError) as e:
        p.error(str(e))


if __name__ == '__main__':
    main()
