---
name: update-wine-data
description: Update the Wine-list dataset and supporting generated files when wines, wine metadata, images, or runtime payloads change. Use this skill for edits to wines-list.json, wines-runtime.js generation, wine images, and related loader-visible data.
---

# Update Wine Data

Use this skill for data changes in `C:\Users\Demch\OneDrive\projects\Wine-list`.

## Primary Files

- canonical data: `data/categories/wines-list.json`
- generated fallback: `data/categories/wines-runtime.js`
- generator: `scripts/generate_wine_runtime.mjs`
- file protocol fallback loader: `data/loader.js`

## Required Workflow

1. Prefer editing `data/categories/wines-list.json` as the source of truth.
2. Do not manually maintain `data/categories/wines-runtime.js` if regeneration is possible.
3. After data edits, run:

```powershell
node scripts/generate_wine_runtime.mjs
python .agent/skills/app-version-bump/scripts/bump_app_version.py
```

4. If images were added, keep them under `data/categories/images/`.
5. Smoke-test at least one affected wine page over HTTP.

## Guardrails

- keep the canonical dataset as a JSON array
- keep runtime generation deterministic
- preserve loader compatibility with both HTTP JSON loading and `file://` fallback

## References

- `references/data-flow.md`
