# Miro Read Skill

A portable, read-only agent skill for reading **your own Miro boards**. Includes a Python command-line reader that works without any AI agent, MCP server or third-party Python package.

**MIT licensed · Python 3.10+ · Windows / macOS / Linux · Your own credentials**

## What it does

- Reads API-visible items across every cursor page, with optional connector retrieval.
- Produces UTF-8 JSON and Markdown with frame grouping, timestamps and direct item links.
- Reads individual items and downloads explicitly selected original images through Miro resource descriptors.
- Separates source material from interpretations and reports content the API cannot expose.
- Uses GET only. No editing, moving, archiving, deleting or board sharing.

No account, team, board, project, access token or local machine path is bundled. All tests use synthetic data. Exports are local, private material and are not automatically published.

## Install as a skill

Download the `miro-read` ZIP asset from the repository's **Releases** section and extract its `miro-read` folder into your agent's skill directory. Alternatively, clone the repository and copy just `skills/miro-read`, not the whole collection.

For Codex, the destination is `~/.codex/skills/miro-read`; on Windows, `~` means your own user profile. The installed folder must contain [`SKILL.md`](SKILL.md) directly. Restart or reload your agent if needed. For another Agent Skills-compatible tool, use its documented skills directory. If the destination already exists, preserve it and review differences before replacing files.

Then ask:

```text
Use $miro-read to read this Miro board and summarize the latest decisions with source links: BOARD_URL
```

An already connected Miro tool may supply access in an agent. The bundled REST helper independently requires **your own** authorized access token with `boards:read`, set as `MIRO_ACCESS_TOKEN`. It does not borrow credentials from another person's computer or an agent connector. See [setup and authentication](references/setup.md) for private token entry on PowerShell and Bash, Miro OAuth links and common access errors.

## Use the CLI directly

From the repository directory, after configuring your own token in the same shell:

```bash
python scripts/miro_read.py read --board "BOARD_URL_OR_ID" --output-dir "../miro-local-export"
python scripts/miro_read.py read --board "BOARD_URL_OR_ID" --include-connectors --output-dir "../miro-local-export-with-links"
python scripts/miro_read.py item --board "BOARD_URL_OR_ID" --item "ITEM_ID"
python scripts/miro_read.py image --board "BOARD_URL_OR_ID" --item "IMAGE_ITEM_ID" --output "../miro-local-image.png"
python scripts/miro_read.py boards --query "SEARCH_TEXT"
```

Use `python3` or `py` where that is your Python command. No `pip install` is needed. A new or empty output directory is required; existing exports and images are preserved.

## Limits

API-visible items are not necessarily the whole visual board. Freehand/legacy objects, comments, attachment contents and unsupported objects may need separate visual inspection. Images are not automatically OCRed. A board edited while paging is not a transactional snapshot. This is a reader, not a lossless backup tool or a hosted OAuth service. [Coverage and API notes](references/api-notes.md) explain these boundaries.

## Development

```bash
python -m unittest discover -s tests -v
python scripts/miro_read.py --help
```

Tests simulate pagination, authorization failures, retries, resource descriptors, UTF-8 conversion, frame grouping and private-token handling. They neither require nor contact a real Miro board. GitHub Actions runs the tests on multiple Python versions. A real account's authorization and board access must be verified by its owner.

Please use synthetic examples in issues and pull requests. Do not submit tokens, signed image URLs, private exports or identifiable board screenshots. Runtime code uses only Python's standard library. Contributions are licensed under the [MIT license](LICENSE). This project is independent of Miro and is not an official Miro product.

## 中文快速开始

这是一个通用、只读的 Miro 阅读 skill，不包含任何预置看板、项目资料或访问凭据。克隆到你的 skill 目录，按[配置说明](references/setup.md)设置**你自己的** Miro Token，再提供你自己的看板链接即可。也可以直接运行上面的 Python 命令，不依赖 Codex。读取结果保存在本地；公开分享前请自行检查导出内容中的隐私信息。
