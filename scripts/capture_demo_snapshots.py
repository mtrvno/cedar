"""Capture live API responses as offline snapshots — run this the morning of demo day.

If venue wifi dies mid-demo, the server automatically falls back to these
snapshots, and provenance honestly reports "snapshot (captured ...)".

Usage:
    python scripts/capture_demo_snapshots.py
"""

import asyncio
import os
import sys
from pathlib import Path

os.environ["CHILDSIGHT_CAPTURE"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from childsight import clients  # noqa: E402


async def main() -> None:
    print("Capturing GDACS event list...")
    g = await clients.gdacs_events()
    iso3s = sorted({e["iso3"].strip() for e in g["events"] if e.get("iso3") and len(e["iso3"].strip()) == 3})
    print(f"  {g['count']} events across {len(iso3s)} countries: {', '.join(iso3s)}")

    print("Capturing EONET events...")
    try:
        await clients.eonet_events(limit=30)
    except Exception as e:  # noqa: BLE001
        print(f"  EONET skipped: {e}")

    for iso3 in iso3s:
        print(f"Capturing UNICEF CCRI + child population for {iso3}...")
        try:
            await clients.unicef_ccri(iso3)
        except Exception as e:  # noqa: BLE001
            print(f"  CCRI {iso3} skipped: {e}")
        try:
            await clients.unicef_child_population(iso3)
        except Exception as e:  # noqa: BLE001
            print(f"  Population {iso3} skipped: {e}")

        area = clients.ISO3_TO_M49.get(iso3)
        if not area:
            continue
        for series in ("VC_DSR_MTMP", "SH_DYN_MORT", "SH_STA_STNT", "SP_ACS_BSRVH2O", "AG_PRD_FIESMS"):
            try:
                await clients.sdg_series_data(series, area, page_size=1)
            except Exception:  # noqa: BLE001
                pass  # not every series exists for every country

    n = len(list(clients.SNAPSHOT_DIR.glob("*.json")))
    print(f"\nDone. {n} snapshots in {clients.SNAPSHOT_DIR}")
    print("The server will use these automatically if live APIs are unreachable.")


if __name__ == "__main__":
    asyncio.run(main())
