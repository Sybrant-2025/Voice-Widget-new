import os
import json
import time
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==============================
# CONFIG
# ==============================
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
SHEET_ID = os.getenv("SHEET_ID")               # e.g. 1WF0NB9fnxhDPEi_arGSp18Kev9KXdoX-IePIE8KJgCQ
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "Sheet1")
BRAND = os.getenv("BRAND", "default")

# ==============================
# GOOGLE CREDS (ENV or FILE)
# ==============================
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

if "GOOGLE_SERVICE_ACCOUNT_JSON" in os.environ:
    print("[AutoUpdate] Using credentials from Railway environment variable")
    data = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    CREDS = ServiceAccountCredentials.from_json_keyfile_dict(data, SCOPE)
else:
    print("[AutoUpdate] Using local file google_service_account.json")
    CREDS = ServiceAccountCredentials.from_json_keyfile_name("google_service_account.json", SCOPE)

gc = gspread.authorize(CREDS)
sheet = gc.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)

# ==============================
# ELEVENLABS API CONFIG
# ==============================
BASE_URL = "https://api.elevenlabs.io/v1/convai/conversations"
HEADERS = {
    "xi-api-key": ELEVENLABS_API_KEY,
    "Accept": "application/json"
}

# ==============================
# FETCH TRANSCRIPT + DURATION
# ==============================
def fetch_transcript(conv_id):
    try:
        resp = requests.get(f"{BASE_URL}/{conv_id}", headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"[AutoUpdate] Failed to fetch {conv_id}: {resp.status_code}")
            return None, None

        data = resp.json()
        duration = (
            data.get("metadata", {}).get("call_duration_secs")
            or data.get("conversation_initiation_client_data", {})
                .get("dynamic_variables", {})
                .get("system__call_duration_secs")
        )

        transcript = ""
        if "transcript" in data:
            for t in data["transcript"]:
                role = t.get("role", "UNKNOWN").upper()
                msg = t.get("message", "")
                transcript += f"{role}: {msg}\n"

        return duration, transcript.strip()
    except Exception as e:
        print(f"[AutoUpdate] Error fetching {conv_id}: {e}")
        return None, None

# ==============================
# UPDATE SHEET
# ==============================
def update_sheet():
    print("[AutoUpdate] Checking for rows with Conversation ID but empty Transcript...")
    data = sheet.get_all_records()

    headers = sheet.row_values(1)
    if "Conversation ID" not in headers or "Transcript" not in headers:
        print("[AutoUpdate] Sheet missing required columns.")
        return

    conv_idx = headers.index("Conversation ID") + 1
    duration_idx = headers.index("Call Duration (secs)") + 1
    transcript_idx = headers.index("Transcript") + 1

    updated = 0
    for i, row in enumerate(data, start=2):  # start=2 because first row is headers
        conv_id = row.get("Conversation ID", "").strip()
        transcript = row.get("Transcript", "").strip()
        duration = row.get("Call Duration (secs)", "")

        if conv_id and (not transcript or not duration):
            dur, trans = fetch_transcript(conv_id)
            if dur or trans:
                sheet.update_cell(i, duration_idx, dur or "")
                sheet.update_cell(i, transcript_idx, trans or "")
                print(f"[AutoUpdate] ✅ Updated row {i} for {conv_id}")
                updated += 1
                time.sleep(1.5)  # Avoid Google rate limits

    print(f"[AutoUpdate] Finished — {updated} rows updated.")

# ==============================
# MAIN LOOP (RUN EVERY 5 MIN)
# ==============================
if __name__ == "__main__":
    print("[Scheduler] Triggering auto_update_transcripts.py")
    update_sheet()
