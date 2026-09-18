# Historical OCR Utility

**Status:** Historical evidence only — not part of the active A2 runtime.

This utility was used to extract text from the supplied HubSpot data-model image. Its output is preserved at `evaluations/hubspot-intake/data-model-tiled-ocr.json`, and the extraction method remains recorded in `foundations/hubspot/HUBSPOT-SNAPSHOT-MANIFEST.json`.

A2 does not require OCR for its operational enrichment workflows. The heavy OCR dependencies (`rapidocr-onnxruntime`, OpenCV, ONNX Runtime, NumPy, Pillow, Shapely and PyClipper) are therefore intentionally excluded from the active runtime environment.

The archived script hash before relocation was:

`96b7094f328c2e01761fa9d338244b32252b90480ccea1136915c3b8d9f2db43`

Re-running this historical utility requires a separate temporary environment and does not form part of A2 acceptance or normal operation.
