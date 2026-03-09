# Validation Checklist

## Data changes

```powershell
python .agent/skills/app-version-bump/scripts/bump_app_version.py
node scripts/generate_wine_runtime.mjs
```

Verify:

- `manifest.json` version changed
- `data/categories/wines-runtime.js` matches `wines-list.json`
- wine pages still load data through `data/loader.js`

## UI smoke targets

- `index.html`
- `wine_catalog.html`
- `wine_builder.html`
- `wine_trainer.html`
