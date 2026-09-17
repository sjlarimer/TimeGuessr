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
# Same card treatment as the confusion matrices below — light background,
# soft border/shadow, a little hover "pop" — so they sit together as one
# consistent design instead of a styled chart next to bare white ones.
with st.container(key="year_dist_chart_card"):
    st.plotly_chart(fig_single, use_container_width=True, theme=None)

st.markdown("""
<style>
    .st-key-year_dist_chart_card, .st-key-conf_matrix_michael_card, .st-key-conf_matrix_sarah_card, .st-key-conf_matrix_michael_year_card, .st-key-conf_matrix_sarah_year_card { margin:0 auto 35px auto !important; padding:20px 20px 12px 20px; background:#fbfbf9; border:1px solid #e7e5dd; border-radius:18px; box-shadow:0 6px 22px rgba(0,0,0,0.07); box-sizing:border-box; }
    .st-key-year_dist_chart_card { max-width:1300px; }
    /* The four confusion matrix cards further down get the same card
       treatment as this chart — light background, soft border/shadow —
       plus a gentle hover "pop" of their own. */
    .st-key-year_dist_chart_card, .st-key-conf_matrix_michael_card, .st-key-conf_matrix_sarah_card, .st-key-conf_matrix_michael_year_card, .st-key-conf_matrix_sarah_year_card { transition:transform .15s ease, box-shadow .15s ease; }
    .st-key-year_dist_chart_card:hover, .st-key-conf_matrix_michael_card:hover, .st-key-conf_matrix_sarah_card:hover, .st-key-conf_matrix_michael_year_card:hover, .st-key-conf_matrix_sarah_year_card:hover { transform:scale(1.01); box-shadow:0 10px 28px rgba(0,0,0,0.12); }
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

def _gamma_colorscale(hex_color, gamma=0.45, steps=12):
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
        cr = round(255 * (1 - blend) + r * blend)
        cg = round(255 * (1 - blend) + g * blend)
        cb = round(255 * (1 - blend) + b * blend)
        stops.append([frac, f"rgb({cr},{cg},{cb})"])
    return stops

def _confusion_heatmap(table, title, leader_color, axis_suffix="", show_text=True, darken=False):
    labels = list(table.index)
    _scale = _gamma_colorscale(leader_color) if darken else [[0, "#ffffff"], [1, leader_color]]
    fig = go.Figure(data=go.Heatmap(
        z=table.values, x=labels, y=labels,
        colorscale=_scale, showscale=False,
        xgap=0, ygap=0,
        hovertemplate=f"<b>Actual:</b> %{{x}}{axis_suffix}<br><b>Guessed:</b> %{{y}}{axis_suffix}<br><b>Count:</b> %{{z}}<extra></extra>",
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=leader_color,
                        font=dict(family="Inter, sans-serif", size=12, color="#222222")),
        **({"text": table.values, "texttemplate": "%{text}",
            "textfont": dict(color="#000000", size=10, family="Inter, sans-serif")} if show_text else {}),
    ))
    span = (max(labels) - min(labels)) * 0.04 + 1
    min_l, max_l = min(labels) - span, max(labels) + span
    tick_step = 10 if len(labels) > 40 else 1
    tickvals = [l for l in labels if l % tick_step == 0] if tick_step > 1 else labels
    fig.update_layout(**PLOT_THEME)
    fig.update_layout(
        title=dict(text=title, font=dict(family="Poppins, sans-serif", size=17, color="#000000")),
        xaxis_title=f"Actual{' Decade' if axis_suffix else ' Year'}",
        yaxis_title=f"Guessed{' Decade' if axis_suffix else ' Year'}",
        # No forced 1:1 aspect ratio: these heatmaps sit side by side in a
        # fairly narrow column, and locking the cells square shrank the
        # whole grid down to a tiny fraction of the available width, leaving
        # the tick labels and cell counts too cramped to read. Letting it
        # fill the column's actual width makes cells rectangular but
        # legible instead of square but tiny.
        height=460,
        margin=dict(l=60, r=20, t=55, b=60),
        xaxis=dict(tickmode='array', tickvals=tickvals, ticktext=[f"{v}{axis_suffix}" for v in tickvals],
                   range=[min_l, max_l], showgrid=False),
        yaxis=dict(tickmode='array', tickvals=tickvals, ticktext=[f"{v}{axis_suffix}" for v in tickvals],
                   range=[min_l, max_l], showgrid=False),
    )
    if axis_suffix:
        # Coarse decade grid: outline each correct-decade cell individually.
        for _l in labels:
            fig.add_shape(type="rect", x0=_l - 5, x1=_l + 5, y0=_l - 5, y1=_l + 5,
                          line=dict(color=_DIAGONAL_GOLD, width=2.5), fillcolor="rgba(0,0,0,0)")
    return fig

def _confusion_table(guess_col, actual_col, decade=False):
    _t = _conf_df.copy()
    if decade:
        _t["_g"] = (_t[guess_col] // 10 * 10).astype(int)
        _t["_a"] = (_t[actual_col] // 10 * 10).astype(int)
    else:
        _t["_g"] = _t[guess_col].round().astype(int)
        _t["_a"] = _t[actual_col].astype(int)
    labels = sorted(_t["_a"].unique())
    table = pd.crosstab(_t["_g"], _t["_a"])
    return table.reindex(index=labels, columns=labels, fill_value=0)

st.markdown('<div class="section-heading">Year Confusion Matrices</div>', unsafe_allow_html=True)
_michael_yr_conf = _confusion_table(col_michael, col_year, decade=False)
_sarah_yr_conf = _confusion_table(col_sarah, col_year, decade=False)
_yr_conf_col1, _yr_conf_col2 = st.columns(2)
with _yr_conf_col1:
    with st.container(key="conf_matrix_michael_year_card"):
        st.plotly_chart(_confusion_heatmap(_michael_yr_conf, "Michael's Guesses", COLOR_M, show_text=False, darken=True),
                        use_container_width=True, theme=None)
with _yr_conf_col2:
    with st.container(key="conf_matrix_sarah_year_card"):
        st.plotly_chart(_confusion_heatmap(_sarah_yr_conf, "Sarah's Guesses", COLOR_S, show_text=False, darken=True),
                        use_container_width=True, theme=None)

st.markdown('<div class="section-heading">Decade Confusion Matrices</div>', unsafe_allow_html=True)
_michael_conf = _confusion_table(col_michael, col_year, decade=True)
_sarah_conf = _confusion_table(col_sarah, col_year, decade=True)
_conf_col1, _conf_col2 = st.columns(2)
with _conf_col1:
    with st.container(key="conf_matrix_michael_card"):
        st.plotly_chart(_confusion_heatmap(_michael_conf, "Michael's Guesses", COLOR_M, axis_suffix="s"),
                        use_container_width=True, theme=None)
with _conf_col2:
    with st.container(key="conf_matrix_sarah_card"):
        st.plotly_chart(_confusion_heatmap(_sarah_conf, "Sarah's Guesses", COLOR_S, axis_suffix="s"),
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