import base64
import json
import streamlit as st
import streamlit.components.v1 as components


def load_css():
    try:
        with open("styles.css", encoding="utf-8") as f:
            css = f.read()
    except FileNotFoundError:
        return

    try:
        with open("Images/logo.png", "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        logo_b64 = None

    # Inject into body immediately for the current render
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    # Inject CSS into <head> and keep the logo alive via MutationObserver.
    # Streamlit is a SPA — the <head> is never torn down, but sidebar components
    # re-render on every page navigation, causing st.logo() to blink. Instead we
    # inject the logo img directly into the sidebar header DOM and use a
    # MutationObserver to re-insert it instantly if React removes it.
    css_json = json.dumps(css)
    logo_js = ""
    if logo_b64:
        logo_js = f"""
            var logoSrc = 'data:image/png;base64,{logo_b64}';
            var logoId  = 'tg-persistent-logo';
            function ensureLogo() {{
                var header = doc.querySelector('[data-testid="stSidebarHeader"]');
                if (!header || doc.getElementById(logoId)) return;
                var img = doc.createElement('img');
                img.id  = logoId;
                img.src = logoSrc;
                header.appendChild(img);
            }}
            ensureLogo();
            if (!win._tgLogoObserver) {{
                win._tgLogoObserver = new MutationObserver(ensureLogo);
                win._tgLogoObserver.observe(doc.body, {{ childList: true, subtree: true }});
            }}
        """

    components.html(
        f"""<script>
        (function() {{
            var doc = window.parent.document;
            var win = window.parent;

            var cssId = 'timeguessr-global-css';
            if (!doc.getElementById(cssId)) {{
                var s = doc.createElement('style');
                s.id = cssId;
                s.textContent = {css_json};
                doc.head.appendChild(s);
            }}

            {logo_js}
        }})();
        </script>""",
        height=0,
    )
