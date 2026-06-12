"""Build the bundled CCRI reference dataset (one-time setup, ~5 min).

CCRI is a static 2020-21 release — there is no reason to query UNICEF's SDMX
API per-country at demo time. This script downloads it once for all countries
into src/childsight/data/ccri_all.csv; after that, every CCRI lookup is
instant and immune to SDMX slowness.

Usage:
    python scripts/fetch_ccri_bundle.py
"""

import csv
import io
import sys
import time
from pathlib import Path

import requests

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
from childsight.clients import ISO3_TO_M49, UNICEF_SDMX  # noqa: E402

OUT = SRC / "childsight" / "data" / "ccri_all.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers["User-Agent"] = "childsight-mcp/0.1 (UN Hackathon 2026, bundle build)"


def fetch(url: str, timeout: float = 60.0, tries: int = 3) -> str | None:
    for i in range(tries):
        try:
            r = session.get(url, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:  # noqa: BLE001
            print(f"    attempt {i + 1}/{tries} failed: {e}")
            time.sleep(2 * (i + 1))
    return None


def main() -> None:
    # Resume support: skip countries already in the bundle from earlier runs
    done: set[str] = set()
    existing_rows: list[dict] = []
    header: list[str] | None = None
    if OUT.exists():
        with OUT.open() as f:
            for row in csv.DictReader(f):
                existing_rows.append(row)
                done.add(row["REF_AREA"].strip().upper())
        if existing_rows:
            header = list(existing_rows[0].keys())
        print(f"Resuming: {len(done)} countries already bundled.")

    if not done:
        # Try the bulk query first (one request, all countries; 'all' is SDMX syntax)
        print("Trying bulk CCRI download (all countries, one request)...")
        bulk = fetch(f"{UNICEF_SDMX}/data/UNICEF,CCRI,1.0/all?format=csv&lastNObservations=1", timeout=180)
        if bulk and bulk.count("\n") > 1000:
            OUT.write_text(bulk)
            print(f"Bulk download OK — {bulk.count(chr(10))} rows -> {OUT}")
            return
        print("Bulk failed or too small; fetching per country (resumable — rerun anytime)...")

    all_rows = existing_rows
    failed: list[str] = []
    todo = [c for c in sorted(ISO3_TO_M49) if c not in done]
    for i, iso3 in enumerate(todo):
        print(f"  [{i + 1}/{len(todo)}] {iso3}")
        text = fetch(f"{UNICEF_SDMX}/data/UNICEF,CCRI,1.0/{iso3}.?format=csv&lastNObservations=1", timeout=45, tries=2)
        if not text:
            failed.append(iso3)
            continue
        rows = list(csv.DictReader(io.StringIO(text)))
        if rows and header is None:
            header = list(rows[0].keys())
        all_rows.extend(rows)
        # Write incrementally so progress survives interruption
        if header:
            with OUT.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=header)
                w.writeheader()
                w.writerows(all_rows)
        time.sleep(0.4)  # be polite, avoid throttling

    if not all_rows:
        print("ERROR: no data retrieved at all — the SDMX service is likely down. Rerun later; progress resumes.")
        sys.exit(1)

    print(f"\nBundle: {len(all_rows)} rows, {len({r['REF_AREA'] for r in all_rows})} countries -> {OUT}")
    if failed:
        print(f"Missing ({len(failed)}): {', '.join(failed)}")
        print("Rerun this script to retry just the missing ones (resume is automatic).")
    print("\nCommit the bundle: git add src/childsight/data/ccri_all.csv")


if __name__ == "__main__":
    main()
