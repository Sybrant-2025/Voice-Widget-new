from flask import Flask, request, Response
from flask_cors import CORS
from flask import render_template_string
import requests
import os
import datetime
import requests



app = Flask(__name__)
CORS(app)

# --- Constants ---
# GOOGLE_SHEET_WEBHOOK_URL = (
#     'https://script.google.com/macros/s/'
#     'AKfycbwrkqqFYAuoV9_zg1PYSC5Cr134XZ6mD_OqMhjX_oxMq7fzINpMQY46HtxgR0gkj1inPA/exec'
# )

GOOGLE_SHEET_WEBHOOK_URL = 'https://script.google.com/macros/s/AKfycbwrkqqFYAuoV9_zg1PYSC5Cr134XZ6mD_OqMhjX_oxMq7fzINpMQY46HtxgR0gkj1inPA/exec'

GOOGLE_SHEET_WEBHOOK_URL_DEFAULT = 'https://script.google.com/macros/s/AKfycbwrkqqFYAuoV9_zg1PYSC5Cr134XZ6mD_OqMhjX_oxMq7fzINpMQY46HtxgR0gkj1inPA/exec'
GOOGLE_SHEET_WEBHOOK_URL_KFWCORP = 'https://script.google.com/macros/s/AKfycbxy0M-bIHt92nT_FxpyIHXTxqU1UX-bhvoJkVbgfFzb2ZlmY79WUubg2xlvE6pwdus/exec'
GOOGLE_SHEET_WEBHOOK_URL_SUCCESSGYAN = 'https://script.google.com/macros/s/AKfycbyASM8a0kZ649kxqvzmkOiyYbFpdXobDPCUYEF0y3CK-409iEe9dgWnsYp5dhCCOmrLhw/exec'
GOOGLE_SHEET_WEBHOOK_URL_ORIENTBELL = 'https://script.google.com/macros/s/AKfycbzA7qpkwQJBpbXb3-rLWoKzXEuR4wD2gcDY8zzTTeIn00Vu_M7FrAw8n0X26F5meJVCqw/exec'
GOOGLE_SHEET_WEBHOOK_URL_GALENT = 'https://script.google.com/macros/s/AKfycbzZrTfc6KbWz0L98YjhWiID1Wwwhcg4_MLybcKF4plbCYzOcVMQgsPsS-cnPv5nKxVPSw/exec'
GOOGLE_SHEET_WEBHOOK_URL_MYNDWELL = 'https://script.google.com/macros/s/AKfycbz52ul8_xCPMWLfRFuuQxqPfgo_YgpnkPgpdsfSlfE_X17SAoVVCjK0B5efxPhfmrXImA/exec'
GOOGLE_SHEET_WEBHOOK_URL_PRELUDESYS = 'https://script.google.com/macros/s/AKfycbwZpUmj42D_GB3AgxTqSSdQcua2byy5dvFr7dO5jJBhYrUDNhulPj-RxLtWwlz_87T5Pg/exec'
GOOGLE_SHEET_WEBHOOK_URL_CFOBRIDGE = 'https://script.google.com/macros/s/AKfycbwLV_WE3fs1ocw_PhFpWdwC9uASNU2wbD0Uuhk-2WHte5T12c0sWOg2Pq5VtmlAIvDM/exec'
GOOGLE_SHEET_WEBHOOK_URL_SYBRANT = 'https://script.google.com/macros/s/AKfycbxw4RJYQkdWRN3Fu3Vakj5C8h2P-YUN4qJZQrzxjyDk8t2dCY6Wst3wV0pJ2e5h_nn-6Q/exec'

LOG_FILE = "log.txt"

def append_to_log(data, webhook_url):
    """Save visitor data into log.txt (tab separated with webhook_url)"""
    try:
        row = [
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("name", ""),
            data.get("mobile", ""),
            data.get("email", ""),
            data.get("url", ""),
            data.get("brand", ""),
            webhook_url
        ]
        line = "    ".join(row)  # 4 spaces
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print("Error writing to log file:", e)


def read_log():
    """Read log.txt into list of dicts"""
    if not os.path.exists(LOG_FILE):
        return []
    entries = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("    ")
            if len(parts) >= 7:
                entries.append({
                    "timestamp": parts[0],
                    "name": parts[1],
                    "mobile": parts[2],
                    "email": parts[3],
                    "url": parts[4],
                    "brand": parts[5],
                    "webhook_url": parts[6]
                })
    return entries


def write_log(entries):
    """Rewrite log.txt with pending (unsent) entries"""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for e in entries:
            row = [
                e.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                e.get("name", ""),
                e.get("mobile", ""),
                e.get("email", ""),
                e.get("url", ""),
                e.get("brand", ""),
                e.get("webhook_url", "")
            ]
            f.write("    ".join(row) + "\n")





# def generate_widget_js(agent_id, branding, brand=""):
#     return f"""
#     (function() {{
#         const CACHE_HOURS = 8;
#         const CACHE_MS = CACHE_HOURS * 60 * 60 * 1000;

#         // --- Branding Removal ---
#         const preloadStyle = document.createElement("style");
#         preloadStyle.textContent = `
#             [class*="poweredBy"],
#             div[part="branding"],
#             span:has(a[href*="elevenlabs"]),
#             a[href*="elevenlabs"],
#             [class*="_poweredBy_"],
#             [class*="branding"],
#             [class*="_status_1968y_121"],
#             div[class*="branding"] {{
#                 display: none !important;
#                 opacity: 0 !important;
#                 visibility: hidden !important;
#                 height: 0 !important;
#                 font-size: 0 !important;
#                 line-height: 0 !important;
#                 pointer-events: none !important;                
#             }}
#         `;
#         document.head.appendChild(preloadStyle);

#         // --- Load Widget ---
#         const tag = document.createElement("elevenlabs-convai");
#         tag.setAttribute("agent-id", "{agent_id}");
#         document.body.appendChild(tag);

#         const script = document.createElement("script");
#         script.src = "https://elevenlabs.io/convai-widget/index.js";
#         script.async = true;
#         document.body.appendChild(script);

#         // --- Helper: log visitor ---
#         function logVisitor(fromForm, formData) {{
#             const url = window.location.href;
#             let payload;

#             if (fromForm) {{
#                 payload = {{ ...formData, url, brand: "{brand}" }};
#             }} else {{
#                 payload = {{ url, brand: "{brand}" }}; // minimal log
#             }}

#             fetch('https://voice-widget-new-production-177d.up.railway.app/log-visitor', {{
#                 method: 'POST',
#                 headers: {{ 'Content-Type': 'application/json' }},
#                 body: JSON.stringify(payload)
#             }});
#         }}

#         // --- Observe DOM for widget load ---
#         const observer = new MutationObserver(() => {{
#             const widget = document.querySelector('elevenlabs-convai');
#             if (!widget || !widget.shadowRoot) return;
#             const shadowRoot = widget.shadowRoot;

#             // Remove branding inside shadow DOM
#             shadowRoot.querySelectorAll('[class*="poweredBy"], div[part="branding"]').forEach(el => el.remove());

#             // Apply custom CSS if not added
#             if (!shadowRoot.querySelector("#custom-style")) {{
#                 const style = document.createElement("style");
#                 style.id = "custom-style";
#                 style.textContent = `
#                     [class*="_avatar_"] {{ display: none !important; }}
#                     div[part='feedback-button'],
#                     img[alt*='logo'] {{ display: none !important; }}
#                 `;
#                 shadowRoot.appendChild(style);
#             }}

#             // Hook Start Call button
#             setTimeout(() => {{
#                 const startCallButton = shadowRoot.querySelector('button[title="Start a call"]');
#                 if (startCallButton && !startCallButton._hooked) {{
#                     startCallButton._hooked = true;

#                     const clonedButton = startCallButton.cloneNode(true);
#                     startCallButton.style.display = 'none';

#                     // Apply custom style except for cfo bridge
#                     if ("{brand}".toLowerCase() !== "cfobridge") {{
#                         clonedButton.style.cssText = `
#                             background-color: #0b72e7;
#                             color: #fff;
#                             border: none;
#                             padding: 12px 20px;
#                             border-radius: 8px;
#                             cursor: pointer;
#                             font-weight: 600;
#                             font-size: 15px;
#                         `;
#                     }}

#                     const wrapper = document.createElement('div');
#                     wrapper.appendChild(clonedButton);
#                     startCallButton.parentElement.appendChild(wrapper);

#                     clonedButton.addEventListener('click', (e) => {{
#                         e.stopPropagation();
#                         e.preventDefault();
#                         const key = "convai_form_submitted_" + "{brand}";
#                         const expiry = localStorage.getItem(key);

#                         if (expiry && Date.now() < parseInt(expiry)) {{
#                             // Already filled in last 8h → still log again
#                             logVisitor(false);
#                             startCallButton.click();
#                         }} else {{
#                             // Show form
#                             document.getElementById('visitor-form-modal').style.display = 'flex';
#                         }}
#                     }});
#                 }}
#             }}, 100);
#         }});
#         observer.observe(document.body, {{ childList: true, subtree: true }});

#         // --- Visitor Form Modal ---
#         window.addEventListener('DOMContentLoaded', () => {{
#             const modal = document.createElement('div');
#             modal.id = 'visitor-form-modal';
#             modal.style = `
#                 display: none;
#                 position: fixed;
#                 z-index: 99999;
#                 top: 0; left: 0; width: 100%; height: 100%;
#                 background: rgba(0, 0, 0, 0.6);
#                 align-items: center;
#                 justify-content: center;
#             `;

#             modal.innerHTML = `
#                 <div style="background: white; padding: 25px; border-radius: 12px; width: 320px; position: relative;">
#                     <span id="close-form" style="position: absolute; top: 8px; right: 12px; cursor: pointer;">&times;</span>
#                     <form id="visitor-form">
#                         <h3 style="margin-bottom: 15px;">Tell us about you</h3>
#                         <input type="text" name="name" placeholder="Name" required style="margin-bottom:10px;width:100%;padding:8px;" />
#                         <input type="tel" name="mobile" placeholder="Mobile (+91...)" required style="margin-bottom:10px;width:100%;padding:8px;" />
#                         <input type="email" name="email" placeholder="Email" required style="margin-bottom:20px;width:100%;padding:8px;" />
#                         <button type="submit" style="width:100%;padding:10px;background:#1e88e5;color:#fff;border:none;border-radius:6px;">Start Call</button>
#                     </form>
#                 </div>
#             `;
#             document.body.appendChild(modal);

#             const modalEl = document.getElementById('visitor-form-modal');
#             document.getElementById('close-form').onclick = () => modalEl.style.display = 'none';
#             window.onclick = (e) => {{ if (e.target === modalEl) modalEl.style.display = 'none'; }};

#             document.getElementById('visitor-form').addEventListener('submit', function(e) {{
#                 e.preventDefault();

#                 const name = this.name.value.trim();
#                 const mobile = this.mobile.value.trim();
#                 const email = this.email.value.trim();

#                 if (!name || !mobile || !email) {{
#                     alert("Please fill all fields.");
#                     return;
#                 }}

#                 const formData = {{ name, mobile, email }};
#                 logVisitor(true, formData);

#                 // Save brand-specific cache for 8h
#                 const key = "convai_form_submitted_" + "{brand}";
#                 localStorage.setItem(key, (Date.now() + CACHE_MS).toString());

#                 modalEl.style.display = 'none';
#                 const widget = document.querySelector('elevenlabs-convai');
#                 widget?.shadowRoot?.querySelector('button[title="Start a call"]')?.click();
#             }});
#         }});
#     }})();
#     """

# --- Core JS generator: instant modal + triple-guard injection + per-brand cache key ---
def generate_widget_js1(agent_id, brand=""):
    # NOTE: we set brand to lowercase for keys but preserve original for display
    brand_key = (brand or "").lower()
    # 8 hours cache TTL
    CACHE_MS = 8 * 60 * 60 * 1000

    return f"""
(function(){{
  const BRAND = "{brand_key}";
  const CACHE_MS = {CACHE_MS};

  // Prevent showing any branding ASAP (outside Shadow DOM)
  const preloadStyle = document.createElement("style");
  preloadStyle.textContent = `
    [class*="poweredBy"],
    div[part="branding"],
    span:has(a[href*="elevenlabs"]),
    a[href*="elevenlabs"],
    span:has([href*="conversational"]),
    a[href*="conversational"],
    [class*="_poweredBy_"],
    [class*="branding"],
    [class*="_status_"], /* defensive */
    div[class*="branding"] {{
      display:none !important; opacity:0 !important; visibility:hidden !important;
      height:0 !important; font-size:0 !important; line-height:0 !important; pointer-events:none !important;
    }}
  `;
  document.head.appendChild(preloadStyle);

  // Inject widget tag early
  const tag = document.createElement("elevenlabs-convai");
  tag.setAttribute("agent-id", "{agent_id}");
  document.body.appendChild(tag);

  // Create modal immediately (instant availability)
  (function injectModal(){{
    if (document.getElementById("visitor-form-modal")) return;
    const modal = document.createElement('div');
    modal.id = 'visitor-form-modal';
    modal.style = `
      display:none; position:fixed; z-index:99999; inset:0;
      background: rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center;
    `;
    modal.innerHTML = `
      <div id="form-container" style="
        background:#fff; padding:24px; border-radius:12px; width:92%; max-width:360px;
        box-shadow:0 10px 30px rgba(0,0,0,0.2); position:relative; font-family:system-ui, -apple-system, Segoe UI, Roboto, Arial;
        animation: voizeeFadeIn .25s ease;
      ">
        <style>
          @keyframes voizeeFadeIn {{ from {{opacity:0; transform:scale(.96)}} to {{opacity:1; transform:scale(1)}} }}
          .vz-input {{ width:100%; padding:10px; border:1px solid #e0e0e0; border-radius:8px; margin:8px 0; font-size:14px; }}
          .vz-btn {{ width:100%; padding:12px; border:none; border-radius:10px; font-weight:600; cursor:pointer; }}
          .vz-btn-primary {{ background:#0b72e7; color:#fff; }}
          .vz-close {{ position:absolute; top:8px; right:12px; cursor:pointer; font-size:18px; font-weight:700; }}
        </style>
        <span id="close-form" class="vz-close">&times;</span>
        <form id="visitor-form">
          <h3 style="margin:0 0 12px 0; font-size:18px;">Tell us about you</h3>
          <input class="vz-input" type="text" name="name" placeholder="Name" required />
          <input class="vz-input" type="tel" name="mobile" placeholder="Mobile (+91...)" required />
          <input class="vz-input" type="email" name="email" placeholder="Email" required />
          <button class="vz-btn vz-btn-primary" type="submit">Start Call</button>
        </form>
      </div>
    `;
    document.body.appendChild(modal);

    const modalEl = modal;
    const closeEl = modal.querySelector('#close-form');
    closeEl.onclick = () => modalEl.style.display = 'none';
    window.addEventListener('click', (e) => {{ if (e.target === modalEl) modalEl.style.display = 'none'; }});

    const form = modal.querySelector('#visitor-form');
    form.addEventListener('submit', function(e){{
      e.preventDefault();
      const name = this.name.value.trim();
      const mobile = this.mobile.value.trim();
      const email = this.email.value.trim();
      const url = window.location.href;

      if(!name || !mobile || !email) {{ alert('Please fill all fields.'); return; }}

      // Immediate send to server (first-try success path)
      fetch('{request.host_url.rstrip("/")}/log-visitor', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ name, mobile, email, url, brand: BRAND }})
      }}).catch(()=>{{}});

      // brand-specific cache key for 8h
      const key = "convai_form_submitted_" + BRAND;
      localStorage.setItem(key, (Date.now() + {CACHE_MS}).toString());

      modalEl.style.display = 'none';
      // Click native start button
      const widget = document.querySelector('elevenlabs-convai');
      const btn = widget?.shadowRoot?.querySelector('button[title="Start a call"]');
      btn?.click();
    }});
  }})();

  // Load ElevenLabs script
  const script = document.createElement("script");
  script.src = "https://elevenlabs.io/convai-widget/index.js";
  script.async = true;

  script.onload = () => {{
    // As soon as script is ready, start attaching handlers
    attachHandlers();
    startBrandingRemovalGuards();
  }};

  document.body.appendChild(script);

  // Repeated + observed branding removal (triple-guard)
  function startBrandingRemovalGuards(){{
    // 1) Interval attempts
    let tries = 0;
    const iv = setInterval(() => {{
      if (removeBranding()) {{
        tries++;
        if (tries > 5) clearInterval(iv); // after multiple successes, stop interval
      }} else {{
        if (tries > 40) clearInterval(iv); // ~12s cap
        tries++;
      }}
    }}, 300);

    // 2) MutationObserver
    const mo = new MutationObserver(() => removeBranding());
    mo.observe(document.body, {{ childList: true, subtree: true }});
  }}

  function removeBranding(){{
    const widget = document.querySelector('elevenlabs-convai');
    const shadow = widget?.shadowRoot;
    if(!shadow) return false;

    // Nuke common branding nodes
    shadow.querySelectorAll('[class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"], span:has(a[href*="elevenlabs"])')
      .forEach(el => el.remove());

    // Defensive: hide any status/footer boxes that mention ElevenLabs
    shadow.querySelectorAll('[class*="_box_"], [class*="_status_"]').forEach(el => {{
      if ((el.textContent || "").toLowerCase().includes("elevenlabs")) el.remove();
    }});

    // Inject style once
    if(!shadow.querySelector("#vz-style")) {{
      const style = document.createElement("style");
      style.id = "vz-style";
      style.textContent = `
        [class*="_avatar_"] {{ display:none !important; }}
        div[part='feedback-button'], img[alt*='logo'] {{ display:none !important; }}
        [class*="_box_"] {{
          background: transparent !important; box-shadow: none !important; border: none !important;
          padding: 0 !important; margin: 0 !important; display:flex !important; align-items:center !important; justify-content:center !important;
        }}
      `;
      shadow.appendChild(style);
    }}

    return true;
  }}

  function attachHandlers(){{
    const widget = document.querySelector('elevenlabs-convai');
    if(!widget) return;

    // Poll shadow until native button exists, then wrap/clone
    let attempts = 0;
    const poll = setInterval(() => {{
      const shadow = widget.shadowRoot;
      const startCallButton = shadow?.querySelector('button[title="Start a call"]');
      if (startCallButton) {{
        clearInterval(poll);
        hookStartButton(startCallButton);
      }} else if (++attempts > 50) {{
        clearInterval(poll);
      }}
    }}, 200);
  }}

  function hookStartButton(nativeBtn){{
    if (nativeBtn._vzHooked) return;
    nativeBtn._vzHooked = true;

    const clone = nativeBtn.cloneNode(true);
    nativeBtn.style.display = 'none';

    // Styling: CFOBridge special; others unified
    if (BRAND === "cfobridge") {{
      Object.assign(clone.style, {{
        backgroundColor: "#0b72e7", color:"#fff", border:"none",
        padding:"14px 28px", borderRadius:"8px", fontSize:"16px",
        fontWeight:"bold", boxShadow:"0 4px 12px rgba(0,0,0,0.2)", cursor:"pointer"
      }});
    }} else {{
      Object.assign(clone.style, {{
        backgroundColor: "#0b72e7", color:"#fff", border:"none",
        padding:"12px 20px", borderRadius:"24px", fontSize:"15px",
        fontWeight:"600", cursor:"pointer"
      }});
    }}

    const wrapper = document.createElement("div");
    wrapper.appendChild(clone);
    nativeBtn.parentElement.appendChild(wrapper);

    clone.addEventListener('click', (e) => {{
      e.preventDefault(); e.stopPropagation();
      const key = "convai_form_submitted_" + BRAND;
      const expiry = localStorage.getItem(key);

      if (expiry && Date.now() < parseInt(expiry)) {{
        nativeBtn.click(); // direct start
      }} else {{
        // open modal instantly
        const modal = document.getElementById('visitor-form-modal');
        if (modal) modal.style.display = 'flex';
      }}
    }});
  }}
}})();
"""

# --- Helper to add "no-store" cache headers for widget JS endpoints ---
def no_store(response: Response) -> Response:
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response



# --- JS Generator ---
def generate_widget_js(agent_id, branding, brand=""):
    return f"""
    (function() {{
        // Immediately apply global CSS to hide branding early (before widget loads)
        const preloadStyle = document.createElement("style");
        preloadStyle.textContent = `
            [class*="poweredBy"],
            div[part="branding"],
            span:has(a[href*="elevenlabs"]),
            a[href*="elevenlabs"],
            span:has([href*="conversational"]),
            a[href*="conversational"],
            [class*="_poweredBy_"],
            [class*="branding"],
            div[class*="branding"],
            div[part="branding"] {{
                display: none !important;
                opacity: 0 !important;
                visibility: hidden !important;
                height: 0 !important;
                font-size: 0 !important;
                line-height: 0 !important;
                pointer-events: none !important;                
            }}
            div[part="branding"],
            [class*="_status_1968y_121"] {{
                display: none !important;
                opacity: 0 !important;
                visibility: hidden !important;
                height: 0 !important;
                font-size: 0 !important;
                line-height: 0 !important;
                pointer-events: none !important;
            }}
        `;
        document.head.appendChild(preloadStyle);

        // Inject the widget tag
        const tag = document.createElement("elevenlabs-convai");
        tag.setAttribute("agent-id", "{agent_id}");
        document.body.appendChild(tag);

        // Inject widget script
        const script = document.createElement("script");
        script.src = "https://elevenlabs.io/convai-widget/index.js";
        script.async = true;
        document.body.appendChild(script);

        // Observe the DOM for widget load and apply custom styles
        const observer = new MutationObserver(() => {{
            const widget = document.querySelector('elevenlabs-convai');
            if (!widget || !widget.shadowRoot) return;
            const shadowRoot = widget.shadowRoot;

            // Try to forcibly remove branding again if found inside Shadow DOM
            const brandingElem = shadowRoot.querySelector('[class*="poweredBy"], div[part="branding"]');
            if (brandingElem) {{
                brandingElem.remove(); // REMOVE instead of customizing
            }}

            if (!shadowRoot.querySelector("#custom-style")) {{
                const style = document.createElement("style");
                style.id = "custom-style";
                style.textContent = `
                    div[part='branding'],
                    a[href*="elevenlabs"],
                    span:has(a[href*="elevenlabs"]) {{
                        display: none !important;
                    }}

                    [class*="_avatar_"] {{
                        display: none !important;
                    }}

                    [class*="_box_"] {{
                        background: transparent !important;
                        box-shadow: none !important;
                        border: none !important;
                        padding: 0 !important;
                        margin: 0 !important;
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                    }}

                    [class*="_btn_"] {{
                        border-radius: 30px !important;
                        padding: 10px 20px !important;
                        background-color: #0b72e7 !important;
                        color: #fff !important;
                        border: none !important;
                        cursor: pointer !important;
                        font-weight: 500;
                        font-size: 14px;
                    }}

                    div[part='feedback-button'],
                    img[alt*='logo'] {{
                        display: none !important;
                    }}
                `;
                shadowRoot.appendChild(style);
            }}

            const startCallButton = shadowRoot.querySelector('button[title="Start a call"]');
            if (startCallButton && !startCallButton._hooked) {{
                startCallButton._hooked = true;
                const clonedButton = startCallButton.cloneNode(true);
                startCallButton.style.display = 'none';

                clonedButton.style.backgroundColor = "#0b72e7";
                clonedButton.style.color = "#fff";
                clonedButton.style.border = "none";
                clonedButton.style.padding = "10px 20px";
                clonedButton.style.borderRadius = "6px";
                clonedButton.style.cursor = "pointer";

                const wrapper = document.createElement('div');
                wrapper.appendChild(clonedButton);
                startCallButton.parentElement.appendChild(wrapper);

                clonedButton.addEventListener('click', (e) => {{
                    e.stopPropagation();
                    e.preventDefault();
                    const expiry = localStorage.getItem("convai_form_submitted");
                    if (expiry && Date.now() < parseInt(expiry)) {{
                        startCallButton.click();
                    }} else {{
                        document.getElementById('visitor-form-modal').style.display = 'flex';
                    }}
                }});
            }}
        }});
        observer.observe(document.body, {{ childList: true, subtree: true }});

        // Visitor form modal logic
        window.addEventListener('DOMContentLoaded', () => {{
            const modal = document.createElement('div');
            modal.id = 'visitor-form-modal';
            modal.style = `
                display: none;
                position: fixed;
                z-index: 99999;
                top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.6);
                align-items: center;
                justify-content: center;
            `;

            modal.innerHTML = `
                <div id="form-container" style="
                    background: white;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    width: 320px;
                    font-family: sans-serif;
                    position: relative;
                ">
                    <span id="close-form" style="
                        position: absolute;
                        top: 8px;
                        right: 12px;
                        cursor: pointer;
                        font-size: 18px;
                        font-weight: bold;
                    ">&times;</span>

                    <form id="visitor-form">
                        <h3 style="margin-bottom: 15px;">Tell us about you</h3>
                        <input type="text" placeholder="Name" name="name" required style="margin-bottom: 10px; width: 100%; padding: 8px;" />
                        <input type="tel" placeholder="Mobile (+91...)" name="mobile" required style="margin-bottom: 10px; width: 100%; padding: 8px;" />
                        <input type="email" placeholder="Email" name="email" required style="margin-bottom: 20px; width: 100%; padding: 8px;" />
                        <button type="submit" style="width: 100%; padding: 10px; background: #1e88e5; color: white; border: none; border-radius: 4px;">Start Call</button>
                    </form>
                </div>
            `;
            document.body.appendChild(modal);

            const modalEl = document.getElementById('visitor-form-modal');
            const closeForm = document.getElementById('close-form');

            closeForm.onclick = () => modalEl.style.display = 'none';
            window.onclick = (e) => {{
                if (e.target === modalEl) modalEl.style.display = 'none';
            }};

            document.getElementById('visitor-form').addEventListener('submit', function(e) {{
                e.preventDefault();

                const name = this.name.value.trim();
                const mobile = this.mobile.value.trim();
                const email = this.email.value.trim();
                const url = window.location.href;

                if (!name || !mobile || !email) {{
                    alert("Please fill all fields.");
                    return;
                }}

                fetch('https://voice-widget-new-production-177d.up.railway.app/log-visitor', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ name, mobile, email, url, brand: "{brand}" }})
                }});

                localStorage.setItem("convai_form_submitted", (Date.now() + 86400000).toString());
                modalEl.style.display = 'none';

                const widget = document.querySelector('elevenlabs-convai');
                const realBtn = widget?.shadowRoot?.querySelector('button[title="Start a call"]');
                realBtn?.click();
            }});
        }});
    }})();
    """


# --- Serve Branded Widget Scripts ---
@app.route('/convai-widget.js')
def serve_sybrant_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by Sybrant")
    return Response(js, mimetype='application/javascript')

@app.route('/successgyan')
def serve_successgyan_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by successgyan", brand="successgyan")
    return Response(js, mimetype='application/javascript')

@app.route('/kfwcorp')
def serve_kfwcorp_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by kfwcorp", brand="kfwcorp")
    return Response(js, mimetype='application/javascript')

@app.route('/myndwell')
def serve_myndwell_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by myndwell", brand="myndwell")
    return Response(js, mimetype='application/javascript')

@app.route('/galent')
def serve_galent():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by galent", brand="galent")
    return Response(js, mimetype='application/javascript')


@app.route('/orientbell')
def serve_orientbell():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by orientbell", brand="orientbell")
    return Response(js, mimetype='application/javascript')

@app.route('/preludesys')
def serve_preludesys():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by preludesys", brand="preludesys")
    return Response(js, mimetype='application/javascript')

@app.route('/cfobridge')
def serve_cfobridge():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by cfobridge", brand="cfobridge")
    return Response(js, mimetype='application/javascript')

@app.route('/sybrant')
def serve_sybrant():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by cfobridge", brand="sybrant")
    return Response(js, mimetype='application/javascript')

def get_webhook_url(brand):
    brand = (brand or "").lower()
    if brand == "successgyan":
        return GOOGLE_SHEET_WEBHOOK_URL_SUCCESSGYAN
    elif brand == "kfwcorp":
        return GOOGLE_SHEET_WEBHOOK_URL_KFWCORP
    elif brand == "orientbell":
        return GOOGLE_SHEET_WEBHOOK_URL_ORIENTBELL
    elif brand == "galent":
        return GOOGLE_SHEET_WEBHOOK_URL_GALENT
    elif brand == "myndwell":
        return GOOGLE_SHEET_WEBHOOK_URL_MYNDWELL
    elif brand == "preludesys":
        return GOOGLE_SHEET_WEBHOOK_URL_PRELUDESYS
    elif brand == "cfobridge":
        return GOOGLE_SHEET_WEBHOOK_URL_CFOBRIDGE
    elif brand == "sybrant":
        return GOOGLE_SHEET_WEBHOOK_URL_SYBRANT
    else:
        return GOOGLE_SHEET_WEBHOOK_URL_DEFAULT


@app.route('/log-visitor', methods=['POST'])
def log_visitor():
    data = request.json
    brand = data.get("brand", "").lower()
    webhook_url = get_webhook_url(brand)

    # --- Always log first (with webhook_url) ---
    append_to_log(data, webhook_url)

    # --- Retry sending all entries (including new one) ---
    all_entries = read_log()
    remaining = []

    for entry in all_entries:
        try:
            res = requests.post(entry["webhook_url"], json=entry, timeout=10)
            if res.status_code == 200:
                print(f"[{entry['brand']}] Sent to Google Sheet: {entry}")
            else:
                print(f"[{entry['brand']}] Failed {res.status_code}, keeping in log")
                remaining.append(entry)
        except Exception as e:
            print(f"Error sending to Google Sheet for {entry['brand']}: {e}")
            remaining.append(entry)

    # Keep only unsent
    write_log(remaining)

    return jsonify({"status": "ok", "pending": len(remaining)})



# --- Form Submission Logging ---
# @app.route('/log-visitor', methods=['POST'])
# def log_visitor():
#     data = request.json
#     print("Visitor Info:", data)
#     try:
#         res = requests.post(GOOGLE_SHEET_WEBHOOK_URL, json=data)
#         print("Google Sheet Response:", res.text)
#     except Exception as e:
#         print("Error sending to Google Sheet:", e)
#     return {"status": "ok"}


# @app.route('/log-visitor', methods=['POST'])
# def log_visitor():
#     data = request.json
#     brand = data.get("brand", "").lower()

#     if brand == "successgyan":
#         webhook_url = GOOGLE_SHEET_WEBHOOK_URL_SUCCESSGYAN
#     elif brand == "kfwcorp":
#         webhook_url = GOOGLE_SHEET_WEBHOOK_URL_KFWCORP
#     elif brand == "orientbell":
#         webhook_url = GOOGLE_SHEET_WEBHOOK_URL_ORIENTBELL
#     elif brand == "galent":
#         webhook_url = GOOGLE_SHEET_WEBHOOK_URL_GALENT
#     elif brand == "myndwell":
#         webhook_url = GOOGLE_SHEET_WEBHOOK_URL_MYNDWELL
#     elif brand == "preludesys":
#         webhook_url = GOOGLE_SHEET_WEBHOOK_URL_PRELUDESYS
#     elif brand == "cfobridge":
#         webhook_url = GOOGLE_SHEET_WEBHOOK_URL_CFOBRIDGE
#     elif brand == "sybrant":
#         webhook_url = GOOGLE_SHEET_WEBHOOK_URL_SYBRANT
#     else:
#         webhook_url = GOOGLE_SHEET_WEBHOOK_URL_DEFAULT

#     try:
#         res = requests.post(webhook_url, json=data)
#         print(f"[{brand}] Google Sheet Response: {res.text}")
#     except Exception as e:
#         print(f"Error sending to Google Sheet for brand '{brand}':", e)

#     return {"status": "ok"}



# --- Demo Pages ---
@app.route('/demo/successgyan')
def demo_successgyan():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SuccessGyan Voizee Assistant Demo</title>
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
            /* Override widget position via script injection */
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
        <div class="logo">
            <img src="https://successgyan.com/wp-content/uploads/2024/02/SG-logo-1@2x-150x67.png" alt="SuccessGyan Logo" height="60">
        </div>
        <h2>SuccessGyan Voizee Assistant Demo</h2>
        <div class="widget-wrapper">
            <script src="/successgyan?agent=agent_01k06m09xefx4vxwc0drtf6sje"></script>
        </div>
            <script>
function removeBrandingFromWidget() {
  const widget = document.querySelector('elevenlabs-convai');
  if (!widget || !widget.shadowRoot) return false;

  const shadow = widget.shadowRoot;
  const brandingElements = shadow.querySelectorAll('[class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"], span:has(a[href*="elevenlabs"])');

  brandingElements.forEach(el => el.remove());

  // Optionally remove footer shadow or extra boxes
  const footer = shadow.querySelector('[class*="_box_"]');
  if (footer && footer.textContent.toLowerCase().includes('elevenlabs')) {
    footer.remove();
  }

  return brandingElements.length > 0;
}

const tryRemove = () => {
  const success = removeBrandingFromWidget();
  if (!success) {
    setTimeout(tryRemove, 300);  // retry until it appears
  }
};

tryRemove(); // start the removal loop

// Also attach MutationObserver in case of dynamic updates
const observer = new MutationObserver(() => removeBrandingFromWidget());
observer.observe(document.body, { childList: true, subtree: true });
</script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route('/demo/kfwcorp')
def demo_kfwcorp():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>kfwcorp Voizee Assistant Demo</title>
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
                background: #001F54;
            }
            .widget-wrapper {
                margin-top: 60px;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 400px;
                position: relative;
            }
            /* Override widget position via script injection */
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
        <div class="logo">
            <img src="https://kfwcorp.com/assets/img/logo-w.png" alt="KFWCorpl Logo" height="60">
        </div>
        <h2>KFWCorp Voizee Assistant Demo</h2>
        <div class="widget-wrapper">
            <script src="/kfwcorp?agent=agent_01jzm4vq12f58bfgnyr07ac819"></script>
        </div>
      <script>
function removeBrandingFromWidget() {
  const widget = document.querySelector('elevenlabs-convai');
  if (!widget || !widget.shadowRoot) return false;

  const shadow = widget.shadowRoot;
  const brandingElements = shadow.querySelectorAll('[class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"], span:has(a[href*="elevenlabs"])');

  brandingElements.forEach(el => el.remove());

  // Optionally remove footer shadow or extra boxes
  const footer = shadow.querySelector('[class*="_box_"]');
  if (footer && footer.textContent.toLowerCase().includes('elevenlabs')) {
    footer.remove();
  }

  return brandingElements.length > 0;
}

const tryRemove = () => {
  const success = removeBrandingFromWidget();
  if (!success) {
    setTimeout(tryRemove, 300);  // retry until it appears
  }
};

tryRemove(); // start the removal loop

// Also attach MutationObserver in case of dynamic updates
const observer = new MutationObserver(() => removeBrandingFromWidget());
observer.observe(document.body, { childList: true, subtree: true });
</script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route('/demo/myndwell')
def demo_myndwell():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Myndwell Voizee Assistant Demo</title>
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
            }
            .widget-wrapper {
                margin-top: 60px;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 400px;
                position: relative;
            }
            /* Override widget position via script injection */
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
        <div class="logo">
            <img src="https://myndwell.io/wp-content/uploads/2022/11/logo.png" alt="Myndwell Logo" height="60">
        </div>
        <h2>Myndwell Voizee Assistant Demo</h2>
        <div class="widget-wrapper">
            <script src="/myndwell?agent=agent_01k099ck2mf0tr5g558de7w0av"></script>
        </div>
    <script>
function removeBrandingFromWidget() {
  const widget = document.querySelector('elevenlabs-convai');
  if (!widget || !widget.shadowRoot) return false;

  const shadow = widget.shadowRoot;
  const brandingElements = shadow.querySelectorAll('[class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"], span:has(a[href*="elevenlabs"])');

  brandingElements.forEach(el => el.remove());

  // Optionally remove footer shadow or extra boxes
  const footer = shadow.querySelector('[class*="_box_"]');
  if (footer && footer.textContent.toLowerCase().includes('elevenlabs')) {
    footer.remove();
  }

  return brandingElements.length > 0;
}

const tryRemove = () => {
  const success = removeBrandingFromWidget();
  if (!success) {
    setTimeout(tryRemove, 300);  // retry until it appears
  }
};

tryRemove(); // start the removal loop

// Also attach MutationObserver in case of dynamic updates
const observer = new MutationObserver(() => removeBrandingFromWidget());
observer.observe(document.body, { childList: true, subtree: true });
</script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route('/demo/galent')
def demo_galent():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Galent Voizee Assistant Demo</title>
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
            }
            .widget-wrapper {
                margin-top: 60px;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 400px;
                position: relative;
            }
            /* Override widget position via script injection */
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
        <div class="logo">
            <img src="https://galent.com/wp-content/themes/twentytwentyone/img/icons/galent-nav-logo.svg" alt="galent Logo" height="60">
        </div>
        <h2>Galent Voizee Assistant Demo</h2>
        <div class="widget-wrapper">
            <script src="/galent?agent=agent_01k0bxx69dezk91kdpvgj9k8yn"></script>
        </div>

    <script>
function removeBrandingFromWidget() {
  const widget = document.querySelector('elevenlabs-convai');
  if (!widget || !widget.shadowRoot) return false;

  const shadow = widget.shadowRoot;
  const brandingElements = shadow.querySelectorAll('[class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"], span:has(a[href*="elevenlabs"])');

  brandingElements.forEach(el => el.remove());

  // Optionally remove footer shadow or extra boxes
  const footer = shadow.querySelector('[class*="_box_"]');
  if (footer && footer.textContent.toLowerCase().includes('elevenlabs')) {
    footer.remove();
  }

  return brandingElements.length > 0;
}

const tryRemove = () => {
  const success = removeBrandingFromWidget();
  if (!success) {
    setTimeout(tryRemove, 300);  // retry until it appears
  }
};

tryRemove(); // start the removal loop

// Also attach MutationObserver in case of dynamic updates
const observer = new MutationObserver(() => removeBrandingFromWidget());
observer.observe(document.body, { childList: true, subtree: true });
</script>

    </body>
    </html>
    """
    return render_template_string(html)


@app.route('/demo/orientbell')
def demo_orientbell():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>orientbell Voizee Assistantt Demo</title>
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
            }
            .widget-wrapper {
                margin-top: 60px;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 400px;
                position: relative;
            }
            /* Override widget position via script injection */
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
        <div class="logo">
            <img src="https://tiles.orientbell.com/landingpage/logo/logo.png" alt="galent Logo" height="60">
        </div>
        <h2>Orientbell Voizee Assistant Demo</h2>
        <div class="widget-wrapper">
            <script src="https://voizee.sybrant.com/orientbell?agent=agent_0501k16aqfe5f0xvnp0eg2c532bt"></script>
        </div>

    <script>
function removeBrandingFromWidget() {
  const widget = document.querySelector('elevenlabs-convai');
  if (!widget || !widget.shadowRoot) return false;

  const shadow = widget.shadowRoot;
  const brandingElements = shadow.querySelectorAll('[class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"], span:has(a[href*="elevenlabs"])');

  brandingElements.forEach(el => el.remove());

  // Optionally remove footer shadow or extra boxes
  const footer = shadow.querySelector('[class*="_box_"]');
  if (footer && footer.textContent.toLowerCase().includes('elevenlabs')) {
    footer.remove();
  }

  return brandingElements.length > 0;
}

const tryRemove = () => {
  const success = removeBrandingFromWidget();
  if (!success) {
    setTimeout(tryRemove, 300);  // retry until it appears
  }
};

tryRemove(); // start the removal loop

// Also attach MutationObserver in case of dynamic updates
const observer = new MutationObserver(() => removeBrandingFromWidget());
observer.observe(document.body, { childList: true, subtree: true });
</script>

    </body>
    </html>
    """
    return render_template_string(html)    


@app.route('/demo/test')
def demo_test():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>orientbell Voizee Assistantt Demo</title>
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
            }
            .widget-wrapper {
                margin-top: 60px;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 400px;
                position: relative;
            }
            /* Override widget position via script injection */
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
        <div class="logo">
            <img src="https://tiles.orientbell.com/landingpage/logo/logo.png" alt="galent Logo" height="60">
        </div>
        <h2>Orientbell Voizee Assistant Demo</h2>
        <div class="widget-wrapper">
            <script src="https://voizee.sybrant.com/test?agent=agent_0501k16aqfe5f0xvnp0eg2c532bt"></script>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)    




@app.route('/demo/preludesys')
def demo_preludesys():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Preludesys Voizee Assistantt Demo</title>
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
                background: #000000;
            }
            
        </style>
    </head>
    <body>
        <div class="logo">
            <img src="https://preludesys.com/wp-content/themes/preludesys/images/logo.svg" alt="preludesys Logo" height="60">
        </div>
        <h2>Preludesys Voizee Assistant Demo</h2>
        
    
    <script src="https://voizee.sybrant.com/preludesys?agent=agent_3501k18965z0fetshdah8ressxza"></script>  

    <script>
function removeBrandingFromWidget() {
  const widget = document.querySelector('elevenlabs-convai');
  if (!widget || !widget.shadowRoot) return false;

  const shadow = widget.shadowRoot;
  const brandingElements = shadow.querySelectorAll('[class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"], span:has(a[href*="elevenlabs"])');

  brandingElements.forEach(el => el.remove());

  // Optionally remove footer shadow or extra boxes
  const footer = shadow.querySelector('[class*="_box_"]');
  if (footer && footer.textContent.toLowerCase().includes('elevenlabs')) {
    footer.remove();
  }

  return brandingElements.length > 0;
}

const tryRemove = () => {
  const success = removeBrandingFromWidget();
  if (!success) {
    setTimeout(tryRemove, 300);  // retry until it appears
  }
};

tryRemove(); // start the removal loop

// Also attach MutationObserver in case of dynamic updates
const observer = new MutationObserver(() => removeBrandingFromWidget());
observer.observe(document.body, { childList: true, subtree: true });
</script>

    </body>
    </html>
    """
    return render_template_string(html)    

@app.route('/demo/cfobridge')
def demo_cfobridge():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CFOBridge Voizee Assistantt Demo</title>
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
                background: #000000;
            }
            
        </style>
    </head>
    <body>
        <div class="logo">
            <img src="https://cfobridge.com/assets/images/logo.webp" alt="cfobridge Logo" height="60">
        </div>
        <h2>CFOBridge Voizee Assistant Demo</h2>
        
    
    <script src="https://voizee.sybrant.com/cfobridge?agent=agent_3201k2c2hxn4e0stk07tkjmgj4e5"></script>  

<script>
  const styleEnhancerInterval = setInterval(() => {
    const widget = document.querySelector("elevenlabs-convai");
    const shadow = widget?.shadowRoot;
    const realStart = shadow?.querySelector('button[title="Start a call"]');
    const clone = shadow?.querySelector('button[title="Start a call"] + div > button');

    if (clone && !clone._cfoStyled) {
      clone._cfoStyled = true;
      Object.assign(clone.style, {
        backgroundColor: "#0b72e7",
        color: "#fff",
        border: "none",
        padding: "14px 28px",
        borderRadius: "8px",
        fontSize: "16px",
        fontWeight: "bold",
        boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
        cursor: "pointer"
      });

      clearInterval(styleEnhancerInterval); // Stop retrying once styled
    }
  }, 300);
</script>


    <script>
function removeBrandingFromWidget() {
  const widget = document.querySelector('elevenlabs-convai');
  if (!widget || !widget.shadowRoot) return false;

  const shadow = widget.shadowRoot;
  const brandingElements = shadow.querySelectorAll('[class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"], span:has(a[href*="elevenlabs"])');

  brandingElements.forEach(el => el.remove());

  // Optionally remove footer shadow or extra boxes
  const footer = shadow.querySelector('[class*="_box_"]');
  if (footer && footer.textContent.toLowerCase().includes('elevenlabs')) {
    footer.remove();
  }

  return brandingElements.length > 0;
}

const tryRemove = () => {
  const success = removeBrandingFromWidget();
  if (!success) {
    setTimeout(tryRemove, 300);  // retry until it appears
  }
};

tryRemove(); // start the removal loop

// Also attach MutationObserver in case of dynamic updates
const observer = new MutationObserver(() => removeBrandingFromWidget());
observer.observe(document.body, { childList: true, subtree: true });
</script>

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
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sybrant Voizee</title>
  <style>
    body {
      font-family: "Segoe UI", Arial, sans-serif;
      margin: 0;
      padding: 0;
      background: linear-gradient(135deg, #f5f7fa, #e4ebf7);
      color: #222;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
    }

    header {
      display: flex;
      justify-content: center;
      margin-top: 40px;
    }

    .logo-box {
      background: #000;
      padding: 12px 20px;
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    .logo-box img {
      height: 60px;
      display: block;
    }

    .title-section {
      text-align: center;
      margin: 40px 0 30px;
    }

    .title-section h1 {
      font-size: 32px;
      font-weight: 700;
      margin: 0;
      color: #222;
    }

    .title-section h2 {
      font-size: 22px;
      font-weight: 500;
      margin: 10px 0;
      color: #555;
    }

    .title-section p {
      font-size: 16px;
      margin: 6px 0;
      color: #666;
    }

    .assistant-container {
      background: #fff;
      border-radius: 20px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.1);
      padding: 30px;
      max-width: 600px;
      width: 90%;
      text-align: center;
      margin-bottom: 40px;
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .assistant-container:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 28px rgba(0,0,0,0.15);
    }

    .robot-image {
  text-align: center;
  margin: 20px 0 80px 30px;
}

.robot-image img {
  max-width: 280px;  /* keeps it responsive */
  width: 100%;
  height: auto;
  display: inline-block;
}


    .start-btn {
      margin-top: 20px;
      padding: 12px 24px;
      font-size: 16px;
      border-radius: 30px;
      border: none;
      background: #0077ff;
      color: #fff;
      cursor: pointer;
      transition: background 0.3s;
    }

    .start-btn:hover {
      background: #005ecc;
    }

    [class*="_status_1968y_121"] {
  display: none !important;
  opacity: 0 !important;
  visibility: hidden !important;
  pointer-events: none !important;
  height: 0 !important;
  font-size: 0 !important;
}
  </style>
</head>
<body>

  <header>
    <div class="logo-box">
      <img src="https://sybrant.com/wp-content/uploads/2025/05/sybrant.png" alt="Sybrant Logo">
    </div>
  </header>

  <div class="title-section">
    <h1>Sybrant Voizee</h1>
    <h2>Sales Agent Demo</h2>
    <p>Click <b>"Start a call"</b> and ask your questions about Sybrant Voizee.</p>
    <p>We will customize this for your products / services.</p>
  </div>

    <div class="robot-image">
    <img src="https://sybrant.com/wp-content/uploads/2025/08/voizee_sybrant-e1755606750640.png" alt="Voizee Assistant" />
  </div>

      <script src="https://voizee.sybrant.com/sybrant?agent=agent_01jwfxypsyfja9bjqhq5d1zp43"></script>  

    <script>
function removeBrandingFromWidget() {
  const widget = document.querySelector('elevenlabs-convai');
  if (!widget || !widget.shadowRoot) return false;

  const shadow = widget.shadowRoot;
  const brandingElements = shadow.querySelectorAll('[class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"], span:has(a[href*="elevenlabs"]), [class*="_status_1968y_121"]');

  brandingElements.forEach(el => el.remove());

  // Optionally remove footer shadow or extra boxes
  const footer = shadow.querySelector('[class*="_box_"]');
  if (footer && footer.textContent.toLowerCase().includes('elevenlabs')) {
    footer.remove();
  }

  return brandingElements.length > 0;
}

const tryRemove = () => {
  const success = removeBrandingFromWidget();
  if (!success) {
    setTimeout(tryRemove, 300);  // retry until it appears
  }
};

tryRemove(); // start the removal loop

// Also attach MutationObserver in case of dynamic updates
const observer = new MutationObserver(() => removeBrandingFromWidget());
observer.observe(document.body, { childList: true, subtree: true });
</script>


</body>
</html>
    """
    return render_template_string(html)


    
# --- Health Check & Root ---
@app.route('/')
def home():
    return "Voice Widget Server Running!"

@app.route('/health')
def health():
    return {"status": "healthy"}


# --- Start Server ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
