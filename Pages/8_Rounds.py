import streamlit as st
import pandas as pd
import numpy as np
import pycountry
import datetime
from streamlit.components.v1 import html as components_html

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
        return f'''
        <div class="tg-bar-bg" style="position:relative;">
            <div style="position:absolute; left:0; width:{min_pct:.2f}%; height:100%; background:#db5049;"></div>
            <div style="position:absolute; left:{min_pct:.2f}%; width:{max_pct - min_pct:.2f}%; height:100%; background:#d1d647;"></div>
            <div style="position:absolute; left:{max_pct:.2f}%; width:{100 - max_pct:.2f}%; height:100%; background:#b0afaa;"></div>
        </div>
        '''
    return '<div class="tg-bar-bg"><div class="tg-bar-fill" style="width:0%;"></div></div>'

# --- Main Page Logic ---
st.title("All Rounds")

df = load_data("./Data/Timeguessr_Stats.csv")

if df is not None:
    # Toggle to filter out single-player rounds
    st.markdown("### Filters")
    both_players_only = st.checkbox("Show only rounds where both players participated", value=True)
    show_perfect_geo = st.checkbox("Show only perfect Geography scores (5,000)", value=False)
    show_perfect_time = st.checkbox("Show only perfect Time scores (5,000)", value=False)
    
    # Country filter - get countries ordered by frequency
    country_counts = df["Country"].value_counts()
    # Remove NaN if present
    country_counts = country_counts[country_counts.index.notna()]
    available_countries = country_counts.index.tolist()
    
    selected_countries = st.multiselect(
        "Filter by countries:",
        options=available_countries,
        default=[],
        help="Select one or more countries to filter. Leave empty to show all countries."
    )
    
    # Date Filter
    min_date = df["Date"].min()
    max_date = df["Date"].max()
    
    st.markdown("### Filter by Date Range")
    date_range = st.slider(
        "Select date range:",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )
    
    # Filter dataframe by selected date range
    df_filtered = df[(df["Date"] >= date_range[0]) & (df["Date"] <= date_range[1])]
    
    # Filter by countries if any selected
    if selected_countries:
        df_filtered = df_filtered[df_filtered["Country"].isin(selected_countries)]
    
    # Filter for both players if toggle is enabled
    if both_players_only:
        df_filtered = df_filtered[
            (df_filtered["Michael Geography"].notna() | df_filtered["Michael Geography Score"].notna()) &
            (df_filtered["Sarah Geography"].notna() | df_filtered["Sarah Geography Score"].notna())
        ]
    
    # Define conditions for perfect scores
    m_geo_perf = (df_filtered["Michael Geography Score"] == 5000) | (df_filtered["Michael Geography"] == "OOO")
    s_geo_perf = (df_filtered["Sarah Geography Score"] == 5000) | (df_filtered["Sarah Geography"] == "OOO")
    m_time_perf = (df_filtered["Michael Time Score"] == 5000) | (df_filtered["Michael Time"] == "OOO")
    s_time_perf = (df_filtered["Sarah Time Score"] == 5000) | (df_filtered["Sarah Time"] == "OOO")

    # Apply filters based on selection
    if show_perfect_geo and show_perfect_time:
        # STRICT FILTER: One player must have BOTH perfect Geo and perfect Time in the same round
        cond_m_both = m_geo_perf & m_time_perf
        cond_s_both = s_geo_perf & s_time_perf
        df_filtered = df_filtered[cond_m_both | cond_s_both]
    elif show_perfect_geo:
        # Filter where ANY player got 5000 Geo
        df_filtered = df_filtered[m_geo_perf | s_geo_perf]
    elif show_perfect_time:
        # Filter where ANY player got 5000 Time
        df_filtered = df_filtered[m_time_perf | s_time_perf]
    
    if df_filtered.empty:
        st.warning("No data available for the selected filters.")
        st.stop()
    
    # Use filtered dataframe for all calculations
    df = df_filtered
    
    # 1. Calculate Grand Totals
    # We maintain sets for Days to count unique days in the filtered subset
    totals = {
        "Michael": {"Total": 0, "Geo": 0, "Time": 0, "Days": set(), "Rounds": 0}, 
        "Sarah": {"Total": 0, "Geo": 0, "Time": 0, "Days": set(), "Rounds": 0}
    }

    # Iterate through the filtered rows and sum up scores directly
    for _, row in df.iterrows():
        day_num = row["Timeguessr Day"]
        for p in ["Michael", "Sarah"]:
            # Check for participation (explicit score or pattern)
            has_data = (
                pd.notna(row.get(f"{p} Geography Score")) or 
                pd.notna(row.get(f"{p} Geography")) or
                pd.notna(row.get(f"{p} Time Score")) or 
                pd.notna(row.get(f"{p} Time"))
            )
            
            if has_data:
                g_score = get_midpoint_score(row, p, "Geography")
                t_score = get_midpoint_score(row, p, "Time")
                
                totals[p]["Rounds"] += 1
                totals[p]["Days"].add(day_num)
                totals[p]["Geo"] += g_score
                totals[p]["Time"] += t_score
                totals[p]["Total"] += (g_score + t_score)

    # Convert sets to counts
    totals["Michael"]["Days"] = len(totals["Michael"]["Days"])
    totals["Sarah"]["Days"] = len(totals["Sarah"]["Days"])
    
    total_rounds = len(df)
    unique_days = df["Timeguessr Day"].unique()
    num_days = len(unique_days)

    # 2. Build HTML
    def build_player_column(player):
        is_michael = player == "Michael"
        bg = "#dde5eb" if is_michael else "#edd3df"
        header_col = "#221e8f" if is_michael else "#8a005c"
        
        # Header Stats (based on filtered data)
        player_rounds = totals[player]["Rounds"]
        
        # Max Total is now calculated based on Rounds * 10,000 (perfect score per round)
        # instead of Days * 50,000, to accurately reflect the percentage of the subset.
        max_total = player_rounds * 10000 
        max_sub = player_rounds * 5000
        
        t_val = int(totals[player]["Total"])
        g_val = int(totals[player]["Geo"])
        tm_val = int(totals[player]["Time"])
        
        # Calculate percentages
        total_pct = (t_val / max_total * 100) if max_total > 0 else 0
        geo_pct = (g_val / max_sub * 100) if max_sub > 0 else 0
        time_pct = (tm_val / max_sub * 100) if max_sub > 0 else 0
        
        html = f"""
        <div class="tg-container" style="background-color: {bg};">
            <div class="tg-header" style="color: {header_col};">{player}</div>
            <div class="tg-total" style="font-size: 1.5rem; color: #333;">All-Time Total: {total_pct:.2f}%   -   {t_val:,} / {max_total:,}</div>
            <div class="tg-sub" style="color: #444;">🌎 All-Time Geo: {geo_pct:.2f}%   -   <b>{g_val:,}</b> / {max_sub:,}</div>
            <div class="tg-sub" style="color: #444;">📅 All-Time Time: {time_pct:.2f}%   -   <b>{tm_val:,}</b> / {max_sub:,}</div>
            <div style="margin-top: 20px;"></div>
        """
        
        # Sort and limit to last 100 rounds for display (or all if fewer than 100)
        player_df = df.sort_values(by=["Timeguessr Day", "Timeguessr Round"], ascending=[False, True])
        if len(player_df) > 100:
            player_df = player_df.head(100)
        
        current_day = None
        
        for _, row in player_df.iterrows():
            day = row["Timeguessr Day"]
            if day != current_day:
                # Use black for Day header for contrast
                html += f'<div style="font-weight:700; margin: 15px 0 5px 0; color:#000000;">Day #{day} ({row["Date"]})</div>'
                current_day = day
                
            r_num = row["Timeguessr Round"]
            country = row["Country"]
            
            # Check if Subdivision exists and is populated
            subdivision = row.get("Subdivision")
            if pd.notna(subdivision) and str(subdivision).strip() != "":
                location_display = f"{subdivision}, {country}"
            else:
                location_display = country

            flag = get_flag_img(country)
            
            # Scores & Patterns
            gs = row.get(f"{player} Geography Score")
            gp = row.get(f"{player} Geography")
            ts = row.get(f"{player} Time Score")
            tp = row.get(f"{player} Time")
            
            # Text Generation
            if pd.notna(gs): g_txt = f"{int(gs):,}"
            elif gp in GEOGRAPHY_RANGES: g_txt = f"{GEOGRAPHY_RANGES[gp][0]}-{GEOGRAPHY_RANGES[gp][1]}"
            else: g_txt = "???"
            
            if pd.notna(ts): t_txt = f"{int(ts):,}"
            elif tp in TIME_RANGES: t_txt = f"{TIME_RANGES[tp][0]}-{TIME_RANGES[tp][1]}"
            else: t_txt = "???"

            # Increased visibility for the score text in the HTML component by changing the small color to black
            html += f"""
            <div class="tg-round">
                <div style="font-size: 0.85rem; font-weight: 600; color: #db5049; margin-bottom: 2px;">Round {r_num} - {location_display}</div>
                <div class="tg-row">
                    <div class="tg-half">
                        <div class="tg-score-note">{flag} <small style="color: #000000;">{g_txt}</small></div>
                        {get_bar_html(gs, gp, GEOGRAPHY_RANGES)}
                    </div>
                    <div class="tg-half">
                        <div class="tg-score-note">📅 <small style="color: #000000;">{t_txt}</small></div>
                        {get_bar_html(ts, tp, TIME_RANGES)}
                    </div>
                </div>
            </div>
            """
            
        html += "</div>"
        return html

    col1, col2 = st.columns(2)
    
    # Base CSS template for the HTML component
    css_template = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
        body { margin: 0; padding: 0; font-family: 'Poppins', sans-serif; }
        
        .tg-container {
            padding: 15px;
            border-radius: 12px;
            width: 100%;
            box-sizing: border-box;
            /* Disable internal scrollbar */
            overflow-y: hidden; 
        }
        .tg-header { font-weight: 800; font-size: 32px; line-height: 1.1; margin-bottom: 5px; }
        .tg-total { color: #222; font-weight: 700; margin-bottom: 10px; }
        .tg-sub { font-size: 18px; color: #444; line-height: 1.3; }
        .tg-round { margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(0,0,0,0.05); }
        .tg-row { display: flex; gap: 10px; align-items: center; }
        .tg-half { flex: 1; }
        .tg-score-note { font-size: 16px; margin-bottom: 3px; white-space: nowrap; }
        .tg-bar-bg { background: #b0afaa; border-radius: 6px; height: 8px; width: 100%; overflow: hidden; position: relative; }
        .tg-bar-fill { height: 100%; border-radius: 6px; background: #db5049; }
    </style>
    """

    # Calculate required height for synchronous scrolling
    # Estimate: ~80px for header + 60px per round + 20px per day header
    # Only displaying last 100 rounds, so calculate based on that
    ROUNDS_TO_DISPLAY = min(100, total_rounds)
    ROUND_HEIGHT = 60 
    HEADER_HEIGHT = 150
    
    # Estimate number of day headers in last 100 rounds (conservative estimate)
    estimated_days_in_display = min(20, num_days)
    
    # Calculate a height for the displayed rounds + headers
    # Adding a margin (500px) for safety and padding
    component_height = (ROUNDS_TO_DISPLAY * ROUND_HEIGHT) + (estimated_days_in_display * 35) + HEADER_HEIGHT + 500 

    with col1:
        h1 = build_player_column("Michael")
        # Set exact calculated height and disable internal scrolling
        components_html(css_template + h1, height=component_height, scrolling=False)

    with col2:
        h2 = build_player_column("Sarah")
        # Set exact calculated height and disable internal scrolling
        components_html(css_template + h2, height=component_height, scrolling=False)

else:
    st.error("No data found.")