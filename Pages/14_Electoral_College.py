import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# ──────────────────────────────────────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Electoral College")

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
try:
    with open("styles.css") as f: st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError: pass

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
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Data Loading
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
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
    df = pd.read_json(df_json, orient='split')
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

    # Group by date — process all rounds that happened on the same day together
    for date, group in us_df.groupby('Date', sort=True):
        changed_states = set()
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
        if current_ev != prev_ev:
            rows.append({'Date': date, **current_ev})
            prev_ev = current_ev.copy()

    if not rows:
        return pd.DataFrame(columns=['Date', 'michael', 'sarah', 'tied', 'third'])

    timeline = pd.DataFrame(rows)
    # Duplicate last point to today so line extends to right edge
    last = timeline.iloc[-1].copy()
    last['Date'] = pd.Timestamp.now().normalize()
    if last['Date'] > timeline['Date'].iloc[-1]:
        timeline = pd.concat([timeline, last.to_frame().T], ignore_index=True)

    return timeline

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Electoral Settings")
    college_mode = st.radio(
        "Mode:",
        ["Electoral College", "TimeGuessr College"],
        index=0,
    )
    score_mode = st.radio(
        "Score Type:",
        ["Total Score", "Geography Score", "Time Score"],
        index=0,
    )
    if "Date" in load_data().columns:
        raw = load_data()
        min_d = raw[raw['Country'].notna()]["Date"].min().date()
        max_d = raw["Date"].max().date()
        sel_dates = st.slider("Date Range:", min_d, max_d, (min_d, max_d), format="MM/DD/YY")
    else:
        sel_dates = None

data = load_data()
if sel_dates:
    filtered_data = data[
        (data["Date"].dt.date >= sel_dates[0]) &
        (data["Date"].dt.date <= sel_dates[1])
    ].copy()
else:
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
threshold_desc = (f"{threshold:,} {vote_label_s} needed to win · {TOTAL_VOTES:,} total"
                  if is_tg_college else
                  f"270 electoral votes needed to win · {TOTAL_VOTES:,} total")
st.markdown(
    f'<p style="color:#696761;font-size:0.87rem;margin-top:-0.4rem;margin-bottom:0.8rem;">'
    f'All-time {score_mode_label} decides each state · Winner-take-all · '
    f'Tied states award no votes · Unplayed states award no votes · {threshold:,} to win</p>',
    unsafe_allow_html=True
)

# ── EV progress bar ───────────────────────────────────────────────────────────
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
st.markdown(f'<div class="ev-bar-wrap">{bar_inner}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="threshold-note">{threshold_desc}</div>', unsafe_allow_html=True)

# ── Popular vote bar ──────────────────────────────────────────────────────────
pv_michael = int(state_results['Michael_Score'].sum())
pv_sarah   = int(state_results['Sarah_Score'].sum())
pv_total   = pv_michael + pv_sarah

if pv_total > 0:
    pv_m_pct = pv_michael / pv_total * 100
    pv_s_pct = pv_sarah   / pv_total * 100
    pv_winner = 'michael' if pv_michael > pv_sarah else ('sarah' if pv_sarah > pv_michael else None)

    st.markdown(f"""
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
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)

# ── Score cards ───────────────────────────────────────────────────────────────
def winner_badge(player):
    return '<div class="win-badge">&#127942; WINNER</div>' if overall_winner == player else ''

m_pct  = ev['michael'] / bar_total * 100
s_pct  = ev['sarah']   / bar_total * 100
ti_pct = ev['tied']    / bar_total * 100
th_pct = ev['third']   / bar_total * 100

st.markdown(f"""
<div class="ec-scoreboard">
  <div class="ec-card card-michael">
    <div class="card-name">Michael</div>
    <div class="card-ev">{ev['michael']:,}</div>
    <div class="card-label">{vote_label}</div>
    <div class="card-pct">{m_pct:.1f}%</div>
    {winner_badge('michael')}
  </div>
  <div class="ec-card card-sarah">
    <div class="card-name">Sarah</div>
    <div class="card-ev">{ev['sarah']:,}</div>
    <div class="card-label">{vote_label}</div>
    <div class="card-pct">{s_pct:.1f}%</div>
    {winner_badge('sarah')}
  </div>
  <div class="ec-card card-tied">
    <div class="card-name">Tied</div>
    <div class="card-ev">{ev['tied']:,}</div>
    <div class="card-label">{vote_label}</div>
    <div class="card-pct">{ti_pct:.1f}%</div>
  </div>
  <div class="ec-card card-third">
    <div class="card-name">Not Played</div>
    <div class="card-ev">{ev['third']:,}</div>
    <div class="card-label">{vote_label}</div>
    <div class="card-pct">{th_pct:.1f}%</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Map
# ──────────────────────────────────────────────────────────────────────────────
fig = go.Figure()

for winner_key, color in WIN_COLORS.items():
    subset = state_results[state_results['Winner'] == winner_key]
    if subset.empty:
        continue

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
        locations=subset['abbrev'],
        z=[1] * len(subset),
        locationmode='USA-states',
        colorscale=[[0, color], [1, color]],
        zmin=0, zmax=1,
        showscale=False,
        marker_line_color='white',
        marker_line_width=1.8,
        hovertemplate=hover_texts,
        name=WIN_LABELS[winner_key],
        showlegend=False,
    ))

lats, lons, labels = [], [], []
for _, row in state_results.iterrows():
    abbr = row['abbrev']
    if abbr and abbr in STATE_CENTROIDS:
        lat, lon = STATE_CENTROIDS[abbr]
        lats.append(lat)
        lons.append(lon)
        labels.append(str(int(row['Votes'])))

fig.add_trace(go.Scattergeo(
    lat=lats, lon=lons,
    mode='text',
    text=labels,
    textfont=dict(size=8.5, color='white', family='Arial Bold'),
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
)

st.plotly_chart(fig, use_container_width=True)

# ── Legend ────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# EV Timeline
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-header">{vote_label} Over Time</div>', unsafe_allow_html=True)

# Serialize filtered_data → JSON for cache-safe passing
df_json = filtered_data.to_json(orient='split', date_format='iso')
timeline = calculate_ev_timeline(df_json, score_mode, is_tg_college)

if not timeline.empty and len(timeline) > 1:
    # Compute threshold line — for TG mode it changes over time, so just use
    # the current snapshot threshold for simplicity (a horizontal reference line)
    tl_threshold = 270 if not is_tg_college else threshold

    fig_tl = go.Figure()

    # Shaded fill under Michael's line
    fig_tl.add_trace(go.Scatter(
        x=timeline['Date'], y=timeline['michael'],
        mode='lines',
        line=dict(color=COLORS['michael'], width=2.5),
        fill='tozeroy',
        fillcolor='rgba(34,30,143,0.10)',
        name='Michael',
        hovertemplate='<b>Michael</b>: %{y:,}<br>%{x|%b %d, %Y}<extra></extra>',
    ))

    # Shaded fill under Sarah's line (drawn on top, different fill direction)
    fig_tl.add_trace(go.Scatter(
        x=timeline['Date'], y=timeline['sarah'],
        mode='lines',
        line=dict(color=COLORS['sarah'], width=2.5),
        fill='tozeroy',
        fillcolor='rgba(138,0,92,0.10)',
        name='Sarah',
        hovertemplate='<b>Sarah</b>: %{y:,}<br>%{x|%b %d, %Y}<extra></extra>',
    ))

    # Threshold line
    fig_tl.add_hline(
        y=tl_threshold,
        line_dash='dot',
        line_color='#696761',
        line_width=1.5,
        annotation_text=f'{tl_threshold:,} to win',
        annotation_position='right',
        annotation_font_color='#696761',
        annotation_font_size=11,
    )

    # Annotate final values
    last_row = timeline.iloc[-1]
    for player, col, yshift in [('michael', COLORS['michael'], 8), ('sarah', COLORS['sarah'], -14)]:
        fig_tl.add_annotation(
            x=last_row['Date'],
            y=last_row[player],
            text=f"  {int(last_row[player]):,}",
            showarrow=False,
            font=dict(color=col, size=11, family='Arial'),
            xanchor='left',
            yanchor='middle',
            yshift=yshift,
        )

    # Detect flip events — dates where the leading player changed
    lead = (timeline['michael'] > timeline['sarah']).map({True: 'michael', False: 'sarah'})
    # Pad with a sentinel so we catch the first real lead
    prev_lead = lead.shift(1, fill_value=lead.iloc[0])
    flip_mask = lead != prev_lead
    flips = timeline[flip_mask & (timeline.index > 0)]

    for _, flip_row in flips.iterrows():
        new_leader = 'michael' if flip_row['michael'] > flip_row['sarah'] else 'sarah'
        fig_tl.add_vline(
            x=flip_row['Date'].timestamp() * 1000,
            line_dash='dash',
            line_color=WIN_COLORS[new_leader],
            line_width=1,
            opacity=0.45,
        )

    fig_tl.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=40, l=50, r=80),
        height=320,
        legend=dict(
            orientation='h',
            yanchor='bottom', y=1.02,
            xanchor='left',   x=0,
            font=dict(size=12),
        ),
        xaxis=dict(
            showgrid=False,
            showline=True, linecolor='#d9d7cc',
            tickfont=dict(color='#696761', size=11),
            title=None,
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#ede9e4', gridwidth=1,
            showline=False,
            tickfont=dict(color='#696761', size=11),
            title=dict(text=vote_label, font=dict(color='#696761', size=11)),
            rangemode='tozero',
        ),
        hoverlabel=dict(bgcolor='white', font_size=12, bordercolor='#d9d7cc'),
        hovermode='x unified',
    )

    st.plotly_chart(fig_tl, use_container_width=True)
    st.markdown(
        f'<p style="color:#9c9790;font-size:0.71rem;text-align:center;margin-top:-0.5rem;">'
        f'Dashed vertical lines mark moments when the lead changed · '
        f'Each point reflects the cumulative {score_mode_label} through that date'
        f'</p>',
        unsafe_allow_html=True
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