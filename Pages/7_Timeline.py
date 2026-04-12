import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import math
import os

# --- Page Config ---
st.set_page_config(page_title="Timeline Analysis", layout="wide")

# --- Load External CSS ---
if os.path.exists("styles.css"):
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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
def load_timeline_data():
    data = pd.read_csv("./Data/Timeguessr_Stats.csv")
    return data

data = load_timeline_data()

col_year = "Year"
col_michael = "Michael Time Guessed"
col_sarah = "Sarah Time Guessed"

year_vals = pd.to_numeric(data[col_year], errors="coerce").dropna().astype(float).values
michael_vals = pd.to_numeric(data[col_michael], errors="coerce").dropna().astype(float).values
sarah_vals = pd.to_numeric(data[col_sarah], errors="coerce").dropna().astype(float).values

# ==========================================
# 0. INDIVIDUAL YEAR FREQUENCY (NEW)
# ==========================================
st.markdown('<div class="section-heading">Actual Year Distribution</div>', unsafe_allow_html=True)

# Calculate counts for every single year
min_y = int(min(year_vals))
max_y = int(max(year_vals))
all_years = np.arange(min_y, max_y + 1)
counts_single, _ = np.histogram(year_vals, bins=np.arange(min_y, max_y + 2))

fig_single = go.Figure()
fig_single.add_trace(go.Bar(
    x=all_years, 
    y=counts_single, 
    marker_color=COLOR_ACTUAL,
    name="Actual Year Frequency",
    hovertemplate="<b>Year:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>"
))

fig_single.update_layout(**PLOT_THEME)
fig_single.update_layout(
    title="Appearance Count per Individual Year (Bucket size = 1)",
    xaxis_title="Year",
    yaxis_title="Frequency",
    bargap=0, # Continuous look for single years
    xaxis=dict(tickmode='linear', dtick=10) # Show labels every 10 years
)
st.plotly_chart(fig_single, use_container_width=True, theme=None)

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