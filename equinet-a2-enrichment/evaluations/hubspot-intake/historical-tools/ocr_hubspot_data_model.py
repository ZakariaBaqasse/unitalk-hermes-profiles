#!/usr/bin/env python3
"""Tile and OCR the supplied HubSpot data-model image."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter
from rapidocr_onnxruntime import RapidOCR

SOURCE = Path("/opt/data/profiles/equinet/attachments/data-model-objects (1).png")
OUTPUT = Path("/opt/data/profiles/equinet-a2-enrichment/evaluations/hubspot-intake/data-model-tiled-ocr.json")
TILE_W = 700
TILE_H = 600
OVERLAP = 100
SCALE = 3


def main() -> None:
    image = Image.open(SOURCE).convert("RGB")
    engine = RapidOCR()
    rows = []
    tile_id = 0
    for top in range(0, image.height, TILE_H - OVERLAP):
        for left in range(0, image.width, TILE_W - OVERLAP):
            right = min(left + TILE_W, image.width)
            bottom = min(top + TILE_H, image.height)
            if right - left < 100 or bottom - top < 100:
                continue
            tile_id += 1
            tile = image.crop((left, top, right, bottom)).resize(
                ((right - left) * SCALE, (bottom - top) * SCALE),
                Image.Resampling.LANCZOS,
            ).convert("L")
            tile = ImageEnhance.Contrast(tile).enhance(1.7).filter(ImageFilter.SHARPEN)
            result = engine(tile)[0] or []
            for box, text, score in result:
                xs = [point[0] for point in box]
                ys = [point[1] for point in box]
                rows.append({
                    "tile_id": tile_id,
                    "text": text.strip(),
                    "score": float(score),
                    "x": left + min(xs) / SCALE,
                    "y": top + min(ys) / SCALE,
                    "box": box,
                })

    # Deduplicate overlapping-tile detections by normalized text and nearby position.
    kept = []
    for row in sorted(rows, key=lambda item: (-item["score"], item["y"], item["x"])):
        normalized = "".join(ch.lower() for ch in row["text"] if ch.isalnum())
        if not normalized:
            continue
        duplicate = False
        for prior in kept:
            prior_norm = "".join(ch.lower() for ch in prior["text"] if ch.isalnum())
            if normalized == prior_norm and abs(row["x"] - prior["x"]) < 80 and abs(row["y"] - prior["y"]) < 50:
                duplicate = True
                break
        if not duplicate:
            kept.append(row)

    kept.sort(key=lambda item: (item["y"], item["x"]))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(kept, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"image_size": image.size, "tiles": tile_id, "detections": len(kept), "output": str(OUTPUT)}, indent=2))
    for item in kept:
        print(f"y={item['y']:.0f} x={item['x']:.0f} score={item['score']:.3f} {item['text']}")


if __name__ == "__main__":
    main()
