import pandas as pd
import numpy as np
import os
import json
import hashlib
import random
import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_MODELS = PROJECT_ROOT / "data" / "models"
DATA_TRAINING = PROJECT_ROOT / "outputs" / "training_data"
OUTPUTS_REPORTS = PROJECT_ROOT / "outputs" / "reports"
OUTPUTS_CHARTS = PROJECT_ROOT / "outputs" / "charts"
DB_PATH = PROJECT_ROOT / "data" / "processed" / "atm_data.db"
ECOSYSTEM_DB = PROJECT_ROOT / "data" / "processed" / "ecosystem.db"

BANK_TYPE_MAP = {
    "BANK OF BARODA": "PSU", "BANK OF INDIA": "PSU", "BANK OF MAHARASHTRA": "PSU",
    "CANARA BANK": "PSU", "CENTRAL BANK OF INDIA": "PSU", "INDIAN BANK": "PSU",
    "INDIAN OVERSEAS BANK": "PSU", "PUNJAB AND SIND BANK": "PSU",
    "PUNJAB NATIONAL BANK": "PSU", "STATE BANK OF INDIA": "PSU", "UCO BANK": "PSU",
    "UNION BANK OF INDIA": "PSU",
    "AXIS BANK LTD": "PVT", "BANDHAN BANK LTD": "PVT", "CITY UNION BANK LTD.": "PVT",
    "CSB BANK LTD.": "PVT", "DCB BANK LTD": "PVT", "DHANALAXMI BANK LTD": "PVT",
    "FEDERAL BANK LTD": "PVT", "HDFC BANK LTD": "PVT", "ICICI BANK LTD": "PVT",
    "IDBI BANK LTD": "PVT", "IDFC FIRST BANK LTD": "PVT", "INDUSIND BANK LTD": "PVT",
    "JAMMU AND KASHMIR BANK LTD": "PVT", "KARNATAKA BANK LTD": "PVT",
    "KARUR VYSYA BANK LTD": "PVT", "KOTAK MAHINDRA BANK LTD": "PVT",
    "NAINITAL BANK LTD": "PVT", "RBL BANK LTD": "PVT", "SOUTH INDIAN BANK": "PVT",
    "TAMILNAD MERCANTILE BANK LTD": "PVT", "YES BANK LTD": "PVT",
    "AMERICAN EXPRESS BANKING CORPORATION": "FOREIGN", "BANK OF AMERICA": "FOREIGN",
    "BANK OF BAHRAIN & KUWAIT B.S.C.": "FOREIGN", "BARCLAYS BANK PLC": "FOREIGN",
    "CITI BANK": "FOREIGN", "DBS INDIA BANK LTD": "FOREIGN",
    "DEUTSCHE BANK LTD": "FOREIGN", "DOHA BANK Q.P.S.C.": "FOREIGN",
    "HSBC LTD": "FOREIGN", "KEB HANA BANK": "FOREIGN", "KOOKMIN BANK": "FOREIGN",
    "SBM BANK INDIA LTD": "FOREIGN", "STANDARD CHARTERED BANK LTD": "FOREIGN",
    "WOORI BANK": "FOREIGN",
    "AIRTEL PAYMENTS BANK": "PAYMENTS", "FINO PAYMENTS BANK": "PAYMENTS",
    "INDIA POST PAYMENTS BANK": "PAYMENTS", "JIO PAYMENTS BANK ": "PAYMENTS",
    "NSDL PAYMENTS BANK": "PAYMENTS", "PAYTM PAYMENTS BANK": "PAYMENTS",
    "AU SMALL FINANCE BANK LTD": "SFB", "CAPITAL SMALL FINANCE BANK LTD": "SFB",
    "EQUITAS SMALL FINANCE BANK LTD": "SFB", "ESAF SMALL FINANCE BANK LTD": "SFB",
    "JANA SMALL FINANCE BANK LTD": "SFB", "NORTH EAST SMALL FINANCE BANK LTD": "SFB",
    "SHIVALIK SMALL FINANCE BANK LTD": "SFB", "SLICE SMALL FINANCE BANK LTD": "SFB",
    "SURYODAY SMALL FINANCE BANK LTD": "SFB", "UJJIVAN SMALL FINANCE BANK LTD": "SFB",
    "UNITY SMALL FINANCE BANK LTD": "SFB", "UTKARSH SMALL FINANCE BANK LTD": "SFB",
}

MONTH_ORDER = ["April", "May", "June", "July", "August", "September",
               "October", "November", "December", "January"]

BANK_ALIASES = {
    "SBI": "STATE BANK OF INDIA", "BOB": "BANK OF BARODA",
    "PNB": "PUNJAB NATIONAL BANK", "BOI": "BANK OF INDIA",
    "CANARA": "CANARA BANK", "UBI": "UNION BANK OF INDIA",
    "HDFC": "HDFC BANK LTD", "ICICI": "ICICI BANK LTD",
    "AXIS": "AXIS BANK LTD", "KOTAK": "KOTAK MAHINDRA BANK LTD",
    "YES": "YES BANK LTD", "FEDERAL": "FEDERAL BANK LTD",
    "INDUSIND": "INDUSIND BANK LTD", "IDFC": "IDFC FIRST BANK LTD",
    "RBL": "RBL BANK LTD", "BANDHAN": "BANDHAN BANK LTD",
    "SBIN": "STATE BANK OF INDIA", "IDBI": "IDBI BANK LTD",
    "IOB": "INDIAN OVERSEAS BANK", "CBI": "CENTRAL BANK OF INDIA",
    "UCO": "UCO BANK", "PSB": "PUNJAB AND SIND BANK",
    "BOM": "BANK OF MAHARASHTRA", "SIB": "SOUTH INDIAN BANK",
    "KVB": "KARUR VYSYA BANK LTD", "KBL": "KARNATAKA BANK LTD",
    "JKB": "JAMMU AND KASHMIR BANK LTD", "CUB": "CITY UNION BANK LTD.",
    "DCB": "DCB BANK LTD", "CSB": "CSB BANK LTD.",
    "TMB": "TAMILNAD MERCANTILE BANK LTD", "CITI": "CITI BANK",
    "HSBC": "HSBC LTD", "SC": "STANDARD CHARTERED BANK LTD",
    "DBS": "DBS INDIA BANK LTD", "DEUTSCHE": "DEUTSCHE BANK LTD",
    "BARCLAYS": "BARCLAYS BANK PLC", "BOA": "BANK OF AMERICA",
    "AMEX": "AMERICAN EXPRESS BANKING CORPORATION",
    "AXP": "AMERICAN EXPRESS BANKING CORPORATION",
    "PAYTM": "PAYTM PAYMENTS BANK", "AIRTEL": "AIRTEL PAYMENTS BANK",
    "JIO": "JIO PAYMENTS BANK ", "NSDL": "NSDL PAYMENTS BANK",
    "FINO": "FINO PAYMENTS BANK", "IPPB": "INDIA POST PAYMENTS BANK",
    "AU": "AU SMALL FINANCE BANK LTD", "EQUITAS": "EQUITAS SMALL FINANCE BANK LTD",
    "UJJIVAN": "UJJIVAN SMALL FINANCE BANK LTD",
    "UTKARSH": "UTKARSH SMALL FINANCE BANK LTD",
    "SURYODAY": "SURYODAY SMALL FINANCE BANK LTD",
    "SLICE": "SLICE SMALL FINANCE BANK LTD",
    "JANA": "JANA SMALL FINANCE BANK LTD",
    "ESAF": "ESAF SMALL FINANCE BANK LTD",
    "SHIVALIK": "SHIVALIK SMALL FINANCE BANK LTD",
    "UNITY": "UNITY SMALL FINANCE BANK LTD",
    "NESFB": "NORTH EAST SMALL FINANCE BANK LTD",
    "KOTAK MAHINDRA": "KOTAK MAHINDRA BANK LTD",
    "HDF": "HDFC BANK LTD",
}

AGE_GROUPS = {
    (10, 13): ("Child", True),
    (14, 17): ("Teen", True),
    (18, 25): ("Young Adult", False),
    (26, 40): ("Adult", False),
    (41, 60): ("Middle-aged", False),
    (61, 120): ("Senior", False),
}

def get_age_group(age):
    for (lo, hi), (label, is_minor) in AGE_GROUPS.items():
        if lo <= age <= hi:
            return label, is_minor
    return ("Unknown", False)

def get_bank_type(bank_name):
    return BANK_TYPE_MAP.get(bank_name.strip().upper(), "OTHER")

def resolve_bank_alias(text):
    t = text.strip().upper()
    if t in BANK_ALIASES:
        return BANK_ALIASES[t]
    return text

def hash_pin(pin):
    return hashlib.sha256(str(pin).encode()).hexdigest()

def ensure_dirs():
    for d in [DATA_RAW, DATA_PROCESSED, DATA_MODELS, OUTPUTS_REPORTS, OUTPUTS_CHARTS, DATA_TRAINING]:
        d.mkdir(parents=True, exist_ok=True)

def month_to_num(month_str):
    mapping = {
        "april": 4, "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12, "january": 1
    }
    return mapping.get(month_str.strip().lower(), 0)

def safe_float(val):
    try:
        f = float(str(val).replace(",", ""))
        return f if not np.isnan(f) else 0.0
    except:
        return 0.0

def safe_int(val):
    return int(safe_float(val))

def format_currency(val):
    if abs(val) >= 1_00_00_000:
        return f"₹{val/1_00_00_000:.2f}Cr"
    elif abs(val) >= 1_000:
        return f"₹{val/1_000:.2f}K"
    return f"₹{val:.2f}"

def format_number(val):
    if abs(val) >= 1_00_00_000:
        return f"{val/1_00_00_000:.2f}Cr"
    elif abs(val) >= 1_000:
        return f"{val/1_000:.2f}K"
    return f"{val:.0f}"

def validate_name(name):
    if not name or len(name.strip()) < 3:
        return False, "Name must be at least 3 characters"
    parts = name.strip().split()
    if len(parts) < 2:
        return False, "Full name required (first and last)"
    if not all(re.match(r"^[A-Za-z.\-']+$", p) for p in parts):
        return False, "Name can only contain letters, dots, hyphens"
    return True, name.strip().title()

def validate_phone(phone):
    digits = re.sub(r"\D", "", phone)
    if len(digits) != 10:
        return False, "Phone must be 10 digits"
    if digits[0] not in "6789":
        return False, "Phone must start with 6, 7, 8, or 9"
    return True, digits

def validate_email(email):
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email.strip()):
        return False, "Invalid email format"
    return True, email.strip().lower()

def validate_age(age):
    try:
        a = int(age)
        if a < 10:
            return False, "Minimum age is 10"
        if a > 120:
            return False, "Maximum age is 120"
        return True, a
    except:
        return False, "Age must be a number"

def generate_account_no(bank_prefix):
    suffix = str(random.randint(1000, 99999))
    return f"{bank_prefix}{suffix}"

def generate_card_no():
    return f"{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"

def calculate_cash_denominations(amount):
    notes = {}
    for denom in [500, 200, 100]:
        count = amount // denom
        if count > 0:
            notes[denom] = count
            amount -= count * denom
    return notes

def format_denominations(notes):
    parts = [f"₹{d} × {c}" for d, c in sorted(notes.items(), reverse=True)]
    return " + ".join(parts)

def income_bracket_options():
    return [
        ("not_earning_student", "Not Earning — Student"),
        ("not_earning_homemaker", "Not Earning — Homemaker"),
        ("not_earning_unemployed", "Not Earning — Unemployed"),
        ("not_earning_retired", "Not Earning — Retired"),
        ("earning_under_2.5L", "Earning — Below ₹2.5L/yr"),
        ("earning_2.5L_5L", "Earning — ₹2.5L to ₹5L/yr"),
        ("earning_5L_10L", "Earning — ₹5L to ₹10L/yr"),
        ("earning_10L_25L", "Earning — ₹10L to ₹25L/yr"),
        ("earning_25L_plus", "Earning — Above ₹25L/yr"),
    ]

def get_scenario_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")
