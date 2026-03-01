#!/usr/bin/env python3
"""
Generate glossary entries for menu items using AI models.

Input:
- JS wrapper file like: window.registerFoodCategory([...]);
- or plain JSON array file.

Output:
- Separate file with the same item keys as original, but with updated `glossary`.
- Default output format mirrors JS wrapper for easy merge.

Providers:
- ollama  (local)
- openai  (GPT API)
- gemini  (Google Gemini API)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Tuple


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def extract_items_from_source(raw: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Returns (items, mode)
    mode in {"js", "json"}
    """
    text = raw.strip()

    # JS wrapper mode
    marker = "window.registerFoodCategory("
    if marker in text:
        start = text.find(marker)
        open_idx = text.find("(", start)
        close_idx = text.rfind(");")
        if open_idx == -1 or close_idx == -1 or close_idx <= open_idx:
            raise ValueError("Invalid registerFoodCategory wrapper format.")
        payload = text[open_idx + 1 : close_idx].strip()
        items = json.loads(payload)
        if not isinstance(items, list):
            raise ValueError("Menu payload is not a list.")
        return items, "js"

    # JSON mode
    parsed = json.loads(text)
    if not isinstance(parsed, list):
        raise ValueError("JSON source must be an array of items.")
    return parsed, "json"


def dump_output(items: List[Dict[str, Any]], mode: str) -> str:
    payload = json.dumps(items, ensure_ascii=False, indent=2)
    if mode == "js":
        return f"window.registerFoodCategory({payload});\n"
    return payload + "\n"


def normalize_model_output(text: str) -> str:
    t = text.strip()
    # Remove markdown fences if present
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    return t.strip()


def parse_glossary(text: str, item: Dict[str, Any]) -> List[str]:
    cleaned = normalize_model_output(text)
    data = json.loads(cleaned)
    if not isinstance(data, list):
        raise ValueError("Model did not return a JSON array.")

    context_text = " ".join(
        str(item.get(k, "") or "") for k in ("name", "subtitle", "description")
    ).lower()
    allowed_terms = {
        "blini",
        "blinis",
        "caviar",
        "veloute",
        "meuniere",
        "aioli",
        "ponzu",
        "miso",
        "yuzu",
        "kosho",
        "tataki",
        "ceviche",
        "tartare",
        "romesco",
        "salsa verde",
        "purslane",
        "sea beet",
        "sea aster",
    }
    banned_starts = {
        "flavor profile",
        "flavour profile",
        "serving suggestion",
        "allergens",
        "allergen",
        "pairing",
        "wine pairing",
        "service note",
        "cooking style",
    }

    def keep_line(line: str) -> bool:
        if ":" not in line:
            return False
        term = line.split(":", 1)[0].strip().lower()
        if not term:
            return False
        if term in banned_starts:
            return False
        # keep only terms present in dish text, or whitelisted culinary terms
        if term in context_text:
            return True
        return any(term == t or term in t or t in term for t in allowed_terms)

    out: List[str] = []
    for x in data:
        if isinstance(x, str):
            s = x.strip()
            if s and keep_line(s):
                out.append(s)
    # Deduplicate while preserving order
    uniq: List[str] = []
    seen = set()
    for x in out:
        k = x.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(x)
    return uniq[:6]


def http_post_json(url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout: int = 120) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def build_prompt(item: Dict[str, Any]) -> str:
    name = item.get("name")
    subtitle = item.get("subtitle")
    description = item.get("description")
    category = item.get("category")
    allergens = item.get("allergens")

    return (
        "You generate concise restaurant glossary lines for staff training.\n"
        "Output ONLY valid JSON array of strings. No markdown, no commentary.\n"
        "Each line format: 'Term: short explanation'.\n"
        "Rules:\n"
        "- 2 to 5 lines\n"
        "- Focus on key ingredients, techniques, sauces, or culinary terms from dish text\n"
        "- Every 'Term' MUST be explicitly present in dish name/subtitle/description (or obvious singular/plural form)\n"
        "- Keep each line <= 140 chars\n"
        "- Practical and service-friendly wording\n"
        "- Do not repeat the dish name itself as a term\n"
        "- Forbidden terms: Flavor Profile, Serving Suggestion, Allergens, Pairing, Wine Pairing\n"
        "- Do NOT output service advice; only explain ingredient/culinary terms\n"
        "\n"
        f"Dish name: {name}\n"
        f"Subtitle: {subtitle}\n"
        f"Category: {category}\n"
        f"Description: {description}\n"
        f"Allergens: {allergens}\n"
    )


def generate_ollama(prompt: str, model: str, base_url: str) -> str:
    url = base_url.rstrip("/") + "/api/generate"
    data = http_post_json(
        url,
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        },
        headers={},
    )
    if "response" not in data:
        raise ValueError(f"Unexpected Ollama response: {data}")
    return str(data["response"])


def generate_openai(prompt: str, model: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    data = http_post_json(
        "https://api.openai.com/v1/chat/completions",
        {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": "Return only JSON array of glossary strings."},
                {"role": "user", "content": prompt},
            ],
        },
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise ValueError(f"Unexpected OpenAI response: {data}") from e


def generate_gemini(prompt: str, model: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    model_enc = urllib.parse.quote(model, safe="")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_enc}:generateContent?key={api_key}"
    data = http_post_json(
        url,
        {
            "generationConfig": {"temperature": 0.2},
            "contents": [{"parts": [{"text": prompt}]}],
        },
        headers={},
    )
    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "\n".join(p.get("text", "") for p in parts)
        if not text.strip():
            raise ValueError("Empty Gemini response text.")
        return text
    except Exception as e:
        raise ValueError(f"Unexpected Gemini response: {data}") from e


def generate_glossary_for_item(item: Dict[str, Any], provider: str, model: str, ollama_url: str, retries: int) -> List[str]:
    prompt = build_prompt(item)
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            if provider == "ollama":
                raw = generate_ollama(prompt, model, ollama_url)
            elif provider == "openai":
                raw = generate_openai(prompt, model)
            elif provider == "gemini":
                raw = generate_gemini(prompt, model)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            glossary = parse_glossary(raw, item)
            if not glossary:
                raise ValueError("No valid glossary lines after filtering.")
            return glossary
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(1.2 * attempt)
            else:
                break
    raise RuntimeError(f"Failed glossary generation for item '{item.get('name')}'. Last error: {last_err}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate glossary for menu items via Ollama/OpenAI/Gemini.")
    parser.add_argument("--input", required=True, help="Path to source menu file (JS wrapper or JSON array).")
    parser.add_argument("--output", required=True, help="Path to output file.")
    parser.add_argument("--provider", choices=["ollama", "openai", "gemini"], required=True)
    parser.add_argument("--model", required=True, help="Model name for selected provider.")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama base URL.")
    parser.add_argument("--limit", type=int, default=0, help="Process only first N items (0 = all).")
    parser.add_argument("--retries", type=int, default=3, help="Retries per item.")
    parser.add_argument("--overwrite-existing", action="store_true", help="Replace existing non-empty glossary as well.")
    args = parser.parse_args()

    raw = read_text(args.input)
    items, mode = extract_items_from_source(raw)

    total = len(items)
    limit = args.limit if args.limit and args.limit > 0 else total
    limit = min(limit, total)

    def is_empty_glossary(v: Any) -> bool:
        if v is None:
            return True
        if isinstance(v, list):
            return len([x for x in v if isinstance(x, str) and x.strip()]) == 0
        if isinstance(v, str):
            return v.strip() == ""
        return False

    updated = 0
    skipped = 0

    for idx, item in enumerate(items[:limit], start=1):
        if not args.overwrite_existing and not is_empty_glossary(item.get("glossary")):
            skipped += 1
            print(f"[{idx}/{limit}] skip: {item.get('name')}")
            continue

        glossary = generate_glossary_for_item(item, args.provider, args.model, args.ollama_url, args.retries)
        item["glossary"] = glossary
        updated += 1
        print(f"[{idx}/{limit}] updated: {item.get('name')} ({len(glossary)} lines)")

    output_text = dump_output(items, mode)
    write_text(args.output, output_text)

    print("---")
    print(f"Input items: {total}")
    print(f"Processed: {limit}")
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")
    print(f"Output: {args.output}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
