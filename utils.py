import json
import streamlit as st
import streamlit.components.v1 as components


def load_css():
    try:
        with open("styles.css", encoding="utf-8") as f:
            css = f.read()
    except FileNotFoundError:
        return

    # Inject into body immediately for the current render
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    # Also inject into the parent document <head> via JS so the CSS persists
    # across page navigation. Streamlit is a SPA — the React root and <head>
    # are never torn down when switching pages, only the page body rerenders.
    # Idempotent: the id check prevents duplicate <style> elements.
    css_json = json.dumps(css)
    components.html(
        f"""<script>
        (function() {{
            var id = 'timeguessr-global-css';
            var doc = window.parent.document;
            if (!doc.getElementById(id)) {{
                var s = doc.createElement('style');
                s.id = id;
                s.textContent = {css_json};
                doc.head.appendChild(s);
            }}
        }})();
        </script>""",
        height=0,
    )
