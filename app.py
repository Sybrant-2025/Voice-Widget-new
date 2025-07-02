from flask import Flask, request, Response
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)


# --- Constants ---
# not working_GOOGLE_SHEET_WEBHOOK_URL = 'https://script.google.com/macros/s/AKfycbysX7ZKHVAsxTmGoZeVBV65Q8imTgSEmwsrW27crcqJzDxQjCx9w-EeXMLnckmlFz38Uw/exec'
# working live dhilak sheet
GOOGLE_SHEET_WEBHOOK_URL = 'https://script.google.com/macros/s/AKfycbwrkqqFYAuoV9_zg1PYSC5Cr134XZ6mD_OqMhjX_oxMq7fzINpMQY46HtxgR0gkj1inPA/exec'

# --- JS Generator ---
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
                        margin-right: 30px;
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
                <form id="visitor-form" style="
                    background: white;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    width: 320px;
                    font-family: sans-serif;
                ">
                    <h3 style="margin-bottom: 15px;">Tell us about you</h3>
                    <input type="text" placeholder="Name" name="name" required style="margin-bottom: 10px; width: 100%; padding: 8px;" />
                    <input type="tel" placeholder="Mobile (+91...)" name="mobile" required style="margin-bottom: 10px; width: 100%; padding: 8px;" />
                    <input type="email" placeholder="Email" name="email" required style="margin-bottom: 20px; width: 100%; padding: 8px;" />
                    <button type="submit" style="width: 100%; padding: 10px; background: #1e88e5; color: white; border: none; border-radius: 4px;">Start Call</button>
                </form>
            `;
            document.body.appendChild(modal);

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

                fetch('https://voice-widget-new-production.up.railway.app/log-visitor', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ name, mobile, email, url }})
                }});

                localStorage.setItem("convai_form_submitted", (Date.now() +  (1 * 24 * 60 * 60 * 1000)).toString());
                document.getElementById('visitor-form-modal').style.display = 'none';

                const widget = document.querySelector('elevenlabs-convai');
                const shadowRoot = widget?.shadowRoot;
                const realBtn = shadowRoot?.querySelector('button[title="Start a call"]');
                realBtn?.click();
            }});
        }});
    }})();
    """

# --- Routes ---
@app.route('/convai-widget.js')
def serve_sybrant_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by Sybrant")
    return Response(js, mimetype='application/javascript')

@app.route('/leaserush-widget.js')
def serve_leaserush_widget():
    agent_id = request.args.get('agent', 'agent_01jvscwr0gf66r27cb61rhj5zc')
    js = generate_widget_js(agent_id, branding="Powered by Leaserush")  # <-- Correct branding
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

# # --- Run Server ---
# if __name__ == '__main__':
#     port = int(os.environ.get("PORT", 5000))
#     app.run(debug=True, host='0.0.0.0', port=port)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

