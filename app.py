from flask import Flask, request, Response, render_template_string
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Constants: Google Sheet Webhook URLs
GOOGLE_SHEET_WEBHOOK_URL = 'https://script.google.com/macros/s/AKfycbwrkqqFYAuoV9_zg1PYSC5Cr134XZ6mD_OqMhjX_oxMq7fzINpMQY46HtxgR0gkj1inPA/exec'
GOOGLE_SHEET_WEBHOOK_URL_KFWCORP = 'https://script.google.com/macros/s/AKfycbzEyuAW9j3WbPlTAcnpml0uMXAx_UnpQrw0JjfWZ4ew7HxhJZt04Z31ItpBpfoFo9y1yw/exec'
# Add other URLs as needed, example:
GOOGLE_SHEET_WEBHOOK_URL_SUCCESS_GYAN = ''  # You can fill this if needed
GOOGLE_SHEET_WEBHOOK_URL_SYBRANT = ''
GOOGLE_SHEET_WEBHOOK_URL_GALENT = ''
GOOGLE_SHEET_WEBHOOK_URL_MYNDWELL = ''

# JS Generator (branding param is currently unused inside function, so you can remove it)
# def generate_widget_js(agent_id, branding=None):
#     return f"""
# (function() {{
#   console.log("[Widget] starting...");
#   const preloadStyle = document.createElement("style");
#   preloadStyle.textContent = `
#     [class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"], span:has(a[href*="elevenlabs"]) {{
#        display: none !important;
#     }}
#   `;
#   document.head.appendChild(preloadStyle);

#   const tag = document.createElement("elevenlabs-convai");
#   tag.setAttribute("agent-id", "{agent_id}");
#   document.body.appendChild(tag);
#   const script = document.createElement("script");
#   script.src = "https://elevenlabs.io/convai-widget/index.js";
#   script.async = true;
#   document.body.appendChild(script);

#   window.addEventListener('DOMContentLoaded', () => {{
#     console.log("[Widget] DOM loaded, injecting modal...");
#     const modal = document.createElement('div');
#     modal.id = 'visitor-form-modal';
#     modal.style = `
#       display: none; position: fixed; z-index:9999;
#       top:0;left:0;width:100%;height:100%;
#       background: rgba(0,0,0,0.6);
#       align-items:center;justify-content:center;
#     `;
#     modal.innerHTML = `
#       <div style="background:#fff;padding:30px;border-radius:12px;max-width:320px;width:90%;text-align:center;">
#         <span id="close-form" style="cursor:pointer;position:absolute;top:8px;right:12px;">&times;</span>
#         <h3>Tell us about you</h3>
#         <form id="visitor-form">
#           <input name="name" placeholder="Name" required style="width:100%;margin:8px 0;padding:8px;" />
#           <input name="mobile" type="tel" placeholder="Mobile" required style="width:100%;margin:8px 0;padding:8px;" />
#           <input name="email" type="email" placeholder="Email" required style="width:100%;margin:8px 0;padding:8px;" />
#           <button type="submit" style="padding:10px 15px;background:#106FAB;color:#fff;border:none;border-radius:4px;">Start Call</button>
#         </form>
#       </div>
#     `;
#     document.body.appendChild(modal);

#     modal.querySelector('#close-form').onclick = () => modal.style.display = 'none';
#     window.onclick = e => e.target == modal && (modal.style.display = 'none');

#     const observer = new MutationObserver((_, obs) => {{
#       const widget = document.querySelector('elevenlabs-convai');
#       const btn = widget?.shadowRoot?.querySelector('button[title="Start a call"]');
#       if (btn) {{
#         if (!btn._hooked) {{
#           btn._hooked = true;
#           const copy = btn.cloneNode(true);
#           btn.style.display = 'none';
#           btn.parentElement.appendChild(copy);
#           copy.onclick = e => {{
#             e.preventDefault();
#             if (localStorage.getItem("convai_form_submitted") &&
#                 Date.now() < parseInt(localStorage.getItem("convai_form_submitted"))) {{
#               btn.click();
#             }} else {{
#               modal.style.display = 'flex';
#             }}
#           }};
#         }}
#         obs.disconnect();
#       }}
#     }});
#     observer.observe(document.body, {{ childList: true, subtree: true }});

#     document.getElementById('visitor-form').onsubmit = e => {{
#       e.preventDefault();
#       const name = e.target.name.value.trim();
#       const mobile = e.target.mobile.value.trim();
#       const email = e.target.email.value.trim();
#       if (!name||!mobile||!email) return alert("All fields are required");
#       fetch('https://voizee.sybrant.com/log-visitor', {{
#         method:'POST', headers:{{'Content-Type':'application/json'}},
#         body: JSON.stringify({{name, mobile, email, url: window.location.href}})
#       }});
#       localStorage.setItem("convai_form_submitted", (Date.now()+86400000).toString());
#       modal.style.display = 'none';
#       setTimeout(() => {
#     const widget = document.querySelector('elevenlabs-convai');
#     const btn = widget?.shadowRoot?.querySelector('button[title="Start a call"]');
#     if (btn) {
#       btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
#     } else {
#       console.warn("Start a call button not found");
#     }
#   }, 300);
#     }};
#   }});
# }})();
# """


def generate_widget_js(agent_id, branding):
    return f"""
(function() {{
    console.log("[Widget] Initializing...");

    // Preload style to hide branding immediately
    const preloadStyle = document.createElement("style");
    preloadStyle.textContent = `
        [class*="poweredBy"],
        div[part="branding"],
        span:has(a[href*="elevenlabs"]),
        a[href*="elevenlabs"],
        [class*="_poweredBy_"],
        div[class*="branding"],
        [part="branding"] {{
            display: none !important;
            opacity: 0 !important;
            visibility: hidden !important;
            height: 0 !important;
            pointer-events: none !important;
        }}
    `;
    document.head.appendChild(preloadStyle);

    // Inject ElevenLabs widget tag and script
    const tag = document.createElement("elevenlabs-convai");
    tag.setAttribute("agent-id", "{agent_id}");
    document.body.appendChild(tag);

    const script = document.createElement("script");
    script.src = "https://elevenlabs.io/convai-widget/index.js";
    script.async = true;
    document.body.appendChild(script);

    // Wait for DOM ready to inject form modal
    window.addEventListener('DOMContentLoaded', () => {{
        // === Modal Setup ===
        const modal = document.createElement('div');
        modal.id = 'visitor-form-modal';
        Object.assign(modal.style, {{
            display: 'none',
            position: 'fixed',
            zIndex: '99999',
            top: '0',
            left: '0',
            width: '100%',
            height: '100%',
            background: 'rgba(0, 0, 0, 0.6)',
            alignItems: 'center',
            justifyContent: 'center'
        }});
        modal.innerHTML = `
            <div style="background: white; padding: 30px; border-radius: 10px; width: 320px; position: relative; font-family: sans-serif;">
                <span id="close-form" style="position: absolute; top: 10px; right: 15px; cursor: pointer;">&times;</span>
                <form id="visitor-form">
                    <h3 style="margin-bottom: 15px;">Tell us about you</h3>
                    <input type="text" name="name" placeholder="Name" required style="width:100%;margin:8px 0;padding:8px;" />
                    <input type="tel" name="mobile" placeholder="Mobile (+91...)" required style="width:100%;margin:8px 0;padding:8px;" />
                    <input type="email" name="email" placeholder="Email" required style="width:100%;margin:8px 0;padding:8px;" />
                    <button type="submit" style="width:100%;padding:10px;margin-top:10px;background:#106FAB;color:#fff;border:none;border-radius:5px;">Start Call</button>
                </form>
            </div>
        `;
        document.body.appendChild(modal);

        // Close modal logic
        document.getElementById("close-form").onclick = () => modal.style.display = "none";
        window.onclick = e => e.target === modal && (modal.style.display = "none");

        // Form submission handler
        document.getElementById("visitor-form").onsubmit = e => {{
            e.preventDefault();
            const name = e.target.name.value.trim();
            const mobile = e.target.mobile.value.trim();
            const email = e.target.email.value.trim();
            const url = window.location.href;

            if (!name || !mobile || !email) {{
                alert("Please fill all fields.");
                return;
            }}

            fetch('https://voice-widget-new-production-177d.up.railway.app/log-visitor', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ name, mobile, email, url }})
            }}).then(() => {{
                localStorage.setItem("convai_form_submitted", (Date.now() + 5 * 60 * 1000).toString());
                modal.style.display = "none";
                attemptClickStartCall(5); // Retry up to 5 times
            }}).catch(err => {{
                console.error("Error submitting form:", err);
                alert("Failed to log visitor. Please try again.");
            }});
        }};
    }});

    // === Mutation Observer to monitor widget load and hook button ===
    const observer = new MutationObserver(() => {{
        const widget = document.querySelector("elevenlabs-convai");
        const shadow = widget?.shadowRoot;
        if (!shadow) return;

        // Try to remove branding from inside Shadow DOM
        const branding = shadow.querySelector("[part='branding'], [class*='poweredBy']");
        branding?.remove();

        const btn = shadow.querySelector('button[title="Start a call"]');
        if (btn && !btn._hooked) {{
            btn._hooked = true;
            console.log("Found Start Call button");

            // Overlay invisible proxy to intercept first click
            const overlay = document.createElement("div");
            Object.assign(overlay.style, {{
                position: 'absolute',
                top: btn.offsetTop + 'px',
                left: btn.offsetLeft + 'px',
                width: btn.offsetWidth + 'px',
                height: btn.offsetHeight + 'px',
                background: 'transparent',
                zIndex: '9999',
                cursor: 'pointer'
            }});
            btn.parentElement.style.position = 'relative';
            btn.parentElement.appendChild(overlay);

            overlay.onclick = e => {{
                e.preventDefault();
                const expiry = localStorage.getItem("convai_form_submitted");
                if (expiry && Date.now() < parseInt(expiry)) {{
                    console.log("Start call allowed, triggering...");
                    btn.click();
                }} else {{
                    document.getElementById('visitor-form-modal').style.display = 'flex';
                }}
            }};
        }}
    }});
    observer.observe(document.body, {{ childList: true, subtree: true }});

    // === Retry click on original button after form submission ===
    function attemptClickStartCall(retries) {{
        const widget = document.querySelector('elevenlabs-convai');
        const btn = widget?.shadowRoot?.querySelector('button[title="Start a call"]');
        if (btn) {{
            console.log("Retry click: Triggering real button");
            btn.click();
        }} else if (retries > 0) {{
            console.log("Retrying... attempts left:", retries);
            setTimeout(() => attemptClickStartCall(retries - 1), 300);
        }} else {{
            console.error("Failed to find Start Call button after retries.");
        }}
    }}
}})();
"""




# Widget endpoints with explicit brand strings
@app.route('/convai-widget.js')
def serve_convai_widget():
    agent_id = request.args.get('agent', '')
    return Response(generate_widget_js(agent_id, branding=None), mimetype='application/javascript')

@app.route('/successgyan')
def serve_successgyan_widget():
    agent_id = request.args.get('agent', '')
    return Response(generate_widget_js(agent_id, branding="successgyan"), mimetype='application/javascript')

@app.route('/kfwcorp')
def serve_kfwcorp_widget():
    agent_id = request.args.get('agent', '')
    return Response(generate_widget_js(agent_id, branding="kfwcorp"), mimetype='application/javascript')

@app.route('/myndwell')
def serve_myndwell_widget():
    agent_id = request.args.get('agent', '')
    return Response(generate_widget_js(agent_id, branding="myndwell"), mimetype='application/javascript')

@app.route('/galent')
def serve_galent_widget():
    agent_id = request.args.get('agent', '')
    return Response(generate_widget_js(agent_id, branding="galent"), mimetype='application/javascript')

# Log visitor form submissions
@app.route('/log-visitor', methods=['POST'])
def log_visitor():
    data = request.json or {}
    print("=== log-visitor POST ===\n", data, "\nURL:", data.get('url'))

    # Master log
    try:
        res_all = requests.post(GOOGLE_SHEET_WEBHOOK_URL, json=data)
        print("Master sheet:", res_all.status_code)
    except Exception as e:
        print("Error master:", e)

    url = data.get('url', '').lower()

    # Map keywords to webhook URLs (make sure to fill them)
    webhook_map = {
        "kfwcorp": GOOGLE_SHEET_WEBHOOK_URL_KFWCORP,
        "successgyan": GOOGLE_SHEET_WEBHOOK_URL_SUCCESS_GYAN,
        "sybrant": GOOGLE_SHEET_WEBHOOK_URL_SYBRANT,
        "galent": GOOGLE_SHEET_WEBHOOK_URL_GALENT,
        "myndwell": GOOGLE_SHEET_WEBHOOK_URL_MYNDWELL,
    }

    for keyword, hook in webhook_map.items():
        if hook and keyword in url:
            try:
                res = requests.post(hook, json=data)
                print(f"{keyword} sheet:", res.status_code)
            except Exception as e:
                print(f"Error {keyword} sheet:", e)
            break

    return {"status": "ok"}

# Demo pages (inject correct agent IDs)
def render_demo(brand, logo_url, agent_id):
    return f"""
<!DOCTYPE html>
<html>
<head><title>{brand.title()} Demo</title></head>
<body style="text-align:center;padding:20px;">
  <img src="{logo_url}" alt="{brand} logo" height="60"><h2>{brand.title()} Voice Demo</h2>
  <script src="/{brand}?agent={agent_id}"></script>
</body>
</html>"""

@app.route('/demo/kfwcorp')
def demo_kfw():
    return render_template_string(render_demo(
        'kfwcorp',
        'https://kfwcorp.com/assets/img/logo-w.png',
        'agent_01jzm4vq12f58bfgnyr07ac819'
    ))

@app.route('/demo/successgyan')
def demo_successgyan():
    return render_template_string(render_demo(
        'successgyan',
        'https://successgyan.com/wp-content/uploads/2024/02/SG-logo-1@2x-150x67.png',
        'agent_01k06m09xefx4vxwc0drtf6sje'
    ))

@app.route('/demo/myndwell')
def demo_myndwell():
    return render_template_string(render_demo(
        'myndwell',
        'https://myndwell.io/wp-content/uploads/2022/11/logo.png',
        'agent_01k099ck2mf0tr5g558de7w0av'
    ))

@app.route('/')
def home():
    return "Voice Widget Server Running!"

@app.route('/health')
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
