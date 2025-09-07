#!/usr/bin/env python3
"""
Spyder-friendly script to seed MockAPI.io with FAQ data from a CSV.

Fixes NaN -> None so JSON encoding works.
Adds basic validation & logging.
"""

import time
import sys
import pandas as pd
import requests

# ===== CONFIG (edit as needed) =====
CSV_FILE = "utas_faq_agent_QA.csv"   # put the CSV in the same folder as this script
BASE_URL = "https://68b84cdbb71540504327cbc4.mockapi.io/api/v1"
RESOURCE = "faqs"
SLEEP = 0.35   # seconds between POSTs (avoid rate limit)
DRY_RUN = False  # True = print payloads but don't POST
# ===================================

def to_none_if_nan(x):
    """Convert pandas NaN to None, leave others as-is."""
    if pd.isna(x):
        return None
    return x

def to_str_or_none(x):
    """Prefer string for text fields; None if NaN/empty after strip."""
    if pd.isna(x):
        return None
    s = str(x).strip()
    return s if s != "" else None

def main():
    # Load CSV
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        print(f"❌ CSV file not found: {CSV_FILE}")
        sys.exit(1)

    required = {"intent", "question", "answer"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        print(f"❌ CSV missing required columns: {missing}")
        sys.exit(1)

    # Normalize: replace NaN with None across the DataFrame
    df = df.where(pd.notnull(df), None)

    url = f"{BASE_URL.rstrip('/')}/{RESOURCE}"
    ok, fail = 0, 0

    for i, row in df.iterrows():
        # Build clean payload (strings for text fields; None for missing)
        payload = {
            "intent": to_str_or_none(row.get("intent")),
            "question": to_str_or_none(row.get("question")),
            "answer": to_str_or_none(row.get("answer")),
            "filename": to_str_or_none(row.get("filename")),
            "link": to_str_or_none(row.get("link")),
            "topic": to_str_or_none(row.get("topic")),
            "course_code": to_str_or_none(row.get("course_code")),
            "course_name": to_str_or_none(row.get("course_name")),
        }

        # Validate required fields
        if not payload["intent"] or not payload["question"] or not payload["answer"]:
            fail += 1
            print(f"[SKIP row {i}] Missing required fields → {payload}")
            continue

        # Optional: show what we'll send
        print(f"[{i}] POST → {url} | intent={payload['intent']}")

        if DRY_RUN:
            ok += 1
            continue

        try:
            r = requests.post(url, json=payload, timeout=20)
            if r.status_code in (200, 201):
                ok += 1
                rid = r.json().get("id")
                print(f"   ✅ Created id={rid}")
            else:
                fail += 1
                print(f"   [ERR] {r.status_code} {r.text}")
        except Exception as e:
            fail += 1
            print(f"   [EXC] {e}")

        time.sleep(SLEEP)

    print(f"\n🎉 Done. Created={ok}, Failed/Skipped={fail}")

if __name__ == "__main__":
    main()
