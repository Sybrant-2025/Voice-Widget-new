import os
import time
import json
import requests
import threading
from datetime import datetime

# ======================
# CONFIG (ENV)
# ======================
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY", "").strip()

# Use ONLY ONE sheet webapp (your listed sheet)
# Example: newcfobridge script URL
SHEET_WEBAPP_URL = os.getenv("SHEET_WEBAPP_URL", "https://script.google.com/macros/s/AKfycbwJFIK9NJ4-nkNcozftSVbZX-EJ2hLuoOWF3n87sWu2Qh3dsENrNAl_44o-rd4-DK7qjQ/exec").strip()

# CFO backend injection
# CFO_API_URL = os.getenv("CFO_API_URL", "https://cfobackend.apps.magentic.in/api/voice-lead").strip()
# CFO_API_SECRET = os.getenv("CFO_API_SECRET", "").strip()

# Worker behavior
POLL_EVERY_SECONDS = int(os.getenv("TRANSCRIPT_POLL_SECONDS", "1800"))  # 30 min
BATCH_LIMIT = int(os.getenv("TRANSCRIPT_BATCH_LIMIT", "30"))           # per cycle
START_ROW = int(os.getenv("TRANSCRIPT_START_ROW", "2"))                # skip header

# ElevenLabs conversations endpoint
ELEVEN_CONV_URL = "https://api.elevenlabs.io/v1/convai/conversations"


# ======================
# Helpers
# ======================
def _secs_to_hhmmss(seconds: int) -> str:
    seconds = int(seconds or 0)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def _fetch_conversation(conv_id: str) -> dict:
    if not ELEVEN_API_KEY:
        raise RuntimeError("ELEVEN_API_KEY env missing")

    headers = {"xi-api-key": ELEVEN_API_KEY, "Accept": "application/json"}
    r = requests.get(f"{ELEVEN_CONV_URL}/{conv_id}", headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def _extract_duration_and_transcript(data: dict) -> tuple[int, str]:
    # duration (secs)
    dur = (
        data.get("metadata", {}).get("call_duration_secs")
        or data.get("conversation_initiation_client_data", {})
              .get("dynamic_variables", {})
              .get("system__call_duration_secs")
        or 0
    )

    # transcript (role/message)
    lines = []
    for t in data.get("transcript", []) or []:
        role = (t.get("role") or "UNKNOWN").upper()
        msg = (t.get("message") or "").strip()
        if msg:
            lines.append(f"{role}: {msg}")
    transcript_text = "\n".join(lines).strip()

    return int(dur or 0), transcript_text


def _sheet_get_pending() -> list[dict]:
    if not SHEET_WEBAPP_URL:
        raise RuntimeError("SHEET_WEBAPP_URL env missing")

    payload = {
        "action": "get_pending",
        "startRow": START_ROW,
        "limit": BATCH_LIMIT
    }
    r = requests.post(SHEET_WEBAPP_URL, json=payload, timeout=30)
    r.raise_for_status()
    out = r.json()
    return out.get("rows", []) or []


def _sheet_update_fields(row_number: int, **fields) -> None:
    payload = {"action": "update_fields", "rowNumber": row_number}
    payload.update(fields)
    r = requests.post(SHEET_WEBAPP_URL, json=payload, timeout=30)
    r.raise_for_status()


def _inject_to_cfo_backend(name: str, company: str, mobile: str, email: str, transcript: str, duration_secs: int) -> None:
    if not CFO_API_SECRET:
        raise RuntimeError("CFO_API_SECRET env missing")

    # CFO requires callDuration string
    call_duration = _secs_to_hhmmss(duration_secs)

    headers = {
        "Content-Type": "application/json",
        "x-api-secret": CFO_API_SECRET
    }
    payload = {
        "name": name or "",
        "companyName": company or "",
        "mobile": mobile or "",
        "email": email or "",
        "transcript": transcript or "",
        "callDuration": call_duration
    }
    r = requests.post(CFO_API_URL, headers=headers, json=payload, timeout=30)
    r.raise_for_status()


# ======================
# Main worker
# ======================
def run_transcript_cycle():
    """
    1) get pending rows
    2) for each row: fetch ElevenLabs conversation, update sheet transcript+duration+status
    3) inject to CFO backend, update DB_injected status
    """
    pending = _sheet_get_pending()

    for item in pending:
        row_num = int(item.get("rowNumber", 0))
        conv_id = (item.get("conversation_id") or "").strip()

        if not row_num:
            continue

        # If no conversation_id => mark and skip
        if not conv_id:
            _sheet_update_fields(
                row_num,
                transcript_updated="SKIP_NO_CONV_ID",
                db_injected="SKIP_NO_CONV_ID"
            )
            continue

        try:
            data = _fetch_conversation(conv_id)
            duration_secs, transcript_text = _extract_duration_and_transcript(data)

            if not transcript_text:
                # call might still be processing; don't mark as updated yet
                _sheet_update_fields(
                    row_num,
                    call_duration_secs=duration_secs,
                    transcript="",
                    transcript_updated="PENDING_TRANSCRIPT"
                )
                continue

            # 1) update transcript in sheet
            _sheet_update_fields(
                row_num,
                call_duration_secs=duration_secs,
                transcript=transcript_text,
                transcript_updated="UPDATED"
            )

            # 2) inject into CFO backend
            # NOTE: if you want Name/Email/Mobile/Company from sheet, add them to get_pending response.
            # For now inject only transcript + duration with blank name/company unless you extend Apps Script to return more cols.
            _inject_to_cfo_backend(
                name="",
                company="",
                mobile="",
                email="",
                transcript=transcript_text,
                duration_secs=duration_secs
            )

            _sheet_update_fields(row_num, db_injected="UPDATED")

        except Exception as e:
            _sheet_update_fields(
                row_num,
                transcript_updated=f"ERROR: {type(e).__name__}",
                db_injected=f"ERROR: {type(e).__name__}"
            )


def start_transcript_poller():
    """
    Starts a daemon thread that runs every 30 minutes.
    """
    def _loop():
        while True:
            try:
                run_transcript_cycle()
            except Exception:
                # don't crash the loop
                pass
            time.sleep(POLL_EVERY_SECONDS)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t
