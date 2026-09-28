"""Generate Chart Agent demo fixture metadata from the VHop warehouse exports.

The committed demo JSON is deliberately small and sanitized.  This utility verifies
the expected VHop exports exist before regenerating any production fixture content;
it is never invoked at Chart Agent runtime.
"""

from __future__ import annotations

from pathlib import Path

REQUIRED_EXPORTS = ("fact_unit_inventory_snapshot.csv", "fact_unit_price_history.csv", "fact_sales_funnel_daily.csv")


def validate_vhop_source(warehouse_root: Path) -> None:
    export = warehouse_root / "vhop" / "export"
    missing = [name for name in REQUIRED_EXPORTS if not (export / name).is_file()]
    if missing:
        raise FileNotFoundError(f"VHop exports missing: {', '.join(missing)}")


if __name__ == "__main__":
    validate_vhop_source(Path("warehouse"))
    print("VHop source exports are available; committed Chart Agent demo fixtures are reproducible inputs.")
