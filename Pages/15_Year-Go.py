import io
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- Page Config ---
st.set_page_config(page_title="Year-Go", layout="wide")
from background import set_random_sarah_background
set_random_sarah_background(__file__, lightness_level=0.7)

# --- Load External CSS ---
from utils import load_css
load_css()

COLOR_M = "#221e8f"
COLOR_S = "#8a005c"

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar — same "Settings" pill-button pattern as the Electoral College page:
# pick which score decides each year's winner. Defaults to Time Score.
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
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

_YG_HR = '<hr style="border:none;border-top:1px solid #d9d7cc;margin:1px 24px 12px 24px;">'

with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>Settings</h2>", unsafe_allow_html=True)

    _win_mode_cur = st.session_state.get('yg_win', 'Count')
    _wc1, _wc2 = st.columns(2)
    with _wc1:
        if st.button("Count", key="yg_btn_count", use_container_width=True,
                     type="primary" if _win_mode_cur == "Count" else "secondary"):
            st.session_state['yg_win'] = 'Count'
            st.rerun()
    with _wc2:
        if st.button("Score", key="yg_btn_score", use_container_width=True,
                     type="primary" if _win_mode_cur == "Score" else "secondary"):
            st.session_state['yg_win'] = 'Score'
            st.rerun()

    st.markdown(_YG_HR, unsafe_allow_html=True)

    _game_mode_cur = st.session_state.get('yg_mode', 'Regular')
    _mc1, _mc2 = st.columns(2)
    with _mc1:
        if st.button("Regular", key="yg_btn_regular", use_container_width=True,
                     type="primary" if _game_mode_cur == "Regular" else "secondary"):
            st.session_state['yg_mode'] = 'Regular'
            st.rerun()
    with _mc2:
        if st.button("Bonus", key="yg_btn_bonus", use_container_width=True,
                     type="primary" if _game_mode_cur == "Bonus" else "secondary"):
            st.session_state['yg_mode'] = 'Bonus'
            st.rerun()

    st.markdown(_YG_HR, unsafe_allow_html=True)

    _score_mode_cur = st.session_state.get('yg_score', 'Time Score')
    _sc1, _sc2, _sc3 = st.columns(3)
    with _sc1:
        if st.button("Total", key="yg_btn_total", use_container_width=True,
                     type="primary" if _score_mode_cur == "Total Score" else "secondary"):
            st.session_state['yg_score'] = 'Total Score'
            st.rerun()
    with _sc2:
        if st.button("Geo", key="yg_btn_geo", use_container_width=True,
                     type="primary" if _score_mode_cur == "Geography Score" else "secondary"):
            st.session_state['yg_score'] = 'Geography Score'
            st.rerun()
    with _sc3:
        if st.button("Time", key="yg_btn_time", use_container_width=True,
                     type="primary" if _score_mode_cur == "Time Score" else "secondary"):
            st.session_state['yg_score'] = 'Time Score'
            st.rerun()

win_mode = st.session_state.get('yg_win', 'Count')
game_mode = st.session_state.get('yg_mode', 'Regular')
score_mode = st.session_state.get('yg_score', 'Time Score')
_score_mode_label = {"Total Score": "total score", "Geography Score": "geography score", "Time Score": "time score"}[score_mode]
_score_pts_label = {"Total Score": "pts", "Geography Score": "geo pts", "Time Score": "time pts"}[score_mode]

# ──────────────────────────────────────────────────────────────────────────────
# Header — same titling/subtitling format as the Electoral College page: an
# emoji + "##" title, then a small grey descriptive line right beneath it.
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("## 🗓️ Year-by-Year Leaderboard")
st.markdown(
    f'<p style="color:#696761;font-size:0.87rem;margin-top:-0.4rem;margin-bottom:0.8rem;">'
    f'All-time average {_score_mode_label} decides each year · Highest average wins the year · '
    f'Equal averages tie · Years with no rounds played are unclaimed</p>',
    unsafe_allow_html=True
)

@st.cache_data
def load_timeline_data(mtime=0):
    data = pd.read_csv("./Data/Timeguessr_Stats.csv")
    return data

stats_mtime = os.path.getmtime("./Data/Timeguessr_Stats.csv") if os.path.exists("./Data/Timeguessr_Stats.csv") else 0
data = load_timeline_data(stats_mtime)

col_year = "Year"

def _score_columns(df, mode):
    """(michael_series, sarah_series) for the selected score mode, matching
    the Electoral College page's own fallback: prefer the precomputed Round
    Score column for Total, else fall back to Geography + Time."""
    if mode == "Total Score":
        if "Michael Round Score" in df.columns and "Sarah Round Score" in df.columns:
            return df["Michael Round Score"], df["Sarah Round Score"]
        return (
            pd.to_numeric(df["Michael Geography Score"], errors="coerce").fillna(0)
            + pd.to_numeric(df["Michael Time Score"], errors="coerce").fillna(0),
            pd.to_numeric(df["Sarah Geography Score"], errors="coerce").fillna(0)
            + pd.to_numeric(df["Sarah Time Score"], errors="coerce").fillna(0),
        )
    elif mode == "Geography Score":
        return df["Michael Geography Score"], df["Sarah Geography Score"]
    else:
        return df["Michael Time Score"], df["Sarah Time Score"]

# ==========================================
# SHARED: per-year / per-decade / per-digit / grand-total Time Score rollups,
# and the "who's ahead, by how much" colour logic derived from them — the
# same numbers and logic the Timeline page's year-grid used to use.
# ==========================================
def _hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

_M_RGB = _hex_to_rgb(COLOR_M)
_S_RGB = _hex_to_rgb(COLOR_S)
# avg score gap treated as a "landslide" -> full-saturation tile. Total Score
# spans roughly double Geography/Time Score's 0-5000 range, so its cap scales
# up to match.
_LEAD_CAP = 3000 if score_mode == "Total Score" else 1500

def _year_cell_style(diff):
    """(background, border color, label color) for a year, given
    diff = Michael's avg score minus Sarah's avg score there."""
    if diff is None or pd.isna(diff) or diff == 0:
        return "#f2f1ec", "#bdbdb5", "#333333"
    leader_rgb = _M_RGB if diff > 0 else _S_RGB
    border = COLOR_M if diff > 0 else COLOR_S
    intensity = min(abs(diff) / _LEAD_CAP, 1.0)
    # Blend the leader's color into white, capped well short of full strength
    # so the tile never gets so dark the text on it stops being readable.
    blend = 0.12 + intensity * 0.5
    r = round(255 * (1 - blend) + leader_rgb[0] * blend)
    g = round(255 * (1 - blend) + leader_rgb[1] * blend)
    b = round(255 * (1 - blend) + leader_rgb[2] * blend)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    label_color = "#ffffff" if luminance < 0.55 else "#222222"
    return f"rgb({r},{g},{b})", border, label_color

_m_score_col, _s_score_col = _score_columns(data, score_mode)
_yr_df = pd.DataFrame({col_year: data[col_year], "_m": _m_score_col, "_s": _s_score_col})
for _c in _yr_df.columns:
    _yr_df[_c] = pd.to_numeric(_yr_df[_c], errors="coerce")
_yr_df = _yr_df.dropna(subset=[col_year])
_yr_df[col_year] = _yr_df[col_year].astype(int)
#
# Both a mean (michael_avg/sarah_avg — decides who wins the period, unchanged
# from before Score mode existed) and a sum (michael_sum/sarah_sum — feeds
# Score mode's per-square point value, see Margin below) are kept side by
# side, since the two answer different questions: "who's ahead on average"
# vs. "how many total points is that lead worth."
_yr_stats = _yr_df.groupby(col_year).agg(
    count=(col_year, "size"),
    michael_avg=("_m", "mean"),
    sarah_avg=("_s", "mean"),
    michael_sum=("_m", "sum"),
    sarah_sum=("_s", "sum"),
)

# Same aggregation one level up, keyed by decade start — feeds the wide
# "row header" cell to the left of each row (a whole-decade rollup, not an
# average of the 10 per-year averages, so a decade isn't skewed by a
# lightly-played year sitting next to a heavily-played one).
_yr_df["_decade"] = (_yr_df[col_year] // 10 * 10)
_decade_stats = _yr_df.groupby("_decade").agg(
    count=(col_year, "size"),
    michael_avg=("_m", "mean"),
    sarah_avg=("_s", "mean"),
    michael_sum=("_m", "sum"),
    sarah_sum=("_s", "sum"),
)

# Orthogonal rollup, keyed by the year's last digit (1903/1913/.../2023 all
# feed digit 3) — feeds the tall "column header" cell above each column.
_yr_df["_digit"] = _yr_df[col_year] % 10
_digit_stats = _yr_df.groupby("_digit").agg(
    count=(col_year, "size"),
    michael_avg=("_m", "mean"),
    sarah_avg=("_s", "mean"),
    michael_sum=("_m", "sum"),
    sarah_sum=("_s", "sum"),
)

# Every row folded into one — feeds the corner cell where the row-header
# column and column-header row would otherwise leave an empty square.
_grand_stats = {
    "count": len(_yr_df),
    "michael_avg": _yr_df["_m"].mean(),
    "sarah_avg": _yr_df["_s"].mean(),
    "michael_sum": _yr_df["_m"].sum(),
    "sarah_sum": _yr_df["_s"].sum(),
}

# ──────────────────────────────────────────────────────────────────────────────
# All years (1900-2029), each classified by who's ahead on average score that
# year (unchanged — this is what decides ownership everywhere, Count mode
# included) plus a "Margin" for Score mode: not the average gap, but the
# actual difference between the two players' total summed scores for that
# year — a lightly-played year's average lead isn't worth as many points as
# the same-size average lead racked up over many more rounds.
# ──────────────────────────────────────────────────────────────────────────────
_GRID_START = 1900
_DECADE_ROWS = 13
_ALL_YEARS = list(range(_GRID_START, _GRID_START + _DECADE_ROWS * 10))

_year_rows = []
for _yr in _ALL_YEARS:
    if _yr in _yr_stats.index:
        _r = _yr_stats.loc[_yr]
        _cnt = int(_r["count"])
        _m, _s = _r["michael_avg"], _r["sarah_avg"]
        _m_sum, _s_sum = _r["michael_sum"], _r["sarah_sum"]
    else:
        _cnt, _m, _s, _m_sum, _s_sum = 0, float("nan"), float("nan"), float("nan"), float("nan")
    if _cnt == 0 or pd.isna(_m) or pd.isna(_s):
        _winner, _margin = "third", 0.0
    elif _m > _s:
        _winner, _margin = "michael", abs(_m_sum - _s_sum)
    elif _s > _m:
        _winner, _margin = "sarah", abs(_m_sum - _s_sum)
    else:
        _winner, _margin = "tied", 0.0
    _year_rows.append({"Year": _yr, "Count": _cnt, "Michael_Avg": _m, "Sarah_Avg": _s,
                        "Winner": _winner, "Margin": _margin})

_year_df_all = pd.DataFrame(_year_rows)
_TOTAL_YEARS = len(_year_df_all)
_YEAR_WIN_COUNTS = {k: int((_year_df_all["Winner"] == k).sum()) for k in ["michael", "sarah", "tied", "third"]}

def _winner_of(cnt, m_avg, s_avg):
    """Same win/lose/tie/unplayed classification the year cells use, applied
    to any rollup (decade, digit, or grand-total) with a count and two
    averages."""
    if cnt == 0 or pd.isna(m_avg) or pd.isna(s_avg):
        return "third"
    if m_avg > s_avg:
        return "michael"
    if s_avg > m_avg:
        return "sarah"
    return "tied"

# ──────────────────────────────────────────────────────────────────────────────
# CONTIGUITY — the actual scoring goal for this board: the largest block of
# same-controlled year squares that touch edge-to-edge (not diagonally).
# Built from the 13x10 grid of year cells (row = decade, col = last digit),
# indexed 0..12 / 0..9. In Bonus mode the decade cells (col -1), digit cells
# (row -1), and the All-Time corner (-1,-1) join the grid too, so a block can
# bridge two years through a header square they both touch; in Regular mode
# those header cells are left out and never participate.
# ──────────────────────────────────────────────────────────────────────────────
_grid_owner = {}
for _, _gr in _year_df_all.iterrows():
    _gyr = int(_gr["Year"])
    _grow = (_gyr - _GRID_START) // 10
    _gcol = (_gyr - _GRID_START) % 10
    _grid_owner[(_grow, _gcol)] = _gr["Winner"]

if game_mode == "Bonus":
    for _dec_row in range(_DECADE_ROWS):
        _decade = _GRID_START + _dec_row * 10
        if _decade in _decade_stats.index:
            _dr = _decade_stats.loc[_decade]
            _grid_owner[(_dec_row, -1)] = _winner_of(_dr["count"], _dr["michael_avg"], _dr["sarah_avg"])
        else:
            _grid_owner[(_dec_row, -1)] = "third"
    for _dig in range(10):
        if _dig in _digit_stats.index:
            _dr = _digit_stats.loc[_dig]
            _grid_owner[(-1, _dig)] = _winner_of(_dr["count"], _dr["michael_avg"], _dr["sarah_avg"])
        else:
            _grid_owner[(-1, _dig)] = "third"
    _grid_owner[(-1, -1)] = _winner_of(_grand_stats["count"], _grand_stats["michael_avg"], _grand_stats["sarah_avg"])

# Each header cell (decade/digit/corner) touched by a Bonus-mode block
# multiplies that block's effective size by this factor, stacking per header.
_HEADER_MULTIPLIER = 1.1

def _connected_blocks(grid, owner_key, multiplier=_HEADER_MULTIPLIER, values=None):
    """Every 4-connected (up/down/left/right) block of cells controlled by
    owner_key within `grid` (a {(row, col): owner} dict), as
    {"real", "headers", "effective"} dicts sorted by effective size,
    largest first. Reused for the live board and for each timeline snapshot
    below, so both agree on what counts as "contiguous".

    In Bonus mode `grid` also carries header cells (decade rows at col -1,
    digit columns at row -1, the corner at (-1,-1)) so a block can bridge
    through them. A header cell is not itself a "year" though, so it doesn't
    add to the block's "real" total — instead each header cell inside the
    block multiplies the block's "effective" size by `multiplier`, stacking
    with every other header cell the block also touches, rounded to the
    nearest whole number at the end.

    `values` optionally maps a real year cell's (row, col) to how much it
    contributes to the block's "real" total — Score mode passes each year's
    point margin there so a block is worth the sum of its margins rather
    than a plain count; left as None (Count mode) every real cell is worth 1.

    `multiplier` takes an explicit default rather than always reading the
    module-level constant directly so that a cached caller (calculate_year_
    timeline below) can pass it in as a real argument — st.cache_data keys
    only on a function's own arguments, so a value pulled from a global at
    call time can change (as it did when this went from 2x to 1.25x) without
    busting an already-cached result."""
    _seen = set()
    _blocks = []
    for _pos, _owner in grid.items():
        if _owner != owner_key or _pos in _seen:
            continue
        _stack = [_pos]
        _seen.add(_pos)
        _real = _headers = 0
        while _stack:
            _r, _c = _stack.pop()
            if _r >= 0 and _c >= 0:
                _real += (values.get((_r, _c), 1) if values is not None else 1)
            else:
                _headers += 1
            for _dr, _dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                _nxt = (_r + _dr, _c + _dc)
                if grid.get(_nxt) == owner_key and _nxt not in _seen:
                    _seen.add(_nxt)
                    _stack.append(_nxt)
        _effective = int(round(_real * (multiplier ** _headers)))
        _blocks.append({"real": _real, "headers": _headers, "effective": _effective})
    return sorted(_blocks, key=lambda b: b["effective"], reverse=True)

# Minimum (effective) size for a secondary block to be worth calling out in
# the "Other" cards below — small 1-2 cell scraps aren't meaningfully
# "another block".
_MIN_NOTABLE_BLOCK = 4

# Score mode: each real year cell is worth its "Margin" (the sum-based point
# gap computed alongside Winner above) rather than a flat 1. Built once here
# so the live board and the "Other" totals below agree on each year's value.
_year_margin_grid = {}
for _, _gr in _year_df_all.iterrows():
    _gyr = int(_gr["Year"])
    _year_margin_grid[((_gyr - _GRID_START) // 10, (_gyr - _GRID_START) % 10)] = _gr["Margin"]

_block_values = _year_margin_grid if win_mode == "Score" else None

_michael_blocks = _connected_blocks(_grid_owner, "michael", values=_block_values)
_sarah_blocks = _connected_blocks(_grid_owner, "sarah", values=_block_values)
_MICHAEL_BLOCK = _michael_blocks[0]["effective"] if _michael_blocks else 0
_SARAH_BLOCK = _sarah_blocks[0]["effective"] if _sarah_blocks else 0
_michael_block_real = _michael_blocks[0]["real"] if _michael_blocks else 0
_sarah_block_real = _sarah_blocks[0]["real"] if _sarah_blocks else 0

# "Other" is whatever's left outside the (real, unmultiplied) largest block —
# a leftover year count in Count mode, or leftover margin points in Score
# mode — never the multiplied "effective" score.
if win_mode == "Score":
    _michael_total_available = float(_year_df_all.loc[_year_df_all["Winner"] == "michael", "Margin"].sum())
    _sarah_total_available = float(_year_df_all.loc[_year_df_all["Winner"] == "sarah", "Margin"].sum())
else:
    _michael_total_available = _YEAR_WIN_COUNTS["michael"]
    _sarah_total_available = _YEAR_WIN_COUNTS["sarah"]
_MICHAEL_OTHER = int(round(_michael_total_available - _michael_block_real))
_SARAH_OTHER = int(round(_sarah_total_available - _sarah_block_real))
_michael_other_blocks = [b["effective"] for b in _michael_blocks[1:] if b["effective"] >= _MIN_NOTABLE_BLOCK]
_sarah_other_blocks = [b["effective"] for b in _sarah_blocks[1:] if b["effective"] >= _MIN_NOTABLE_BLOCK]

# The same light-blue / light-magenta tints used by the "Other" cards below,
# pulled out as flat colors so the years-controlled bar can use them too.
_OTHER_M_COLOR = "#9b9acd"
_OTHER_S_COLOR = "#ca8cb6"

# ──────────────────────────────────────────────────────────────────────────────
# TOP SCOREBOARD — same shape as the Electoral College page's header: two
# summary bars above a row of score cards.
#   - Top bar: the actual scoring comparison — largest contiguous block,
#     Michael vs Sarah, ignoring tied/unplayed squares entirely.
#   - Bottom bar: years controlled as a share of the whole board, regardless
#     of margin — every controlled year counts the same.
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .ec-scoreboard { display: flex; gap: 1rem; margin: 1rem 0 0.6rem 0; align-items: stretch; flex-wrap: wrap; }
    .ec-card { flex: 1; min-width: 130px; border-radius: 12px; padding: 1.1rem 1.4rem; text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.10); }
    .ec-card .card-name  { font-size: 0.82rem; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase; margin-bottom: 0.15rem; }
    .ec-card .card-ev    { font-size: 3rem; font-weight: 700; line-height: 1.05; }
    .ec-card .card-label { font-size: 0.68rem; opacity: 0.72; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.1rem; }
    .ec-card .card-pct   { font-size: 0.92rem; font-weight: 600; margin-top: 0.25rem; opacity: 0.88; }
    .ec-card .card-sub   { font-size: 0.68rem; font-weight: 500; margin-top: 0.4rem; opacity: 0.85; }

    .card-michael { background: linear-gradient(135deg,#221e8f,#3d37d4); color: white; }
    .card-sarah   { background: linear-gradient(135deg,#8a005c,#c2006f); color: white; }
    .card-tied    { background: linear-gradient(135deg,#857b73,#a09587); color: white; }
    .card-third   { background: linear-gradient(135deg,#d9d7cc,#eeebe5); color: #696761; }
    /* The two "Other" cards (years controlled but outside the largest block)
       use the map's existing light-blue and light-magenta "leaning" tints
       rather than new colors, so they read as part of the same palette. */
    .card-other-michael { background: linear-gradient(135deg,#9b9acd,#c4c3e6); color: #221e8f; }
    .card-other-sarah   { background: linear-gradient(135deg,#ca8cb6,#e8bcd8); color: #8a005c; }

    .ev-bar-wrap { width: 100%; height: 20px; background: #e8e5e0; border-radius: 10px; overflow: hidden; display: flex; margin: 0.5rem 0 0.25rem 0; box-shadow: inset 0 1px 3px rgba(0,0,0,0.10); }
    .ev-seg { height: 100%; transition: width 0.5s ease; }
    .threshold-note { text-align: center; font-size: 0.76rem; color: #696761; margin-bottom: 1rem; font-weight: 500; letter-spacing: 0.02em; }
</style>
""", unsafe_allow_html=True)

_bar_total = _TOTAL_YEARS if _TOTAL_YEARS > 0 else 1

# Bonus mode's per-header multiplier makes "% of board" meaningless — a
# block's effective size can run well past the actual 130 squares. Show it
# instead as a share of a reference "max points" ceiling: a strongly
# controlled board (100 real years) touching every header cell (21 of them)
# it can reach. Derived from _HEADER_MULTIPLIER rather than a hardcoded
# number so this ceiling can't drift out of sync the way the timeline cache
# once did when the multiplier itself changed.
_MAX_BONUS_POINTS = _HEADER_MULTIPLIER ** 21 * 100

def _block_pct_html(block_size):
    if game_mode == "Bonus" or win_mode == "Score":
        return f"{block_size / _MAX_BONUS_POINTS * 100:.1f}% of max points"
    return f"{block_size / _bar_total * 100:.1f}% of board"

# Top bar: contiguous-block comparison, Michael vs Sarah only.
_cb_total = (_MICHAEL_BLOCK + _SARAH_BLOCK) or 1
_cb_m_pct = _MICHAEL_BLOCK / _cb_total * 100
_cb_s_pct = _SARAH_BLOCK / _cb_total * 100
_cb_segs = [(_MICHAEL_BLOCK, COLOR_M), (_SARAH_BLOCK, COLOR_S)]
_cb_bar_inner = "".join(
    f'<div class="ev-seg" style="width:{v / _cb_total * 100:.2f}%;background:{c};"></div>'
    for v, c in _cb_segs if v > 0
)

# Bottom bar: years controlled, as a percent of the whole board — each
# player's segment is split into their largest block (solid) and their
# other controlled years (light), the same solid/light language the map
# on the Electoral College page uses for "safe" vs "leaning".
_yc_segs = [
    (_MICHAEL_BLOCK,              COLOR_M),
    (_MICHAEL_OTHER,              _OTHER_M_COLOR),
    (_YEAR_WIN_COUNTS["tied"],    "#a09587"),
    (_YEAR_WIN_COUNTS["third"],   "#ddd9d4"),
    (_SARAH_OTHER,                _OTHER_S_COLOR),
    (_SARAH_BLOCK,                COLOR_S),
]
_yc_bar_inner = "".join(
    f'<div class="ev-seg" style="width:{v / _bar_total * 100:.2f}%;background:{c};"></div>'
    for v, c in _yc_segs if v > 0
)

def _other_blocks_html(block_sizes):
    if not block_sizes:
        return f'<div class="card-sub">No other blocks &ge;{_MIN_NOTABLE_BLOCK}</div>'
    _listed = ", ".join(str(s) for s in block_sizes)
    return f'<div class="card-sub">Also &ge;{_MIN_NOTABLE_BLOCK}: {_listed}</div>'

_michael_other_html = _other_blocks_html(_michael_other_blocks)
_sarah_other_html = _other_blocks_html(_sarah_other_blocks)

st.markdown(f"""
<div class="ev-bar-wrap">{_cb_bar_inner}</div>
<div class="threshold-note">Largest contiguous block &middot; Michael {_MICHAEL_BLOCK} ({_cb_m_pct:.1f}%) &middot; Sarah {_SARAH_BLOCK} ({_cb_s_pct:.1f}%)</div>

<div class="ev-bar-wrap">{_yc_bar_inner}</div>
<div class="threshold-note">Years controlled &middot; {_YEAR_WIN_COUNTS['michael']} Michael ({_YEAR_WIN_COUNTS['michael'] / _bar_total * 100:.1f}%) &middot; {_YEAR_WIN_COUNTS['sarah']} Sarah ({_YEAR_WIN_COUNTS['sarah'] / _bar_total * 100:.1f}%) &middot; {_YEAR_WIN_COUNTS['tied']} Tied &middot; {_YEAR_WIN_COUNTS['third']} Not Played</div>

<div class="ec-scoreboard">
  <div class="ec-card card-michael">
    <div class="card-name">Michael</div>
    <div class="card-ev">{_MICHAEL_BLOCK}</div>
    <div class="card-label">Largest Block</div>
    <div class="card-pct">{_block_pct_html(_MICHAEL_BLOCK)}</div>
  </div>
  <div class="ec-card card-sarah">
    <div class="card-name">Sarah</div>
    <div class="card-ev">{_SARAH_BLOCK}</div>
    <div class="card-label">Largest Block</div>
    <div class="card-pct">{_block_pct_html(_SARAH_BLOCK)}</div>
  </div>
  <div class="ec-card card-other-michael">
    <div class="card-name">Other Michael</div>
    <div class="card-ev">{_MICHAEL_OTHER}</div>
    <div class="card-label">Outside Block</div>
    {_michael_other_html}
  </div>
  <div class="ec-card card-other-sarah">
    <div class="card-name">Other Sarah</div>
    <div class="card-ev">{_SARAH_OTHER}</div>
    <div class="card-label">Outside Block</div>
    {_sarah_other_html}
  </div>
  <div class="ec-card card-tied">
    <div class="card-name">Tied</div>
    <div class="card-ev">{_YEAR_WIN_COUNTS['tied']}</div>
    <div class="card-label">Years</div>
  </div>
  <div class="ec-card card-third">
    <div class="card-name">Not Played</div>
    <div class="card-ev">{_YEAR_WIN_COUNTS['third']}</div>
    <div class="card-label">Years</div>
  </div>
</div>
""", unsafe_allow_html=True)

def _cell_html(label, stats_row, extra_cls=""):
    if stats_row is not None:
        _cnt = int(stats_row["count"])
        _m_avg, _s_avg = stats_row["michael_avg"], stats_row["sarah_avg"]
        _diff = (_m_avg - _s_avg) if (pd.notna(_m_avg) and pd.notna(_s_avg)) else None
        _bg, _border, _label_c = _year_cell_style(_diff)
        if _diff is None:
            _lead_cls, _lead_txt = "yc-tied", "—"
        elif _diff == 0:
            _lead_cls, _lead_txt = "yc-tied", "Tied"
        else:
            _lead_cls = "yc-m" if _diff > 0 else "yc-s"
            _lead_txt = f"+{abs(_diff):,.0f}"
        _count_txt = f"{_cnt}&times;"
        _faded = ""
    else:
        _bg, _border, _label_c = "#f7f7f4", "#e2e1da", "#999999"
        _lead_cls, _lead_txt = "yc-tied", "—"
        _count_txt = "0&times;"
        _faded = "opacity:0.55;"
    cls = f"year-cell {extra_cls}".strip()
    return (
        f'<div class="{cls}" style="background:{_bg}; border-color:{_border}; {_faded}" title="{label}">'
        f'<div class="yc-year" style="color:{_label_c};">{label}</div>'
        f'<div class="yc-count" style="color:{_label_c};">{_count_txt}</div>'
        f'<div class="yc-scores"><span class="yc-lead {_lead_cls}">{_lead_txt}</span></div>'
        f'</div>'
    )

# ==========================================
# YEAR GRID — 13 decades (rows) x 10 years-within-decade (columns) = every
# year from 1900 to 2029, one cell each. Each cell shows how many rounds have
# actually landed on that year, and by how much whoever's ahead there is
# leading on average Time Score; the cell's background and border shade
# toward that leader, darker the bigger the lead is. A wide cell to the left
# of each row rolls up its decade; a tall cell above each column rolls up
# every year ending in that digit; the corner where those two headers would
# otherwise leave a dead square instead rolls up literally everything.
# ==========================================
_cells_html = []

# Header row: the corner (grand total) first, then one tall cell per column
# rolling up every year that ends in that digit.
_cells_html.append(_cell_html("🏆 All-Time", _grand_stats, extra_cls="corner-cell"))
for _digit in range(10):
    _dg_stats = _digit_stats.loc[_digit] if _digit in _digit_stats.index else None
    _cells_html.append(_cell_html(f"{_digit}s", _dg_stats, extra_cls="digit-cell"))

for _row in range(_DECADE_ROWS):
    _decade = _GRID_START + _row * 10
    _d_stats = _decade_stats.loc[_decade] if _decade in _decade_stats.index else None
    _cells_html.append(_cell_html(f"🗓️ {_decade}s", _d_stats, extra_cls="decade-cell"))
    for _col in range(10):
        _yr = _decade + _col
        _y_stats = _yr_stats.loc[_yr] if _yr in _yr_stats.index else None
        _cells_html.append(_cell_html(str(_yr), _y_stats))

# The grid sits inside its own centered, padded "card" rather than running
# edge-to-edge in the page column — with a wide decade key thrown into the
# mix, a flush-edge grid reads as lopsided even though its box is technically
# centered; a visible, symmetric frame around the whole thing removes any
# doubt that it's centered on the page.
st.markdown("""
<style>
    .year-grid-card { margin:20px auto 35px auto !important; padding:20px 20px 12px 20px; background:#fbfbf9; border:1px solid #e7e5dd; border-radius:18px; box-shadow:0 6px 22px rgba(0,0,0,0.07); box-sizing:border-box; }
    /* Decade column is a fixed width rather than an "Nfr" share: the year
       columns' own content (the lead badge) has a real minimum width the
       grid honors first, which was quietly capping how much wider a
       merely-proportional decade track could actually end up — pinning it
       in px sidesteps that fight entirely and guarantees the ~2x width. The
       header row (digit + corner cells) is pinned to that same 190px, so it
       ends up exactly as tall as the decade cells are wide. */
    .year-grid { display:grid; grid-template-columns:190px repeat(10, minmax(90px, 1fr)); grid-template-rows:190px repeat(13, auto); gap:6px; width:100%; }
    .year-cell { display:flex; flex-direction:column; align-items:center; justify-content:center; border-radius:9px; padding:8px 3px 7px 3px; text-align:center; box-sizing:border-box; border:6.25px solid; transition:transform .12s ease; cursor:default; }
    .year-cell:hover { transform:scale(1.08); z-index:3; box-shadow:0 4px 14px rgba(0,0,0,0.25); }
    .yc-year { font-family:'Poppins',sans-serif; font-weight:800; font-size:14px; line-height:1.1; }
    .yc-count { font-family:'Inter',sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; margin-top:1px; opacity:.8; }
    .yc-scores { display:flex; justify-content:center; gap:4px; margin-top:5px; }
    .yc-lead { font-family:'Inter',sans-serif; font-size:10px; font-weight:800; padding:1px 6px; border-radius:5px; background:rgba(255,255,255,0.6); }
    .yc-lead.yc-m { color:#221e8f; }
    .yc-lead.yc-s { color:#8a005c; }
    .yc-lead.yc-tied { color:#666660; }
    /* The decade cell is the "Shift key" of its row: a fixed 190px-wide
       track (about double a year cell's own width), its own rounder
       corners, a bolder/bigger label carrying a small calendar mark, and
       a bigger lead badge — several cues stacked together so it unmistakably
       reads as the row's label rather than just another tile. */
    .decade-cell { border-radius:14px; }
    .decade-cell .yc-year { font-size:17px; font-weight:900; letter-spacing:.3px; }
    .decade-cell .yc-lead { font-size:11px; padding:2px 7px; }
    /* Digit cell is the decade cell's counterpart turned 90°: same rounder
       corners and bold label, but tall (190px, via the header row track)
       rather than wide, rolling up "every year ending in N" above its
       column. The corner cell is both at once — a full 190x190 square —
       since it's where those two headers would otherwise leave a dead
       square, rolled up into a grand total across every year on the board. */
    .digit-cell, .corner-cell { border-radius:14px; }
    .digit-cell .yc-year, .corner-cell .yc-year { font-size:17px; font-weight:900; letter-spacing:.3px; }
    .digit-cell .yc-lead, .corner-cell .yc-lead { font-size:11px; padding:2px 7px; }
    .corner-cell .yc-year { font-size:15px; }
    @media (max-width: 900px) {
        .year-grid { grid-template-columns:120px repeat(4, minmax(60px, 1fr)); grid-template-rows:120px repeat(13, auto); }
    }
</style>
""", unsafe_allow_html=True)
st.markdown(f'<div class="year-grid-card"><div class="year-grid">{"".join(_cells_html)}</div></div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# OVER TIME — same shape as the Electoral College page's EV timeline: replay
# every round chronologically, re-run the same contiguity logic after each
# date's rounds land, and emit a point whenever either side's largest block
# size actually changes. In Bonus mode the plotted value is the header
# multiplier's "points" score rather than a plain block size, so the section
# is titled accordingly.
# ──────────────────────────────────────────────────────────────────────────────
_over_time_title = "Points Over Time" if (game_mode == "Bonus" or win_mode == "Score") else "Largest Block Over Time"
st.markdown(f'<div class="section-header">{_over_time_title}</div>', unsafe_allow_html=True)

@st.cache_data
def calculate_year_timeline(df_json, mode, bonus, multiplier, use_score):
    _df = pd.read_json(io.StringIO(df_json), orient='split')
    _df['Date'] = pd.to_datetime(_df['Date'], errors='coerce')
    _df['_yr'] = pd.to_numeric(_df[col_year], errors='coerce')
    _m_raw, _s_raw = _score_columns(_df, mode)
    _df['_m'] = pd.to_numeric(_m_raw, errors='coerce')
    _df['_s'] = pd.to_numeric(_s_raw, errors='coerce')
    _df = _df.dropna(subset=['_yr', 'Date'])
    _df['_yr'] = _df['_yr'].astype(int)
    _df = _df.sort_values('Date').reset_index(drop=True)

    _m_sum, _s_sum, _m_cnt, _s_cnt, _winner = {}, {}, {}, {}, {}

    def _compute_winner(yr):
        # Ownership stays average-based (unchanged from before Score mode
        # existed) — only the per-square point *value* used below is sum
        # based, so Count mode's board never shifts.
        mc, sc = _m_cnt.get(yr, 0), _s_cnt.get(yr, 0)
        if mc == 0 or sc == 0:
            return "third"
        ma, sa = _m_sum.get(yr, 0) / mc, _s_sum.get(yr, 0) / sc
        if ma > sa: return "michael"
        if sa > ma: return "sarah"
        return "tied"

    def _rollup_winner(years):
        mt = st_ = 0.0
        mn = sn = 0
        for yr in years:
            mt += _m_sum.get(yr, 0); mn += _m_cnt.get(yr, 0)
            st_ += _s_sum.get(yr, 0); sn += _s_cnt.get(yr, 0)
        if mn == 0 or sn == 0:
            return "third"
        ma, sa = mt / mn, st_ / sn
        if ma > sa: return "michael"
        if sa > ma: return "sarah"
        return "tied"

    _rows, _prev_state, _total_rounds, _last_date = [], None, 0, None
    _year_lo, _year_hi = _GRID_START, _GRID_START + _DECADE_ROWS * 10

    for _date, _group in _df.groupby('Date', sort=True):
        _changed = set()
        for _, _row in _group.iterrows():
            _yr = int(_row['_yr'])
            if not (_year_lo <= _yr < _year_hi):
                continue
            if pd.notna(_row['_m']):
                _m_sum[_yr] = _m_sum.get(_yr, 0) + _row['_m']
                _m_cnt[_yr] = _m_cnt.get(_yr, 0) + 1
            if pd.notna(_row['_s']):
                _s_sum[_yr] = _s_sum.get(_yr, 0) + _row['_s']
                _s_cnt[_yr] = _s_cnt.get(_yr, 0) + 1
            _changed.add(_yr)
            _total_rounds += 1
        for _yr in _changed:
            _winner[_yr] = _compute_winner(_yr)
        _last_date = _date

        _grid, _values = {}, {}
        for _yr in range(_year_lo, _year_hi):
            _w = _winner.get(_yr, "third")
            _pos = ((_yr - _GRID_START) // 10, (_yr - _GRID_START) % 10)
            _grid[_pos] = _w
            if use_score:
                _values[_pos] = abs(_m_sum.get(_yr, 0) - _s_sum.get(_yr, 0))

        if bonus:
            for _dec_row in range(_DECADE_ROWS):
                _decade = _year_lo + _dec_row * 10
                _grid[(_dec_row, -1)] = _rollup_winner(range(_decade, _decade + 10))
            for _dig in range(10):
                _grid[(-1, _dig)] = _rollup_winner(range(_year_lo + _dig, _year_hi, 10))
            _grid[(-1, -1)] = _rollup_winner(range(_year_lo, _year_hi))

        _block_vals = _values if use_score else None
        _m_grid_blocks = _connected_blocks(_grid, "michael", multiplier, _block_vals)
        _s_grid_blocks = _connected_blocks(_grid, "sarah", multiplier, _block_vals)
        _m_block = _m_grid_blocks[0]["effective"] if _m_grid_blocks else 0
        _s_block = _s_grid_blocks[0]["effective"] if _s_grid_blocks else 0

        _state = (_m_block, _s_block)
        if _state != _prev_state:
            _rows.append({
                "Date": _date, "round_num": _total_rounds,
                "michael_block": _m_block, "sarah_block": _s_block,
            })
            _prev_state = _state

    if not _rows:
        return pd.DataFrame(columns=["Date", "round_num", "michael_block", "sarah_block"])

    _tl = pd.DataFrame(_rows)
    _last = _tl.iloc[-1].copy()
    if _total_rounds > _last["round_num"]:
        _last["round_num"] = _total_rounds
        _last["Date"] = _last_date
        _tl = pd.concat([_tl, _last.to_frame().T], ignore_index=True)
    return _tl

_df_json = data.to_json(orient='split', date_format='iso')
_year_timeline = calculate_year_timeline(_df_json, score_mode, game_mode == "Bonus", _HEADER_MULTIPLIER, win_mode == "Score")

if not _year_timeline.empty and len(_year_timeline) > 1:
    _tl = _year_timeline.copy()
    _tl['round_num'] = pd.to_numeric(_tl['round_num'], errors='coerce').fillna(0).astype(int)
    _tl['Date'] = pd.to_datetime(_tl['Date'])

    _monthly_dates = pd.date_range(_tl['Date'].min(), _tl['Date'].max(), freq='MS')
    if len(_tl) > 1 and len(_monthly_dates) > 0:
        _tick_rounds = np.interp(
            [d.timestamp() for d in _monthly_dates],
            [d.timestamp() for d in _tl['Date']],
            _tl['round_num'].astype(float)
        ).astype(int)
        _tick_labels = [d.strftime('%b %Y') for d in _monthly_dates]
    else:
        _tick_rounds = _tl['round_num'].tolist()
        _tick_labels = _tl['Date'].dt.strftime('%b %Y').tolist()

    fig_yr_tl = go.Figure()
    fig_yr_tl.add_trace(go.Scatter(
        x=_tl['round_num'], y=_tl['michael_block'], customdata=_tl['Date'],
        mode='lines', line=dict(color=COLOR_M, width=2.5, shape='hv'),
        fill='tozeroy', fillcolor='rgba(34,30,143,0.10)', name='Michael',
        hovertemplate='<b>Michael</b>: %{y:,}<br>Round %{x:,} &middot; %{customdata|%b %d, %Y}<extra></extra>',
    ))
    fig_yr_tl.add_trace(go.Scatter(
        x=_tl['round_num'], y=_tl['sarah_block'], customdata=_tl['Date'],
        mode='lines', line=dict(color=COLOR_S, width=2.5, shape='hv'),
        fill='tozeroy', fillcolor='rgba(138,0,92,0.10)', name='Sarah',
        hovertemplate='<b>Sarah</b>: %{y:,}<br>Round %{x:,} &middot; %{customdata|%b %d, %Y}<extra></extra>',
    ))
    _last_row = _tl.iloc[-1]
    for _key, _col, _yshift in [('michael_block', COLOR_M, 8), ('sarah_block', COLOR_S, -14)]:
        fig_yr_tl.add_annotation(
            x=int(_last_row['round_num']), y=float(_last_row[_key]),
            text=f"  {int(_last_row[_key]):,}",
            showarrow=False, font=dict(color=_col, size=11, family='Arial'),
            xanchor='left', yanchor='middle', yshift=_yshift,
        )

    _lead = (_tl['michael_block'] > _tl['sarah_block']).map({True: 'michael', False: 'sarah'})
    _prev_lead = _lead.shift(1, fill_value=_lead.iloc[0])
    _flips = _tl[(_lead != _prev_lead) & (_tl.index > 0)]
    for _, _flip_row in _flips.iterrows():
        _new_leader = 'michael' if _flip_row['michael_block'] > _flip_row['sarah_block'] else 'sarah'
        fig_yr_tl.add_vline(
            x=int(_flip_row['round_num']),
            line_dash='dash', line_color=(COLOR_M if _new_leader == 'michael' else COLOR_S),
            line_width=1, opacity=0.45,
        )

    fig_yr_tl.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=40, l=70, r=80), height=320,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0, font=dict(size=12)),
        xaxis=dict(
            tickvals=_tick_rounds, ticktext=_tick_labels,
            showgrid=False, showline=True, linecolor='#d9d7cc',
            tickfont=dict(color='#696761', size=11), title=None, automargin=False,
            range=[int(_tl['round_num'].iloc[0]), int(_tl['round_num'].iloc[-1])],
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#ede9e4', gridwidth=1, showline=False,
            tickfont=dict(color='#696761', size=11), automargin=False,
            title=dict(text=("Points" if (game_mode == "Bonus" or win_mode == "Score") else "Years"), font=dict(color='#696761', size=11)),
            rangemode='tozero',
        ),
        hoverlabel=dict(bgcolor='white', font_size=12, bordercolor='#d9d7cc'),
        hovermode='x unified',
    )

    st.plotly_chart(fig_yr_tl, use_container_width=True)
    st.markdown(
        '<p style="color:#9c9790;font-size:0.71rem;text-align:center;margin-top:0.5rem;">'
        'X-axis spacing proportional to rounds played &middot; tick labels show calendar month &middot; '
        'dashed lines mark block-lead changes &middot; lines track each side&rsquo;s largest contiguous block</p>',
        unsafe_allow_html=True
    )
else:
    st.info("Not enough data points to render a timeline.")

# ==========================================
# YEAR RESULTS TABLE — every year from 1900-2029, filterable/sortable, styled
# to match the Electoral College page's State Results table at the bottom of
# that page (same section header, badge, and table CSS).
# ==========================================
st.markdown("""
<style>
    .section-header {
        font-size: 1rem; font-weight: 600; color: #696761;
        margin: 1.6rem 0 0.7rem 0;
        border-left: 4px solid #696761; padding-left: 0.6rem;
    }
    .year-table { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
    .year-table th {
        background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;
        padding: 10px 12px; text-align: left; color: #696761;
        font-weight: 600; font-size: 0.74rem;
        text-transform: uppercase; letter-spacing: 0.05em;
    }
    .year-table th.right  { text-align: right; }
    .year-table th.center { text-align: center; }
    .year-table td { padding: 8px 12px; border-bottom: 1px solid #d9d7cc; color: #696761; }
    .year-table tr:hover td { background-color: rgba(255,255,255,0.55); }

    .badge { display: inline-block; padding: 2px 10px; border-radius: 99px; font-size: 0.71rem; font-weight: 600; }
    .badge-michael { background: #e8e7ff; color: #221e8f; }
    .badge-sarah   { background: #ffe6f4; color: #8a005c; }
    .badge-tied    { background: #e8e5e0; color: #696761; }
    .badge-third   { background: #f0ede8; color: #9c9790; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header">Year Results</div>', unsafe_allow_html=True)

_tc1, _tc2 = st.columns([2, 2])
with _tc1:
    _filter_winner = st.selectbox("Filter by outcome", ["All", "Michael", "Sarah", "Tied", "Not Played"])
with _tc2:
    _sort_opts = ["Year", "Michael Avg ↓", "Sarah Avg ↓", "Lead ↓", "Times Appeared ↓"]
    _sort_by = st.selectbox("Sort by", _sort_opts)

_disp = _year_df_all.copy()
_w_map = {"Michael": "michael", "Sarah": "sarah", "Tied": "tied", "Not Played": "third"}
if _filter_winner != "All":
    _disp = _disp[_disp["Winner"] == _w_map[_filter_winner]]

if _sort_by == "Michael Avg ↓":
    _disp = _disp.sort_values("Michael_Avg", ascending=False)
elif _sort_by == "Sarah Avg ↓":
    _disp = _disp.sort_values("Sarah_Avg", ascending=False)
elif _sort_by == "Lead ↓":
    _disp = _disp.assign(_lead=(_disp["Michael_Avg"] - _disp["Sarah_Avg"]).abs())
    _disp = _disp.sort_values("_lead", ascending=False)
elif _sort_by == "Times Appeared ↓":
    _disp = _disp.sort_values("Count", ascending=False)
else:
    _disp = _disp.sort_values("Year")

_badge_html = {
    "michael": '<span class="badge badge-michael">Michael</span>',
    "sarah":   '<span class="badge badge-sarah">Sarah</span>',
    "tied":    '<span class="badge badge-tied">Tied</span>',
    "third":   '<span class="badge badge-third">Not Played</span>',
}

_rows_html = ""
for _, _row in _disp.iterrows():
    _m, _s = _row["Michael_Avg"], _row["Sarah_Avg"]
    _m_str = f"{_m:,.0f}" if pd.notna(_m) else "—"
    _s_str = f"{_s:,.0f}" if pd.notna(_s) else "—"
    if pd.notna(_m) and pd.notna(_s):
        _diff = _m - _s
        if _diff > 0:
            _diff_str = f'<span style="color:{COLOR_M};font-weight:600;">+{_diff:,.0f}</span>'
        elif _diff < 0:
            _diff_str = f'<span style="color:{COLOR_S};font-weight:600;">+{abs(_diff):,.0f}</span>'
        else:
            _diff_str = '<span style="color:#a09587;">0</span>'
    else:
        _diff_str = "—"

    _rows_html += f"""
    <tr>
      <td><b>{int(_row['Year'])}</b></td>
      <td style="text-align:center;font-weight:700;">{int(_row['Count'])}</td>
      <td style="text-align:center;">{_badge_html[_row['Winner']]}</td>
      <td style="color:{COLOR_M};text-align:right;">{_m_str}</td>
      <td style="color:{COLOR_S};text-align:right;">{_s_str}</td>
      <td style="text-align:center;">{_diff_str}</td>
    </tr>"""

st.markdown(
    f"""
    <table class="year-table">
      <thead><tr>
        <th>Year</th>
        <th class="center">Times Appeared</th>
        <th class="center">Winner</th>
        <th class="right" style="color:{COLOR_M};">Michael (avg {_score_pts_label})</th>
        <th class="right" style="color:{COLOR_S};">Sarah (avg {_score_pts_label})</th>
        <th class="center">Lead</th>
      </tr></thead>
      <tbody>{_rows_html}</tbody>
    </table>
    """,
    unsafe_allow_html=True,
)
