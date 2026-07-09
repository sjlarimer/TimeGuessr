import streamlit as st
import pandas as pd
from PIL import Image
import numpy as np
import plotly.graph_objects as go

# --- Configuration ---
st.set_page_config(page_title="Welcome", layout='wide')

# --- Load Global CSS ---
from utils import load_css
load_css()

import importlib, sys as _sys
if "aggregation" in _sys.modules:
    importlib.reload(_sys.modules["aggregation"])
from aggregation import run_aggregation
run_aggregation()

# --- Custom Page Styles ---
st.markdown(
    """
    <style>
        /* Modern Card Styling */
        .info-card {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            border: 1px solid #eee;
            height: 100%; /* Fill flex container */
            box-sizing: border-box;
        }

        /* Flex Container for Equal Height Cards */
        .flex-row {
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
            margin-bottom: 2rem;
        }

        .flex-col-overview {
            flex: 1.4; /* Wider column */
            min-width: 300px;
        }

        .flex-col-legend {
            flex: 1; /* Narrower column */
            min-width: 300px;
        }

        .stat-card {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 5px solid #db5049;
            text-align: center;
        }

        /* Typography */
        h1, h2, h3 {
            font-family: 'Poppins', sans-serif;
            color: #db5049 !important;
        }

        .big-number {
            font-size: 2rem;
            font-weight: 700;
            color: #333;
        }

        .stat-label {
            font-size: 0.9rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Table Styling */
        .stat-table {
            width: 100%;
            font-family: 'Poppins', sans-serif;
            font-size: 16px;
            border-collapse: separate;
            border-spacing: 0;
            background-color: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin: 20px 0;
        }

        .stat-table th {
            text-align: center;
            padding: 15px;
            background-color: #db5049;
            color: white !important;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 14px;
            letter-spacing: 0.5px;
        }

        .stat-table th:first-child {
            text-align: left;
            padding-left: 20px;
        }

        .stat-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
            color: #444;
        }

        .stat-table tr:last-child td {
            border-bottom: none;
        }

        .stat-val {
            font-weight: 700;
            text-align: center;
            color: #222;
        }

        .stat-row-label {
            font-weight: 500;
            padding-left: 20px !important;
        }

        /* Compact Legend Table Styling */
        .compact-legend {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px; /* Slightly adjusted size */
            font-family: 'Poppins', sans-serif;
        }
        .compact-legend th {
            text-align: left;
            padding: 5px 8px;
            font-size: 11px;
            text-transform: uppercase;
            color: #999;
            border-bottom: 1px solid #eee;
            font-weight: 600;
        }
        .compact-legend td {
            padding: 4px 8px;
            color: #555;
            border-bottom: 1px solid #f5f5f5;
        }
        .compact-legend tr:last-child td {
            border-bottom: none;
        }
        .emoji-col {
            font-family: 'Segoe UI Emoji', 'Roboto', sans-serif;
            letter-spacing: 1px;
            font-size: 14px;
        }

        /* Activity Log Styling */
        .activity-table-container {
            max-height: 600px;
            overflow-y: auto;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border: 1px solid #eee;
            background: white;
        }
        .activity-table {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
        }
        .activity-table thead {
            position: sticky;
            top: 0;
            z-index: 10;
            background-color: #db5049;
        }
        .activity-table th {
            color: white !important;
            font-weight: 600;
            padding: 15px;
            text-align: left;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
        }
        .activity-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
            color: #444;
            vertical-align: middle;
        }
        /* Override inline style on hover with !important */
        .activity-table tr:hover td {
            background-color: #eaeaea !important;
        }
        .loc-city {
            font-weight: 600;
            color: #333;
            display: block;
        }
        .loc-country {
            font-size: 12px;
            color: #888;
            display: block;
            margin-top: 2px;
        }
        .score-val {
            font-weight: 600;
            font-variant-numeric: tabular-nums;
        }
        .score-m { color: #221e8f; }
        .score-s { color: #8a005c; }

        /* Scrollbar Styling for Activity Log */
        .activity-table-container::-webkit-scrollbar {
            width: 8px;
        }
        .activity-table-container::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 0 12px 12px 0;
        }
        .activity-table-container::-webkit-scrollbar-thumb {
            background: #ccc;
            border-radius: 4px;
        }
        .activity-table-container::-webkit-scrollbar-thumb:hover {
            background: #bbb;
        }

        /* Link Styling */
        a {
            color: #db5049;
            text-decoration: none;
            transition: color 0.3s;
        }
        a:hover {
            color: #b03d36;
            text-decoration: underline;
        }

        /* --- Force Streamlit Columns to Equal Height --- */
        [data-testid="column"] {
            display: flex;
            flex-direction: column;
        }
        [data-testid="column"] > div {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        /* Target the internal markdown container */
        [data-testid="column"] > div > div {
            flex: 1;
        }
        /* Target the div wrapping the HTML content */
        [data-testid="column"] > div > div > div {
            height: 100%;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header Section (Centered) ---
head_c1, head_c2, head_c3 = st.columns([1, 2, 1])

with head_c2:
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem; margin-bottom: 10px;'>Michael & Sarah</h1>", unsafe_allow_html=True)

    # --- Top Image ---
    try:
        img = Image.open("Images/home.png")
        width, height = img.size
        crop_height = int(height * 0.75)
        img_cropped = img.crop((0, 0, width, crop_height))
        st.image(img_cropped, use_container_width=True)
    except FileNotFoundError:
        st.warning("Cover image not found.")

    st.markdown("<h1 style='text-align: center; margin-top: 0;'>Tracking</h1>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<br>", unsafe_allow_html=True)

# --- Pre-compute stats for Overview card ---
try:
    _d = pd.read_csv("./Data/Timeguessr_Stats.csv")
    _d["Date"] = pd.to_datetime(_d["Date"]).dt.date
    _d["Michael Total Score"] = pd.to_numeric(_d["Michael Total Score"], errors="coerce")
    _d["Sarah Total Score"] = pd.to_numeric(_d["Sarah Total Score"], errors="coerce")
    _daily = _d.groupby("Date", as_index=False).agg(
        michael_played=("Michael Total Score", lambda x: x.notna().any()),
        sarah_played=("Sarah Total Score", lambda x: x.notna().any())
    )
    _dt = pd.to_datetime("2025-10-10").date()
    both_all = int((_daily["michael_played"] & _daily["sarah_played"]).sum())
    both_since = int((_daily[_daily["Date"] >= _dt]["michael_played"] & _daily[_daily["Date"] >= _dt]["sarah_played"]).sum())
except Exception:
    both_all = "—"
    both_since = "—"

# --- Overview (left) + Score Reference Charts (right) ---
_overview_col, _legend_col = st.columns([1.4, 1])

with _overview_col:
    st.markdown(
        f"""<h2 style="margin-top: 0; text-align: center;">Overview</h2><div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;"><div class="stat-card" style="flex: 1;"><div class="stat-label">Total Days Played</div><div class="big-number">{both_all}</div></div><div class="stat-card" style="flex: 1;"><div class="stat-label">Days Played Since Tracking</div><div class="big-number">{both_since}</div></div></div><div style='font-family: Poppins; font-size: 16px; line-height: 1.8; color: #444;'>TimeGuessr is a daily geography and history browser game that challenges players to identify the context of historical photographs.<br><br>Each day, players are presented with five rounds. In each round, an image is revealed, and the goal is to:<ul style="margin-bottom: 1rem;"><li><b>Guess the Location:</b> Pinpoint where the photo was taken on a world map.</li><li><b>Guess the Year:</b> Select the year the photo was taken on a timeline.</li></ul>Points are awarded based on the accuracy of both the location and the year. A perfect round yields <b>10,000 points</b>, for a maximum daily score of <b>50,000</b>.<br><br><div style="text-align: center; margin-top: 20px;"><a href="https://timeguessr.com/" target="_blank" style="background-color: #db5049; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold; text-decoration: none;">Play TimeGuessr</a></div></div>""",
        unsafe_allow_html=True
    )

_legend_col.markdown(
    """
    <style>
    /* Rounded line caps on all Plotly line traces */
    .js-plotly-plot .js-line {
        stroke-linecap: round;
        stroke-linejoin: round;
    }
    /* Both columns rendered as equal-height cards */
    div[data-testid="stHorizontalBlock"]:has(.score-ref-header) {
        align-items: stretch !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.score-ref-header) > div[data-testid="stColumn"] {
        background-color: #ffffff;
        padding: 2rem !important;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eee;
        box-sizing: border-box;
    }
    </style>
    <h2 class="score-ref-header" style="margin-top: 0; text-align: center;">Score Reference</h2>
    """,
    unsafe_allow_html=True
)

# Colors matching the notebook's pattern_colors dict exactly
# "yellow" is unusable on white, so goldenrod stands in for O%X line color
_line_color = {
    "OOO": "mediumorchid",
    "OO%": "blue",
    "OOX": "green",
    "O%X": "gold",
    "OXX": "darkorange",
    "%XX": "red",
    "XXX": "maroon",
}
_box_color = {
    "OOO": "rgba(186,85,211,0.12)",
    "OO%": "rgba(0,0,255,0.08)",
    "OOX": "rgba(0,128,0,0.08)",
    "O%X": "rgba(255,215,0,0.15)",
    "OXX": "rgba(255,140,0,0.10)",
    "%XX": "rgba(220,50,50,0.08)",
    "XXX": "rgba(128,0,0,0.08)",
}

_chart_layout = dict(
    height=220,
    margin=dict(l=10, r=10, t=30, b=40),
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="Poppins", size=9, color="#111"),
)
_yaxis_cfg = dict(
    range=[-100, 5200],
    gridcolor="#ddd", showline=True, linecolor="#888",
    tickcolor="#888", tickfont=dict(color="#111"),
    automargin=True,
)

with _legend_col:
    fig_geo = go.Figure()

    for cat, x0, x1 in [
        ("OOO", 0.02,  0.05),
        ("OO%", 0.05,  37.5),
        ("OOX", 37.5,  100),
        ("O%X", 100,   250),
        ("OXX", 250,   1000),
        ("%XX", 1000,  2000),
        ("XXX", 2000,  10000),
    ]:
        fig_geo.add_shape(type="rect", x0=x0, x1=x1, y0=0, y1=1,
                          xref="x", yref="paper",
                          fillcolor=_box_color[cat], line_width=0, layer="below")

    # Piecewise formula from aggregation.py (dist in metres):
    #   score = max(12, intercept - dist_m * slope)
    # Each tuple is one formula segment with its category colour.
    # Segments of the same colour that are separated by a jump are drawn as
    # separate traces so they don't connect.  On the log x-axis the lines are
    # curved (formula is linear in metres, not log-metres).
    _geo_segs = [
        #  cat      d_start_m   d_end_m   intercept  slope
        ("OOO",     30,         50,        5000,      0         ),  # ~0.03 → 0.05 km
        ("OO%",     50,         1000,      5000,      0.02      ),  # 0.05 → 1 km
        ("OO%",     1000,       5000,      4980,      0.016     ),  # 1 → 5 km
        ("OO%",     5000,       37500,     4900,      0.004     ),  # 5 → 37.5 km
        ("OOX",     37500,      100000,    4900,      0.004     ),  # 37.5 → 100 km
        ("O%X",     100000,     250000,    4500,      0.001     ),  # 100 → 250 km
        ("OXX",     250000,     1000000,   4500,      0.001     ),  # 250 → 1000 km
        ("%XX",     1000000,    2000000,   3500,      0.0005    ),  # 1000 → 2000 km
        ("XXX",     2000000,    3000000,   2500,      0.0003333 ),  # 2000 → 3000 km
        ("XXX",     3000000,    6000000,   1500,      0.0002    ),  # 3000 → 6000 km
        ("XXX",     6000000,    12000000,  12,        0         ),  # 6000 → 12000 km
    ]
    for _cat, _d0, _d1, _ic, _sl in _geo_segs:
        _dm = np.logspace(np.log10(_d0), np.log10(_d1), 80)
        _sc = np.clip(_ic - _dm * _sl, 12, 5000)
        fig_geo.add_trace(go.Scatter(
            x=_dm / 1000,
            y=_sc,
            mode="lines",
            line=dict(color=_line_color[_cat], width=3),
            showlegend=False,
            hovertemplate="<b>%{x:.2f} km</b><br>Score: %{y:.0f}<extra></extra>",
        ))

    fig_geo.update_layout(
        **_chart_layout,
        title=dict(text="Geography Score", x=0.5, xanchor="center",
                   font=dict(family="Poppins", size=14, color="#db5049")),
        xaxis=dict(
            type="log", title="Distance (km)",
            range=[np.log10(0.02), np.log10(12000)],
            tickvals=[0.1, 1, 10, 100, 1000, 10000],
            ticktext=["100m", "1km", "10km", "100km", "1,000km", "10,000km"],
            gridcolor="#ddd", showline=True, linecolor="#888",
            tickcolor="#888", tickfont=dict(color="#111"),
            title_font=dict(color="#111"),
        ),
        yaxis=_yaxis_cfg,
    )
    st.plotly_chart(fig_geo, use_container_width=True)

_legend_col.markdown(
    """
    <div style="display:flex; gap:10px; justify-content:center; flex-wrap:wrap;
                font-family:'Poppins',sans-serif; font-size:13px; margin-top:-10px; margin-bottom:16px;">
      <span style="background:rgba(128,0,128,0.18); padding:3px 10px; border-radius:4px; color:#333;">&#x1F7E9;&#x1F7E9;&#x1F7E9;</span>
      <span style="background:rgba(0,0,255,0.14);   padding:3px 10px; border-radius:4px; color:#333;">&#x1F7E9;&#x1F7E9;&#x1F7E8;</span>
      <span style="background:rgba(0,128,0,0.16);   padding:3px 10px; border-radius:4px; color:#333;">&#x1F7E9;&#x1F7E9;&#x2B1B;</span>
      <span style="background:rgba(200,160,0,0.22); padding:3px 10px; border-radius:4px; color:#333;">&#x1F7E9;&#x1F7E8;&#x2B1B;</span>
      <span style="background:rgba(255,140,0,0.20); padding:3px 10px; border-radius:4px; color:#333;">&#x1F7E9;&#x2B1B;&#x2B1B;</span>
      <span style="background:rgba(220,50,50,0.18); padding:3px 10px; border-radius:4px; color:#333;">&#x1F7E8;&#x2B1B;&#x2B1B;</span>
      <span style="background:rgba(128,0,0,0.16);   padding:3px 10px; border-radius:4px; color:#333;">&#x2B1B;&#x2B1B;&#x2B1B;</span>
    </div>
    """,
    unsafe_allow_html=True,
)

with _legend_col:
    fig_time = go.Figure()

    for cat, x0, x1 in [
        ("OOO", -0.5, 0.5),
        ("OO%", 0.5,  2.5),
        ("OOX", 2.5,  4.5),
        ("O%X", 4.5,  7.5),
        ("OXX", 7.5,  15.5),
        ("%XX", 15.5, 20.5),
        ("XXX", 20.5, 25.5),
    ]:
        fig_time.add_shape(type="rect", x0=x0, x1=x1, y0=0, y1=1,
                           xref="x", yref="paper",
                           fillcolor=_box_color[cat], line_width=0, layer="below")

    # Exact per-year scores confirmed from data (all values are exact constants)
    _yr_score = [5000, 4950, 4800, 4600, 4300, 3900, 3400, 3400,
                 2500, 2500, 2500, 2000, 2000, 2000, 2000, 2000,
                 1000, 1000, 1000, 1000, 1000, 0, 0, 0, 0, 0]
    _yr_cat   = ["OOO", "OO%", "OO%", "OOX", "OOX", "O%X", "O%X", "O%X",
                 "OXX", "OXX", "OXX", "OXX", "OXX", "OXX", "OXX", "OXX",
                 "%XX", "%XX", "%XX", "%XX", "%XX",
                 "XXX", "XXX", "XXX", "XXX", "XXX"]

    # One disconnected segment per (cat, score) run.
    # Endpoints are the first and last year (both inclusive) so lines never
    # extend into the next year's territory (>= vs > distinction).
    # Single-year runs become a horizontal tick marker (a zero-length line
    # would be invisible, and a wide line would overshoot the box boundary).
    i = 0
    while i < len(_yr_cat):
        cat = _yr_cat[i]
        sc = _yr_score[i]
        start_yr = i
        while i < len(_yr_cat) and _yr_cat[i] == cat and _yr_score[i] == sc:
            i += 1
        last_yr = i - 1  # inclusive end

        if start_yr == last_yr:
            fig_time.add_trace(go.Scatter(
                x=[start_yr], y=[sc],
                mode="markers",
                marker=dict(color=_line_color[cat], size=8, symbol="circle"),
                showlegend=False,
                hovertemplate="<b>Year %{x:.0f}</b><br>Score: %{y}<extra></extra>",
            ))
        else:
            fig_time.add_trace(go.Scatter(
                x=[start_yr, last_yr], y=[sc, sc],
                mode="lines",
                line=dict(color=_line_color[cat], width=3),
                showlegend=False,
                hovertemplate="<b>%{x:.0f} years off</b><br>Score: %{y}<extra></extra>",
            ))

    fig_time.update_layout(
        **_chart_layout,
        title=dict(text="Time Score", x=0.5, xanchor="center",
                   font=dict(family="Poppins", size=14, color="#db5049")),
        xaxis=dict(
            title="Years Off", tickvals=list(range(0, 26, 2)),
            range=[-0.5, 25.5], gridcolor="#ddd", showline=True, linecolor="#888",
            tickcolor="#888", tickfont=dict(color="#111"),
            title_font=dict(color="#111"),
        ),
        yaxis=_yaxis_cfg,
    )
    st.plotly_chart(fig_time, use_container_width=True)


# --- Data Processing ---
try:
    data = pd.read_csv("./Data/Timeguessr_Stats.csv")
    data["Date"] = pd.to_datetime(data["Date"]).dt.date

    data["Michael Total Score"] = pd.to_numeric(data["Michael Total Score"], errors="coerce")
    data["Sarah Total Score"] = pd.to_numeric(data["Sarah Total Score"], errors="coerce")

    # Group by date
    daily = data.groupby("Date", as_index=False).agg(
        michael_played=("Michael Total Score", lambda x: x.notna().any()),
        sarah_played=("Sarah Total Score", lambda x: x.notna().any())
    )

    # --- Recent Activity Section ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## Recent Activity Log")

    display_data = data.iloc[::-1]

    # Generate Table Rows with Alternating Date Shading
    table_rows = ""
    last_date = None
    is_shaded = True # Start with True so the first toggle makes it False (White)

    for _, row in display_data.iterrows():
        # Track date changes for shading
        current_date = row['Date']
        if current_date != last_date:
            is_shaded = not is_shaded
            last_date = current_date

        bg_style = 'background-color: #f6f6f6;' if is_shaded else 'background-color: #ffffff;'

        # Format Date
        date_str = current_date.strftime('%b %d, %Y') if pd.notna(current_date) else ""

        # Format Location (Combine City and Country)
        city = str(row['City']).strip() if pd.notna(row['City']) else ""
        country = str(row['Country']).strip() if pd.notna(row['Country']) else ""

        if city and country:
            if city == country:
                loc_html = f'<span class="loc-city">{country}</span>'
            else:
                loc_html = f'<span class="loc-city">{city}</span><span class="loc-country">{country}</span>'
        elif country:
            loc_html = f'<span class="loc-city">{country}</span>'
        else:
            loc_html = "-"

        # Format Year
        year_str = str(int(row['Year'])) if pd.notna(row['Year']) else "-"

        # Format Scores
        def fmt_score(val):
            return f"{int(val):,}" if pd.notna(val) else "-"

        m_total = fmt_score(row['Michael Total Score'])
        s_total = fmt_score(row['Sarah Total Score'])
        m_round = fmt_score(row['Michael Round Score'])
        s_round = fmt_score(row['Sarah Round Score'])

        table_rows += f"""<tr style="{bg_style}"><td style="color: #666; font-size: 13px;">{date_str}</td><td>{loc_html}</td><td style="text-align: center; font-weight: 500;">{year_str}</td><td style="text-align: right;"><span class="score-val score-m">{m_round}</span></td><td style="text-align: right;"><span class="score-val score-s">{s_round}</span></td><td style="text-align: right;"><span class="score-val score-m" style="opacity: 0.6; font-size: 13px;">{m_total}</span></td><td style="text-align: right;"><span class="score-val score-s" style="opacity: 0.6; font-size: 13px;">{s_total}</span></td></tr>"""

    # Assemble HTML Table (Compact)
    # Adjusted widths: Narrowed Date (15->12%) and Year (10->8%), Widened Score cols (10->11%) and Location (35->36%)
    full_table_html = f"""<div class="activity-table-container"><table class="activity-table"><thead><tr><th style="width: 12%;">Date</th><th style="width: 36%;">Location</th><th style="width: 8%; text-align: center;">Year</th><th style="width: 11%; text-align: right;">Michael Round</th><th style="width: 11%; text-align: right;">Sarah Round</th><th style="width: 11%; text-align: right;">Michael Daily</th><th style="width: 11%; text-align: right;">Sarah Daily</th></tr></thead><tbody>{table_rows}</tbody></table></div>"""

    st.markdown(full_table_html, unsafe_allow_html=True)

except FileNotFoundError:
    st.error("Data file not found. Please ensure 'Data/Timeguessr_Stats.csv' exists.")
