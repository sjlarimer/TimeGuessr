import os
import random
import base64
import io
import streamlit as st
from PIL import Image

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


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
    _set_background(_get_base64_image(random.choice(candidates)), lightness_level)
