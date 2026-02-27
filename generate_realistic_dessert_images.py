#!/usr/bin/env python3
"""Generate realistic dish images via OpenAI Images API and update scotts.js image paths.

Usage (PowerShell):
  $env:OPENAI_API_KEY='sk-...'
  python generate_realistic_dessert_images.py
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SCOTTS_PATH = ROOT / "data" / "categories" / "scotts.js"
IMG_DIR = ROOT / "data" / "categories" / "menu_images"
API_URL = "https://api.openai.com/v1/images/generations"
MODEL = "gpt-image-1"
FORCE_REGENERATE_NAMES = {"mashed potatoes"}

def load_scotts_items() -> tuple[str, List[dict], str]:
    content = SCOTTS_PATH.read_text(encoding="utf-8")
    start = content.find("[")
    end = content.rfind("]") + 1
    items = json.loads(content[start:end])
    return content[:start], items, content[end:]


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "dish"


def image_path_exists(rel_path: str) -> bool:
    if not rel_path:
        return False
    rel = rel_path.replace("\\", "/")
    if rel.startswith("data/"):
        p = ROOT / rel
    else:
        p = ROOT / rel
    return p.exists()


def build_prompt(item: dict) -> str:
    name = (item.get("name") or "").strip()
    subtitle = (item.get("subtitle") or "").strip()
    description = (item.get("description") or "").strip()
    category = (item.get("category") or "").strip()

    parts = [
        f"Photorealistic high-end restaurant food photo of {name}.",
        "Single plated dish, realistic ingredients, natural textures, fine dining presentation.",
        "No text, no logo, no watermark, no people, no hands.",
    ]
    if category:
        parts.append(f"Category: {category}.")
    if subtitle:
        parts.append(f"Key elements: {subtitle}.")
    if description:
        parts.append(f"Dish context: {description[:280]}.")
    return " ".join(parts)


def collect_missing_image_items(items: List[dict], replace_svg: bool = True) -> List[dict]:
    missing = []
    for item in items:
        name = (item.get("name") or "").strip().lower()
        img = item.get("image")
        if name in FORCE_REGENERATE_NAMES:
            missing.append(item)
            continue
        if not img or not image_path_exists(img):
            missing.append(item)
            continue
        if replace_svg and isinstance(img, str) and img.lower().endswith(".svg"):
            missing.append(item)
    return missing


def call_images_api(api_key: str, prompt: str, size: str = "1024x1024") -> bytes:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": size,
        "n": 1,
    }
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API error {exc.code}: {err_body}") from exc

    if "data" not in data or not data["data"]:
        raise RuntimeError(f"Unexpected API response: {data}")

    b64 = data["data"][0].get("b64_json")
    if not b64:
        raise RuntimeError(f"No b64_json in API response: {data}")

    return base64.b64decode(b64)


def update_scotts_images(items: List[dict], paths_by_name: Dict[str, str]) -> int:
    updated = 0
    for item in items:
        name = item.get("name")
        if name in paths_by_name:
            item["image"] = paths_by_name[name]
            updated += 1
    return updated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate realistic images for all menu items missing image files")
    parser.add_argument("--size", default="1024x1024", help="Image size, e.g. 1024x1024")
    parser.add_argument("--dry-run", action="store_true", help="Show planned actions without API calls")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit for number of generated images (0 = all missing)",
    )
    parser.add_argument(
        "--no-replace-svg",
        action="store_true",
        help="Do not regenerate items that currently use .svg images",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key and not args.dry_run:
        print("OPENAI_API_KEY is not set.")
        return 1

    IMG_DIR.mkdir(parents=True, exist_ok=True)

    prefix, items, suffix = load_scotts_items()
    missing_items = collect_missing_image_items(items, replace_svg=not args.no_replace_svg)
    if args.limit > 0:
        missing_items = missing_items[: args.limit]

    if not missing_items:
        print("No missing/broken images found in scotts.js")
        return 0

    print(f"Missing/broken images to process: {len(missing_items)}")

    paths_by_name: Dict[str, str] = {}
    failed: List[str] = []
    for item in missing_items:
        dish_name = (item.get("name") or "").strip()
        filename = f"{slugify(dish_name)}-generated.png"
        out_path = IMG_DIR / filename
        rel_path = f"data/categories/menu_images/{filename}"
        paths_by_name[dish_name] = rel_path
        prompt = build_prompt(item)

        if args.dry_run:
            print(f"[dry-run] {dish_name} -> {out_path}")
            continue

        print(f"Generating: {dish_name}")
        try:
            image_bytes = call_images_api(api_key=api_key, prompt=prompt, size=args.size)
            out_path.write_bytes(image_bytes)
            print(f"Saved: {out_path}")
        except Exception as exc:  # noqa: BLE001
            failed.append(f"{dish_name}: {exc}")
            paths_by_name.pop(dish_name, None)
            print(f"Failed: {dish_name} -> {exc}")

    if args.dry_run:
        print(f"[dry-run] Would update image paths in {SCOTTS_PATH} for {len(paths_by_name)} item(s)")
    else:
        updated = update_scotts_images(items, paths_by_name)
        SCOTTS_PATH.write_text(
            prefix + json.dumps(items, ensure_ascii=False, indent=2) + suffix,
            encoding="utf-8",
        )
        print(f"Updated image paths in {SCOTTS_PATH} for {updated} item(s)")
        if failed:
            print(f"Failed items: {len(failed)}")
            for line in failed:
                print(f" - {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
