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
def generate_widget_js(agent_id, branding):
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
            a[href*="conversational"]),
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
        <img src="{logo_url}" alt="{brand} logo" height="60">
        <h2>{brand.title()} Voice Demo</h2>
        <script src="/{brand}?agent={agent_id}"></script>

        <script>
        function customizeConvaiWidget() {{
            const convaiEl = document.querySelector("elevenlabs-convai");
            if (!convaiEl || !convaiEl.shadowRoot) {{
                setTimeout(customizeConvaiWidget, 300);
                return;
            }}

            const shadow = convaiEl.shadowRoot;

            // Hide avatar
            const avatar = shadow.querySelector("._avatar_1f9vw_68");
            if (avatar) avatar.style.display = "none";

            // Transparent chat box
            const box = shadow.querySelector("._box_1f9vw_39");
            if (box) {{
                box.style.backgroundColor = "transparent";
                box.style.boxShadow = "none";
                box.style.border = "none";
                box.style.outline = "none";
            }}
        }}

        window.addEventListener("DOMContentLoaded", () => {{
            setTimeout(customizeConvaiWidget, 1000);
        }});
        </script>
    </body>
    </html>
    """


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

@app.route('/demo/orientbell')
def demo_orientbell():
    return render_template_string(render_demo(
        'Orientbell',
        'https://tiles.orientbell.com/landingpage/logo/logo.png',
        'agent_0501k16aqfe5f0xvnp0eg2c532bt'
    ))


@app.route('/')
def home():
    return "Voice Widget Server Running!"

@app.route('/health')
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
