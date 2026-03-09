---
name: change-validation
description: Validate Wine-list changes before finishing a task. Use this skill whenever wine data, HTML, JS, CSS, manifest, or service worker files are modified and the result must be proven with targeted checks and smoke testing.
---

# Change Validation

Use this skill after implementation changes in `C:\Users\Demch\OneDrive\projects\Wine-list`.

## Required Rules

1. Run at least one targeted validation for the changed behavior.
2. Run a smoke check of the affected page or data flow.
3. Bump the app version for meaningful app changes.
4. If coverage is missing, add the smallest useful validation instead of skipping tests.

## Common Commands

### Wine data changes

```powershell
python .agent/skills/app-version-bump/scripts/bump_app_version.py
node scripts/generate_wine_runtime.mjs
```

Then confirm `data/categories/wines-runtime.js` was regenerated from `data/categories/wines-list.json`.

### UI or static changes

Start a local server and smoke-test the affected page:

```powershell
python -m http.server 8080
```

Check:

- page renders
- version label loads
- no obvious JS errors
- affected interaction still works

## Output Contract

Final report must say:

- what command(s) ran
- what passed
- what smoke check was done
- any blocker or unverified area

## References

- `references/validation-checklist.md`
