# Data Flow

## Canonical flow

`data/categories/wines-list.json` -> `scripts/generate_wine_runtime.mjs` -> `data/categories/wines-runtime.js`

## Runtime behavior

- HTTP pages fetch `wines-list.json`
- `file://` fallback uses `wines-runtime.js`
- `data/loader.js` normalizes data into `window.allWineCards`
