#!/usr/bin/env python3
"""Create non-overwriting planning records, never runtime features or release approval."""
import argparse
import csv
import io
import json
from pathlib import Path
import re
import sys

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def csv_header(fields):
    output = io.StringIO(newline="")
    csv.writer(output).writerow(fields)
    return output.getvalue()


def contained(path, root):
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("output must stay inside the resolved project directory")
    return resolved


def build_records(game_id, title, modes):
    records = []
    for item in json.loads((ASSETS / "capabilities.json").read_text(encoding="utf-8")):
        group = item["group"]
        enabled = group == "base" or (group == "ai" and "solo-ai" in modes) or (group == "online" and "online" in modes)
        # Base requirements are reviewed against the actual product promise; no PASS inferred.
        records.append({**item, "scope": "REQUIRED" if enabled else "DEFERRED",
                        "scopeReason": "Review against confirmed launch promises" if enabled else "Not enabled by selected launch modes; explicit scope decision required to enable",
                        "implementation": "MISSING", "verification": "NOT_RUN" if enabled else "NOT_APPLICABLE",
                        "owner": None, "interface": None, "runtimeEntry": None,
                        "placeholder": {"currentBehavior": None, "gate": None, "exitCondition": None},
                        "evidence": [], "candidate": None})
    brief = (ASSETS / "game-brief.md").read_text(encoding="utf-8")
    brief = brief.replace("# 游戏初始化合同", "# " + title + " 初始化合同")
    brief = brief.replace("稳定gameId：由初始化命令填入", "稳定gameId：" + game_id)
    brief = brief.replace("首发模式：由初始化命令填入", "首发模式：" + ", ".join(modes))
    checklist = (ASSETS / "release-checklist.md").read_text(encoding="utf-8")
    checklist = checklist.replace("首发模式：未填写", "首发模式：" + ", ".join(modes))
    # Leave checklist rows NOT_RUN: an owner must explicitly review applicability.
    return {
        "brief.md": brief,
        "rule-map.csv": csv_header(["rule_id", "source_version", "source_location", "original_term", "reskin_term", "phase_action", "data_invariant", "implementation", "verification", "owner"]),
        "capabilities.json": json.dumps({"schemaVersion": 1, "skillVersion": "2.0.0", "gameId": game_id, "title": title, "stage": "B0", "launchModes": modes, "capabilities": records}, ensure_ascii=False, indent=2) + "\n",
        "asset-plan.csv": csv_header(["asset_id", "role", "decision", "source_file", "runtime_file", "display_size", "anchor", "alpha", "atlas_frame", "budget", "status", "owner"]),
        "release-checklist.md": checklist,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True, type=Path)
    parser.add_argument("--game-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--mode", action="append", choices=["solo-ai", "hotseat", "online"])
    parser.add_argument("--output-rel", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.game_id) or len(args.game_id) > 63:
            raise ValueError("game-id must be 1-63 lowercase letters/digits with internal hyphens")
        if not args.title.strip() or any(c in args.title for c in "\r\n\x00"):
            raise ValueError("title must be a nonempty single line")
        project = args.project_dir.resolve(strict=True)
        if not project.is_dir():
            raise ValueError("project-dir must be an existing directory")
        rel = args.output_rel if args.output_rel is not None else Path("docs") / "games" / args.game_id
        if rel.is_absolute() or rel.drive or ".." in rel.parts:
            raise ValueError("output-rel must be a relative path without parent traversal")
        target = contained(project / rel, project)
        if target.exists() and not target.is_dir():
            raise ValueError("output target is not a directory")
        modes = list(dict.fromkeys(args.mode or ["solo-ai"]))
        records = build_records(args.game_id, args.title.strip(), modes)
        # Preflight every path before making any write, including existing symlinks/junctions.
        for name in records:
            contained(target / name, project)
        report = {"write": args.write, "output": str(target), "launchModes": modes, "files": []}
        if args.write:
            target.mkdir(parents=True, exist_ok=True)
        for name, content in records.items():
            dest = target / name
            if dest.exists() or dest.is_symlink():
                action = "SKIPPED_EXISTS"
            elif args.write:
                contained(dest, project)
                try:
                    with dest.open("x", encoding="utf-8", newline="\n") as handle:
                        handle.write(content)
                    action = "CREATED"
                except FileExistsError:
                    action = "SKIPPED_EXISTS"
            else:
                action = "WOULD_CREATE"
            report["files"].append({"file": name, "action": action})
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    sys.exit(main())
