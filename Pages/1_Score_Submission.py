import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import json
import math
import re
from streamlit.components.v1 import html as components_html

# --- Layout Config ---
st.set_page_config(layout="wide", page_title="Timeguessr Score Submission")

from background import set_random_sarah_background
set_random_sarah_background(lightness_level=0.7)

# --- Setup & Config ---
try:
    from Score_Update import score_update
except ImportError:
    def score_update(): pass

try:
    from aggregation import (
        update_averages_entry, update_community_averages_entry,
        update_actuals_txt_entry, update_player_txt_entry,
    )
except ImportError:
    def update_averages_entry(*args, **kwargs): pass
    def update_community_averages_entry(*args, **kwargs): pass
    def update_actuals_txt_entry(*args, **kwargs): pass
    def update_player_txt_entry(*args, **kwargs): pass

from utils import load_css
load_css()

# --- Global Font Override & CSS ---
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        
        /* Apply font to text elements only, avoiding icons */
        html, body, p, h1, h2, h3, h4, h5, h6, label, input, textarea, select, button {
            font-family: 'Poppins', sans-serif !important;
        }
        
        /* Compact Toggles */
        .stToggle {
            margin-top: 0px !important; 
        }
        
        /* Force color and alignment on Toggle Labels */
        div[data-testid="stToggle"] p,
        div[data-testid="stToggle"] label p,
        div[data-testid="stWidgetLabel"] p {
            font-size: 14px !important;
            font-weight: 400 !important; /* Removed bolding */
            color: #db5049 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* Responsive Score Box */
        .score-box {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 39px; /* Restored exact Streamlit input height for alignment */
            padding: 0 10px;
            margin-top: 0px; /* Removed extra margin to align with prompts */
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 600;
            box-sizing: border-box;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        /* COLOR OVERRIDE: Make all standard text TimeGuessr Red */
        .stMarkdown p, label, h1, h2, h3, h4, h5, h6 {
            color: #db5049 !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

try:
    with open("config.json", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

st.title("Score Submission")
score_update()

# --- 1. Constants ---
COUNTRY_ALIASES = {
    "Russia": "Russian Federation", "Ivory Coast": "Côte d'Ivoire",
    "South Korea": "Korea, Republic of", "North Korea": "Korea, Democratic People's Republic of",
    "Vietnam": "Viet Nam", "Syria": "Syrian Arab Republic",
    "Laos": "Lao People's Democratic Republic", "Bolivia": "Bolivia, Plurinational State of",
    "Venezuela": "Venezuela, Bolivarian Republic of", "Iran": "Iran, Islamic Republic of",
    "Moldova": "Moldova, Republic of", "Tanzania": "Tanzania, United Republic of",
    "Palestine": "Palestine, State of", "Brunei": "Brunei Darussalam",
    "Congo": "Congo, Republic of the", "Democratic Republic of the Congo": "Congo, The Democratic Republic of the",
    "Macau": "Macao", "Taiwan": "Taiwan, Province of China",
    "Cape Verde": "Cabo Verde", "Vatican City": "Holy See (Vatican City State)",
    "Turkey": "Türkiye", "Bosnia": "Bosnia and Herzegovina",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
}

GEOGRAPHY_RANGES = {
    "OOO": (5000, 5000), "OO%": (4750, 4999), "OOX": (4500, 4749),
    "O%X": (4250, 4499), "OXX": (3500, 4249), "%XX": (2500, 3499), "XXX": (12, 2499)
}

TIME_RANGES = {
    "OOO": (5000, 5000), "OO%": (4800, 4950), "OOX": (4300, 4600),
    "O%X": (3400, 3900), "OXX": (2000, 2500), "%XX": (1000, 1000), "XXX": (0, 0)
}

# --- 2. Helper Functions (Visuals & Data) ---
@st.cache_data
def load_data(filepath, mtime):
    try:
        df = pd.read_csv(filepath)
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        return df
    except FileNotFoundError:
        return None

def get_flag_emoji(country_name):
    import pycountry
    fallback = '<img src="https://twemoji.maxcdn.com/v/latest/svg/1f1fa-1f1f3.svg" width="20" style="vertical-align:middle;"/>'
    if not country_name or pd.isna(country_name): return fallback
    name_str = COUNTRY_ALIASES.get(country_name.strip(), country_name.strip())
    try:
        country = pycountry.countries.lookup(name_str)
        code = country.alpha_2.upper()
        codepoints = "-".join([f"1f1{format(ord(c) - ord('A') + 0xE6, 'x')}" for c in code])
        return f'<img src="https://twemoji.maxcdn.com/v/latest/svg/{codepoints}.svg" width="20" style="vertical-align:middle;"/>'
    except LookupError: return fallback

def half_bar_html(score, pattern=None, range_dict=GEOGRAPHY_RANGES):
    total = 5000
    if score is not None and not pd.isna(score):
        pct = min(max(float(score) / total * 100.0, 0.0), 100.0)
        return f'<div class="tg-bar-bg"><div class="tg-bar-fill" style="width:{pct:.2f}%; background:#db5049;"></div></div>'
    elif pattern and pattern in range_dict:
        min_val, max_val = range_dict[pattern]
        min_pct = min_val / total * 100
        max_pct = max_val / total * 100
        return f'''<div class="tg-bar-bg" style="position:relative;"><div style="position:absolute; left:0; width:{min_pct:.2f}%; height:100%; background:#db5049;"></div><div style="position:absolute; left:{min_pct:.2f}%; width:{max_pct - min_pct:.2f}%; height:100%; background:#d1d647;"></div><div style="position:absolute; left:{max_pct:.2f}%; width:{100 - max_pct:.2f}%; height:100%; background:#b0afaa;"></div></div>'''
    return '<div class="tg-bar-bg"><div class="tg-bar-fill" style="width:0%;"></div></div>'

def generate_player_html(player_name, date_rows, players, highlight=False):
    if len(date_rows) == 0: return ""
    row_0 = date_rows.iloc[0]
    total_score = row_0.get(f"{player_name} Total Score")
    all_rounds = date_rows[date_rows["Timeguessr Round"].between(1, 5)]
    
    geo_sum, time_sum = 0, 0
    for _, r in all_rounds.iterrows():
        gs = r.get(f"{player_name} Geography Score")
        gp = r.get(f"{player_name} Geography")
        ts = r.get(f"{player_name} Time Score")
        tp = r.get(f"{player_name} Time")
        
        if pd.notna(gs): geo_sum += gs
        elif gp in GEOGRAPHY_RANGES: geo_sum += sum(GEOGRAPHY_RANGES[gp])/2
        
        if pd.notna(ts): time_sum += ts
        elif tp in TIME_RANGES: time_sum += sum(TIME_RANGES[tp])/2

    total_text = "???" if pd.isna(total_score) else f"{int(total_score):,}/50,000"
    is_michael = player_name == "Michael"
    bg = "#dde5eb" if is_michael else "#edd3df"
    header = "#221e8f" if is_michael else "#8a005c"
    border = "border: 3px solid #db5049; box-shadow: 0 0 15px rgba(219,80,73,0.4);" if highlight else ""

    html = [f'<div class="tg-container" style="background-color: {bg}; {border}"><div class="tg-header" style="color: {header};">{player_name}</div><div class="tg-total">{total_text}</div>']
    
    if geo_sum == 0 and time_sum == 0:
        html.append('<div class="tg-sub">🌎 Geo: <b>???</b>/25,000</div><div class="tg-sub">📅 Time: <b>???</b>/25,000</div>')
    else:
        html.append(f'<div class="tg-sub">🌎 Geo: <b>{int(geo_sum):,}</b>/25,000</div><div class="tg-sub">📅 Time: <b>{int(time_sum):,}</b>/25,000</div>')
    
    html.append('<div class="tg-rounds-wrapper">')
    
    for r_num in range(1, 6):
        r_data = date_rows[date_rows["Timeguessr Round"] == r_num]
        geo_score = time_score = geo_pattern = time_pattern = country_name = None
        if len(r_data) > 0:
            row = r_data.iloc[0]
            geo_score = row.get(f"{player_name} Geography Score")
            time_score = row.get(f"{player_name} Time Score")
            geo_pattern = row.get(f"{player_name} Geography")
            time_pattern = row.get(f"{player_name} Time")
            country_name = row.get("Country")

        round_revealed = True
        if len(r_data) > 0:
            game_date = row_0["Date"]
            if game_date >= datetime.date.today():
                for p in players:
                    if pd.isna(r_data.iloc[0].get(f"{p} Geography Score")):
                        round_revealed = False; break
        else: round_revealed = False
        
        flag = get_flag_emoji(country_name) if round_revealed else get_flag_emoji("United Nations")
        
        g_txt = f"{int(geo_score):,}/5k" if pd.notna(geo_score) else ("???/5k" if geo_pattern not in GEOGRAPHY_RANGES else f"{GEOGRAPHY_RANGES[geo_pattern][0]:,}-{GEOGRAPHY_RANGES[geo_pattern][1]:,}/5k")
        t_txt = f"{int(time_score):,}/5k" if pd.notna(time_score) else ("???/5k" if time_pattern not in TIME_RANGES else f"{TIME_RANGES[time_pattern][0]:,}-{TIME_RANGES[time_pattern][1]:,}/5k")
        
        html.append(f'<div class="tg-round"><div class="tg-row"><div class="tg-half"><div class="tg-score-note">{flag} <small>{g_txt}</small></div>{half_bar_html(geo_score, geo_pattern, GEOGRAPHY_RANGES)}</div><div class="tg-half"><div class="tg-score-note">📅 <small>{t_txt}</small></div>{half_bar_html(time_score, time_pattern, TIME_RANGES)}</div></div></div>')

    html.append('</div></div>')
    return "\n".join(html)

def generate_community_html(date_rows):
    if len(date_rows) == 0: return ""
    row_0 = date_rows.iloc[0]
    total_score = row_0.get("Community Average")
    total_text = "???" if pd.isna(total_score) else f"{int(total_score):,}/50,000"

    # Geo/Time sub-totals aren't reported for the community average, so estimate them
    # by summing each round's estimated geo/time score (from years-off/distance, via
    # the same formulas used for players) — display-only, hence the quotation marks.
    geo_sum_est, time_sum_est = 0, 0
    have_geo_est, have_time_est = False, False
    round_scores = []

    for r_num in range(1, 6):
        r_data = date_rows[date_rows["Timeguessr Round"] == r_num]
        row_r = r_data.iloc[0] if len(r_data) > 0 else None
        round_scores.append(row_r.get("Community Round Score") if row_r is not None else None)

        time_off = row_r.get("Community Time Distance") if row_r is not None else None
        if pd.notna(time_off):
            t_est = calculate_time_score(float(time_off), 0)
            if t_est is not None:
                time_sum_est += t_est
                have_time_est = True

        dist_m = row_r.get("Community Geography Distance") if row_r is not None else None
        if pd.notna(dist_m):
            geo_sum_est += geography_score(float(dist_m))
            have_geo_est = True

    html = [f'<div class="tg-container" style="background-color: #e9ecef;"><div class="tg-header" style="color: #495057;">Community</div><div class="tg-total">{total_text}</div>']

    geo_txt = f'"{int(geo_sum_est):,}"' if have_geo_est else '"???"'
    time_txt = f'"{int(time_sum_est):,}"' if have_time_est else '"???"'
    html.append(f'<div class="tg-sub">🌎 Geo: <b>{geo_txt}</b>/25,000</div><div class="tg-sub">📅 Time: <b>{time_txt}</b>/25,000</div>')

    html.append('<div class="tg-rounds-wrapper">')

    for r_num, round_score in zip(range(1, 6), round_scores):
        r_txt = f"{int(round_score):,}/10k" if pd.notna(round_score) else "???/10k"
        pct = min(max(float(round_score) / 10000 * 100.0, 0.0), 100.0) if pd.notna(round_score) else 0
        bar_html = f'<div class="tg-bar-bg"><div class="tg-bar-fill" style="width:{pct:.2f}%; background:#6c757d;"></div></div>'

        html.append(f'<div class="tg-round"><div class="tg-score-note">🏆 <small>{r_txt}</small></div>{bar_html}</div>')

    html.append('</div></div>')
    return "\n".join(html)

@st.cache_data
def load_map_subdivisions(mtime):
    _ = mtime  # cache-busting key only
    path = "./Data/Custom_World_Map_New.json"
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        gj = json.load(f)
    iso_to_names = {}
    for feature in gj.get('features', []):
        props = feature.get('properties', {})
        iso3 = str(props.get('ISO3', '')).strip()
        name = str(props.get('NAME', '')).strip()
        if iso3 and name:
            iso_to_names.setdefault(iso3, set()).add(name)
    return {iso: sorted(names) for iso, names in iso_to_names.items() if len(names) > 1}

def country_to_iso3(country_name):
    import pycountry
    if not country_name:
        return None
    name = COUNTRY_ALIASES.get(country_name.strip(), country_name.strip())
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return None

# --- 3. Math & Logic Helpers ---
def geography_score(x):
    if x <= 50: return 5000
    elif x <= 1000: return 5000 - (x * 0.02)
    elif x <= 5000: return 4980 - (x * 0.016)
    elif x <= 100000: return 4900 - (x * 0.004)
    elif x <= 1000000: return 4500 - (x * 0.001)
    elif x <= 2000000: return 3500 - (x * 0.0005)
    elif x <= 3000000: return 2500 - (x * 0.0003333)
    elif x <= 6000000: return 1500 - (x * 0.0002)
    else: return 12

def calculate_time_score(year_guessed, actual_year):
    if actual_year is None: return None
    years_off = abs(int(year_guessed) - actual_year)
    if years_off == 0: return 5000
    elif years_off == 1: return 4950
    elif years_off == 2: return 4800
    elif years_off == 3: return 4600
    elif years_off == 4: return 4300
    elif years_off == 5: return 3900
    elif years_off in [6, 7]: return 3400
    elif years_off in [8, 9, 10]: return 2500
    elif 10 < years_off < 16: return 2000
    elif 15 < years_off < 21: return 1000
    else: return 0

UNIT_ALIASES = {
    "ft": "ft", "feet": "ft", "foot": "ft",
    "mi": "mi", "mile": "mi", "miles": "mi",
    "m": "m", "meter": "m", "meters": "m", "metre": "m", "metres": "m",
    "km": "km", "kilometer": "km", "kilometers": "km", "kilometre": "km", "kilometres": "km",
}

def parse_distance_input(text):
    """Parse text like '150 ft' or '0.5 kilometers' into (value, unit).
    unit is one of 'ft'/'mi'/'m'/'km', or None if missing/unrecognized."""
    if not text or not str(text).strip():
        return None, None
    match = re.match(r'^\s*([\d,]*\.?\d+)\s*([a-zA-Z]*)\s*$', str(text).strip())
    if not match:
        return None, None
    num_str, unit_str = match.groups()
    try:
        value = float(num_str.replace(',', ''))
    except ValueError:
        return None, None
    unit = UNIT_ALIASES.get(unit_str.strip().lower())
    return value, unit

def distance_to_meters(value, unit):
    if unit == "km": return value * 1000
    if unit == "mi": return value * 1609.344
    if unit == "ft": return value * 0.3048
    return value


# --- 4. Main Layout & Execution ---
date_col, michael_col, sarah_col, community_col = st.columns([1, 1, 1, 1])

with date_col:
    date = st.date_input("Date", value=datetime.date.today(), max_value=datetime.date.today())

# Load data at top level so it's available to all columns
df = None
date_rows = pd.DataFrame()
if date:
    stats_mtime = os.path.getmtime("./Data/Timeguessr_Stats.csv") if os.path.exists("./Data/Timeguessr_Stats.csv") else 0
    df = load_data("./Data/Timeguessr_Stats.csv", stats_mtime)
    if df is not None:
        date_rows = df[df["Date"] == date]

# Render Scoreboard & Custom Bar Chart
if not date_rows.empty:
    with date_col:
        # Prepare Data
        m_total_scores = []
        s_total_scores = []
        m_geo_scores = []
        s_geo_scores = []
        m_time_scores = []
        s_time_scores = []
        
        for r in range(1, 6):
            r_data = date_rows[date_rows["Timeguessr Round"] == r]
            mg, mt, sg, s_time = 0, 0, 0, 0
            if len(r_data) > 0:
                row = r_data.iloc[0]
                mg_val = row.get("Michael Geography Score", 0)
                mt_val = row.get("Michael Time Score", 0)
                sg_val = row.get("Sarah Geography Score", 0)
                st_val = row.get("Sarah Time Score", 0)
                
                if pd.notna(mg_val): mg = mg_val
                if pd.notna(mt_val): mt = mt_val
                if pd.notna(sg_val): sg = sg_val
                if pd.notna(st_val): s_time = st_val
            
            m_total_scores.append(mg + mt)
            s_total_scores.append(sg + s_time)
            m_geo_scores.append(mg)
            s_geo_scores.append(sg)
            m_time_scores.append(mt)
            s_time_scores.append(s_time)

        # Generate HTML for Vertical Stacked Bars
        def get_bar_segments(scores, opponent_scores, max_score):
            bar_html = ""
            bright_palette = ["#db5049", "#fd7e14", "#fcc419", "#40c057", "#228be6"]
            pale_palette = ["#eba5a2", "#fecba6", "#ffe7a3", "#a7e0b0", "#9ccbf2"]
            for i, score in enumerate(scores):
                pct = (score / max_score) * 100
                if pct > 0:
                    color = bright_palette[i] if score >= opponent_scores[i] else pale_palette[i]
                    bar_html += f'<div style="height:{pct}%; width:100%; background-color:{color}; box-sizing: border-box;" title="Round {i+1}: {int(score)}"></div>'
            return bar_html

        m_tot_seg = get_bar_segments(m_total_scores, s_total_scores, 50000)
        s_tot_seg = get_bar_segments(s_total_scores, m_total_scores, 50000)
        m_geo_seg = get_bar_segments(m_geo_scores, s_geo_scores, 25000)
        s_geo_seg = get_bar_segments(s_geo_scores, m_geo_scores, 25000)
        m_time_seg = get_bar_segments(m_time_scores, s_time_scores, 25000)
        s_time_seg = get_bar_segments(s_time_scores, m_time_scores, 25000)

        bars_html = f"""
        <style>
            .vs-container {{
                display: flex;
                justify-content: space-between;
                gap: 20px;
                height: 315px;
                align-items: flex-end;
                margin-top: 15px;
                width: 100%;
            }}
            .group-wrapper {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 5px;
                height: 100%;
                justify-content: flex-end;
                flex: 1;
                min-width: 0;
            }}
            .bars-row {{
                display: flex;
                gap: 5px;
                height: 100%;
                align-items: flex-end;
                justify-content: center;
                width: 100%;
            }}
            .bar-col {{
                display: flex;
                flex-direction: column;
                align-items: center;
                height: 100%;
                justify-content: flex-end;
                flex: 1;
                width: 100%;
            }}
            .bar-track {{
                width: 100%;
                height: 100%;
                background-color: #b0afaa;
                border-radius: 6px;
                overflow: hidden;
                display: flex;
                flex-direction: column-reverse;
                justify-content: flex-start;
            }}
            .group-title {{
                font-weight: 700;
                font-size: 0.9rem;
                margin-bottom: 5px;
                color: #555;
                white-space: nowrap;
            }}
            .bar-lbl {{
                font-weight: 700;
                font-size: 0.8rem;
                margin-top: 2px;
            }}
        </style>
        <div class="vs-container">
            <div class="group-wrapper"><div class="bars-row">
            <div class="bar-col"><div class="bar-track">{m_tot_seg}</div><div class="bar-lbl" style="color: #221e8f;">M</div></div>
            <div class="bar-col"><div class="bar-track">{s_tot_seg}</div><div class="bar-lbl" style="color: #8a005c;">S</div></div>
            </div><div class="group-title">Total</div></div>
            <div class="group-wrapper"><div class="bars-row">
            <div class="bar-col"><div class="bar-track">{m_geo_seg}</div><div class="bar-lbl" style="color: #221e8f;">M</div></div>
            <div class="bar-col"><div class="bar-track">{s_geo_seg}</div><div class="bar-lbl" style="color: #8a005c;">S</div></div>
            </div><div class="group-title">Geo</div></div>
            <div class="group-wrapper"><div class="bars-row">
            <div class="bar-col"><div class="bar-track">{m_time_seg}</div><div class="bar-lbl" style="color: #221e8f;">M</div></div>
            <div class="bar-col"><div class="bar-track">{s_time_seg}</div><div class="bar-lbl" style="color: #8a005c;">S</div></div>
            </div><div class="group-title">Time</div></div>
        </div>
        """
        st.markdown(bars_html, unsafe_allow_html=True)

    row_0 = date_rows.iloc[0]
    m_total = row_0.get("Michael Total Score", 0)
    s_total = row_0.get("Sarah Total Score", 0)
    m_val = 0 if pd.isna(m_total) else m_total
    s_val = 0 if pd.isna(s_total) else s_total
    players = ["Michael", "Sarah"]

    p1_html = generate_player_html(players[0], date_rows, players, highlight=(m_val > s_val))
    p2_html = generate_player_html(players[1], date_rows, players, highlight=(s_val > m_val))

    component_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
    body { margin: 0; padding: 0; font-family: 'Poppins', sans-serif; }
    .tg-container { position: relative; padding: 10px 12px; box-sizing: border-box; width: 100%; border-radius: 12px; margin-bottom: 0; }
    .tg-header { font-weight:700; font-size:30px; margin:0 0 5px 0; line-height:1.1; }
    .tg-total { color:#222; font-size:24px; font-weight:600; margin:0 0 7px 0; line-height:1.1; }
    .tg-sub { font-size:20px; margin:0 0 7px 0; line-height:1.1; color:#333; }
    .tg-rounds-wrapper { margin-top:7px; }
    .tg-round { margin:7px 0; }
    .tg-row { display:flex; gap:12px; align-items:center; flex-wrap:nowrap; }
    .tg-half { width: 50%; flex: 1; }
    .tg-bar-bg { background:#b0afaa; border-radius:10px; height:10px; overflow:hidden; width: 100%; position: relative; }
    .tg-bar-fill { height:10px; border-radius:10px; background:#db5049; }
    .tg-score-note { font-size:18px; margin:0 0 7px 0; white-space: nowrap; }
    .tg-score-note small { color:#444; }
    </style>
    """

    with michael_col:
        components_html(f'{component_css}{p1_html}', height=450, scrolling=True)

    with sarah_col:
        components_html(f'{component_css}{p2_html}', height=450, scrolling=True)

    with community_col:
        community_html = generate_community_html(date_rows)
        components_html(f'{component_css}{community_html}', height=450, scrolling=True)

elif df is None:
    with date_col:
        st.error("Data file not found.")
else:
    with date_col:
        st.info("No data found for this date.")

# --- 5. Row-Based Input Section ---
if date:
    # Calculate Day
    reference_date = datetime.date(2025, 10, 28)
    timeguessr_day = 880 + (date - reference_date).days
    
    if "last_viewed_timeguessr_day" not in st.session_state:
        st.session_state["last_viewed_timeguessr_day"] = timeguessr_day
    st.session_state["last_viewed_timeguessr_day"] = timeguessr_day

    row_for_stats = date_rows.iloc[0] if not date_rows.empty else None
    has_community = row_for_stats is not None and pd.notna(row_for_stats.get("Community Average"))
    is_community_edit = st.session_state.get(f"edit_community_{date}", False)
    if has_community and not is_community_edit:
        for r_idx in range(1, 6):
            for k in [f"cs_{r_idx}_{date}", f"ct_{r_idx}_{date}", f"cd_{r_idx}_{date}", f"cu_{r_idx}_{date}"]:
                if k in st.session_state: del st.session_state[k]
        for k in [f"cavg_{date}", f"cyrs_{date}", f"cloc_{date}"]:
            if k in st.session_state: del st.session_state[k]

    st.divider()

    # --- Pre-load Actuals Data ---
    act_path = "./Data/Timeguessr_Actuals_Parsed.csv"
    act_df = pd.DataFrame()
    if os.path.exists(act_path): act_df = pd.read_csv(act_path)

    map_mtime = os.path.getmtime("./Data/Custom_World_Map_New.json") if os.path.exists("./Data/Custom_World_Map_New.json") else 0
    map_subdivs = load_map_subdivisions(map_mtime)
    
    curr_act = act_df[(act_df['Timeguessr Day'] == timeguessr_day)] if not act_df.empty else pd.DataFrame()
    act_exists = not curr_act.empty
    
    is_act_edit = st.session_state.get(f"edit_act_{date}", False)
    if act_exists and not is_act_edit:
        for r_idx in range(1, 6):
            for k in [f"ay_{r_idx}_{date}", f"ac_{r_idx}_{date}", f"as_{r_idx}_{date}", f"acs_{r_idx}_{date}", f"aci_{r_idx}_{date}", f"acity_{r_idx}_{date}"]:
                if k in st.session_state: del st.session_state[k]
    
    m_path = "./Data/Timeguessr_Michael_Parsed.csv"
    s_path = "./Data/Timeguessr_Sarah_Parsed.csv"
    m_has = not pd.read_csv(m_path)[pd.read_csv(m_path)['Timeguessr Day'] == timeguessr_day].empty if os.path.exists(m_path) else False
    s_has = not pd.read_csv(s_path)[pd.read_csv(s_path)['Timeguessr Day'] == timeguessr_day].empty if os.path.exists(s_path) else False
    
    act_hidden = date == datetime.date.today() and act_exists and not (m_has and s_has)

    # --- Pre-load Player State Data ---
    p_state = {}
    for p_name, opp_name in [("Michael", "Sarah"), ("Sarah", "Michael")]:
        csv_p = f"./Data/Timeguessr_{p_name}_Parsed.csv"
        csv_o = f"./Data/Timeguessr_{opp_name}_Parsed.csv"
        
        df_p = pd.read_csv(csv_p) if os.path.exists(csv_p) else pd.DataFrame()
        df_o = pd.read_csv(csv_o) if os.path.exists(csv_o) else pd.DataFrame()
        
        curr_p = df_p[df_p['Timeguessr Day'] == timeguessr_day] if not df_p.empty else pd.DataFrame()
        curr_o = df_o[df_o['Timeguessr Day'] == timeguessr_day] if not df_o.empty else pd.DataFrame()
        
        has_g = not curr_p.empty
        opp_has_g = not curr_o.empty
        
        is_hid = date == datetime.date.today() and has_g and not opp_has_g

        is_p_edit = st.session_state.get(f"edit_{p_name}_{date}", False)
        if has_g and not is_p_edit:
            for r_idx in range(1, 6):
                for k in [f"d_{p_name}_{r_idx}_{date}", f"y_{p_name}_{r_idx}_{date}"]:
                    if k in st.session_state: del st.session_state[k]
            for suffix in ("masked", "real"):
                for k in [f"ts_{p_name}_{date}_{suffix}", f"pct_{p_name}_{date}_{suffix}", f"yrs_{p_name}_{date}_{suffix}", f"loc_{p_name}_{date}_{suffix}"]:
                    if k in st.session_state: del st.session_state[k]

        def_total = ""
        if has_g:
            ts = curr_p.iloc[0].get(f'{p_name} Total Score')
            def_total = "" if pd.isna(ts) else f"{ts:g}"

        p_state[p_name] = {
            'df': df_p, 'curr': curr_p, 'has_g': has_g, 'is_hid': is_hid,
            'def_total': def_total, 'csv': csv_p,
            'input': {}, 'comp_tot': 0, 'edit': False,
        }

    # --- HEADERS ROW ---
    h1, h2, h3, h4 = st.columns([1, 1, 1, 1])

    edit_act = False
    with h1:
        ah1, ah2 = st.columns([2, 1])
        with ah1: st.subheader("Actual Answers")
        with ah2:
            edit_act = True
            if act_exists:
                st.markdown('<div style="margin-top: 8px;"></div>', unsafe_allow_html=True)
                edit_act = st.toggle("Edit", key=f"edit_act_{date}")
                if act_hidden and not edit_act:
                    st.caption("🔒 Hidden until both play")

    for col, p_name in [(h2, "Michael"), (h3, "Sarah")]:
        with col:
            st_state = p_state[p_name]
            ph1, ph2 = st.columns([2, 1])
            with ph1: st.subheader(f"{p_name}'s Guesses")
            with ph2:
                if st_state['has_g']:
                    st.markdown('<div style="margin-top: 8px;"></div>', unsafe_allow_html=True)
                    st_state['edit'] = st.toggle("Edit", value=False, key=f"edit_{p_name}_{date}")
            if st_state['is_hid'] and not st_state['edit']:
                st.caption("🔒 Hidden until opponent submits")

    edit_community = False
    with h4:
        if has_community:
            chh1, chh2 = st.columns([2, 1])
            with chh1: st.subheader("Community Averages")
            with chh2:
                st.markdown('<div style="margin-top: 8px;"></div>', unsafe_allow_html=True)
                edit_community = st.toggle("Edit", key=f"edit_community_{date}")
        else:
            st.subheader("Community Averages")
            edit_community = True

    # --- ROUNDS ROW-BY-ROW LOOP ---
    actual_rounds_data = {}
    all_valid_act = True
    save_rows_act = []
    community_round_input = {}
    community_fields_disabled = has_community and not edit_community

    for r in range(1, 6):
        st.markdown("---")
        rc1, rc2, rc3, rc4 = st.columns([1, 1, 1, 1])

        # ACTUALS ROUND
        with rc1:
            st.markdown(f"**Round {r}**")
            row = curr_act[curr_act['Timeguessr Round'] == r].iloc[0] if act_exists and len(curr_act[curr_act['Timeguessr Round'] == r]) > 0 else {}

            y_val = str(int(row['Year'])) if 'Year' in row and pd.notna(row['Year']) else ""
            c_def_raw = row.get('Country', '')
            s_def = row.get('Subdivision', '')
            c_val = row.get('City', '')

            if act_exists and not edit_act:
                if act_hidden:
                    st.markdown("""
<div style="background:linear-gradient(135deg,#fff5f5,#ffe8e8); border-radius:10px; padding:12px 14px; border-left:4px solid #db5049; box-shadow:0 2px 6px rgba(219,80,73,0.12); margin-top:2px;">
    <div style="font-weight:700; color:#db5049; font-size:1.05em; margin-bottom:6px;">?</div>
    <div style="display:flex; align-items:center; gap:7px; margin-bottom:4px;">
        <span style="font-size:1.1em; line-height:1;">❓</span>
        <span style="color:#444; font-size:0.88em;">?</span>
    </div>
    <div style="color:#555; font-size:0.85em;">📅 ?</div>
</div>
                    """, unsafe_allow_html=True)
                else:
                    flag_html = get_flag_emoji(c_def_raw) if c_def_raw else get_flag_emoji("United Nations")
                    sub_country = c_def_raw or "—"
                    if pd.notna(s_def) and str(s_def).strip(): sub_country = f"{s_def}, {sub_country}"

                    st.markdown(f"""
<div style="background:linear-gradient(135deg,#fff5f5,#ffe8e8); border-radius:10px; padding:12px 14px; border-left:4px solid #db5049; box-shadow:0 2px 6px rgba(219,80,73,0.12); margin-top:2px;">
    <div style="font-weight:700; color:#db5049; font-size:1.05em; margin-bottom:6px;">{c_val or "—"}</div>
    <div style="display:flex; align-items:center; gap:7px; margin-bottom:4px;">
        <span style="font-size:1.1em; line-height:1;">{flag_html}</span>
        <span style="color:#444; font-size:0.88em;">{sub_country}</span>
    </div>
    <div style="color:#555; font-size:0.85em;">📅 {y_val or "—"}</div>
</div>
                    """, unsafe_allow_html=True)

                valid_y = y_val.isdigit() and len(y_val)==4 and 1900<=int(y_val)<=date.year
                actual_rounds_data[r] = {'year': y_val if valid_y else None, 'year_valid': valid_y}
            else:
                r_top = st.columns(2)
                r_bot = st.columns(2)

                y = r_top[0].text_input("Year", value=y_val, key=f"ay_{r}_{date}", disabled=not edit_act)
                cit = r_top[1].text_input("City", value=c_val, key=f"acity_{r}_{date}", disabled=not edit_act)

                # Build country list from config; float countries matching typed city to top
                all_countries = list(config.get('countries', {}).keys())
                typed_city_for_country = (cit or "").strip().lower()
                matching_countries = []
                if typed_city_for_country and not act_df.empty and 'City' in act_df.columns and 'Country' in act_df.columns:
                    hit_countries = act_df[
                        act_df['City'].str.lower() == typed_city_for_country
                    ]['Country'].dropna().unique().tolist()
                    matching_countries = [c for c in all_countries if c in hit_countries]

                other_countries = [c for c in all_countries if c not in matching_countries]
                opts = [""] + matching_countries + other_countries
                matching_country_set = set(matching_countries)

                c_def = c_def_raw if c_def_raw in opts else opts[0]
                c_idx = opts.index(c_def) if c_def in opts else 0
                cou = r_bot[0].selectbox(
                    "Country", opts, index=c_idx,
                    format_func=lambda c, ms=matching_country_set: ("★ " + c if c in ms else c),
                    key=f"ac_{r}_{date}", disabled=not edit_act
                )

                # Build subdivision list from map data; float subs matching typed city to top
                iso3 = country_to_iso3(cou) if cou else None
                subs_raw = map_subdivs.get(iso3, []) if iso3 else []

                typed_city = (cit or "").strip().lower()
                matching_subs = []
                if subs_raw and typed_city and not act_df.empty and 'City' in act_df.columns and 'Subdivision' in act_df.columns:
                    hit_subs = act_df[
                        (act_df['Country'] == cou) &
                        (act_df['City'].str.lower() == typed_city)
                    ]['Subdivision'].dropna().unique().tolist()
                    matching_subs = [s for s in subs_raw if s in hit_subs]

                if subs_raw:
                    other_subs = [s for s in subs_raw if s not in matching_subs]
                    subs_ordered = [""] + matching_subs + other_subs
                    matching_set = set(matching_subs)

                    if s_def in subs_ordered: s_idx = subs_ordered.index(s_def)
                    else: s_idx = 0

                    sub = r_bot[1].selectbox(
                        "Sub", subs_ordered, index=s_idx,
                        format_func=lambda s, ms=matching_set: ("★ " + s if s in ms else s),
                        key=f"as_{r}_{date}", disabled=not edit_act
                    )
                else:
                    sub = ""

                valid_y = y.isdigit() and len(y)==4 and 1900<=int(y)<=date.year
                actual_rounds_data[r] = {'year': y if valid_y else None, 'year_valid': valid_y}

                if edit_act:
                    if not (y and cou and cit and valid_y): all_valid_act = False
                    save_rows_act.append({
                        "Timeguessr Day": timeguessr_day,
                        "Timeguessr Round": r,
                        "City": cit,
                        "Subdivision": sub,
                        "Country": cou,
                        "Year": int(y) if valid_y else 0
                    })

        # PLAYER ROUNDS
        for col, p_name in [(rc2, "Michael"), (rc3, "Sarah")]:
            with col:
                st_state = p_state[p_name]
                d_dist, d_year = "", ""

                if st_state['has_g']:
                    r_row = st_state['curr'][st_state['curr']['Timeguessr Round'] == r]
                    if not r_row.empty:
                        rw = r_row.iloc[0]
                        dist_raw = rw.get(f'{p_name} Geography Distance')
                        if pd.notna(dist_raw):
                            d_dist = f"{float(dist_raw)/0.3048:.0f} ft"
                        time_raw = rw.get(f'{p_name} Time Guessed')
                        if pd.notna(time_raw): d_year = str(int(time_raw))

                d_key = f"d_{p_name}_{r}_{date}"
                y_key = f"y_{p_name}_{r}_{date}"

                st.markdown(f"**Round {r}**")

                # Pre-calculate scores from session state before rendering widgets
                g_score_disp = None
                d_meters_calc = 0
                current_dist_val = st.session_state.get(d_key, d_dist)
                current_dist_num, current_unit = parse_distance_input(current_dist_val)
                has_dist_val = current_dist_num is not None
                dist_unit_missing = has_dist_val and current_unit is None
                if has_dist_val and current_unit is not None:
                    if current_dist_num >= 0:
                        d_meters_calc = distance_to_meters(current_dist_num, current_unit)
                        g_score_disp = geography_score(d_meters_calc)
                        st_state['comp_tot'] += g_score_disp

                t_score_disp = None
                year_int = None
                y_valid = False
                act_y = None
                current_year_val = st.session_state.get(y_key, d_year)
                has_year_val = bool(current_year_val and str(current_year_val).strip())
                if has_year_val:
                    if current_year_val.isdigit() and len(current_year_val) == 4:
                        y_val = int(current_year_val)
                        if 1900 <= y_val <= date.year:
                            y_valid = True
                            year_int = y_val
                            if r in actual_rounds_data and actual_rounds_data.get(r, {}).get('year_valid'):
                                act_y = int(actual_rounds_data[r]['year'])
                            if act_y:
                                t_score_disp = calculate_time_score(y_val, act_y)
                                st_state['comp_tot'] += t_score_disp

                submitted = st_state['has_g'] and not st_state['edit']
                p_color = "#221e8f" if p_name == "Michael" else "#8a005c"
                p_bg = "#dde5eb" if p_name == "Michael" else "#edd3df"

                if submitted:
                    year_val_in = d_year
                    dist_val = d_dist

                    if st_state['is_hid']:
                        st.markdown(f'''<div style="background:{p_bg}; border-radius:10px; padding:10px 14px; border-left:4px solid {p_color}; box-shadow:0 2px 6px rgba(0,0,0,0.1); margin-top:2px;">
    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
        <span style="color:#444; font-size:0.9em;">📅 ?</span>
        <span style="color:{p_color}; background-color:{p_bg}; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px;">?</span>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px;">
        <span style="color:#444; font-size:0.9em;">🌎 ?</span>
        <span style="color:{p_color}; background-color:{p_bg}; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px;">?</span>
    </div>
</div>''', unsafe_allow_html=True)
                    else:
                        time_txt = f"{t_score_disp:.0f}" if t_score_disp is not None else ("?" if y_valid else "—")
                        geo_txt = f"{g_score_disp:.0f}" if g_score_disp is not None else "—"

                        st.markdown(f'''<div style="background:{p_bg}; border-radius:10px; padding:10px 14px; border-left:4px solid {p_color}; box-shadow:0 2px 6px rgba(0,0,0,0.1); margin-top:2px;">
    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
        <span style="color:#444; font-size:0.9em;">📅 {d_year or "—"}</span>
        <span style="color:{p_color}; background-color:{p_bg}; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{time_txt}</span>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px;">
        <span style="color:#444; font-size:0.9em;">🌎 {d_dist or "—"}</span>
        <span style="color:{p_color}; background-color:{p_bg}; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{geo_txt}</span>
    </div>
</div>''', unsafe_allow_html=True)
                else:
                    year_val_in = st.text_input("Year", value=d_year, key=y_key)
                    if has_year_val:
                        c_color = "#221e8f" if p_name == "Michael" else "#8a005c"
                        c_bg = "#dde5eb" if p_name == "Michael" else "#edd3df"
                        if t_score_disp is not None:
                            st.markdown(f'<div style="margin-top: 0px;"><label style="margin-bottom: 6px; display: block;"><p style="font-size: 14px; margin: 0; padding: 0;">Time Score</p></label><div class="score-box" style="background-color:{c_bg}; color:{c_color}; border-left:5px solid {c_color};">📅 {t_score_disp:.0f}</div></div>', unsafe_allow_html=True)
                        elif y_valid:
                            st.markdown(f'<div style="margin-top: 0px;"><label style="margin-bottom: 6px; display: block;"><p style="font-size: 14px; margin: 0; padding: 0;">Time Score</p></label><div class="score-box" style="background-color:#bcb0ff; color:#221e8f; border-left:5px solid #221e8f;" title="Submit actuals to see score">📅 ?</div></div>', unsafe_allow_html=True)

                    dist_val = st.text_input("Distance", value=d_dist, key=d_key)
                    if dist_unit_missing:
                        st.caption("⚠️ Include a unit: ft, mi, m, or km")
                    if has_dist_val and g_score_disp is not None:
                        c_color = "#221e8f" if p_name == "Michael" else "#8a005c"
                        c_bg = "#dde5eb" if p_name == "Michael" else "#edd3df"
                        st.markdown(f'<div style="margin-top: 0px;"><label style="margin-bottom: 6px; display: block;"><p style="font-size: 14px; margin: 0; padding: 0;">Geo Score</p></label><div class="score-box" style="background-color:{c_bg}; color:{c_color}; border-left:5px solid {c_color};">🌎 {g_score_disp:.0f}</div></div>', unsafe_allow_html=True)

                st_state['input'][r] = {
                    'dist_raw': dist_val, 'dist_value': current_dist_num, 'unit': current_unit,
                    'dist_m': d_meters_calc,
                    'year': year_val_in, 'year_int': year_int, 'y_valid': y_valid,
                    'g_score': g_score_disp
                }

        # COMMUNITY ROUND
        with rc4:
            st.markdown(f"**Round {r}**")
            row_r_df = date_rows[date_rows["Timeguessr Round"] == r]
            row_r = row_r_df.iloc[0] if not row_r_df.empty else None

            def_c_score = "" if row_r is None or pd.isna(row_r.get("Community Round Score")) else f"{row_r.get('Community Round Score'):g}"
            def_c_time = "" if row_r is None or pd.isna(row_r.get("Community Time Distance")) else f"{row_r.get('Community Time Distance'):g}"

            c_unit_key = f"cu_{r}_{date}"
            last_c_unit = st.session_state.get(c_unit_key, "mi")
            if last_c_unit not in ["ft", "mi", "m", "km"]:
                last_c_unit = "mi"
            def_c_dist = ""
            if row_r is not None and pd.notna(row_r.get("Community Geography Distance")):
                cval = float(row_r.get("Community Geography Distance"))
                if last_c_unit == "km":  def_c_dist = f"{cval/1000:.3f} km"
                elif last_c_unit == "mi": def_c_dist = f"{cval/1609.344:.3f} mi"
                elif last_c_unit == "ft": def_c_dist = f"{cval/0.3048:.0f} ft"
                else:                     def_c_dist = f"{cval:.0f} m"

            if community_fields_disabled:
                c_score_in, c_time_in, c_dist_in = def_c_score, def_c_time, def_c_dist

                # Estimated scores derived from the average years-off/distance, purely for
                # display — NOT the true community average (that would require averaging
                # individual scores, not scoring the averaged inputs), so shown in quotes
                # and never saved anywhere.
                time_est_txt = "—"
                if def_c_time:
                    try:
                        time_est = calculate_time_score(float(def_c_time), 0)
                        if time_est is not None:
                            time_est_txt = f'"{time_est:,.0f}"'
                    except ValueError:
                        pass

                geo_est_txt = "—"
                dist_val_parsed, dist_unit_parsed = parse_distance_input(def_c_dist)
                if dist_val_parsed is not None and dist_unit_parsed is not None:
                    geo_est_txt = f'"{geography_score(distance_to_meters(dist_val_parsed, dist_unit_parsed)):,.0f}"'

                st.markdown(f'''<div style="background:#eef0f2; border-radius:10px; padding:10px 14px; border-left:4px solid #6c757d; box-shadow:0 2px 6px rgba(0,0,0,0.08); margin-top:2px;">
    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
        <span style="color:#444; font-size:0.9em;">🏆 Score</span>
        <span style="color:#495057; background-color:#e9ecef; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{def_c_score or "—"}</span>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px;">
        <span style="color:#444; font-size:0.9em;">📅 {def_c_time or "—"}</span>
        <span style="color:#495057; background-color:#e9ecef; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{time_est_txt}</span>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px;">
        <span style="color:#444; font-size:0.9em;">🌎 {def_c_dist or "—"}</span>
        <span style="color:#495057; background-color:#e9ecef; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{geo_est_txt}</span>
    </div>
</div>''', unsafe_allow_html=True)
            else:
                c_score_in = st.text_input("Score", value=def_c_score, key=f"cs_{r}_{date}")
                ctd1, ctd2 = st.columns(2)
                c_time_in = ctd1.text_input("Time", value=def_c_time, key=f"ct_{r}_{date}")
                c_dist_in = ctd2.text_input("Distance", value=def_c_dist, key=f"cd_{r}_{date}")
                _, c_dist_unit = parse_distance_input(c_dist_in)
                if c_dist_in.strip() and c_dist_unit is None:
                    st.caption("⚠️ Include a unit: ft, mi, m, or km")
                if c_dist_unit is not None:
                    st.session_state[c_unit_key] = c_dist_unit

            community_round_input[r] = {'score': c_score_in, 'time': c_time_in, 'dist': c_dist_in}

    # --- FOOTER ROW ---
    st.markdown("---")
    fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 1])

    with fc1:
        if edit_act:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Submit Actuals", key=f"sub_act_{date}", use_container_width=True):
                if all_valid_act:
                    f_df = act_df[act_df['Timeguessr Day'] != timeguessr_day]
                    f_df = pd.concat([f_df, pd.DataFrame(save_rows_act)], ignore_index=True)
                    f_df.sort_values(['Timeguessr Day', 'Timeguessr Round']).to_csv(act_path, index=False)

                    rounds_for_txt = {row["Timeguessr Round"]: row for row in save_rows_act}
                    update_actuals_txt_entry(timeguessr_day, {
                        r: {'city': v['City'], 'subdivision': v['Subdivision'], 'country': v['Country'], 'year': v['Year']}
                        for r, v in rounds_for_txt.items()
                    })

                    st.success("Saved!"); st.rerun()
                else: st.error("Invalid actuals")
                
    for col, p_name in [(fc2, "Michael"), (fc3, "Sarah")]:
        with col:
            st_state = p_state[p_name]
            masked_footer = st_state['is_hid'] and not st_state['edit']
            with st.container():
                ct1, ct2 = st.columns([1, 1])
                with ct1: st.markdown(f"**Computed Total**")
                with ct2:
                    c_color = "#221e8f" if p_name == "Michael" else "#8a005c"
                    c_bg = "#dde5eb" if p_name == "Michael" else "#edd3df"
                    total_display = "?" if masked_footer else f'{int(st_state["comp_tot"]):,}'
                    st.markdown(f'<div class="score-box" style="background-color:{c_bg}; color:{c_color}; border-left:5px solid {c_color};">{total_display}</div>', unsafe_allow_html=True)

                key_suffix = "masked" if masked_footer else "real"
                pct_key = f"pct_{p_name}_{date}_{key_suffix}"
                yrs_key = f"yrs_{p_name}_{date}_{key_suffix}"
                loc_key = f"loc_{p_name}_{date}_{key_suffix}"
                ts_key = f"ts_{p_name}_{date}_{key_suffix}"
                fields_disabled = st_state['has_g'] and not st_state['edit']

                def _stat_default(col, mult=1):
                    if row_for_stats is None: return ""
                    v = row_for_stats.get(col)
                    return "" if pd.isna(v) else f"{v * mult:g}"

                if masked_footer or fields_disabled:
                    tt1, tt2 = st.columns([1, 1])
                    with tt1: st.markdown(f"**Total Score**")
                    with tt2:
                        ts_display = "?" if masked_footer else (st_state['def_total'] or "—")
                        st.markdown(f'<div class="score-box" style="background-color:{c_bg}; color:{c_color}; border-left:5px solid {c_color};">{ts_display}</div>', unsafe_allow_html=True)
                    total_input = st_state['def_total']
                else:
                    total_input = st.text_input("Total Score", value=st_state['def_total'], key=ts_key)

                if masked_footer or fields_disabled:
                    pct_val = "?" if masked_footer else (_stat_default(f"{p_name} Percentile", 100) or "—")
                    yrs_val = "?" if masked_footer else (_stat_default(f"{p_name} Years") or "—")
                    loc_val = "?" if masked_footer else (_stat_default(f"{p_name} Location") or "—")
                    st.markdown(f'''<div style="background:{c_bg}; border-radius:10px; padding:10px 14px; border-left:4px solid {c_color}; box-shadow:0 2px 6px rgba(0,0,0,0.1); margin-top:2px;">
    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
        <span style="color:#444; font-size:0.9em;">Percentile</span>
        <span style="color:{c_color}; background-color:{c_bg}; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{pct_val}</span>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px;">
        <span style="color:#444; font-size:0.9em;">Years</span>
        <span style="color:{c_color}; background-color:{c_bg}; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{yrs_val}</span>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px;">
        <span style="color:#444; font-size:0.9em;">Location</span>
        <span style="color:{c_color}; background-color:{c_bg}; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{loc_val}</span>
    </div>
</div>''', unsafe_allow_html=True)
                    pct_in = "" if masked_footer else _stat_default(f"{p_name} Percentile", 100)
                    yrs_in = "" if masked_footer else _stat_default(f"{p_name} Years")
                    loc_in = "" if masked_footer else _stat_default(f"{p_name} Location")
                else:
                    pc1, pc2, pc3 = st.columns(3)
                    pct_in = pc1.text_input("Percentile", value=_stat_default(f"{p_name} Percentile", 100), key=pct_key)
                    yrs_in = pc2.text_input("Years", value=_stat_default(f"{p_name} Years"), key=yrs_key)
                    loc_in = pc3.text_input("Location", value=_stat_default(f"{p_name} Location"), key=loc_key)

                if not st_state['has_g'] or (st_state['has_g'] and st_state['edit']):
                    if st.button(f"Submit {p_name}'s Guesses", key=f"sub_{p_name}_{date}", use_container_width=True):

                        def process_submission():
                            def _to_float(s):
                                s = (s or "").strip()
                                if not s: return None
                                try: return float(s)
                                except ValueError: return None

                            total_val = _to_float(total_input)
                            if total_val is None:
                                st.error("Missing Total Score"); return
                            ts_val = int(round(total_val))

                            if abs(ts_val - st_state['comp_tot']) > 10:
                                st.error(f"Computed total ({int(st_state['comp_tot']):,}) differs from Total Score ({ts_val:,}) by more than 10 points.")
                                return

                            new_rows = []
                            rounds_for_txt = {}
                            for r in range(1, 6):
                                d = st_state['input'][r]
                                if not d['dist_raw'] or not d['year']:
                                    st.error(f"Round {r} incomplete"); return
                                if not d['y_valid']:
                                    st.error(f"Round {r} invalid year"); return
                                if d['dist_value'] is None or d['unit'] is None:
                                    st.error(f"Round {r}: Enter a distance with a unit (ft, mi, m, or km)"); return
                                if d['dist_value'] < 0:
                                    st.error(f"Round {r} negative distance"); return

                                act_y = actual_rounds_data.get(r, {}).get('year')

                                t_dist = np.nan
                                t_score = np.nan
                                r_score = np.nan

                                if act_y:
                                    t_dist = abs(d['year_int'] - int(act_y))
                                    t_score = calculate_time_score(d['year_int'], int(act_y))

                                if pd.notna(t_score) and pd.notna(d['g_score']):
                                    r_score = t_score + d['g_score']

                                rounds_for_txt[r] = {
                                    'year': d['year_int'], 'dist_value': d['dist_value'], 'unit': d['unit'],
                                }

                                new_rows.append({
                                    "Timeguessr Day": int(timeguessr_day),
                                    "Timeguessr Round": int(r),
                                    f"{p_name} Total Score": ts_val,
                                    f"{p_name} Round Score": r_score,
                                    f"{p_name} Geography Distance": int(d['dist_m']),
                                    f"{p_name} Time Guessed": int(d['year_int']),
                                    f"{p_name} Time Distance": t_dist,
                                    f"{p_name} Geography Score": d['g_score'],
                                    f"{p_name} Geography Score (Min)": d['g_score'],
                                    f"{p_name} Geography Score (Max)": d['g_score'],
                                    f"{p_name} Time Score": t_score,
                                    f"{p_name} Time Score (Min)": t_score,
                                    f"{p_name} Time Score (Max)": t_score,
                                })

                            try:
                                df_out = st_state['df'][st_state['df']['Timeguessr Day'] != timeguessr_day]
                                df_out = pd.concat([df_out, pd.DataFrame(new_rows)], ignore_index=True)
                                df_out.sort_values(['Timeguessr Day', 'Timeguessr Round']).to_csv(st_state['csv'], index=False)

                                update_averages_entry(
                                    timeguessr_day, p_name,
                                    percentile=_to_float(pct_in),
                                    years=_to_float(yrs_in),
                                    location=_to_float(loc_in),
                                )
                                update_player_txt_entry(p_name, timeguessr_day, ts_val, rounds_for_txt)

                                st.success("Saved!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Save failed: {e}")

                        process_submission()

    with fc4:
        def _to_float_c(s):
            s = (s or "").strip()
            if not s: return None
            try: return float(s)
            except ValueError: return None

        community_comp_tot = sum(
            v for v in (_to_float_c(community_round_input.get(r, {}).get('score')) for r in range(1, 6))
            if v is not None
        )

        cct1, cct2 = st.columns([1, 1])
        with cct1: st.markdown(f"**Computed Total**")
        with cct2:
            st.markdown(f'<div class="score-box" style="background-color:#e9ecef; color:#495057; border-left:5px solid #6c757d;">{int(community_comp_tot):,}</div>', unsafe_allow_html=True)

        def_c_avg = "" if row_for_stats is None or pd.isna(row_for_stats.get("Community Average")) else f"{row_for_stats.get('Community Average'):g}"
        def_c_yrs = "" if row_for_stats is None or pd.isna(row_for_stats.get("Community Years Average")) else f"{row_for_stats.get('Community Years Average'):g}"
        def_c_loc = "" if row_for_stats is None or pd.isna(row_for_stats.get("Community Location Average")) else f"{row_for_stats.get('Community Location Average'):g}"

        if community_fields_disabled:
            cat1, cat2 = st.columns([1, 1])
            with cat1: st.markdown(f"**Average Score**")
            with cat2:
                st.markdown(f'<div class="score-box" style="background-color:#e9ecef; color:#495057; border-left:5px solid #6c757d;">{def_c_avg or "—"}</div>', unsafe_allow_html=True)

            st.markdown(f'''<div style="background:#eef0f2; border-radius:10px; padding:10px 14px; border-left:4px solid #6c757d; box-shadow:0 2px 6px rgba(0,0,0,0.08); margin-top:2px;">
    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
        <span style="color:#444; font-size:0.9em;">Years Avg</span>
        <span style="color:#495057; background-color:#e9ecef; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{def_c_yrs or "—"}</span>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px;">
        <span style="color:#444; font-size:0.9em;">Location Avg</span>
        <span style="color:#495057; background-color:#e9ecef; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{def_c_loc or "—"}</span>
    </div>
</div>''', unsafe_allow_html=True)
            c_avg_in, c_yrs_in, c_loc_in = def_c_avg, def_c_yrs, def_c_loc
        else:
            c_avg_in = st.text_input("Average Score", value=def_c_avg, key=f"cavg_{date}")
            cf1, cf2 = st.columns(2)
            c_yrs_in = cf1.text_input("Years Average", value=def_c_yrs, key=f"cyrs_{date}")
            c_loc_in = cf2.text_input("Location Average", value=def_c_loc, key=f"cloc_{date}")

        if edit_community:
            if st.button("Save Community Stats", key=f"sub_community_{date}", use_container_width=True):
                rounds_payload = {}
                for r in range(1, 6):
                    ci = community_round_input.get(r, {})
                    _, dunit = parse_distance_input(ci.get('dist', ''))
                    geo_text = ci.get('dist', '').strip() if dunit is not None else None
                    rounds_payload[r] = {
                        'score': _to_float_c(ci.get('score')),
                        'time': _to_float_c(ci.get('time')),
                        'geo_text': geo_text,
                    }

                avg_val = _to_float_c(c_avg_in)
                round_scores = [rounds_payload[r]['score'] for r in range(1, 6)]
                round_sum = sum(s for s in round_scores if s is not None)

                if avg_val is not None and all(s is not None for s in round_scores) and abs(round_sum - avg_val) > 10:
                    st.error(f"Sum of round scores ({round_sum:,.0f}) differs from Average ({avg_val:,.0f}) by more than 10 points.")
                else:
                    update_community_averages_entry(
                        timeguessr_day,
                        average=avg_val,
                        years_average=_to_float_c(c_yrs_in),
                        location_average=_to_float_c(c_loc_in),
                        rounds=rounds_payload,
                    )
                    st.success("Saved!")
                    st.rerun()