# update.py  (FIXED: multi-brand sheets + safe scheduler + Railway-ready)
import os
import json
import time
import traceback
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

import gspread
from oauth2client.service_account import ServiceAccountCredentials


# =========================================================
# ENV CONFIG (Railway Variables)
# =========================================================
# Single-sheet fallback (ONLY used if BRAND_SHEETS is empty)
# IMPORTANT: SPREADSHEET_ID must be GOOGLE SHEET KEY (not Apps Script URL)
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "").strip()
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "Sheet1").strip()

# Multi-brand sheets (preferred)
# Format:
#   brand:SPREADSHEET_KEY:WORKSHEET_TAB,brand2:KEY2:TAB2
BRAND_SHEETS = os.getenv("BRAND_SHEETS", "").strip()

# Service Account JSON (either file path or raw JSON string)
GOOGLE_SA_JSON_PATH = os.getenv("GOOGLE_SA_JSON_PATH", "").strip()
GOOGLE_SA_JSON = os.getenv("GOOGLE_SA_JSON", "").strip()

# Poll interval
POLL_MINUTES = int(os.getenv("POLL_MINUTES", "30").strip())

# ElevenLabs
XI_API_KEY = os.getenv("XI_API_KEY", "").strip()  # required for transcript fetch
ELEVEN_CONV_BASE_URL = os.getenv(
    "ELEVEN_CONV_BASE_URL",
    "https://api.elevenlabs.io/v1/convai/conversations"
).strip()

# Injection targets
INJECT_MODE = os.getenv("INJECT_MODE", "test").strip().lower()
# INJECT_MODE = "test" | "client" | "both" | "off"

# Your test API (you said working)
TEST_API_URL = os.getenv("TEST_API_URL", "http://115.243.144.114:5000/api/voice-lead").strip()

# Client API
CFO_API_URL = os.getenv("CFO_API_URL", "https://cfobackend.apps.magentic.in/api/voice-lead").strip()
CFO_API_SECRET = os.getenv("CFO_API_SECRET", "").strip()

# Optional: don’t actually POST, just update sheet statuses
DRY_RUN = os.getenv("DRY_RUN", "0").strip() == "1"

# Limits per run (avoid huge scan)
MAX_ROWS_PER_RUN = int(os.getenv("MAX_ROWS_PER_RUN", "200").strip())


# =========================================================
# BRAND SHEETS PARSER
# =========================================================
def parse_brand_sheets():
    """
    Returns list of (brand, spreadsheet_key, worksheet_name).
    If BRAND_SHEETS is empty, falls back to SPREADSHEET_ID + WORKSHEET_NAME.
    """
    items = []

    if BRAND_SHEETS:
        for part in BRAND_SHEETS.split(","):
            part = part.strip()
            if not part:
                continue
            bits = part.split(":")
            if len(bits) != 3:
                raise RuntimeError(
                    f"Invalid BRAND_SHEETS entry: '{part}'. Expected brand:key:worksheet"
                )
            brand, key, ws = bits
            items.append((brand.strip(), key.strip(), ws.strip()))
        return items

    # fallback
    if SPREADSHEET_ID:
        items.append(("default", SPREADSHEET_ID, WORKSHEET_NAME))
    return items


# =========================================================
# Helpers
# =========================================================
def _now_iso():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def seconds_to_hhmmss(seconds: int) -> str:
    if seconds is None:
        return ""
    seconds = int(max(0, seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def safe_get(d, *path, default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
        if cur is None:
            return default
    return cur


# =========================================================
# Google Sheets client
# =========================================================
def get_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    if GOOGLE_SA_JSON_PATH:
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SA_JSON_PATH, scope)
        return gspread.authorize(creds)

    if GOOGLE_SA_JSON:
        sa_dict = json.loads(GOOGLE_SA_JSON)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(sa_dict, scope)
        return gspread.authorize(creds)

    raise RuntimeError("Missing GOOGLE_SA_JSON_PATH or GOOGLE_SA_JSON env var")


def open_sheet(spreadsheet_id: str, worksheet_name: str):
    gc = get_gspread_client()
    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet(worksheet_name)
    return ws


# =========================================================
# ElevenLabs fetch
# =========================================================
def fetch_conversation(conv_id: str) -> dict:
    if not XI_API_KEY:
        raise RuntimeError("XI_API_KEY not set")

    headers = {"xi-api-key": XI_API_KEY, "Accept": "application/json"}
    url = f"{ELEVEN_CONV_BASE_URL}/{conv_id}"
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code == 404:
        return {"__not_found__": True}
    r.raise_for_status()
    return r.json()


def extract_duration_and_transcript(conv_json: dict):
    dur = (
        safe_get(conv_json, "metadata", "call_duration_secs")
        or safe_get(conv_json, "conversation_initiation_client_data", "dynamic_variables", "system__call_duration_secs")
    )

    transcript_items = conv_json.get("transcript", []) or []
    lines = []
    for t in transcript_items:
        role = (t.get("role") or "UNKNOWN").upper()
        msg = (t.get("message") or "").strip()
        if msg:
            lines.append(f"{role}: {msg}")
    transcript_text = "\n".join(lines).strip()

    try:
        dur_int = int(float(dur)) if dur is not None and str(dur).strip() != "" else None
    except Exception:
        dur_int = None

    return dur_int, transcript_text


# =========================================================
# Injection (test / client)
# =========================================================
def post_json(url: str, payload: dict, headers: dict | None = None):
    if DRY_RUN:
        return {"dry_run": True, "url": url}

    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)

    r = requests.post(url, headers=h, json=payload, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    try:
        return r.json()
    except Exception:
        return {"raw": r.text}


def inject_to_test(row_obj: dict):
    payload = {
        "name": row_obj.get("Name", ""),
        "companyName": row_obj.get("Company", ""),
        "mobile": row_obj.get("Phone", ""),
        "email": row_obj.get("Email", ""),
        "transcript": row_obj.get("Transcript", ""),
        "callDuration": row_obj.get("CallDurationHHMMSS", ""),
    }
    return post_json(TEST_API_URL, payload)


def inject_to_client(row_obj: dict):
    if not CFO_API_SECRET:
        raise RuntimeError("CFO_API_SECRET not set")
    payload = {
        "name": row_obj.get("Name", ""),
        "companyName": row_obj.get("Company", ""),
        "mobile": row_obj.get("Phone", ""),
        "email": row_obj.get("Email", ""),
        "transcript": row_obj.get("Transcript", ""),
        "callDuration": row_obj.get("CallDurationHHMMSS", ""),
    }
    return post_json(CFO_API_URL, payload, headers={"x-api-secret": CFO_API_SECRET})


# =========================================================
# Main poll logic (per sheet)
# =========================================================
def run_sheet_cycle_for(spreadsheet_id: str, worksheet_name: str, brand: str):
    try:
        ws = open_sheet(spreadsheet_id, worksheet_name)
        values = ws.get_all_values()
        if not values or len(values) < 2:
            print(f"[update.py] brand={brand} Sheet empty or only header.")
            return

        header = values[0]
        rows = values[1:]
        idx = {h.strip(): i for i, h in enumerate(header)}

        needed_cols = [
            "Conversation ID",
            "Transcript",
            "Call Duration (secs)",
            "transcript updated",
            "DB_injected",
            "Name",
            "Email",
            "Phone",
            "Company",
        ]
        for c in needed_cols:
            if c not in idx:
                print(f"[update.py] brand={brand} Missing header column: {c}")
                return

        processed = 0

        for i in range(len(rows) - 1, -1, -1):
            if processed >= MAX_ROWS_PER_RUN:
                break

            sheet_row_num = i + 2
            row = rows[i]

            conv_id = row[idx["Conversation ID"]].strip()
            transcript = row[idx["Transcript"]].strip()
            transcript_status = row[idx["transcript updated"]].strip().upper() or "PENDING"
            db_status = row[idx["DB_injected"]].strip().upper() or "PENDING"

            if not conv_id:
                if transcript_status not in ("NO_CONV_ID", "UPDATED"):
                    ws.update_cell(sheet_row_num, idx["transcript updated"] + 1, "NO_CONV_ID")
                continue

            # Step A: fetch transcript
            if transcript_status != "UPDATED":
                try:
                    conv_json = fetch_conversation(conv_id)
                    if conv_json.get("__not_found__"):
                        ws.update_cell(sheet_row_num, idx["transcript updated"] + 1, "NOT_FOUND")
                        continue

                    dur_secs, transcript_text = extract_duration_and_transcript(conv_json)

                    if not transcript_text:
                        ws.update_cell(sheet_row_num, idx["transcript updated"] + 1, "ERROR_EMPTY_TRANSCRIPT")
                        continue

                    if dur_secs is not None:
                        ws.update_cell(sheet_row_num, idx["Call Duration (secs)"] + 1, str(dur_secs))
                    ws.update_cell(sheet_row_num, idx["Transcript"] + 1, transcript_text)
                    ws.update_cell(sheet_row_num, idx["transcript updated"] + 1, "UPDATED")

                    transcript = transcript_text
                    transcript_status = "UPDATED"

                except Exception as e:
                    print(f"[update.py] brand={brand} Transcript fetch error row={sheet_row_num} conv={conv_id}: {e}")
                    ws.update_cell(sheet_row_num, idx["transcript updated"] + 1, "ERROR")
                    continue

            # Step B: inject
            if transcript_status == "UPDATED" and db_status != "SENT":
                try:
                    name = row[idx["Name"]].strip()
                    email = row[idx["Email"]].strip()
                    phone = row[idx["Phone"]].strip()
                    company = row[idx["Company"]].strip()

                    dur_secs_cell = row[idx["Call Duration (secs)"]].strip()
                    try:
                        dur_secs_int = int(float(dur_secs_cell)) if dur_secs_cell else 0
                    except Exception:
                        dur_secs_int = 0

                    row_obj = {
                        "Name": name,
                        "Email": email,
                        "Phone": phone,
                        "Company": company,
                        "Transcript": transcript,
                        "CallDurationHHMMSS": seconds_to_hhmmss(dur_secs_int),
                    }

                    if not (name and (email or phone) and transcript):
                        ws.update_cell(sheet_row_num, idx["DB_injected"] + 1, "SKIPPED_MISSING_FIELDS")
                        continue

                    if INJECT_MODE == "off":
                        ws.update_cell(sheet_row_num, idx["DB_injected"] + 1, "READY")
                        continue

                    if INJECT_MODE in ("test", "both"):
                        inject_to_test(row_obj)

                    if INJECT_MODE in ("client", "both"):
                        inject_to_client(row_obj)

                    ws.update_cell(sheet_row_num, idx["DB_injected"] + 1, "SENT")

                except Exception as e:
                    print(f"[update.py] brand={brand} Inject error row={sheet_row_num} conv={conv_id}: {e}")
                    ws.update_cell(sheet_row_num, idx["DB_injected"] + 1, "ERROR")
                    continue

            processed += 1

        print(f"[update.py] brand={brand} Cycle complete. processed={processed} at {_now_iso()}")

    except Exception:
        print(f"[update.py] brand={brand} Fatal cycle error:\n{traceback.format_exc()}")


# =========================================================
# Run all brands wrapper
# =========================================================
def run_all_brands_cycle():
    sheets = parse_brand_sheets()
    if not sheets:
        print("[update.py] No sheets configured. Set BRAND_SHEETS or SPREADSHEET_ID.")
        return

    for brand, key, wsname in sheets:
        try:
            print(f"[update.py] ▶ brand={brand} | sheet={key} | tab={wsname}")
            run_sheet_cycle_for(key, wsname, brand)
        except Exception as e:
            print(f"[update.py] ❌ brand={brand} failed: {e}")
            print(traceback.format_exc())


# =========================================================
# Scheduler start
# =========================================================
_scheduler = None

def start_sheet_poller():
    global _scheduler
    if _scheduler:
        return _scheduler

    sheets = parse_brand_sheets()
    if not sheets:
        raise RuntimeError("No sheets configured. Use BRAND_SHEETS or SPREADSHEET_ID")

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        run_all_brands_cycle,
        "interval",
        minutes=POLL_MINUTES,
        next_run_time=datetime.now()
    )
    _scheduler.start()

    print(f"[update.py] Sheet poller started: every {POLL_MINUTES} minutes | sheets={len(sheets)} | mode={INJECT_MODE} | dry_run={DRY_RUN}")
    return _scheduler


# -------------------------
# Backward-compatible alias
# -------------------------
def start_transcript_poller():
    return start_sheet_poller()


# Optional standalone run (local debug)
if __name__ == "__main__":
    run_all_brands_cycle()
    start_sheet_poller()
    while True:
        time.sleep(60)
