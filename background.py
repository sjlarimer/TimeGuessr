import os
import random
import base64
import io
import inspect
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


def set_random_sarah_background(lightness_level=0.7):
    image_dir = "Images"
    candidates = [
        os.path.join(image_dir, f)
        for f in os.listdir(image_dir)
        if "Sarah" in f and os.path.splitext(f)[1].lower() in _IMAGE_EXTS
    ]
    if not candidates:
        return

    # Identify the page that's calling so the chosen image stays fixed while
    # the user interacts with (reruns) the same page, and only re-randomizes
    # when they navigate to a different page.
    try:
        caller_file = inspect.currentframe().f_back.f_globals.get("__file__", "")
        page_key = os.path.splitext(os.path.basename(caller_file))[0] or "_default"
    except Exception:
        page_key = "_default"

    state_key = "_sarah_bg_choice"
    stored = st.session_state.get(state_key)
    if not stored or stored[0] != page_key or stored[1] not in candidates:
        choice = random.choice(candidates)
        st.session_state[state_key] = (page_key, choice)
    else:
        choice = stored[1]

    _set_background(_get_base64_image(choice), lightness_level)
