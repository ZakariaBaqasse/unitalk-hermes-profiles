#!/usr/bin/env python3
"""Run bounded Firecrawl landing-page smoke tests for approved A1 directories."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[2]
HERMES = Path("/opt/hermes")
_VENV = PROFILE / ".venv" / "lib" / "python3.13" / "site-packages"
if _VENV.is_dir():
    sys.path.insert(0, str(_VENV))
sys.path.insert(0, str(HERMES))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROFILE / ".env", override=False)
os.chdir(PROFILE)

from plugins.web.firecrawl.provider import FirecrawlWebSearchProvider  # noqa: E402

SOURCES = {
    "pdf.american_farriers_association": "https://americanfarriers.org/search/newsearch.asp",
    "pdf.professional_farriers_directory": "https://professionalfarriers.com/",
    "pdf.farrier_industry_association": "https://www.farrierindustry.org/",
    "pdf.farrieriq": "https://farrieriq.com/directory",
    "pdf.horseprofinder": "https://horseprofinder.com/",
    "pdf.edss_farriers": "https://edss.co/farriers",
    "pdf.bwfa_kentucky": "https://www.bwfa.net/kentucky",
    "pdf.mad_barn_directory": "https://madbarn.com/directory",
    "pdf.equinenow_kentucky_farms": "https://www.equinenow.com/kentuckyfarms.htm",
    "pdf.newhorse": "https://www.newhorse.com/",
    "pdf.hast_farriers": "http://www.hast.net/farriers.htm",
    "pdf.best_of_lexington_farriers": "https://www.bestoflexingtonkentucky.com/farrier/kentucky",
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


async def run(source_ids: list[str]) -> list[dict]:
    provider = FirecrawlWebSearchProvider()
    if not provider.is_available():
        raise RuntimeError("Firecrawl provider is not available through the configured A1 profile credentials.")
    output: list[dict] = []
    for source_id in source_ids:
        url = SOURCES[source_id]
        started_at = now()
        result = (await provider.extract([url], format="markdown"))[0]
        output.append({
            "source_id": source_id,
            "requested_url": url,
            "started_at": started_at,
            "completed_at": now(),
            "result": result,
        })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", nargs="+", required=True, choices=sorted(SOURCES))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = {
        "test_id": "equinet-a1-firecrawl-directory-smoke-20260819",
        "test_type": "landing_page_access",
        "method": "Firecrawl web extraction",
        "scope": "public pages only; no login, proxy, browser fallback or write",
        "generated_at": now(),
        "results": asyncio.run(run(args.sources)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "sources": args.sources,
        "errors": [item["source_id"] for item in payload["results"] if item["result"].get("error")],
        "content_lengths": {item["source_id"]: len(item["result"].get("content", "")) for item in payload["results"]},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
