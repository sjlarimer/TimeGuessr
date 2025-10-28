import streamlit as st
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
from PIL import Image
import numpy as np

st.set_page_config(layout='wide')

st.logo("Images/logo.png")

# --- Top centered title ---
st.markdown("<h1 style='text-align: center;'>Michael and Sarah</h1>", unsafe_allow_html=True)

# --- Top center image with bottom 25% cropped ---
img = Image.open("Images/home.png")
width, height = img.size
crop_height = int(height * 0.75)  # keep top 75%
img_cropped = img.crop((0, 0, width, crop_height))

col1, col2, col3 = st.columns([1, 2, 1])  # center column
with col2:
    st.image(img_cropped, use_container_width=True)

# --- Centered subtitle ---
st.markdown("<h1 style='text-align: center;'>Score Tracking</h2>", unsafe_allow_html=True)

st.markdown("""## Overview""")
st.markdown("Timeguessr is a geography and history based game. The link can be found [here](https://timeguessr.com/)")

# --- Side by side images ---
col1, col2 = st.columns(2)
with col1:
    st.image("Images/Results.png")  # optional secondary image

st.markdown("""## Data""")
data = pd.read_csv("./Data/Timeguessr_Stats.csv")
st.dataframe(data)