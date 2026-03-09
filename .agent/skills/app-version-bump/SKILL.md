---
name: app-version-bump
description: Bump the Wine-list application version after meaningful changes so the PWA and service worker fetch fresh assets and wine data. Use this skill whenever HTML, JS, CSS, manifest, service worker, or wine data files change.
---

# App Version Bump

Use this skill after meaningful changes in `C:\Users\Demch\OneDrive\projects\Wine-list`.

## Why

This project reads `manifest.json.version` through `data/app-init.js` and registers `sw.js?v=<version>`.

If the version stays the same, the cached app can keep stale wine data and assets.

## Required Rule

Before finishing a real change, bump `manifest.json.version`.

## Version Format

- first version of the day: `YYYY.M.D`
- another version on the same day: `YYYY.M.D.HH:mm`

Examples:

- `2026.3.9`
- `2026.3.9.11:24`

## Command

```powershell
python .agent/skills/app-version-bump/scripts/bump_app_version.py
```

## Verification

- confirm `manifest.json` contains the new version
- confirm pages still show the updated version label when loaded over HTTP

## References

- `references/versioning-rules.md`
