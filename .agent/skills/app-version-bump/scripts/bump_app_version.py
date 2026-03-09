import json
from datetime import datetime
from pathlib import Path


MANIFEST_PATH = Path("manifest.json")


def build_versions(now: datetime) -> tuple[str, str]:
    base = f"{now.year}.{now.month}.{now.day}"
    timed = f"{base}.{now:%H%M}"
    return base, timed


def next_version(current: str, now: datetime) -> str:
    base, timed = build_versions(now)
    if current == base or current.startswith(base + "."):
        return timed
    return base


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    current = str(manifest.get("version", "")).strip()
    updated = next_version(current, datetime.now())
    manifest["version"] = updated
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated manifest version: {current or '<empty>'} -> {updated}")


if __name__ == "__main__":
    main()
