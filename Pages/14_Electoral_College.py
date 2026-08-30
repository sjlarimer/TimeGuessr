import io
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# ──────────────────────────────────────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Electoral College")
from background import set_random_sarah_background
set_random_sarah_background(lightness_level=0.7)

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
COLORS = {'michael': '#221e8f', 'sarah': '#8a005c', 'neutral': '#696761'}

ELECTORAL_VOTES = {
    'Alabama': 9, 'Alaska': 3, 'Arizona': 11, 'Arkansas': 6,
    'California': 54, 'Colorado': 10, 'Connecticut': 7, 'Delaware': 3,
    'District of Columbia': 3, 'Florida': 30, 'Georgia': 16, 'Hawaii': 4,
    'Idaho': 4, 'Illinois': 19, 'Indiana': 11, 'Iowa': 6,
    'Kansas': 6, 'Kentucky': 8, 'Louisiana': 8, 'Maine': 4,
    'Maryland': 10, 'Massachusetts': 11, 'Michigan': 15, 'Minnesota': 10,
    'Mississippi': 6, 'Missouri': 10, 'Montana': 4, 'Nebraska': 5,
    'Nevada': 6, 'New Hampshire': 4, 'New Jersey': 14, 'New Mexico': 5,
    'New York': 28, 'North Carolina': 16, 'North Dakota': 3, 'Ohio': 17,
    'Oklahoma': 7, 'Oregon': 8, 'Pennsylvania': 19, 'Rhode Island': 4,
    'South Carolina': 9, 'South Dakota': 3, 'Tennessee': 11, 'Texas': 40,
    'Utah': 6, 'Vermont': 3, 'Virginia': 13, 'Washington': 12,
    'West Virginia': 4, 'Wisconsin': 10, 'Wyoming': 3,
}
TOTAL_EV = sum(ELECTORAL_VOTES.values())  # 538

STATE_ABBREV = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI',
    'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
    'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME',
    'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
    'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE',
    'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
    'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
    'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI',
    'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX',
    'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
    'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
}

SUBDIV_NORMALIZATION = {
    'Washington DC': 'District of Columbia',
    'Washington D.C.': 'District of Columbia',
    'D.C.': 'District of Columbia',
    'DC': 'District of Columbia',
}

STATE_CENTROIDS = {
    'AL': (32.80, -86.80), 'AK': (64.20, -153.00), 'AZ': (34.30, -111.09),
    'AR': (34.95, -92.37), 'CA': (36.78, -119.42), 'CO': (39.55, -105.78),
    'CT': (41.60, -72.69), 'DE': (38.99, -75.51), 'DC': (38.91, -77.02),
    'FL': (27.99, -81.76), 'GA': (32.68, -83.62), 'HI': (20.80, -157.00),
    'ID': (44.07, -114.74), 'IL': (40.06, -89.20), 'IN': (40.27, -86.13),
    'IA': (41.88, -93.10), 'KS': (38.53, -98.35), 'KY': (37.84, -84.27),
    'LA': (30.98, -91.96), 'ME': (45.25, -69.45), 'MD': (38.81, -76.64),
    'MA': (42.41, -71.38), 'MI': (44.18, -84.47), 'MN': (46.39, -94.64),
    'MS': (32.35, -89.40), 'MO': (38.46, -92.30), 'MT': (46.88, -110.36),
    'NE': (41.49, -99.90), 'NV': (38.80, -116.42), 'NH': (43.19, -71.57),
    'NJ': (40.06, -74.41), 'NM': (34.84, -106.25), 'NY': (42.17, -74.95),
    'NC': (35.63, -79.81), 'ND': (47.53, -99.78), 'OH': (40.39, -82.76),
    'OK': (35.57, -96.93), 'OR': (43.94, -120.56), 'PA': (40.59, -77.21),
    'RI': (41.68, -71.51), 'SC': (33.84, -80.95), 'SD': (44.37, -100.34),
    'TN': (35.86, -86.66), 'TX': (31.05, -97.56), 'UT': (39.32, -111.09),
    'VT': (44.07, -72.67), 'VA': (37.43, -78.66), 'WA': (47.75, -120.74),
    'WV': (38.49, -80.95), 'WI': (44.27, -89.62), 'WY': (43.08, -107.29),
}

WIN_COLORS = {
    'michael': '#221e8f',
    'sarah':   '#8a005c',
    'tied':    '#a09587',
    'third':   '#ddd9d4',
}
WIN_LABELS = {
    'michael': 'Michael',
    'sarah':   'Sarah',
    'tied':    'Tied',
    'third':   'Not Played',
}

# ──────────────────────────────────────────────────────────────────────────────
# CSS & Styles
# ──────────────────────────────────────────────────────────────────────────────
from utils import load_css
load_css()

st.markdown("""
<style>
    /* ── Score cards ── */
    .ec-scoreboard {
        display: flex; gap: 1rem;
        margin: 1rem 0 0.6rem 0; align-items: stretch;
    }
    .ec-card {
        flex: 1; border-radius: 12px; padding: 1.1rem 1.4rem;
        text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.10);
    }
    .ec-card .card-name  { font-size: 0.82rem; font-weight: 600;
                           letter-spacing: 0.07em; text-transform: uppercase; margin-bottom: 0.15rem; }
    .ec-card .card-ev    { font-size: 3rem; font-weight: 700; line-height: 1.05; }
    .ec-card .card-label { font-size: 0.68rem; opacity: 0.72;
                           text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.1rem; }
    .ec-card .card-pct   { font-size: 0.92rem; font-weight: 600; margin-top: 0.25rem; opacity: 0.88; }
    .ec-card .card-states { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em;
                            text-transform: uppercase; opacity: 0.72; margin-top: 0.1rem; }

    .card-michael { background: linear-gradient(135deg,#221e8f,#3d37d4); color: white; }
    .card-sarah   { background: linear-gradient(135deg,#8a005c,#c2006f); color: white; }
    .card-tied    { background: linear-gradient(135deg,#857b73,#a09587); color: white; }
    .card-third   { background: linear-gradient(135deg,#d9d7cc,#eeebe5); color: #696761; }

    .win-badge {
        display: inline-block; margin-top: 0.4rem;
        background: rgba(255,255,255,0.22); border: 1px solid rgba(255,255,255,0.45);
        border-radius: 99px; padding: 2px 12px;
        font-size: 0.70rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
    }

    /* ── EV bar ── */
    .ev-bar-wrap {
        width: 100%; height: 20px; background: #e8e5e0;
        border-radius: 10px; overflow: hidden; display: flex;
        margin: 0.5rem 0 0.25rem 0;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.10);
    }
    .ev-seg { height: 100%; transition: width 0.5s ease; }

    .threshold-note {
        text-align: center; font-size: 0.76rem; color: #696761;
        margin-bottom: 1rem; font-weight: 500; letter-spacing: 0.02em;
    }

    /* ── Legend ── */
    .ec-legend {
        display: flex; gap: 1.4rem; flex-wrap: wrap;
        justify-content: center; margin: 0 0 0.8rem 0;
    }
    .ec-legend-item { display: flex; align-items: center; gap: 0.4rem; font-size: 0.79rem; color: #696761; }
    .ec-swatch { width: 13px; height: 13px; border-radius: 3px; display: inline-block; border: 1px solid rgba(0,0,0,0.12); }

    /* ── Table ── */
    .state-table { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
    .state-table th {
        background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;
        padding: 10px 12px; text-align: left; color: #696761;
        font-weight: 600; font-size: 0.74rem;
        text-transform: uppercase; letter-spacing: 0.05em;
    }
    .state-table th.right  { text-align: right; }
    .state-table th.center { text-align: center; }
    .state-table td { padding: 8px 12px; border-bottom: 1px solid #d9d7cc; color: #696761; }
    .state-table tr:hover td { background-color: rgba(255,255,255,0.55); }

    .badge { display: inline-block; padding: 2px 10px; border-radius: 99px; font-size: 0.71rem; font-weight: 600; }
    .badge-michael { background: #e8e7ff; color: #221e8f; }
    .badge-sarah   { background: #ffe6f4; color: #8a005c; }
    .badge-tied    { background: #e8e5e0; color: #696761; }
    .badge-third   { background: #f0ede8; color: #9c9790; }

    .section-header {
        font-size: 1rem; font-weight: 600; color: #696761;
        margin: 1.6rem 0 0.7rem 0;
        border-left: 4px solid #696761; padding-left: 0.6rem;
    }

    /* ── Sidebar controls (pill segmented style, matches Comparison page) ── */
    div[data-testid="stSidebar"] div[data-testid="stToggle"] label p,
    div[data-testid="stSidebar"] div[data-testid="stCheckbox"] label p {
        color: #eae8dc !important;
        font-size: 13px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stSidebar"] button[data-testid="baseButton-primary"],
    div[data-testid="stSidebar"] button[kind="primary"] {
        background-color: #3a3935 !important;
        color: #eae8dc !important;
        border-color: #3a3935 !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stSidebar"] button[data-testid="baseButton-secondary"],
    div[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #d9d7cc !important;
        color: #696761 !important;
        border-color: #d9d7cc !important;
        border-radius: 20px !important;
        font-weight: 500 !important;
    }
    div[data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover,
    div[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #c8c6bb !important;
        color: #3a3935 !important;
        border-color: #8f8d85 !important;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Data Loading
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(mtime=0):
    try:
        df = pd.read_csv("./Data/Timeguessr_Stats.csv")
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')

        def fill_missing_scores(prefix, round_col_name):
            geo_col  = f"{prefix} Geography Score"
            time_col = f"{prefix} Time Score"
            geo_min,  geo_max  = f"{geo_col} (Min)",  f"{geo_col} (Max)"
            time_min, time_max = f"{time_col} (Min)", f"{time_col} (Max)"
            if not {geo_min, geo_max, time_min, time_max}.issubset(df.columns):
                return
            m_geo  = df[geo_col].isna()  & df[geo_min].notna()  & df[geo_max].notna()
            m_time = df[time_col].isna() & df[time_min].notna() & df[time_max].notna()
            if m_geo.any():
                df.loc[m_geo,  geo_col]  = (df.loc[m_geo,  geo_min]  + df.loc[m_geo,  geo_max])  / 2
            if m_time.any():
                df.loc[m_time, time_col] = (df.loc[m_time, time_min] + df.loc[m_time, time_max]) / 2
            if round_col_name and round_col_name in df.columns:
                m_rnd = df[round_col_name].isna() & df[geo_col].notna() & df[time_col].notna()
                if m_rnd.any():
                    df.loc[m_rnd, round_col_name] = df.loc[m_rnd, geo_col] + df.loc[m_rnd, time_col]

        m_col = 'Michael Round Score' if 'Michael Round Score' in df.columns else None
        s_col = 'Sarah Round Score'   if 'Sarah Round Score'   in df.columns else None
        fill_missing_scores('Michael', m_col)
        fill_missing_scores('Sarah',   s_col)
        return df
    except FileNotFoundError:
        st.error("Stats file not found at ./Data/Timeguessr_Stats.csv")
        st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# State Results (snapshot)
# ──────────────────────────────────────────────────────────────────────────────
def calculate_state_results(df, score_mode):
    us_df = df[
        df['Country'].isin(['United States', 'USA', 'United States of America'])
    ].copy()
    us_df['State'] = us_df['Subdivision'].replace(SUBDIV_NORMALIZATION)
    us_df = us_df[us_df['State'].notna()]

    m_total_col = 'Michael Round Score' if 'Michael Round Score' in us_df.columns else None
    s_total_col = 'Sarah Round Score'   if 'Sarah Round Score'   in us_df.columns else None
    if m_total_col and s_total_col:
        us_df = us_df[us_df[m_total_col].notna() & us_df[s_total_col].notna()]

    if score_mode == "Total Score":
        if 'Michael Round Score' in us_df.columns:
            us_df['_m'] = us_df['Michael Round Score']
        else:
            us_df['_m'] = us_df['Michael Geography Score'].fillna(0) + us_df['Michael Time Score'].fillna(0)
        if 'Sarah Round Score' in us_df.columns:
            us_df['_s'] = us_df['Sarah Round Score']
        else:
            us_df['_s'] = us_df['Sarah Geography Score'].fillna(0) + us_df['Sarah Time Score'].fillna(0)
    elif score_mode == "Geography Score":
        us_df['_m'] = us_df['Michael Geography Score']
        us_df['_s'] = us_df['Sarah Geography Score']
    else:
        us_df['_m'] = us_df['Michael Time Score']
        us_df['_s'] = us_df['Sarah Time Score']

    m_played = us_df['_m'].notna()
    s_played = us_df['_s'].notna()
    us_df['_m_clean'] = np.where(m_played, us_df['_m'], np.nan)
    us_df['_s_clean'] = np.where(s_played, us_df['_s'], np.nan)

    agg = us_df.groupby('State').agg(
        Michael_Score=('_m_clean', 'sum'),
        Sarah_Score=('_s_clean', 'sum'),
        Michael_Rounds=('_m_clean', 'count'),
        Sarah_Rounds=('_s_clean', 'count'),
        Total_Rounds=('State', 'count'),
    ).reset_index()

    def get_winner(row):
        mr, sr = row['Michael_Rounds'], row['Sarah_Rounds']
        ms, ss = row['Michael_Score'],  row['Sarah_Score']
        if mr == 0 and sr == 0: return 'third'
        if mr > 0  and sr == 0: return 'michael'
        if sr > 0  and mr == 0: return 'sarah'
        if ms > ss: return 'michael'
        if ss > ms: return 'sarah'
        return 'tied'

    agg['Winner'] = agg.apply(get_winner, axis=1)
    return agg

# ──────────────────────────────────────────────────────────────────────────────
# EV Timeline
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def calculate_ev_timeline(df_json, score_mode, is_tg):
    """
    Returns a DataFrame with columns:
        Date, michael_votes, sarah_votes, tied_votes, third_votes, total_votes
    one row per unique date on which the EV tally changes.

    Strategy: replay rows chronologically, maintaining per-state running
    score totals; after every new date boundary, recompute state winners
    and EV sums — but only emit a row when something actually changed.
    """
    df = pd.read_json(io.StringIO(df_json), orient='split')
    df['Date'] = pd.to_datetime(df['Date'])

    us_df = df[df['Country'].isin(['United States', 'USA', 'United States of America'])].copy()
    us_df['State'] = us_df['Subdivision'].replace(SUBDIV_NORMALIZATION)
    us_df = us_df[us_df['State'].notna()]

    m_total_col = 'Michael Round Score' if 'Michael Round Score' in us_df.columns else None
    s_total_col = 'Sarah Round Score'   if 'Sarah Round Score'   in us_df.columns else None
    if m_total_col and s_total_col:
        us_df = us_df[us_df[m_total_col].notna() & us_df[s_total_col].notna()]

    # Pick the scoring column
    if score_mode == "Total Score":
        score_col_m = 'Michael Round Score' if 'Michael Round Score' in us_df.columns else None
        score_col_s = 'Sarah Round Score'   if 'Sarah Round Score'   in us_df.columns else None
        us_df['_m'] = us_df[score_col_m] if score_col_m else (
            us_df['Michael Geography Score'].fillna(0) + us_df['Michael Time Score'].fillna(0))
        us_df['_s'] = us_df[score_col_s] if score_col_s else (
            us_df['Sarah Geography Score'].fillna(0) + us_df['Sarah Time Score'].fillna(0))
    elif score_mode == "Geography Score":
        us_df['_m'] = us_df['Michael Geography Score']
        us_df['_s'] = us_df['Sarah Geography Score']
    else:
        us_df['_m'] = us_df['Michael Time Score']
        us_df['_s'] = us_df['Sarah Time Score']

    us_df = us_df.sort_values('Date').reset_index(drop=True)

    # Running per-state accumulators
    state_m_score  = {}   # state → cumulative michael score
    state_s_score  = {}   # state → cumulative sarah score
    state_m_rounds = {}   # state → michael round count
    state_s_rounds = {}   # state → sarah round count

    # Current winner per state (cached to detect changes)
    state_winner = {}

    def state_ev(state):
        return ELECTORAL_VOTES.get(state, 0)

    def compute_winner(state):
        ms = state_m_score.get(state, 0)
        ss = state_s_score.get(state, 0)
        mr = state_m_rounds.get(state, 0)
        sr = state_s_rounds.get(state, 0)
        if mr == 0 and sr == 0: return 'third'
        if mr > 0  and sr == 0: return 'michael'
        if sr > 0  and mr == 0: return 'sarah'
        if ms > ss: return 'michael'
        if ss > ms: return 'sarah'
        return 'tied'

    def count_states():
        c = {'michael': 0, 'sarah': 0, 'tied': 0, 'third': 0}
        for state in ELECTORAL_VOTES:
            c[state_winner.get(state, 'third')] += 1
        return c

    def tally(is_tg_mode):
        ev = {'michael': 0, 'sarah': 0, 'tied': 0, 'third': 0}
        if is_tg_mode:
            for state in ELECTORAL_VOTES:
                mr = state_m_rounds.get(state, 0)
                sr = state_s_rounds.get(state, 0)
                w  = state_winner.get(state, 'third')
                ev[w] += mr + sr
            # Unplayed states have 0 rounds; add nothing — they just stay in 'third' with 0
        else:
            for state, votes in ELECTORAL_VOTES.items():
                w = state_winner.get(state, 'third')
                ev[w] += votes
        return ev

    rows = []
    prev_ev = None

    total_rounds = 0

    # Group by date — process all rounds that happened on the same day together
    for date, group in us_df.groupby('Date', sort=True):
        changed_states = set()
        group_rounds = 0
        for _, row in group.iterrows():
            state = row['State']
            if state not in ELECTORAL_VOTES:
                continue
            changed_states.add(state)
            group_rounds += 1
        total_rounds += group_rounds
        for _, row in group.iterrows():
            state = row['State']
            if state not in ELECTORAL_VOTES:
                continue

            m_val = row['_m']
            s_val = row['_s']

            if pd.notna(m_val):
                state_m_score[state]  = state_m_score.get(state, 0)  + m_val
                state_m_rounds[state] = state_m_rounds.get(state, 0) + 1
            if pd.notna(s_val):
                state_s_score[state]  = state_s_score.get(state, 0)  + s_val
                state_s_rounds[state] = state_s_rounds.get(state, 0) + 1

            changed_states.add(state)

        # Recompute winner for every touched state
        for state in changed_states:
            state_winner[state] = compute_winner(state)

        current_ev = tally(is_tg)

        # Dynamic threshold: for TG mode, total votes = sum of rounds played so far
        if is_tg:
            total_so_far = sum(current_ev.values())
            current_threshold = total_so_far // 2 + 1
        else:
            current_threshold = 270

        if current_ev != prev_ev:
            _sc = count_states()
            rows.append({'Date': date, **current_ev, 'threshold': current_threshold, 'round_num': total_rounds,
                         'm_states': _sc['michael'], 's_states': _sc['sarah'],
                         'tied_states': _sc['tied'], 'third_states': _sc['third']})
            prev_ev = current_ev.copy()

    if not rows:
        return pd.DataFrame(columns=['Date', 'michael', 'sarah', 'tied', 'third', 'threshold', 'round_num',
                                     'm_states', 's_states', 'tied_states', 'third_states'])

    timeline = pd.DataFrame(rows)
    last = timeline.iloc[-1].copy()
    last['Date'] = pd.Timestamp.now().normalize()
    if last['Date'] > timeline['Date'].iloc[-1]:
        timeline = pd.concat([timeline, last.to_frame().T], ignore_index=True)

    return timeline

# ──────────────────────────────────────────────────────────────────────────────
# Timelapse: per-day snapshots of the full board
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def build_timelapse_frames(df_json, score_mode, is_tg):
    """Replay US rounds chronologically, emitting one snapshot per day on which
    any round was played. Each snapshot carries the full per-state winner map so
    the choropleth and scoreboard can be redrawn for that moment in time."""
    df = pd.read_json(io.StringIO(df_json), orient='split')
    df['Date'] = pd.to_datetime(df['Date'])

    us_df = df[df['Country'].isin(['United States', 'USA', 'United States of America'])].copy()
    us_df['State'] = us_df['Subdivision'].replace(SUBDIV_NORMALIZATION)
    us_df = us_df[us_df['State'].notna()]

    m_total_col = 'Michael Round Score' if 'Michael Round Score' in us_df.columns else None
    s_total_col = 'Sarah Round Score'   if 'Sarah Round Score'   in us_df.columns else None
    if m_total_col and s_total_col:
        us_df = us_df[us_df[m_total_col].notna() & us_df[s_total_col].notna()]

    if score_mode == "Total Score":
        col_m = 'Michael Round Score' if 'Michael Round Score' in us_df.columns else None
        col_s = 'Sarah Round Score'   if 'Sarah Round Score'   in us_df.columns else None
        us_df['_m'] = us_df[col_m] if col_m else (
            us_df['Michael Geography Score'].fillna(0) + us_df['Michael Time Score'].fillna(0))
        us_df['_s'] = us_df[col_s] if col_s else (
            us_df['Sarah Geography Score'].fillna(0) + us_df['Sarah Time Score'].fillna(0))
    elif score_mode == "Geography Score":
        us_df['_m'] = us_df['Michael Geography Score']
        us_df['_s'] = us_df['Sarah Geography Score']
    else:
        us_df['_m'] = us_df['Michael Time Score']
        us_df['_s'] = us_df['Sarah Time Score']

    us_df = us_df.sort_values('Date').reset_index(drop=True)

    m_score, s_score, m_rounds, s_rounds = {}, {}, {}, {}
    frames = []
    total_rounds = 0

    for date, group in us_df.groupby('Date', sort=True):
        touched = False
        for _, row in group.iterrows():
            state = row['State']
            if state not in ELECTORAL_VOTES:
                continue
            if pd.notna(row['_m']):
                m_score[state]  = m_score.get(state, 0)  + row['_m']
                m_rounds[state] = m_rounds.get(state, 0) + 1
            if pd.notna(row['_s']):
                s_score[state]  = s_score.get(state, 0)  + row['_s']
                s_rounds[state] = s_rounds.get(state, 0) + 1
            total_rounds += 1
            touched = True

        if not touched:
            continue

        states_snap = {}
        for stt in ELECTORAL_VOTES:
            ms, ss = m_score.get(stt, 0), s_score.get(stt, 0)
            mr, sr = m_rounds.get(stt, 0), s_rounds.get(stt, 0)
            if   mr == 0 and sr == 0: w = 'third'
            elif mr > 0  and sr == 0: w = 'michael'
            elif sr > 0  and mr == 0: w = 'sarah'
            elif ms > ss:             w = 'michael'
            elif ss > ms:             w = 'sarah'
            else:                     w = 'tied'
            states_snap[stt] = (w, float(ms), float(ss), int(mr), int(sr))

        frames.append({
            'Date': pd.Timestamp(date),
            'round_num': int(total_rounds),
            'states': states_snap,
        })

    return frames


def frame_to_state_results(frame, is_tg_college):
    """Turn one timelapse snapshot into a state_results-shaped DataFrame."""
    recs = []
    for stt, ev_ct in ELECTORAL_VOTES.items():
        w, ms, ss, mr, sr = frame['states'][stt]
        recs.append({
            'State': stt, 'EV': ev_ct,
            'Michael_Score': ms, 'Sarah_Score': ss,
            'Michael_Rounds': mr, 'Sarah_Rounds': sr,
            'Total_Rounds': mr + sr, 'Winner': w,
        })
    sr_df = pd.DataFrame(recs)
    sr_df['abbrev']       = sr_df['State'].map(STATE_ABBREV)
    sr_df['color']        = sr_df['Winner'].map(WIN_COLORS)
    sr_df['winner_label'] = sr_df['Winner'].map(WIN_LABELS)
    if is_tg_college:
        sr_df['Votes'] = ((sr_df['Michael_Rounds'] + sr_df['Sarah_Rounds']).astype(int)) / 2 + 2
    else:
        sr_df['Votes'] = sr_df['EV'].astype(int)
    return sr_df


# ──────────────────────────────────────────────────────────────────────────────
# Shared renderers (used by both the live view and the timelapse)
# ──────────────────────────────────────────────────────────────────────────────
def build_ev_map(state_results, is_tg_college):
    fig = go.Figure()

    # Always emit one Choropleth trace per outcome, in a fixed order, even when
    # empty. Keeping the trace list stable lets Plotly patch the map in place
    # between timelapse frames instead of tearing it down and remounting (which
    # reads as a blink).
    for winner_key, color in WIN_COLORS.items():
        subset = state_results[state_results['Winner'] == winner_key]

        hover_texts = []
        for _, row in subset.iterrows():
            mr, sr    = int(row['Michael_Rounds']), int(row['Sarah_Rounds'])
            ms, ss    = int(row['Michael_Score']),  int(row['Sarah_Score'])
            votes_val = int(row['Votes'])
            ev_val    = int(row['EV'])

            if winner_key == 'third':
                detail = "Not yet played"
            elif winner_key == 'tied':
                detail = f"Tied — Michael: {ms:,} pts ({mr} rounds) · Sarah: {ss:,} pts ({sr} rounds)"
            elif winner_key == 'michael':
                detail = f"Michael: {ms:,} pts ({mr} rounds) · Sarah: {ss:,} pts ({sr} rounds)"
            else:
                detail = f"Sarah: {ss:,} pts ({sr} rounds) · Michael: {ms:,} pts ({mr} rounds)"

            vote_line = (f"Rounds (votes): <b>{votes_val:,}</b>" if is_tg_college
                         else f"Electoral Votes: <b>{ev_val}</b>")

            hover_texts.append(
                f"<b>{row['State']}</b><br>"
                f"{vote_line}<br>"
                f"Winner: <b>{row['winner_label']}</b><br>"
                f"{detail}"
                f"<extra></extra>"
            )

        fig.add_trace(go.Choropleth(
            locations=list(subset['abbrev']),
            z=[1] * len(subset),
            locationmode='USA-states',
            colorscale=[[0, color], [1, color]],
            zmin=0, zmax=1,
            showscale=False,
            marker_line_color='white',
            marker_line_width=1.8,
            hovertemplate=hover_texts if hover_texts else None,
            name=WIN_LABELS[winner_key],
            showlegend=False,
        ))

    lats, lons, labels, label_colors = [], [], [], []
    for _, row in state_results.iterrows():
        abbr = row['abbrev']
        if abbr and abbr in STATE_CENTROIDS:
            lat, lon = STATE_CENTROIDS[abbr]
            lats.append(lat)
            lons.append(lon)
            labels.append(str(int(row['Votes'])))
            # Match the timelapse: white on the filled (won/tied) states,
            # dark grey on the pale "not played" states so the number stays legible.
            label_colors.append('#5a5651' if row['Winner'] == 'third' else '#ffffff')

    fig.add_trace(go.Scattergeo(
        lat=lats, lon=lons,
        mode='text',
        text=labels,
        textfont=dict(size=8.5, color=label_colors, family='Arial Black'),
        hoverinfo='skip',
        showlegend=False,
    ))

    fig.update_layout(
        geo=dict(
            scope='usa',
            showframe=False,
            showcoastlines=False,
            showland=True,  landcolor='#f0ede8',
            showlakes=True, lakecolor='#dde8f0',
            bgcolor='rgba(0,0,0,0)',
            projection_type='albers usa',
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=0, b=0, l=0, r=0),
        height=500,
        hoverlabel=dict(bgcolor='white', font_size=13, bordercolor='#d9d7cc'),
        showlegend=False,
        # Same revision id every frame → Plotly treats each update as "same
        # plot, new data" and re-renders in place rather than resetting.
        uirevision='ec-map',
    )
    return fig


def render_ev_scoreboard(state_results, is_tg_college, vote_label, vote_label_s, show_popular=True):
    TOTAL_VOTES = int(state_results['Votes'].sum())
    ev = {k: int(state_results.loc[state_results['Winner'] == k, 'Votes'].sum()) for k in WIN_COLORS}
    threshold = TOTAL_VOTES // 2 + 1
    overall_winner = ('michael' if ev['michael'] >= threshold
                      else 'sarah' if ev['sarah'] >= threshold
                      else None)

    threshold_desc = (f"{threshold:,} {vote_label_s} needed to win · {TOTAL_VOTES:,} total"
                      if is_tg_college else
                      f"270 electoral votes needed to win · {TOTAL_VOTES:,} total")

    bar_total = TOTAL_VOTES if TOTAL_VOTES > 0 else 1
    segs = [
        (ev['michael'], WIN_COLORS['michael']),
        (ev['tied'],    WIN_COLORS['tied']),
        (ev['third'],   WIN_COLORS['third']),
        (ev['sarah'],   WIN_COLORS['sarah']),
    ]
    bar_inner = "".join(
        f'<div class="ev-seg" style="width:{v/bar_total*100:.2f}%;background:{c};"></div>'
        for v, c in segs if v > 0
    )

    # Assemble the whole scoreboard as one HTML string emitted in a single
    # st.markdown call. Fewer elements = a cleaner in-place diff between
    # timelapse frames (less flicker).
    html = [f'<div class="ev-bar-wrap">{bar_inner}</div>'
            f'<div class="threshold-note">{threshold_desc}</div>']

    if show_popular:
        pv_michael = int(state_results['Michael_Score'].sum())
        pv_sarah   = int(state_results['Sarah_Score'].sum())
        pv_total   = pv_michael + pv_sarah
        if pv_total > 0:
            pv_m_pct = pv_michael / pv_total * 100
            pv_s_pct = pv_sarah   / pv_total * 100
            pv_winner = 'michael' if pv_michael > pv_sarah else ('sarah' if pv_sarah > pv_michael else None)

            html.append(f"""
    <div style="margin: 0.2rem 0 0.1rem 0;">
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:0.3rem;">
        <span style="font-size:0.75rem;font-weight:600;color:{COLORS['michael']};letter-spacing:0.04em;text-transform:uppercase;">
          {"&#9654; " if pv_winner == "michael" else ""}Michael &nbsp;
          <span style="font-weight:700;font-size:0.88rem;">{pv_michael:,}</span>
          <span style="font-weight:400;opacity:0.7;"> pts ({pv_m_pct:.1f}%)</span>
        </span>
        <span style="font-size:0.72rem;color:#696761;font-weight:500;letter-spacing:0.03em;">Popular Vote</span>
        <span style="font-size:0.75rem;font-weight:600;color:{COLORS['sarah']};letter-spacing:0.04em;text-transform:uppercase;text-align:right;">
          <span style="font-weight:700;font-size:0.88rem;">{pv_sarah:,}</span>
          <span style="font-weight:400;opacity:0.7;"> pts ({pv_s_pct:.1f}%)</span>
          &nbsp;{"&#9664; " if pv_winner == "sarah" else ""}Sarah
        </span>
      </div>
      <div style="width:100%;height:16px;background:#e8e5e0;border-radius:8px;overflow:hidden;display:flex;
                  box-shadow:inset 0 1px 3px rgba(0,0,0,0.10);">
        <div style="width:{pv_m_pct:.2f}%;background:linear-gradient(90deg,#221e8f,#3d37d4);height:100%;"></div>
        <div style="width:{pv_s_pct:.2f}%;background:linear-gradient(90deg,#c2006f,#8a005c);height:100%;"></div>
      </div>
    </div>
    """)

    html.append("<div style='margin-bottom:0.8rem;'></div>")

    def winner_badge(player):
        return '<div class="win-badge">&#127942; WINNER</div>' if overall_winner == player else ''

    m_pct  = ev['michael'] / bar_total * 100
    s_pct  = ev['sarah']   / bar_total * 100
    ti_pct = ev['tied']    / bar_total * 100
    th_pct = ev['third']   / bar_total * 100

    nst = {k: int((state_results['Winner'] == k).sum()) for k in WIN_COLORS}
    def states_line(k):
        n = nst[k]
        return f'<div class="card-states">{n} {"state" if n == 1 else "states"}</div>'

    html.append(f"""
<div class="ec-scoreboard">
  <div class="ec-card card-michael">
    <div class="card-name">Michael</div>
    <div class="card-ev">{ev['michael']:,}</div>
    <div class="card-label">{vote_label}</div>
    <div class="card-pct">{m_pct:.1f}%</div>
    {states_line('michael')}
    {winner_badge('michael')}
  </div>
  <div class="ec-card card-sarah">
    <div class="card-name">Sarah</div>
    <div class="card-ev">{ev['sarah']:,}</div>
    <div class="card-label">{vote_label}</div>
    <div class="card-pct">{s_pct:.1f}%</div>
    {states_line('sarah')}
    {winner_badge('sarah')}
  </div>
  <div class="ec-card card-tied">
    <div class="card-name">Tied</div>
    <div class="card-ev">{ev['tied']:,}</div>
    <div class="card-label">{vote_label}</div>
    <div class="card-pct">{ti_pct:.1f}%</div>
    {states_line('tied')}
  </div>
  <div class="ec-card card-third">
    <div class="card-name">Not Played</div>
    <div class="card-ev">{ev['third']:,}</div>
    <div class="card-label">{vote_label}</div>
    <div class="card-pct">{th_pct:.1f}%</div>
    {states_line('third')}
  </div>
</div>
""")

    st.markdown("".join(html), unsafe_allow_html=True)

    return ev, TOTAL_VOTES, threshold, overall_winner


def render_ev_legend(vote_label_s):
    tied_label = f"Tied (no {vote_label_s} awarded)"
    st.markdown(f"""
<div class="ec-legend">
  <span class="ec-legend-item">
    <span class="ec-swatch" style="background:#221e8f;"></span>Michael wins
  </span>
  <span class="ec-legend-item">
    <span class="ec-swatch" style="background:#8a005c;"></span>Sarah wins
  </span>
  <span class="ec-legend-item">
    <span class="ec-swatch" style="background:#a09587;"></span>{tied_label}
  </span>
  <span class="ec-legend-item">
    <span class="ec-swatch" style="background:#ddd9d4;border-color:#c8c3bc;"></span>Not yet played
  </span>
</div>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _plotly_js_bundle():
    from plotly.offline import get_plotlyjs
    return get_plotlyjs()


def build_timelapse_payload(frames, is_tg_college):
    """Flatten the frame snapshots into a compact JSON payload the browser-side
    player consumes: one map + scoreboard that it updates in place per frame.

    State colour codes: 0/1 Michael faded/solid, 2/3 Sarah faded/solid,
    4/5 tied faded/solid, 6 not played. A state stays faded while it can still
    change hands; from the last frame its winner changes onward it is shown
    solid ("locked in").
    """
    abbrevs = [STATE_ABBREV[s] for s in ELECTORAL_VOTES]
    lats = [STATE_CENTROIDS[a][0] for a in abbrevs]
    lons = [STATE_CENTROIDS[a][1] for a in abbrevs]
    state_order = list(ELECTORAL_VOTES)

    # Last frame at which each state's winner changed → settled from then on.
    last_flip = {s: 0 for s in state_order}
    prev = {s: 'third' for s in state_order}
    for i, fr in enumerate(frames):
        snap = fr['states']
        for s in state_order:
            w = snap[s][0]
            if w != prev[s]:
                last_flip[s] = i
            prev[s] = w

    base = {'michael': 0, 'sarah': 2, 'tied': 4}

    def cc(winner, settled):
        if winner == 'third':
            return 6
        return base[winner] + (1 if settled else 0)

    out = []
    for i, fr in enumerate(frames):
        sr = frame_to_state_results(fr, is_tg_college)
        winners = list(sr['Winner'])
        codes = [cc(w, i >= last_flip[state_order[j]])
                 for j, w in enumerate(winners)]
        labels = [str(int(v)) for v in sr['Votes']]
        ev = {k: int(sr.loc[sr['Winner'] == k, 'Votes'].sum()) for k in WIN_COLORS}
        nst = {k: int((sr['Winner'] == k).sum()) for k in WIN_COLORS}
        total = int(sr['Votes'].sum())
        out.append({
            'date':      pd.Timestamp(fr['Date']).strftime('%B %d, %Y'),
            'round':     int(fr['round_num']),
            'codes':     codes,
            'labels':    labels,
            'names':     list(sr['State']),
            'ev':        [ev['michael'], ev['sarah'], ev['tied'], ev['third']],
            'nstates':   [nst['michael'], nst['sarah'], nst['tied'], nst['third']],
            'total':     total,
            'threshold': total // 2 + 1,
            'pv':        [int(sr['Michael_Score'].sum()), int(sr['Sarah_Score'].sum())],
        })

    light = {'michael': '#9b9acd', 'sarah': '#ca8cb6', 'tied': '#cbc5bd'}
    colors = [light['michael'], WIN_COLORS['michael'],
              light['sarah'],   WIN_COLORS['sarah'],
              light['tied'],    WIN_COLORS['tied'],
              WIN_COLORS['third']]

    return {
        'abbrevs':   abbrevs,
        'lats':      lats,
        'lons':      lons,
        'frames':    out,
        'colors':    colors,
        'is_tg':     bool(is_tg_college),
        'vote_label': "Rounds" if is_tg_college else "Electoral Votes",
        'frame_ms':  450,
    }


def render_timelapse_player(payload):
    """A self-contained HTML/JS player. The whole animation runs client-side:
    Plotly draws the map once and each frame only restyles the state fills, so
    nothing blinks except the states that actually change hands."""
    import json
    import streamlit.components.v1 as components

    data_json = json.dumps(payload).replace("</", "<\\/")
    plotly_js = _plotly_js_bundle()

    html = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
  :root { color-scheme: light; }
  body { margin:0; background:transparent;
         font-family:'Poppins','Source Sans Pro',-apple-system,BlinkMacSystemFont,sans-serif; }
  #tl { color:#696761; font-family:'Poppins','Source Sans Pro',sans-serif; }
  #tl .tl-head { display:flex; justify-content:space-between; align-items:baseline; margin:0 0 4px; font-size:0.9rem; }
  #tl .tl-head b { color:#4a4844; }
  /* Bars — match the static view: EV bar 20px/10px, popular-vote bar 16px/8px */
  #tl .ev-wrap, #tl .pvbar { width:100%; background:#e8e5e0; overflow:hidden; display:flex;
                             box-shadow:inset 0 1px 3px rgba(0,0,0,0.10); }
  #tl .ev-wrap { height:20px; border-radius:10px; margin:0.5rem 0 0.6rem; }
  #tl .pvbar   { height:16px; border-radius:8px; margin:0 0 0.3rem; }
  #tl .ev-wrap > div { height:100%; transition:width .5s ease; }
  #tl .pvbar   > div { height:100%; transition:width .4s ease; }
  #tl .thresh { text-align:center; font-size:0.76rem; color:#696761; font-weight:500;
                letter-spacing:0.02em; margin:2px 0 0.9rem; }
  #tl .cards { display:flex; gap:1rem; margin:1rem 0 0.6rem; align-items:stretch; }
  #tl .card { flex:1; border-radius:12px; padding:1.1rem 1.4rem; text-align:center; color:#fff;
              box-shadow:0 2px 12px rgba(0,0,0,0.10); }
  #tl .card .n  { font-size:0.82rem; font-weight:600; letter-spacing:0.07em; text-transform:uppercase;
                  margin-bottom:0.15rem; }
  #tl .card .v  { font-size:3rem; font-weight:700; line-height:1.05; }
  #tl .card .l  { font-size:0.68rem; opacity:0.72; text-transform:uppercase; letter-spacing:0.06em;
                  margin-top:0.1rem; }
  #tl .card .p  { font-size:0.92rem; font-weight:600; margin-top:0.25rem; opacity:0.88; }
  #tl .card .st { font-size:0.7rem; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;
                  opacity:0.72; margin-top:0.1rem; }
  #tl .c0 { background:linear-gradient(135deg,#221e8f,#3d37d4); }
  #tl .c1 { background:linear-gradient(135deg,#8a005c,#c2006f); }
  #tl .c2 { background:linear-gradient(135deg,#857b73,#a09587); }
  #tl .c3 { background:linear-gradient(135deg,#d9d7cc,#eeebe5); color:#696761; }
  #tl .pv { display:flex; justify-content:space-between; align-items:baseline;
            font-size:0.72rem; margin:0 0 0.3rem; font-weight:600; }
  #tl .pv .m { color:#221e8f; font-size:0.75rem; letter-spacing:0.04em; text-transform:uppercase; }
  #tl .pv .s { color:#8a005c; font-size:0.75rem; letter-spacing:0.04em; text-transform:uppercase; }
  #tl .pv > span:nth-child(2) { color:#696761; font-weight:500; letter-spacing:0.03em; text-transform:none; }
  #tl .pv b { font-size:0.88rem; font-weight:700; }
  #tl .pv i { font-style:normal; font-weight:400; opacity:0.7; letter-spacing:0; }
  #tl .barcap { text-align:center; font-size:0.7rem; font-weight:600; letter-spacing:.04em;
                text-transform:uppercase; color:#8f8a83; margin:0 0 2px; }
  #tl #map { width:100%; height:490px; }
  #tl .tl-foot { margin-top:8px; }
  #tl .ctl { display:flex; align-items:center; gap:12px; }
  #tl button { font:inherit; font-size:0.85rem; font-weight:600; padding:6px 16px; border-radius:8px;
               border:1px solid #c8c3bc; background:#fff; color:#4a4844; cursor:pointer; }
  #tl button:hover { background:#f3f0ec; }
  /* Timeline scrubber: light-grey track, coloured (from JS) only over spans of
     time when someone had clinched the EC; portion past the current frame is
     washed out. */
  #tl input[type=range] {
    flex:1; -webkit-appearance:none; appearance:none;
    height:16px; background:transparent; cursor:pointer; margin:0; --tl-pos:0%;
  }
  #tl input[type=range]::-webkit-slider-runnable-track {
    height:12px; border-radius:6px;
    background:
      linear-gradient(to right, rgba(0,0,0,0) var(--tl-pos), rgba(240,237,232,0.6) var(--tl-pos)),
      var(--tl-grad, #d9d7cc);
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.28);
  }
  #tl input[type=range]::-moz-range-track {
    height:12px; border-radius:6px;
    background:
      linear-gradient(to right, rgba(0,0,0,0) var(--tl-pos), rgba(240,237,232,0.6) var(--tl-pos)),
      var(--tl-grad, #d9d7cc);
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.28);
  }
  #tl input[type=range]::-webkit-slider-thumb {
    -webkit-appearance:none; appearance:none; width:16px; height:16px; border-radius:50%;
    background:#fff; border:2px solid #3a3935; margin-top:-2px; box-shadow:0 1px 4px rgba(0,0,0,0.35);
  }
  #tl input[type=range]::-moz-range-thumb {
    width:14px; height:14px; border-radius:50%;
    background:#fff; border:2px solid #3a3935; box-shadow:0 1px 4px rgba(0,0,0,0.35);
  }
  #tl .legend { display:flex; gap:18px; justify-content:center; flex-wrap:wrap; font-size:0.78rem; margin:8px 0 2px; }
  #tl .legend span { display:inline-flex; align-items:center; gap:6px; }
  #tl .legend-sub { font-size:0.72rem; opacity:0.8; margin:2px 0 2px; }
  #tl .sw { width:13px; height:13px; border-radius:3px; border:1px solid rgba(0,0,0,0.12); display:inline-block; }
</style>

<div id="tl">
  <div class="barcap" id="tl-barcap">Electoral Votes</div>
  <div class="ev-wrap" id="tl-evwrap"></div>
  <div class="thresh" id="tl-thresh">—</div>
  <div class="pv"><span class="m" id="pvm">Michael</span><span>Popular Vote</span><span class="s" id="pvs">Sarah</span></div>
  <div class="pvbar"><div id="pvm-bar" style="background:linear-gradient(90deg,#221e8f,#3d37d4);height:100%;transition:width .4s ease;"></div><div id="pvs-bar" style="background:linear-gradient(90deg,#c2006f,#8a005c);height:100%;transition:width .4s ease;"></div></div>

  <div class="cards">
    <div class="card c0"><div class="n">Michael</div><div class="v" id="ev0">0</div><div class="l" id="lbl0"></div><div class="p" id="pct0"></div><div class="st" id="st0"></div></div>
    <div class="card c1"><div class="n">Sarah</div><div class="v" id="ev1">0</div><div class="l" id="lbl1"></div><div class="p" id="pct1"></div><div class="st" id="st1"></div></div>
    <div class="card c2"><div class="n">Tied</div><div class="v" id="ev2">0</div><div class="l" id="lbl2"></div><div class="p" id="pct2"></div><div class="st" id="st2"></div></div>
    <div class="card c3"><div class="n">Not Played</div><div class="v" id="ev3">0</div><div class="l" id="lbl3"></div><div class="p" id="pct3"></div><div class="st" id="st3"></div></div>
  </div>

  <div id="map"></div>

  <div class="legend">
    <span><span class="sw" style="background:#221e8f"></span>Michael</span>
    <span><span class="sw" style="background:#8a005c"></span>Sarah</span>
    <span><span class="sw" style="background:#a09587"></span>Tied</span>
    <span><span class="sw" style="background:#ddd9d4;border-color:#c8c3bc"></span>Not played</span>
  </div>
  <div class="legend legend-sub">
    <span><span class="sw" style="background:#cbc6be"></span>Faded &mdash; still changing hands</span>
    <span><span class="sw" style="background:#5c5952"></span>Solid &mdash; settled, never flips again</span>
  </div>

  <div class="tl-foot">
    <div class="tl-head">
      <span><b id="tl-date">—</b></span>
      <span id="tl-frame">—</span>
    </div>
    <div class="ctl">
      <button id="tl-play">⏸ Pause</button>
      <button id="tl-restart">↺ Restart</button>
      <input type="range" id="tl-scrub" min="0" value="0" step="1">
    </div>
  </div>
</div>

<script>__PLOTLY_JS__</script>
<script>
const D = __DATA__;
const F = D.frames, N = F.length, C = D.colors;
const VL = D.vote_label, IS_TG = D.is_tg;

function scale(colors){
  const n = colors.length, s = [];
  for (let k = 0; k < n; k++){ s.push([k/n, colors[k]]); s.push([(k+1)/n, colors[k]]); }
  return s;
}
const WHO  = ['Michael','Michael','Sarah','Sarah','Tied','Tied','Not yet played'];
const SAFE = c => (c === 1 || c === 3 || c === 5);

function hoverText(f){
  return f.codes.map((c,i) => {
    const tag = SAFE(c) ? ' · settled' : (c === 6 ? '' : ' · still changing');
    return '<b>' + f.names[i] + '</b><br>' + VL + ': ' + f.labels[i] + '<br>' + WHO[c] + tag;
  });
}
function labelColors(f){
  return f.codes.map(c => SAFE(c) ? '#ffffff' : '#5a5651');
}

const choro = {
  type:'choropleth', locationmode:'USA-states', locations: D.abbrevs,
  z: F[0].codes, zmin:-0.5, zmax: C.length - 0.5,
  colorscale: scale(C), showscale:false, autocolorscale:false,
  marker:{ line:{ color:'white', width:1.4 } },
  text: hoverText(F[0]), hoverinfo:'text'
};
const labels = {
  type:'scattergeo', lat: D.lats, lon: D.lons, mode:'text',
  text: F[0].labels, textfont:{ size:8.5, color: labelColors(F[0]), family:'Arial Black' },
  hoverinfo:'skip'
};
const layout = {
  geo:{ scope:'usa', projection:{ type:'albers usa' }, showframe:false, showcoastlines:false,
        showland:true, landcolor:'#f0ede8', showlakes:true, lakecolor:'#dde8f0', bgcolor:'rgba(0,0,0,0)' },
  paper_bgcolor:'rgba(0,0,0,0)', margin:{ t:0,b:0,l:0,r:0 }, dragmode:false,
  hoverlabel:{ bgcolor:'white', bordercolor:'#d9d7cc' }, uirevision:'tl'
};

Plotly.newPlot('map', [choro, labels], layout,
  {displayModeBar:false, responsive:true, scrollZoom:false, doubleClick:false, editable:false});

const $ = id => document.getElementById(id);
const fmt = n => n.toLocaleString('en-US');

// Scoreboard / EV-bar colours are always the solid palette (michael, sarah, tied, third).
const BAR = ['#221e8f', '#8a005c', '#a09587', '#ddd9d4'];
$('tl-barcap').textContent = VL;

// Scrubber track (hard-edged, no blend): a near-grey tinted toward whoever
// currently leads the electoral college, and their full solid colour across any
// stretch where they've actually clinched it.
const _GREY = [217, 215, 204], _MICH = [34, 30, 143], _SAR = [138, 0, 92];
function _tint(base, target, t){
  return 'rgb(' + base.map((v, i) => Math.round(v + (target[i] - v) * t)).join(',') + ')';
}
function segColor(f){
  if (f.ev[0] >= f.threshold) return '#221e8f';
  if (f.ev[1] >= f.threshold) return '#8a005c';
  if (f.ev[0] > f.ev[1]) return _tint(_GREY, _MICH, 0.16);
  if (f.ev[1] > f.ev[0]) return _tint(_GREY, _SAR,  0.16);
  return 'rgb(217,215,204)';
}
(function(){
  const stops = [];
  for (let i = 0; i < N; i++){
    const c = segColor(F[i]);
    stops.push(c + ' ' + (i / N * 100).toFixed(2) + '%',
               c + ' ' + ((i + 1) / N * 100).toFixed(2) + '%');
  }
  $('tl-scrub').style.setProperty('--tl-grad', 'linear-gradient(to right, ' + stops.join(', ') + ')');
})();

function paintHud(f, k){
  $('tl-date').textContent = '⏳ ' + f.date;
  $('tl-frame').textContent = 'Round ' + fmt(f.round) + ' · ' + (k+1) + ' / ' + N;
  $('tl-scrub').value = k;
  $('tl-scrub').style.setProperty('--tl-pos', (k / (N - 1) * 100).toFixed(2) + '%');

  const tot = f.total || 1;
  const seg = [[f.ev[0],BAR[0]],[f.ev[2],BAR[2]],[f.ev[3],BAR[3]],[f.ev[1],BAR[1]]];
  $('tl-evwrap').innerHTML = seg.filter(s=>s[0]>0)
     .map(s => '<div style="width:'+(s[0]/tot*100).toFixed(2)+'%;background:'+s[1]+'"></div>').join('');
  $('tl-thresh').textContent = fmt(f.threshold) + ' ' + VL.toLowerCase() + ' to win · ' + fmt(f.total) + ' total';

  for (let j=0;j<4;j++){
    $('ev'+j).textContent = fmt(f.ev[j]);
    $('lbl'+j).textContent = VL;
    $('pct'+j).textContent = (f.ev[j]/tot*100).toFixed(1) + '%';
    const ns = f.nstates ? f.nstates[j] : 0;
    $('st'+j).textContent = ns + (ns === 1 ? ' state' : ' states');
  }
  const pm = f.pv[0], ps = f.pv[1], pt = (pm+ps)||1;
  const pw = pm > ps ? 'm' : (ps > pm ? 's' : '');
  $('pvm').innerHTML = (pw === 'm' ? '▶ ' : '') + 'Michael <b>' + fmt(pm) +
                       '</b><i> pts (' + (pm/pt*100).toFixed(1) + '%)</i>';
  $('pvs').innerHTML = '<b>' + fmt(ps) + '</b><i> pts (' + (ps/pt*100).toFixed(1) + '%)</i> ' +
                       (pw === 's' ? '◀ ' : '') + 'Sarah';
  $('pvm-bar').style.width = (pm/pt*100).toFixed(2) + '%';
  $('pvs-bar').style.width = (ps/pt*100).toFixed(2) + '%';
}

let i = 0, playing = true, timer = null;

function render(k){
  i = k;
  const f = F[k];
  Plotly.restyle('map', { z:[f.codes], text:[hoverText(f)] }, [0]);
  Plotly.restyle('map', { text:[f.labels], 'textfont.color':[labelColors(f)] }, [1]);
  paintHud(f, k);
}
function tick(){
  if (!playing) return;
  if (i >= N-1){ playing = false; syncBtn(); return; }
  render(i+1);
  timer = setTimeout(tick, D.frame_ms);
}
function syncBtn(){ $('tl-play').textContent = playing ? '⏸ Pause' : '▶ Play'; }

$('tl-play').onclick = () => {
  playing = !playing;
  if (playing){ if (i >= N-1) i = 0; render(i); tick(); }
  syncBtn();
};
$('tl-restart').onclick = () => { playing = true; render(0); syncBtn(); clearTimeout(timer); tick(); };
$('tl-scrub').max = N-1;
$('tl-scrub').oninput = e => { playing = false; clearTimeout(timer); syncBtn(); render(+e.target.value); };

render(0);
tick();
</script>
"""
    # Inject data first (small, trusted template), then the Plotly bundle last
    # so nothing inside the bundle can collide with a placeholder.
    html = html.replace("__DATA__", data_json).replace("__PLOTLY_JS__", plotly_js)
    components.html(html, height=940, scrolling=False)

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
_HR = '<hr style="border:none;border-top:1px solid #d9d7cc;margin:1px 24px 12px 24px;">'

with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>Settings</h2>", unsafe_allow_html=True)

    college_mode = st.session_state.get('ec_mode', 'Electoral College')
    _mc1, _mc2 = st.columns(2)
    with _mc1:
        if st.button("Electoral", key="ec_btn_ec", use_container_width=True,
                     type="primary" if college_mode == "Electoral College" else "secondary"):
            st.session_state['ec_mode'] = 'Electoral College'
            st.rerun()
    with _mc2:
        if st.button("TimeGuessr", key="ec_btn_tg", use_container_width=True,
                     type="primary" if college_mode == "TimeGuessr College" else "secondary"):
            st.session_state['ec_mode'] = 'TimeGuessr College'
            st.rerun()

    st.markdown(_HR, unsafe_allow_html=True)

    score_mode = st.session_state.get('ec_score', 'Total Score')
    _sc1, _sc2, _sc3 = st.columns(3)
    with _sc1:
        if st.button("Total", key="ec_btn_total", use_container_width=True,
                     type="primary" if score_mode == "Total Score" else "secondary"):
            st.session_state['ec_score'] = 'Total Score'
            st.rerun()
    with _sc2:
        if st.button("Geo", key="ec_btn_geo", use_container_width=True,
                     type="primary" if score_mode == "Geography Score" else "secondary"):
            st.session_state['ec_score'] = 'Geography Score'
            st.rerun()
    with _sc3:
        if st.button("Time", key="ec_btn_time", use_container_width=True,
                     type="primary" if score_mode == "Time Score" else "secondary"):
            st.session_state['ec_score'] = 'Time Score'
            st.rerun()

stats_mtime = os.path.getmtime("./Data/Timeguessr_Stats.csv") if os.path.exists("./Data/Timeguessr_Stats.csv") else 0
data = load_data(stats_mtime)
filtered_data = data.copy()

# ──────────────────────────────────────────────────────────────────────────────
# Compute snapshot results
# ──────────────────────────────────────────────────────────────────────────────
state_results = calculate_state_results(filtered_data, score_mode)

all_states_df = pd.DataFrame({
    'State': list(ELECTORAL_VOTES.keys()),
    'EV':    list(ELECTORAL_VOTES.values()),
})
state_results = all_states_df.merge(state_results, on='State', how='left')
state_results['Winner'] = state_results['Winner'].fillna('third')
for col in ['Michael_Score', 'Sarah_Score', 'Michael_Rounds', 'Sarah_Rounds', 'Total_Rounds']:
    state_results[col] = state_results[col].fillna(0)

state_results['abbrev']       = state_results['State'].map(STATE_ABBREV)
state_results['color']        = state_results['Winner'].map(WIN_COLORS)
state_results['winner_label'] = state_results['Winner'].map(WIN_LABELS)

is_tg_college = (college_mode == "TimeGuessr College")
if is_tg_college:
    state_results['Votes'] = ((state_results['Michael_Rounds'] + state_results['Sarah_Rounds']).astype(int)) / 2 + 2
    vote_label   = "Rounds"
    vote_label_s = "rounds"
    mode_emoji   = "⏱️"
    mode_title   = "TimeGuessr College"
else:
    state_results['Votes'] = state_results['EV'].astype(int)
    vote_label   = "Electoral Votes"
    vote_label_s = "electoral votes"
    mode_emoji   = "🗳️"
    mode_title   = "Electoral College"

TOTAL_VOTES = int(state_results['Votes'].sum())
ev = {k: int(state_results.loc[state_results['Winner'] == k, 'Votes'].sum()) for k in WIN_COLORS}
threshold    = TOTAL_VOTES // 2 + 1
overall_winner = ('michael' if ev['michael'] >= threshold
                  else 'sarah' if ev['sarah'] >= threshold
                  else None)

# ──────────────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(f"## {mode_emoji} {mode_title}")
score_mode_label = {"Total Score": "total score", "Geography Score": "geography score", "Time Score": "time score"}[score_mode]
st.markdown(
    f'<p style="color:#696761;font-size:0.87rem;margin-top:-0.4rem;margin-bottom:0.8rem;">'
    f'All-time {score_mode_label} decides each state · Winner-take-all · '
    f'Tied states award no votes · Unplayed states award no votes · {threshold:,} to win</p>',
    unsafe_allow_html=True
)

# ──────────────────────────────────────────────────────────────────────────────
# Timelapse controls
# ──────────────────────────────────────────────────────────────────────────────
df_json = filtered_data.to_json(orient='split', date_format='iso')
frames = build_timelapse_frames(df_json, score_mode, is_tg_college)

_tl_on = st.session_state.get('ec_timelapse', False)
with st.sidebar:
    st.markdown(_HR, unsafe_allow_html=True)
    _tc1, _tc2 = st.columns(2)
    with _tc1:
        if st.button("Static", key="ec_btn_static", use_container_width=True,
                     type="primary" if not _tl_on else "secondary"):
            st.session_state['ec_timelapse'] = False
            st.rerun()
    with _tc2:
        if st.button("Timelapse", key="ec_btn_timelapse", use_container_width=True,
                     type="primary" if _tl_on else "secondary",
                     disabled=len(frames) < 2):
            st.session_state['ec_timelapse'] = True
            st.rerun()
tl_active = _tl_on

# ──────────────────────────────────────────────────────────────────────────────
# Timelapse playback — a self-contained client-side player. Nothing on the
# Streamlit side reruns while it plays, and each frame only recolors the states
# that changed hands, so the map no longer blinks.
# ──────────────────────────────────────────────────────────────────────────────
if tl_active and len(frames) >= 2:
    render_timelapse_player(build_timelapse_payload(frames, is_tg_college))
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Live view (up to date)
# ──────────────────────────────────────────────────────────────────────────────
ev, TOTAL_VOTES, threshold, overall_winner = render_ev_scoreboard(
    state_results, is_tg_college, vote_label, vote_label_s, show_popular=True
)
st.plotly_chart(build_ev_map(state_results, is_tg_college),
                use_container_width=True, key="ec_map")
render_ev_legend(vote_label_s)

# ──────────────────────────────────────────────────────────────────────────────
# EV Timeline
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-header">{vote_label} Over Time</div>', unsafe_allow_html=True)

# Serialize filtered_data → JSON for cache-safe passing
df_json = filtered_data.to_json(orient='split', date_format='iso')
timeline = calculate_ev_timeline(df_json, score_mode, is_tg_college)

if not timeline.empty and len(timeline) > 1:

    # ── Build month-based tick labels mapped to round positions ──────────────
    tl = timeline.copy()
    tl['round_num'] = pd.to_numeric(tl['round_num'], errors='coerce').fillna(0).astype(int)
    tl['Date'] = pd.to_datetime(tl['Date'])

    monthly_dates = pd.date_range(tl['Date'].min(), tl['Date'].max(), freq='MS')
    if len(tl) > 1 and len(monthly_dates) > 0:
        tick_rounds = np.interp(
            [d.timestamp() for d in monthly_dates],
            [d.timestamp() for d in tl['Date']],
            tl['round_num'].astype(float)
        ).astype(int)
        tick_labels = [d.strftime('%b %Y') for d in monthly_dates]
    else:
        tick_rounds = tl['round_num'].tolist()
        tick_labels = tl['Date'].dt.strftime('%b %Y').tolist()

    fig_tl = go.Figure()

    fig_tl.add_trace(go.Scatter(
        x=tl['round_num'], y=tl['michael'],
        customdata=tl['Date'],
        mode='lines',
        line=dict(color=COLORS['michael'], width=2.5, shape='hv'),
        fill='tozeroy', fillcolor='rgba(34,30,143,0.10)',
        name='Michael',
        hovertemplate='<b>Michael</b>: %{y:,}<br>Round %{x:,} · %{customdata|%b %d, %Y}<extra></extra>',
    ))

    fig_tl.add_trace(go.Scatter(
        x=tl['round_num'], y=tl['sarah'],
        customdata=tl['Date'],
        mode='lines',
        line=dict(color=COLORS['sarah'], width=2.5, shape='hv'),
        fill='tozeroy', fillcolor='rgba(138,0,92,0.10)',
        name='Sarah',
        hovertemplate='<b>Sarah</b>: %{y:,}<br>Round %{x:,} · %{customdata|%b %d, %Y}<extra></extra>',
    ))

    fig_tl.add_trace(go.Scatter(
        x=tl['round_num'], y=tl['tied'],
        customdata=tl['Date'],
        mode='lines',
        line=dict(color='#a09587', width=1.8, shape='hv'),
        name='Tied',
        hovertemplate='<b>Tied</b>: %{y:,}<br>Round %{x:,} · %{customdata|%b %d, %Y}<extra></extra>',
    ))

    fig_tl.add_trace(go.Scatter(
        x=tl['round_num'], y=tl['third'],
        customdata=tl['Date'],
        mode='lines',
        line=dict(color='#a49d92', width=1.8, shape='hv', dash='dot'),
        name='Not Played',
        hovertemplate='<b>Not Played</b>: %{y:,}<br>Round %{x:,} · %{customdata|%b %d, %Y}<extra></extra>',
    ))

    # Threshold line
    if is_tg_college and 'threshold' in tl.columns:
        fig_tl.add_trace(go.Scatter(
            x=tl['round_num'], y=pd.to_numeric(tl['threshold']),
            customdata=tl['Date'],
            mode='lines',
            line=dict(color='#696761', width=1.5, dash='dot', shape='hv'),
            name='Threshold',
            hovertemplate='<b>Threshold</b>: %{y:,}<br>Round %{x:,} · %{customdata|%b %d, %Y}<extra></extra>',
        ))
        fig_tl.add_annotation(
            x=int(tl['round_num'].iloc[-1]), y=float(pd.to_numeric(tl['threshold']).iloc[-1]),
            text=f"  {int(pd.to_numeric(tl['threshold']).iloc[-1]):,} to win",
            showarrow=False, font=dict(color='#696761', size=11, family='Arial'),
            xanchor='left', yanchor='middle',
        )
    else:
        fig_tl.add_hline(
            y=270, line_dash='dot', line_color='#696761', line_width=1.5,
            annotation_text='270 to win', annotation_position='right',
            annotation_font_color='#696761', annotation_font_size=11,
        )

    last_row = tl.iloc[-1]
    for player, col, yshift in [('michael', COLORS['michael'], 8), ('sarah', COLORS['sarah'], -14),
                                ('tied', '#8f8579', 0), ('third', '#9c968c', 0)]:
        fig_tl.add_annotation(
            x=int(last_row['round_num']), y=float(last_row[player]),
            text=f"  {int(last_row[player]):,}",
            showarrow=False, font=dict(color=col, size=11, family='Arial'),
            xanchor='left', yanchor='middle', yshift=yshift,
        )

    # Flip lines — now at round_num instead of timestamp
    lead = (tl['michael'] > tl['sarah']).map({True: 'michael', False: 'sarah'})
    prev_lead = lead.shift(1, fill_value=lead.iloc[0])
    flips = tl[(lead != prev_lead) & (tl.index > 0)]
    for _, flip_row in flips.iterrows():
        new_leader = 'michael' if flip_row['michael'] > flip_row['sarah'] else 'sarah'
        fig_tl.add_vline(
            x=int(flip_row['round_num']),
            line_dash='dash', line_color=WIN_COLORS[new_leader],
            line_width=1, opacity=0.45,
        )

    fig_tl.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=40, l=70, r=80), height=320,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0, font=dict(size=12)),
        xaxis=dict(
            tickvals=tick_rounds, ticktext=tick_labels,
            showgrid=False, showline=True, linecolor='#d9d7cc',
            tickfont=dict(color='#696761', size=11), title=None, automargin=False,
            range=[int(tl['round_num'].iloc[0]), int(tl['round_num'].iloc[-1])],
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#ede9e4', gridwidth=1, showline=False,
            tickfont=dict(color='#696761', size=11), automargin=False,
            title=dict(text=vote_label, font=dict(color='#696761', size=11)),
            rangemode='tozero',
        ),
        hoverlabel=dict(bgcolor='white', font_size=12, bordercolor='#d9d7cc'),
        hovermode='x unified',
    )

    st.plotly_chart(fig_tl, use_container_width=True)

    # ── Control bars ────────────────────────────────────────────────────────
    # Two static echoes of the timelapse scrubber track — hard-edged strips
    # under the chart, aligned to its data area by matching the fixed pixel
    # margins (l=70, r=80). Top strip: who held the electoral college (solid
    # team colour = clinched, near-grey tint = merely leading). Bottom strip:
    # who controlled more states, always in solid colour.
    _GREY, _MICH, _SAR = (217, 215, 204), (34, 30, 143), (138, 0, 92)

    def _tint(base, target, t):
        return "rgb(%d,%d,%d)" % tuple(round(b + (tg - b) * t) for b, tg in zip(base, target))

    def _ev_color(r):
        m, s = float(r['michael']), float(r['sarah'])
        thr = float(pd.to_numeric(r['threshold']))
        if m >= thr:  return '#221e8f'
        if s >= thr:  return '#8a005c'
        if m > s:     return _tint(_GREY, _MICH, 0.16)
        if s > m:     return _tint(_GREY, _SAR, 0.16)
        return 'rgb(217,215,204)'

    def _states_color(r):
        m, s = int(float(r['m_states'])), int(float(r['s_states']))
        if m > s:  return '#221e8f'
        if s > m:  return '#8a005c'
        return '#a09587'

    _rows = tl.reset_index(drop=True)
    _x0 = int(_rows['round_num'].iloc[0])
    _x1 = int(_rows['round_num'].iloc[-1])
    _span = max(_x1 - _x0, 1)
    _MIN_LAST = 1.6  # guarantee the final (ongoing) state a visible sliver

    def _gradient(color_fn):
        segs = []
        for _i in range(len(_rows)):
            c = color_fn(_rows.iloc[_i])
            if segs and segs[-1][0] == c:
                continue
            segs.append([c, (int(_rows['round_num'].iloc[_i]) - _x0) / _span * 100])
        if len(segs) >= 2 and segs[-1][1] > 100 - _MIN_LAST:
            segs[-1][1] = 100 - _MIN_LAST
        stops = []
        for k, (c, p0) in enumerate(segs):
            p1 = segs[k + 1][1] if k + 1 < len(segs) else 100.0
            stops += [f"{c} {p0:.2f}%", f"{c} {p1:.2f}%"]
        return "linear-gradient(to right, " + ", ".join(stops) + ")"

    _grad_ev = _gradient(_ev_color)
    _grad_st = _gradient(_states_color)
    _bar = ('height:12px;border-radius:6px;'
            'box-shadow:inset 0 1px 3px rgba(0,0,0,0.28);')
    st.markdown(
        f'<div style="margin:-0.35rem 80px 0 70px;">'
        f'<div style="{_bar}background:{_grad_ev};"></div>'
        f'<div style="{_bar}background:{_grad_st};margin-top:4px;"></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:#9c9790;font-size:0.71rem;text-align:center;margin-top:0.35rem;">'
        f'X-axis spacing proportional to rounds played · tick labels show calendar month · '
        f'dashed lines mark lead changes · top bar: who held the electoral college '
        f'(solid = clinched, faint = leading) · bottom bar: who controlled more states</p>',
        unsafe_allow_html=True
    )

    # ── Time in office ──────────────────────────────────────────────────────
    # Per span between timeline points: whoever had clinched the EC is
    # "president"; if neither had, whoever controls more states is "interim";
    # if neither clinched and the state counts are level, there's no president.
    _office = {'m': 0, 's': 0, 'mi': 0, 'si': 0, 'none': 0}
    for i in range(len(tl) - 1):
        span = int(tl.loc[i + 1, 'round_num']) - int(tl.loc[i, 'round_num'])
        thresh = float(pd.to_numeric(tl.loc[i, 'threshold']))
        m, s = float(tl.loc[i, 'michael']), float(tl.loc[i, 'sarah'])
        mst, sst = int(float(tl.loc[i, 'm_states'])), int(float(tl.loc[i, 's_states']))
        if m >= thresh:
            _office['m'] += span
        elif s >= thresh:
            _office['s'] += span
        elif mst > sst:
            _office['mi'] += span
        elif sst > mst:
            _office['si'] += span
        else:
            _office['none'] += span

    _tot_office = sum(_office.values()) or 1

    def _oi(key, label, color, weight=600):
        d = _office[key]
        return (f'<span style="color:{color};font-weight:{weight};">'
                f'{label} {d:,} days ({d / _tot_office * 100:.1f}%)</span>')

    _dot = '<span style="color:#c8c3bc;">·</span>'
    st.markdown(
        '<div style="display:flex;flex-wrap:wrap;gap:0.9rem;margin:0.5rem 0 0.4rem 0;font-size:0.82rem;">'
        '<span style="color:#696761;font-weight:600;">Time in office:</span>'
        + _oi('m',  'Michael',          COLORS['michael']) + _dot
        + _oi('mi', 'Interim Michael',  COLORS['michael'], 400) + _dot
        + _oi('si', 'Interim Sarah',    COLORS['sarah'], 400) + _dot
        + _oi('s',  'Sarah',            COLORS['sarah']) + _dot
        + _oi('none', 'No president',   '#a09587', 400)
        + '</div>',
        unsafe_allow_html=True,
    )

else:
    st.info("Not enough data points to render a timeline.")

# ──────────────────────────────────────────────────────────────────────────────
# State Results Table
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">State Results</div>', unsafe_allow_html=True)

tc1, tc2 = st.columns([2, 2])
with tc1:
    filter_winner = st.selectbox(
        "Filter by outcome",
        ["All", "Michael", "Sarah", "Tied", "Not Played"],
    )
with tc2:
    sort_opts = [f"{vote_label} ↓", "State Name", "Michael Score ↓", "Sarah Score ↓", "Score Difference ↓"]
    sort_by = st.selectbox("Sort by", sort_opts)

disp = state_results.copy()
w_map = {"Michael": "michael", "Sarah": "sarah", "Tied": "tied", "Not Played": "third"}
if filter_winner != "All":
    disp = disp[disp['Winner'] == w_map[filter_winner]]

if sort_by == "State Name":
    disp = disp.sort_values("State")
elif sort_by == "Michael Score ↓":
    disp = disp.sort_values("Michael_Score", ascending=False)
elif sort_by == "Sarah Score ↓":
    disp = disp.sort_values("Sarah_Score", ascending=False)
elif sort_by == "Score Difference ↓":
    disp['_diff'] = (disp['Michael_Score'] - disp['Sarah_Score']).abs()
    disp = disp.sort_values("_diff", ascending=False)
else:
    disp = disp.sort_values("Votes", ascending=False)

score_label = {"Total Score": "pts", "Geography Score": "geo pts", "Time Score": "time pts"}[score_mode]

badge_html = {
    'michael': '<span class="badge badge-michael">Michael</span>',
    'sarah':   '<span class="badge badge-sarah">Sarah</span>',
    'tied':    '<span class="badge badge-tied">Tied</span>',
    'third':   '<span class="badge badge-third">Not Played</span>',
}

rows_html = ""
for _, row in disp.iterrows():
    mr, sr     = int(row['Michael_Rounds']), int(row['Sarah_Rounds'])
    ms, ss     = int(row['Michael_Score']),  int(row['Sarah_Score'])
    votes_disp = int(row['Votes'])

    m_str = (f"{ms:,}&nbsp;<span style='font-size:0.71rem;opacity:0.65;'>({mr}r)</span>"
             if mr > 0 else "—")
    s_str = (f"{ss:,}&nbsp;<span style='font-size:0.71rem;opacity:0.65;'>({sr}r)</span>"
             if sr > 0 else "—")

    if mr > 0 and sr > 0:
        diff = ms - ss
        if diff > 0:
            diff_str = f'<span style="color:{COLORS["michael"]};font-weight:600;">+{diff:,}</span>'
        elif diff < 0:
            diff_str = f'<span style="color:{COLORS["sarah"]};font-weight:600;">+{abs(diff):,}</span>'
        else:
            diff_str = '<span style="color:#a09587;">0</span>'
    else:
        diff_str = "—"

    rows_html += f"""
    <tr>
      <td><b>{row['State']}</b></td>
      <td style="text-align:center;font-weight:700;">{votes_disp:,}</td>
      <td style="text-align:center;">{badge_html[row['Winner']]}</td>
      <td style="color:{COLORS['michael']};text-align:right;">{m_str}</td>
      <td style="color:{COLORS['sarah']};text-align:right;">{s_str}</td>
      <td style="text-align:center;">{diff_str}</td>
    </tr>"""

st.markdown(
    f"""
    <table class="state-table">
      <thead><tr>
        <th>State</th>
        <th class="center">{vote_label}</th>
        <th class="center">Winner</th>
        <th class="right" style="color:{COLORS['michael']};">Michael ({score_label})</th>
        <th class="right" style="color:{COLORS['sarah']};">Sarah ({score_label})</th>
        <th class="center">Difference</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    """,
    unsafe_allow_html=True,
)

if is_tg_college:
    footnote = f"TimeGuessr College · votes = rounds played per state · {TOTAL_VOTES:,} total rounds · {threshold:,} needed to win"
else:
    footnote = f"2024 apportionment · 538 total electoral votes · 270 needed to win · Tied states award no electoral votes"

st.markdown(
    f"<div style='margin-top:1.5rem;color:#b0a89e;font-size:0.72rem;text-align:center;'>{footnote}</div>",
    unsafe_allow_html=True,
)