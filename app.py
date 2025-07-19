from flask import Flask, request, Response
from flask_cors import CORS
from flask import render_template_string
import requests


app = Flask(__name__)
CORS(app)

# --- Constants ---
# GOOGLE_SHEET_WEBHOOK_URL = (
#     'https://script.google.com/macros/s/'
#     'AKfycbwrkqqFYAuoV9_zg1PYSC5Cr134XZ6mD_OqMhjX_oxMq7fzINpMQY46HtxgR0gkj1inPA/exec'
# )

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

        // Add form modal
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

                localStorage.setItem("convai_form_submitted", (Date.now() + (1 * 24 * 60 * 60 * 1000)).toString());
                document.getElementById('visitor-form-modal').style.display = 'none';

                const widget = document.querySelector('elevenlabs-convai');
                const realBtn = widget?.shadowRoot?.querySelector('button[title="Start a call"]');
                realBtn?.click();
            }});
        }});

        // Poll for shadow DOM and override branding
        const interval = setInterval(() => {{
            const widget = document.querySelector('elevenlabs-convai');
            if (!widget || !widget.shadowRoot) return;
            const shadowRoot = widget.shadowRoot;

            // Hide all branding elements
            const brandingElem = shadowRoot.querySelector('[class*="poweredBy"], div[part="branding"]');
            if (brandingElem) brandingElem.remove();

            const feedback = shadowRoot.querySelector("div[part='feedback-button']");
            if (feedback) feedback.remove();

            const logo = shadowRoot.querySelector("img[alt*='logo']");
            if (logo) logo.remove();

            // Replace Start Call button
            const realBtn = shadowRoot.querySelector('button[title="Start a call"]');
            if (realBtn && !realBtn._replaced) {{
                realBtn._replaced = true;
                realBtn.style.display = "none";

                const wrapper = document.createElement("div");
                wrapper.style = "position: fixed; bottom: 30px; right: 30px; z-index: 99999;";
                const customBtn = document.createElement("button");
                customBtn.textContent = "Start a Call";
                customBtn.style = `
                    padding: 12px 24px;
                    background: #1e88e5;
                    color: white;
                    font-size: 16px;
                    border: none;
                    border-radius: 30px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    cursor: pointer;
                `;
                wrapper.appendChild(customBtn);
                document.body.appendChild(wrapper);

                customBtn.addEventListener("click", () => {{
                    const expiry = localStorage.getItem("convai_form_submitted");
                    if (expiry && Date.now() < parseInt(expiry)) {{
                        realBtn.click();
                    }} else {{
                        document.getElementById("visitor-form-modal").style.display = "flex";
                    }}
                }});
            }}

            clearInterval(interval); // Stop polling once set
        }}, 300);
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
    js = generate_widget_js(agent_id, branding="Powered by successgyan")
    return Response(js, mimetype='application/javascript')

@app.route('/kfwcorp')
def serve_kfwcorp_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by kfwcorp")
    return Response(js, mimetype='application/javascript')

@app.route('/myndwell')
def serve_myndwell_widget():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by myndwell")
    return Response(js, mimetype='application/javascript')

@app.route('/galent')
def serve_galent():
    agent_id = request.args.get('agent', 'YOUR_DEFAULT_AGENT_ID')
    js = generate_widget_js(agent_id, branding="Powered by galent")
    return Response(js, mimetype='application/javascript')


# --- Form Submission Logging ---
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


# --- Demo Pages ---
@app.route('/demo/successgyan')
def demo_successgyan():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SuccessGyan Voice Agent Demo</title>
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
        <h2>SuccessGyan Voice Assistant Demo</h2>
        <div class="widget-wrapper">
            <script src="/successgyan?agent=agent_01k06m09xefx4vxwc0drtf6sje"></script>
        </div>
        <script>
  const observer = new MutationObserver(() => {
    const widget = document.querySelector('elevenlabs-convai');
    if (!widget || !widget.shadowRoot) return;

    const shadow = widget.shadowRoot;
    const branding = shadow.querySelector('[class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"]');

    if (branding) {
      branding.remove(); // ✅ REMOVE instead of hiding
    }

    // Unhide widget once safe
    const blocker = document.getElementById("branding-blocker");
    if (blocker) blocker.remove();

    // Stop observing once branding handled
    observer.disconnect();
  });

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
        <title>kfwcorp Voice Agent Demo</title>
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
        <h2>KFWCorp Voice Assistant Demo</h2>
        <div class="widget-wrapper">
            <script src="/kfwcorp?agent=agent_01jzm4vq12f58bfgnyr07ac819"></script>
        </div>
        <script>
  const observer = new MutationObserver(() => {
    const widget = document.querySelector('elevenlabs-convai');
    if (!widget || !widget.shadowRoot) return;

    const shadow = widget.shadowRoot;
    const branding = shadow.querySelector('[class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"]');

    if (branding) {
      branding.remove(); // ✅ REMOVE instead of hiding
    }

    // Unhide widget once safe
    const blocker = document.getElementById("branding-blocker");
    if (blocker) blocker.remove();

    // Stop observing once branding handled
    observer.disconnect();
  });

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
        <title>Myndwell Voice Agent Demo</title>
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
        <h2>Myndwell Voice Assistant Demo</h2>
        <div class="widget-wrapper">
            <script src="/myndwell?agent=agent_01k099ck2mf0tr5g558de7w0av"></script>
        </div>
        <script>
  const observer = new MutationObserver(() => {
    const widget = document.querySelector('elevenlabs-convai');
    if (!widget || !widget.shadowRoot) return;

    const shadow = widget.shadowRoot;
    const branding = shadow.querySelector('[class*="poweredBy"], div[part="branding"], a[href*="elevenlabs"]');

    if (branding) {
      branding.remove(); // ✅ REMOVE instead of hiding
    }

    // Unhide widget once safe
    const blocker = document.getElementById("branding-blocker");
    if (blocker) blocker.remove();

    // Stop observing once branding handled
    observer.disconnect();
  });

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
        <title>Galent Voice Agent Demo</title>
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
        <h2>Galent Voice Assistant Demo</h2>
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
