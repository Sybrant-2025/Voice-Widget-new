from flask import Flask, request, Response
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Google Sheet Webhook URL (for logging form submissions)
GOOGLE_SHEET_WEBHOOK_URL = 'https://script.google.com/macros/s/AKfycbwrkqqFYAuoV9_zg1PYSC5Cr134XZ6mD_OqMhjX_oxMq7fzINpMQY46HtxgR0gkj1inPA/exec'

# -----------------------------
# JS GENERATOR
# -----------------------------
def generate_widget_js(agent_id, branding):
    return f"""
    (function() {{
        const tag = document.createElement("elevenlabs-convai");
        tag.setAttribute("agent-id", "{agent_id}");
        document.body.appendChild(tag);

        const script = document.createElement("script");
        script.src = "https://elevenlabs.io/convai-widget/index.js";
        script.async = true;
        document.body.appendChild(script);

        const observer = new MutationObserver(() => {{
            const widget = document.querySelector('elevenlabs-convai');
            if (!widget || !widget.shadowRoot) return;
            const shadowRoot = widget.shadowRoot;

            const brandingElem = shadowRoot.querySelector('[class*="poweredBy"], div[part="branding"]');
            if (brandingElem) {{
                brandingElem.textContent = "{branding}";
            }}

            if (!shadowRoot.querySelector("#custom-style")) {{
                const style = document.createElement("style");
                style.id = "custom-style";
                style.textContent = `
                    div[part='branding'] {{
                        font-size: 12px !important;
                        font-family: Arial, sans-serif !important;
                        color: #888 !important;
                        text-align: right;
                        margin-top: 10px;
                        margin-bottom: 40px;
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
                    body: JSON.stringify({{ name, mobile, email, url }})
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

# -----------------------------
# ROUTES
# -----------------------------
@app.route('/')
def home():
    return "Voice Widget Server Running!"

@app.route('/health')
def health():
    return {"status": "healthy"}

@app.route('/log-visitor', methods=['POST'])
def log_visitor():
    data = request.json
    print("Visitor Info:", data)
    try:
        res = requests.post(GOOGLE_SHEET_WEBHOOK_URL, json=data)
        print("Google Sheet Response:", res.text)
    except Exception as e:
        print("Error sending to Google Sheet:", e)
    return {"status": "ok"}

@app.route('/convai-widget.js')
def serve_sybrant_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by Sybrant")
    return Response(js, mimetype='application/javascript', headers={"Access-Control-Allow-Origin": "*"})

@app.route('/successgyan')
def serve_successgyan_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by successgyan")
    return Response(js, mimetype='application/javascript', headers={"Access-Control-Allow-Origin": "*"})

@app.route('/kfwcorp')
def serve_kfwcorp_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by kfwcorp")
    return Response(js, mimetype='application/javascript', headers={"Access-Control-Allow-Origin": "*"})

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
