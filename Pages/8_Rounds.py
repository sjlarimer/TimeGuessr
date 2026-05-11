import streamlit as st
import pandas as pd
import numpy as np
import pycountry
import datetime
from streamlit.components.v1 import html as components_html
from collections import Counter

# --- Page Config ---
st.set_page_config(page_title="All Rounds", layout="wide")

# --- CSS Loading (as requested) ---
try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# --- Global Font Override & CSS for Streamlit elements ---
st.markdown(
    """
    <style>
        /* CSS from Score Submission page for consistency */
        /* Ensures global elements (like title) are red */
        .stMarkdown p, label, h1, h2, h3, h4, h5, h6 {
            color: #db5049 !important;
        }
        /* Ensure font consistency across Streamlit elements */
        html, body, p, h1, h2, h3, h4, h5, h6, label, input, textarea, select, button {
            font-family: 'Poppins', sans-serif !important;
        }
        
        /* Sidebar specific styling */
        /* Sidebar headers white, text/labels grey */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: white !important;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown p {
            color: #696761 !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Constants ---
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

# --- Helper Functions ---
@st.cache_data
def load_data(filepath):
    try:
        df = pd.read_csv(filepath)
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        return df
    except FileNotFoundError:
        return None

@st.cache_data
def get_flag_img(country_name):
    """Generates HTML img tag for flag."""
    fallback = '<img src="https://twemoji.maxcdn.com/v/latest/svg/1f1fa-1f1f3.svg" width="20" style="vertical-align:middle;"/>'
    if not country_name or pd.isna(country_name): return fallback
    name_str = COUNTRY_ALIASES.get(country_name.strip(), country_name.strip())
    try:
        country = pycountry.countries.lookup(name_str)
        code = country.alpha_2.upper()
        codepoints = "-".join([f"1f1{format(ord(c) - ord('A') + 0xE6, 'x')}" for c in code])
        return f'<img src="https://twemoji.maxcdn.com/v/latest/svg/{codepoints}.svg" width="20" style="vertical-align:middle;"/>'
    except LookupError: return fallback

def get_midpoint_score(row, player, category):
    """Calculates score using explicit value or pattern midpoint."""
    col_score = f"{player} {category} Score"
    col_pattern = f"{player} {category}"
    ranges = GEOGRAPHY_RANGES if category == "Geography" else TIME_RANGES
    
    val = row.get(col_score)
    if pd.notna(val): return float(val)
    
    pat = row.get(col_pattern)
    if pat in ranges:
        low, high = ranges[pat]
        return (low + high) / 2
    return 0

def get_filter_score(row, player, category):
    """Returns a float score for filtering purposes."""
    col_score = f"{player} {category} Score"
    col_pattern = f"{player} {category}"
    ranges = GEOGRAPHY_RANGES if category == "Geography" else TIME_RANGES
    
    val = row.get(col_score)
    if pd.notna(val): return float(val)
    
    pat = row.get(col_pattern)
    if pat in ranges:
        return (ranges[pat][0] + ranges[pat][1]) / 2
    
    return np.nan

def get_bar_html(score, pattern, ranges):
    """Generates the progress bar HTML."""
    total = 5000
    if pd.notna(score):
        pct = min(max(score / total * 100.0, 0.0), 100.0)
        return f'<div class="tg-bar-bg"><div class="tg-bar-fill" style="width:{pct:.2f}%; background:#db5049;"></div></div>'
    elif pattern in ranges:
        min_v, max_v = ranges[pattern]
        min_pct = min_v / total * 100
        max_pct = max_v / total * 100
        return f'<div class="tg-bar-bg" style="position:relative;"><div style="position:absolute; left:0; width:{min_pct:.2f}%; height:100%; background:#db5049;"></div><div style="position:absolute; left:{min_pct:.2f}%; width:{max_pct - min_pct:.2f}%; height:100%; background:#d1d647;"></div><div style="position:absolute; left:{max_pct:.2f}%; width:{100 - max_pct:.2f}%; height:100%; background:#b0afaa;"></div></div>'
    return '<div class="tg-bar-bg"><div class="tg-bar-fill" style="width:0%;"></div></div>'

def get_base_location_name(row):
    """Returns the base location name."""
    country = row["Country"]
    subdivision = row.get("Subdivision")
    if pd.notna(subdivision) and str(subdivision).strip() != "":
        return f"{subdivision}, {country}"
    return country

# --- Main Page Logic ---
st.title("All Rounds")

df = load_data("./Data/Timeguessr_Stats.csv")

if df is not None:
    # Pre-calculate score columns for filtering
    df["_M_Geo_Filter"] = df.apply(lambda r: get_filter_score(r, "Michael", "Geography"), axis=1)
    df["_S_Geo_Filter"] = df.apply(lambda r: get_filter_score(r, "Sarah", "Geography"), axis=1)
    df["_M_Time_Filter"] = df.apply(lambda r: get_filter_score(r, "Michael", "Time"), axis=1)
    df["_S_Time_Filter"] = df.apply(lambda r: get_filter_score(r, "Sarah", "Time"), axis=1)

    # --- Sidebar Filters ---
    with st.sidebar:
        st.header("Filter Settings")
        
        min_date, max_date = df["Date"].min(), df["Date"].max()
        date_range = st.slider("Select date range:", min_date, max_date, (min_date, max_date), format="YYYY-MM-DD")
        
        both_players_only = st.checkbox("Show only rounds where both players participated", value=True)
        
        enable_location_filter = st.toggle("Filter by Location", value=False)
        selected_countries = []
        if enable_location_filter:
            country_counts = df["Country"].value_counts()
            available_countries = country_counts[country_counts.index.notna()].index.tolist()
            selected_countries = st.multiselect("Select countries:", available_countries, default=[])
        
        enable_year_filter = st.toggle("Filter by Year", value=False)
        year_range = (1900, 2026)
        if enable_year_filter:
            year_range = st.slider("Select year range:", 1900, 2026, (1900, 2026))
        
        st.markdown("### Score Filters")
        m_geo_range = st.slider("Michael Geography Score:", 0, 5000, (0, 5000))
        s_geo_range = st.slider("Sarah Geography Score:", 0, 5000, (0, 5000))
        m_time_range = st.slider("Michael Time Score:", 0, 5000, (0, 5000))
        s_time_range = st.slider("Sarah Time Score:", 0, 5000, (0, 5000))
        
        viewport_height = 1025
    
    # --- Data Filtering ---
    df_filtered = df[(df["Date"] >= date_range[0]) & (df["Date"] <= date_range[1])]
    
    if enable_year_filter and "Year" in df_filtered.columns:
        df_filtered = df_filtered[(df_filtered["Year"] >= year_range[0]) & (df_filtered["Year"] <= year_range[1])]
    if enable_location_filter and selected_countries:
        df_filtered = df_filtered[df_filtered["Country"].isin(selected_countries)]
    
    if m_geo_range != (0, 5000):
        df_filtered = df_filtered[(df_filtered["_M_Geo_Filter"] >= m_geo_range[0]) & (df_filtered["_M_Geo_Filter"] <= m_geo_range[1])]
    if s_geo_range != (0, 5000):
        df_filtered = df_filtered[(df_filtered["_S_Geo_Filter"] >= s_geo_range[0]) & (df_filtered["_S_Geo_Filter"] <= s_geo_range[1])]
    if m_time_range != (0, 5000):
        df_filtered = df_filtered[(df_filtered["_M_Time_Filter"] >= m_time_range[0]) & (df_filtered["_M_Time_Filter"] <= m_time_range[1])]
    if s_time_range != (0, 5000):
        df_filtered = df_filtered[(df_filtered["_S_Time_Filter"] >= s_time_range[0]) & (df_filtered["_S_Time_Filter"] <= s_time_range[1])]

    if both_players_only:
        df_filtered = df_filtered[
            (df_filtered["Michael Geography"].notna() | df_filtered["Michael Geography Score"].notna()) &
            (df_filtered["Sarah Geography"].notna() | df_filtered["Sarah Geography Score"].notna())
        ]
    
    if df_filtered.empty:
        st.warning("No data available for the selected filters.")
        st.stop()
    
    df = df_filtered
    
    # 1. Calculate Grand Totals and Matrix Data
    totals = {
        "Michael": {"Total": 0, "Geo": 0, "Time": 0, "Days": set(), "Rounds": 0, "Perfect_Geo": 0, "Perfect_Time": 0, "Perfect_Round": 0, "Horrible_Round": 0, "Horrible_Geo": 0, "Horrible_Time": 0}, 
        "Sarah": {"Total": 0, "Geo": 0, "Time": 0, "Days": set(), "Rounds": 0, "Perfect_Geo": 0, "Perfect_Time": 0, "Perfect_Round": 0, "Horrible_Round": 0, "Horrible_Geo": 0, "Horrible_Time": 0}
    }
    
    matrix = {
        'M_geo': {'M_time': 0, 'T_time': 0, 'S_time': 0},
        'T_geo': {'M_time': 0, 'T_time': 0, 'S_time': 0},
        'S_geo': {'M_time': 0, 'T_time': 0, 'S_time': 0},
    }
    total_h2h_rounds = 0

    for _, row in df.iterrows():
        day_num = row["Timeguessr Day"]
        
        has_m = pd.notna(row.get("Michael Geography Score")) or pd.notna(row.get("Michael Geography")) or pd.notna(row.get("Michael Time Score")) or pd.notna(row.get("Michael Time"))
        has_s = pd.notna(row.get("Sarah Geography Score")) or pd.notna(row.get("Sarah Geography")) or pd.notna(row.get("Sarah Time Score")) or pd.notna(row.get("Sarah Time"))
        
        if has_m and has_s:
            m_g, s_g = get_midpoint_score(row, "Michael", "Geography"), get_midpoint_score(row, "Sarah", "Geography")
            m_t, s_t = get_midpoint_score(row, "Michael", "Time"), get_midpoint_score(row, "Sarah", "Time")
            
            geo_win = 'M_geo' if m_g > s_g else ('S_geo' if s_g > m_g else 'T_geo')
            time_win = 'M_time' if m_t > s_t else ('S_time' if s_t > m_t else 'T_time')
            
            matrix[geo_win][time_win] += 1
            total_h2h_rounds += 1
            
        for p in ["Michael", "Sarah"]:
            has_data = pd.notna(row.get(f"{p} Geography Score")) or pd.notna(row.get(f"{p} Geography")) or pd.notna(row.get(f"{p} Time Score")) or pd.notna(row.get(f"{p} Time"))
            if has_data:
                g_score, t_score = get_midpoint_score(row, p, "Geography"), get_midpoint_score(row, p, "Time")
                
                totals[p]["Rounds"] += 1
                totals[p]["Days"].add(day_num)
                totals[p]["Geo"] += g_score
                totals[p]["Time"] += t_score
                totals[p]["Total"] += (g_score + t_score)
                
                if g_score == 5000: totals[p]["Perfect_Geo"] += 1
                if t_score == 5000: totals[p]["Perfect_Time"] += 1
                if g_score == 5000 and t_score == 5000: totals[p]["Perfect_Round"] += 1
                
                if g_score < 2500: totals[p]["Horrible_Geo"] += 1
                if t_score == 0: totals[p]["Horrible_Time"] += 1
                if t_score == 0 and g_score < 2500: totals[p]["Horrible_Round"] += 1

    totals["Michael"]["Days"] = len(totals["Michael"]["Days"])
    totals["Sarah"]["Days"] = len(totals["Sarah"]["Days"])
    
    # 2. Render Top Section: Stats Cards and Confusion Matrix (Secure Iframe)
    max_matrix_val = max([matrix[r][c] for r in matrix for c in matrix[r]]) if total_h2h_rounds > 0 else 1

    def format_cell(count):
        pct = (count / total_h2h_rounds * 100) if total_h2h_rounds > 0 else 0
        alpha = 0.05 + (0.45 * (count / max_matrix_val)) if max_matrix_val > 0 else 0.05
        bg = f"rgba(219, 80, 73, {alpha})"
        return f'<td style="background-color: {bg};"><span class="m-val">{count}</span><span class="m-pct">{pct:.1f}%</span></td>'

    def generate_stats_card(player, bg_color, header_col):
        player_rounds = totals[player]["Rounds"]
        max_total = player_rounds * 10000 
        max_sub = player_rounds * 5000
        
        t_val = int(totals[player]["Total"])
        g_val = int(totals[player]["Geo"])
        tm_val = int(totals[player]["Time"])
        
        total_pct = (t_val / max_total * 100) if max_total > 0 else 0
        geo_pct = (g_val / max_sub * 100) if max_sub > 0 else 0
        time_pct = (tm_val / max_sub * 100) if max_sub > 0 else 0
        
        avg_total = (t_val / player_rounds) if player_rounds > 0 else 0
        avg_geo = (g_val / player_rounds) if player_rounds > 0 else 0
        avg_time = (tm_val / player_rounds) if player_rounds > 0 else 0
        
        perf_geo = totals[player]["Perfect_Geo"]
        perf_time = totals[player]["Perfect_Time"]
        perf_round = totals[player]["Perfect_Round"]
        horrible_round = totals[player]["Horrible_Round"]
        horrible_geo = totals[player]["Horrible_Geo"]
        horrible_time = totals[player]["Horrible_Time"]
        
        return f"""
        <div class="stat-card" style="background-color: {bg_color};">
            <div class="stat-title" style="color: {header_col};">{player}'s Overall Stats</div>
            <div class="stat-grid">
                <div class="stat-label">Total</div>
                <div class="stat-val"><b>{t_val:,}</b></div>
                <div class="stat-metric" title="Average Total Score">🎯 {avg_total:,.0f}</div>
                <div class="stat-metric" title="Perfect 10k Rounds">🟩🟩🟩 {perf_round}</div>
                <div class="stat-metric" title="0 Time AND <2500 Geo">⬛⬛⬛ {horrible_round}</div>

                <div class="stat-label">🌎 Geo</div>
                <div class="stat-val"><b>{g_val:,}</b></div>
                <div class="stat-metric" title="Average Geo Score">🎯 {avg_geo:,.0f}</div>
                <div class="stat-metric" title="Perfect 5k Geo">🟩🟩🟩 {perf_geo}</div>
                <div class="stat-metric" title="<2500 Geo">⬛⬛⬛ {horrible_geo}</div>

                <div class="stat-label">📅 Time</div>
                <div class="stat-val"><b>{tm_val:,}</b></div>
                <div class="stat-metric" title="Average Time Score">🎯 {avg_time:,.0f}</div>
                <div class="stat-metric" title="Perfect 5k Time">🟩🟩🟩 {perf_time}</div>
                <div class="stat-metric" title="0 Time">⬛⬛⬛ {horrible_time}</div>
            </div>
        </div>
        """

    top_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
        body { margin: 0; font-family: 'Poppins', sans-serif; background: transparent; padding: 5px; box-sizing: border-box; }
        .top-container { display: flex; gap: 25px; align-items: stretch; width: 100%; justify-content: center; }
        .stats-wrapper { flex: 1.1; max-width: 700px; display: flex; flex-direction: column; gap: 15px; justify-content: center; }
        .matrix-wrapper { flex: 0.9; max-width: 550px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        
        .stat-card { padding: 15px 18px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.05); }
        .stat-title { font-weight: 800; font-size: 1.25rem; margin-bottom: 12px; line-height: 1; }
        .stat-grid { display: grid; grid-template-columns: 60px 105px minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr); gap: 8px 10px; align-items: center; background: rgba(255,255,255,0.4); padding: 12px; border-radius: 8px; font-size: 0.85rem; }
        .stat-label { font-weight: 800; color: #444; }
        .stat-val { color: #222; }
        .stat-sub { color: #666; font-size: 0.75rem; font-weight: 600; }
        .stat-metric { color: #555; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        
        .matrix-title { font-weight: 800; color: #db5049; font-size: 1.4rem; margin-bottom: 20px; text-align: center; }
        table.matrix { border-collapse: separate; border-spacing: 6px; margin: 0 auto; }
        table.matrix th, table.matrix td { border: none; }
        table.matrix th { padding: 8px; font-weight: 800; font-size: 1rem; }
        table.matrix td { padding: 12px; text-align: center; border-radius: 8px; box-shadow: inset 0 0 0 1px rgba(0,0,0,0.05); width: 80px; }
        .m-val { font-size: 1.3rem; font-weight: 800; color: #111; display: block; margin-bottom: 2px; }
        .m-pct { font-size: 0.8rem; color: #555; font-weight: 600; }
        
        /* Headers formatting */
        .th-time { color: #db5049; border-bottom: 2px solid #db5049; }
        .th-m { color: #221e8f; text-align: center; }
        .th-t { color: #696761; text-align: center; }
        .th-s { color: #8a005c; text-align: center; }
        .th-geo { color: #db5049; border-right: 2px solid #db5049; vertical-align: middle; padding-right: 12px; text-align: center; }
        .geo-text { writing-mode: vertical-rl; transform: rotate(180deg); letter-spacing: 1px; display: inline-block; margin-right: 5px; }
        .th-row-m { color: #221e8f; text-align: right; padding-right: 10px; }
        .th-row-t { color: #696761; text-align: right; padding-right: 10px; }
        .th-row-s { color: #8a005c; text-align: right; padding-right: 10px; }
    </style>
    """

    matrix_html_table = f"""
    <table class="matrix">
        <tr>
            <td colspan="2" rowspan="2" style="background:transparent; box-shadow:none;"></td>
            <th colspan="3" class="th-time">Time Result</th>
        </tr>
        <tr>
            <th class="th-m">Michael</th>
            <th class="th-t">Tie</th>
            <th class="th-s">Sarah</th>
        </tr>
        <tr>
            <th rowspan="3" class="th-geo">
                <span class="geo-text">Geography</span>
            </th>
            <th class="th-row-m">Michael</th>
            {format_cell(matrix['M_geo']['M_time'])}
            {format_cell(matrix['M_geo']['T_time'])}
            {format_cell(matrix['M_geo']['S_time'])}
        </tr>
        <tr>
            <th class="th-row-t">Tie</th>
            {format_cell(matrix['T_geo']['M_time'])}
            {format_cell(matrix['T_geo']['T_time'])}
            {format_cell(matrix['T_geo']['S_time'])}
        </tr>
        <tr>
            <th class="th-row-s">Sarah</th>
            {format_cell(matrix['S_geo']['M_time'])}
            {format_cell(matrix['S_geo']['T_time'])}
            {format_cell(matrix['S_geo']['S_time'])}
        </tr>
    </table>
    """

    top_banner_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    {top_css}
    </head>
    <body>
        <div class="top-container">
            <div class="stats-wrapper">
                {generate_stats_card("Michael", "#dde5eb", "#221e8f")}
                {generate_stats_card("Sarah", "#edd3df", "#8a005c")}
            </div>
            <div class="matrix-wrapper">
                {matrix_html_table}
            </div>
        </div>
    </body>
    </html>
    """

    # Injecting the insulated top banner with fixed height
    components_html(top_banner_html, height=420, scrolling=False)
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

    # 3. Build the Merged Single-Scroll View
    css_template = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
        body { margin: 0; padding: 0; font-family: 'Poppins', sans-serif; height: 100vh; overflow: hidden; }
        
        .tg-outer-container { display: flex; flex-direction: column; height: 100vh; width: 100%; border-radius: 12px; box-sizing: border-box; overflow: hidden; box-shadow: 0 0 10px rgba(0,0,0,0.05); }
        .tg-static-header { flex-shrink: 0; z-index: 10; display: flex; }
        .tg-header-m { flex: 1; background-color: #dde5eb; color: #221e8f; text-align: center; padding: 15px; font-size: 28px; font-weight: 800; border-bottom: 1px solid rgba(0,0,0,0.05); }
        .tg-header-s { flex: 1; background-color: #edd3df; color: #8a005c; text-align: center; padding: 15px; font-size: 28px; font-weight: 800; border-bottom: 1px solid rgba(0,0,0,0.05); border-left: 1px solid rgba(0,0,0,0.03); }
        
        .tg-scrollable-content { 
            flex-grow: 1; 
            overflow-y: auto; 
            padding: 10px 0 15px 0; 
            background: linear-gradient(90deg, #dde5eb 50%, #edd3df 50%);
        }
        .tg-scrollable-content::-webkit-scrollbar { width: 8px; }
        .tg-scrollable-content::-webkit-scrollbar-track { background: rgba(0,0,0,0.05); }
        .tg-scrollable-content::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.2); border-radius: 4px; }
        
        .tg-day-section { display: block; width: 100%; }

        .tg-day-divider {
            position: sticky;
            top: 0px;
            z-index: 5;
            text-align: center;
            margin: 15px 0;
            padding: 5px 0;
            pointer-events: none; /* Lets clicks pass through to the rounds if needed */
        }
        
        .tg-day-badge {
            font-weight: 700;
            color: #000000;
            background: rgba(255, 255, 255, 0.9); /* Opaque enough to hide text scrolling underneath */
            padding: 6px 16px;
            border-radius: 16px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            font-size: 14px;
            backdrop-filter: blur(4px); /* Soft blur for a modern glass effect */
        }
        
        .tg-round-row { display: flex; width: 100%; margin-bottom: 16px; }
        .tg-round-col { flex: 1; padding: 0 15px; box-sizing: border-box; }
        
        .tg-round { padding: 12px; background: rgba(255,255,255,0.5); border-radius: 10px; border: 1px solid rgba(0,0,0,0.03); box-sizing: border-box; width: 100%; overflow: hidden; }
        .tg-row { display: flex; gap: 15px; align-items: center; width: 100%; }
        .tg-half { flex: 1; min-width: 0; }
        .tg-score-note { font-size: 15px; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; gap: 6px; }
        .tg-bar-bg { background: rgba(0,0,0,0.08); border-radius: 10px; height: 8px; width: 100%; overflow: hidden; position: relative; }
        .tg-bar-fill { height: 100%; border-radius: 10px; background: #db5049; transition: width 0.3s ease; }
    </style>
    """

    def build_combined_view(df):
        html = f"""
        <div class="tg-outer-container">
            <div class="tg-static-header">
                <div class="tg-header-m">Michael's Rounds</div>
                <div class="tg-header-s">Sarah's Rounds</div>
            </div>
            <div class="tg-scrollable-content">
        """
        
        player_df = df.sort_values(by=["Timeguessr Day", "Timeguessr Round"], ascending=[False, True])
        
        location_counts = Counter()
        for _, row in player_df.iterrows():
            location_counts[get_base_location_name(row)] += 1
            
        current_day = None
        
        for _, row in player_df.iterrows():
            day = row["Timeguessr Day"]
            if day != current_day:
                if current_day is not None:
                    html += "</div>" # Close previous tg-day-section
                html += f'''
                <div class="tg-day-section">
                    <div class="tg-day-divider">
                        <span class="tg-day-badge">
                            Day #{day} ({row["Date"]})
                        </span>
                    </div>
                '''
                current_day = day
                
            r_num = row["Timeguessr Round"]
            country = row["Country"]
            year = row["Year"]
            
            base_loc = get_base_location_name(row)
            if location_counts[base_loc] >= 5:
                city = row.get("City")
                subdivision = row.get("Subdivision")
                is_dc = False
                if pd.notna(subdivision):
                    sub_str = str(subdivision).strip()
                    if sub_str in ["Washington DC", "Washington D.C.", "District of Columbia", "D.C.", "DC"]:
                        is_dc = True

                if not is_dc and pd.notna(city) and str(city).strip() != "":
                    location_display = f"{city}, {subdivision}, {country}" if (pd.notna(subdivision) and str(subdivision).strip() != "") else f"{city}, {country}"
                else:
                    location_display = base_loc
            else:
                location_display = base_loc

            flag = get_flag_img(country)
            
            year_str = f"({int(year)})" if pd.notna(year) and str(year).strip() != "" else ""
            loc_str = str(location_display).strip() if pd.notna(location_display) and str(location_display).strip() != "" else ""

            content_parts = []
            if loc_str: content_parts.append(loc_str)
            if year_str: content_parts.append(year_str)
            
            content_str = " ".join(content_parts)
            header_text = f"Round {r_num} - {content_str}" if content_str else f"Round {r_num}"

            m_gs_mid = get_midpoint_score(row, "Michael", "Geography")
            s_gs_mid = get_midpoint_score(row, "Sarah", "Geography")
            m_ts_mid = get_midpoint_score(row, "Michael", "Time")
            s_ts_mid = get_midpoint_score(row, "Sarah", "Time")

            m_won_geo = m_gs_mid > s_gs_mid
            s_won_geo = s_gs_mid > m_gs_mid
            m_won_time = m_ts_mid > s_ts_mid
            s_won_time = s_ts_mid > m_ts_mid

            def make_card(player, won_geo, won_time):
                gs, gp = row.get(f"{player} Geography Score"), row.get(f"{player} Geography")
                ts, tp = row.get(f"{player} Time Score"), row.get(f"{player} Time")
                
                g_txt = f"{int(gs):,}" if pd.notna(gs) else (f"{GEOGRAPHY_RANGES[gp][0]}-{GEOGRAPHY_RANGES[gp][1]}" if gp in GEOGRAPHY_RANGES else "???")
                t_txt = f"{int(ts):,}" if pd.notna(ts) else (f"{TIME_RANGES[tp][0]}-{TIME_RANGES[tp][1]}" if tp in TIME_RANGES else "???")

                crown_geo = '<span style="margin-left:auto; font-size:1.1rem;" title="Category Winner">👑</span>' if won_geo else ''
                crown_time = '<span style="margin-left:auto; font-size:1.1rem;" title="Category Winner">👑</span>' if won_time else ''

                round_total = get_midpoint_score(row, player, "Geography") + get_midpoint_score(row, player, "Time")
                opponent = "Sarah" if player == "Michael" else "Michael"
                opp_round_total = get_midpoint_score(row, opponent, "Geography") + get_midpoint_score(row, opponent, "Time")
                
                bg_color = "rgba(255, 215, 0, 0.15)" if round_total > opp_round_total else "rgba(255,255,255,0.5)"
                border_color = "rgba(218, 165, 32, 0.4)" if round_total > opp_round_total else "rgba(0,0,0,0.03)"

                return f"""
                <div class="tg-round" style="background: {bg_color}; border: 1px solid {border_color};">
                    <div style="font-size: 0.9rem; font-weight: 700; color: #db5049; margin-bottom: 6px; word-wrap: break-word; line-height: 1.3;">{header_text}</div>
                    <div class="tg-row">
                        <div class="tg-half">
                            <div class="tg-score-note">{flag} <span style="font-weight: 700; color: #222;">{g_txt}</span>{crown_geo}</div>
                            {get_bar_html(gs, gp, GEOGRAPHY_RANGES)}
                        </div>
                        <div class="tg-half">
                            <div class="tg-score-note">📅 <span style="font-weight: 700; color: #222;">{t_txt}</span>{crown_time}</div>
                            {get_bar_html(ts, tp, TIME_RANGES)}
                        </div>
                    </div>
                </div>
                """

            html += f"""
            <div class="tg-round-row">
                <div class="tg-round-col">{make_card("Michael", m_won_geo, m_won_time)}</div>
                <div class="tg-round-col">{make_card("Sarah", s_won_geo, s_won_time)}</div>
            </div>
            """
            
        if current_day is not None:
            html += "</div>" # Close the final day section
            
        html += """
            </div>
        </div>
        """
        return html

    components_html(css_template + build_combined_view(df), height=viewport_height, scrolling=False)

else:
    st.error("No data found.")