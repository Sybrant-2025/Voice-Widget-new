from flask import Flask, request, Response, jsonify, render_template
from flask_cors import CORS
from flask import render_template_string
import logging, json, threading
import requests
import os
import datetime
import time

app = Flask(__name__)
CORS(app)

# --- Env / Config ---
ELEVENLABS_API_KEY_DEFAULT = "sk_2672b9e5e381a863f2e79b2add72e15782bd0b94957700c5"  # dev only; prefer env
ELEVENLABS_API_KEY = (os.getenv("ELEVENLABS_API_KEY") or ELEVENLABS_API_KEY_DEFAULT).strip()

# Fallback single-sheet URL (only used if brand is unknown and no default below)
SHEET_WEBHOOK_URL_FALLBACK = os.getenv(
    "SHEET_WEBHOOK_URL",
    "https://script.google.com/macros/s/AKfycby0hb5wDlSqtDwLiTWKULqkuZzVmtpJXRgof9ncF5adfIV_y3hL7QmDw7tliYtvF_fRGw/exec"  # dhilak
)

# ---- Brand → Apps Script mapping ----
BRAND_TO_WEBHOOK = {
    "default":     "https://script.google.com/macros/s/AKfycbzW-OSCQ1bJA17bqac6WlsdXs3pVrUvPlFhhbIud_uZwuQugD8HoHRxG3NWp-J6e0wP/exec",  
    "kfwcorp":     "https://script.google.com/macros/s/AKfycbw3Mw25MO3a0JDsTE9YWpOIx9skESyftz4FUYZY6CnycStnrIcNVjFO7LqKkjlkvyoH7A/exec",
    "successgyan": "https://script.google.com/macros/s/AKfycbyASM8a0kZ649kxqvzmkOiyYbFpdXobDPCUYEF0y3CK-409iEe9dgWnsYp5dhCCOmrLhw/exec",
    "orientbell":  "https://script.google.com/macros/s/AKfycby0hb5wDlSqtDwLiTWKULqkuZzVmtpJXRgof9ncF5adfIV_y3hL7QmDw7tliYtvF_fRGw/exec",
    "galent":      "https://script.google.com/macros/s/AKfycbzZrTfc6KbWz0L98YjhWiID1Wwwhcg4_MLybcKF4plbCYzOcVMQgsPsS-cnPv5nKxVPSw/exec",
    "myndwell":    "https://script.google.com/macros/s/AKfycbznRQAdKL7e2y7AqOhK6vmFuW9xzKZ29AHJQa8HFPqS01tn_bAF4hiGCohxvex2R8LGeA/exec",
    "preludesys":  "https://script.google.com/macros/s/AKfycbwZpUmj42D_GB3AgxTqSSdQcua2byy5dvFr7dO5jJBhYrUDNhulPj-RxLtWwlz_87T5Pg/exec",
    "cfobridge":   "https://script.google.com/macros/s/AKfycbxltOr9C6T7Nw2DOKanBjiKVYrma9-EODtoReLUCNTp-3dANl2s0mS3oQACIp_P--Bb/exec",
    "voiceassistant": "https://script.google.com/macros/s/AKfycbyde5ank1ylpdAM3Kn28ZAULySme300V__VjOy7ESLHd0NX-gtoQAvMkmbt0bv7QJ01LQ/exec",
    "sybrant": "https://script.google.com/macros/s/AKfycbzW-OSCQ1bJA17bqac6WlsdXs3pVrUvPlFhhbIud_uZwuQugD8HoHRxG3NWp-J6e0wP/exec",
    "dhilaktest_old": "https://script.google.com/macros/s/AKfycby0hb5wDlSqtDwLiTWKULqkuZzVmtpJXRgof9ncF5adfIV_y3hL7QmDw7tliYtvF_fRGw/exec",
    "dhilaktest": "https://script.google.com/macros/s/AKfycbz_VKhTD7G2Iqqk-ZrqOkebX-sXncZiqhxP12EOv3xgMvCchPbZ4n6PHPdTOKA7spwnKw/exec",
    "kopiko": "https://script.google.com/macros/s/AKfycbzip7wk995Q8BfktpVNZp6uJREQ8CqydyTVtxlTG0NucPugFOECa6XBpqo3Xv6pAkgM/exec",
    "leaserush" :"https://script.google.com/a/macros/sybrantdata.com/s/AKfycbxt20fVA71fAuePCWGzoRB-KRhjmpoogQF62Yr_qmFlqAP0wUQBkeNLJzlr9CrosIo9/exec",
	"demo": "https://script.google.com/macros/s/AKfycbx5P0eiH1v7SE1Uoy1R_V4u-ab7dOqJJO7CpLFxgjkH7C8gMXwICzsaGTl3AWG2KU_Y0g/exec",
	"newgendigital": "https://script.google.com/macros/s/AKfycbyKHdnaO1IFWQSkpJiV-_dIZ6PU9GC-oRNwb8JjW6RM-DVVCcwScy3qTrG0ltRyH5Dc/exec",
}

# pretty labels for sheet display
BRAND_DISPLAY_NAMES = {
    "sybrant": "Sybrant Technologies",
    "kfwcorp": "KFW Corp",
    "myndwell": "Myndwell",
    "cfobridge": "CFO Bridge",
    "galent": "Galent",
    "orientbell": "Orientbell Tiles",
    "preludesys": "PreludeSys",
    "voiceassistant": "Sybrant Voizee",
    "dhilaktest": "Dhilak Test",
    "kopiko": "Kopiko",
    "demo": "Demo",
	"leaserush": "Lease Rush",
	"newgendigital": "Newgen Digital"
}

DRY_RUN_SHEETS = os.getenv("DRY_RUN_SHEETS", "0") == "1"
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.DEBUG),
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("voizee")

# Keep track so we don't duplicate background pulls + remember brand/url for transcripts
_SCHEDULED_TRANSCRIPTS = set()
_SCHEDULE_LOCK = threading.Lock()
_VISIT_META = {}   # visit_id -> {"brand": str, "url": str}
_CONV_META  = {}   # conv_id  -> {"brand": str, "url": str, "visit_id": str}

# In-memory cache
recent_visitors = {}       # { email/phone: { data, ts } }
cached_conversations = {}  # { conv_id: { url, ts } }

########################
# ---------- Helpers for Sheets ----------
def _brand_webhook(brand: str) -> str:
    b = (brand or "").lower().strip()
    if b in BRAND_TO_WEBHOOK:
        return BRAND_TO_WEBHOOK[b]
    # unknown brand → use default if set; otherwise fallback env/url
    return BRAND_TO_WEBHOOK.get("default", SHEET_WEBHOOK_URL_FALLBACK)

def _send_to_sheet(webhook_url: str, payload: dict, tag: str = "sheet"):
    if DRY_RUN_SHEETS:
        app.logger.info("[DRY_RUN] → %s %s", tag, payload)
        return True, "dry_run"
    try:
        r = requests.post(webhook_url, json=payload, timeout=15)
        app.logger.info("[%s] Apps Script → %s %s", tag, r.status_code, r.text[:200])
        return (200 <= r.status_code < 300), r.text
    except Exception as e:
        app.logger.exception("[%s] Apps Script POST failed", tag)
        return False, str(e)

def _send_to_sheet_brand(payload: dict, brand: str):
    url = _brand_webhook(brand)
    # Always lower internally for routing
    bkey = (brand or "").lower().strip()
    # Use mapped display name for Sheets
    payload["brand"] = BRAND_DISPLAY_NAMES.get(bkey, brand)
    return _send_to_sheet(url, payload, tag=(bkey or "default"))

# ---------- ElevenLabs helpers ----------
def _pull_transcript(conv_id: str, api_key: str):
    headers = {"xi-api-key": api_key, "Accept": "application/json"}
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conv_id}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        app.logger.info("ConvAI GET %s → %s", conv_id, resp.status_code)
        if resp.status_code != 200:
            # always 3-tuple
            try:
                ejson = resp.json()
                return "", None, f"{resp.status_code}: {ejson}"
            except Exception:
                return "", None, f"{resp.status_code}: {resp.text[:200]}"

        j = resp.json()

        # --- duration ---
        duration = (
            j.get("metadata", {}).get("call_duration_secs")
            or j.get("conversation_initiation_client_data", {})
                 .get("dynamic_variables", {})
                 .get("system__call_duration_secs")
        )

        # --- transcript ---
        items = j.get("transcript", []) or []
        lines = []
        for t in items:
            role = (t.get("role") or "").upper()
            msg  = t.get("message") or t.get("text") or ""
            if msg:
                lines.append(f"{role}: {msg}")
        txt = "\n".join(lines).strip()
        if not txt:
            return "", duration, "empty_transcript"
        if len(txt) > 30000:
            txt = txt[:30000] + "\n...[truncated]"

        return txt, duration, ""
    except Exception as e:
        # always 3-tuple
        return "", None, f"exception: {e}"

def _push_transcript_to_sheet(visit_id: str, conv_id: str, transcript: str, brand: str, page_url: str, duration: int | None = None):
    payload = {
        "event": "transcript",
        "visit_id": visit_id,
        "conversation_id": conv_id,
        "transcript": transcript,
        "brand": brand or "",
        "url": page_url or "",
        "server_timestamp_ms": int(time.time() * 1000),
    }
    if duration is not None:
        payload["call_duration_secs"] = duration
    return _send_to_sheet_brand(payload, brand)

def _background_transcript_worker(visit_id: str, conv_id: str, agent_id: str, brand: str, page_url: str):
    api_key = (os.getenv("ELEVENLABS_API_KEY") or ELEVENLABS_API_KEY).strip()
    app.logger.info("[BG] transcript worker for %s (visit=%s, brand=%s)", conv_id, visit_id, brand or "default")

    delays = [30, 90, 300]  # seconds after schedule
    last_err = ""
    for idx, wait_s in enumerate(delays, 1):
        time.sleep(wait_s)
        txt, duration, err = _pull_transcript(conv_id, api_key)
        if txt:
            ok, _ = _push_transcript_to_sheet(visit_id, conv_id, txt, brand, page_url, duration)
            if ok:
                app.logger.info("[BG] transcript pushed on attempt %d", idx)
                break
        else:
            last_err = err
            app.logger.info("[BG] still no transcript (%s) on attempt %d", err, idx)
            if idx == len(delays):
                _push_transcript_to_sheet(visit_id, conv_id, f"[TRANSCRIPT_ERROR] {err or 'unavailable'}", brand, page_url, None)

    with _SCHEDULE_LOCK:
        _SCHEDULED_TRANSCRIPTS.discard(conv_id)

def _schedule_transcript_pull(visit_id: str, conv_id: str, agent_id: str, brand: str, page_url: str):
    with _SCHEDULE_LOCK:
        if conv_id in _SCHEDULED_TRANSCRIPTS:
            return
        _SCHEDULED_TRANSCRIPTS.add(conv_id)
    t = threading.Thread(
        target=_background_transcript_worker,
        args=(visit_id, conv_id, agent_id, (brand or ""), (page_url or "")),
        daemon=True
    )
    t.start()
    app.logger.info("Scheduled background transcript pulls for conv_id=%s (brand=%s)", conv_id, brand or "default")

# ---------- Widget JS (brand-aware) ----------
def serve_widget_js_updated(agent_id, branding="Powered by Voizee", brand=""):
    js = r"""
(function(){
  const AGENT_ID = "__AGENT_ID__";
  const BRAND = "__BRAND__";
  const BRANDING_TEXT = "__BRANDING__";
  // Deployed host:
  const LOG_ENDPOINT = "https://voice-widget-new-production-177d.up.railway.app/log-visitor-updated";

  // --- fetch with retries (for submit) ---
  async function fetchWithRetry(url, opts, retries = 2, backoffMs = 800, timeoutMs = 10000) {
    const attempt = (n) =>
      new Promise((resolve, reject) => {
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), timeoutMs);
        fetch(url, { ...opts, signal: ctrl.signal })
          .then((r) => {
            clearTimeout(t);
            if (r.ok) return resolve(r);
            if (n < retries) return setTimeout(() => resolve(attempt(n + 1)), backoffMs * (n + 1));
            reject(new Error(`HTTP ${r.status}`));
          })
          .catch((e) => {
            clearTimeout(t);
            if (n < retries) return setTimeout(() => resolve(attempt(n + 1)), backoffMs * (n + 1));
            reject(e);
          });
      });
    return attempt(0);
  }

  // ===== Cache (24h) =====
  const FORM_KEY = "convai_form_cache";
  const TTL_KEY  = "convai_form_submitted";
  const FORM_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

  function saveFormCache(fields){
    try {
      const rec = { data: fields, ts: Date.now() };
      localStorage.setItem(FORM_KEY, JSON.stringify(rec));
      localStorage.setItem(TTL_KEY, String(Date.now() + FORM_TTL_MS));
    } catch(_) {}
  }
  function getFormCache(){
    try {
      const rec = JSON.parse(localStorage.getItem(FORM_KEY) || "null");
      if (!rec || !rec.data) return null;
      if (Date.now() - (rec.ts || 0) > FORM_TTL_MS) return null;
      return rec.data;
    } catch(_) { return null; }
  }
  function ttlActive(){
    const ttl = parseInt(localStorage.getItem(TTL_KEY) || "0");
    return Date.now() < ttl;
  }

  // ===== Visit & Conv correlation =====
  let VISIT_ID = (typeof crypto !== "undefined" && crypto.randomUUID)
    ? crypto.randomUUID()
    : (Date.now() + "_" + Math.random().toString(36).slice(2));
  try { localStorage.setItem("convai_visit_id", VISIT_ID); } catch(_) {}

  let CONV_ID = null;
  let _convIdResolve;
  const conversationIdReady = new Promise(res => (_convIdResolve = res));

  // Will POST cached visitor_log once per page load
  let __cachedLogSent = false;
  function sendCachedVisitorLog(reason){
    if (__cachedLogSent) return;
    const cached = getFormCache();
    if (!cached) return;

    __cachedLogSent = true;
    const payload = {
      event: "visitor_log",
      visit_id: VISIT_ID,
      agent_id: AGENT_ID,
      brand: BRAND,
      url: location.href,
      timestamp: new Date().toISOString(),
      name: cached.name || "",
      company: cached.company || "",
      email: cached.email || "",
      phone: cached.phone || "",
      conversation_id: CONV_ID || null
    };
    fetch(LOG_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).catch(()=>{});
    console.log("[ConvAI] auto-logged cached form → sheet (", reason, ")");
  }

  function setConvIdOnce(cid){
    if (!cid || CONV_ID) return;
    CONV_ID = cid;
    try { _convIdResolve(CONV_ID); } catch(_) {}

    // 1) Update sheet with conversation_id
    fetch(LOG_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event: "conversation_id",
        visit_id: VISIT_ID,
        conversation_id: CONV_ID,
        agent_id: AGENT_ID,
        brand: BRAND,
        url: location.href,
        timestamp: new Date().toISOString()
      })
    }).catch(()=>{});

    // 2) If we skipped the modal due to 24h TTL and haven't sent the cached data yet, do it now
    if (ttlActive()) sendCachedVisitorLog("conv_id_arrived");

    // 3) End hooks + unload beacons
    setupCallEndHooks && setupCallEndHooks();
    setupUnloadBeacons && setupUnloadBeacons();
  }

  window.addEventListener("message", (evt) => {
    try {
      const d = evt?.data;
      const cid =
        d?.conversation_initiation_metadata_event?.conversation_id ||
        d?.conversation_id;
      setConvIdOnce(cid);
    } catch(_) {}
  }, false);

  (function patchWebSocket(){
    const OriginalWS = window.WebSocket;
    if (!OriginalWS) return;
    function WrappedWS(url, protocols){
      const ws = protocols ? new OriginalWS(url, protocols) : new OriginalWS(url);
      ws.addEventListener("message", (ev) => {
        try {
          if (typeof ev.data !== "string") return;
          const d = JSON.parse(ev.data);
          const cid = d?.conversation_initiation_metadata_event?.conversation_id || d?.conversation_id;
          if (cid) setConvIdOnce(cid);
        } catch(_) {}
      });
      return ws;
    }
    WrappedWS.prototype = OriginalWS.prototype;
    Object.getOwnPropertyNames(OriginalWS).forEach(k => { try { WrappedWS[k] = OriginalWS[k]; } catch(_){} });
    window.WebSocket = WrappedWS;
  })();

  function removeExtras(sr){
    if (!sr) return;
    try { ['span.opacity-30','a[href*="elevenlabs.io/conversational-ai"]'].forEach(sel => {
      sr.querySelectorAll(sel).forEach(el => el.remove());
    }); } catch(e){}
  }

  function hookStartButton(){
    const widget = document.querySelector("elevenlabs-convai");
    if (!widget) return false;
    const sr = widget.shadowRoot;
    if (!sr) return false;

    removeExtras(sr);

    const sels = [
      'button[title="Start a call"]',
      'button[aria-label="Start a call"]',
      'button[title*="Start"]',
      'button[aria-label*="Start"]'
    ];
    for (const sel of sels) {
      const btn = sr.querySelector(sel);
      if (btn && !btn._hooked) {
        btn._hooked = true;
        interceptStartClick(btn);
        return true;
      }
    }
    return false;
  }

  function interceptStartClick(btn){
    window.__last_call_btn = btn;
    btn.addEventListener("click", (e) => {
      if (ttlActive() && getFormCache()) {
        sendCachedVisitorLog("start_btn_ttl_active");
        return;
      }
      if (btn._allowCall) { btn._allowCall = false; return; }
      e.preventDefault();
      e.stopImmediatePropagation();
      const modal = document.getElementById("convai-visitor-modal");
      if (modal) modal.style.display = "flex";
    }, true);
  }

  function hookEndButton(){
    const widget = document.querySelector("elevenlabs-convai");
    if (!widget) return false;
    const sr = widget.shadowRoot;
    if (!sr) return false;

    let btn = sr.querySelector('button[aria-label="End"], button[title="End"], button[aria-label="End call"], button[title="End call"]');
    if (!btn) {
      const icon = sr.querySelector('slot[name="icon-phone-off"]');
      if (icon) btn = icon.closest('button');
    }
    if (!btn) {
      const allButtons = Array.from(sr.querySelectorAll('button'));
      btn = allButtons.find(b => (b.textContent || "").trim().toLowerCase() === "end");
    }
    if (!btn) return false;

    if (!btn.__endHooked) {
      btn.__endHooked = true;
      btn.addEventListener("click", () => {
        setTimeout(() => {
          if (!CONV_ID) return;
          fetch("https://voice-widget-new-production-177d.up.railway.app/fetch-transcript-updated", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              visit_id: VISIT_ID,
              conversation_id: CONV_ID,
              agent_id: AGENT_ID,
              brand: BRAND,
              url: location.href
            }),
            keepalive: true
          }).catch(()=>{});
          console.log("[ConvAI] requested transcript (T+30s) for", CONV_ID);
        }, 30000);
      }, { capture: true });
    }
    return true;
  }

  function setupCallEndHooks(){
    hookEndButton();
    const widget = document.querySelector("elevenlabs-convai");
    const sr = widget && widget.shadowRoot;
    if (!sr) return;
    if (!window.__endBtnObserver){
      window.__endBtnObserver = new MutationObserver(() => { hookEndButton(); });
      window.__endBtnObserver.observe(sr, { childList: true, subtree: true });
    }
  }

  function setupUnloadBeacons(){
    function beacon(){
      if (!CONV_ID) return;
      try {
        const payload = JSON.stringify({
          visit_id: VISIT_ID,
          conversation_id: CONV_ID,
          agent_id: AGENT_ID,
          brand: BRAND,
          url: location.href
        });
        const blob = new Blob([payload], {type: "application/json"});
        navigator.sendBeacon("https://voice-widget-new-production-177d.up.railway.app/fetch-transcript-updated-beacon", blob);
      } catch(_) {}
    }
    window.addEventListener("pagehide", beacon);
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") beacon();
    });
  }

  function createVisitorModal(){
    if (document.getElementById("convai-visitor-modal")) return;

    const modal = document.createElement("div");
    modal.id = "convai-visitor-modal";
    modal.style = "display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:999999;align-items:center;justify-content:center;";
    modal.innerHTML = `
      <div style="background:white;border-radius:8px;padding:20px;max-width:400px;width:90%;font-family:sans-serif;">
        <div style="text-align:right;"><button id="convai-close" style="font-size:18px;background:none;border:none;">×</button></div>
        <h3 style="margin-top:0;">Tell us about you</h3>
        <form id="convai-form" style="display:flex;flex-direction:column;gap:10px;">
          <input name="name" placeholder="Full name" required style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <input name="company" placeholder="Company name" required style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <input name="email" type="email" placeholder="Email" required style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <input name="phone" placeholder="Phone" required style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <div style="display:flex;gap:10px;">
            <button type="submit" style="flex:1;padding:10px;background:#007bff;color:white;border:none;border-radius:4px;">Submit</button>
            <button type="button" id="convai-cancel" style="padding:10px;background:#eee;border:none;border-radius:4px;">Cancel</button>
          </div>
        </form>
      </div>
    `;
    document.body.appendChild(modal);

    try {
      const cached = getFormCache();
      if (cached) {
        modal.querySelector('input[name="name"]').value    = cached.name || "";
        modal.querySelector('input[name="company"]').value = cached.company || "";
        modal.querySelector('input[name="email"]').value   = cached.email || "";
        modal.querySelector('input[name="phone"]').value   = cached.phone || "";
      }
    } catch(_) {}

    modal.querySelector("#convai-close").onclick = () => modal.style.display = "none";
    modal.querySelector("#convai-cancel").onclick = () => modal.style.display = "none";

    const form = modal.querySelector("#convai-form");
    form.onsubmit = async function(ev){
      ev.preventDefault();
      if (form.__submitting) return; // double-click guard
      form.__submitting = true;

      const submitBtn = form.querySelector('button[type="submit"]');
      const cancelBtn = modal.querySelector("#convai-cancel");
      const originalText = submitBtn.innerText;

      const setDisabled = (el, on) => {
        if (!el) return;
        el.disabled = on;
        if (on) {
          el.style.opacity = "0.6";
          el.style.cursor = "not-allowed";
          el.style.pointerEvents = "none";
        } else {
          el.style.opacity = "";
          el.style.cursor = "";
          el.style.pointerEvents = "";
        }
      };

      setDisabled(submitBtn, true);
      setDisabled(cancelBtn, true);
      submitBtn.innerText = "Submitting…";

      const fd = new FormData(form);
      const fields = Object.fromEntries(fd.entries());

      saveFormCache(fields);

      const data = {
        event: "visitor_log",
        visit_id: VISIT_ID,
        agent_id: AGENT_ID,
        brand: BRAND,
        url: location.href,
        timestamp: new Date().toISOString(),
        conversation_id: CONV_ID || null,
        ...fields
      };

      try {
        await fetchWithRetry(
          LOG_ENDPOINT,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
          },
          2,    // retries
          800,  // backoff
          10000 // timeout per try
        );

        // success
        submitBtn.innerText = "Submitted ✓";
        modal.style.display = "none";
        try {
          if (window.__last_call_btn) {
            window.__last_call_btn._allowCall = true;
            window.__last_call_btn.click();
          }
        } catch(_) {}

        // keep submit disabled on success
      } catch(err){
        // failure after retries
        console.warn("Logging failed:", err);
        submitBtn.innerText = "Retry submit";
        setDisabled(submitBtn, false);
        setDisabled(cancelBtn, false);
        form.__submitting = false;
        return; // keep modal open for retry
      }

      form.__submitting = false;
      // leave submit disabled after success; re-enable cancel (optional)
      setDisabled(cancelBtn, false);
    }
  }

  try {
    const tag = document.createElement("elevenlabs-convai");
    tag.setAttribute("agent-id", AGENT_ID);
    document.body.appendChild(tag);
  } catch (e) {}

  (function loadEmbed(){
    const s = document.createElement("script");
    s.src = "https://unpkg.com/@elevenlabs/convai-widget-embed";
    s.async = true;
    s.onerror = function(){
      const fallback = document.createElement("script");
      fallback.src = "https://elevenlabs.io/convai-widget/index.js";
      fallback.async = true;
      document.body.appendChild(fallback);
    };
    document.body.appendChild(s);
  })();

  createVisitorModal();

  const obs = new MutationObserver(() => { try { if (hookStartButton()) obs.disconnect(); } catch(e){} });
  obs.observe(document, { childList: true, subtree: true });
  let tries = 0;
  const poll = setInterval(() => {
    const ok = hookStartButton();
    if (ok || ++tries > 50) clearInterval(poll);
  }, 300);

})();
    """
    return (js
            .replace("__AGENT_ID__", agent_id)
            .replace("__BRANDING__", branding)
            .replace("__BRAND__", brand))


# test version  widget

def serve_widget_js_update_new(agent_id, branding="Powered by Voizee", brand=""):
    js = r"""
(function(){
  const AGENT_ID = "__AGENT_ID__";
  const BRAND = "__BRAND__";
  const BRANDING_TEXT = "__BRANDING__";
  const LOG_ENDPOINT = "https://voice-widget-new-production-177d.up.railway.app/log-visitor-updated";

  // --- fetch with retries (for submit) ---
  async function fetchWithRetry(url, opts, retries = 2, backoffMs = 800, timeoutMs = 10000) {
    const attempt = (n) =>
      new Promise((resolve, reject) => {
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), timeoutMs);
        fetch(url, { ...opts, signal: ctrl.signal })
          .then((r) => {
            clearTimeout(t);
            if (r.ok) return resolve(r);
            if (n < retries) return setTimeout(() => resolve(attempt(n + 1)), backoffMs * (n + 1));
            reject(new Error(`HTTP ${r.status}`));
          })
          .catch((e) => {
            clearTimeout(t);
            if (n < retries) return setTimeout(() => resolve(attempt(n + 1)), backoffMs * (n + 1));
            reject(e);
          });
      });
    return attempt(0);
  }

  // ===== Cache (24h) =====
  const FORM_KEY = "convai_form_cache";
  const TTL_KEY  = "convai_form_submitted";
  const FORM_TTL_MS = 24 * 60 * 60 * 1000;

  function saveFormCache(fields){
    try {
      const rec = { data: fields, ts: Date.now() };
      localStorage.setItem(FORM_KEY, JSON.stringify(rec));
      localStorage.setItem(TTL_KEY, String(Date.now() + FORM_TTL_MS));
    } catch(_) {}
  }
  function getFormCache(){
    try {
      const rec = JSON.parse(localStorage.getItem(FORM_KEY) || "null");
      if (!rec || !rec.data) return null;
      if (Date.now() - (rec.ts || 0) > FORM_TTL_MS) return null;
      return rec.data;
    } catch(_) { return null; }
  }
  function ttlActive(){
    const ttl = parseInt(localStorage.getItem(TTL_KEY) || "0");
    return Date.now() < ttl;
  }

  // ===== Visit & Conv correlation =====
  let VISIT_ID = (typeof crypto !== "undefined" && crypto.randomUUID)
    ? crypto.randomUUID()
    : (Date.now() + "_" + Math.random().toString(36).slice(2));
  try { localStorage.setItem("convai_visit_id", VISIT_ID); } catch(_) {}

  let CONV_ID = null;
  let _convIdResolve;
  const conversationIdReady = new Promise(res => (_convIdResolve = res));

  let __cachedLogSent = false;
  function sendCachedVisitorLog(reason){
    if (__cachedLogSent) return;
    const cached = getFormCache();
    if (!cached) return;
    __cachedLogSent = true;
    const payload = {
      event: "visitor_log",
      visit_id: VISIT_ID,
      agent_id: AGENT_ID,
      brand: BRAND,
      url: location.href,
      timestamp: new Date().toISOString(),
      name: cached.name || "",
      company: cached.company || "",
      email: cached.email || "",
      phone: cached.phone || "",
      conversation_id: CONV_ID || null
    };
    fetch(LOG_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).catch(()=>{});
    console.log("[ConvAI] auto-logged cached form → sheet (", reason, ")");
  }

  function setConvIdOnce(cid){
    if (!cid || CONV_ID) return;
    CONV_ID = cid;
    try { _convIdResolve(CONV_ID); } catch(_) {}
    fetch(LOG_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event: "conversation_id",
        visit_id: VISIT_ID,
        conversation_id: CONV_ID,
        agent_id: AGENT_ID,
        brand: BRAND,
        url: location.href,
        timestamp: new Date().toISOString()
      })
    }).catch(()=>{});
    if (ttlActive()) sendCachedVisitorLog("conv_id_arrived");
    setupCallEndHooks && setupCallEndHooks();
    setupUnloadBeacons && setupUnloadBeacons();
  }

  window.addEventListener("message", (evt) => {
    try {
      const d = evt?.data;
      const cid =
        d?.conversation_initiation_metadata_event?.conversation_id ||
        d?.conversation_id;
      setConvIdOnce(cid);
    } catch(_) {}
  }, false);

  (function patchWebSocket(){
    const OriginalWS = window.WebSocket;
    if (!OriginalWS) return;
    function WrappedWS(url, protocols){
      const ws = protocols ? new OriginalWS(url, protocols) : new OriginalWS(url);
      ws.addEventListener("message", (ev) => {
        try {
          if (typeof ev.data !== "string") return;
          const d = JSON.parse(ev.data);
          const cid = d?.conversation_initiation_metadata_event?.conversation_id || d?.conversation_id;
          if (cid) setConvIdOnce(cid);
        } catch(_) {}
      });
      return ws;
    }
    WrappedWS.prototype = OriginalWS.prototype;
    Object.getOwnPropertyNames(OriginalWS).forEach(k => { try { WrappedWS[k] = OriginalWS[k]; } catch(_){} });
    window.WebSocket = WrappedWS;
  })();

  // --- Replace default widget layout ---
  function replaceWidgetUI(){
    const widget = document.querySelector("elevenlabs-convai");
    if (!widget) return false;
    const sr = widget.shadowRoot;
    if (!sr) return false;
    const oldCard = sr.querySelector('div.flex.flex-col.p-2.rounded-sheet');
    if (oldCard && !oldCard.__customized) {
      oldCard.__customized = true;
      oldCard.outerHTML = `
		<div class="voizee-card" 
			 style="display:flex;flex-direction:column;align-items:center;justify-content:center;
			 		background:transparent;border-radius:16px;
			 		box-shadow:none;overflow:visible;width:240px;
			 		font-family:sans-serif;">
		  <div class="voizee-avatar" 
		  	style="width:240px;height:360px;
		  			background-image:url('https://sybrant.com/wp-content/uploads/2025/10/voizee-vidhya-unscreen.gif');
		  			background-size:contain;background-repeat:no-repeat;
		  			background-position:center;">
		  </div>
		  <button type="button" aria-label="Start a call"
		  		style="width:90%;margin-top:-10px;margin-bottom:10px;padding:10px 0;
		  			background:#000;color:white;font-size:14px;border:none;
		  			border-radius:8px;cursor:pointer;display:flex;
		  			align-items:center;justify-content:center;gap:8px;
		  			box-shadow:0 3px 6px rgba(0,0,0,0.2);">
		  <svg height="1em" width="1em" viewBox="0 0 18 18" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
		  	<path d="M3.7489 2.25C2.93286 2.25 2.21942 2.92142 2.27338 3.7963C2.6686 10.2041 7.79483 15.3303 14.2026 15.7255C15.0775 15.7795 15.7489 15.066 15.7489 14.25V11.958C15.7489 11.2956 15.3144 10.7116 14.6799 10.5213L12.6435 9.91035C12.1149 9.75179 11.542 9.89623 11.1518 10.2864L10.5901 10.8482C9.15291 10.0389 7.95998 8.84599 7.15074 7.40881L7.71246 6.84709C8.10266 6.45689 8.24711 5.88396 8.08854 5.35541L7.47761 3.31898C7.28727 2.6845 6.70329 2.25 6.04087 2.25H3.7489Z"></path>
		  </svg>
		  <span>Start a call</span>
		  </button>
		</div>`;
      return true;
    }
    return false;
  }

  // Observe DOM until ElevenLabs widget appears
  const observer = new MutationObserver(() => {
    try { if (replaceWidgetUI()) observer.disconnect(); } catch(_) {}
  });
  observer.observe(document, { childList: true, subtree: true });

  // Fallback polling
  let tries = 0;
  const poll = setInterval(() => {
    const ok = replaceWidgetUI();
    if (ok || ++tries > 50) clearInterval(poll);
  }, 400);

  // --- Core visitor modal logic ---
  function createVisitorModal(){
    if (document.getElementById("convai-visitor-modal")) return;
    const modal = document.createElement("div");
    modal.id = "convai-visitor-modal";
    modal.style = "display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:999999;align-items:center;justify-content:center;";
    modal.innerHTML = `
      <div style="background:white;border-radius:8px;padding:20px;max-width:400px;width:90%;font-family:sans-serif;">
        <div style="text-align:right;"><button id="convai-close" style="font-size:18px;background:none;border:none;">×</button></div>
        <h3 style="margin-top:0;">Tell us about you</h3>
        <form id="convai-form" style="display:flex;flex-direction:column;gap:10px;">
          <input name="name" placeholder="Full name" required style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <input name="company" placeholder="Company name" required style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <input name="email" type="email" placeholder="Email" required style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <input name="phone" placeholder="Phone" required style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <div style="display:flex;gap:10px;">
            <button type="submit" style="flex:1;padding:10px;background:#007bff;color:white;border:none;border-radius:4px;">Submit</button>
            <button type="button" id="convai-cancel" style="padding:10px;background:#eee;border:none;border-radius:4px;">Cancel</button>
          </div>
        </form>
      </div>`;
    document.body.appendChild(modal);

    try {
      const cached = getFormCache();
      if (cached) {
        modal.querySelector('input[name="name"]').value = cached.name || "";
        modal.querySelector('input[name="company"]').value = cached.company || "";
        modal.querySelector('input[name="email"]').value = cached.email || "";
        modal.querySelector('input[name="phone"]').value = cached.phone || "";
      }
    } catch(_) {}

    modal.querySelector("#convai-close").onclick = () => modal.style.display = "none";
    modal.querySelector("#convai-cancel").onclick = () => modal.style.display = "none";

    const form = modal.querySelector("#convai-form");
    form.onsubmit = async function(ev){
      ev.preventDefault();
      if (form.__submitting) return;
      form.__submitting = true;

      const submitBtn = form.querySelector('button[type="submit"]');
      const cancelBtn = modal.querySelector("#convai-cancel");

      const setDisabled = (el, on) => {
        if (!el) return;
        el.disabled = on;
        el.style.opacity = on ? "0.6" : "";
        el.style.cursor = on ? "not-allowed" : "";
        el.style.pointerEvents = on ? "none" : "";
      };

      setDisabled(submitBtn, true);
      setDisabled(cancelBtn, true);
      submitBtn.innerText = "Submitting…";

      const fd = new FormData(form);
      const fields = Object.fromEntries(fd.entries());
      saveFormCache(fields);

      const data = {
        event: "visitor_log",
        visit_id: VISIT_ID,
        agent_id: AGENT_ID,
        brand: BRAND,
        url: location.href,
        timestamp: new Date().toISOString(),
        conversation_id: CONV_ID || null,
        ...fields
      };

      try {
        await fetchWithRetry(LOG_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });
        submitBtn.innerText = "Submitted ✓";
        modal.style.display = "none";
        try {
          if (window.__last_call_btn) {
            window.__last_call_btn._allowCall = true;
            window.__last_call_btn.click();
          }
        } catch(_) {}
      } catch(err){
        console.warn("Logging failed:", err);
        submitBtn.innerText = "Retry submit";
        setDisabled(submitBtn, false);
        setDisabled(cancelBtn, false);
        form.__submitting = false;
        return;
      }
      form.__submitting = false;
      setDisabled(cancelBtn, false);
    };
  }

  try {
    const tag = document.createElement("elevenlabs-convai");
    tag.setAttribute("agent-id", AGENT_ID);
    document.body.appendChild(tag);
  } catch(e){}

  (function loadEmbed(){
    const s = document.createElement("script");
    s.src = "https://unpkg.com/@elevenlabs/convai-widget-embed";
    s.async = true;
    s.onerror = function(){
      const fallback = document.createElement("script");
      fallback.src = "https://elevenlabs.io/convai-widget/index.js";
      fallback.async = true;
      document.body.appendChild(fallback);
    };
    document.body.appendChild(s);
  })();

  createVisitorModal();

})();
    """
    return js.replace("__AGENT_ID__", agent_id).replace("__BRANDING__", branding).replace("__BRAND__", brand)




#test version 22222
def serve_widget_js_updated2(agent_id, branding="Powered by Voizee", brand=""):
    js = r"""
(function(){
  const AGENT_ID = "__AGENT_ID__";
  const BRAND = "__BRAND__";
  const BRANDING_TEXT = "__BRANDING__";
  const LOG_ENDPOINT = "https://voice-widget-new-production-177d.up.railway.app/log-visitor-updated";

  // --- fetch with retries ---
  async function fetchWithRetry(url, opts, retries = 2, backoffMs = 800, timeoutMs = 10000) {
    const attempt = (n) =>
      new Promise((resolve, reject) => {
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), timeoutMs);
        fetch(url, { ...opts, signal: ctrl.signal })
          .then((r) => {
            clearTimeout(t);
            if (r.ok) return resolve(r);
            if (n < retries) return setTimeout(() => resolve(attempt(n + 1)), backoffMs * (n + 1));
            reject(new Error(`HTTP ${r.status}`));
          })
          .catch((e) => {
            clearTimeout(t);
            if (n < retries) return setTimeout(() => resolve(attempt(n + 1)), backoffMs * (n + 1));
            reject(e);
          });
      });
    return attempt(0);
  }

  // ===== Cache (24h) =====
  const FORM_KEY = "convai_form_cache";
  const TTL_KEY  = "convai_form_submitted";
  const FORM_TTL_MS = 24 * 60 * 60 * 1000;

  function saveFormCache(fields){
    try {
      const rec = { data: fields, ts: Date.now() };
      localStorage.setItem(FORM_KEY, JSON.stringify(rec));
      localStorage.setItem(TTL_KEY, String(Date.now() + FORM_TTL_MS));
    } catch(_) {}
  }
  function getFormCache(){
    try {
      const rec = JSON.parse(localStorage.getItem(FORM_KEY) || "null");
      if (!rec || !rec.data) return null;
      if (Date.now() - (rec.ts || 0) > FORM_TTL_MS) return null;
      return rec.data;
    } catch(_) { return null; }
  }
  function ttlActive(){
    const ttl = parseInt(localStorage.getItem(TTL_KEY) || "0");
    return Date.now() < ttl;
  }

  // ===== Visit & Conversation correlation =====
  let VISIT_ID = (typeof crypto !== "undefined" && crypto.randomUUID)
    ? crypto.randomUUID()
    : (Date.now() + "_" + Math.random().toString(36).slice(2));
  try { localStorage.setItem("convai_visit_id", VISIT_ID); } catch(_) {}

  let CONV_ID = null;
  let _convIdResolve;
  const conversationIdReady = new Promise(res => (_convIdResolve = res));

  // ---- Cached log sending ----
  let __cachedLogSent = false;
  function sendCachedVisitorLog(reason){
    if (__cachedLogSent) return;
    const cached = getFormCache();
    if (!cached) return;
    __cachedLogSent = true;
    const payload = {
      event: "visitor_log",
      visit_id: VISIT_ID,
      agent_id: AGENT_ID,
      brand: BRAND,
      url: location.href,
      timestamp: new Date().toISOString(),
      name: cached.name || "",
      company: cached.company || "",
      email: cached.email || "",
      phone: cached.phone || "",
      conversation_id: CONV_ID || null
    };
    fetch(LOG_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).catch(()=>{});
    console.log("[ConvAI] auto-logged cached form → sheet (", reason, ")");
  }

  function setConvIdOnce(cid){
    if (!cid || CONV_ID) return;
    CONV_ID = cid;
    try { _convIdResolve(CONV_ID); } catch(_) {}

    fetch(LOG_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event: "conversation_id",
        visit_id: VISIT_ID,
        conversation_id: CONV_ID,
        agent_id: AGENT_ID,
        brand: BRAND,
        url: location.href,
        timestamp: new Date().toISOString()
      })
    }).catch(()=>{});

    if (ttlActive()) sendCachedVisitorLog("conv_id_arrived");

    setupCallEndHooks && setupCallEndHooks();
    setupUnloadBeacons && setupUnloadBeacons();
  }

  window.addEventListener("message", (evt) => {
    try {
      const d = evt?.data;
      const cid =
        d?.conversation_initiation_metadata_event?.conversation_id ||
        d?.conversation_id;
      setConvIdOnce(cid);
    } catch(_) {}
  }, false);

  (function patchWebSocket(){
    const OriginalWS = window.WebSocket;
    if (!OriginalWS) return;
    function WrappedWS(url, protocols){
      const ws = protocols ? new OriginalWS(url, protocols) : new OriginalWS(url);
      ws.addEventListener("message", (ev) => {
        try {
          if (typeof ev.data !== "string") return;
          const d = JSON.parse(ev.data);
          const cid = d?.conversation_initiation_metadata_event?.conversation_id || d?.conversation_id;
          if (cid) setConvIdOnce(cid);
        } catch(_) {}
      });
      return ws;
    }
    WrappedWS.prototype = OriginalWS.prototype;
    Object.getOwnPropertyNames(OriginalWS).forEach(k => { try { WrappedWS[k] = OriginalWS[k]; } catch(_){} });
    window.WebSocket = WrappedWS;
  })();

  // --- Clean unwanted elements, keep circular button only ---
  function removeExtras(sr) {
    if (!sr) return;
    try {
      // Remove "Need help?" and "Powered by ElevenLabs"
      sr.querySelectorAll('span').forEach(span => {
        const text = span.textContent.trim().toLowerCase();
        if (text === 'need help?' || text === 'powered by elevenlabs') {
          const parent = span.closest('.flex.items-center.p-1.gap-2.min-w-60') || span;
          parent.remove();
        }
      });

      // Remove branding spans and links
      sr.querySelectorAll('span.opacity-30').forEach(el => el.remove());
      sr.querySelectorAll('a[href*="elevenlabs.io"]').forEach(el => el.remove());

      // Remove white box wrappers but keep button clickable
      sr.querySelectorAll('.flex.flex-col.p-2.rounded-sheet.bg-base.shadow-md.pointer-events-auto.overflow-hidden').forEach(el => {
        const btn = el.querySelector('button');
        if (btn) {
          const parent = el.parentNode;
          parent.insertBefore(btn, el);
          el.remove();
        } else el.remove();
      });

      // Cleanup styling
      sr.querySelectorAll('.rounded-sheet, .bg-base, .shadow-md').forEach(el => {
        el.style.background = 'transparent';
        el.style.boxShadow = 'none';
        el.style.padding = '0';
        el.style.margin = '0';
        el.style.pointerEvents = 'auto';
      });

    } catch (e) {
      console.warn('[ConvAI cleanup] error removing extras:', e);
    }
  }

  function makeStartButtonCircular(btn) {
    if (!btn) return;
    btn.style.width = "56px";
    btn.style.height = "56px";
    btn.style.borderRadius = "50%";
    btn.style.display = "flex";
    btn.style.alignItems = "center";
    btn.style.justifyContent = "center";
    btn.style.padding = "0";
    btn.style.margin = "8px";
    btn.style.transition = "all 0.2s ease";
    btn.style.pointerEvents = "auto";
    btn.style.cursor = "pointer";
    btn.style.zIndex = "99999";
    const span = btn.querySelector("span");
    if (span) span.style.display = "none";
    btn.disabled = false;
  }

  function hookStartButton(){
    const widget = document.querySelector("elevenlabs-convai");
    if (!widget) return false;
    const sr = widget.shadowRoot;
    if (!sr) return false;

    removeExtras(sr);

    const sels = [
      'button[title="Start a call"]',
      'button[aria-label="Start a call"]',
      'button[title*="Start"]',
      'button[aria-label*="Start"]'
    ];
    for (const sel of sels) {
      const btn = sr.querySelector(sel);
      if (btn && !btn._hooked) {
        btn._hooked = true;
        makeStartButtonCircular(btn);
        interceptStartClick(btn);
        return true;
      }
    }
    return false;
  }

  function interceptStartClick(btn){
    window.__last_call_btn = btn;
    btn.addEventListener("click", (e) => {
      if (ttlActive() && getFormCache()) {
        sendCachedVisitorLog("start_btn_ttl_active");
        return;
      }
      if (btn._allowCall) { btn._allowCall = false; return; }
      e.preventDefault();
      e.stopImmediatePropagation();
      const modal = document.getElementById("convai-visitor-modal");
      if (modal) modal.style.display = "flex";
    }, true);
  }

  function hookEndButton(){
    const widget = document.querySelector("elevenlabs-convai");
    if (!widget) return false;
    const sr = widget.shadowRoot;
    if (!sr) return false;

    let btn = sr.querySelector('button[aria-label="End"], button[title="End"], button[aria-label="End call"], button[title="End call"]');
    if (!btn) {
      const icon = sr.querySelector('slot[name="icon-phone-off"]');
      if (icon) btn = icon.closest('button');
    }
    if (!btn) return false;

    if (!btn.__endHooked) {
      btn.__endHooked = true;
      btn.addEventListener("click", () => {
        setTimeout(() => {
          if (!CONV_ID) return;
          fetch("https://voice-widget-new-production-177d.up.railway.app/fetch-transcript-updated", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              visit_id: VISIT_ID,
              conversation_id: CONV_ID,
              agent_id: AGENT_ID,
              brand: BRAND,
              url: location.href
            }),
            keepalive: true
          }).catch(()=>{});
          console.log("[ConvAI] requested transcript (T+30s) for", CONV_ID);
        }, 30000);
      }, { capture: true });
    }
    return true;
  }

  function setupCallEndHooks(){
    hookEndButton();
    const widget = document.querySelector("elevenlabs-convai");
    const sr = widget && widget.shadowRoot;
    if (!sr) return;
    if (!window.__endBtnObserver){
      window.__endBtnObserver = new MutationObserver(() => { hookEndButton(); });
      window.__endBtnObserver.observe(sr, { childList: true, subtree: true });
    }
  }

  function setupUnloadBeacons(){
    function beacon(){
      if (!CONV_ID) return;
      try {
        const payload = JSON.stringify({
          visit_id: VISIT_ID,
          conversation_id: CONV_ID,
          agent_id: AGENT_ID,
          brand: BRAND,
          url: location.href
        });
        const blob = new Blob([payload], {type: "application/json"});
        navigator.sendBeacon("https://voice-widget-new-production-177d.up.railway.app/fetch-transcript-updated-beacon", blob);
      } catch(_) {}
    }
    window.addEventListener("pagehide", beacon);
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") beacon();
    });
  }

  // --- Create modal ---
  function createVisitorModal(){
    if (document.getElementById("convai-visitor-modal")) return;
    const modal = document.createElement("div");
    modal.id = "convai-visitor-modal";
    modal.style = "display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:999999;align-items:center;justify-content:center;";
    modal.innerHTML = `
      <div style="background:white;border-radius:8px;padding:20px;max-width:400px;width:90%;font-family:sans-serif;">
        <div style="text-align:right;"><button id="convai-close" style="font-size:18px;background:none;border:none;">×</button></div>
        <h3 style="margin-top:0;">Tell us about you</h3>
        <form id="convai-form" style="display:flex;flex-direction:column;gap:10px;">
          <input name="name" placeholder="Full name" required style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <input name="company" placeholder="Company name" required style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <input name="email" type="email" placeholder="Email" required style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <input name="phone" placeholder="Phone" required style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <div style="display:flex;gap:10px;">
            <button type="submit" style="flex:1;padding:10px;background:#007bff;color:white;border:none;border-radius:4px;">Submit</button>
            <button type="button" id="convai-cancel" style="padding:10px;background:#eee;border:none;border-radius:4px;">Cancel</button>
          </div>
        </form>
      </div>
    `;
    document.body.appendChild(modal);
  }

  // --- Load ElevenLabs widget ---
  try {
    const tag = document.createElement("elevenlabs-convai");
    tag.setAttribute("agent-id", AGENT_ID);
    document.body.appendChild(tag);
  } catch (e) {}

  (function loadEmbed(){
    const s = document.createElement("script");
    s.src = "https://unpkg.com/@elevenlabs/convai-widget-embed";
    s.async = true;
    s.onerror = function(){
      const fallback = document.createElement("script");
      fallback.src = "https://elevenlabs.io/convai-widget/index.js";
      fallback.async = true;
      document.body.appendChild(fallback);
    };
    document.body.appendChild(s);
  })();

  createVisitorModal();

  const obs = new MutationObserver(() => { try { if (hookStartButton()) obs.disconnect(); } catch(e){} });
  obs.observe(document, { childList: true, subtree: true });
  let tries = 0;
  const poll = setInterval(() => {
    const ok = hookStartButton();
    if (ok || ++tries > 50) clearInterval(poll);
  }, 300);

})();
    """
    return (js
            .replace("__AGENT_ID__", agent_id)
            .replace("__BRANDING__", branding)
            .replace("__BRAND__", brand))






##########updated end##########
##### --- Core JS serve_widget_js2222222: instant modal + triple-guard injection + per-brand cache key ---
##test end

# --- Serve Branded Widget Scripts ---
@app.route('/sybrant')
def serve_sybrant_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_updated(agent_id, branding="Powered by Sybrant", brand="sybrant")
    return Response(js, mimetype='application/javascript')

@app.route('/leaserush')
def serve_leaserush_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_updated(agent_id, branding="Powered by Leaserush", brand="leaserush")
    return Response(js, mimetype='application/javascript')

@app.route('/successgyan')
def serve_successgyan_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_updated(agent_id, branding="Powered by successgyan", brand="successgyan")
    return Response(js, mimetype='application/javascript')

@app.route('/kfwcorp')
def serve_kfwcorp_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_updated(agent_id, branding="Powered by kfwcorp", brand="kfwcorp")
    return Response(js, mimetype='application/javascript')

@app.route('/myndwell')
def serve_myndwell_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_updated(agent_id, branding="Powered by myndwell", brand="myndwell")
    return Response(js, mimetype='application/javascript')

@app.route('/galent')
def serve_galent_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_updated(agent_id, branding="Powered by galent", brand="galent")
    return Response(js, mimetype='application/javascript')

@app.route('/orientbell')
def serve_orientbell_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_updated(agent_id, branding="Powered by orientbell", brand="orientbell")
    return Response(js, mimetype='application/javascript')

@app.route('/preludesys')
def serve_preludesys_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_updated(agent_id, branding="Powered by preludesys", brand="preludesys")
    return Response(js, mimetype='application/javascript')

@app.route('/cfobridge')
def serve_cfobridge_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_updated(agent_id, branding="Powered by cfobridge", brand="cfobridge")
    return Response(js, mimetype='application/javascript')

@app.route('/newcfobridge')
def serve_newcfobridge_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_updated2(agent_id, branding="Powered by cfobridge", brand="demo")
    return Response(js, mimetype='application/javascript')

@app.route('/voiceassistant')
def serve_voiceassistant_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_updated(agent_id, branding="Powered by sybrant", brand="voiceassistant")
    return Response(js, mimetype='application/javascript')

@app.route('/dhilaktest')
def serve_dhilaktest_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_update_new(agent_id, branding="Powered by dhilaktest", brand="dhilaktest")
    return Response(js, mimetype='application/javascript')

@app.route('/kopiko')
def serve_kopiko_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    # fixed: use existing function
    js = serve_widget_js_updated(agent_id, branding="Powered by kopiko", brand="kopiko")
    return Response(js, mimetype='application/javascript')

@app.route('/ctobridge')
def serve_ctobridge_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_updated(agent_id, branding="Powered by ctobridge", brand="ctobridge")
    return Response(js, mimetype='application/javascript')

@app.route('/demo')
def serve_demo_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js_updated(agent_id, branding="Powered by Sybrant", brand="demo")
    return Response(js, mimetype='application/javascript')

@app.route('/newgendigital')
def serve_newgendigital_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    # fixed: use existing function
    js = serve_widget_js_updated(agent_id, branding="Powered by Newgen", brand="newgendigital")
    return Response(js, mimetype='application/javascript')

########updated method
# ---------- Logging / Transcript (brand-aware) ----------
@app.route('/log-visitor-updated', methods=['POST'])
def log_visitor_updated():
    try:
        data = request.get_json(force=True) or {}
        app.logger.info(">>> /log-visitor-updated")

        event     = (data.get("event") or "").strip()
        visit_id  = (data.get("visit_id") or "").strip()
        name      = (data.get("name") or "").strip()
        email     = (data.get("email") or "").strip()
        phone     = (data.get("phone") or "").strip()
        company   = (data.get("company") or "").strip()
        url       = (data.get("url") or "").strip()
        brand     = (data.get("brand") or "").strip()
        agent_id  = (data.get("agent_id") or "").strip()
        conv_id   = (data.get("conversation_id") or "").strip()
        client_ts = (data.get("timestamp") or data.get("client_timestamp") or "").strip()
        server_ts_ms = int(time.time() * 1000)

        # remember metadata for transcript routing
        if visit_id:
            _VISIT_META[visit_id] = {"brand": brand, "url": url}
        if conv_id:
            _CONV_META[conv_id] = {"brand": brand, "url": url, "visit_id": visit_id}

        if not event:
            event = "conversation_id" if conv_id and not (name or email or phone) else "visitor_log"

        payload = {
            "event": event,
            "visit_id": visit_id,
            "name": name,
            "email": email,
            "phone": phone,
            "company": company,
            "url": url,
            "brand": brand,
            "agent_id": agent_id,
            "conversation_id": conv_id,
            "client_timestamp": client_ts,
            "server_timestamp_ms": server_ts_ms,
        }

        ok, body = _send_to_sheet_brand(payload, brand)

        # schedule background transcript pulls with brand awareness
        if event == "conversation_id" and visit_id and conv_id:
            _schedule_transcript_pull(visit_id, conv_id, agent_id, brand, url)

        return jsonify({"status": "success" if ok else "error", "detail": body[:200]}), (200 if ok else 502)

    except Exception as e:
        app.logger.exception("log_visitor_updated failed")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/fetch-transcript-updated', methods=['POST'])
def fetch_transcript_updated():
    try:
        data = request.get_json(force=True) or {}
        visit_id = (data.get("visit_id") or "").strip()
        conv_id  = (data.get("conversation_id") or "").strip()
        agent_id = (data.get("agent_id") or "").strip()
        brand    = (data.get("brand") or "").strip()
        page_url = (data.get("url") or "").strip()

        # backfill brand/url if missing
        meta = _VISIT_META.get(visit_id) or _CONV_META.get(conv_id) or {}
        brand = brand or (meta.get("brand") or "")
        page_url = page_url or (meta.get("url") or "")

        app.logger.info(">>> /fetch-transcript-updated visit=%s conv=%s brand=%s", visit_id, conv_id, brand or "default")
        if not conv_id:
            return jsonify({"status": "error", "message": "Missing conversation_id"}), 400

        api_key = (os.getenv("ELEVENLABS_API_KEY") or ELEVENLABS_API_KEY).strip()

        last_err = ""
        for _ in range(6):
            txt, duration, err = _pull_transcript(conv_id, api_key)
            if txt:
                _push_transcript_to_sheet(visit_id, conv_id, txt, brand, page_url, duration)
                return jsonify({"status": "success"}), 200
            last_err = err
            time.sleep(2)

        _push_transcript_to_sheet(visit_id, conv_id, f"[TRANSCRIPT_ERROR] {last_err or 'unavailable'}", brand, page_url, None)
        return jsonify({"status": "error", "message": last_err}), 200

    except Exception as e:
        app.logger.exception("/fetch-transcript-updated failed")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/fetch-transcript-updated-beacon', methods=['POST'])
def fetch_transcript_updated_beacon():
    """
    Handles navigator.sendBeacon() payloads during pagehide/unload.
    """
    try:
        raw = request.get_data(as_text=True) or ""
        try:
            data = json.loads(raw)
        except Exception:
            data = request.get_json(silent=True) or {}

        visit_id = (data.get("visit_id") or "").strip()
        conv_id  = (data.get("conversation_id") or "").strip()
        agent_id = (data.get("agent_id") or "").strip()
        brand    = (data.get("brand") or "").strip()
        page_url = (data.get("url") or "").strip()

        # backfill
        meta = _VISIT_META.get(visit_id) or _CONV_META.get(conv_id) or {}
        brand = brand or (meta.get("brand") or "")
        page_url = page_url or (meta.get("url") or "")

        app.logger.info(">>> /fetch-transcript-updated-beacon conv=%s brand=%s", conv_id, brand or "default")
        if conv_id:
            _schedule_transcript_pull(visit_id, conv_id, agent_id, brand, page_url)
        return ("", 204)

    except Exception:
        return ("", 204)

#######updated method end

# Legacy /log-visitor (kept as-is, but unused by new flow)
@app.route('/log-visitor', methods=['POST'])
def log_visitor():
    data = request.json
    brand = data.get("brand", "").lower()

    # These constants are commented out in your file;
    # leaving this legacy route as-is (no-ops if constants are not defined).
    try:
        res = requests.post(BRAND_TO_WEBHOOK.get(brand, BRAND_TO_WEBHOOK["default"]), json=data, timeout=10)
        print(f"[{brand}] Google Sheet Response: {res.text}")
    except Exception as e:
        print(f"Error sending to Google Sheet for brand '{brand}': {e}")

    return {"status": "ok"}

# --- Demo Pages test ---
@app.route('/demo/dhilaktest')
def demo_dhilaktest():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>dhilaktest Voizee Assistant Demo</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 0;
                padding: 0;
                background: #f5f7fa;
            }
            .logo {
                margin-top: 40px;
                background: #181A1C;
            }
            .widget-wrapper {
                margin-top: 60px;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 400px;
                position: relative;
            }
            script + elevenlabs-convai {
                position: absolute !important;
                bottom: 50% !important;
                right: 50% !important;
                transform: translate(50%, 50%) !important;
                z-index: 1000 !important;
            }
        </style>
    </head>
    <body>
        <h2>Test For Voizee Assistant Demo</h2>
        <script src="https://voizee.sybrant.com/dhilaktest?agent=agent_01jx28rjk1ftfvf5c6enxm70te"></script>
    </body>
    </html>
    """
    return render_template_string(html)

# --- Demo Pages start ---
@app.route('/demo/successgyan')
def demo_successgyan():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sybrant Voizee</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- Favicon -->
  <link rel="icon" type="image/png" href="https://successgyan.com/wp-content/uploads/2024/02/cropped-round-favicon-icon.png">

  <style>
    :root {
      --primary: linear-gradient(135deg, #3b82f6, #6366f1);
      --bg-dark: #0f172a;
      --glass-bg: rgba(255, 255, 255, 0.1);
      --glass-border: rgba(255, 255, 255, 0.2);
      --text-light: #e2e8f0;
      --text-muted: #94a3b8;
    }

    body {
      font-family: "Inter", sans-serif;
      margin: 0;
      padding: 0;
      background: var(--bg-dark);
      color: var(--text-light);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      align-items: center;
      justify-content: center;
      overflow-x: hidden;
      position: relative;
    }

    /* Animated background orbs */
    .orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.6;
      animation: float 20s infinite alternate ease-in-out;
      z-index: 0;
    }
    .orb.blue { background: #3b82f6; width: 400px; height: 400px; top: 10%; left: -150px; }
    .orb.indigo { background: #6366f1; width: 500px; height: 500px; bottom: -100px; right: -200px; }

    @keyframes float {
      from { transform: translateY(0) translateX(0); }
      to { transform: translateY(-40px) translateX(30px); }
    }

    /* Main Content */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
      text-align: center;
      z-index: 1;
      max-width: 900px;
      width: 100%;
    }

    /* Header */
    header {
      display: flex;
      justify-content: center;
      margin-bottom: 30px;
    }

    .logo-box {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 14px;
      padding: 16px 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
      position: relative;
      overflow: hidden;
    }
    .logo-box::before {
      content: "";
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(120deg, transparent, rgba(255,255,255,0.3), transparent);
      transform: rotate(25deg);
      animation: shine 4s infinite;
    }
    @keyframes shine {
      from { transform: rotate(25deg) translateX(-100%); }
      to { transform: rotate(25deg) translateX(100%); }
    }
    .logo-box img {
      height: 60px;
      display: block;
      position: relative;
      z-index: 1;
    }

    .title-section {
      margin: 20px 0 30px;
    }
    .title-section h1 {
      font-size: 40px;
      font-weight: 700;
      background: var(--primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0;
    }
    .title-section h2 {
      font-size: 20px;
      font-weight: 500;
      margin: 10px 0;
      color: var(--text-muted);
    }
    .title-section p {
      font-size: 15px;
      margin: 6px 0;
      color: #cbd5e1;
    }

    /* Assistant Container */
    .assistant-container {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.25);
      padding: 30px;
      max-width: 720px;
      width: 95%;
      text-align: center;
      margin-bottom: 40px;
      transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .assistant-container:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 14px 40px rgba(0,0,0,0.4);
    }

    .robot-image {
      margin: 20px 0 40px;
    }
    .robot-image img {
      max-width: 280px;
      width: 100%;
      animation: pulse 6s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.05); opacity: 0.9; }
    }

    /* Footer */
    footer {
      margin-top: auto;
      padding: 20px;
      text-align: center;
      font-size: 13px;
      color: var(--text-muted);
      z-index: 1;
    }
    footer a {
      color: #60a5fa;
      text-decoration: none;
    }
    footer a:hover {
      text-decoration: underline;
    }

    /* Hide widget branding */
    [class*="_status_"] {
      display: none !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .title-section h1 { font-size: 28px; }
      .logo-box img { height: 50px; }
    }
  </style>
</head>
<body>

  <!-- Background Orbs -->
  <div class="orb blue"></div>
  <div class="orb indigo"></div>

  <!-- Main Content -->
  <div class="main-content">
    <header>
      <div class="logo-box">
        <img src="https://successgyan.com/wp-content/uploads/2024/02/SG-logo-1@2x-150x67.png" alt="Logo" />
      </div>
    </header>

    <div class="title-section">
      <h1>Successgyan Voizee Assistant Demo</h1>
      <p>Click <b>"Start a call"</b> and ask your questions.</p>
      <p>We will customize this for your products / services.</p>
    </div>

    <div class="assistant-container">
      <div class="robot-image">
        <img src="https://sybrant.com/wp-content/uploads/2025/08/voizee_sybrant-e1755606750640.png" alt="Voizee Assistant" />
      </div>
      <script src="https://voizee.sybrant.com/demo?agent=agent_3501k18965z0fetshdah8ressxza"></script>
    </div>

    <footer>
      © 2025 Sybrant Technologies · Powered by <a href="https://sybrant.com">Sybrant</a>
    </footer>
  </div>

</body>
</html>
    """
    return render_template_string(html)


@app.route('/demo/kfwcorp')
@app.route('/demo/chrobridge')
def demo_kfwcorp():
    html = """
    <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>kfwcorp Voizee Assistant Demo</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- Favicon -->
  <link rel="icon" type="image/png" href="https://kfwcorp.com/assets/img/tab.png">

  <style>
    :root {
      --primary: linear-gradient(135deg, #3b82f6, #6366f1);
      --bg-dark: #0f172a;
      --glass-bg: rgba(255, 255, 255, 0.1);
      --glass-border: rgba(255, 255, 255, 0.2);
      --text-light: #e2e8f0;
      --text-muted: #94a3b8;
    }

    body {
      font-family: "Inter", sans-serif;
      margin: 0;
      padding: 0;
      background: var(--bg-dark);
      color: var(--text-light);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      align-items: center;
      justify-content: center;
      overflow-x: hidden;
      position: relative;
    }

    /* Animated background orbs */
    .orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.6;
      animation: float 20s infinite alternate ease-in-out;
      z-index: 0;
    }
    .orb.blue { background: #3b82f6; width: 400px; height: 400px; top: 10%; left: -150px; }
    .orb.indigo { background: #6366f1; width: 500px; height: 500px; bottom: -100px; right: -200px; }

    @keyframes float {
      from { transform: translateY(0) translateX(0); }
      to { transform: translateY(-40px) translateX(30px); }
    }

    /* Main Content */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
      text-align: center;
      z-index: 1;
      max-width: 900px;
      width: 100%;
    }

    /* Header */
    header {
      display: flex;
      justify-content: center;
      margin-bottom: 30px;
    }

    .logo-box {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 14px;
      padding: 16px 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
      position: relative;
      overflow: hidden;
    }
    .logo-box::before {
      content: "";
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(120deg, transparent, rgba(255,255,255,0.3), transparent);
      transform: rotate(25deg);
      animation: shine 4s infinite;
    }
    @keyframes shine {
      from { transform: rotate(25deg) translateX(-100%); }
      to { transform: rotate(25deg) translateX(100%); }
    }
    .logo-box img {
      height: 60px;
      display: block;
      position: relative;
      z-index: 1;
    }

    .title-section {
      margin: 20px 0 30px;
    }
    .title-section h1 {
      font-size: 40px;
      font-weight: 700;
      background: var(--primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0;
    }
    .title-section h2 {
      font-size: 20px;
      font-weight: 500;
      margin: 10px 0;
      color: var(--text-muted);
    }
    .title-section p {
      font-size: 15px;
      margin: 6px 0;
      color: #cbd5e1;
    }

    /* Assistant Container */
    .assistant-container {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.25);
      padding: 30px;
      max-width: 720px;
      width: 95%;
      text-align: center;
      margin-bottom: 40px;
      transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .assistant-container:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 14px 40px rgba(0,0,0,0.4);
    }

    .robot-image {
      margin: 20px 0 40px;
    }
    .robot-image img {
      max-width: 280px;
      width: 100%;
      animation: pulse 6s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.05); opacity: 0.9; }
    }

    /* Footer */
    footer {
      margin-top: auto;
      padding: 20px;
      text-align: center;
      font-size: 13px;
      color: var(--text-muted);
      z-index: 1;
    }
    footer a {
      color: #60a5fa;
      text-decoration: none;
    }
    footer a:hover {
      text-decoration: underline;
    }

    /* Hide widget branding */
    [class*="_status_"] {
      display: none !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .title-section h1 { font-size: 28px; }
      .logo-box img { height: 50px; }
    }
  </style>
</head>
<body>

  <!-- Background Orbs -->
  <div class="orb blue"></div>
  <div class="orb indigo"></div>

  <!-- Main Content -->
  <div class="main-content">
    <header>
      <div class="logo-box">
        <img src="https://kfwcorp.com/assets/img/logo-w.png" alt="kfwcorp Logo" />
      </div>
    </header>

    <div class="title-section">
      <h1>KFW Corp Voizee Assistant Demo</h1>
      <p>Click <b>"Start a call"</b> and ask your questions.</p>
      <p>We will customize this for your products / services.</p>
    </div>

    <div class="assistant-container">
      <div class="robot-image">
        <img src="https://sybrant.com/wp-content/uploads/2025/08/voizee_sybrant-e1755606750640.png" alt="Voizee Assistant" />
      </div>
      <script src="https://voizee.sybrant.com/demo?agent=agent_4301k4yjp68seawayd65egj0dwb5"></script>
    </div>

    <footer>
      © 2025 Sybrant Technologies · Powered by <a href="https://sybrant.com">Sybrant</a>
    </footer>
  </div>

</body>
</html>
    """
    return render_template_string(html)


@app.route('/demo/myndwell')
def demo_myndwell():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Myndwell Voizee Assistant Demo</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- Favicon -->
  <link rel="icon" type="image/png" href="https://myndwell.io/_next/static/media/logo.0155ab6c.png">

  <style>
    :root {
      --primary: linear-gradient(135deg, #3b82f6, #6366f1);
      --bg-dark: #0f172a;
      --glass-bg: rgba(255, 255, 255, 0.1);
      --glass-border: rgba(255, 255, 255, 0.2);
      --text-light: #e2e8f0;
      --text-muted: #94a3b8;
    }

    body {
      font-family: "Inter", sans-serif;
      margin: 0;
      padding: 0;
      background: var(--bg-dark);
      color: var(--text-light);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      align-items: center;
      justify-content: center;
      overflow-x: hidden;
      position: relative;
    }

    /* Animated background orbs */
    .orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.6;
      animation: float 20s infinite alternate ease-in-out;
      z-index: 0;
    }
    .orb.blue { background: #3b82f6; width: 400px; height: 400px; top: 10%; left: -150px; }
    .orb.indigo { background: #6366f1; width: 500px; height: 500px; bottom: -100px; right: -200px; }

    @keyframes float {
      from { transform: translateY(0) translateX(0); }
      to { transform: translateY(-40px) translateX(30px); }
    }

    /* Main Content */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
      text-align: center;
      z-index: 1;
      max-width: 900px;
      width: 100%;
    }

    /* Header */
    header {
      display: flex;
      justify-content: center;
      margin-bottom: 30px;
    }

    .logo-box {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 14px;
      padding: 16px 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
      position: relative;
      overflow: hidden;
    }
    .logo-box::before {
      content: "";
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(120deg, transparent, rgba(255,255,255,0.3), transparent);
      transform: rotate(25deg);
      animation: shine 4s infinite;
    }
    @keyframes shine {
      from { transform: rotate(25deg) translateX(-100%); }
      to { transform: rotate(25deg) translateX(100%); }
    }
    .logo-box img {
      height: 60px;
      display: block;
      position: relative;
      z-index: 1;
    }

    .title-section {
      margin: 20px 0 30px;
    }
    .title-section h1 {
      font-size: 40px;
      font-weight: 700;
      background: var(--primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0;
    }
    .title-section h2 {
      font-size: 20px;
      font-weight: 500;
      margin: 10px 0;
      color: var(--text-muted);
    }
    .title-section p {
      font-size: 15px;
      margin: 6px 0;
      color: #cbd5e1;
    }

    /* Assistant Container */
    .assistant-container {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.25);
      padding: 30px;
      max-width: 720px;
      width: 95%;
      text-align: center;
      margin-bottom: 40px;
      transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .assistant-container:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 14px 40px rgba(0,0,0,0.4);
    }

    .robot-image {
      margin: 20px 0 40px;
    }
    .robot-image img {
      max-width: 280px;
      width: 100%;
      animation: pulse 6s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.05); opacity: 0.9; }
    }

    /* Footer */
    footer {
      margin-top: auto;
      padding: 20px;
      text-align: center;
      font-size: 13px;
      color: var(--text-muted);
      z-index: 1;
    }
    footer a {
      color: #60a5fa;
      text-decoration: none;
    }
    footer a:hover {
      text-decoration: underline;
    }

    /* Hide widget branding */
    [class*="_status_"] {
      display: none !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .title-section h1 { font-size: 28px; }
      .logo-box img { height: 50px; }
    }
  </style>
</head>
<body>

  <!-- Background Orbs -->
  <div class="orb blue"></div>
  <div class="orb indigo"></div>

  <!-- Main Content -->
  <div class="main-content">
    <header>
      <div class="logo-box">
        <img src="https://myndwell.io/_next/static/media/logo.0155ab6c.png" alt="Myndwell Logo" />
      </div>
    </header>

    <div class="title-section">
      <h1>Myndwell Voizee Assistant Demo</h1>
      <p>Click <b>"Start a call"</b> and ask your questions.</p>
      <p>We will customize this for your products / services.</p>
    </div>

    <div class="assistant-container">
      <div class="robot-image">
        <img src="https://sybrant.com/wp-content/uploads/2025/08/voizee_sybrant-e1755606750640.png" alt="Voizee Assistant" />
      </div>
      <script src="https://voizee.sybrant.com/demo?agent=agent_0001k4yjr8esecetfyf8pnb4awjb"></script>
    </div>

    <footer>
      © 2025 Sybrant Technologies · Powered by <a href="https://sybrant.com">Sybrant</a>
    </footer>
  </div>

</body>
</html>
 """
    return render_template_string(html)


@app.route('/demo/galent')
def demo_galent():
    html = """
 <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Galent Voizee Assistant Demo</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- Favicon -->
  <link rel="icon" type="image/png" href="https://galent.com/wp-content/themes/twentytwentyone/img/icons/favicon.png">

  <style>
    :root {
      --primary: linear-gradient(135deg, #3b82f6, #6366f1);
      --bg-dark: #0f172a;
      --glass-bg: rgba(255, 255, 255, 0.1);
      --glass-border: rgba(255, 255, 255, 0.2);
      --text-light: #e2e8f0;
      --text-muted: #94a3b8;
    }

    body {
      font-family: "Inter", sans-serif;
      margin: 0;
      padding: 0;
      background: var(--bg-dark);
      color: var(--text-light);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      align-items: center;
      justify-content: center;
      overflow-x: hidden;
      position: relative;
    }

    /* Animated background orbs */
    .orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.6;
      animation: float 20s infinite alternate ease-in-out;
      z-index: 0;
    }
    .orb.blue { background: #3b82f6; width: 400px; height: 400px; top: 10%; left: -150px; }
    .orb.indigo { background: #6366f1; width: 500px; height: 500px; bottom: -100px; right: -200px; }

    @keyframes float {
      from { transform: translateY(0) translateX(0); }
      to { transform: translateY(-40px) translateX(30px); }
    }

    /* Main Content */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
      text-align: center;
      z-index: 1;
      max-width: 900px;
      width: 100%;
    }

    /* Header */
    header {
      display: flex;
      justify-content: center;
      margin-bottom: 30px;
    }

    .logo-box {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 14px;
      padding: 16px 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
      position: relative;
      overflow: hidden;
    }
    .logo-box::before {
      content: "";
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(120deg, transparent, rgba(255,255,255,0.3), transparent);
      transform: rotate(25deg);
      animation: shine 4s infinite;
    }
    @keyframes shine {
      from { transform: rotate(25deg) translateX(-100%); }
      to { transform: rotate(25deg) translateX(100%); }
    }
    .logo-box img {
      height: 60px;
      display: block;
      position: relative;
      z-index: 1;
    }

    .title-section {
      margin: 20px 0 30px;
    }
    .title-section h1 {
      font-size: 40px;
      font-weight: 700;
      background: var(--primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0;
    }
    .title-section h2 {
      font-size: 20px;
      font-weight: 500;
      margin: 10px 0;
      color: var(--text-muted);
    }
    .title-section p {
      font-size: 15px;
      margin: 6px 0;
      color: #cbd5e1;
    }

    /* Assistant Container */
    .assistant-container {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.25);
      padding: 30px;
      max-width: 720px;
      width: 95%;
      text-align: center;
      margin-bottom: 40px;
      transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .assistant-container:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 14px 40px rgba(0,0,0,0.4);
    }

    .robot-image {
      margin: 20px 0 40px;
    }
    .robot-image img {
      max-width: 280px;
      width: 100%;
      animation: pulse 6s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.05); opacity: 0.9; }
    }

    /* Footer */
    footer {
      margin-top: auto;
      padding: 20px;
      text-align: center;
      font-size: 13px;
      color: var(--text-muted);
      z-index: 1;
    }
    footer a {
      color: #60a5fa;
      text-decoration: none;
    }
    footer a:hover {
      text-decoration: underline;
    }

    /* Hide widget branding */
    [class*="_status_"] {
      display: none !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .title-section h1 { font-size: 28px; }
      .logo-box img { height: 50px; }
    }
  </style>
</head>
<body>

  <!-- Background Orbs -->
  <div class="orb blue"></div>
  <div class="orb indigo"></div>

  <!-- Main Content -->
  <div class="main-content">
    <header>
      <div class="logo-box">
        <img src="https://galent.com/wp-content/themes/twentytwentyone/img/icons/galent-nav-logo.svg" alt="Logo" />
      </div>
    </header>

    <div class="title-section">
      <h1>Galent Voizee Assistant Demo</h1>
      <p>Click <b>"Start a call"</b> and ask your questions.</p>
      <p>We will customize this for your products / services.</p>
    </div>

    <div class="assistant-container">
      <div class="robot-image">
        <img src="https://sybrant.com/wp-content/uploads/2025/08/voizee_sybrant-e1755606750640.png" alt="Voizee Assistant" />
      </div>
      <script src="https://voizee.sybrant.com/demo?agent=agent_01k0bxx69dezk91kdpvgj9k8yn"></script>
    </div>

    <footer>
      © 2025 Sybrant Technologies · Powered by <a href="https://sybrant.com">Sybrant</a>
    </footer>
  </div>

</body>
</html>
    """
    return render_template_string(html)


@app.route('/demo/orientbell')
def demo_orientbell():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>OrientBell Voizee Assistant Demo</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- Favicon -->
  <link rel="icon" type="image/png" href="https://tiles.orientbell.com/landingpage/logo/logo.png">

  <style>
    :root {
      --primary: linear-gradient(135deg, #3b82f6, #6366f1);
      --bg-dark: #0f172a;
      --glass-bg: rgba(255, 255, 255, 0.1);
      --glass-border: rgba(255, 255, 255, 0.2);
      --text-light: #e2e8f0;
      --text-muted: #94a3b8;
    }

    body {
      font-family: "Inter", sans-serif;
      margin: 0;
      padding: 0;
      background: var(--bg-dark);
      color: var(--text-light);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      align-items: center;
      justify-content: center;
      overflow-x: hidden;
      position: relative;
    }

    /* Animated background orbs */
    .orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.6;
      animation: float 20s infinite alternate ease-in-out;
      z-index: 0;
    }
    .orb.blue { background: #3b82f6; width: 400px; height: 400px; top: 10%; left: -150px; }
    .orb.indigo { background: #6366f1; width: 500px; height: 500px; bottom: -100px; right: -200px; }

    @keyframes float {
      from { transform: translateY(0) translateX(0); }
      to { transform: translateY(-40px) translateX(30px); }
    }

    /* Main Content */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
      text-align: center;
      z-index: 1;
      max-width: 900px;
      width: 100%;
    }

    /* Header */
    header {
      display: flex;
      justify-content: center;
      margin-bottom: 30px;
    }

    .logo-box {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 14px;
      padding: 16px 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
      position: relative;
      overflow: hidden;
    }
    .logo-box::before {
      content: "";
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(120deg, transparent, rgba(255,255,255,0.3), transparent);
      transform: rotate(25deg);
      animation: shine 4s infinite;
    }
    @keyframes shine {
      from { transform: rotate(25deg) translateX(-100%); }
      to { transform: rotate(25deg) translateX(100%); }
    }
    .logo-box img {
      height: 60px;
      display: block;
      position: relative;
      z-index: 1;
    }

    .title-section {
      margin: 20px 0 30px;
    }
    .title-section h1 {
      font-size: 40px;
      font-weight: 700;
      background: var(--primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0;
    }
    .title-section h2 {
      font-size: 20px;
      font-weight: 500;
      margin: 10px 0;
      color: var(--text-muted);
    }
    .title-section p {
      font-size: 15px;
      margin: 6px 0;
      color: #cbd5e1;
    }

    /* Assistant Container */
    .assistant-container {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.25);
      padding: 30px;
      max-width: 720px;
      width: 95%;
      text-align: center;
      margin-bottom: 40px;
      transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .assistant-container:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 14px 40px rgba(0,0,0,0.4);
    }

    .robot-image {
      margin: 20px 0 40px;
    }
    .robot-image img {
      max-width: 280px;
      width: 100%;
      animation: pulse 6s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.05); opacity: 0.9; }
    }

    /* Footer */
    footer {
      margin-top: auto;
      padding: 20px;
      text-align: center;
      font-size: 13px;
      color: var(--text-muted);
      z-index: 1;
    }
    footer a {
      color: #60a5fa;
      text-decoration: none;
    }
    footer a:hover {
      text-decoration: underline;
    }

    /* Hide widget branding */
    [class*="_status_"] {
      display: none !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .title-section h1 { font-size: 28px; }
      .logo-box img { height: 50px; }
    }
  </style>
</head>
<body>

  <!-- Background Orbs -->
  <div class="orb blue"></div>
  <div class="orb indigo"></div>

  <!-- Main Content -->
  <div class="main-content">
    <header>
      <div class="logo-box">
        <img src="https://tiles.orientbell.com/landingpage/logo/logo.png" alt="Logo" />
      </div>
    </header>

    <div class="title-section">
      <h1>OrientBell Voizee Assistant Demo</h1>
      <p>Click <b>"Start a call"</b> and ask your questions.</p>
      <p>We will customize this for your products / services.</p>
    </div>

    <div class="assistant-container">
      <div class="robot-image">
        <img src="https://sybrant.com/wp-content/uploads/2025/08/voizee_sybrant-e1755606750640.png" alt="Voizee Assistant" />
      </div>
      <script src="https://voizee.sybrant.com/demo?agent=agent_0501k16aqfe5f0xvnp0eg2c532bt"></script>
    </div>

    <footer>
      © 2025 Sybrant Technologies · Powered by <a href="https://sybrant.com">Sybrant</a>
    </footer>
  </div>

</body>
</html>
    """
    return render_template_string(html)    
   

@app.route('/demo/preludesys')
def demo_preludesys():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PreludeSys Voizee Assistant Demo</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- Favicon -->
  <link rel="icon" type="image/png" href="https://preludesys.com/wp-content/themes/preludesys/images/logo.svg">

  <style>
    :root {
      --primary: linear-gradient(135deg, #3b82f6, #6366f1);
      --bg-dark: #0f172a;
      --glass-bg: rgba(255, 255, 255, 0.1);
      --glass-border: rgba(255, 255, 255, 0.2);
      --text-light: #e2e8f0;
      --text-muted: #94a3b8;
    }

    body {
      font-family: "Inter", sans-serif;
      margin: 0;
      padding: 0;
      background: var(--bg-dark);
      color: var(--text-light);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      align-items: center;
      justify-content: center;
      overflow-x: hidden;
      position: relative;
    }

    /* Animated background orbs */
    .orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.6;
      animation: float 20s infinite alternate ease-in-out;
      z-index: 0;
    }
    .orb.blue { background: #3b82f6; width: 400px; height: 400px; top: 10%; left: -150px; }
    .orb.indigo { background: #6366f1; width: 500px; height: 500px; bottom: -100px; right: -200px; }

    @keyframes float {
      from { transform: translateY(0) translateX(0); }
      to { transform: translateY(-40px) translateX(30px); }
    }

    /* Main Content */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
      text-align: center;
      z-index: 1;
      max-width: 900px;
      width: 100%;
    }

    /* Header */
    header {
      display: flex;
      justify-content: center;
      margin-bottom: 30px;
    }

    .logo-box {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 14px;
      padding: 16px 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
      position: relative;
      overflow: hidden;
    }
    .logo-box::before {
      content: "";
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(120deg, transparent, rgba(255,255,255,0.3), transparent);
      transform: rotate(25deg);
      animation: shine 4s infinite;
    }
    @keyframes shine {
      from { transform: rotate(25deg) translateX(-100%); }
      to { transform: rotate(25deg) translateX(100%); }
    }
    .logo-box img {
      height: 60px;
      display: block;
      position: relative;
      z-index: 1;
    }

    .title-section {
      margin: 20px 0 30px;
    }
    .title-section h1 {
      font-size: 40px;
      font-weight: 700;
      background: var(--primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0;
    }
    .title-section h2 {
      font-size: 20px;
      font-weight: 500;
      margin: 10px 0;
      color: var(--text-muted);
    }
    .title-section p {
      font-size: 15px;
      margin: 6px 0;
      color: #cbd5e1;
    }

    /* Assistant Container */
    .assistant-container {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.25);
      padding: 30px;
      max-width: 720px;
      width: 95%;
      text-align: center;
      margin-bottom: 40px;
      transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .assistant-container:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 14px 40px rgba(0,0,0,0.4);
    }

    .robot-image {
      margin: 20px 0 40px;
    }
    .robot-image img {
      max-width: 280px;
      width: 100%;
      animation: pulse 6s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.05); opacity: 0.9; }
    }

    /* Footer */
    footer {
      margin-top: auto;
      padding: 20px;
      text-align: center;
      font-size: 13px;
      color: var(--text-muted);
      z-index: 1;
    }
    footer a {
      color: #60a5fa;
      text-decoration: none;
    }
    footer a:hover {
      text-decoration: underline;
    }

    /* Hide widget branding */
    [class*="_status_"] {
      display: none !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .title-section h1 { font-size: 28px; }
      .logo-box img { height: 50px; }
    }
  </style>
</head>
<body>

  <!-- Background Orbs -->
  <div class="orb blue"></div>
  <div class="orb indigo"></div>

  <!-- Main Content -->
  <div class="main-content">
    <header>
      <div class="logo-box">
        <img src="https://preludesys.com/wp-content/themes/preludesys/images/logo.svg" alt="Logo" />
      </div>
    </header>

    <div class="title-section">
      <h1>PreludeSys Voizee Assistant Demo</h1>
      <p>Click <b>"Start a call"</b> and ask your questions.</p>
      <p>We will customize this for your products / services.</p>
    </div>

    <div class="assistant-container">
      <div class="robot-image">
        <img src="https://sybrant.com/wp-content/uploads/2025/08/voizee_sybrant-e1755606750640.png" alt="Voizee Assistant" />
      </div>
      <script src="https://voizee.sybrant.com/demo?agent=agent_3501k18965z0fetshdah8ressxza"></script>
    </div>

    <footer>
      © 2025 Sybrant Technologies · Powered by <a href="https://sybrant.com">Sybrant</a>
    </footer>
  </div>

</body>
</html>
    """
    return render_template_string(html)    

@app.route('/demo/cfobridge')
def demo_cfobridge():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>CFOBridge Voizee Assistant Demo</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- Favicon -->
  <link rel="icon" type="image/png" href="https://cfobridge.com/assets/images/logo.webp">

  <style>
    :root {
      --primary: linear-gradient(135deg, #3b82f6, #6366f1);
      --bg-dark: #0f172a;
      --glass-bg: rgba(255, 255, 255, 0.1);
      --glass-border: rgba(255, 255, 255, 0.2);
      --text-light: #e2e8f0;
      --text-muted: #94a3b8;
    }

    body {
      font-family: "Inter", sans-serif;
      margin: 0;
      padding: 0;
      background: var(--bg-dark);
      color: var(--text-light);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      align-items: center;
      justify-content: center;
      overflow-x: hidden;
      position: relative;
    }

    /* Animated background orbs */
    .orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.6;
      animation: float 20s infinite alternate ease-in-out;
      z-index: 0;
    }
    .orb.blue { background: #3b82f6; width: 400px; height: 400px; top: 10%; left: -150px; }
    .orb.indigo { background: #6366f1; width: 500px; height: 500px; bottom: -100px; right: -200px; }

    @keyframes float {
      from { transform: translateY(0) translateX(0); }
      to { transform: translateY(-40px) translateX(30px); }
    }

    /* Main Content */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
      text-align: center;
      z-index: 1;
      max-width: 900px;
      width: 100%;
    }

    /* Header */
    header {
      display: flex;
      justify-content: center;
      margin-bottom: 30px;
    }

    .logo-box {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 14px;
      padding: 16px 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
      position: relative;
      overflow: hidden;
    }
    .logo-box::before {
      content: "";
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(120deg, transparent, rgba(255,255,255,0.3), transparent);
      transform: rotate(25deg);
      animation: shine 4s infinite;
    }
    @keyframes shine {
      from { transform: rotate(25deg) translateX(-100%); }
      to { transform: rotate(25deg) translateX(100%); }
    }
    .logo-box img {
      height: 60px;
      display: block;
      position: relative;
      z-index: 1;
    }

    .title-section {
      margin: 20px 0 30px;
    }
    .title-section h1 {
      font-size: 40px;
      font-weight: 700;
      background: var(--primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0;
    }
    .title-section h2 {
      font-size: 20px;
      font-weight: 500;
      margin: 10px 0;
      color: var(--text-muted);
    }
    .title-section p {
      font-size: 15px;
      margin: 6px 0;
      color: #cbd5e1;
    }

    /* Assistant Container */
    .assistant-container {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.25);
      padding: 30px;
      max-width: 720px;
      width: 95%;
      text-align: center;
      margin-bottom: 40px;
      transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .assistant-container:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 14px 40px rgba(0,0,0,0.4);
    }

    .robot-image {
      margin: 20px 0 40px;
    }
    .robot-image img {
      max-width: 280px;
      width: 100%;
      animation: pulse 6s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.05); opacity: 0.9; }
    }

    /* Footer */
    footer {
      margin-top: auto;
      padding: 20px;
      text-align: center;
      font-size: 13px;
      color: var(--text-muted);
      z-index: 1;
    }
    footer a {
      color: #60a5fa;
      text-decoration: none;
    }
    footer a:hover {
      text-decoration: underline;
    }

    /* Hide widget branding */
    [class*="_status_"] {
      display: none !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .title-section h1 { font-size: 28px; }
      .logo-box img { height: 50px; }
    }
  </style>
</head>
<body>

  <!-- Background Orbs -->
  <div class="orb blue"></div>
  <div class="orb indigo"></div>

  <!-- Main Content -->
  <div class="main-content">
    <header>
      <div class="logo-box">
        <img src="https://cfobridge.com/assets/images/logo.webp" alt="Logo" />
      </div>
    </header>

    <div class="title-section">
      <h1>CFOBridge Voizee Assistant Demo</h1>
      <p>Click <b>"Start a call"</b> and ask your questions.</p>
      <p>We will customize this for your products / services.</p>
    </div>

    <div class="assistant-container">
      <div class="robot-image">
        <img src="https://sybrant.com/wp-content/uploads/2025/08/voizee_sybrant-e1755606750640.png" alt="Voizee Assistant" />
      </div>
      <script src="https://voizee.sybrant.com/demo?agent=agent_0001k4yjma29e8hshpq6snzpvy4b"></script>
    </div>

    <footer>
      © 2025 Sybrant Technologies · Powered by <a href="https://sybrant.com">Sybrant</a>
    </footer>
  </div>

</body>
</html>
    """
    return render_template_string(html) 



@app.route('/demo/sybrant')
def demo_sybrant():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sybrant Voizee</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="icon" type="image/png" href="https://sybrant.com/wp-content/uploads/2025/05/cropped-site-logo-180x180.jpg">
  <style>
    :root {
      --primary: linear-gradient(135deg, #3b82f6, #6366f1);
      --bg-dark: #0f172a;
      --glass-bg: rgba(255, 255, 255, 0.1);
      --glass-border: rgba(255, 255, 255, 0.2);
      --text-light: #e2e8f0;
      --text-muted: #94a3b8;
    }

    body {
      font-family: "Inter", sans-serif;
      margin: 0;
      padding: 0;
      background: var(--bg-dark);
      color: var(--text-light);
      display: flex;
      flex-direction: row;
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* Animated background orbs */
    .orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.6;
      animation: float 20s infinite alternate ease-in-out;
      z-index: 0;
    }
    .orb.blue { background: #3b82f6; width: 400px; height: 400px; top: 10%; left: -150px; }
    .orb.indigo { background: #6366f1; width: 500px; height: 500px; bottom: -100px; right: -200px; }

    @keyframes float {
      from { transform: translateY(0) translateX(0); }
      to { transform: translateY(-40px) translateX(30px); }
    }

    /* Sidebar */
    .sidebar {
      width: 260px;
      background: rgba(15, 23, 42, 0.8);
      backdrop-filter: blur(16px);
      border-right: 1px solid var(--glass-border);
      padding: 30px 20px;
      display: flex;
      flex-direction: column;
      gap: 15px;
      position: fixed;
      top: 0; bottom: 0; left: 0;
      z-index: 2;
    }

    .sidebar h3 {
      text-align: center;
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 1px;
      color: #cbd5e1;
    }

    .sidebar a {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--glass-bg);
      color: var(--text-light);
      text-decoration: none;
      padding: 12px 16px;
      border-radius: 10px;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.3s ease;
    }
    .sidebar a:hover {
      background: var(--primary);
      transform: translateX(6px);
    }
    .sidebar a::after {
      content: "↗";
      font-size: 12px;
      opacity: 0.5;
    }

    /* Main Content */
    .main-content {
      margin-left: 280px;
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
      position: relative;
      z-index: 1;
    }

    /* Header */
    header {
      display: flex;
      justify-content: center;
      margin-bottom: 30px;
    }

    .logo-box {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 14px;
      padding: 16px 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
      position: relative;
      overflow: hidden;
    }
    .logo-box::before {
      content: "";
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(120deg, transparent, rgba(255,255,255,0.3), transparent);
      transform: rotate(25deg);
      animation: shine 4s infinite;
    }
    @keyframes shine {
      from { transform: rotate(25deg) translateX(-100%); }
      to { transform: rotate(25deg) translateX(100%); }
    }
    .logo-box img {
      height: 60px;
      display: block;
      position: relative;
      z-index: 1;
    }

    .title-section {
      text-align: center;
      margin: 20px 0 30px;
    }
    .title-section h1 {
      font-size: 40px;
      font-weight: 700;
      background: var(--primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0;
    }
    .title-section h2 {
      font-size: 20px;
      font-weight: 500;
      margin: 10px 0;
      color: var(--text-muted);
    }
    .title-section p {
      font-size: 15px;
      margin: 6px 0;
      color: #cbd5e1;
    }

    /* Assistant Container */
    .assistant-container {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.25);
      padding: 30px;
      max-width: 720px;
      width: 95%;
      text-align: center;
      margin-bottom: 40px;
      transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .assistant-container:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 14px 40px rgba(0,0,0,0.4);
    }

    .robot-image {
      margin: 20px 0 40px;
    }
    .robot-image img {
      max-width: 280px;
      width: 100%;
      animation: pulse 6s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.05); opacity: 0.9; }
    }

    /* Footer */
    footer {
      margin-top: auto;
      padding: 20px;
      text-align: center;
      font-size: 13px;
      color: var(--text-muted);
    }
    footer a {
      color: #60a5fa;
      text-decoration: none;
    }
    footer a:hover {
      text-decoration: underline;
    }

    /* Hide widget branding */
    [class*="_status_"] {
      display: none !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .sidebar { display: none; }
      .main-content { margin-left: 0; padding: 20px; }
      .title-section h1 { font-size: 28px; }
    }
  </style>
</head>
<body>

  <!-- Background Orbs -->
  <div class="orb blue"></div>
  <div class="orb indigo"></div>

  <!-- Sidebar -->
  <div class="sidebar">
    <h3>Voizee for Different Companies</h3>
    <h3>Click to Know More</h2>
    <a href="https://voizee.sybrant.com/demo/cfobridge">CFO Bridge</a>
    <a href="https://voizee.sybrant.com/demo/chrobridge">CHRO Bridge</a>
    <a href="https://voizee.sybrant.com/demo/ctobridge">CTO Bridge</a>
    <a href="https://voizee.sybrant.com/demo/galent">Galent</a>
    <a href="http://voizee.sybrant.com/demo/kopiko">Kopiko</a>
    <a href="https://voizee.sybrant.com/demo/myndwell">Myndwell</a>
    <a href="https://voizee.sybrant.com/demo/orientbell">OrientBell</a>
    <a href="http://voizee.sybrant.com/demo/preludesys">PreludeSys</a>
    <a href="https://voizee.sybrant.com/demo/successgyan">SuccessGyan</a>
    <!-- <a href="https://voizee.sybrant.com/demo/sybrantservices">Sybrant Services</a> -->
  </div>

  <!-- Main Content -->
  <div class="main-content">
    <header>
      <div class="logo-box">
        <img src="https://sybrant.com/wp-content/uploads/2025/05/sybrant.png" alt="Sybrant Logo" />
      </div>
    </header>

    <div class="title-section">
      <h1>Sybrant Voizee</h1>
      <h2>Sales Agent Demo</h2>
      <p>Click <b>"Start a call"</b> and ask your questions about Sybrant Voizee.</p>
      <p>We will customize this for your products / services.</p>
    </div>

    <div class="assistant-container">
      <div class="robot-image">
        <img src="https://sybrant.com/wp-content/uploads/2025/08/voizee_sybrant-e1755606750640.png" alt="Voizee Assistant" />
      </div>
      <script src="https://voizee.sybrant.com/voiceassistant?agent=agent_01jwfxypsyfja9bjqhq5d1zp43"></script>
    </div>

    <footer>
      © 2025 Sybrant Technologies · Powered by <a href="https://sybrant.com">Sybrant</a>
    </footer>
  </div>

</body>
</html>
    """
    return render_template_string(html)


    

@app.route('/demo/ctobridge')
def demo_ctobridge():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>CTOBridge Voizee Assistant Demo</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- Favicon -->
  <link rel="icon" type="image/png" href="https://ctobridge.com/assets/img/logo.png">

  <style>
    :root {
      --primary: linear-gradient(135deg, #3b82f6, #6366f1);
      --bg-dark: #0f172a;
      --glass-bg: rgba(255, 255, 255, 0.1);
      --glass-border: rgba(255, 255, 255, 0.2);
      --text-light: #e2e8f0;
      --text-muted: #94a3b8;
    }

    body {
      font-family: "Inter", sans-serif;
      margin: 0;
      padding: 0;
      background: var(--bg-dark);
      color: var(--text-light);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      align-items: center;
      justify-content: center;
      overflow-x: hidden;
      position: relative;
    }

    /* Animated background orbs */
    .orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.6;
      animation: float 20s infinite alternate ease-in-out;
      z-index: 0;
    }
    .orb.blue { background: #3b82f6; width: 400px; height: 400px; top: 10%; left: -150px; }
    .orb.indigo { background: #6366f1; width: 500px; height: 500px; bottom: -100px; right: -200px; }

    @keyframes float {
      from { transform: translateY(0) translateX(0); }
      to { transform: translateY(-40px) translateX(30px); }
    }

    /* Main Content */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
      text-align: center;
      z-index: 1;
      max-width: 900px;
      width: 100%;
    }

    /* Header */
    header {
      display: flex;
      justify-content: center;
      margin-bottom: 30px;
    }

    .logo-box {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 14px;
      padding: 16px 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
      position: relative;
      overflow: hidden;
    }
    .logo-box::before {
      content: "";
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(120deg, transparent, rgba(255,255,255,0.3), transparent);
      transform: rotate(25deg);
      animation: shine 4s infinite;
    }
    @keyframes shine {
      from { transform: rotate(25deg) translateX(-100%); }
      to { transform: rotate(25deg) translateX(100%); }
    }
    .logo-box img {
      height: 60px;
      display: block;
      position: relative;
      z-index: 1;
    }

    .title-section {
      margin: 20px 0 30px;
    }
    .title-section h1 {
      font-size: 40px;
      font-weight: 700;
      background: var(--primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0;
    }
    .title-section h2 {
      font-size: 20px;
      font-weight: 500;
      margin: 10px 0;
      color: var(--text-muted);
    }
    .title-section p {
      font-size: 15px;
      margin: 6px 0;
      color: #cbd5e1;
    }

    /* Assistant Container */
    .assistant-container {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.25);
      padding: 30px;
      max-width: 720px;
      width: 95%;
      text-align: center;
      margin-bottom: 40px;
      transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .assistant-container:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 14px 40px rgba(0,0,0,0.4);
    }

    .robot-image {
      margin: 20px 0 40px;
    }
    .robot-image img {
      max-width: 280px;
      width: 100%;
      animation: pulse 6s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.05); opacity: 0.9; }
    }

    /* Footer */
    footer {
      margin-top: auto;
      padding: 20px;
      text-align: center;
      font-size: 13px;
      color: var(--text-muted);
      z-index: 1;
    }
    footer a {
      color: #60a5fa;
      text-decoration: none;
    }
    footer a:hover {
      text-decoration: underline;
    }

    /* Hide widget branding */
    [class*="_status_"] {
      display: none !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .title-section h1 { font-size: 28px; }
      .logo-box img { height: 50px; }
    }
  </style>
</head>
<body>

  <!-- Background Orbs -->
  <div class="orb blue"></div>
  <div class="orb indigo"></div>

  <!-- Main Content -->
  <div class="main-content">
    <header>
      <div class="logo-box">
        <img src="https://ctobridge.com/assets/img/logo.png" alt="Logo" />
      </div>
    </header>

    <div class="title-section">
      <h1>CTOBridge Voizee Assistant Demo</h1>
      <p>Click <b>"Start a call"</b> and ask your questions.</p>
      <p>We will customize this for your products / services.</p>
    </div>

    <div class="assistant-container">
      <div class="robot-image">
        <img src="https://sybrant.com/wp-content/uploads/2025/08/voizee_sybrant-e1755606750640.png" alt="Voizee Assistant" />
      </div>
      <script src="https://voizee.sybrant.com/demo?agent=agent_4801k3fnfz4nexdt8mfts31zx0rd"></script>
    </div>

    <footer>
      © 2025 Sybrant Technologies · Powered by <a href="https://sybrant.com">Sybrant</a>
    </footer>
  </div>

</body>
</html>
    """
    return render_template_string(html)

@app.route('/demo/kopiko')
def demo_kopiko():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Kopiko Voizee Assistant Demo</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- Favicon -->
  <link rel="icon" type="image/png" href="https://www.mayora.com/storage/files/new-kopiko-logo.jpg">

  <style>
    :root {
      --primary: linear-gradient(135deg, #3b82f6, #6366f1);
      --bg-dark: #0f172a;
      --glass-bg: rgba(255, 255, 255, 0.1);
      --glass-border: rgba(255, 255, 255, 0.2);
      --text-light: #e2e8f0;
      --text-muted: #94a3b8;
    }

    body {
      font-family: "Inter", sans-serif;
      margin: 0;
      padding: 0;
      background: var(--bg-dark);
      color: var(--text-light);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      align-items: center;
      justify-content: center;
      overflow-x: hidden;
      position: relative;
    }

    /* Animated background orbs */
    .orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.6;
      animation: float 20s infinite alternate ease-in-out;
      z-index: 0;
    }
    .orb.blue { background: #3b82f6; width: 400px; height: 400px; top: 10%; left: -150px; }
    .orb.indigo { background: #6366f1; width: 500px; height: 500px; bottom: -100px; right: -200px; }

    @keyframes float {
      from { transform: translateY(0) translateX(0); }
      to { transform: translateY(-40px) translateX(30px); }
    }

    /* Main Content */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
      text-align: center;
      z-index: 1;
      max-width: 900px;
      width: 100%;
    }

    /* Header */
    header {
      display: flex;
      justify-content: center;
      margin-bottom: 30px;
    }

    .logo-box {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 14px;
      padding: 16px 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
      position: relative;
      overflow: hidden;
    }
    .logo-box::before {
      content: "";
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(120deg, transparent, rgba(255,255,255,0.3), transparent);
      transform: rotate(25deg);
      animation: shine 4s infinite;
    }
    @keyframes shine {
      from { transform: rotate(25deg) translateX(-100%); }
      to { transform: rotate(25deg) translateX(100%); }
    }
    .logo-box img {
      height: 60px;
      display: block;
      position: relative;
      z-index: 1;
    }

    .title-section {
      margin: 20px 0 30px;
    }
    .title-section h1 {
      font-size: 40px;
      font-weight: 700;
      background: var(--primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0;
    }
    .title-section h2 {
      font-size: 20px;
      font-weight: 500;
      margin: 10px 0;
      color: var(--text-muted);
    }
    .title-section p {
      font-size: 15px;
      margin: 6px 0;
      color: #cbd5e1;
    }

    /* Assistant Container */
    .assistant-container {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.25);
      padding: 30px;
      max-width: 720px;
      width: 95%;
      text-align: center;
      margin-bottom: 40px;
      transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .assistant-container:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 14px 40px rgba(0,0,0,0.4);
    }

    .robot-image {
      margin: 20px 0 40px;
    }
    .robot-image img {
      max-width: 280px;
      width: 100%;
      animation: pulse 6s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.05); opacity: 0.9; }
    }

    /* Footer */
    footer {
      margin-top: auto;
      padding: 20px;
      text-align: center;
      font-size: 13px;
      color: var(--text-muted);
      z-index: 1;
    }
    footer a {
      color: #60a5fa;
      text-decoration: none;
    }
    footer a:hover {
      text-decoration: underline;
    }

    /* Hide widget branding */
    [class*="_status_"] {
      display: none !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .title-section h1 { font-size: 28px; }
      .logo-box img { height: 50px; }
    }
  </style>
</head>
<body>

  <!-- Background Orbs -->
  <div class="orb blue"></div>
  <div class="orb indigo"></div>

  <!-- Main Content -->
  <div class="main-content">
    <header>
      <div class="logo-box">
        <img src="https://www.mayora.com/storage/files/new-kopiko-logo.jpg" alt="Logo" />
      </div>
    </header>

    <div class="title-section">
      <h1>Kopiko Voizee Assistant Demo</h1>
      <p>Click <b>"Start a call"</b> and ask your questions.</p>
      <p>We will customize this for your products / services.</p>
    </div>

    <div class="assistant-container">
      <div class="robot-image">
        <img src="https://sybrant.com/wp-content/uploads/2025/08/voizee_sybrant-e1755606750640.png" alt="Voizee Assistant" />
      </div>
      <script src="https://voizee.sybrant.com/kopiko?agent=agent_8601k4mej4mpesm895yv6zhey96y"></script>
    </div>

    <footer>
      © 2025 Sybrant Technologies · Powered by <a href="https://sybrant.com">Sybrant</a>
    </footer>
  </div>

</body>
</html>
    """
    return render_template_string(html)


@app.route('/demo/newgendigital')
def demo_newgendigital():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Newgen Digitalworks Voizee Assistant Demo</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- Favicon -->
  <link rel="icon" type="image/png" href="https://newgendigital.com/img/home/ndw-logo.svg">

  <style>
    :root {
      --primary: linear-gradient(135deg, #3b82f6, #6366f1);
      --bg-dark: #0f172a;
      --glass-bg: rgba(255, 255, 255, 0.1);
      --glass-border: rgba(255, 255, 255, 0.2);
      --text-light: #e2e8f0;
      --text-muted: #94a3b8;
    }

    body {
      font-family: "Inter", sans-serif;
      margin: 0;
      padding: 0;
      background: var(--bg-dark);
      color: var(--text-light);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      align-items: center;
      justify-content: center;
      overflow-x: hidden;
      position: relative;
    }

    /* Animated background orbs */
    .orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.6;
      animation: float 20s infinite alternate ease-in-out;
      z-index: 0;
    }
    .orb.blue { background: #3b82f6; width: 400px; height: 400px; top: 10%; left: -150px; }
    .orb.indigo { background: #6366f1; width: 500px; height: 500px; bottom: -100px; right: -200px; }

    @keyframes float {
      from { transform: translateY(0) translateX(0); }
      to { transform: translateY(-40px) translateX(30px); }
    }

    /* Main Content */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
      text-align: center;
      z-index: 1;
      max-width: 900px;
      width: 100%;
    }

    /* Header */
    header {
      display: flex;
      justify-content: center;
      margin-bottom: 30px;
    }

    .logo-box {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 14px;
      padding: 16px 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
      position: relative;
      overflow: hidden;
    }
    .logo-box::before {
      content: "";
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(120deg, transparent, rgba(255,255,255,0.3), transparent);
      transform: rotate(25deg);
      animation: shine 4s infinite;
    }
    @keyframes shine {
      from { transform: rotate(25deg) translateX(-100%); }
      to { transform: rotate(25deg) translateX(100%); }
    }
    .logo-box img {
      height: 60px;
      display: block;
      position: relative;
      z-index: 1;
    }

    .title-section {
      margin: 20px 0 30px;
    }
    .title-section h1 {
      font-size: 40px;
      font-weight: 700;
      background: var(--primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0;
    }
    .title-section h2 {
      font-size: 20px;
      font-weight: 500;
      margin: 10px 0;
      color: var(--text-muted);
    }
    .title-section p {
      font-size: 15px;
      margin: 6px 0;
      color: #cbd5e1;
    }

    /* Assistant Container */
    .assistant-container {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.25);
      padding: 30px;
      max-width: 720px;
      width: 95%;
      text-align: center;
      margin-bottom: 40px;
      transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .assistant-container:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 14px 40px rgba(0,0,0,0.4);
    }

    .robot-image {
      margin: 20px 0 40px;
    }
    .robot-image img {
      max-width: 280px;
      width: 100%;
      animation: pulse 6s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.05); opacity: 0.9; }
    }

    /* Footer */
    footer {
      margin-top: auto;
      padding: 20px;
      text-align: center;
      font-size: 13px;
      color: var(--text-muted);
      z-index: 1;
    }
    footer a {
      color: #60a5fa;
      text-decoration: none;
    }
    footer a:hover {
      text-decoration: underline;
    }

    /* Hide widget branding */
    [class*="_status_"] {
      display: none !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .title-section h1 { font-size: 28px; }
      .logo-box img { height: 50px; }
    }
  </style>
</head>
<body>

  <!-- Background Orbs -->
  <div class="orb blue"></div>
  <div class="orb indigo"></div>

  <!-- Main Content -->
  <div class="main-content">
    <header>
      <div class="logo-box">
        <img src="https://newgendigital.com/img/home/ndw-logo.svg" alt="Logo" />
      </div>
    </header>

    <div class="title-section">
      <h1>Newgen Digitalworks Voizee Assistant Demo</h1>
      <p>Click <b>"Start a call"</b> and ask your questions.</p>
      <p>We will customize this for your products / services.</p>
    </div>

    <div class="assistant-container">
      <div class="robot-image">
        <img src="https://sybrant.com/wp-content/uploads/2025/08/voizee_sybrant-e1755606750640.png" alt="Voizee Assistant" />
      </div>
      <script src="https://voizee.sybrant.com/newgendigital?agent=agent_0901k71z2tc9fmwszw361tewbwtn"></script>
    </div>

    <footer>
      © 2025 Sybrant Technologies · Powered by <a href="https://sybrant.com">Sybrant</a>
    </footer>
  </div>

</body>
</html>
    """
    return render_template_string(html)

@app.route('/demo/newcfobridge')
def demo_newcfobridge():
    return render_template('cfobridge.html')

# --- Health Check & Root ---
@app.route('/')
def home():
    return "Voice Widget Server Running!"

@app.route('/health')
def health():
    return {"status": "healthy"}

@app.route('/favicon.ico')
def favicon():
    return ('', 204)

# --- Start Server ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
