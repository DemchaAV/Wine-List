# Food List (Scott's Richmond)

A web app for menu reference and staff training for Scott's Richmond.

The project combines static HTML pages (no build step) with Python utilities for menu, allergen, and image maintenance.

## What's Inside

- `index.html` - home page and navigation.
- `food_trainer.html` - training mode (description, wine, allergens, MEP).
- `mobile_food.html` - menu catalog with search, filters, and full detail view.
- `food_builder.html` - dish editor with export to `scotts.js` format.
- `data/loader.js` - loads current and previous menu datasets.
- `sw.js` + `manifest.json` - PWA/offline support.

## Data

Primary files:

- `data/categories/scotts.js` - current menu (`window.registerFoodCategory([...])`).
- `data/categories/scotts_previous.js` - previous menu (`window.registerPreviousFoodCategory([...])`).
- `data/categories/food.json` - alternative JSON representation.
- `data/categories/menu_images/` - dish images.

Current repository stats:

- Current menu: `78` items.
- Previous menu: `71` items.
- Current categories: `Oysters`, `Caviar`, `Starters`, `Mains`, `Sides`, `Desserts`, `Festive Menu (SLM)`.

## Quick Start

1. Run a local HTTP server in the project root:

```powershell
python -m http.server 8080
```

2. Open:

```text
http://localhost:8080
```

Important: `file://` is not enough (data scripts and service worker need HTTP/HTTPS).

## Requirements

For the web app:

- Any modern browser (Tailwind and fonts are loaded from CDN).

For Python utilities:

- Python 3.10+
- Script-specific extras:
  - `requests` (for `cleanup_scotts.py`)
  - `PyMuPDF`/`fitz` (for `images_migrate.py`)
  - `OPENAI_API_KEY` (for `generate_realistic_dessert_images.py`)

Example install:

```powershell
pip install requests PyMuPDF
```

## Main Allergen Update Workflow

1. Scrape allergen data from viewthe.menu:

```powershell
python scrape_viewthemenu_allergens.py --url https://viewthe.menu/dbav --out data/viewthemenu_allergens.json
```

2. Sync allergens into local menu files:

```powershell
python sync_allergens_from_scraped.py
```

3. Review sync exceptions:

- `data/allergen_sync_exceptions.json`

## Useful Scripts

- `validate_scotts.py` - basic structure/type/ID validation for `scotts.js`.
- `validate_scotts_full.py` - extended glossary-format validation.
- `verify_allergens.py` - heuristic check for likely missing allergens.
- `normalize_glossary.py` - normalizes glossary structure.
- `match_images.py` - auto-matches dish images.
- `generate_realistic_dessert_images.py` - generates missing images via OpenAI Images API.
- `images_migrate.py` - extracts images from `Scotts Bibles - New-23.pdf`.
- `food_builder.html` (Export button) - exports data as `window.registerFoodCategory([...]);`.

## Manual Validation After Changes

```powershell
python validate_scotts.py
python validate_scotts_full.py
```

Then verify UI behavior in:

- `food_trainer.html`
- `mobile_food.html`
- `food_builder.html`

## Notes

- The project uses a service worker (`sw.js`) and caching. After frontend/data updates, you may need a hard refresh or cache clear.
- The repository includes one-off/historical migration scripts (for example `update_menu_feb2026.py`, `fix_mep_fields.py`). Review inputs before rerunning them.
