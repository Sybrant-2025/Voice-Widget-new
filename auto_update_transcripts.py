import time
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ===== CONFIG =====
API_KEY = "sk_2672b9e5e381a863f2e79b2add72e15782bd0b94957700c5"
BASE_URL = "https://api.elevenlabs.io/v1/convai/conversations"

# your Google Service Account JSON file
SERVICE_FILE = "google_service_account.json"

# list of brand-specific webhook sheet URLs (or spreadsheet IDs)
SHEETS = {
    "newcfobridge": "https://script.google.com/macros/s/AKfycbxLYMDjeIyNU5-eO6OgnVa8RqOgvp2pBA8jNF5azWY1qiUDutrIyJs3zSkn1ZgyL5zfwQ/exec"
}

# ===== GOOGLE AUTH =====
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_FILE, scope)
gclient = gspread.authorize(creds)

# ===== ELEVENLABS FETCH =====
def fetch_convai_details(conv_id):
    headers = {"xi-api-key": API_KEY, "Accept": "application/json"}
    try:
        r = requests.get(f"{BASE_URL}/{conv_id}", headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()

        # duration
        dur = (
            data.get("metadata", {}).get("call_duration_secs")
            or data.get("conversation_initiation_client_data", {})
            .get("dynamic_variables", {})
            .get("system__call_duration_secs")
        )

        # transcript (combined text)
        t_items = [
            f"{t.get('role', '').upper()}: {t.get('message', '').strip()}"
            for t in data.get("transcript", [])
            if t.get("message")
        ]
        transcript = "\n".join(t_items) if t_items else ""

        return dur, transcript
    except Exception as e:
        print(f"[ERROR] {conv_id}: {e}")
        return None, None


# ===== UPDATE SHEET =====
def update_sheet(sheet_name, sheet_url):
    try:
        sheet = gclient.open_by_url(sheet_url).sheet1
        rows = sheet.get_all_records()
        header = sheet.row_values(1)
        conv_idx = header.index("Conversation ID") + 1
        dur_idx = header.index("Call Duration (secs)") + 1
        tran_idx = header.index("Transcript") + 1

        for i, row in enumerate(rows, start=2):  # row 1 = header
            conv_id = row.get("Conversation ID", "").strip()
            dur = row.get("Call Duration (secs)", "")
            tran = row.get("Transcript", "")
            if not conv_id or (dur and tran):
                continue  # skip blanks or already filled

            print(f"[{sheet_name}] Fetching for {conv_id}")
            call_duration, transcript = fetch_convai_details(conv_id)
            if call_duration or transcript:
                sheet.update_cell(i, dur_idx, call_duration or "")
                sheet.update_cell(i, tran_idx, transcript or "")
                print(f"  ✅ Updated row {i}: duration {call_duration}s")
            time.sleep(2)  # small delay to avoid rate-limits

    except Exception as e:
        print(f"[ERROR updating {sheet_name}] {e}")


# ===== MAIN LOOP =====
if __name__ == "__main__":
    print("🔁 Auto-update service started (every 5 minutes)")
    while True:
        for brand, url in SHEETS.items():
            update_sheet(brand, url)
        print("✅ Cycle complete — sleeping 5 min\n")
        time.sleep(300)
