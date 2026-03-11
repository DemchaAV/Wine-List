# Wine List

`Wine List` is a static web app for working with a wine catalogue in three modes: browsing, study, and editing. The project is designed as a lightweight no-build PWA, so it can be hosted on any static server and maintained without a frontend toolchain.

## What The Product Does

- Shows a searchable wine catalogue with filters by type and detailed product cards.
- Helps users study wines through flashcards and quiz sessions.
- Lets admins or owners edit wine records in the browser and export updated datasets.
- Supports installable PWA behavior and offline caching for the core app shell.

## Main User Flows

### Wine Catalog

`wine_catalog.html` is the browsing experience. It supports:

- full-text search by wine name, producer, region, and grapes
- category filters
- detailed wine profiles with tasting notes, grapes, food pairing, and technical facts
- image lightbox for bottle photos
- sweetness highlighting for sweet wines

### Wine Trainer

`wine_trainer.html` is a study mode for wine knowledge. It includes:

- category-based practice sessions
- flashcards before quiz mode
- quiz focus by region, grapes, tasting profile, food pairing, technical facts, or producer
- accuracy summary at the end of the session

### Wine Builder

`wine_builder.html` is the data editor. It allows you to:

- search and filter existing wine records
- add, edit, and delete entries
- save working changes to browser `localStorage`
- reset local edits back to the source dataset
- export both the canonical JSON file and the runtime fallback file

## Tech Stack

- Plain HTML pages
- Tailwind CSS via CDN
- Vanilla JavaScript
- Static JSON dataset
- Service worker + web app manifest for PWA support

The app intentionally avoids bundlers, frameworks, and build steps for the main runtime.

## Project Structure

```text
.
|- index.html
|- wine_catalog.html
|- wine_trainer.html
|- wine_builder.html
|- manifest.json
|- sw.js
|- data/
|  |- app-init.js
|  |- loader.js
|  |- wine-shared.js
|  `- categories/
|     |- wines-list.json
|     |- wines-runtime.js
|     `- images/
`- scripts/
   `- generate_wine_runtime.mjs
```

## Data Model And Runtime

The source of truth is:

- `data/categories/wines-list.json` - canonical raw wine records

Supporting assets:

- `data/categories/images/` - bottle and product images referenced by the `image` field
- `data/categories/wines-runtime.js` - generated fallback payload used when the app is opened via `file://`

Shared runtime files:

- `data/wine-shared.js` - helpers for category normalization, sweetness detection, and runtime card creation
- `data/loader.js` - loads the dataset and publishes runtime globals
- `data/app-init.js` - app version label and service worker bootstrap

At runtime, `data/loader.js` exposes:

- `window.allWineItems` - raw wine records
- `window.allWineCards` - normalized cards used by the UI
- `window.wineDataReady` - readiness flag
- `wineLoaded` - event fired when data is ready

Legacy `food*` aliases are still preserved for compatibility with older code paths during migration.

## Quick Start

Run a local static server from the repository root:

```powershell
python -m http.server 8080
```

Then open:

```text
http://localhost:8080
```

Important:

- Use HTTP or HTTPS for normal development.
- `file://` works only in a limited fallback mode through `data/categories/wines-runtime.js`.
- Service worker and full PWA behavior require HTTP or HTTPS.

## Editing And Export Workflow

If you are updating the wine list:

1. Open `wine_builder.html`.
2. Make changes in the editor.
3. Use `Save` to keep temporary edits in browser `localStorage`.
4. Use `Export wines-list.json` to download the canonical dataset.
5. Use `Export wines-runtime.js` to download the `file://` fallback payload if needed.

You can also regenerate the runtime fallback file from the canonical JSON source:

```powershell
node .\scripts\generate_wine_runtime.mjs
```

The script reads `data/categories/wines-list.json` and writes `data/categories/wines-runtime.js`.

## PWA And Offline Support

- `manifest.json` defines install metadata and app version
- `sw.js` caches the main pages and shared runtime files
- the dataset is cached for offline reuse
- the home page displays the current app version from the manifest

If the UI looks stale after an update, do a hard refresh or clear the old cache.

## Maintenance Notes

These files are support or report artifacts and are not part of the normal runtime load path:

- `data/categories/clean_wine_data.mjs`
- `data/categories/wine-data.cleaned.js`
- `data/categories/wine-data.validation-report.json`

## Recommended Checks After Changes

1. Open `index.html`, `wine_catalog.html`, `wine_trainer.html`, and `wine_builder.html` through a local server.
2. Confirm there are no JavaScript errors in the browser console.
3. Verify that catalogue search, filters, details, and image zoom work.
4. Run a trainer session and confirm cards, quiz flow, and results screen behave correctly.
5. Confirm builder load, save, reset, and export actions still work.
6. Check that the service worker registers and updates correctly.
