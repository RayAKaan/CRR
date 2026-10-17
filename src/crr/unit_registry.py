"""Loading and validation of immutable, versioned unit registry configuration."""

from __future__ import annotations

import json
import os
from decimal import Decimal
from pathlib import Path

from crr.domain import UnitDefinition, UnitRegistry


def load_unit_registry(path: str | None = None) -> UnitRegistry:
    configured = path or os.getenv("CRR_UNIT_REGISTRY_PATH")
    registry_path = (
        Path(configured)
        if configured
        else (Path(__file__).resolve().parent / "data" / "unit_registry.json")
    )
    with registry_path.open(encoding="utf-8") as file:
        payload = json.load(file)
    units = {
        item["code"]: UnitDefinition(
            code=item["code"],
            dimension=item["dimension"],
            to_base_factor=Decimal(item["to_base_factor"]),
        )
        for item in payload["units"]
    }
    return UnitRegistry(version=payload["version"], units=units)
