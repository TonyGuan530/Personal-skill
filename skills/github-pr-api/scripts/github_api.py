"""GitHub REST requests using explicitly configured environment credentials.

No retries, redirects, credential discovery, shell interpolation, or token output.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit


class ApiError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(method, path, body=None, opener=None):
    parsed = urlsplit(path)
    if (not path.startswith('/') or path.startswith('//') or parsed.scheme
            or parsed.netloc or parsed.fragment or '\\' in path
            or any(ord(c) < 32 or ord(c) == 127 for c in path)):
        raise ApiError('Use an API path such as /repos/OWNER/REPO/pulls; absolute URLs are rejected.')
    if method not in ('GET', 'POST', 'PATCH'):
        raise ApiError('Supported methods: GET, POST, PATCH.')
    resource = parsed.path
    allowed = r'/repos/[^/]+/[^/]+(?:/(?:pulls(?:/\d+)?|compare/[^?]+|commits/[^?]+|branches(?:/[^?]+)?))?'
    if not (re.fullmatch(allowed, resource) or resource == '/user'):
        raise ApiError('This helper only supports identity, repository, branch, commit, compare, and PR endpoints.')
    if method == 'POST' and not re.fullmatch(r'/repos/[^/]+/[^/]+/pulls', resource):
        raise ApiError('POST is limited to PR creation.')
    if method == 'PATCH' and not re.fullmatch(r'/repos/[^/]+/[^/]+/pulls/\d+', resource):
        raise ApiError('PATCH is limited to PR updates.')
    if method == 'GET' and body is not None:
        raise ApiError('GET does not accept a request body.')
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ApiError('No API credential: configure GH_TOKEN or GITHUB_TOKEN locally. Do not paste it in chat.')
    payload = None if body is None else json.dumps(body, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request('https://api.github.com' + path, data=payload, method=method,
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'Content-Type': 'application/json', 'X-GitHub-Api-Version': '2026-03-10',
                 'User-Agent': 'codex-github-pr-api'})
    client = opener or urllib.request.build_opener(NoRedirect())
    try:
        with client.open(req, timeout=30) as response:
            data = response.read()
            return json.loads(data) if data else None
    except urllib.error.HTTPError as exc:
        # Never echo request headers, token, or an untrusted response body.
        reasons = {401: 'Authentication failed.',
                   403: 'Forbidden: check repository permissions, SSO, and rate limits.',
                   404: 'Resource absent or hidden from this credential; user access is not established by 404.',
                   422: 'Validation failed: inspect fields and check for an existing PR.'}
        reason = reasons.get(exc.code, 'Request failed; inspect the target before retrying writes.')
        raise ApiError(f'HTTP {exc.code}. {reason} No automatic retry was made.') from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise ApiError('Network or response failure. A write may have succeeded: GET the target before retrying.') from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', help='/repos/OWNER/REPO/pulls or another GitHub REST path')
    parser.add_argument('--method', choices=['GET', 'POST', 'PATCH'], default='GET')
    parser.add_argument('--body-file', type=Path, help='UTF-8 JSON request body, without credentials')
    args = parser.parse_args(argv)
    try:
        body = json.loads(args.body_file.read_text(encoding='utf-8-sig')) if args.body_file else None
        result = request(args.method, args.path, body)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ApiError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
