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
# GOOGLE_SHEET_WEBHOOK_URL_CFOBRIDGE = 'https://script.google.com/macros/s/AKfycbwLV_WE3fs1ocw_PhFpWdwC9uASNU2wbD0Uuhk-2WHte5T12c0sWOg2Pq5VtmlAIvDM/exec'
# GOOGLE_SHEET_WEBHOOK_URL_CFOBRIDGE = 'https://script.google.com/macros/s/AKfycbwhN9SDC8jM3tyqFjrnOMtLqecx5_bBPVuKvFk_1ZuM41EAWEZuIUfwsTcd1cI-bXk/exec'
GOOGLE_SHEET_WEBHOOK_URL_CFOBRIDGE = 'https://script.google.com/macros/s/AKfycbwrkqqFYAuoV9_zg1PYSC5Cr134XZ6mD_OqMhjX_oxMq7fzINpMQY46HtxgR0gkj1inPA/exec'
GOOGLE_SHEET_WEBHOOK_URL_SYBRANT = 'https://script.google.com/macros/s/AKfycbxw4RJYQkdWRN3Fu3Vakj5C8h2P-YUN4qJZQrzxjyDk8t2dCY6Wst3wV0pJ2e5h_nn-6Q/exec'


def serve_widget_js(agent_id, branding="Powered by Voizee", brand="dhilaktest"):
    js = """
(function(){
  const AGENT_ID = "__AGENT_ID__";
  const BRAND = "__BRAND__";
  const BRANDING_TEXT = "__BRANDING__";

  // create widget tag
  try {
    const tag = document.createElement("elevenlabs-convai");
    tag.setAttribute("agent-id", AGENT_ID);
    document.body.appendChild(tag);
  } catch (e) {
    console.error("Failed to create elevenlabs-convai tag:", e);
  }

  // prefer the unpkg embed (same as your page), fallback to old URL if needed
  (function loadEmbed(){
    const s = document.createElement("script");
    s.src = "https://unpkg.com/@elevenlabs/convai-widget-embed";
    s.async = true;
    s.onerror = function(){
      // fallback after failure
      const s2 = document.createElement("script");
      s2.src = "https://elevenlabs.io/convai-widget/index.js";
      s2.async = true;
      document.body.appendChild(s2);
    };
    document.body.appendChild(s);

    // if widget not initialized after short delay, try fallback script
    setTimeout(() => {
      const w = document.querySelector('elevenlabs-convai');
      if (!w || !w.shadowRoot) {
        const s2 = document.createElement("script");
        s2.src = "https://elevenlabs.io/convai-widget/index.js";
        s2.async = true;
        document.body.appendChild(s2);
      }
    }, 1400);
  })();

  // remove/minimize branding inside shadow root if possible
  function removeBrandingFromShadow(sr){
    if(!sr) return;
    try {
      const selectors = ['[class*="poweredBy"]', "div[part='branding']", 'a[href*="elevenlabs"]', "[class*='_status_']"];
      selectors.forEach(sel=>{
        const nodes = sr.querySelectorAll(sel);
        nodes.forEach(n => n.remove());
      });
    } catch(e){}
  }

  // create modal (only once)
  function createModal(){
    if(document.getElementById('convai-visitor-modal')) return;
    const modal = document.createElement('div');
    modal.id = 'convai-visitor-modal';
    modal.style = "display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:2147483647;align-items:center;justify-content:center;";

    modal.innerHTML = `
      <div style="background:#fff;border-radius:10px;padding:20px;max-width:420px;width:92%;box-shadow:0 10px 30px rgba(0,0,0,0.2);font-family:Arial, sans-serif;">
        <div style="text-align:right;"><button id="convai-modal-close" style="border:none;background:none;font-size:20px;cursor:pointer;">&times;</button></div>
        <h3 style="margin:0 0 12px 0;">Tell us about you</h3>
        <form id="convai-visitor-form" style="display:flex;flex-direction:column;gap:8px;">
          <input name="name" placeholder="Full name" required style="padding:10px;border-radius:6px;border:1px solid #ddd"/>
          <input name="email" type="email" placeholder="Email" required style="padding:10px;border-radius:6px;border:1px solid #ddd"/>
          <input name="phone" placeholder="Phone" style="padding:10px;border-radius:6px;border:1px solid #ddd"/>
          <div style="display:flex;gap:8px;margin-top:6px;">
            <button type="submit" style="flex:1;padding:10px;border-radius:6px;border:none;background:#0b72e7;color:#fff;cursor:pointer;">Submit & Start Call</button>
            <button type="button" id="convai-modal-cancel" style="flex:0;padding:10px;border-radius:6px;border:1px solid #ccc;background:#fff;cursor:pointer;">Cancel</button>
          </div>
        </form>
      </div>
    `;
    document.body.appendChild(modal);

    modal.querySelector('#convai-modal-close').addEventListener('click', ()=> modal.style.display='none');
    modal.querySelector('#convai-modal-cancel').addEventListener('click', ()=> modal.style.display='none');

    const form = modal.querySelector('#convai-visitor-form');
    form.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const fd = new FormData(form);
      const payload = Object.fromEntries(fd.entries());
      payload.url = window.location.href;
      payload.brand = BRAND || "dhilaktest";
      payload.agent_id = AGENT_ID;
      payload.timestamp = new Date().toISOString();

      try {
        // POST to your Flask /log-visitor endpoint (same-origin)
        await fetch('https://voice-widget-new-production-177d.up.railway.app/log-visitor', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
      } catch (err) {
        console.error('Failed to log visitor', err);
      }

      // set small TTL so user doesn't need to re-fill immediately (5 minutes)
      localStorage.setItem('convai_form_submitted', (Date.now() + 5*60*1000).toString());
      modal.style.display='none';

      // trigger original button (if saved)
      try {
        if (window.__convai_last_button) {
          window.__convai_last_button._allowCall = true;
          try { window.__convai_last_button.click(); } catch(e) {
            const simulated = new MouseEvent('click', {bubbles:true, cancelable:true, composed:true});
            window.__convai_last_button.dispatchEvent(simulated);
          }
        }
      } catch(e){ console.error("Error triggering original button:", e); }
    });
  }

  createModal();

  // find and hook Start button (shadow DOM or document)
  function hookIfFound(){
    const widget = document.querySelector('elevenlabs-convai');
    if (!widget) return false;

    // try shadow root first
    const sr = widget.shadowRoot;
    if (sr) {
      removeBrandingFromShadow(sr);
      const selectors = ['button[title="Start a call"]','button[aria-label="Start a call"]','button[title*="Start"]','button[aria-label*="Start"]','button'];
      for (const sel of selectors) {
        const btn = sr.querySelector(sel);
        if (btn && !btn._convai_hooked) {
          attachInterceptor(btn);
          return true;
        }
      }
    }

    // fallback to global document
    const docSelectors = ['button[aria-label="Start a call"]','button[title="Start a call"]','button[aria-label*="Start"]','button[title*="Start"]'];
    for (const sel of docSelectors) {
      const btn = document.querySelector(sel);
      if (btn && !btn._convai_hooked) {
        attachInterceptor(btn);
        return true;
      }
    }

    return false;
  }

  function attachInterceptor(btn) {
    btn._convai_hooked = true;
    window.__convai_last_button = btn;

    const handler = function(e) {
      // expiry-bypass: if user recently submitted, allow the click to proceed
      const expiryStr = localStorage.getItem('convai_form_submitted');
      const expiry = expiryStr ? parseInt(expiryStr, 10) : 0;
      if (expiry && Date.now() < expiry) {
        return; // let default behavior happen
      }

      // allow programmatic click to pass through once
      if (btn._allowCall) {
        btn._allowCall = false;
        return;
      }

      e.preventDefault();
      e.stopImmediatePropagation();

      // open modal
      const modal = document.getElementById('convai-visitor-modal');
      if (modal) modal.style.display = 'flex';
    };

    // use capture so we intercept before widget internal handlers
    btn.addEventListener('click', handler, true);

    // attempt to remove branding (safety)
    try {
      const root = btn.getRootNode && btn.getRootNode();
      if (root && root instanceof ShadowRoot) removeBrandingFromShadow(root);
    } catch(e){}
  }

  // Observe DOM for widget/button
  const obs = new MutationObserver((mutations, ob) => {
    try {
      hookIfFound();
    } catch(e){}
  });
  obs.observe(document, {childList:true, subtree:true});

  // Poll fallback for a short time (in case MutationObserver misses)
  let tries = 0;
  const poll = setInterval(()=>{
    try {
      const ok = hookIfFound();
      if (ok || ++tries > 50) clearInterval(poll);
    } catch(e){}
  }, 300);

})();
    """
    return js.replace("__AGENT_ID__", agent_id).replace("__BRANDING__", branding).replace("__BRAND__", brand)




# --- Core JS serve_widget_js2222222: instant modal + triple-guard injection + per-brand cache key ---
def serve_widget_js2(agent_id, branding="Powered by Voizee", brand="default"):
    js = """
(function(){
  const AGENT_ID = "__AGENT_ID__";
  const BRAND = "__BRAND__";
  const BRANDING_TEXT = "__BRANDING__";

  // Inject widget
  try {
    const tag = document.createElement("elevenlabs-convai");
    tag.setAttribute("agent-id", AGENT_ID);
    document.body.appendChild(tag);
  } catch (e) {
    console.error("Widget creation failed", e);
  }

  // Load embed script
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

  // Remove branding, avatar and prompt
  function removeExtras(sr){
    if (!sr) return;
    try {
      const selectors = [
        'span.opacity-30', // "Powered by ElevenLabs"
        'div[style*="avatar.png"]', // avatar image
        'div.relative.text-sm.max-w-64', // "Speak to know more"
        'div.relative.shrink-0.w-9.h-9'  // avatar wrapper
      ];
      selectors.forEach(sel => {
        sr.querySelectorAll(sel).forEach(el => el.remove());
      });
    } catch(e){
      console.warn("Brand cleanup error", e);
    }
  }

  // Try hooking call button
  function hookButton(){
    const widget = document.querySelector("elevenlabs-convai");
    if (!widget) return false;
    const sr = widget.shadowRoot;
    if (!sr) return false;

    removeExtras(sr);

    const selectors = [
      'button[title="Start a call"]',
      'button[aria-label="Start a call"]',
      'button[title*="Start"]',
      'button[aria-label*="Start"]'
    ];
    for (const sel of selectors) {
      const btn = sr.querySelector(sel);
      if (btn && !btn._hooked) {
        btn._hooked = true;
        interceptClick(btn);
        return true;
      }
    }
    return false;
  }

  // Show modal on click
  function interceptClick(btn){
    window.__last_call_btn = btn;
    btn.addEventListener("click", (e) => {
      const ttl = parseInt(localStorage.getItem("convai_form_submitted") || "0");
      if (Date.now() < ttl) return;

      if (btn._allowCall) {
        btn._allowCall = false;
        return;
      }

      e.preventDefault();
      e.stopImmediatePropagation();

      const modal = document.getElementById("convai-visitor-modal");
      if (modal) modal.style.display = "flex";
    }, true);
  }

  // Inject visitor form
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
          <input name="email" type="email" placeholder="Email" required style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <input name="phone" placeholder="Phone (optional)" style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <div style="display:flex;gap:10px;">
            <button type="submit" style="flex:1;padding:10px;background:#007bff;color:white;border:none;border-radius:4px;">Submit</button>
            <button type="button" id="convai-cancel" style="padding:10px;background:#eee;border:none;border-radius:4px;">Cancel</button>
          </div>
        </form>
      </div>
    `;
    document.body.appendChild(modal);

    modal.querySelector("#convai-close").onclick = () => modal.style.display = "none";
    modal.querySelector("#convai-cancel").onclick = () => modal.style.display = "none";

    const form = modal.querySelector("#convai-form");
    form.onsubmit = async function(ev){
      ev.preventDefault();
      const fd = new FormData(form);
      const data = Object.fromEntries(fd.entries());
      data.agent_id = AGENT_ID;
      data.brand = BRAND;
      data.url = location.href;
      data.timestamp = new Date().toISOString();

      try {
        await fetch("https://voice-widget-new-production-177d.up.railway.app/log-visitor", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });
      } catch(err){
        console.warn("Logging failed", err);
      }

      localStorage.setItem("convai_form_submitted", (Date.now() + 5*60*1000).toString());
      modal.style.display = "none";

      try {
        if (window.__last_call_btn) {
          window.__last_call_btn._allowCall = true;
          window.__last_call_btn.click();
        }
      } catch(err) {}
    }
  }

  createVisitorModal();

  // Observe and poll widget for shadow access
  const obs = new MutationObserver(() => {
    try {
      const found = hookButton();
      if (found) obs.disconnect();
    } catch(e){}
  });
  obs.observe(document, { childList: true, subtree: true });

  let tries = 0;
  const poll = setInterval(() => {
    const ok = hookButton();
    if (ok || ++tries > 50) clearInterval(poll);
  }, 300);
})();
    """
    return js.replace("__AGENT_ID__", agent_id).replace("__BRANDING__", branding).replace("__BRAND__", brand)


# --- Core JS cfobridge instant modal + triple-guard injection + per-brand cache key ---
def serve_widget_js_cfo(agent_id, branding="Powered by Voizee", brand="cfobridge"):
    js = """
(function(){
  const AGENT_ID = "__AGENT_ID__";
  const BRAND = "__BRAND__";
  const BRANDING_TEXT = "__BRANDING__";

  // Inject widget
  try {
    const tag = document.createElement("elevenlabs-convai");
    tag.setAttribute("agent-id", AGENT_ID);
    document.body.appendChild(tag);
  } catch (e) {
    console.error("Widget creation failed", e);
  }

  // Load embed script
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

  // Remove branding, avatar and prompt
  function removeExtras(sr){
    if (!sr) return;
    try {
      const selectors = [
        'span.opacity-30', // "Powered by ElevenLabs"
      ];
      selectors.forEach(sel => {
        sr.querySelectorAll(sel).forEach(el => el.remove());
      });
    } catch(e){
      console.warn("Brand cleanup error", e);
    }
  }

  // Try hooking call button
  function hookButton(){
    const widget = document.querySelector("elevenlabs-convai");
    if (!widget) return false;
    const sr = widget.shadowRoot;
    if (!sr) return false;

    removeExtras(sr);

    const selectors = [
      'button[title="Start a call"]',
      'button[aria-label="Start a call"]',
      'button[title*="Start"]',
      'button[aria-label*="Start"]'
    ];
    for (const sel of selectors) {
      const btn = sr.querySelector(sel);
      if (btn && !btn._hooked) {
        btn._hooked = true;
        interceptClick(btn);
        return true;
      }
    }
    return false;
  }

  // Show modal on click
  function interceptClick(btn){
    window.__last_call_btn = btn;
    btn.addEventListener("click", (e) => {
      const ttl = parseInt(localStorage.getItem("convai_form_submitted") || "0");
      if (Date.now() < ttl) return;

      if (btn._allowCall) {
        btn._allowCall = false;
        return;
      }

      e.preventDefault();
      e.stopImmediatePropagation();

      const modal = document.getElementById("convai-visitor-modal");
      if (modal) modal.style.display = "flex";
    }, true);
  }

  // Inject visitor form
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
          <input name="phone" placeholder="Phone (optional)" style="padding:10px;border:1px solid #ccc;border-radius:4px;">
          <div style="display:flex;gap:10px;">
            <button type="submit" style="flex:1;padding:10px;background:#007bff;color:white;border:none;border-radius:4px;">Submit</button>
            <button type="button" id="convai-cancel" style="padding:10px;background:#eee;border:none;border-radius:4px;">Cancel</button>
          </div>
        </form>
      </div>
    `;
    document.body.appendChild(modal);

    modal.querySelector("#convai-close").onclick = () => modal.style.display = "none";
    modal.querySelector("#convai-cancel").onclick = () => modal.style.display = "none";

    const form = modal.querySelector("#convai-form");
    form.onsubmit = async function(ev){
      ev.preventDefault();
      const fd = new FormData(form);
      const data = Object.fromEntries(fd.entries());
      data.agent_id = AGENT_ID;
      data.brand = BRAND;
      data.url = location.href;
      data.timestamp = new Date().toISOString();

      try {
        await fetch("https://voice-widget-new-production-177d.up.railway.app/log-visitor-cfo", {
          method: "POST",
          headers: { 'Content-Type': 'application/json' },
    	  body: JSON.stringify({
              name,
        	  email,
        	  phone,
        	  company,
        	  website_url: window.location.origin   // 👈 capture here
    		})
        });
      } catch(err){
        console.warn("Logging failed", err);
      }

      localStorage.setItem("convai_form_submitted", (Date.now() + 5*60*1000).toString());
      modal.style.display = "none";

      try {
        if (window.__last_call_btn) {
          window.__last_call_btn._allowCall = true;
          window.__last_call_btn.click();
        }
      } catch(err) {}
    }
  }

  createVisitorModal();

  // Observe and poll widget for shadow access
  const obs = new MutationObserver(() => {
    try {
      const found = hookButton();
      if (found) obs.disconnect();
    } catch(e){}
  });
  obs.observe(document, { childList: true, subtree: true });

  let tries = 0;
  const poll = setInterval(() => {
    const ok = hookButton();
    if (ok || ++tries > 50) clearInterval(poll);
  }, 300);
})();
    """
    return js.replace("__AGENT_ID__", agent_id).replace("__BRANDING__", branding).replace("__BRAND__", brand)



# --- Core JS generator222222: instant modal + triple-guard injection + per-brand cache key ---
def generate_widget_js2(agent_id, brand=""):
    return f"""
    (function() {{
        // --- 1. Hide branding instantly ---
        const preloadStyle = document.createElement("style");
        preloadStyle.textContent = `
            [class*="poweredBy"],
            div[part="branding"],
            span:has(a[href*="elevenlabs"]),
            a[href*="elevenlabs"],
            [class*="branding"],
            div[class*="branding"],
            img[alt*='logo'],
            div[part='feedback-button'],
            [class*="_status_"] {{
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

        // --- 2. Inject widget ---
        const tag = document.createElement("elevenlabs-convai");
        tag.setAttribute("agent-id", "{agent_id}");
        document.body.appendChild(tag);

        const script = document.createElement("script");
        script.src = "https://unpkg.com/@elevenlabs/convai-widget-embed";
        script.async = true;
        script.type = "text/javascript";
        document.body.appendChild(script);

        // --- 3. Create popup form modal ---
        function createModal() {{
            if (document.getElementById('visitor-form-modal')) return;

            const modal = document.createElement('div');
            modal.id = 'visitor-form-modal';
            modal.style = `
                display:none; position:fixed; z-index:99999;
                top:0; left:0; width:100%; height:100%;
                background:rgba(0,0,0,0.6);
                align-items:center; justify-content:center;
            `;

            modal.innerHTML = `
                <div style="
                    background:white; padding:25px; border-radius:10px;
                    width:300px; font-family:sans-serif; position:relative;
                ">
                    <span id="close-form" style="
                        position:absolute; top:5px; right:10px; cursor:pointer;
                        font-size:18px; font-weight:bold;
                    ">&times;</span>

                    <form id="visitor-form">
                        <h3 style="margin-bottom:12px;">Enter your details</h3>
                        <input type="text" name="name" placeholder="Name" required style="margin-bottom:8px; width:100%; padding:8px;" />
                        <input type="tel" name="mobile" placeholder="Mobile (+91...)" required style="margin-bottom:8px; width:100%; padding:8px;" />
                        <input type="email" name="email" placeholder="Email" required style="margin-bottom:15px; width:100%; padding:8px;" />
                        <button type="submit" style="
                            width:100%; padding:10px; background:#0b72e7;
                            color:white; border:none; border-radius:5px;
                            cursor:pointer;
                        ">Start Call</button>
                    </form>
                </div>
            `;
            document.body.appendChild(modal);

            const modalEl = document.getElementById('visitor-form-modal');
            document.getElementById('close-form').onclick = () => modalEl.style.display = 'none';
            window.onclick = (e) => {{ if (e.target === modalEl) modalEl.style.display = 'none'; }};

            // --- form submit ---
            document.getElementById('visitor-form').addEventListener('submit', function(e) {{
                e.preventDefault();
                const name = this.name.value.trim();
                const mobile = this.mobile.value.trim();
                const email = this.email.value.trim();
                const url = window.location.href;

                fetch('https://voice-widget-new-production-177d.up.railway.app/log-visitor', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ name, mobile, email, url, brand: "{brand}" }})
                }}).catch(err => console.error("Log visitor failed", err));

                // cache 15 min expiry
                localStorage.setItem("convai_form_submitted", (Date.now() + 15*60*1000).toString());
                modalEl.style.display = 'none';

                // trigger real widget button
                const widget = document.querySelector('elevenlabs-convai');
                const realBtn = widget?.shadowRoot?.querySelector('button[title="Start a call"]');
                realBtn?.click();
            }});
        }}

        // --- 4. Intercept Start button ---
        const observer = new MutationObserver(() => {{
            const widget = document.querySelector('elevenlabs-convai');
            if (!widget || !widget.shadowRoot) return;

            // nuke branding inside shadowRoot
            const branding = widget.shadowRoot.querySelector('[class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"]');
            if (branding) branding.remove();

            const startBtn = widget.shadowRoot.querySelector('button[title="Start a call"]');
            if (startBtn && !startBtn._hooked) {{
                startBtn._hooked = true;
                const clone = startBtn.cloneNode(true);
                startBtn.style.display = 'none';

                clone.addEventListener('click', (e) => {{
                    e.preventDefault();
                    const expiry = localStorage.getItem("convai_form_submitted");
                    if (expiry && Date.now() < parseInt(expiry)) {{
                        startBtn.click();
                    }} else {{
                        document.getElementById('visitor-form-modal').style.display = 'flex';
                    }}
                }});

                startBtn.parentElement.appendChild(clone);
                createModal();
            }}
        }});
        observer.observe(document.body, {{ childList: true, subtree: true }});
    }})();
    """






# --- Helper to add "no-store" cache headers for widget JS endpoints ---
# def no_store(response: Response) -> Response:
#     response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
#     response.headers["Pragma"] = "no-cache"
#     response.headers["Expires"] = "0"
#     return response



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

                localStorage.setItem("convai_form_submitted", (Date.now() + 150000).toString());
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
    js = serve_widget_js_cfo(agent_id, branding="Powered by cfobridge", brand="cfobridge")
    return Response(js, mimetype='application/javascript')

@app.route('/sybrant')
def serve_sybrant():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js2(agent_id, branding="Powered by sybrant", brand="sybrant")
    return Response(js, mimetype='application/javascript')

@app.route('/dhilaktest')
def serve_dhilaktest():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js2(agent_id, branding="Powered by dhilaktest", brand="dhilaktest")
    return Response(js, mimetype='application/javascript')


@app.route('/ctobridge')
def serve_ctobridge():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = serve_widget_js2(agent_id, branding="Powered by ctobridge", brand="ctobridge")
    return Response(js, mimetype='application/javascript')

# def get_webhook_url(brand):
#     brand = (brand or "").lower()
#     if brand == "successgyan":
#         return GOOGLE_SHEET_WEBHOOK_URL_SUCCESSGYAN
#     elif brand == "kfwcorp":
#         return GOOGLE_SHEET_WEBHOOK_URL_KFWCORP
#     elif brand == "orientbell":
#         return GOOGLE_SHEET_WEBHOOK_URL_ORIENTBELL
#     elif brand == "galent":
#         return GOOGLE_SHEET_WEBHOOK_URL_GALENT
#     elif brand == "myndwell":
#         return GOOGLE_SHEET_WEBHOOK_URL_MYNDWELL
#     elif brand == "preludesys":
#         return GOOGLE_SHEET_WEBHOOK_URL_PRELUDESYS
#     elif brand == "cfobridge":
#         return GOOGLE_SHEET_WEBHOOK_URL_CFOBRIDGE
#     elif brand == "ctobridge":
#         return GOOGLE_SHEET_WEBHOOK_URL_CFOBRIDGE
#     elif brand == "sybrant":
#         return GOOGLE_SHEET_WEBHOOK_URL_SYBRANT
#     elif brand == "dhilaktest":
#         return GOOGLE_SHEET_WEBHOOK_URL_DEFAULT
#     else:
#         return GOOGLE_SHEET_WEBHOOK_URL_DEFAULT

# @app.route('/log-visitor', methods=['POST'])
# def log_visitor():
#     data = request.json
#     brand = data.get("brand", "").lower()
#     webhook_url = get_webhook_url(brand)
#     print(f"[DEBUG] Incoming data: {data}")
#     print(f"[DEBUG] Using webhook URL: {webhook_url}")

#     append_to_log(data, webhook_url)

#     all_entries = read_log()
#     remaining = []

#     for entry in all_entries:
#         try:
#             res = requests.post(entry["webhook_url"], json=entry, timeout=10)
#             print(f"[DEBUG] POST {entry['webhook_url']} => {res.status_code}")
#             if res.status_code == 200:
#                 print(f"[{entry['brand']}] Sent to Google Sheet: {entry}")
#             else:
#                 remaining.append(entry)
#         except Exception as e:
#             print(f"[{entry['brand']}] Exception: {e}")
#             remaining.append(entry)

#     write_log(remaining)
#     return jsonify({"status": "ok", "pending": len(remaining)})


# --- Form Submission Logging try2 ---
# @app.route('/log-visitor', methods=['POST'])
# def log_visitor():
#     data = request.json
#     brand = data.get("brand", "").lower()
#     webhook_url = get_webhook_url(brand)

#     # --- Always log first (with webhook_url) ---
#     append_to_log(data, webhook_url)

#     # --- Retry sending all entries (including new one) ---
#     all_entries = read_log()
#     remaining = []

#     for entry in all_entries:
#         try:
#             res = requests.post(entry["webhook_url"], json=entry, timeout=10)
#             if res.status_code == 200:
#                 print(f"[{entry['brand']}] Sent to Google Sheet: {entry}")
#             else:
#                 print(f"[{entry['brand']}] Failed {res.status_code}, keeping in log")
#                 remaining.append(entry)
#         except Exception as e:
#             print(f"Error sending to Google Sheet for {entry['brand']}: {e}")
#             remaining.append(entry)

#     # Keep only unsent
#     write_log(remaining)

#     return jsonify({"status": "ok", "pending": len(remaining)})



# --- Form Submission Logging try1 ---
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

# webhook_url = "https://script.google.com/macros/s/AKfycbyjjh4lvPTR2xytjabkcofRYIPzFF0UOGI9McuYZCQt8UbQszgH_hMKtUS4Jkyp1S9V/exec"

@app.route('/log-visitor-cfo', methods=['POST'])
def log_visitor_cfo():
    try:
        data = request.get_json(force=True)
        name = data.get("name", "")
        email = data.get("email", "")
        phone = data.get("phone", "")
        company = data.get("company", "")
        website_url = data.get("website_url", request.host_url)  # fallback to server host

        webhook_url = "https://script.google.com/macros/s/AKfycbyjjh4lvPTR2xytjabkcofRYIPzFF0UOGI9McuYZCQt8UbQszgH_hMKtUS4Jkyp1S9V/exec"

        payload = {
            "name": name,
            "email": email,
            "phone": phone,
            "company": company,
            "website_url": website_url
        }

        resp = requests.post(webhook_url, json=payload, timeout=10)

        if resp.status_code == 200:
            return jsonify({"status": "success", "message": "Data logged to CFO sheet"}), 200
        else:
            return jsonify({"status": "error", "message": resp.text}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route('/log-visitor', methods=['POST'])
def log_visitor():
    data = request.json
    brand = data.get("brand", "").lower()

    if brand == "successgyan":
        webhook_url = GOOGLE_SHEET_WEBHOOK_URL_SUCCESSGYAN
    elif brand == "kfwcorp":
        webhook_url = GOOGLE_SHEET_WEBHOOK_URL_KFWCORP
    elif brand == "orientbell":
        webhook_url = GOOGLE_SHEET_WEBHOOK_URL_ORIENTBELL
    elif brand == "galent":
        webhook_url = GOOGLE_SHEET_WEBHOOK_URL_GALENT
    elif brand == "myndwell":
        webhook_url = GOOGLE_SHEET_WEBHOOK_URL_MYNDWELL
    elif brand == "preludesys":
        webhook_url = GOOGLE_SHEET_WEBHOOK_URL_PRELUDESYS
    elif brand == "cfobridge":
        webhook_url = GOOGLE_SHEET_WEBHOOK_URL_CFOBRIDGE
    elif brand == "sybrant":
        webhook_url = GOOGLE_SHEET_WEBHOOK_URL_SYBRANT
    elif brand == "dhilaktest":
        webhook_url = GOOGLE_SHEET_WEBHOOK_URL_DEFAULT
    else:
        webhook_url = GOOGLE_SHEET_WEBHOOK_URL_DEFAULT

    try:
        res = requests.post(webhook_url, json=data)
        print(f"[{brand}] Google Sheet Response: {res.text}")
    except Exception as e:
        print(f"Error sending to Google Sheet for brand '{brand}':", e)

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
            <script src="https://voizee.sybrant.com/successgyan?agent=agent_01k06m09xefx4vxwc0drtf6sje"></script>
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
            <script src="https://voizee.sybrant.com/myndwell?agent=agent_01k099ck2mf0tr5g558de7w0av"></script>
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


    

@app.route('/demo/ctobridge')
def demo_ctobridge():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CTO Bridge Voizee</title>
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
      # background: #000;
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
      <img src="https://ctobridge.com/assets/img/logo.png" alt="CTOBridge Logo">
    </div>
  </header>

  <div class="title-section">
    <h1>CTO Bridge Voizee Assistant Demo</h1>
    <p>Click <b>"Start a call"</b> and ask your questions about CTO Bridge.</p>
  </div>

 
      <script src="https://voizee.sybrant.com/ctobridge?agent=agent_4801k3fnfz4nexdt8mfts31zx0rd"></script>  

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
