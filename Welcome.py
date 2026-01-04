import streamlit as st
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
from PIL import Image
import numpy as np
import random



st.set_page_config(layout='wide')

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
st.markdown(
    """
    <div style='font-family: Poppins; font-size: 16px; line-height: 1.6;'>
        TimeGuessr is a daily geography and history browser game that challenges players to identify the context of historical photographs.
        <br><br>
        Each day, players are presented with five rounds. In each round, an image is revealed, and the goal is to:
        <ul>
            <li><b>Guess the Location:</b> Pinpoint where the photo was taken on a world map.</li>
            <li><b>Guess the Year:</b> Select the year the photo was taken on a timeline.</li>
        </ul>
        Points are awarded based on the accuracy of both the location (distance from the actual spot) and the year (difference from the actual date). A perfect round yields 10,000 points (5,000 for location + 5,000 for year), for a maximum daily score of 50,000.
        <br><br>
        You can play the game yourself <a href="https://timeguessr.com/" target="_blank" style="color: #db5049; text-decoration: none; font-weight: bold;">here</a>.
    </div>
    """, 
    unsafe_allow_html=True
)

st.markdown("""""")

st.markdown("""## Data""")

# --- Data Processing ---
data = pd.read_csv("./Data/Timeguessr_Stats.csv")
data["Date"] = pd.to_datetime(data["Date"]).dt.date

data["Michael Total Score"] = pd.to_numeric(data["Michael Total Score"], errors="coerce")
data["Sarah Total Score"] = pd.to_numeric(data["Sarah Total Score"], errors="coerce")

# Group by date
daily = data.groupby("Date", as_index=False).agg(
    michael_played=("Michael Total Score", lambda x: x.notna().any()),
    sarah_played=("Sarah Total Score", lambda x: x.notna().any())
)

# --- CALCULATIONS ---

# 1. Define the cutoff dates
date_1020 = pd.to_datetime("2025-10-20").date()
date_1010 = pd.to_datetime("2025-10-10").date()

# 2. Create filtered dataframes
daily_since_1020 = daily[daily["Date"] >= date_1020]
daily_since_1010 = daily[daily["Date"] >= date_1010]

# 3. Helper function to calculate the 4 metrics for any dataframe
def get_stats(df):
    total = len(df)
    both = ((df["michael_played"]) & (df["sarah_played"])).sum()
    m_only = ((df["michael_played"]) & (~df["sarah_played"])).sum()
    s_only = ((~df["michael_played"]) & (df["sarah_played"])).sum()
    return total, both, m_only, s_only

# 4. Get values for all three timeframes
all_total, all_both, all_m, all_s = get_stats(daily)
s1020_total, s1020_both, s1020_m, s1020_s = get_stats(daily_since_1020)
s1010_total, s1010_both, s1010_m, s1010_s = get_stats(daily_since_1010)

# --- DISPLAY: Grid Table ---
st.markdown(
    f"""
    <style>
        .stat-table {{
            width: 100%;
            font-family: Poppins;
            font-size: 18px;
            color: #db5049;
            border-collapse: collapse;
        }}
        .stat-table th {{
            text-align: center; /* Center headers */
            padding-bottom: 10px;
            border-bottom: 2px solid #db5049;
        }}
        /* Left align the first column header specifically */
        .stat-table th:first-child {{
            text-align: left;
        }}
        .stat-table td {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .stat-val {{
            font-weight: bold;
            text-align: center;
        }}
    </style>

    <table class="stat-table">
        <thead>
            <tr>
                <th style="width: 30%;">Metric</th>
                <th>All Time</th>
                <th>Post-Sarah Tracking (10/20/25)</th>
                <th>Post-Michael Tracking (10/10/25)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Total Days Played</td>
                <td class="stat-val">{all_total}</td>
                <td class="stat-val">{s1020_total}</td>
                <td class="stat-val">{s1010_total}</td>
            </tr>
            <tr>
                <td>Days Both Played</td>
                <td class="stat-val">{all_both}</td>
                <td class="stat-val">{s1020_both}</td>
                <td class="stat-val">{s1010_both}</td>
            </tr>
            <tr>
                <td>Days Only Michael Played</td>
                <td class="stat-val">{all_m}</td>
                <td class="stat-val">{s1020_m}</td>
                <td class="stat-val">{s1010_m}</td>
            </tr>
            <tr>
                <td>Days Only Sarah Played</td>
                <td class="stat-val">{all_s}</td>
                <td class="stat-val">{s1020_s}</td>
                <td class="stat-val">{s1010_s}</td>
            </tr>
        </tbody>
    </table>
    <br>
    """,
    unsafe_allow_html=True
)

display_data = data.iloc[::-1]

display_data = display_data[['Date', 'City', 'Country', 'Year', 
                             'Michael Total Score', 'Sarah Total Score', 'Michael Round Score', 'Sarah Round Score',
                             'Michael Geography', 'Sarah Geography', 'Michael Time', 'Sarah Time']]

st.dataframe(display_data)
    