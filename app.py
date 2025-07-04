from flask import Flask, request, Response
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

GOOGLE_SHEET_WEBHOOK_URL = 'https://script.google.com/macros/s/AKfycbwrkqqFYAuoV9_zg1PYSC5Cr134XZ6mD_OqMhjX_oxMq7fzINpMQY46HtxgR0gkj1inPA/exec'

def generate_widget_js(agent_id, branding):
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

        // Create modal form
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
        window.onclick = (e) => {
            if (e.target === modalEl) modalEl.style.display = 'none';
        };

        document.getElementById("visitor-form").addEventListener("submit", function(e) {
            e.preventDefault();
            const name = this.name.value.trim();
            const mobile = this.mobile.value.trim();
            const email = this.email.value.trim();
            const url = window.location.href;

            if (!name || !mobile || !email) {
                alert("Please fill all fields");
                return;
            }

            fetch("https://voice-widget-new-production.up.railway.app/log-visitor", {
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({ name, mobile, email, url })
            }).then(() => {
                localStorage.setItem("convai_form_submitted", (Date.now() + 86400000).toString());
                modalEl.style.display = "none";
                const realBtn = document.querySelector("elevenlabs-convai")?.shadowRoot?.querySelector('button[title="Start a call"]');
                realBtn?.click();
            });
        });

        function waitForWidget() {
            const widget = document.querySelector("elevenlabs-convai");
            if (!widget || !widget.shadowRoot) return setTimeout(waitForWidget, 500);

            const shadow = widget.shadowRoot;

            const realBtn = shadow.querySelector('button[title="Start a call"]');
            if (!realBtn || realBtn._cloned) return setTimeout(waitForWidget, 500);

            // Hide all default ElevenLabs UI
            shadow.querySelectorAll('[part="branding"], a[href*="elevenlabs"], img, [class*="feedback"], [class*="_avatar_"], [class*="_box_"]').forEach(el => el.remove());

            if (!shadow.querySelector("#clean-style")) {
                const style = document.createElement("style");
                style.id = "clean-style";
                style.textContent = `
                    button[title="Start a call"] {{
                        background: #000;
                        color: #fff;
                        padding: 10px 15px;
                        border-radius: 8px;
                        font-size: 14px;
                    }}
                `;
                shadow.appendChild(style);
            }

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
            document.body.appendChild(wrapper);

            clone.addEventListener("click", e => {
                e.preventDefault();
                const expiry = localStorage.getItem("convai_form_submitted");
                if (expiry && Date.now() < parseInt(expiry)) {
                    realBtn.click();
                } else {
                    modalEl.style.display = "flex";
                }
            });
        }

        setTimeout(waitForWidget, 1000);
    }})();
    """

# Routes
@app.route('/convai-widget.js')
def serve_sybrant_widget():
    agent_id = request.args.get('agent', 'agent_01jx2adczxfw7rrv6n8ffbfsb1')
    js = generate_widget_js(agent_id, branding="Powered by Sybrant")
    return Response(js, mimetype='application/javascript')

@app.route('/leaserush-widget.js')
def serve_leaserush_widget():
    agent_id = request.args.get('agent', 'agent_01jvscwr0gf66r27cb61rhj5zc')
    js = generate_widget_js(agent_id, branding="Powered by Leaserush")
    return Response(js, mimetype='application/javascript')

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

@app.route('/')
def home():
    return "Voice Widget Server Running!"

@app.route('/health')
def health():
    return {"status": "healthy"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
