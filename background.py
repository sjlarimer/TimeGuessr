import os
import random
import base64
import io
import streamlit as st
from PIL import Image

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@st.cache_data(show_spinner=False)
def _get_base64_image(image_path):
    try:
        img = Image.open(image_path)
        file_format = img.format if img.format is not None else 'PNG'
        buffer = io.BytesIO()
        img.save(buffer, format=file_format)
        return base64.b64encode(buffer.getvalue()).decode()
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _set_background(base64_string, lightness_level=0.7):
    if not base64_string:
        return
    rgba = f"rgba(255, 255, 255, {lightness_level})"
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: linear-gradient({rgba}, {rgba}),
                          url("data:image/png;base64,{base64_string}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
    }}
    </style>
    """, unsafe_allow_html=True)


def _page_key(page_file):
    return os.path.splitext(os.path.basename(page_file))[0] or "_default"


def mark_page_active(page_file):
    """This app's "did we just navigate to a different page" signal. Every
    page calls this near the top of its script, passing its own __file__, so
    the stored page_key always reflects whichever page last ran. Returns
    True exactly when the calling page differs from that — i.e. this is a
    fresh arrival, not a rerun triggered by interacting with a widget on the
    same page.

    Takes `page_file` explicitly (rather than inspecting the caller's stack
    frame) so this keeps working the same way regardless of Python/Streamlit
    version or how the page script happens to be executed — the previous
    frame-introspection approach was found to silently break under some
    environments, leaving the page-switch signal permanently False."""
    page_key = _page_key(page_file)
    state_key = "_active_page_key"
    prev = st.session_state.get(state_key)
    st.session_state[state_key] = page_key
    return prev != page_key


def set_random_sarah_background(page_file, lightness_level=0.7):
    """Sets a random Sarah photo as the page background, keeping the same
    choice across reruns of the same page and re-randomizing on navigation.
    Also returns the mark_page_active() page-switch signal (see above) —
    kept independent of whether any background images are actually found,
    so a missing/renamed Images folder on some machine can't silently break
    that signal for callers (e.g. the Daily page's date-reset) too."""
    switched_page = mark_page_active(page_file)

    image_dir = "Images"
    try:
        candidates = [
            os.path.join(image_dir, f)
            for f in os.listdir(image_dir)
            if "Sarah" in f and os.path.splitext(f)[1].lower() in _IMAGE_EXTS
        ]
    except OSError:
        candidates = []
    if not candidates:
        return switched_page

    page_key = _page_key(page_file)
    state_key = "_sarah_bg_choice"
    stored = st.session_state.get(state_key)
    if switched_page or stored is None or stored[0] != page_key or stored[1] not in candidates:
        choice = random.choice(candidates)
        st.session_state[state_key] = (page_key, choice)
    else:
        choice = stored[1]

    _set_background(_get_base64_image(choice), lightness_level)
    return switched_page
