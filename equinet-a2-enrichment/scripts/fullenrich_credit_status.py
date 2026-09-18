#!/usr/bin/env python3
"""Print the FullEnrich credit-cap ledger summary."""
from __future__ import annotations
import json
from a2_fullenrich_budget import usage_summary
if __name__=='__main__':print(json.dumps(usage_summary(),indent=2))
