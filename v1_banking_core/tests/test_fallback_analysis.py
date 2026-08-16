"""Regression: compare_banks / bank_overview / channel_breakdown must work even on
fallback (no CSV / no DB) data — the 6 detail columns used to be missing there."""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from banking_core.data_analysis import DataAnalysis


def test_fallback_compare_banks():
    da = DataAnalysis()
    da._build_fallback_data()
    res = da.compare_banks(["STATE BANK OF INDIA", "HDFC BANK LTD"])
    cols = set(res.columns)
    for want in ["ATMs_On_Site", "ATMs_Off_Site", "PoS", "Micro_ATMs",
                 "Credit_Cards_Outstanding", "Debit_Cards_Outstanding",
                 "Total_ATMs", "Total_Cards", "Total_Txn_Vol"]:
        assert want in cols, f"missing {want} in compare output"
    assert len(res) == 2


def test_fallback_bank_overview():
    da = DataAnalysis()
    da._build_fallback_data()
    ov = da.bank_overview("STATE BANK OF INDIA")
    assert "ATMs On-Site" in ov and "PoS Terminals" in ov and "Micro ATMs" in ov


def test_fallback_channel_breakdown():
    da = DataAnalysis()
    da._build_fallback_data()
    ch = da.channel_breakdown("STATE BANK OF INDIA")
    assert len(ch) == 6
    assert all("Vol" in v and "Val" in v for v in ch.values())
