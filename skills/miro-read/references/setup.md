# Connect your own Miro account

The REST helper requires Python 3.10+ and uses only its standard library. It has no dependency on a particular editor, operating system, Miro team, project, credential service, MCP installation or subscription to an AI provider.

If the agent already has a connected Miro read tool, its own authorization may be sufficient. The Python helper does not import credentials from that connector.

## Get a token

Follow Miro's [REST quickstart](https://developers.miro.com/docs/build-your-first-hello-world-rest-api-app) and [OAuth guide](https://developers.miro.com/docs/getting-started-with-oauth). Create your own app, request the `boards:read` scope, authorize/install it for the team containing your boards, and obtain the resulting access token through the supported Miro flow. Developer-team test access does not automatically grant access to boards in another team.

This package consumes an already authorized access token; it is not an OAuth callback server, token issuer, refresh service or hosted proxy. A shared or hosted multi-user integration must implement its own OAuth flow and give every user their own authorization. Do not distribute a developer's token to other people. Token expiry and reauthorization are handled through Miro or your own OAuth integration.

## Set the token privately

Use a secret manager or enter the token at a local prompt. Avoid literal tokens in shell history, command arguments, chat, screenshots, files and Git commits.

PowerShell:

```powershell
$miroCredentialInput = Read-Host 'Your Miro access token' -AsSecureString
$env:MIRO_ACCESS_TOKEN = [System.Net.NetworkCredential]::new('', $miroCredentialInput).Password
```

Bash:

```bash
read -r -s -p 'Your Miro access token: ' MIRO_ACCESS_TOKEN
export MIRO_ACCESS_TOKEN
```

Run the reader from the same shell. An AI agent only sees environment variables inherited by its process; if you set the token in another terminal, run the helper there, use your agent's documented secret configuration, or restart that agent from the prepared shell. A later terminal change does not update an already running desktop app.

Remove the environment variable when finished:

```powershell
Remove-Item Env:MIRO_ACCESS_TOKEN
```

```bash
unset MIRO_ACCESS_TOKEN
```

## Read a board

From the skill directory:

```bash
python scripts/miro_read.py read --board "BOARD_URL_OR_ID" --output-dir "../miro-local-export"
```

Use `python3` or `py` if appropriate for your installation. `--output-dir` must be empty or new. The helper never overwrites a previous export and writes results only after all requested API collections have been fetched. Files contain your private board content; keep them out of public repositories. Export normalization omits top-level author profiles, but it does not anonymize names or other private information embedded in board text, links or images.

## Common access failures

| Result | Action |
| --- | --- |
| Missing environment variable | Configure your token in the process running the helper. |
| HTTP 401 | Obtain a fresh authorized access token; do not retry the same invalid token repeatedly. |
| HTTP 403 | Confirm `boards:read`, authorization for the correct team, and your board access. |
| HTTP 404 | Verify the board/item ID and account access. A public viewing link is not a REST API credential. |
| HTTP 429 | The helper retries at most twice with bounded waits. Retry later if it still fails. |
| Network/TLS failure | Check proxy settings, connectivity and certificate trust. TLS verification stays enabled. |
| Cursor loop/page limit | Treat the read as incomplete; narrow the task or deliberately increase `--max-pages`. |

No access to private boards is required to run the synthetic test suite.
