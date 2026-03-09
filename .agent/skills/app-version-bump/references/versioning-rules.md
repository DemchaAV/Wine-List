# Versioning Rules

## Source of truth

- `manifest.json` field `version`

## Update path

- `data/app-init.js` fetches `manifest.json`
- pages show `v<version>`
- service worker registers as `./sw.js?v=<version>`
- `sw.js` uses the query param to build a new cache name

## Affected files

- `manifest.json`
- `sw.js`
- `data/app-init.js`
- `index.html`
- `wine_builder.html`
- `wine_catalog.html`
- `wine_trainer.html`
