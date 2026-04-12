import streamlit as st
import base64
from PIL import Image
import io
import pandas as pd
import numpy as np
import datetime
import os
import json
import math
from streamlit.components.v1 import html as components_html

# --- Layout Config ---
st.set_page_config(layout="wide", page_title="Timeguessr Score Submission")

def get_base64_image(image_path):
    """
    Encodes an image to a Base64 string, using its detected format (e.g., PNG or JPEG) 
    when saving to the in-memory buffer.
    """
    try:
        img = Image.open(image_path)
        file_format = img.format if img.format is not None else 'PNG'
        buffer = io.BytesIO()
        img.save(buffer, format=file_format)
        return base64.b64encode(buffer.getvalue()).decode()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"An error occurred during image processing: {e}")
        return None

def set_lighter_background_image(base64_string, lightness_level=0.7):
    """
    Injects CSS to set the background image and applies a semi-transparent 
    white overlay using linear-gradient to make the image appear lighter.
    """
    if not base64_string:
        return

    rgba_overlay = f"rgba(255, 255, 255, {lightness_level})"
    css = f"""
    <style>
    .stApp {{
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


image_file_path = "Images/Sarah2.png"
base64_img = get_base64_image(image_file_path)
set_lighter_background_image(base64_img, lightness_level=0.7)

# --- Setup & Config ---
try:
    from Score_Update import score_update
except ImportError:
    def score_update(): pass

try:
    with open("styles.css", encoding="utf-8") as f:
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
    "O%X": (4250, 4499), "OXX": (3500, 4249), "%XX": (2500, 3499), "XXX": (0, 2499)
}

TIME_RANGES = {
    "OOO": (5000, 5000), "OO%": (4800, 4950), "OOX": (4300, 4600),
    "O%X": (3400, 3900), "OXX": (2000, 2500), "%XX": (1000, 1000), "XXX": (0, 0)
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

def validate_time_pattern(guessed_year, actual_year, time_pattern, round_num):
    if actual_year is None or time_pattern == "": return True, ""
    diff = abs(int(guessed_year) - actual_year)
    patterns = {
        "OOO": (0, 0), "OO%": (1, 2), "OOX": (3, 4),
        "O%X": (5, 7), "OXX": (8, 15), "%XX": (16, 20), "XXX": (21, float('inf'))
    }
    if time_pattern not in patterns: return True, ""
    low, high = patterns[time_pattern]
    if low <= diff <= high: return True, ""
    
    if diff < low:
        return False, f"Round {round_num}: Year diff ({diff}) is too small (expects {low}-{high})"
    else:
        return False, f"Round {round_num}: Year diff ({diff}) is too large (expects {low}-{high})"

# --- 4. Main Layout & Execution ---
input_col, score_col = st.columns([1, 1.5]) 

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
        .tg-score-note { font-size:18px; margin:0 0 7px 0; white-space: nowrap; }
        .tg-score-note small { color:#444; }
        
        /* Flexbox for the inner scoreboard containers to wrap on mobile */
        .dual-container { 
            display: flex; 
            flex-wrap: wrap; 
            gap: 20px; 
            justify-content: center; 
            width: 100%; 
        }
        .dual-container > div { flex: 1; min-width: 250px; }
        </style>
        """
        combined_html = f'{component_css}<div class="dual-container"><div>{p1_html}</div><div>{p2_html}</div></div>'
        components_html(combined_html, height=450, scrolling=True)

elif df is None:
    with score_col:
        st.error("Data file not found.")
else:
    with score_col:
        st.info("No data found for this date.")

# --- 5. Row-Based Input Section ---
if date:
    # Calculate Day
    reference_date = datetime.date(2025, 10, 28)
    timeguessr_day = 880 + (date - reference_date).days
    
    if "last_viewed_timeguessr_day" not in st.session_state:
        st.session_state["last_viewed_timeguessr_day"] = timeguessr_day
    st.session_state["last_viewed_timeguessr_day"] = timeguessr_day
    
    st.divider()

    # --- Pre-load Actuals Data ---
    act_path = "./Data/Timeguessr_Actuals_Parsed.csv"
    act_df = pd.DataFrame()
    if os.path.exists(act_path): act_df = pd.read_csv(act_path)
    
    curr_act = act_df[(act_df['Timeguessr Day'] == timeguessr_day)] if not act_df.empty else pd.DataFrame()
    act_exists = not curr_act.empty
    
    is_act_edit = st.session_state.get(f"edit_act_{date}", False)
    if act_exists and not is_act_edit:
        for r_idx in range(1, 6):
            for k in [f"ay_{r_idx}_{date}", f"ac_{r_idx}_{date}", f"as_{r_idx}_{date}", f"acs_{r_idx}_{date}", f"aci_{r_idx}_{date}"]:
                if k in st.session_state: del st.session_state[k]
    
    m_path = "./Data/Timeguessr_Michael_Parsed.csv"
    s_path = "./Data/Timeguessr_Sarah_Parsed.csv"
    m_has = not pd.read_csv(m_path)[pd.read_csv(m_path)['Timeguessr Day'] == timeguessr_day].empty if os.path.exists(m_path) else False
    s_has = not pd.read_csv(s_path)[pd.read_csv(s_path)['Timeguessr Day'] == timeguessr_day].empty if os.path.exists(s_path) else False
    
    rev_key_act = f"reveal_act_{timeguessr_day}"
    if rev_key_act not in st.session_state: st.session_state[rev_key_act] = False
    
    act_hidden = act_exists and not (m_has and s_has) and not st.session_state[rev_key_act]

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
        
        rev_key_p = f"{p_name.lower()}_reveal_{timeguessr_day}"
        if rev_key_p not in st.session_state: st.session_state[rev_key_p] = False
        
        is_hid = has_g and not opp_has_g and not st.session_state[rev_key_p]
        
        is_p_edit = st.session_state.get(f"edit_{p_name}_{date}", False)
        if has_g and not is_p_edit:
            for r_idx in range(1, 6):
                for k in [f"d_{p_name}_{r_idx}_{date}", f"y_{p_name}_{r_idx}_{date}", f"u_{p_name}_{r_idx}_{date}"]:
                    if k in st.session_state: del st.session_state[k]
            if f"ta_{p_name}_{date}" in st.session_state:
                del st.session_state[f"ta_{p_name}_{date}"]
        
        default_txt = ""
        if has_g:
            ts = curr_p.iloc[0].get(f'{p_name} Total Score')
            fmt = f"{int(ts):,}/50,000" if pd.notna(ts) else "_____/50,000"
            default_txt = f"TimeGuessr #{timeguessr_day} {fmt}\n"
            
            def map_emoji(pattern):
                if pd.isna(pattern): return "⬛️⬛️⬛️"
                return pattern.replace('O', '🟩').replace('%', '🟨').replace('X', '⬛️')
            
            for r in range(1, 6):
                r_row = curr_p[curr_p['Timeguessr Round'] == r]
                if not r_row.empty:
                    g = r_row.iloc[0].get(f'{p_name} Geography', '')
                    t = r_row.iloc[0].get(f'{p_name} Time', '')
                    default_txt += f"🌎{map_emoji(g)} 📅{map_emoji(t)}\n"
            default_txt = default_txt.strip()
            
        ta_key = f"ta_{p_name}_{date}"
        current_ta_val = st.session_state.get(ta_key, default_txt)
        
        geo_pats = [""] * 5
        time_pats = [""] * 5
        lines = current_ta_val.strip().split('\n')
        round_idx = 0
        valid_combos = ['🟩🟩🟩', '🟩🟩🟨', '🟩🟩⬛', '🟩🟩⬛️', '🟩🟨⬛', '🟩🟨⬛️', '🟩⬛⬛', '🟩⬛️⬛️', '🟩⬛⬛️', '🟩⬛️⬛', '🟨⬛⬛', '🟨⬛️⬛️', '🟨⬛⬛️', '🟨⬛️⬛', '⬛⬛⬛', '⬛️⬛️⬛️', '⬛⬛⬛️', '⬛️⬛⬛', '⬛⬛️⬛', '⬛️⬛️⬛', '⬛️⬛⬛️']
        conv = lambda s: s.replace('🟩','O').replace('🟨','%').replace('⬛️','X').replace('⬛','X')
        
        for line in lines:
            if '🌎' in line and '📅' in line:
                parts = line.split('📅')
                g_part = parts[0].replace('🌎', '').strip()
                t_part = parts[1].strip()
                if g_part in valid_combos and t_part in valid_combos and round_idx < 5:
                    geo_pats[round_idx] = conv(g_part)
                    time_pats[round_idx] = conv(t_part)
                    round_idx += 1

        p_state[p_name] = {
            'df': df_p, 'curr': curr_p, 'has_g': has_g, 'is_hid': is_hid,
            'rev_key': rev_key_p, 'def_txt': default_txt, 'csv': csv_p,
            'input': {}, 'comp_tot': 0, 'edit': False,
            'geo_pats': geo_pats, 'time_pats': time_pats
        }

    # --- HEADERS ROW ---
    h1, h2, h3 = st.columns([1, 1, 1])
    
    edit_act = False
    with h1:
        if act_hidden:
            st.subheader("Actual Answers")
            st.warning("Hidden until both played.")
            if st.button("Reveal Actuals", key=f"rev_act_{date}"): 
                st.session_state[rev_key_act] = True
                st.rerun()
        else:
            ah1, ah2 = st.columns([2, 1])
            with ah1: st.subheader("Actual Answers")
            with ah2: 
                edit_act = True
                if act_exists: 
                    st.markdown('<div style="margin-top: 8px;"></div>', unsafe_allow_html=True)
                    edit_act = st.toggle("Edit", key=f"edit_act_{date}")
                    
    for col, p_name in [(h2, "Michael"), (h3, "Sarah")]:
        with col:
            st_state = p_state[p_name]
            if st_state['is_hid']:
                st.subheader(f"{p_name}'s Guesses")
                st.warning(f"⚠️ Hidden until opponent submits.")
                if st.button(f"Reveal {p_name}", key=f"btn_rev_{p_name}_{date}"):
                    st.session_state[f"popup_{p_name}_{timeguessr_day}"] = True
                    
                if st.session_state.get(f"popup_{p_name}_{timeguessr_day}", False):
                    st.info("Are you sure?")
                    pc1, pc2 = st.columns(2)
                    if pc1.button("Yes", key=f"y_{p_name}_{date}"):
                        st.session_state[st_state['rev_key']] = True
                        st.session_state[f"popup_{p_name}_{timeguessr_day}"] = False
                        st.rerun()
                    if pc2.button("No", key=f"n_{p_name}_{date}"):
                        st.session_state[f"popup_{p_name}_{timeguessr_day}"] = False
                        st.rerun()
            else:
                ph1, ph2 = st.columns([2, 1])
                with ph1: st.subheader(f"{p_name}'s Guesses")
                with ph2:
                    if st_state['has_g']:
                        st.markdown('<div style="margin-top: 8px;"></div>', unsafe_allow_html=True)
                        st_state['edit'] = st.toggle("Edit", value=False, key=f"edit_{p_name}_{date}")

    # --- ROUNDS ROW-BY-ROW LOOP ---
    actual_rounds_data = {}
    all_valid_act = True
    save_rows_act = []
    
    for r in range(1, 6):
        st.markdown("---")
        rc1, rc2, rc3 = st.columns([1, 1, 1])
        
        # ACTUALS ROUND
        with rc1:
            st.markdown(f"**Round {r}**")
            if not act_hidden:
                row = curr_act[curr_act['Timeguessr Round'] == r].iloc[0] if act_exists and len(curr_act[curr_act['Timeguessr Round'] == r]) > 0 else {}
                
                r_top = st.columns(2)
                r_bot = st.columns(2)
                
                y_val = str(int(row['Year'])) if 'Year' in row and pd.notna(row['Year']) else ""
                y = r_top[0].text_input("Year", value=y_val, key=f"ay_{r}_{date}", disabled=not edit_act)
                
                opts = [""] + list(config.get('countries', {}).keys())
                c_def = row['Country'] if 'Country' in row and row['Country'] in opts else opts[0]
                c_idx = opts.index(c_def) if c_def in opts else 0
                cou = r_top[1].selectbox("Country", opts, index=c_idx, key=f"ac_{r}_{date}", disabled=not edit_act)
                
                subs = [""]
                if cou:
                    raw_subs = []
                    for v_list in config['countries'].get(cou, {}).values():
                        raw_subs.extend(v_list)
                    subs.extend(sorted(list(set(raw_subs))))
                s_def = row.get('Subdivision', '')
                s_idx = subs.index(s_def) if s_def in subs else 0
                sub = r_bot[0].selectbox("Sub", subs, index=s_idx, key=f"as_{r}_{date}", disabled=not edit_act)
                
                with r_bot[1]:
                    cities = []
                    if cou and not act_df.empty and 'Country' in act_df.columns and 'City' in act_df.columns:
                        filtered_df = act_df[act_df['Country'] == cou]
                        if sub and 'Subdivision' in filtered_df.columns:
                            filtered_df = filtered_df[filtered_df['Subdivision'] == sub]
                        cities = sorted(filtered_df['City'].dropna().unique().tolist())
                    
                    c_opts = [""] + cities + ["Other"]
                    c_val = row.get('City', '')
                    if c_val in cities: cit_idx = c_opts.index(c_val)
                    elif c_val: cit_idx = c_opts.index("Other")
                    else: cit_idx = 0
                    
                    sel_c = st.selectbox("City", c_opts, index=cit_idx, key=f"acs_{r}_{date}", disabled=not edit_act)
                    
                    if sel_c == "Other":
                        def_txt = c_val if c_val not in cities else ""
                        cit = st.text_input("New City", value=def_txt, key=f"aci_{r}_{date}", disabled=not edit_act, placeholder="City Name")
                    else: cit = sel_c
                
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
                if not st_state['is_hid']:
                    d_dist, d_km, d_year = "", False, ""
                    
                    if st_state['has_g']:
                        r_row = st_state['curr'][st_state['curr']['Timeguessr Round'] == r]
                        if not r_row.empty:
                            rw = r_row.iloc[0]
                            dist_raw = rw.get(f'{p_name} Geography Distance')
                            if pd.notna(dist_raw):
                                val = float(dist_raw)
                                if val >= 1000: d_dist, d_km = str(val/1000), True
                                else: d_dist, d_km = str(val), False
                            time_raw = rw.get(f'{p_name} Time Guessed')
                            if pd.notna(time_raw): d_year = str(int(time_raw))

                    ukey = f"u_{p_name}_{r}_{date}"
                    is_km_current = st.session_state.get(ukey, d_km)
                    d_key = f"d_{p_name}_{r}_{date}"
                    y_key = f"y_{p_name}_{r}_{date}"

                    st.markdown(f"**Round {r}**")

                    row_cols = st.columns(2)
                    
                    with row_cols[0]:
                        dist_col, tog_col = st.columns([1.5, 1])
                        with dist_col:
                            dist_val = st.text_input("Dist", value=d_dist, key=d_key, disabled=(st_state['has_g'] and not st_state['edit']))
                        with tog_col:
                            st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                            is_km = st.toggle("KM" if is_km_current else "M", value=d_km, key=ukey, disabled=(st_state['has_g'] and not st_state['edit']))
                            
                        g_score_disp = None
                        d_meters_calc = 0
                        
                        current_dist_val = st.session_state.get(d_key, d_dist)
                        has_dist_val = bool(current_dist_val and str(current_dist_val).strip())
                        
                        if has_dist_val:
                            try:
                                v = float(current_dist_val)
                                if v >= 0:
                                    d_meters_calc = v * 1000 if is_km else v
                                    g_score_disp = geography_score(d_meters_calc)
                                    st_state['comp_tot'] += g_score_disp
                            except: pass
                            
                        if has_dist_val and g_score_disp is not None:
                            c_color = "#221e8f" if p_name == "Michael" else "#8a005c"
                            c_bg = "#dde5eb" if p_name == "Michael" else "#edd3df"
                            warning_html = ""
                            
                            pat = st_state['geo_pats'][r-1]
                            if pat:
                                dist_valid, dist_msg = validate_distance_pattern(d_meters_calc, pat, r, is_km)
                                if not dist_valid:
                                    c_color = "#d32f2f"
                                    c_bg = "#ffd6d6"
                                    warning_html = " ⚠️"
                                    
                            title_attr = f' title="{dist_msg}"' if warning_html else ''
                            st.markdown(f'<div style="margin-top: 0px;"><label style="margin-bottom: 6px; display: block;"><p style="font-size: 14px; margin: 0; padding: 0;">Geo Score</p></label><div class="score-box" style="background-color:{c_bg}; color:{c_color}; border-left:5px solid {c_color};"{title_attr}>🌎 {g_score_disp:.0f}{warning_html}</div></div>', unsafe_allow_html=True)
                            
                    t_score_disp = None
                    year_int = None
                    y_valid = False
                    
                    current_year_val = st.session_state.get(y_key, d_year)
                    has_year_val = bool(current_year_val and str(current_year_val).strip())

                    if has_year_val:
                        if current_year_val.isdigit() and len(current_year_val) == 4:
                            y_val = int(current_year_val)
                            if 1900 <= y_val <= date.year:
                                y_valid = True
                                year_int = y_val
                                act_y = None
                                if r in actual_rounds_data and actual_rounds_data.get(r, {}).get('year_valid'):
                                    act_y = int(actual_rounds_data[r]['year'])
                                if act_y:
                                    t_score_disp = calculate_time_score(y_val, act_y)
                                    st_state['comp_tot'] += t_score_disp

                    with row_cols[1]:
                        year_val_in = st.text_input("Year", value=d_year, key=y_key, disabled=(st_state['has_g'] and not st_state['edit']))
                        if has_year_val:
                            if t_score_disp is not None:
                                c_color = "#221e8f" if p_name == "Michael" else "#8a005c"
                                c_bg = "#dde5eb" if p_name == "Michael" else "#edd3df"
                                warning_html = ""
                                time_msg = ""
                                
                                pat = st_state['time_pats'][r-1]
                                if pat and act_y is not None:
                                    time_valid, time_msg = validate_time_pattern(year_int, act_y, pat, r)
                                    if not time_valid:
                                        c_color = "#d32f2f"
                                        c_bg = "#ffd6d6"
                                        warning_html = " ⚠️"
                                        
                                title_attr = f' title="{time_msg}"' if warning_html else ''
                                st.markdown(f'<div style="margin-top: 0px;"><label style="margin-bottom: 6px; display: block;"><p style="font-size: 14px; margin: 0; padding: 0;">Time Score</p></label><div class="score-box" style="background-color:{c_bg}; color:{c_color}; border-left:5px solid {c_color};"{title_attr}>📅 {t_score_disp:.0f}{warning_html}</div></div>', unsafe_allow_html=True)
                            elif y_valid:
                                st.markdown(f'<div style="margin-top: 0px;"><label style="margin-bottom: 6px; display: block;"><p style="font-size: 14px; margin: 0; padding: 0;">Time Score</p></label><div class="score-box" style="background-color:#bcb0ff; color:#221e8f; border-left:5px solid #221e8f;" title="Submit actuals to see score">📅 ?</div></div>', unsafe_allow_html=True)

                    st_state['input'][r] = {
                        'dist': dist_val, 'dist_m': d_meters_calc, 'km': is_km, 
                        'year': year_val_in, 'year_int': year_int, 'y_valid': y_valid,
                        'g_score': g_score_disp
                    }

    # --- FOOTER ROW ---
    st.markdown("---")
    fc1, fc2, fc3 = st.columns([1, 1, 1])
    
    with fc1:
        if edit_act and not act_hidden:
            st.markdown("<br>", unsafe_allow_html=True) 
            if st.button("Submit Actuals", key=f"sub_act_{date}", use_container_width=True):
                if all_valid_act:
                    f_df = act_df[act_df['Timeguessr Day'] != timeguessr_day]
                    f_df = pd.concat([f_df, pd.DataFrame(save_rows_act)], ignore_index=True)
                    f_df.sort_values(['Timeguessr Day', 'Timeguessr Round']).to_csv(act_path, index=False)
                    st.success("Saved!"); st.rerun()
                else: st.error("Invalid actuals")
                
    for col, p_name in [(fc2, "Michael"), (fc3, "Sarah")]:
        with col:
            st_state = p_state[p_name]
            if not st_state['is_hid']:
                ct1, ct2 = st.columns([1, 1])
                with ct1: st.markdown(f"**Computed Total**")
                with ct2:
                    c_color = "#221e8f" if p_name == "Michael" else "#8a005c"
                    c_bg = "#dde5eb" if p_name == "Michael" else "#edd3df"
                    st.markdown(f'<div class="score-box" style="background-color:{c_bg}; color:{c_color}; border-left:5px solid {c_color};">{int(st_state["comp_tot"]):,}</div>', unsafe_allow_html=True)

                total_input = st.text_area("Total Score Text", value=st_state['def_txt'], key=f"ta_{p_name}_{date}", height=180, disabled=(st_state['has_g'] and not st_state['edit']))

                if not st_state['has_g'] or (st_state['has_g'] and st_state['edit']):
                    if st.button(f"Submit {p_name}'s Guesses", key=f"sub_{p_name}_{date}", use_container_width=True):
                        
                        def process_submission():
                            valid_combos = ['🟩🟩🟩', '🟩🟩🟨', '🟩🟩⬛', '🟩🟩⬛️', '🟩🟨⬛', '🟩🟨⬛️', '🟩⬛⬛', '🟩⬛️⬛️', '🟩⬛⬛️', '🟩⬛️⬛', '🟨⬛⬛', '🟨⬛️⬛️', '🟨⬛⬛️', '🟨⬛️⬛', '⬛⬛⬛', '⬛️⬛️⬛️', '⬛⬛⬛️', '⬛️⬛⬛', '⬛⬛️⬛', '⬛️⬛️⬛', '⬛️⬛⬛️']
                            if not total_input.strip(): 
                                st.error("Missing Total Score"); return
                            
                            lines = total_input.strip().split('\n')[:7]
                            if len(lines) < 6 or not lines[0].startswith('TimeGuessr #'): 
                                st.error("Invalid format"); return
                            
                            try:
                                ts_val = int(lines[0].split()[-1].split('/')[0].replace(',', ''))
                            except: 
                                st.error("Cannot parse total score number"); return

                            if abs(ts_val - st_state['comp_tot']) > 10:
                                st.error(f"Computed total ({int(st_state['comp_tot']):,}) differs from Total Score ({ts_val:,}) by more than 10 points.")
                                return

                            geo_pats, time_pats = [], []
                            for i, line in enumerate(lines[1:6], 1):
                                if not line.startswith('🌎') or '📅' not in line: 
                                    st.error(f"Round {i} format error"); return
                                parts = line.split('📅')
                                g_part = parts[0].replace('🌎', '').strip()
                                t_part = parts[1].strip()
                                
                                if g_part not in valid_combos: 
                                    st.error(f"Round {i} invalid geo emoji"); return
                                if t_part not in valid_combos: 
                                    st.error(f"Round {i} invalid time emoji"); return
                                
                                conv = lambda s: s.replace('🟩','O').replace('🟨','%').replace('⬛️','X').replace('⬛','X')
                                geo_pats.append(conv(g_part))
                                time_pats.append(conv(t_part))

                            new_rows = []
                            for r in range(1, 6):
                                d = st_state['input'][r]
                                if not d['dist'] or not d['year']: 
                                    st.error(f"Round {r} incomplete"); return
                                if not d['y_valid']: 
                                    st.error(f"Round {r} invalid year"); return
                                if float(d['dist']) < 0: 
                                    st.error(f"Round {r} negative distance"); return
                                
                                ok, msg = validate_distance_pattern(d['dist_m'], geo_pats[r-1], r, d['km'])
                                if not ok: 
                                    st.error(msg); return
                                
                                act_y = actual_rounds_data.get(r, {}).get('year')
                                if act_y:
                                    ok_t, msg_t = validate_time_pattern(d['year_int'], int(act_y), time_pats[r-1], r)
                                    if not ok_t:
                                        st.error(msg_t); return
                                
                                t_dist = np.nan
                                t_score = np.nan
                                t_min = np.nan
                                t_max = np.nan
                                r_score = np.nan
                                time_pat = time_pats[r-1]
                                
                                if act_y:
                                    t_dist = abs(d['year_int'] - int(act_y))
                                    t_score = calculate_time_score(d['year_int'], int(act_y))
                                
                                if pd.notna(t_score):
                                    t_min = t_score
                                    t_max = t_score
                                else:
                                    if time_pat == "OOO":
                                        t_score = 5000
                                        t_min = 5000; t_max = 5000
                                    elif time_pat == "%XX":
                                        t_score = 1000
                                        t_min = 1000; t_max = 1000
                                    elif time_pat == "XXX":
                                        t_score = 0
                                        t_min = 0; t_max = 0
                                    elif time_pat == "OO%":
                                        t_min = 4800; t_max = 4950
                                    elif time_pat == "OOX":
                                        t_min = 4300; t_max = 4600
                                    elif time_pat == "O%X":
                                        t_min = 3400; t_max = 3900
                                    elif time_pat == "OXX":
                                        t_min = 2000; t_max = 2500

                                if pd.notna(t_score) and pd.notna(d['g_score']):
                                    r_score = t_score + d['g_score']
                                
                                new_rows.append({
                                    "Timeguessr Day": int(timeguessr_day),
                                    "Timeguessr Round": int(r),
                                    f"{p_name} Total Score": ts_val,
                                    f"{p_name} Round Score": r_score,
                                    f"{p_name} Geography": geo_pats[r-1],
                                    f"{p_name} Time": time_pat,
                                    f"{p_name} Geography Distance": int(d['dist_m']),
                                    f"{p_name} Time Guessed": int(d['year_int']),
                                    f"{p_name} Time Distance": t_dist,
                                    f"{p_name} Geography Score": d['g_score'],
                                    f"{p_name} Geography Score (Min)": d['g_score'],
                                    f"{p_name} Geography Score (Max)": d['g_score'],
                                    f"{p_name} Time Score": t_score,
                                    f"{p_name} Time Score (Min)": t_min,
                                    f"{p_name} Time Score (Max)": t_max,
                                })

                            try:
                                df_out = st_state['df'][st_state['df']['Timeguessr Day'] != timeguessr_day]
                                df_out = pd.concat([df_out, pd.DataFrame(new_rows)], ignore_index=True)
                                df_out.sort_values(['Timeguessr Day', 'Timeguessr Round']).to_csv(st_state['csv'], index=False)
                                st.success("Saved!")
                                st.rerun()
                            except Exception as e: 
                                st.error(f"Save failed: {e}")
                                
                        process_submission()