import streamlit as st
import base64
from PIL import Image

def get_base64_image(image_path):
    """
    Encodes an image to a Base64 string, using its detected format (e.g., PNG or JPEG) 
    when saving to the in-memory buffer.

    Args:
        image_path (str): Path to the image file (e.g., "Images/Sarah.jpg").

    Returns:
        str or None: The Base64 encoded string, or None if the file is not found.
    """
    try:
        # Open the image using PIL
        img = Image.open(image_path)
        
        # Determine the saving format. PIL reports 'JPEG' for .jpg/.jpeg files 
        # and 'PNG' for .png files. We use the detected format.
        file_format = img.format if img.format is not None else 'PNG'
        
        buffer = io.BytesIO()
        # Save the image into the buffer using its original format
        img.save(buffer, format=file_format)
        
        # Encode the buffer content to Base64
        return base64.b64encode(buffer.getvalue()).decode()
        
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None
    except Exception as e:
        print(f"An error occurred during image processing: {e}")
        return None

def set_lighter_background_image(base64_string, lightness_level=0.7):
    """
    Injects CSS to set the background image and applies a semi-transparent 
    white overlay using linear-gradient to make the image appear lighter.

    Args:
        base64_string (str): The Base64 encoded image string.
        lightness_level (float): The transparency/lightness of the white overlay (0.0=no overlay, 1.0=pure white).
    """
    if not base64_string:
        st.error("Could not load image for background.")
        return

    # Calculate the alpha value for the RGBA overlay
    # We use lightness_level for the alpha (A) component of RGBA(R, G, B, A)
    # The 'white' color is represented by 255, 255, 255
    rgba_overlay = f"rgba(255, 255, 255, {lightness_level})"

    css = f"""
    <style>
    .stApp {{
        /* Use linear-gradient to layer a semi-transparent white color over the image. */
        background-image: linear-gradient({rgba_overlay}, {rgba_overlay}), 
                          url("data:image/png;base64,{base64_string}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# --- Main Streamlit Script ---
import io

image_file_path = "Images/Sarah2.png"

# 1. Get the base64 string
base64_img = get_base64_image(image_file_path)

# 2. Inject the CSS with a 70% lightness overlay
# Try adjusting the second argument (e.g., 0.3 for slightly lighter, 0.9 for very light)
set_lighter_background_image(base64_img, lightness_level=0.7)

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import json
import math
from streamlit.components.v1 import html as components_html

# --- Setup & Config ---
try:
    from Score_Update import score_update
except ImportError:
    def score_update(): pass

try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

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
            margin-top: -5px !important; 
        }
        
        /* Force small font on Toggle Labels inside columns */
        div[data-testid="column"] div[data-testid="stToggle"] label p {
            font-size: 10px !important;
            font-weight: 600 !important;
            color: #db5049 !important;
        }
        
        /* Prevent score text wrapping */
        .score-box {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: flex;
            align-items: center;
            height: 37px; /* Standard Streamlit Input Height */
            margin-top: 0px;
        }
        
        /* COLOR OVERRIDE: Make all standard text TimeGuessr Red */
        .stMarkdown p, label, h1, h2, h3, h4, h5, h6 {
            color: #db5049 !important;
        }
        
        /* Keep text inside inputs dark for readability */
        input {
            color: #333 !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

try:
    with open("config.json") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

st.title("Score Submission")
score_update()

# --- 1. Constants ---
COUNTRY_ALIASES = {
    "Russia": "Russian Federation",
    "Ivory Coast": "Côte d'Ivoire",
    "South Korea": "Korea, Republic of",
    "North Korea": "Korea, Democratic People's Republic of",
    "Vietnam": "Viet Nam",
    "Syria": "Syrian Arab Republic",
    "Laos": "Lao People's Democratic Republic",
    "Bolivia": "Bolivia, Plurinational State of",
    "Venezuela": "Venezuela, Bolivarian Republic of",
    "Iran": "Iran, Islamic Republic of",
    "Moldova": "Moldova, Republic of",
    "Tanzania": "Tanzania, United Republic of",
    "Palestine": "Palestine, State of",
    "Brunei": "Brunei Darussalam",
    "Congo": "Congo, Republic of the",
    "Democratic Republic of the Congo": "Congo, The Democratic Republic of the",
    "Macau": "Macao",
    "Taiwan": "Taiwan, Province of China",
    "Cape Verde": "Cabo Verde",
    "Vatican City": "Holy See (Vatican City State)",
    "Turkey": "Türkiye",
    "Bosnia": "Bosnia and Herzegovina",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
}

GEOGRAPHY_RANGES = {
    "OOO": (5000, 5000), "OO%": (4750, 4999), "OOX": (4500, 4749),
    "O%X": (4250, 4499), "OXX": (3500, 4249), "%XX": (2500, 3499),
    "XXX": (0, 2499)
}

TIME_RANGES = {
    "OOO": (5000, 5000), "OO%": (4800, 4950), "OOX": (4300, 4600),
    "O%X": (3400, 3900), "OXX": (2000, 2500), "%XX": (1000, 1000),
    "XXX": (0, 0)
}

# --- 2. Helper Functions (Visuals & Data) ---
@st.cache_data
def load_data(filepath):
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
        html.append('<div class="tg-sub">🌎 Geography: <b>???</b>/25,000</div><div class="tg-sub">📅 Time: <b>???</b>/25,000</div>')
    else:
        html.append(f'<div class="tg-sub">🌎 Geography: <b>{int(geo_sum):,}</b>/25,000</div><div class="tg-sub">📅 Time: <b>{int(time_sum):,}</b>/25,000</div>')
    
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

def validate_distance_pattern(dist_meters, geo_pattern, round_num, is_km):
    patterns = {
        "OOO": (0, 50), "OO%": (50, 37500), "OOX": (37500, 100000),
        "O%X": (100000, 250000), "OXX": (250000, 1000000),
        "%XX": (1000000, 2000000), "XXX": (2000000, float('inf'))
    }
    if geo_pattern not in patterns: return (True, "")
    low, high = patterns[geo_pattern]
    
    if geo_pattern == "OOO":
        if dist_meters <= high: return (True, "")
        excess = dist_meters - high
        unit = f"{excess/1000:.3f} km" if is_km else f"{excess} m"
        return (False, f"Round {round_num}: Distance is {unit} too great (🟩🟩🟩 requires ≤ 50 m)")
    elif geo_pattern == "XXX":
        if dist_meters > low: return (True, "")
        deficit = low - dist_meters + 1
        unit = f"{deficit/1000:.3f} km" if is_km else f"{deficit} m"
        return (False, f"Round {round_num}: Distance is {unit} too few (⬛⬛⬛ requires > 2000 km)")
    else:
        if low < dist_meters <= high: return (True, "")
        elif dist_meters <= low:
            deficit = low - dist_meters + 1
            unit = f"{deficit/1000:.3f} km" if is_km else f"{deficit} m"
            return (False, f"Round {round_num}: Distance is {unit} too few")
        else:
            excess = dist_meters - high
            unit = f"{excess/1000:.3f} km" if is_km else f"{excess} m"
            return (False, f"Round {round_num}: Distance is {unit} too great")

# --- 4. Main Layout & Execution ---
input_col, score_col = st.columns([1.25, 2])

with input_col:
    date = st.date_input("Date", value=datetime.date.today(), max_value=datetime.date.today())

# Load data at top level so it's available to all columns
df = None
date_rows = pd.DataFrame()
if date:
    df = load_data("./Data/Timeguessr_Stats.csv")
    if df is not None:
        date_rows = df[df["Date"] == date]

# Render Scoreboard & Custom Bar Chart
if not date_rows.empty:
    # 1. Custom Stacked Bars in input_col (Below Date)
    with input_col:
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
                gap: 20px; /* Fixed gap between categories */
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
                flex: 1; /* Groups expand to fill space */
                min-width: 0; /* Allows shrinking on small screens */
            }}
            .bars-row {{
                display: flex;
                gap: 5px; /* Fixed gap between Michael and Sarah */
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
                flex: 1; /* Columns expand to fill group space */
                width: 100%;
            }}
            .bar-track {{
                width: 100%; /* Bars expand to fill column */
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

    with score_col:
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
.tg-score-note { font-size:20px; margin:0 0 7px 0; white-space: nowrap; }
.tg-score-note small { color:#444; }
.dual-container { display: flex; gap: 20px; justify-content: center; width: 100%; }
</style>
"""
        combined_html = f'{component_css}<div class="dual-container"><div style="flex: 1;">{p1_html}</div><div style="flex: 1;">{p2_html}</div></div>'
        components_html(combined_html, height=520, scrolling=False)

elif df is None:
    with score_col:
        st.error("Data file not found.")
else:
    with score_col:
        st.info("No data found for this date.")

# --- 5. Consolidated Column Logic ---
def render_guess_column(container, player_name, opponent_name, timeguessr_day, date_obj, actual_rounds_data):
    """Handles the UI and logic for Michael or Sarah's data entry."""
    with container:
        # Load Data
        csv_path = f"./Data/Timeguessr_{player_name}_Parsed.csv"
        opp_csv_path = f"./Data/Timeguessr_{opponent_name}_Parsed.csv"
        
        player_df = pd.DataFrame()
        if os.path.exists(csv_path): player_df = pd.read_csv(csv_path)
        
        opp_df = pd.DataFrame()
        if os.path.exists(opp_csv_path): opp_df = pd.read_csv(opp_csv_path)
        
        current_data = player_df[player_df['Timeguessr Day'] == timeguessr_day] if not player_df.empty else pd.DataFrame()
        has_guesses = not current_data.empty
        
        opp_data = opp_df[opp_df['Timeguessr Day'] == timeguessr_day] if not opp_df.empty else pd.DataFrame()
        opp_has_guesses = not opp_data.empty

        # Hidden Logic
        reveal_key = f"{player_name.lower()}_reveal_confirmed_{timeguessr_day}"
        if st.session_state.get("last_viewed_timeguessr_day") != timeguessr_day: st.session_state[reveal_key] = False
        if reveal_key not in st.session_state: st.session_state[reveal_key] = False
        
        is_hidden = has_guesses and not opp_has_guesses and not st.session_state[reveal_key]
        
        if is_hidden:
            st.subheader(f"{player_name}'s Guesses")
            st.warning(f"⚠️ {player_name} has submitted guesses. Hidden until {opponent_name} submits.")
            if st.button(f"Reveal {player_name}", key=f"btn_rev_{player_name}_{date_obj}"):
                st.session_state[f"popup_{player_name}_{timeguessr_day}"] = True
            
            if st.session_state.get(f"popup_{player_name}_{timeguessr_day}", False):
                st.info("Are you sure?")
                c1, c2 = st.columns(2)
                if c1.button("Yes", key=f"y_{player_name}_{date_obj}"):
                    st.session_state[reveal_key] = True
                    st.session_state[f"popup_{player_name}_{timeguessr_day}"] = False
                    st.rerun()
                if c2.button("No", key=f"n_{player_name}_{date_obj}"):
                    st.session_state[f"popup_{player_name}_{timeguessr_day}"] = False
                    st.rerun()
            return

        # Header Row with Integrated Toggle
        if has_guesses:
            h1, h2 = st.columns([3, 1])
            with h1:
                st.subheader(f"{player_name}'s Guesses")
            with h2:
                # Spacer to align toggle visually with text
                st.markdown('<div style="margin-top: 5px;"></div>', unsafe_allow_html=True)
                edit_mode = st.toggle("Edit", value=False, key=f"edit_{player_name}_{date_obj}")
        else:
            st.subheader(f"{player_name}'s Guesses")
            edit_mode = False
        
        # Total Score Text Area (Defaults)
        default_text = ""
        if has_guesses:
            total_score = current_data.iloc[0].get(f'{player_name} Total Score')
            fmt_score = f"{int(total_score):,}/50,000" if pd.notna(total_score) else "_____/50,000"
            default_text = f"TimeGuessr #{timeguessr_day} {fmt_score}\n"
            
            def map_emoji(pattern):
                if pd.isna(pattern): return "⬛️⬛️⬛️"
                return pattern.replace('O', '🟩').replace('%', '🟨').replace('X', '⬛️')
            
            for r in range(1, 6):
                r_row = current_data[current_data['Timeguessr Round'] == r]
                if not r_row.empty:
                    g = r_row.iloc[0].get(f'{player_name} Geography', '')
                    t = r_row.iloc[0].get(f'{player_name} Time', '')
                    default_text += f"🌎{map_emoji(g)} 📅{map_emoji(t)}\n"
            default_text = default_text.strip()

        # Inputs Loop
        input_data = {}
        computed_total_score = 0
        
        for r in range(1, 6):
            # State calc for KM/M
            d_dist, d_km, d_year = "", False, ""
            
            if has_guesses:
                r_row = current_data[current_data['Timeguessr Round'] == r]
                if not r_row.empty:
                    row = r_row.iloc[0]
                    dist_raw = row.get(f'{player_name} Geography Distance')
                    if pd.notna(dist_raw):
                        val = float(dist_raw)
                        if val >= 1000: d_dist, d_km = str(val/1000), True
                        else: d_dist, d_km = str(val), False
                    
                    time_raw = row.get(f'{player_name} Time Guessed')
                    if pd.notna(time_raw): d_year = str(int(time_raw))

            ukey = f"u_{player_name}_{r}_{date_obj}"
            if ukey not in st.session_state: st.session_state[ukey] = d_km
            if has_guesses and not edit_mode: st.session_state[ukey] = d_km
            is_km_current = st.session_state[ukey]

            # --- HEADER ROW (Round Title + Unit Toggle) ---
            rh1, rh2, rh3 = st.columns([0.35, 0.35, 1.3])
            with rh1:
                st.markdown(f"<div style='padding-top: 7px; font-weight: bold;'>Round {r}</div>", unsafe_allow_html=True)
            with rh2:
                toggle_label = "KM" if is_km_current else "M"
                is_km = st.toggle(toggle_label, value=is_km_current, key=ukey, disabled=(has_guesses and not edit_mode))
            
            # Reduce gap between header and inputs to ALIGN with Actual Answers column
            st.markdown('<div style="margin-top: -15px;"></div>', unsafe_allow_html=True)

            # --- INPUT ROW ---
            row_cols = st.columns(2)
            
            # 1. Geo Column
            g_score_disp = None
            d_meters_calc = 0
            
            d_key = f"d_{player_name}_{r}_{date_obj}"
            current_dist_val = st.session_state.get(d_key, d_dist)
            has_dist_val = bool(current_dist_val and str(current_dist_val).strip())
            
            if has_dist_val:
                try:
                    v = float(current_dist_val)
                    if v >= 0:
                        d_meters_calc = v * 1000 if is_km else v
                        g_score_disp = geography_score(d_meters_calc)
                        computed_total_score += g_score_disp
                except: pass

            with row_cols[0]:
                dist_label = f"Dist ({'km' if is_km else 'm'})"
                if has_dist_val and g_score_disp is not None:
                    # Split column: Input (small) + Score (rest)
                    sub_c = st.columns([0.4, 0.6])
                    with sub_c[0]:
                        dist_val = st.text_input(dist_label, value=d_dist, key=d_key, disabled=(has_guesses and not edit_mode), label_visibility="visible")
                    with sub_c[1]:
                         color = "#221e8f" if player_name == "Michael" else "#8a005c"
                         bg = "#dde5eb" if player_name == "Michael" else "#edd3df"
                         # Spacer for vertical alignment with input
                         st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                         st.markdown(f'<div class="score-box" style="background-color:{bg}; color:{color}; padding:0px 8px; border-left:5px solid {color}; border-radius:4px; font-size:0.85rem; line-height:1.2; margin-top: 0px;">🌎 {g_score_disp:.0f}</div>', unsafe_allow_html=True)
                else:
                    # Full width input
                    dist_val = st.text_input(dist_label, value=d_dist, key=d_key, disabled=(has_guesses and not edit_mode), label_visibility="visible")

            # 2. Time Column
            t_score_disp = None
            year_int = None
            y_valid = False
            
            y_key = f"y_{player_name}_{r}_{date_obj}"
            current_year_val = st.session_state.get(y_key, d_year)
            has_year_val = bool(current_year_val and str(current_year_val).strip())

            if has_year_val:
                if current_year_val.isdigit() and len(current_year_val) == 4:
                    y = int(current_year_val)
                    if 1900 <= y <= date_obj.year:
                        y_valid = True
                        year_int = y
                        act_y = None
                        if r in actual_rounds_data and actual_rounds_data.get(r, {}).get('year_valid'):
                            act_y = int(actual_rounds_data[r]['year'])
                        if act_y:
                             t_score_disp = calculate_time_score(y, act_y)
                             computed_total_score += t_score_disp

            with row_cols[1]:
                if has_year_val and (t_score_disp is not None or y_valid):
                    sub_c = st.columns([0.4, 0.6])
                    with sub_c[0]:
                        year_val = st.text_input("Year", value=d_year, key=y_key, disabled=(has_guesses and not edit_mode), label_visibility="visible")
                    with sub_c[1]:
                        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                        if t_score_disp is not None:
                            color = "#221e8f" if player_name == "Michael" else "#8a005c"
                            bg = "#dde5eb" if player_name == "Michael" else "#edd3df"
                            st.markdown(f'<div class="score-box" style="background-color:{bg}; color:{color}; padding:0px 8px; border-left:5px solid {color}; border-radius:4px; font-size:0.85rem; line-height:1.2; margin-top: 0px;">📅 {t_score_disp:.0f}</div>', unsafe_allow_html=True)
                        elif y_valid:
                             st.markdown(f'<div class="score-box" style="background-color:#bcb0ff; color:#221e8f; padding:0px 8px; border-left:5px solid #221e8f; border-radius:4px; font-size:0.85rem; line-height:1.2; margin-top: 0px;" title="Submit actuals to see score">📅 ?</div>', unsafe_allow_html=True)
                else:
                    year_val = st.text_input("Year", value=d_year, key=y_key, disabled=(has_guesses and not edit_mode), label_visibility="visible")

            input_data[r] = {
                'dist': dist_val, 'dist_m': d_meters_calc, 'km': is_km, 
                'year': year_val, 'year_int': year_int, 'y_valid': y_valid,
                'g_score': g_score_disp
            }

        # Computed Score Section
        st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
        ct1, ct2 = st.columns([1, 1])
        with ct1:
            st.markdown(f"<div style='padding-top: 5px; font-weight: bold;'>Computed Total</div>", unsafe_allow_html=True)
        with ct2:
            color = "#221e8f" if player_name == "Michael" else "#8a005c"
            bg = "#dde5eb" if player_name == "Michael" else "#edd3df"
            st.markdown(f'<div class="score-box" style="background-color:{bg}; color:{color}; padding:0px 8px; border-left:5px solid {color}; border-radius:4px; font-size:1rem; line-height:1.2; margin-top: 0px;">{int(computed_total_score):,}</div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)

        total_input = st.text_area("Total Score", value=default_text, key=f"ta_{player_name}_{date_obj}", height=180, disabled=(has_guesses and not edit_mode))

        # Save Logic
        if not has_guesses or (has_guesses and edit_mode):
            if st.button(f"Submit {player_name}'s Guesses", key=f"sub_{player_name}_{date_obj}"):
                # 1. Parse Total Score
                valid_combos = ['🟩🟩🟩', '🟩🟩🟨', '🟩🟩⬛', '🟩🟩⬛️', '🟩🟨⬛', '🟩🟨⬛️', '🟩⬛⬛', '🟩⬛️⬛️', '🟩⬛⬛️', '🟩⬛️⬛', '🟨⬛⬛', '🟨⬛️⬛️', '🟨⬛⬛️', '🟨⬛️⬛', '⬛⬛⬛', '⬛️⬛️⬛️', '⬛⬛⬛️', '⬛️⬛⬛', '⬛⬛️⬛', '⬛️⬛️⬛', '⬛️⬛⬛️']
                if not total_input.strip(): st.error("Missing Total Score"); return
                
                lines = total_input.strip().split('\n')[:7]
                if len(lines) < 6 or not lines[0].startswith('TimeGuessr #'): st.error("Invalid format"); return
                
                try:
                    ts_val = int(lines[0].split()[-1].split('/')[0].replace(',', ''))
                except: st.error("Cannot parse total score number"); return

                # CHECK COMPUTED SCORE
                if abs(ts_val - computed_total_score) > 10:
                    st.error(f"Computed total ({int(computed_total_score):,}) differs from Total Score ({ts_val:,}) by more than 10 points.")
                    return

                geo_pats, time_pats = [], []
                format_ok = True
                for i, line in enumerate(lines[1:6], 1):
                    if not line.startswith('🌎') or '📅' not in line: st.error(f"Round {i} format error"); format_ok=False; break
                    parts = line.split('📅')
                    g_part = parts[0].replace('🌎', '').strip()
                    t_part = parts[1].strip()
                    
                    if g_part not in valid_combos: st.error(f"Round {i} invalid geo emoji"); format_ok=False; break
                    if t_part not in valid_combos: st.error(f"Round {i} invalid time emoji"); format_ok=False; break
                    
                    conv = lambda s: s.replace('🟩','O').replace('🟨','%').replace('⬛️','X').replace('⬛','X')
                    geo_pats.append(conv(g_part))
                    time_pats.append(conv(t_part))
                
                if not format_ok: return

                # 2. Validate Inputs & Build Rows
                new_rows = []
                for r in range(1, 6):
                    d = input_data[r]
                    if not d['dist'] or not d['year']: st.error(f"Round {r} incomplete"); return
                    if not d['y_valid']: st.error(f"Round {r} invalid year"); return
                    if float(d['dist']) < 0: st.error(f"Round {r} negative distance"); return
                    
                    ok, msg = validate_distance_pattern(d['dist_m'], geo_pats[r-1], r, d['km'])
                    if not ok: st.error(msg); return
                    
                    new_rows.append({
                        "Timeguessr Day": int(timeguessr_day),
                        "Timeguessr Round": int(r),
                        f"{player_name} Total Score": ts_val,
                        f"{player_name} Round Score": np.nan,
                        f"{player_name} Geography": geo_pats[r-1],
                        f"{player_name} Time": time_pats[r-1],
                        f"{player_name} Geography Distance": int(d['dist_m']),
                        f"{player_name} Time Guessed": int(d['year_int']),
                        f"{player_name} Time Distance": np.nan,
                        f"{player_name} Geography Score": d['g_score'],
                        f"{player_name} Geography Score (Min)": d['g_score'],
                        f"{player_name} Geography Score (Max)": d['g_score'],
                        f"{player_name} Time Score": np.nan,
                        f"{player_name} Time Score (Min)": np.nan,
                        f"{player_name} Time Score (Max)": np.nan,
                    })

                # 3. Save
                try:
                    df_out = player_df[player_df['Timeguessr Day'] != timeguessr_day]
                    df_out = pd.concat([df_out, pd.DataFrame(new_rows)], ignore_index=True)
                    df_out.sort_values(['Timeguessr Day', 'Timeguessr Round']).to_csv(csv_path, index=False)
                    st.success("Saved!"); st.rerun()
                except Exception as e: st.error(f"Save failed: {e}")

# --- 7. Execution: Bottom Section (Inputs) ---
if date:
    # Calculate Day
    reference_date = datetime.date(2025, 10, 28)
    timeguessr_day = 880 + (date - reference_date).days
    
    if "last_viewed_timeguessr_day" not in st.session_state:
        st.session_state["last_viewed_timeguessr_day"] = timeguessr_day
    
    st.divider()
    
    # Gap reduction
    st.markdown('<div style="margin-top: -20px;"></div>', unsafe_allow_html=True)

    # Define Bottom Columns
    col1, col2, col3 = st.columns([1.25, 1, 1])
    
    # Initialize actual_rounds_data
    actual_rounds_data = {}

    # Col 1: Actuals
    with col1:
        act_path = "./Data/Timeguessr_Actuals_Parsed.csv"
        act_df = pd.DataFrame()
        if os.path.exists(act_path): act_df = pd.read_csv(act_path)
        
        curr_act = act_df[(act_df['Timeguessr Day'] == timeguessr_day)]
        act_exists = not curr_act.empty
        
        m_path = "./Data/Timeguessr_Michael_Parsed.csv"
        s_path = "./Data/Timeguessr_Sarah_Parsed.csv"
        m_has = not pd.read_csv(m_path)[pd.read_csv(m_path)['Timeguessr Day'] == timeguessr_day].empty if os.path.exists(m_path) else False
        s_has = not pd.read_csv(s_path)[pd.read_csv(s_path)['Timeguessr Day'] == timeguessr_day].empty if os.path.exists(s_path) else False
        
        rev_key = f"reveal_act_{timeguessr_day}"
        if st.session_state["last_viewed_timeguessr_day"] != timeguessr_day: st.session_state[rev_key] = False
        if rev_key not in st.session_state: st.session_state[rev_key] = False
        st.session_state["last_viewed_timeguessr_day"] = timeguessr_day
        
        if act_exists and not (m_has and s_has) and not st.session_state[rev_key]:
            st.subheader("Actual Answers")
            st.warning("Hidden until both played.")
            if st.button("Reveal Actuals", key=f"rev_act_{date}"): st.session_state[rev_key] = True
        else:
            if act_exists:
                h1, h2 = st.columns([3, 1])
                with h1: st.subheader("Actual Answers")
                with h2:
                    st.markdown('<div style="margin-top: 5px;"></div>', unsafe_allow_html=True)
                    edit_act = st.toggle("Edit", key=f"edit_act_{date}")
            else:
                st.subheader("Actual Answers")
                edit_act = True

            all_valid_act = True
            save_rows = []
            
            for r in range(1, 6):
                h_col, _ = st.columns([1, 4])
                with h_col: st.markdown(f"<div style='padding-top: 7px; font-weight: bold;'>Round {r}</div>", unsafe_allow_html=True)
                st.markdown('<div style="margin-top: -15px;"></div>', unsafe_allow_html=True)

                row = curr_act[curr_act['Timeguessr Round'] == r].iloc[0] if act_exists and len(curr_act[curr_act['Timeguessr Round'] == r]) > 0 else {}
                
                rc = st.columns(4)
                y = rc[0].text_input("Year", value=str(int(row['Year'])) if 'Year' in row else "", key=f"ay_{r}_{date}", disabled=not edit_act, label_visibility="visible")
                
                opts = [""] + list(config.get('countries', {}).keys())
                c_def = row['Country'] if 'Country' in row and row['Country'] in opts else opts[0]
                c_idx = opts.index(c_def) if c_def in opts else 0
                cou = rc[1].selectbox("Country", opts, index=c_idx, key=f"ac_{r}_{date}", disabled=not edit_act, label_visibility="visible")
                
                subs = [""]
                if cou:
                    for k, v in config['countries'].get(cou, {}).items():
                        subs.append(f"─ {k} ─"); subs.extend(v)
                s_def = row.get('Subdivision', '')
                s_idx = subs.index(s_def) if s_def in subs else 0
                sub = rc[2].selectbox("Sub", subs, index=s_idx, key=f"as_{r}_{date}", disabled=not edit_act, label_visibility="visible")
                
                with rc[3]:
                    cities = []
                    if cou and not act_df.empty and 'Country' in act_df.columns and 'City' in act_df.columns:
                        cities = sorted(act_df[act_df['Country'] == cou]['City'].dropna().unique().tolist())
                    
                    c_opts = [""] + cities + ["Other"]
                    c_val = row.get('City', '')
                    if c_val in cities: cit_idx = c_opts.index(c_val)
                    elif c_val: cit_idx = c_opts.index("Other")
                    else: cit_idx = 0
                    
                    sel_c = st.selectbox("City", c_opts, index=cit_idx, key=f"acs_{r}_{date}", disabled=not edit_act, label_visibility="visible")
                    
                    if sel_c == "Other":
                        def_txt = c_val if c_val not in cities else ""
                        cit = st.text_input("New City", value=def_txt, key=f"aci_{r}_{date}", disabled=not edit_act, label_visibility="collapsed", placeholder="City Name")
                    else: cit = sel_c
                
                valid_y = y.isdigit() and len(y)==4 and 1900<=int(y)<=date.year
                actual_rounds_data[r] = {'year': y if valid_y else None, 'year_valid': valid_y}
                
                if edit_act:
                    if not (y and cou and cit and valid_y): all_valid_act = False
                    save_rows.append({"Timeguessr Day": timeguessr_day, "Timeguessr Round": r, "Year": int(y) if valid_y else 0, "Country": cou, "Subdivision": sub, "City": cit})

            if edit_act:
                if st.button("Submit Actuals", key=f"sub_act_{date}"):
                    if all_valid_act:
                        f_df = act_df[act_df['Timeguessr Day'] != timeguessr_day]
                        f_df = pd.concat([f_df, pd.DataFrame(save_rows)], ignore_index=True)
                        f_df.sort_values(['Timeguessr Day', 'Timeguessr Round']).to_csv(act_path, index=False)
                        st.success("Saved!"); st.rerun()
                    else: st.error("Invalid actuals")

    # Col 2 & 3: Players (Consolidated)
    render_guess_column(col2, "Michael", "Sarah", timeguessr_day, date, actual_rounds_data)
    render_guess_column(col3, "Sarah", "Michael", timeguessr_day, date, actual_rounds_data)