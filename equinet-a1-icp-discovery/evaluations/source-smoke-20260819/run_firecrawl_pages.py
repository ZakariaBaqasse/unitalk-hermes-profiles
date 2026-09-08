#!/usr/bin/env python3
"""Run bounded Firecrawl secondary-page smoke tests."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERMES = Path("/opt/hermes")
PROFILE = Path(__file__).resolve().parents[2]
# Add profile venv first so firecrawl-py SDK is importable, then Hermes for the provider
_VENV = PROFILE / ".venv" / "lib" / "python3.13" / "site-packages"
if _VENV.is_dir():
    sys.path.insert(0, str(_VENV))
sys.path.insert(0, str(HERMES))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROFILE / ".env", override=False)
os.chdir(PROFILE)
from plugins.web.firecrawl.provider import FirecrawlWebSearchProvider  # noqa: E402


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


async def run(pages: list[tuple[str, str, str]]) -> list[dict]:
    provider = FirecrawlWebSearchProvider()
    if not provider.is_available():
        raise RuntimeError("Firecrawl provider unavailable")
    results = []
    for source_id, page_type, url in pages:
        started_at = now()
        result = (await provider.extract([url], format="markdown"))[0]
        results.append({
            "source_id": source_id,
            "page_type": page_type,
            "requested_url": url,
            "started_at": started_at,
            "completed_at": now(),
            "result": result,
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", action="append", required=True, help="source_id|page_type|url")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pages = []
    for value in args.page:
        source_id, page_type, url = value.split("|", 2)
        pages.append((source_id, page_type, url))
    payload = {
        "test_id": "equinet-a1-firecrawl-directory-smoke-20260819",
        "test_type": "secondary_page_extraction",
        "generated_at": now(),
        "results": asyncio.run(run(pages)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "pages": len(pages),
        "errors": [{"source_id": item["source_id"], "page_type": item["page_type"], "error": item["result"].get("error")} for item in payload["results"] if item["result"].get("error")],
        "content_lengths": {f"{item['source_id']}:{item['page_type']}": len(item["result"].get("content", "")) for item in payload["results"]},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
