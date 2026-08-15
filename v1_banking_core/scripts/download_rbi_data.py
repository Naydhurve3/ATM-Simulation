"""Download real RBI / NPCI / bank data for validation.

Fetches:
  1. RBI ATM & Card statistics (CSV)  -> data/raw/RBI_ATM_Card_Statistics_<date>.csv
  2. NPCI UPI product statistics (HTML table) -> data/raw/npci_upi_stats_<date>.html
  3. SBI interest rate page (HTML)    -> data/raw/sbi_interest_rates_<date>.html
  4. RBI Weekly Statistical Supplement -> data/raw/rbi_wss_<date>.html

Writes a sources.json manifest with URL, fetch time and status.

Usage:
    python v1_banking_core/scripts/download_rbi_data.py
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

SOURCES = {
    "rbi_atm_cards": {
        "url": "https://www.rbi.org.in/Scripts/ATMView.aspx",
        "accept": "xlsx",
        "follow": "rbidocs.rbi.org.in/rdocs/ATM/DOCs/ATM",
    },
    "npci_upi_stats": {
        "url": "https://www.npci.org.in/product/upi/product-statistics",
        "accept": "html",
    },
    "sbi_interest_rates": {
        "url": "https://sbi.co.in/web/interest-rates/interest-rates",
        "accept": "html",
    },
    "rbi_wss": {
        "url": "https://www.rbi.org.in/Scripts/WSSView.aspx",
        "accept": "html",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-validator/1.0",
    "Accept-Language": "en-IN,en;q=0.9",
}


def fetch(url: str, timeout: int = 60) -> bytes:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_rbi_xlsx(cfg: dict, timeout: int = 60) -> tuple:
    """RBI ATMView is an ASP.NET page; the real dataset is a linked XLSX on rbidocs.

    Note: rbidocs links sit behind an anti-bot JS challenge (Imperva TSPD) — direct
    scripted downloads are usually blocked. On failure this returns the direct link
    so the user can grab it in a browser; `manifest["direct_url"]` will carry it.
    """
    page = fetch(cfg["url"], timeout).decode("utf-8", "replace")
    m = re.search(r"href=['\"](https://rbidocs\.rbi\.org\.in[^'\"]*ATM[^'\"]*\.XLSX)['\"]", page, re.I)
    if not m:
        raise RuntimeError("no ATM XLSX link found on ATMView.aspx")
    payload = fetch(m.group(1), timeout)
    if payload[:9] == b"<!DOCTYPE":  # challenge page, not the workbook
        raise RuntimeError(f"rbidocs blocked the download (anti-bot). Direct URL: {m.group(1)}")
    return payload, m.group(1)


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    manifest = []

    for key, cfg in SOURCES.items():
        status = "error"
        path = None
        try:
            if key == "rbi_atm_cards":
                payload, src_url = fetch_rbi_xlsx(cfg)
                cfg = {**cfg, "url": src_url}
            else:
                payload = fetch(cfg["url"])
            ext = cfg["accept"]
            path = DATA_DIR / f"{key}_{stamp}.{ext}"
            path.write_bytes(payload)
            status = "ok" if len(payload) > 1000 else "too_small"
            print(f"[{status}] {key}: {len(payload)} bytes -> {path.name}")
        except Exception as exc:  # network/parse issues must not block other sources
            print(f"[error] {key}: {exc}")
            path = None
            if key == "rbi_atm_cards":
                m = re.search(r"Direct URL: (\S+)", str(exc))
                cfg = {**cfg, "direct_url": m.group(1) if m else None}
        manifest.append({
            "key": key,
            "url": cfg["url"],
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "status": status,
            "file": str(path) if path else None,
            "direct_url": cfg.get("direct_url") if key == "rbi_atm_cards" else None,
        })

    (DATA_DIR / f"sources_{stamp}.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("manifest ->", DATA_DIR / f"sources_{stamp}.json")
    return 0 if all(m["status"] == "ok" for m in manifest) else 1


if __name__ == "__main__":
    sys.exit(main())
