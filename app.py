from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# --- Config: Google Sheets Webhook ---
GOOGLE_SHEET_WEBHOOK_URL = 'https://script.google.com/macros/s/AKfycbwrkqqFYAuoV9_zg1PYSC5Cr134XZ6mD_OqMhjX_oxMq7fzINpMQY46HtxgR0gkj1inPA/exec'

# --- Config: Brand-Based Agent and Branding ---
BRANDS = {
    "sybrant": {
        "agent_id": "agent_01jx2adczxfw7rrv6n8ffbfsb1",
        "branding": "Powered by Sybrant"
    },
    "leaserush": {
        "agent_id": "agent_01234xyzleaserush56789",
        "branding": "Powered by Leaserush"
    },
    "default": {
        "agent_id": "agent_default123",
        "branding": "Powered by Delve-In"
    }
}

# --- Widget Script Generator ---
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
                        font-size: 12px;
                        font-family: Arial, sans-serif;
                        color: #888;
                        text-align: right;
                        margin-top: 10px;
                        margin-bottom: 40px;
                    }}
                    [class*="_avatar_"] {{ display: none; }}
                    [class*="_box_"] {{
                        background: transparent;
                        box-shadow: none;
                        border: none;
                        padding: 0;
                        margin: 0;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    [class*="_btn_"] {{
                        border-radius: 30px;
                        padding: 10px 20px;
                        background-color: #0b72e7;
                        color: #fff;
                        border: none;
                        cursor: pointer;
                        font-weight: 500;
                        font-size: 14px;
                    }}
                    div[part='feedback-button'], img[alt*='logo'] {{ display: none; }}
                `;
                shadowRoot.appendChild(style);
            }}

            const startCallButton = shadowRoot.querySelector('button[title="Start a call"]');
            if (startCallButton && !startCallButton._hooked) {{
                startCallButton._hooked = true;
                const clone = startCallButton.cloneNode(true);
                startCallButton.style.display = 'none';

                clone.style.backgroundColor = "#0b72e7";
                clone.style.color = "#fff";
                clone.style.padding = "10px 20px";
                clone.style.borderRadius = "6px";
                clone.style.cursor = "pointer";

                const wrapper = document.createElement("div");
                wrapper.appendChild(clone);
                startCallButton.parentElement.appendChild(wrapper);

                clone.addEventListener("click", () => {{
                    const expiry = localStorage.getItem("convai_form_submitted");
                    if (expiry && Date.now() < parseInt(expiry)) {{
                        startCallButton.click();
                    }} else {{
                        document.getElementById("visitor-form-modal").style.display = "flex";
                    }}
                }});
            }}
        }});
        observer.observe(document.body, {{ childList: true, subtree: true }});

        window.addEventListener('DOMContentLoaded', () => {{
            const modal = document.createElement("div");
            modal.id = "visitor-form-modal";
            modal.style = `
                display: none;
                position: fixed;
                z-index: 99999;
                top: 0; left: 0;
                width: 100%; height: 100%;
                background: rgba(0,0,0,0.5);
                align-items: center;
                justify-content: center;
            `;

            modal.innerHTML = `
                <div style="
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    width: 320px;
                    position: relative;
                    font-family: sans-serif;
                ">
                    <span id="close-form" style="
                        position: absolute;
                        top: 10px; right: 15px;
                        cursor: pointer;
                        font-size: 18px;
                        font-weight: bold;">&times;</span>

                    <form id="visitor-form">
                        <h3>Tell us about you</h3>
                        <input type="text" name="name" placeholder="Name" required style="width: 100%; margin: 10px 0; padding: 8px;" />
                        <input type="tel" name="mobile" placeholder="Mobile (+91...)" required style="width: 100%; margin: 10px 0; padding: 8px;" />
                        <input type="email" name="email" placeholder="Email" required style="width: 100%; margin: 10px 0; padding: 8px;" />
                        <button type="submit" style="width: 100%; padding: 10px; background: #1e88e5; color: white; border: none; border-radius: 4px;">Start Call</button>
                    </form>
                </div>
            `;
            document.body.appendChild(modal);

            const closeBtn = document.getElementById("close-form");
            closeBtn.onclick = () => modal.style.display = "none";
            window.onclick = (e) => {{
                if (e.target === modal) modal.style.display = "none";
            }};

            document.getElementById("visitor-form").addEventListener("submit", function(e) {{
                e.preventDefault();
                const name = this.name.value.trim();
                const mobile = this.mobile.value.trim();
                const email = this.email.value.trim();
                const url = window.location.href;

                fetch("/log-visitor", {{
                    method: "POST",
                    headers: {{ "Content-Type": "application/json" }},
                    body: JSON.stringify({{ name, mobile, email, url }})
                }})
                .then(() => {{
                    localStorage.setItem("convai_form_submitted", (Date.now() + 86400000).toString());
                    modal.style.display = "none";
                    const realBtn = document.querySelector("elevenlabs-convai")?.shadowRoot?.querySelector('button[title="Start a call"]');
                    realBtn?.click();
                }});
            }});
        }});
    }})();
    """

# --- Widget Script Route ---
@app.route('/convai-widget.js')
def serve_widget():
    brand_key = request.args.get('brand', 'default').lower()
    brand_config = BRANDS.get(brand_key, BRANDS['default'])

    agent_id = brand_config["agent_id"]
    branding = brand_config["branding"]

    js = generate_widget_js(agent_id, branding)
    return Response(js, mimetype='application/javascript')

# --- Visitor Logging Route ---
@app.route('/log-visitor', methods=['POST'])
def log_visitor():
    data = request.get_json()
    required = ["name", "mobile", "email", "url"]

    if not all(field in data and data[field] for field in required):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    try:
        response = requests.post(GOOGLE_SHEET_WEBHOOK_URL, json=data)
        return jsonify({"status": "success", "response": response.text})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Basic Routes ---
@app.route('/')
def home():
    return "Voice Widget Server is running!"

@app.route('/health')
def health():
    return {"status": "healthy"}

# --- Entry Point ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
