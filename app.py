from flask import Flask, request, Response
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

GOOGLE_SHEET_WEBHOOK_URL = 'https://script.google.com/macros/s/AKfycbwrkqqFYAuoV9_zg1PYSC5Cr134XZ6mD_OqMhjX_oxMq7fzINpMQY46HtxgR0gkj1inPA/exec'

@app.route('/convai-widget.js')
def serve_sybrant_widget():
    agent_id = request.args.get('agent', 'agent_01jx2adczxfw7rrv6n8ffbfsb1')
    js = generate_widget_js(agent_id)
    return Response(js, mimetype='application/javascript')

def generate_widget_js(agent_id):
    return f"""
    (function() {{
        const tag = document.createElement("elevenlabs-convai");
        tag.setAttribute("agent-id", "{agent_id}");
        tag.style.display = "none";
        document.body.appendChild(tag);

        const script = document.createElement("script");
        script.src = "https://elevenlabs.io/convai-widget/index.js";
        script.async = true;
        document.body.appendChild(script);

        // Modal form
        const modal = document.createElement('div');
        modal.id = 'visitor-form-modal';
        modal.style = `
            display: none;
            position: fixed;
            z-index: 99999;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.5);
            align-items: center;
            justify-content: center;
        `;
        modal.innerHTML = `
            <div style="background: white; padding: 20px; border-radius: 10px; width: 300px; position: relative;">
                <span id="close-form" style="position: absolute; top: 10px; right: 15px; font-size: 20px; cursor: pointer;">&times;</span>
                <form id="visitor-form">
                    <h3>Tell us about you</h3>
                    <input name="name" placeholder="Name" required style="width:100%;margin-bottom:10px;padding:8px"/>
                    <input name="mobile" placeholder="Mobile (+91...)" required style="width:100%;margin-bottom:10px;padding:8px"/>
                    <input name="email" placeholder="Email" required style="width:100%;margin-bottom:15px;padding:8px"/>
                    <button type="submit" style="width:100%;padding:10px;background:#1e88e5;color:white;border:none;border-radius:5px">Start Call</button>
                </form>
            </div>
        `;
        document.body.appendChild(modal);

        const closeForm = modal.querySelector("#close-form");
        closeForm.onclick = () => modal.style.display = "none";
        window.onclick = e => {{ if (e.target === modal) modal.style.display = "none"; }};

        // Widget observer
        const observer = new MutationObserver(() => {{
            const widget = document.querySelector("elevenlabs-convai");
            if (!widget || !widget.shadowRoot) return;
            const shadow = widget.shadowRoot;

            // Remove branding/logo/extra UI
            shadow.querySelectorAll('[part="branding"], a[href*="elevenlabs"], img, [class*="feedback"], [class*="_avatar_"], [class*="_box_"]').forEach(el => el.remove());

            if (!shadow.querySelector("style#clean-style")) {{
                const style = document.createElement("style");
                style.id = "clean-style";
                style.textContent = `
                    button[title="Start a call"] {{ background: #000; color: #fff; padding: 10px 15px; border-radius: 8px; font-size: 14px; }}
                `;
                shadow.appendChild(style);
            }}

            const realBtn = shadow.querySelector('button[title="Start a call"]');
            if (realBtn && !realBtn._cloned) {{
                realBtn._cloned = true;
                const clone = realBtn.cloneNode(true);
                realBtn.style.display = "none";

                const wrapper = document.createElement("div");
                wrapper.style.position = "fixed";
                wrapper.style.bottom = "20px";
                wrapper.style.right = "20px";
                wrapper.style.zIndex = "9999";
                wrapper.style.textAlign = "center";

                wrapper.appendChild(clone);

                const brandText = document.createElement("div");
                brandText.textContent = "Powered by Sybrant";
                brandText.style = "font-size: 11px; color: #888; margin-top: 6px;";
                wrapper.appendChild(brandText);

                document.body.appendChild(wrapper);

                clone.addEventListener("click", e => {{
                    e.preventDefault();
                    const expiry = localStorage.getItem("convai_form_submitted");
                    if (expiry && Date.now() < parseInt(expiry)) {{
                        realBtn.click();
                    }} else {{
                        modal.style.display = "flex";
                    }}
                }});
            }}
        }});
        observer.observe(document.body, {{ childList: true, subtree: true }});

        // Form submission logic
        document.addEventListener("DOMContentLoaded", () => {{
            document.getElementById("visitor-form").addEventListener("submit", function(e) {{
                e.preventDefault();
                const name = this.name.value.trim();
                const mobile = this.mobile.value.trim();
                const email = this.email.value.trim();
                const url = window.location.href;

                if (!name || !mobile || !email) {{
                    alert("Please fill all fields");
                    return;
                }}

                fetch("https://voice-widget-new-production.up.railway.app/log-visitor", {{
                    method: "POST",
                    headers: {{ "Content-Type": "application/json" }},
                    body: JSON.stringify({{ name, mobile, email, url }})
                }}).then(() => {{
                    localStorage.setItem("convai_form_submitted", (Date.now() + 86400000).toString());
                    modal.style.display = "none";
                    const widget = document.querySelector("elevenlabs-convai");
                    const realBtn = widget?.shadowRoot?.querySelector('button[title="Start a call"]');
                    realBtn?.click();
                }});
            }});
        }});
    }})();
    """

@app.route('/log-visitor', methods=['POST'])
def log_visitor():
    data = request.json
    try:
        res = requests.post(GOOGLE_SHEET_WEBHOOK_URL, json=data)
        return {"status": "ok", "response": res.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/')
def home():
    return "Voice Widget Server Running!"

@app.route('/health')
def health():
    return {"status": "healthy"}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
