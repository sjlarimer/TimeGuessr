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
    <div class="page-header" style="text-align: center; width: max-content; max-width: 95%; margin: 20px auto 40px auto; border-bottom: 4px double #ccc; padding-bottom: 10px;">
        <h1 class="page-title" style="font-family: 'Poppins', sans-serif; font-weight: 900; font-size: 48px; color: #111; letter-spacing: -1px; margin: 0; text-transform: uppercase;">Timeline Analysis</h1>
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
# Per-year Time Score rollups and the "who's ahead, by how much" colour logic
# derived from them, feeding the distribution chart below. (The year-by-year
# leaderboard grid that used to live here has moved to its own Year-Go page.)
# ==========================================
def _hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

_M_RGB = _hex_to_rgb(COLOR_M)
_S_RGB = _hex_to_rgb(COLOR_S)
_LEAD_CAP = 1500  # avg Time Score gap (points, out of 5000) treated as a "landslide" -> full-saturation tile

def _bar_color(diff):
    """Blend the leader's color into white for the count-overlay bars in the
    distribution chart below — a punchier blend than a tile would want, since
    a bar doesn't need to stay pale for text to sit on top of it, so it leans
    much further into the leader's actual color and reads far more vividly at
    a glance."""
    if diff is None or pd.isna(diff) or diff == 0:
        return "#c9c7bc"
    # Diverging scale with a neutral gray midpoint: an even matchup is gray,
    # sliding smoothly to full Michael blue / Sarah magenta at the cap.
    leader_rgb = _M_RGB if diff > 0 else _S_RGB
    blend = min(abs(diff) / _LEAD_CAP, 1.0)
    gray = (201, 199, 188)
    r = round(gray[0] * (1 - blend) + leader_rgb[0] * blend)
    g = round(gray[1] * (1 - blend) + leader_rgb[1] * blend)
    b = round(gray[2] * (1 - blend) + leader_rgb[2] * blend)
    return f"rgb({r},{g},{b})"

_yr_df = data[[col_year, "Michael Time Score", "Sarah Time Score"]].copy()
for _c in _yr_df.columns:
    _yr_df[_c] = pd.to_numeric(_yr_df[_c], errors="coerce")
# Fall back to the (Min)+(Max) midpoint when the exact Time Score isn't known
# (early days only recorded the emoji-tier bounds) — same convention as
# Daily/Year-Go, so a round contributes a best-guess value to the per-bin
# average below instead of silently dropping out of it (pandas' .mean()
# skips NaN, which would otherwise exclude incomplete rounds here while
# Daily/Year-Go count them).
for _p in ["Michael", "Sarah"]:
    _base, _lo, _hi = f"{_p} Time Score", f"{_p} Time Score (Min)", f"{_p} Time Score (Max)"
    if _lo in data.columns and _hi in data.columns:
        _est = (pd.to_numeric(data[_lo], errors="coerce") + pd.to_numeric(data[_hi], errors="coerce")) / 2
        _yr_df[_base] = _yr_df[_base].where(_yr_df[_base].notna(), _est)
_yr_df = _yr_df.dropna(subset=[col_year])
_yr_df[col_year] = _yr_df[col_year].astype(int)

# ==========================================
# ACTUAL YEAR DISTRIBUTION — a bar per year whose height is that year's
# appearance count and whose shade leans toward whoever's ahead there on
# average Time Score, more vividly the bigger the lead.
# ==========================================
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

st.markdown("""
<style>
    /* Sidebar pill controls (same look as the Locations page) */
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
    [data-testid="stSidebar"] button[kind="primary"] {
        background-color: #3a3935 !important; color: #eae8dc !important;
        border-color: #3a3935 !important; border-radius: 20px !important; font-weight: 600 !important;
    }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
    [data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #d9d7cc !important; color: #696761 !important;
        border-color: #d9d7cc !important; border-radius: 20px !important; font-weight: 500 !important;
    }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #c8c6bb !important; color: #3a3935 !important; border-color: #8f8d85 !important;
    }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] *,
    [data-testid="stSidebar"] button[kind="primary"] * { color: #eae8dc !important; }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] *,
    [data-testid="stSidebar"] button[kind="secondary"] * { color: #696761 !important; }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover *,
    [data-testid="stSidebar"] button[kind="secondary"]:hover * { color: #3a3935 !important; }
</style>
""", unsafe_allow_html=True)

def _pill_group(state_key, default, options, key_prefix, per_row=2):
    """Segmented pill-button control (same helper as the Locations page).
    `options` is a list of (button_label, stored_value); returns the selected value."""
    cur = st.session_state.get(state_key, default)
    cols = []
    for _ in range(0, len(options), per_row):
        cols.extend(st.columns(per_row))
    for col, (label, value) in zip(cols, options):
        with col:
            st.button(label, key=f"{key_prefix}_{value}", use_container_width=True,
                      type="primary" if cur == value else "secondary",
                      on_click=lambda v=value: st.session_state.__setitem__(state_key, v))
    return cur

with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>Settings</h2>", unsafe_allow_html=True)
    # For now every mode shows the same chart.
    map_metric = _pill_group(
        'tl_metric', 'Count',
        [("Count", "Count"), ("Compare", "Comparison"), ("Michael", "Michael"), ("Sarah", "Sarah")],
        'tl_mm')
    _bucket = st.select_slider("Year Bucket Size", options=[1, 2, 5, 10, 20, 25, 50], value=1, key="outcome_bucket_size")
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
def _outline_color(diff):
    """Solid outline in the leader's color (neutral gray when tied / unknown)."""
    if diff is None or pd.isna(diff) or diff == 0:
        return "#8f8d85"
    return COLOR_M if diff > 0 else COLOR_S

_bin_counts, _bin_colors, _bin_hover, _bin_outlines = [], [], [], []
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
    _bin_outlines.append(_outline_color(_diff))
    _bin_hover.append(_hover)

def _with_year(texts):
    # Bold year (or year range, when bucketed) as the first line of each hover box.
    return [f"<b>{b if _bucket == 1 else f'{b}–{b + _bucket - 1}'}</b><br>{t}" for b, t in zip(_bins, texts)]

fig_single = go.Figure()
_max_count = max(_bin_counts) if _bin_counts else 1
if map_metric in ("Michael", "Sarah"):
    # Player modes: bar height is that player's average Time Score for the
    # bin, shaded by how many rounds back it (lighter = fewer, darker = more).
    _pc = COLOR_M if map_metric == "Michael" else COLOR_S
    _avg_col = "michael_avg" if map_metric == "Michael" else "sarah_avg"
    _avgs = [(_lead_stats.loc[b, _avg_col] if b in _lead_stats.index else np.nan) for b in _bins]
    _avgs = [None if pd.isna(a) else float(a) for a in _avgs]
    _pr, _pg, _pb = _hex_to_rgb(_pc)
    _light = f"rgb({round(255 * .75 + _pr * .25)},{round(255 * .75 + _pg * .25)},{round(255 * .75 + _pb * .25)})"
    _p_hover = [f"Appeared {c}&times;<br>{map_metric} avg: {a:,.0f}" if a is not None else "No rounds yet"
                for c, a in zip(_bin_counts, _avgs)]
    fig_single.add_trace(go.Bar(
        x=_bins, y=_avgs, name=f"{map_metric} Avg Score",
        marker=dict(color=_bin_counts, colorscale=[[0, _light], [1, _pc]], cmin=0, cmax=_max_count,
                    line=dict(width=0.6, color="#ffffff"),
                    colorbar=dict(title="Times Appeared", thickness=12, len=0.9)),
        hovertext=_with_year(_p_hover), hoverinfo="text",
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=_pc, font=dict(family="Inter, sans-serif", size=12, color="#222222")),
    ))
    _y_range, _y_title = [0, 5000], "Average Points"
elif map_metric == "Comparison":
    # Diverging: bar height is Michael's avg Time Score minus Sarah's for the
    # bin (up = Michael ahead, down = Sarah ahead). Shade fades with fewer
    # rounds so thinly sampled bins read as less certain.
    _gaps, _g_colors, _g_hover, _g_outlines = [], [], [], []
    for _b, _c in zip(_bins, _bin_counts):
        _g = None
        if _b in _lead_stats.index:
            _mm, _ss = _lead_stats.loc[_b, "michael_avg"], _lead_stats.loc[_b, "sarah_avg"]
            if pd.notna(_mm) and pd.notna(_ss):
                _g = float(_mm - _ss)
        _gaps.append(_g)
        _g_outlines.append(_outline_color(_g))
        if _g is None:
            _g_colors.append("#c9c7bc")
            _g_hover.append("No rounds yet")
            continue
        _lr, _lg, _lb = _M_RGB if _g >= 0 else _S_RGB
        _t = 0.3 + 0.7 * (_c / _max_count if _max_count else 0)
        _g_colors.append(f"rgb({round(217 * (1 - _t) + _lr * _t)},{round(215 * (1 - _t) + _lg * _t)},{round(204 * (1 - _t) + _lb * _t)})")
        _who = "Michael" if _g > 0 else ("Sarah" if _g < 0 else "Tied")
        _g_hover.append(f"Appeared {_c}&times;<br>Michael avg: {_mm:,.0f}<br>Sarah avg: {_ss:,.0f}<br>"
                        f"<b>{_who}</b> ahead by {abs(_g):,.0f}")
    _gmax = max([abs(g) for g in _gaps if g is not None] or [1]) * 1.1
    fig_single.add_trace(go.Bar(
        x=_bins, y=_gaps, name="Score Gap",
        marker=dict(color=_g_colors, line=dict(width=1.2 if _bucket > 1 else 0.8, color=_g_outlines)),
        hovertext=_with_year(_g_hover), hoverinfo="text",
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=_g_colors, font=dict(family="Inter, sans-serif", size=12, color="#222222")),
    ))
    fig_single.add_hline(y=0, line=dict(color="#333333", width=1.3))
    _y_range, _y_title = [-_gmax, _gmax], "Avg Points: Michael − Sarah"
else:
    fig_single.add_trace(go.Bar(
        x=_bins, y=_bin_counts, name="Times Appeared",
        marker=dict(color=_bin_colors, line=dict(width=1.2 if _bucket > 1 else 0.8, color=_bin_outlines)),
        hovertext=_with_year(_bin_hover), hoverinfo="text",
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=_bin_colors, font=dict(family="Inter, sans-serif", size=12, color="#222222")),
    ))
    _y_range, _y_title = [0, _max_count * 1.05], "Times Appeared"
fig_single.update_layout(**PLOT_THEME)
fig_single.update_layout(
    xaxis_title=_x_label,
    yaxis=dict(range=_y_range, title=_y_title, automargin=True,
               showgrid=True, gridcolor="#f0f0ec"),
    xaxis=dict(tickmode='linear', dtick=10 if _bucket == 1 else max(_bucket, 5), showgrid=False),
    showlegend=False,
    bargap=0.15 if _bucket > 1 else 0.05,
    height=420,
    margin=dict(l=70, r=30, t=20, b=50),
)
# Recolor to match the Comparison page's chart-card convention (warm-beige
# paper/plot background, Poppins font, muted grid/axis colors) instead of
# this page's usual white-card PLOT_THEME, so the plot reads as part of the
# card beneath it rather than a white rectangle sitting on top of it.
fig_single.update_layout(
    paper_bgcolor="#eae8dc",
    plot_bgcolor="#d9d7cc",
    font=dict(family="Poppins, Arial, sans-serif", color="#696761"),
)
fig_single.update_xaxes(gridcolor="#bdbbb1", linecolor="#8f8d85", tickcolor="#8f8d85",
                         tickfont=dict(color="#696761"), title_font=dict(color="#696761"))
fig_single.update_yaxes(gridcolor="#bdbbb1", linecolor="#8f8d85", tickcolor="#8f8d85",
                         tickfont=dict(color="#696761"), title_font=dict(color="#696761"))
# Same flat chart-card treatment as the Comparison page's main chart box —
# warm-beige card with a small uppercase title inside it, no shadow/hover.
with st.container(key="year_dist_chart_card"):
    st.markdown(
        '<h4 style="margin:4px 0 0 0;color:#696761;font-size:16px;'
        'text-transform:uppercase;letter-spacing:1px;">Actual Year Distribution</h4>',
        unsafe_allow_html=True
    )
    st.plotly_chart(fig_single, use_container_width=True, theme=None)

st.markdown("""
<style>
    .st-key-conf_matrix_michael_card, .st-key-conf_matrix_sarah_card, .st-key-conf_matrix_michael_year_card, .st-key-conf_matrix_sarah_year_card { margin:0 auto 35px auto !important; padding:20px 20px 12px 20px; background:#fbfbf9; border:1px solid #e7e5dd; border-radius:18px; box-shadow:0 6px 22px rgba(0,0,0,0.07); box-sizing:border-box; }
    /* The four confusion matrix cards further down get the same card
       treatment — light background, soft border/shadow — plus a gentle
       hover "pop" of their own. */
    .st-key-conf_matrix_michael_card, .st-key-conf_matrix_sarah_card, .st-key-conf_matrix_michael_year_card, .st-key-conf_matrix_sarah_year_card { transition:transform .15s ease, box-shadow .15s ease; }
    .st-key-conf_matrix_michael_card:hover, .st-key-conf_matrix_sarah_card:hover, .st-key-conf_matrix_michael_year_card:hover, .st-key-conf_matrix_sarah_year_card:hover { transform:scale(1.01); box-shadow:0 10px 28px rgba(0,0,0,0.12); }

    /* Top chart card — matches the Comparison page's main chart box: flat
       warm-beige card, thin border, no shadow/hover pop. */
    .st-key-year_dist_chart_card, .st-key-confusion_chart_card { margin:0 auto 35px auto !important; max-width:1300px; padding:15px; background-color:#eae8dc; border-radius:12px; border:1px solid #d9d7cc; box-sizing:border-box; }
    .st-key-year_dist_chart_card div[data-testid="stPlotlyChart"], .st-key-confusion_chart_card div[data-testid="stPlotlyChart"] { border:none !important; margin-top:0 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONFUSION MATRICES — for each player, how often a guess landing on X was
# actually a photo from Y: rows are what they guessed, columns are what it
# really was, so the diagonal is every exactly-correct guess. Colored white
# -> that player's own blue/magenta instead of a generic Plotly colorscale.
# Two granularities, year above decade: the year pair is a much finer (and
# much sparser) version of the same idea, so it goes first with the coarser,
# denser decade pair beneath it for contrast. Self-contained (builds its own
# frame straight from `data`) rather than reusing df_box from the section
# below, since that's built later in the script and this now sits above it
# on the page.
# ==========================================
_conf_df = data[[col_year, col_michael, col_sarah]].copy()
for _c in [col_year, col_michael, col_sarah]:
    _conf_df[_c] = pd.to_numeric(_conf_df[_c], errors="coerce")
_conf_df = _conf_df.dropna()

_DIAGONAL_GOLD = "#c9a227"

def _gamma_colorscale(hex_color, gamma=0.45, steps=12, base=(234, 232, 220)):
    """White -> hex_color, but ramped by z**gamma (gamma<1) instead of a
    straight line. The year-level grid is sparse enough that most nonzero
    cells sit far below the single brightest outlier cell, so a plain linear
    scale leaves nearly the whole heatmap looking washed-out white — this
    front-loads the color ramp so low-but-nonzero counts already read as
    clearly shaded instead of only the rare high-count cell standing out."""
    r, g, b = _hex_to_rgb(hex_color)
    stops = []
    for i in range(steps + 1):
        frac = i / steps
        blend = frac ** gamma
        cr = round(base[0] * (1 - blend) + r * blend)
        cg = round(base[1] * (1 - blend) + g * blend)
        cb = round(base[2] * (1 - blend) + b * blend)
        stops.append([frac, f"rgb({cr},{cg},{cb})"])
    return stops

_CONF_YEAR_MAX = int(_conf_df[col_year].max())
_CONF_MAX_LABELS_DETAIL = 14  # up to this many rows/cols: show cell counts + gold outlines

def _bucket_label(v, bucket, short=False):
    """Readable name for the bucket starting at year v: '1994' (size 1),
    '1990s' (size 10), else '1975–1999'. `short` is the axis-tick form, which
    for the narrow 2/5-year buckets is just the start year to keep ticks legible
    (hover always shows the full range). The last bucket stops at the newest
    year in the data rather than claiming years that don't exist."""
    end = min(v + bucket - 1, _CONF_YEAR_MAX)
    if bucket == 1 or end == v:
        return str(v)
    if short and bucket < 10:
        return str(v)
    if bucket == 10:
        return f"{v}s"
    return f"{v}–{end}"

def _lead_colorscale(gamma, steps=20, mid=(201, 199, 188)):
    """Sarah magenta <- gray -> Michael blue (same gray-midpoint lead scale as
    the Actual Year Distribution bars), ramped by |x|**gamma."""
    stops = []
    for i in range(steps + 1):
        pos = i / steps
        f = (pos - 0.5) * 2
        blend = abs(f) ** gamma
        rgb = _M_RGB if f > 0 else _S_RGB
        stops.append([pos, "rgb(" + ",".join(str(round(mid[k] * (1 - blend) + rgb[k] * blend)) for k in range(3)) + ")"])
    return stops

def _confusion_heatmap(table, title, leader_color, bucket=1, height=460, lead=None):
    """One matrix for every Year Bucket Size, adapting to how big the grid is:
      - small grids (<=14 buckets): big cells, so show the counts in them and
        outline each correct (diagonal) bucket in gold.
      - large grids: cells are too small for text, so shade with a gamma ramp
        (so sparse low counts still read) and draw a thin gold diagonal line
        marking 'guess == actual' instead.
    Axis ticks are thinned to round years for the narrow buckets.
    With `lead` (a Michael-minus-Sarah table on the same grid), `table` is the
    pooled count and each cell is colored by who guessed it more instead."""
    labels = list(table.index)
    n = len(labels)
    detail = n <= _CONF_MAX_LABELS_DETAIL
    z = table.values
    zmax = z.max() if z.size else 1
    _scale = [[0, "#eae8dc"], [1, leader_color]] if detail else _gamma_colorscale(leader_color)
    def _cell_hover(i, j):
        if lead is None:
            return f"<b>Count:</b> {z[i][j]}"
        d = lead.values[i][j]
        return (f"<b>Count:</b> {z[i][j]}<br>Michael: {(z[i][j] + d) // 2} · Sarah: {(z[i][j] - d) // 2}")
    hover = [[f"<b>Actual:</b> {_bucket_label(x, bucket)}<br><b>Guessed:</b> {_bucket_label(y, bucket)}"
              f"<br>{_cell_hover(i, j)}" for j, x in enumerate(labels)] for i, y in enumerate(labels)]
    fig = go.Figure()
    if lead is not None:
        # Empty cells stay the card's beige; only cells with rounds get lead color.
        fig.add_trace(go.Heatmap(z=[[0] * n] * n, x=labels, y=labels, showscale=False, hoverinfo="skip",
                                 colorscale=[[0, "#eae8dc"], [1, "#eae8dc"]], xgap=0, ygap=0))
        dz = np.where(z > 0, lead.values, np.nan)
        dmax = np.nanmax(np.abs(dz)) if np.isfinite(dz).any() else 1
        dmax = dmax or 1
        _scale = _lead_colorscale(1.0 if detail else 0.5)
        _z_args = dict(z=dz, zmin=-dmax, zmax=dmax)
    else:
        _z_args = dict(z=z)
    fig.add_trace(go.Heatmap(
        **_z_args, x=labels, y=labels, colorscale=_scale, showscale=False, xgap=0, ygap=0,
        hovertext=hover, hoverinfo="text",
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=leader_color,
                        font=dict(family="Inter, sans-serif", size=12, color="#222222")),
    ))
    half = bucket / 2
    span = max((max(labels) - min(labels)) * 0.04 + 1, half)
    min_l, max_l = min(labels) - span, max(labels) + span
    tickvals = [l for l in labels if l % 10 == 0] if bucket < 10 else labels
    _ticktext = [_bucket_label(v, bucket, short=True) for v in tickvals]
    _unit = "Year" if bucket == 1 else ("Year (bucket start)" if bucket < 10 else "Year Bucket")
    fig.update_layout(**PLOT_THEME)
    fig.update_layout(
        title=dict(text=title, font=dict(family="Poppins, sans-serif", size=17, color="#000000")),
        xaxis_title=f"Actual {_unit}",
        yaxis_title=f"Guessed {_unit}",
        # No forced 1:1 aspect ratio: these heatmaps sit side by side in a
        # fairly narrow column, and locking the cells square shrank the
        # whole grid down to a tiny fraction of the available width, leaving
        # the tick labels and cell counts too cramped to read. Letting it
        # fill the column's actual width makes cells rectangular but
        # legible instead of square but tiny.
        height=height,
        # Left margin grows with the longest tick label so ranges like
        # '2000–2026' are never clipped.
        margin=dict(l=max(60, 30 + 7 * max(len(t) for t in _ticktext)), r=20, t=55, b=60 + (30 if max(len(t) for t in _ticktext) > 6 else 0)),
        xaxis=dict(tickmode='array', tickvals=tickvals, ticktext=_ticktext,
                   range=[min_l, max_l], showgrid=False),
        yaxis=dict(tickmode='array', tickvals=tickvals, ticktext=_ticktext,
                   range=[min_l, max_l], showgrid=False),
    )
    # Same warm-beige chart-card look as the Actual Year Distribution plot.
    fig.update_layout(paper_bgcolor="#eae8dc", plot_bgcolor="#d9d7cc",
                      font=dict(family="Poppins, Arial, sans-serif", color="#696761"),
                      title_font=dict(family="Poppins, Arial, sans-serif", size=15, color="#696761"))
    fig.update_xaxes(linecolor="#8f8d85", tickcolor="#8f8d85",
                     tickfont=dict(color="#696761"), title_font=dict(color="#696761"))
    fig.update_yaxes(linecolor="#8f8d85", tickcolor="#8f8d85",
                     tickfont=dict(color="#696761"), title_font=dict(color="#696761"))
    if detail:
        for _l in labels:
            fig.add_shape(type="rect", x0=_l - half, x1=_l + half, y0=_l - half, y1=_l + half,
                          line=dict(color=_DIAGONAL_GOLD, width=2.5), fillcolor="rgba(0,0,0,0)")
        # Counts as annotations (not heatmap text) so the text can flip to
        # white on dark cells; empty cells stay blank instead of a wall of 0s.
        for i, y in enumerate(labels):
            for j, x in enumerate(labels):
                if z[i][j]:
                    fig.add_annotation(x=x, y=y, text=str(z[i][j]), showarrow=False,
                                       font=dict(size=11, family="Inter, sans-serif",
                                                 color="#ffffff" if ((abs(lead.values[i][j]) / dmax) if lead is not None else (z[i][j] / zmax)) > 0.55 else "#000000"))
    else:
        fig.add_shape(type="line", x0=min(labels) - half, y0=min(labels) - half,
                      x1=max(labels) + half, y1=max(labels) + half,
                      line=dict(color=_DIAGONAL_GOLD, width=1.5, dash="dot"))
    return fig

def _confusion_table(guess_col, actual_col, bucket=1):
    _t = _conf_df.copy()
    if bucket > 1:
        _t["_g"] = (_t[guess_col] // bucket * bucket).astype(int)
        _t["_a"] = (_t[actual_col] // bucket * bucket).astype(int)
    else:
        _t["_g"] = _t[guess_col].round().astype(int)
        _t["_a"] = _t[actual_col].astype(int)
    # Every bucket from the earliest to the latest year seen on either axis,
    # so the grid has no gaps and no guess gets dropped for landing outside
    # the set of actual-year buckets.
    lo = min(_t["_g"].min(), _t["_a"].min())
    hi = max(_t["_g"].max(), _t["_a"].max())
    labels = list(range(int(lo), int(hi) + 1, bucket))
    table = pd.crosstab(_t["_g"], _t["_a"])
    return table.reindex(index=labels, columns=labels, fill_value=0)

_michael_conf = _confusion_table(col_michael, col_year, _bucket)
_sarah_conf = _confusion_table(col_sarah, col_year, _bucket)
# Same flat warm-beige card as the Actual Year Distribution chart: small
# uppercase title inside, both matrices side by side beneath it.
with st.container(key="confusion_chart_card"):
    st.markdown(
        '<h4 style="margin:4px 0 0 0;color:#696761;font-size:16px;'
        'text-transform:uppercase;letter-spacing:1px;">Confusion Matrices</h4>',
        unsafe_allow_html=True
    )
    # Count: both players pooled in neutral gray. Michael / Sarah: that player's
    # matrix alone, drawn larger. Comparison: pooled, colored by who guessed it more.
    if map_metric == "Count":
        _pooled = _michael_conf.add(_sarah_conf, fill_value=0).astype(int)
        st.plotly_chart(_confusion_heatmap(_pooled, "Both Players' Guesses", "#2f2e2b", _bucket, height=620),
                        use_container_width=True, theme=None)
    elif map_metric in ("Michael", "Sarah"):
        _solo, _solo_color = (_michael_conf, COLOR_M) if map_metric == "Michael" else (_sarah_conf, COLOR_S)
        st.plotly_chart(_confusion_heatmap(_solo, f"{map_metric}'s Guesses", _solo_color, _bucket, height=620),
                        use_container_width=True, theme=None)
    else:
        # Comparison: same pooled counts as Count, but each cell is colored by
        # who guessed it more (blue Michael, gray even, magenta Sarah).
        _pooled = _michael_conf.add(_sarah_conf, fill_value=0).astype(int)
        _lead = _michael_conf.sub(_sarah_conf, fill_value=0).astype(int).reindex(index=_pooled.index, columns=_pooled.columns, fill_value=0)
        st.plotly_chart(_confusion_heatmap(_pooled, "Both Players' Guesses", COLOR_M, _bucket, height=620, lead=_lead),
                        use_container_width=True, theme=None)

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

st.markdown('<div class="section-heading">Directional Bias by Decade</div>', unsafe_allow_html=True)

# Removed "Guess Accuracy Matrix" (a guessed-vs-actual scatter) — the Year
# Confusion Matrices above already show the same guessed-vs-actual
# relationship per player, so this data prep now feeds straight into the
# box plot below instead of a scatter plot first.
df_box = data[[col_year, col_michael, col_sarah]].copy()
df_box[col_year] = pd.to_numeric(df_box[col_year], errors="coerce")
df_box[col_michael] = pd.to_numeric(df_box[col_michael], errors="coerce")
df_box[col_sarah] = pd.to_numeric(df_box[col_sarah], errors="coerce")
df_box = df_box.dropna()
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