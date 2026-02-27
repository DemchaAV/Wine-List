#!/usr/bin/env python3
"""Sync allergens from scraped viewthemenu JSON into local menu files.

Updates:
- data/categories/scotts.js (allergens: list[str])
- data/categories/food.json (allergens: str)

Writes report:
- data/allergen_sync_exceptions.json
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent
SCRAPED_PATH = ROOT / "data" / "viewthemenu_allergens.json"
SCOTTS_PATH = ROOT / "data" / "categories" / "scotts.js"
FOOD_PATH = ROOT / "data" / "categories" / "food.json"
REPORT_PATH = ROOT / "data" / "allergen_sync_exceptions.json"

ALLERGEN_MAP = {
    "Cereals with Gluten": "Gluten",
    "Milk": "Dairy",
    "Tree Nuts": "Nuts",
}

# Manual name mapping from local names to the exact item names on viewthe.menu.
# Optional menu_hint disambiguates duplicates existing in multiple menus.
MANUAL_MATCH_RULES = [
    {"name": "BAKED ROSCOFF ONION AND GOAT’S CHEESE", "target": "Baked Roscoff onion and goat’s cheese Tarte Tatin"},
    {"name": "BAKED ROSCOFF ONION AND GOAT'S CHEESE TARTE TATIN", "target": "Baked Roscoff onion and goat’s cheese Tarte Tatin"},
    {"name": "CURRIED PARSNIP SOUP, FRIED ONION PAKORA", "target": "Curried parsnip soup"},
    {"name": "SCOTT'S KING PRAWN AND AVOCADO COCKTAIL", "target": "Scott’s king prawn cocktail"},
    {"name": "SCOTT'S PRAWN COCKTAIL, MARIE ROSE SAUCE", "target": "Scott’s king prawn cocktail"},
    {"name": "ROBATA GRILLED OCTOPUS WITH ROMESCO SAUCE, PINK FIR POTATOES AND SALSA VERDE", "target": "Robata grilled octopus"},
    {"name": "SAUTEED MONKFISH CHEEKS", "target": "Sautéed monkfish cheeks and snails"},
    {"name": "KASHMIRI MONKFISH AND TIGER PRAWN", "target": "Kashmiri Monkfish and tiger prawn masala"},
    {"name": "KASHMIRI MONKFISH AND TIGER PRAWN MASALA CURRY", "target": "Kashmiri Monkfish and tiger prawn masala"},
    {"name": "DOVER SOLE", "target": "Dover sole Meunière"},
    {"name": "SEARED SEABASS", "target": "Seared sea bass"},
    {"name": "ROASTED SHELLFISH", "target": "Roasted shellfish for two"},
    {"name": "ROASTED DEVONSHIRE CORNISH CHICKEN", "target": "Roasted Devonshire chicken"},
    {"name": "FILLET OF HAKE WITH BRAISED WHITE BEANS, CAVOLO NERO, PANCETTA AND CHICKEN BUTTER SAUCE", "target": "Pan-fried fillet of hake"},
    {"name": "FILLET OF HALIBUT, BROWN SHRIMP, CUCUMBER AND CHIVES, CHAMPAGNE VELOUTE AND WHIPPED PINK FIR POTATOES", "target": "Fillet of halibut"},
    {"name": "PORTLAND CRAB LINGUINI, CHILLI, GARLIC AND DATTERINI TOMATOES", "target": "Portland crab linguini"},
    {"name": "CHARCOAL GRILLED BLACK ANGUS SIRLOIN", "target": "Charcoal grilled Black Angus sirloin steak"},
    {"name": "FRIED JERUSALEM ARTICHOKES WITH SPRING ONION AND HOT HONEY DRESSING", "target": "Fried Jerusalem artichokes"},
    {"name": "GRILLED HISPI CABBAGE, BAGNA CAUDA, SHAVED PARMESAN AND SOURDOUGH BREAD CRUMBS", "target": "Grilled hispi cabbage"},
    {"name": "BABY GEM SALAD", "target": "Gem heart salad"},
    {"name": "COX'S PIPPIN AND BRAMBLEY APPLE PIE", "target": "Cox’s pippin and bramley apple pie"},
    {"name": "COX’S PIPPIN AND BRAMBLEY APPLE PIE", "target": "Cox’s pippin and bramley apple pie"},
    {"name": "PARIS - BREST", "target": "Paris-Brest", "menu_hint": "Dessert menu"},
    {"name": "AMEDEI CHOCOLATE MOUSSE WITH SEA SALT, OLIVE OIL AND SOURDOUGH CRISP", "target": "Amedei chocolate mousse"},
    {"name": "(SLM) CARAMELISED JERUSALEM", "target": "Caramelised Jerusalem Artichoke Soup"},
    {"name": "IMPERIAL CAVIAR", "target": "Caviar"},
    {"name": "OSCIETRA CAVIAR", "target": "Caviar"},
    {"name": "TIGER PRAWNS WITH GRILLED PINEAPPLE", "target": "Griddled tiger prawns"},
    {"name": "MIXED BEETROOT", "target": "Mixed beetroot", "menu_hint": "A La Carte"},
    {"name": "WILD MUSHROOM RISOTTO", "target": "Wild mushroom risotto", "menu_hint": "A La Carte"},
    {"name": "PUGLIAN BURRATA", "target": "Puglian Burrata", "menu_hint": "A La Carte"},
    {"name": "PAVLOVA", "target": "Pavlova", "menu_hint": "Dessert menu"},
    {"name": "CINNAMON DOUGHNUTS", "target": "Cinnamon doughnuts", "menu_hint": "Dessert menu"},
    {"name": "GOLDEN PINEAPPLE", "target": "Golden pineapple", "menu_hint": "Dessert menu"},
    {"name": "SEA BASS AND BLUE FIN TUNA CEVICHE", "target": "Sea Bass and bluefin tuna ceviche"},
    {"name": "PLATE AU DE FRUITS DE MER", "target": "Scott’s"},
    {"name": "BAKED ROSCOFF ONION AND GOAT’S CHEESE TARTE TATIN", "target": "Baked Roscoff onion and goat’s cheese Tarte Tatin", "menu_hint": "A La Carte"},
    {"name": "CURRIED PARSNIP SOUP", "target": "Curried parsnip soup", "menu_hint": "A La Carte"},
    {"name": "GILLARDEAU (FR) OYSTER", "target": "Oysters"},
    {"name": "BROWNSEA ISLAND ROCKS", "target": "Oysters"},
    {"name": "JERSEY ROCKS", "target": "Oysters"},
    {"name": "CARLINGFORD ROCKS", "target": "Oysters"},
    {"name": "CHIPPED POTATOES", "target": "Chipped potatoes", "menu_hint": "A La Carte"},
    {"name": "MASHED POTATOES", "target": "Mashed potatoes", "menu_hint": "A La Carte"},
    {"name": "STEAMED SPINACH", "target": "Steamed spinach", "menu_hint": "A La Carte"},
    {"name": "BUTTERED SPINACH", "target": "Buttered spinach", "menu_hint": "A La Carte"},
    {"name": "SPINACH, OLIVE OIL AND GARLIC", "target": "Spinach, olive oil and garlic", "menu_hint": "A La Carte"},
    {"name": "LEMON SORBET", "target": "Lemon sorbet", "menu_hint": "Dessert menu"},
    {"name": "COCONUT AND LIME SORBET", "target": "Coconut and lime sorbet", "menu_hint": "Dessert menu"},
    {"name": "BLOOD ORANGE SORBET", "target": "Blood orange sorbet", "menu_hint": "Dessert menu"},
    {"name": "HONEYCOMB ICE CREAM", "target": "Honeycomb ice cream", "menu_hint": "Dessert menu"},
    {"name": "PISTACHIO ICE CREAM", "target": "Pistachio ice cream", "menu_hint": "Dessert menu"},
    {"name": "RHUBARB RIPPLE ICE CREAM", "target": "Rhubarb ripple ice cream", "menu_hint": "Dessert menu"},
    {"name": "CHOCOLATE ICE CREAM", "target": "Chocolate ice cream", "menu_hint": "Dessert menu"},
]

# Fallback allergens for grouped local items that do not exist as a single dish on viewthe.menu.
# Values are in local display names (after ALLERGEN_MAP).
FALLBACK_ALLERGENS = {
    "ICE CREAMS": ["Dairy", "Eggs", "Nuts", "Soya", "Sulphur Dioxide/Sulphites"],
    "SELECTION OF SORBETS": ["Sulphur Dioxide/Sulphites"],
    "TRUFFLE GIFT BOX": ["Dairy", "Eggs", "Gluten", "Nuts", "Soya", "Sulphur Dioxide/Sulphites"],
}


def normalize_text(value: str) -> str:
    value = value or ""
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def build_name_variants(name: str) -> List[str]:
    variants = set()
    raw = (name or "").strip()
    if not raw:
        return []

    variants.add(normalize_text(raw))
    variants.add(normalize_text(re.sub(r"\([^)]*\)", " ", raw)))
    variants.add(normalize_text(re.sub(r"^\s*\([^)]*\)\s*", "", raw)))
    variants.discard("")
    return sorted(variants)


def mapped_allergen(name: str) -> str:
    return ALLERGEN_MAP.get(name, name)


def build_allergen_values(scraped_item: dict) -> Tuple[List[str], str]:
    contains = [mapped_allergen(x) for x in scraped_item.get("contains", [])]
    may = [mapped_allergen(x) for x in scraped_item.get("may_contain", [])]

    unique_contains = sorted(set(contains))
    unique_may = sorted(x for x in set(may) if x not in unique_contains)

    arr = [*unique_contains, *[f"May contain {x}" for x in unique_may]]
    txt = ", ".join(arr)
    return arr, txt


def category_matches(target_category: str, candidate: dict) -> bool:
    tc = normalize_text(target_category)
    sec = normalize_text(candidate.get("section_name", ""))
    menu = normalize_text(candidate.get("menu_name", ""))
    if not tc:
        return False
    return (tc and sec and (tc in sec or sec in tc)) or (tc and menu and (tc in menu or menu in tc))


def load_scraped() -> List[dict]:
    data = json.loads(SCRAPED_PATH.read_text(encoding="utf-8"))
    return data.get("items", [])


def build_index(scraped_items: List[dict]) -> Dict[str, List[dict]]:
    index: Dict[str, List[dict]] = {}
    for item in scraped_items:
        for key in build_name_variants(item.get("item_name", "")):
            index.setdefault(key, []).append(item)
    return index


def build_manual_rules() -> Dict[str, dict]:
    rules: Dict[str, dict] = {}
    for rule in MANUAL_MATCH_RULES:
        key = normalize_text(rule["name"])
        rules[key] = rule
    return rules


def fallback_allergens_for(name: str) -> Optional[List[str]]:
    return FALLBACK_ALLERGENS.get((name or "").strip().upper())


def apply_manual_rule(name: str, index: Dict[str, List[dict]], manual_rules: Dict[str, dict]) -> Optional[dict]:
    rule = manual_rules.get(normalize_text(name))
    if not rule:
        return None
    candidates = index.get(normalize_text(rule["target"]), [])
    if not candidates:
        return None
    menu_hint = normalize_text(rule.get("menu_hint", ""))
    if menu_hint:
        hinted = [c for c in candidates if menu_hint in normalize_text(c.get("menu_name", ""))]
        if len(hinted) == 1:
            return hinted[0]
    return candidates[0]


def choose_match(name: str, category: str, index: Dict[str, List[dict]], manual_rules: Dict[str, dict]) -> Tuple[Optional[dict], str, List[str]]:
    manual = apply_manual_rule(name, index, manual_rules)
    if manual:
        return manual, "matched_manual", []

    variants = build_name_variants(name)
    pool: Dict[str, dict] = {}
    for key in variants:
        for cand in index.get(key, []):
            pool[cand.get("guid", "")] = cand

    candidates = list(pool.values())
    if not candidates:
        return None, "not_found", []

    if len(candidates) == 1:
        return candidates[0], "matched", []

    cat_filtered = [c for c in candidates if category_matches(category, c)]
    if len(cat_filtered) == 1:
        return cat_filtered[0], "matched", []

    exact_name = normalize_text(name)
    exact_filtered = [c for c in cat_filtered if normalize_text(c.get("item_name", "")) == exact_name]
    if len(exact_filtered) == 1:
        return exact_filtered[0], "matched", []

    candidates_to_report = cat_filtered if cat_filtered else candidates
    candidate_names = [
        f"{c.get('item_name','')} [{c.get('menu_name','')} / {c.get('section_name','')}]"
        for c in candidates_to_report
    ]
    return None, "ambiguous", sorted(set(candidate_names))


def load_scotts_items() -> Tuple[str, List[dict], str]:
    content = SCOTTS_PATH.read_text(encoding="utf-8")
    start = content.find("[")
    end = content.rfind("]") + 1
    items = json.loads(content[start:end])
    return content[:start], items, content[end:]


def save_scotts(prefix: str, items: List[dict], suffix: str) -> None:
    SCOTTS_PATH.write_text(prefix + json.dumps(items, ensure_ascii=False, indent=2) + suffix, encoding="utf-8")


def load_food() -> dict:
    return json.loads(FOOD_PATH.read_text(encoding="utf-8"))


def save_food(data: dict) -> None:
    FOOD_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    scraped_items = load_scraped()
    index = build_index(scraped_items)
    manual_rules = build_manual_rules()

    report = {
        "scraped_source": str(SCRAPED_PATH),
        "updated_files": [str(SCOTTS_PATH), str(FOOD_PATH)],
        "summary": {},
        "exceptions": [],
        "unused_scraped_items": [],
    }

    matched_guids = set()

    sc_prefix, sc_items, sc_suffix = load_scotts_items()
    sc_updated = 0
    sc_renamed = 0
    sc_manual = 0
    sc_fallback = 0
    for item in sc_items:
        matched, status, candidates = choose_match(item.get("name", ""), item.get("category", ""), index, manual_rules)
        if matched:
            new_arr, _ = build_allergen_values(matched)
            item["allergens"] = new_arr
            site_name = matched.get("item_name", "") or item.get("name", "")
            if item.get("name") != site_name:
                sc_renamed += 1
            item["name"] = site_name
            if status == "matched_manual":
                sc_manual += 1
            sc_updated += 1
            matched_guids.add(matched.get("guid", ""))
        else:
            fallback = fallback_allergens_for(item.get("name", ""))
            if fallback is not None:
                item["allergens"] = fallback
                sc_updated += 1
                sc_fallback += 1
                continue
            report["exceptions"].append(
                {
                    "file": str(SCOTTS_PATH),
                    "status": status,
                    "name": item.get("name", ""),
                    "category": item.get("category", ""),
                    "candidates": candidates,
                }
            )
    save_scotts(sc_prefix, sc_items, sc_suffix)

    food_data = load_food()
    food_total = 0
    food_updated = 0
    food_renamed = 0
    food_manual = 0
    food_fallback = 0
    for category in food_data.get("categories", []):
        cat_name = category.get("name", "")
        for item in category.get("items", []):
            food_total += 1
            matched, status, candidates = choose_match(item.get("name", ""), cat_name, index, manual_rules)
            if matched:
                _, new_txt = build_allergen_values(matched)
                item["allergens"] = new_txt
                site_name = matched.get("item_name", "") or item.get("name", "")
                if item.get("name") != site_name:
                    food_renamed += 1
                item["name"] = site_name
                if status == "matched_manual":
                    food_manual += 1
                food_updated += 1
                matched_guids.add(matched.get("guid", ""))
            else:
                fallback = fallback_allergens_for(item.get("name", ""))
                if fallback is not None:
                    item["allergens"] = ", ".join(fallback)
                    food_updated += 1
                    food_fallback += 1
                    continue
                report["exceptions"].append(
                    {
                        "file": str(FOOD_PATH),
                        "status": status,
                        "name": item.get("name", ""),
                        "category": cat_name,
                        "candidates": candidates,
                    }
                )
    save_food(food_data)

    for s in scraped_items:
        guid = s.get("guid", "")
        if guid and guid not in matched_guids:
            report["unused_scraped_items"].append(
                {
                    "name": s.get("item_name", ""),
                    "menu_name": s.get("menu_name", ""),
                    "section_name": s.get("section_name", ""),
                    "guid": guid,
                }
            )

    report["summary"] = {
        "scotts_total": len(sc_items),
        "scotts_updated": sc_updated,
        "scotts_renamed": sc_renamed,
        "scotts_manual_matched": sc_manual,
        "scotts_fallback_applied": sc_fallback,
        "food_total": food_total,
        "food_updated": food_updated,
        "food_renamed": food_renamed,
        "food_manual_matched": food_manual,
        "food_fallback_applied": food_fallback,
        "exceptions_count": len(report["exceptions"]),
        "unused_scraped_items_count": len(report["unused_scraped_items"]),
    }

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"Saved report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
