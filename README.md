# Wine List

A static web app for wine catalog browsing, training, and dataset editing.

The project keeps a no-build architecture (plain HTML + Tailwind CDN + vanilla JS) and includes PWA support.

## Pages

- `index.html` - home and navigation.
- `wine_catalog.html` - wine catalog with search, category filters and detail view.
- `wine_trainer.html` - wine flashcards and quiz trainer.
- `wine_builder.html` - full wine record editor with export tools.

## Data

Primary source:

- `data/categories/wines-list.json` - raw wine records.
- `data/categories/images/` - wine images referenced by `image` field.

Runtime loader:

- `data/loader.js` fetches `wines-list.json`, exposes:
  - `window.allWineItems` (raw records)
  - `window.allFoodItems` (normalized runtime cards)
  - `window.previousFoodItems` (empty compatibility placeholder)
  - dispatches `foodLoaded`

## Quick Start

1. Start local server from repo root:

```powershell
python -m http.server 8080
```

2. Open:

```text
http://localhost:8080
```

Important: use HTTP/HTTPS, not `file://`.
Note: `file://` is supported in a limited fallback mode via `data/categories/wines-runtime.js`
for local quick checks, but PWA/service worker behavior still requires HTTP/HTTPS.

## Builder Exports

In `wine_builder.html`:

- `Export wines-list.json` - raw wine schema (UTF-8 JSON array).
- `Export wines-runtime.js` - compatibility payload:

```js
window.registerFoodCategory([...]);
```

## PWA / Offline

- `manifest.json` defines install metadata.
- `sw.js` pre-caches core pages + loader + `wines-list.json`.
- `data/categories/wines-runtime.js` supports `file://` fallback loading.

After updates, hard refresh if stale cache is observed.

## Validation After Changes

1. Open all pages and confirm no JS errors.
2. Confirm `foodLoaded` flow works (catalog/trainer/builder render records).
3. Verify mobile layouts do not clip controls at narrow widths.
4. Confirm service worker registration remains active.
