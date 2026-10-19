---
name: imaginarium-model-godot-creator
description: Use when creating, regenerating, downloading or integrating game models through Imaginarium's browser-based 3D Models panel and a Blender-to-Godot asset pipeline. Applies to Imaginarium model production requests, not standalone Tripo API integration or concept-only image generation.
---

# Imaginarium Model Godot Creator

Execute the established pipeline: **概念图 → 已登录的 Edge 快捷 3D Models 面板 → 下载 GLB → Blender 减面、修材质 → Godot 实机验收**. Invoking this skill does not itself authorize an unspecified batch, a new paid service or publishing.

## Asset brief and concept

Read the current project instructions, art specifications, existing assets and production records. Reuse the approved visual direction, gameplay dimensions and cartoon materials. Routine details within the requested batch do not need repeated approval.

**Use single-asset images for characters, dogs, buildings, large trees, large GPE and other large or frequently used gameplay assets.** Important silhouette, structural detail and repeated close viewing take priority over batching. Do not put several views or several characters in the same model input; separately generated inspection views are not multi-object source sheets. Rigged characters require an animation-aware processing path.

**Use four assets in one image for small props, small GPE, shrubs and small vegetation.** Keep four distinct isolated front views on a white background, generous separation, no shared ground or composed scene. Submit the whole image; do not split quadrants or silently replace missing objects with local models unless the user changes that requirement. For ambiguous GPE, large/high-frequency/visually important use selects single production; genuinely small variants can share a four-object sheet.

Buildings need clear corners/eaves and structural openings. Preserve roof-tile relief and equal-sized tiles. Use proportional scale; do not flatten height or taper tiles to hide source defects. New bitmap concepts use the available image-generation skill and must be inspected before uploading. Concept art is not a runtime screenshot or a finished model.

## Observe, submit, wait, download

- Use the existing Edge login and current observable 3D Models UI. Prefer a callable supported browser controller; use the project's established controller where appropriate. Read [local-toolchain.md](references/local-toolchain.md) for DoggyYou bindings. Check current authentication and actual tool availability; historical login success is not current-session proof.
- Reuse the dedicated persistent profile without copying cookies, extracting credentials or calling undocumented private endpoints. If authentication is needed, let the user complete it in the visible browser. Do not bypass company authentication or security controls.
- Observe a fresh page snapshot and available settings before acting. References/selectors and download handling must come from the current UI. Imaginarium may label its generator Tripo; that is different from switching to the standalone Tripo API.
- Record input image, prompt/settings, submission time and task/asset identifier. Use existing timing records to choose spaced status checks and keep the user informed; polling completion is an upper bound, not exact server duration. Do not submit again merely because time elapsed. After an ambiguous submission, find the existing task before retrying; after failure, inspect the cause before spending another generation.
- Download through the asset UI. Wait for completed download and preserve the raw source in the local art archive. Check nonzero size, GLB header/declared length, parse/import success and SHA256 before processing. Partial files and screenshots do not prove model completion. A blob download URL is not a reusable external-downloader URL.

## Blender production

- Inspect topology, connected components, normals, UVs, textures, dimensions and any armature. Four concepts may produce fewer than four actual objects: identify requested items visually and structurally; mesh count alone is not an object count. Only register complete retained items. Keep the task incomplete or revise input within scope when items are missing.
- Preserve source and create an editable Blender master. Static assets may use deterministic weld/Collapse Decimate, texture resizing, material cleanup, origin and axis correction. Do not describe decimation as manual quad retopology. Rigged models require an animation-aware pipeline; do not run the static preset on them. GPE requiring moving parts need separate meshes, correct pivots and a functional runtime check.
- Choose geometry/texture budgets for actual viewing distance and silhouette rather than one fixed face target. Preserve eaves, tile relief, holes, thin supports and UV seams. Compare source and candidate close views before selecting an export. Avoid face stretching, lost relief, muddy color and inconsistent scale.
- Export GLB in metres with correct pivot/orientation and proportional scale. Record actual triangles, texture sizes, AABB and hashes. Keep rejected candidates separate rather than overwriting approved assets.

## Godot integration and acceptance

- Use the game's approved shared cartoon shader and scene conventions. Add appropriate collision proxies for reachable objects; document purely distant decorations. Apply LOD, instancing or occlusion where useful and verify transitions/performance.
- Test the real scene at relevant human/dog viewpoints. Inspect imports, visible geometry/materials, placement/scale, collision and camera clearance. For characters check rig/animation; for moving GPE check actual interaction. Successful import is not visual approval.
- Maintain a compact production record: asset ID/use, concept, source/task ID, timestamps, editable master, processing recipe, export, units/budgets/hash, runtime reference, evidence and current status. Preserve unknown licensing status; successful download does not establish commercial permission.
- Carry the authorized production loop through integration and evidence. Distinguish generated, downloaded, processed, imported, runtime-verified and user-approved. Do not stop at a concept or queued generation as if the batch were finished. If blocked by login/service failure, retain identifiers and state what remains.
- For DoggyYou, present 3–5 native screenshots; use a short video where motion matters. Follow the user's PDF preference using the PDF skill. Version control/publishing follow existing authorized scope; never commit browser profiles, credentials or proprietary editor integrations.
