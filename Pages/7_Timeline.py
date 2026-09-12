import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import math
import os

# --- Page Config ---
st.set_page_config(page_title="Timeline Analysis", layout="wide")
from background import set_random_sarah_background
set_random_sarah_background(__file__, lightness_level=0.7)

# --- Load External CSS ---
from utils import load_css
load_css()

# --- Custom Header & Section Styles ---
st.markdown("""
    <div class="page-header" style="text-align: center; margin-bottom: 40px; border-bottom: 4px double #ccc; padding-bottom: 30px; margin-top: 20px;">
        <h1 class="page-title" style="font-family: 'Poppins', sans-serif; font-weight: 900; font-size: 48px; color: #000; letter-spacing: -1px; margin: 0; text-transform: uppercase;">Timeline Analysis</h1>
        <div class="page-subtitle" style="font-family: 'Inter', sans-serif; color: #444; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; margin-top: 12px;">Historical Era Accuracies & Biases</div>
    </div>
    
    <style>
        .section-heading { font-family: 'Poppins', sans-serif; font-size: 22px; font-weight: 800; color: #111; text-transform: uppercase; letter-spacing: 1px; border-left: 6px solid #111; padding-left: 12px; margin-top: 40px; margin-bottom: 20px; }
        /* Ensure text visibility in dark mode for non-plot elements if needed */
        [data-testid="stMarkdownContainer"] p { color: inherit; }
    </style>
""", unsafe_allow_html=True)

# --- Universal Plotly Theme ---
PLOT_THEME = dict(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font=dict(family="Inter, sans-serif", color="#111111"),
    xaxis=dict(
        showgrid=True, 
        gridcolor="#eeeeee", 
        zeroline=False, 
        title_font=dict(size=13, color="#000000"),
        tickfont=dict(color="#222222")
    ),
    yaxis=dict(
        showgrid=True, 
        gridcolor="#eeeeee", 
        zeroline=False, 
        title_font=dict(size=13, color="#000000"),
        tickfont=dict(color="#222222")
    ),
    margin=dict(l=50, r=30, t=60, b=50),
    legend=dict(
        orientation="h", 
        yanchor="bottom", 
        y=1.02, 
        xanchor="right", 
        x=1,
        font=dict(size=12, color="#000000")
    ),
    title_font=dict(family="Poppins, sans-serif", size=20, color="#000000")
)

COLOR_M = "#221e8f"
COLOR_S = "#8a005c"
COLOR_ACTUAL = "#7f8c8d"

@st.cache_data
def load_timeline_data(mtime=0):
    data = pd.read_csv("./Data/Timeguessr_Stats.csv")
    return data

stats_mtime = os.path.getmtime("./Data/Timeguessr_Stats.csv") if os.path.exists("./Data/Timeguessr_Stats.csv") else 0
data = load_timeline_data(stats_mtime)

col_year = "Year"
col_michael = "Michael Time Guessed"
col_sarah = "Sarah Time Guessed"

year_vals = pd.to_numeric(data[col_year], errors="coerce").dropna().astype(float).values
michael_vals = pd.to_numeric(data[col_michael], errors="coerce").dropna().astype(float).values
sarah_vals = pd.to_numeric(data[col_sarah], errors="coerce").dropna().astype(float).values

# ==========================================
# SHARED: per-year / per-decade / per-digit / grand-total Time Score rollups,
# and the "who's ahead, by how much" colour logic derived from them. Both the
# distribution chart and the year-grid below are built from these same
# numbers, so a year is always coloured identically everywhere on this page.
# ==========================================
def _hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

_M_RGB = _hex_to_rgb(COLOR_M)
_S_RGB = _hex_to_rgb(COLOR_S)
_LEAD_CAP = 1500  # avg Time Score gap (points, out of 5000) treated as a "landslide" -> full-saturation tile

def _year_cell_style(diff):
    """(background, border color, label color) for a year, given
    diff = Michael's avg Time Score minus Sarah's avg Time Score there."""
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

def _bar_color(diff):
    """A punchier version of _year_cell_style's blend for the count-overlay
    bars in the distribution chart below — bars don't need to stay pale for
    text to sit on top of them the way a grid tile does, so they lean much
    further into the leader's actual color and read far more vividly at a
    glance."""
    if diff is None or pd.isna(diff) or diff == 0:
        return "#c9c7bc"
    leader_rgb = _M_RGB if diff > 0 else _S_RGB
    intensity = min(abs(diff) / _LEAD_CAP, 1.0)
    blend = 0.45 + intensity * 0.55
    r = round(255 * (1 - blend) + leader_rgb[0] * blend)
    g = round(255 * (1 - blend) + leader_rgb[1] * blend)
    b = round(255 * (1 - blend) + leader_rgb[2] * blend)
    return f"rgb({r},{g},{b})"

_yr_df = data[[col_year, "Michael Time Score", "Sarah Time Score"]].copy()
for _c in _yr_df.columns:
    _yr_df[_c] = pd.to_numeric(_yr_df[_c], errors="coerce")
_yr_df = _yr_df.dropna(subset=[col_year])
_yr_df[col_year] = _yr_df[col_year].astype(int)
_yr_stats = _yr_df.groupby(col_year).agg(
    count=(col_year, "size"),
    michael_avg=("Michael Time Score", "mean"),
    sarah_avg=("Sarah Time Score", "mean"),
)

# Same aggregation one level up, keyed by decade start — feeds the wide
# "row header" cell to the left of each row (a whole-decade rollup, not an
# average of the 10 per-year averages, so a decade isn't skewed by a
# lightly-played year sitting next to a heavily-played one).
_yr_df["_decade"] = (_yr_df[col_year] // 10 * 10)
_decade_stats = _yr_df.groupby("_decade").agg(
    count=(col_year, "size"),
    michael_avg=("Michael Time Score", "mean"),
    sarah_avg=("Sarah Time Score", "mean"),
)

# Orthogonal rollup, keyed by the year's last digit (1903/1913/.../2023 all
# feed digit 3) — feeds the tall "column header" cell above each column.
_yr_df["_digit"] = _yr_df[col_year] % 10
_digit_stats = _yr_df.groupby("_digit").agg(
    count=(col_year, "size"),
    michael_avg=("Michael Time Score", "mean"),
    sarah_avg=("Sarah Time Score", "mean"),
)

# Every row folded into one — feeds the corner cell where the row-header
# column and column-header row would otherwise leave an empty square.
_grand_stats = {
    "count": len(_yr_df),
    "michael_avg": _yr_df["Michael Time Score"].mean(),
    "sarah_avg": _yr_df["Sarah Time Score"].mean(),
}

def _cell_html(label, stats_row, extra_cls=""):
    if stats_row is not None:
        _cnt = int(stats_row["count"])
        _m_avg, _s_avg = stats_row["michael_avg"], stats_row["sarah_avg"]
        _diff = (_m_avg - _s_avg) if (pd.notna(_m_avg) and pd.notna(_s_avg)) else None
        _bg, _border, _label_c = _year_cell_style(_diff)
        _m_txt = f"{_m_avg:,.0f}" if pd.notna(_m_avg) else "—"
        _s_txt = f"{_s_avg:,.0f}" if pd.notna(_s_avg) else "—"
        _count_txt = f"{_cnt}&times;"
        _faded = ""
    else:
        _bg, _border, _label_c = "#f7f7f4", "#e2e1da", "#999999"
        _m_txt = _s_txt = "—"
        _count_txt = "0&times;"
        _faded = "opacity:0.55;"
    cls = f"year-cell {extra_cls}".strip()
    return (
        f'<div class="{cls}" style="background:{_bg}; border-color:{_border}; {_faded}" title="{label}">'
        f'<div class="yc-year" style="color:{_label_c};">{label}</div>'
        f'<div class="yc-count" style="color:{_label_c};">{_count_txt}</div>'
        f'<div class="yc-scores"><span class="yc-m">{_m_txt}</span><span class="yc-s">{_s_txt}</span></div>'
        f'</div>'
    )

# ==========================================
# ACTUAL YEAR DISTRIBUTION — two signals, one chart, one x-axis of years
# shown only once instead of on two separate plots:
#   - bottom: the "who guessed closer" split, a full-width 0-100% stacked
#     bar per year (Michael / Tie / Sarah).
#   - literally resting on top of that, starting exactly at the 100% line
#     and growing upward from there (not overlaid in front of it) — a bar
#     the same width as the stack beneath it, whose height is that year's
#     appearance count and whose shade leans toward whoever's ahead there
#     on average Time Score, the same lead-margin color language the grid
#     below uses, more vividly the bigger the lead.
# Both live on the same y-axis: the percentage stack reads off the left
# 0-100% scale, and the count bars above the 100% line read off a second
# scale (right-hand axis) whose zero is pinned to line up with that same
# 100% mark, so the seam between the two is exact.
# ==========================================
st.markdown('<div class="section-heading">Actual Year Distribution</div>', unsafe_allow_html=True)

_out_df = data[[col_year, col_michael, col_sarah]].copy()
_out_df[col_year]    = pd.to_numeric(_out_df[col_year],    errors="coerce")
_out_df[col_michael] = pd.to_numeric(_out_df[col_michael], errors="coerce")
_out_df[col_sarah]   = pd.to_numeric(_out_df[col_sarah],   errors="coerce")
_out_df = _out_df.dropna()
_out_df["_yr"]  = _out_df[col_year].astype(int)
_out_df["_me"]  = (_out_df[col_michael] - _out_df[col_year]).abs()
_out_df["_se"]  = (_out_df[col_sarah]   - _out_df[col_year]).abs()
_out_df["_out"] = np.where(_out_df["_me"] < _out_df["_se"], "michael",
                  np.where(_out_df["_se"] < _out_df["_me"], "sarah", "tie"))

_bucket = st.sidebar.slider("Year Bucket Size", min_value=1, max_value=10, value=1, step=1, key="outcome_bucket")
_out_df["_bin"] = (_out_df["_yr"] // _bucket) * _bucket

_by = _out_df.groupby("_bin")["_out"].value_counts().unstack(fill_value=0)
for _c in ["michael", "sarah", "tie"]:
    if _c not in _by.columns:
        _by[_c] = 0
_by["_n"] = _by[["michael", "sarah", "tie"]].sum(axis=1)
# No minimum-sample filter: dropping thin bins would silently make real
# years vanish from the chart with no visual explanation. Every bin backed
# by at least one round is kept.
_bins = _by.index.tolist()

_x_label = "Year" if _bucket == 1 else f"{_bucket}-Year Bucket Starting Year"
_hover_x = "%{x}" if _bucket == 1 else "%{x}–%{customdata[0]}"
_end_years = [b + _bucket - 1 for b in _bins]
_n_vals = _by["_n"].tolist()
_total_word = [("1 round total" if n == 1 else f"{n} rounds total") for n in _n_vals]
_cd = np.stack([_end_years, _total_word], axis=-1)

# Same bucketing applied to the lead-margin numbers (avg Time Score), keyed
# to the exact same bins as the outcome split above, so the overlay bar for
# a bin lines up with the stacked bar it sits on top of.
_yr_df["_bin"] = (_yr_df[col_year] // _bucket) * _bucket
_lead_stats = _yr_df.groupby("_bin").agg(
    count=(col_year, "size"),
    michael_avg=("Michael Time Score", "mean"),
    sarah_avg=("Sarah Time Score", "mean"),
)
_bin_counts, _bin_colors, _bin_hover = [], [], []
for _b in _bins:
    if _b in _lead_stats.index:
        _r = _lead_stats.loc[_b]
        _cnt = int(_r["count"])
        _m, _s = _r["michael_avg"], _r["sarah_avg"]
        _diff = (_m - _s) if (pd.notna(_m) and pd.notna(_s)) else None
        _leader = "Michael" if (_diff is not None and _diff > 0) else ("Sarah" if (_diff is not None and _diff < 0) else "Tied")
        _m_txt = f"{_m:,.0f}" if pd.notna(_m) else "—"
        _s_txt = f"{_s:,.0f}" if pd.notna(_s) else "—"
        _hover = (f"Appeared {_cnt}&times;<br>Michael avg: {_m_txt}<br>"
                  f"Sarah avg: {_s_txt}<br><b>{_leader}</b> ahead")
    else:
        _cnt, _diff, _hover = 0, None, "No rounds yet"
    _bin_counts.append(_cnt)
    _bin_colors.append(_bar_color(_diff))
    _bin_hover.append(_hover)

# Michael added first so his slice sits at the bottom of the percentage
# stack, Sarah last so hers sits on top — same order the standalone
# outcome-share chart used to use.
fig_single = go.Figure()
fig_single.add_trace(go.Bar(
    x=_bins, y=(_by["michael"] / _by["_n"] * 100).round(1), customdata=_cd, name="Michael",
    marker=dict(color=COLOR_M, line=dict(width=0.6, color="#ffffff")),
    hoverlabel=dict(bgcolor="#ffffff", bordercolor=COLOR_M, font=dict(family="Inter, sans-serif", size=12, color="#222222")),
    hovertemplate=f"{_hover_x}<br>Michael closer: %{{y:.1f}}%<br>%{{customdata[1]}}<extra></extra>"
))
fig_single.add_trace(go.Bar(
    x=_bins, y=(_by["tie"] / _by["_n"] * 100).round(1), customdata=_cd, name="Tie",
    marker=dict(color="#a7a59a", line=dict(width=0.6, color="#ffffff")),
    hoverlabel=dict(bgcolor="#ffffff", bordercolor="#a7a59a", font=dict(family="Inter, sans-serif", size=12, color="#222222")),
    hovertemplate=f"{_hover_x}<br>Tie: %{{y:.1f}}%<br>%{{customdata[1]}}<extra></extra>"
))
fig_single.add_trace(go.Bar(
    x=_bins, y=(_by["sarah"] / _by["_n"] * 100).round(1), customdata=_cd, name="Sarah",
    marker=dict(color=COLOR_S, line=dict(width=0.6, color="#ffffff")),
    hoverlabel=dict(bgcolor="#ffffff", bordercolor=COLOR_S, font=dict(family="Inter, sans-serif", size=12, color="#222222")),
    hovertemplate=f"{_hover_x}<br>Sarah closer: %{{y:.1f}}%<br>%{{customdata[1]}}<extra></extra>"
))
# The count region gets 200 units of headroom above the 100% line — twice
# the 0-100 span of the percentage region below it — so the top (count)
# region takes up 2/3 of the plot's height and the bottom (percentage)
# region the other 1/3, regardless of how big the largest count happens to
# be. This bar is bound to its own second y-axis (real "times appeared"
# units, no rescaling needed) rather than sharing the primary one — besides
# being the more honest axis to hover/read values off of, Plotly only
# actually draws a y-axis that at least one trace is bound to, so this is
# also what makes that second axis appear at all.
_max_count = max(_bin_counts) if _bin_counts else 1
_HEADROOM = 200
# Where the second y-axis's own zero has to sit so that it lines up with
# the primary axis's 100% mark, and _max_count lines up with the very top
# of the chart — i.e. so a bar of height _max_count on this axis reaches
# exactly as high as a bar of height 100 would on the primary one.
_bottom_frac = 100 / (100 + _HEADROOM)
_y2_min = _bottom_frac * _max_count / (_bottom_frac - 1)

fig_single.add_trace(go.Bar(
    x=_bins, y=_bin_counts, yaxis="y2", name="Times Appeared",
    marker=dict(color=_bin_colors, line=dict(width=0.6, color="#ffffff")),
    hovertext=_bin_hover, hoverinfo="text",
    hoverlabel=dict(bgcolor="#ffffff", bordercolor=_bin_colors, font=dict(family="Inter, sans-serif", size=12, color="#222222")),
))
# A solid line right at the seam makes the "resting on top of" boundary
# explicit instead of leaving it to be inferred from the color change.
fig_single.add_hline(y=100, line=dict(color="#333333", width=1.3))
_count_ticks = sorted(set(round(v) for v in [0, _max_count / 2, _max_count]))
fig_single.update_layout(**PLOT_THEME)
fig_single.update_layout(
    xaxis_title=_x_label,
    # Standard Plotly axis titles, each with automargin so the reserved
    # margin always grows to fit the title text rather than relying on a
    # fixed guess that can end up too tight and get the label clipped.
    yaxis=dict(range=[0, 100 + _HEADROOM], title="% of Rounds", automargin=True,
               showgrid=True, gridcolor="#f0f0ec",
               tickvals=[0, 20, 40, 60, 80, 100], ticktext=["0%", "20%", "40%", "60%", "80%", "100%"]),
    yaxis2=dict(overlaying="y", side="right", range=[_y2_min, _max_count], title="Times Appeared",
                automargin=True, showgrid=False, zeroline=False,
                tickvals=_count_ticks, ticktext=[str(v) for v in _count_ticks]),
    xaxis=dict(tickmode='linear', dtick=10 if _bucket == 1 else max(_bucket, 5), showgrid=False),
    barmode="stack",
    showlegend=False,
    bargap=0.15 if _bucket > 1 else 0.05,
    height=420,
    margin=dict(l=70, r=70, t=20, b=50),
)
# Same card treatment as the leaderboard below — light background, soft
# border/shadow, a little hover "pop" — so the two sit together as one
# consistent design instead of a styled grid next to a bare white chart.
with st.container(key="year_dist_chart_card"):
    st.plotly_chart(fig_single, use_container_width=True, theme=None)

# ==========================================
# YEAR GRID — 13 decades (rows) x 10 years-within-decade (columns) = every
# year from 1900 to 2029, one cell each. Each cell shows how many rounds have
# actually landed on that year, and the two players' average Time Score for
# it; the cell's background and border shade toward whoever's ahead there,
# darker the bigger that lead is. A wide cell to the left of each row rolls
# up its decade; a tall cell above each column rolls up every year ending in
# that digit; the corner where those two headers would otherwise leave a dead
# square instead rolls up literally everything.
# ==========================================
st.markdown('<div class="section-heading">Year-by-Year Leaderboard</div>', unsafe_allow_html=True)

_GRID_START = 1900
_DECADE_ROWS = 13
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
    .year-grid-card, .st-key-year_dist_chart_card { max-width:1300px; margin:0 auto 35px auto !important; padding:24px 24px 20px 24px; background:#fbfbf9; border:1px solid #e7e5dd; border-radius:18px; box-shadow:0 6px 22px rgba(0,0,0,0.07); box-sizing:border-box; }
    /* The combined distribution/outcome chart above gets the same card
       treatment as this grid — light background, soft border/shadow — plus
       a gentle hover "pop" of its own, echoing the grid cells' hover-scale
       without literally copying a per-tile effect onto one big chart. */
    .st-key-year_dist_chart_card { transition:transform .15s ease, box-shadow .15s ease; }
    .st-key-year_dist_chart_card:hover { transform:scale(1.01); box-shadow:0 10px 28px rgba(0,0,0,0.12); }
    /* Decade column is a fixed width rather than an "Nfr" share: the year
       columns' own content (two side-by-side score pills) has a real minimum
       width the grid honors first, which was quietly capping how much wider
       a merely-proportional decade track could actually end up — pinning it
       in px sidesteps that fight entirely and guarantees the ~2x width. The
       header row (digit + corner cells) is pinned to that same 190px, so it
       ends up exactly as tall as the decade cells are wide. */
    .year-grid { display:grid; grid-template-columns:190px repeat(10, minmax(90px, 1fr)); grid-template-rows:190px repeat(13, auto); gap:6px; width:100%; }
    .year-cell { display:flex; flex-direction:column; align-items:center; justify-content:center; border-radius:9px; padding:8px 3px 7px 3px; text-align:center; box-sizing:border-box; border:6.25px solid; transition:transform .12s ease; cursor:default; }
    .year-cell:hover { transform:scale(1.08); z-index:3; box-shadow:0 4px 14px rgba(0,0,0,0.25); }
    .yc-year { font-family:'Poppins',sans-serif; font-weight:800; font-size:14px; line-height:1.1; }
    .yc-count { font-family:'Inter',sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; margin-top:1px; opacity:.8; }
    .yc-scores { display:flex; justify-content:center; gap:4px; margin-top:5px; }
    .yc-m, .yc-s { font-family:'Inter',sans-serif; font-size:10px; font-weight:800; padding:1px 5px; border-radius:5px; background:rgba(255,255,255,0.6); }
    .yc-m { color:#221e8f; }
    .yc-s { color:#8a005c; }
    /* The decade cell is the "Shift key" of its row: a fixed 190px-wide
       track (about double a year cell's own width), its own rounder
       corners, a bolder/bigger label carrying a small calendar mark, and
       bigger score badges — several cues stacked together so it unmistakably
       reads as the row's label rather than just another tile. */
    .decade-cell { border-radius:14px; }
    .decade-cell .yc-year { font-size:17px; font-weight:900; letter-spacing:.3px; }
    .decade-cell .yc-m, .decade-cell .yc-s { font-size:11px; padding:2px 6px; }
    /* Digit cell is the decade cell's counterpart turned 90°: same rounder
       corners and bold label, but tall (190px, via the header row track)
       rather than wide, rolling up "every year ending in N" above its
       column. The corner cell is both at once — a full 190x190 square —
       since it's where those two headers would otherwise leave a dead
       square, rolled up into a grand total across every year on the board. */
    .digit-cell, .corner-cell { border-radius:14px; }
    .digit-cell .yc-year, .corner-cell .yc-year { font-size:17px; font-weight:900; letter-spacing:.3px; }
    .digit-cell .yc-m, .digit-cell .yc-s, .corner-cell .yc-m, .corner-cell .yc-s { font-size:11px; padding:2px 6px; }
    .corner-cell .yc-year { font-size:15px; }
    /* Digit cells are only ~90px wide, too narrow for the Michael/Sarah score
       pills to sit side by side without crowding — stack them instead. */
    .digit-cell .yc-scores { flex-direction:column; gap:3px; }
    .digit-cell .yc-m, .digit-cell .yc-s { width:100%; box-sizing:border-box; }
    @media (max-width: 900px) {
        .year-grid { grid-template-columns:120px repeat(4, minmax(60px, 1fr)); grid-template-rows:120px repeat(13, auto); }
    }
</style>
""", unsafe_allow_html=True)
st.markdown(f'<div class="year-grid-card"><div class="year-grid">{"".join(_cells_html)}</div></div>', unsafe_allow_html=True)

# --- Bin edges: 10-year bins from 1900 to 2025 ---
bin_edges = list(range(1900, 2026, 10))
if bin_edges[-1] != 2025:
    bin_edges = []
    start = 1900
    while start < 2025:
        bin_edges.append(start)
        start += 10
    bin_edges.append(2025)

counts_year, _ = np.histogram(year_vals, bins=bin_edges)
counts_michael, _ = np.histogram(michael_vals, bins=bin_edges)
counts_sarah, _ = np.histogram(sarah_vals, bins=bin_edges)

bin_labels = []
for i in range(len(bin_edges)-1):
    start = bin_edges[i]
    end = bin_edges[i+1] - 1 if i < len(bin_edges)-2 else bin_edges[i+1]
    if i == len(bin_edges)-2:
        end = bin_edges[i+1]
    bin_labels.append(f"{start}s" if (end - start) == 9 else f"{start}-{end}")

max_count = max(counts_year.max() if counts_year.size else 0,
                counts_michael.max() if counts_michael.size else 0,
                counts_sarah.max() if counts_sarah.size else 0)

y_dtick = 1 if max_count <= 10 else math.ceil(max_count / 10)

# ==========================================
# 1. FREQUENCY HISTOGRAMS (COMBINED)
# ==========================================
st.markdown('<div class="section-heading">Frequency Distribution by Era</div>', unsafe_allow_html=True)

fig_hist = go.Figure()
fig_hist.add_trace(go.Bar(x=bin_labels, y=counts_year, name="Actual Year", marker_color=COLOR_ACTUAL, marker_line=dict(width=1, color="white")))
fig_hist.add_trace(go.Bar(x=bin_labels, y=counts_michael, name="Michael's Guesses", marker_color=COLOR_M, marker_line=dict(width=1, color="white")))
fig_hist.add_trace(go.Bar(x=bin_labels, y=counts_sarah, name="Sarah's Guesses", marker_color=COLOR_S, marker_line=dict(width=1, color="white")))

fig_hist.update_layout(**PLOT_THEME)
fig_hist.update_layout(
    title="Volume of Photos vs. Guesses per Decade",
    barmode='group',
    bargap=0.15,
    bargroupgap=0.05,
    xaxis_title="Decade",
    yaxis_title="Count",
    yaxis=dict(range=[0, max_count * 1.05], tick0=0, dtick=y_dtick)
)
st.plotly_chart(fig_hist, use_container_width=True, theme=None)

st.markdown('<div class="section-heading">Guess Accuracy Matrix</div>', unsafe_allow_html=True)

df_scatter = data[[col_year, col_michael, col_sarah]].copy()
df_scatter[col_year] = pd.to_numeric(df_scatter[col_year], errors="coerce")
df_scatter[col_michael] = pd.to_numeric(df_scatter[col_michael], errors="coerce")
df_scatter[col_sarah] = pd.to_numeric(df_scatter[col_sarah], errors="coerce")
df_scatter = df_scatter.dropna()

x_year = df_scatter[col_year].astype(float).values
y_michael = df_scatter[col_michael].astype(float).values
y_sarah = df_scatter[col_sarah].astype(float).values

min_val = min(x_year.min(), y_michael.min(), y_sarah.min()) - 5
max_val = max(x_year.max(), y_michael.max(), y_sarah.max()) + 5
line_x = np.linspace(min_val, max_val, 200)

fig_scatter = go.Figure()
fig_scatter.add_trace(go.Scatter(
    x=line_x, y=line_x, mode="lines", name="Perfect Guess (y = x)",
    line=dict(color="#7f8c8d", width=2, dash="dash"),
    hoverinfo="skip"
))
fig_scatter.add_trace(go.Scatter(
    x=x_year, y=y_michael, mode="markers", name="Michael",
    marker=dict(size=8, color=COLOR_M, opacity=0.8, line=dict(width=1, color="white")),
    hovertemplate="<b>Actual:</b> %{x}<br><b>Guessed:</b> %{y}<extra>Michael</extra>"
))
fig_scatter.add_trace(go.Scatter(
    x=x_year, y=y_sarah, mode="markers", name="Sarah",
    marker=dict(size=8, color=COLOR_S, opacity=0.8, line=dict(width=1, color="white")),
    hovertemplate="<b>Actual:</b> %{x}<br><b>Guessed:</b> %{y}<extra>Sarah</extra>"
))

fig_scatter.update_layout(**PLOT_THEME)
fig_scatter.update_layout(
    title="Time Guessed vs Actual Year",
    xaxis_title="Actual Year",
    yaxis_title="Guessed Year",
    height=600,
)
st.plotly_chart(fig_scatter, use_container_width=True, theme=None)

st.markdown('<div class="section-heading">Directional Bias by Decade</div>', unsafe_allow_html=True)

df_box = df_scatter.copy()
df_box["decade"] = (df_box[col_year] // 10 * 10).astype(int)
df_box["michael_err"] = df_box[col_michael] - df_box[col_year]
df_box["sarah_err"] = df_box[col_sarah] - df_box[col_year]

decades = sorted(df_box["decade"].unique())

fig_box = go.Figure()

for d in decades:
    is_first = bool(d == decades[0])
    fig_box.add_trace(go.Box(
        y=df_box.loc[df_box["decade"] == d, "michael_err"],
        x=[f"{d}s"] * len(df_box.loc[df_box["decade"] == d]),
        name="Michael",
        marker_color=COLOR_M,
        boxmean="sd",
        legendgroup="Michael",
        showlegend=is_first
    ))
    fig_box.add_trace(go.Box(
        y=df_box.loc[df_box["decade"] == d, "sarah_err"],
        x=[f"{d}s"] * len(df_box.loc[df_box["decade"] == d]),
        name="Sarah",
        marker_color=COLOR_S,
        boxmean="sd",
        legendgroup="Sarah",
        showlegend=is_first
    ))

all_errors = pd.concat([df_box["michael_err"], df_box["sarah_err"]])
max_abs = max(abs(all_errors.min()), abs(all_errors.max())) + 5

fig_box.update_layout(**PLOT_THEME)
fig_box.update_layout(
    title="Signed Error Distribution (+ Overestimated / - Underestimated)",
    xaxis_title="Actual Decade",
    yaxis_title="Error (Years)",
    boxmode="group",
    boxgap=0.05,
    boxgroupgap=0.2,
    yaxis=dict(
        range=[-max_abs, max_abs],
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor="#c0392b"
    ),
    height=500
)
st.plotly_chart(fig_box, use_container_width=True, theme=None)

st.markdown('<div class="section-heading">Decade Confusion Matrices</div>', unsafe_allow_html=True)

def count_table(guess_col, actual_col):
    df_temp = df_box.copy()
    df_temp["guess_decade"] = (df_temp[guess_col] // 10 * 10).astype(int)
    df_temp["actual_decade"] = (df_temp[actual_col] // 10 * 10).astype(int)
    table = pd.crosstab(df_temp["guess_decade"], df_temp["actual_decade"])
    decades_all = sorted(df_box["decade"].unique())
    table = table.reindex(index=decades_all, columns=decades_all, fill_value=0)
    return table

michael_counts = count_table(col_michael, col_year)
sarah_counts = count_table(col_sarah, col_year)

def heatmap_fig(table, title, colorscale):
    decades_all = list(table.index)
    
    fig = go.Figure(data=go.Heatmap(
        z=table.values,
        x=decades_all,
        y=decades_all,
        text=table.values,
        texttemplate="%{text}",
        textfont=dict(color="#000000", size=10),
        colorscale=colorscale,
        showscale=False,
        xgap=2,
        ygap=2,
        hovertemplate="<b>Actual:</b> %{x}s<br><b>Guessed:</b> %{y}s<br><b>Count:</b> %{z}<extra></extra>"
    ))
    
    # Range padding for visibility
    min_d = min(decades_all) - 5
    max_d = max(decades_all) + 5
    
    fig.update_layout(**PLOT_THEME)
    fig.update_layout(
        title=dict(text=title, font=dict(family="Poppins", size=18, color="#000")),
        xaxis_title="Actual Decade",
        yaxis_title="Guessed Decade",
        height=600, # Increased height to allow for square ratio in column
        margin=dict(l=60, r=30, t=80, b=60),
        # Equal length axes
        xaxis=dict(
            tickmode='array', 
            tickvals=decades_all, 
            ticktext=[f"{d}s" for d in decades_all],
            range=[min_d, max_d],
            constrain='domain'
        ),
        yaxis=dict(
            tickmode='array', 
            tickvals=decades_all, 
            ticktext=[f"{d}s" for d in decades_all],
            scaleanchor="x", 
            scaleratio=1,
            range=[min_d, max_d],
            constrain='domain'
        )
    )
    return fig

col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(heatmap_fig(michael_counts, "Michael's Guesses", colorscale="Blues"), use_container_width=True, theme=None)

with col2:
    st.plotly_chart(heatmap_fig(sarah_counts, "Sarah's Guesses", colorscale="PuRd"), use_container_width=True, theme=None)