# DoggyYou local bindings

These are known project bindings, not proof that tools/authentication currently work. Check paths and actual schemas before execution. For another project, locate equivalent tooling instead of copying DoggyYou assumptions.

Project: `E:/Project/GOdot/doggy-my-friend`. Read `AGENTS.md`, `docs/art/production-pipeline.md` and `docs/art/browser-controller.md`. `docs/zcode-handoff.md` and production manifests link actual sources. The user's latest single-vs-four grouping rules in this skill supersede older documents describing all GPE as four-object batches.

## Browser

`tools/browser_controller.py` calls Microsoft Playwright MCP 0.0.82 over stdio. Default browser `msedge`; dedicated persistent profile `%LOCALAPPDATA%/DoggyYou/browser-profile-msedge`; output `builds/browser-controller`. One process owns a profile at a time. Use current snapshots and actual schemas, not stale saved element references.

```powershell
python tools/browser_controller.py --list-tools
python tools/browser_controller.py --plan tools/imaginarium-inspect.json
python tools/browser_controller.py --interactive
```

`--headed --plan tools/imaginarium-inspect.json` leaves a visible window for user authentication, then closes normally to save the profile. `tools/download_imaginarium_ui.cjs` is a project-specific UI downloader; inspect its arguments/dependencies before reuse. Its localhost CDP mode is a historical download-crash workaround, not mandatory configuration or permission to extract session secrets. Wait for completion and verify the file before closing the browser.

## Model processing

`tools/inspect_tripo_model.py` inspects sources. `tools/process_static_model.py` runs inside Blender; inspect current arguments before choosing a preset:

```powershell
blender --background --python tools/process_static_model.py -- --input source.glb --out candidate-folder --triangles 8000 --texture-size 1024 --width 1.7
```

Numbers above are examples, not approved budgets or building sizes. The script rejects armatures, preserves source snapshots, scales uniformly and adds Collapse Decimate. Inspect exports and evaluate silhouette/materials; running it does not guarantee repair of all AI topology defects. Use new output directories for new candidates. Characters/dogs require rig/animation-aware work, not this static script.

Use Blender/Godot MCP when exposed and connected as the project requires. If unavailable, record the actual fallback and use supported native tools; never claim MCP execution. Do not copy proprietary `addons/godot_mcp` into deliverables or touch `E:/Project/KARMA`.

Historical raw archives live in ignored `art_source/`; runtime models in `assets/models/`. Keep source hashes, recipes and runtime evidence traceable even when heavy raw sources stay local. Generation timing records may be under `art_source/environment_L3/imaginarium/`; a few samples do not promise a fixed generation time.
