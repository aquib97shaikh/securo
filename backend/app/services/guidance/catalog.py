import json
from pathlib import Path
from typing import Any, Optional


_CATALOG_PATH = Path(__file__).parent / "catalog.json"
_CACHED_CATALOG: Optional[dict[str, Any]] = None


def get_recommendation_catalog() -> dict[str, Any]:
    global _CACHED_CATALOG
    if _CACHED_CATALOG is None:
        try:
            with open(_CATALOG_PATH, "r", encoding="utf-8") as f:
                _CACHED_CATALOG = json.load(f)
        except Exception:
            _CACHED_CATALOG = {"version": "1.0.0", "rules": {}}
    return _CACHED_CATALOG


def get_rule_for_signal(signal_type: str) -> dict[str, Any]:
    catalog = get_recommendation_catalog()
    rules = catalog.get("rules", {})
    return rules.get(
        signal_type,
        {
            "family": "budget_control",
            "action_type": "review",
            "action_label": "Review details",
            "action_url": "/dashboard",
            "cooldown_days": 7,
            "why_template": "This financial signal indicates an area where spending or cash flow can be improved.",
            "how_template": "Calculated from your recent transaction and budget history.",
            "next_action_template": "Review recent activity to keep your finances aligned with your targets.",
        },
    )
