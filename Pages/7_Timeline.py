import streamlit as st
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import math

st.markdown("## Timeline")

# --- Load data ---
data = pd.read_csv("./Data/Timeguessr_Stats.csv")

# --- Ensure numeric columns and drop NaNs ---
# adjust column names if they differ exactly in your CSV
col_year = "Year"
col_michael = "Michael Time Guessed"
col_sarah = "Sarah Time Guessed"

# coerce to numeric (non-numeric -> NaN) then drop NaNs for hist calculations
year_vals = pd.to_numeric(data[col_year], errors="coerce").dropna().astype(float).values
michael_vals = pd.to_numeric(data[col_michael], errors="coerce").dropna().astype(float).values
sarah_vals = pd.to_numeric(data[col_sarah], errors="coerce").dropna().astype(float).values

# --- Bin edges: 10-year bins from 1900 to 2025 ---
bin_edges = list(range(1900, 2026, 10))  # e.g. 1900,1910,...,2020,2030? but stops at 2025 due to 2026
# make sure last edge is exactly 2025 (we want end=2025)
if bin_edges[-1] != 2025:
    # rebuild edges to guarantee last edge 2025
    bin_edges = []
    start = 1900
    while start < 2025:
        bin_edges.append(start)
        start += 10
    bin_edges.append(2025)

# compute counts using numpy histogram (shared bin edges)
counts_year, _ = np.histogram(year_vals, bins=bin_edges)
counts_michael, _ = np.histogram(michael_vals, bins=bin_edges)
counts_sarah, _ = np.histogram(sarah_vals, bins=bin_edges)

# create readable bin labels (e.g. "1900-1909", last one "2020-2025")
bin_labels = []
for i in range(len(bin_edges)-1):
    start = bin_edges[i]
    end = bin_edges[i+1] - 1 if i < len(bin_edges)-2 else bin_edges[i+1]  # last bin inclusive to 2025
    # For the last bin, making label "2020-2025"
    if i == len(bin_edges)-2:
        end = bin_edges[i+1]
    bin_labels.append(f"{start}-{end}")

# --- Find maximum bucket value across all three histograms ---
max_count = max(counts_year.max() if counts_year.size else 0,
                counts_michael.max() if counts_michael.size else 0,
                counts_sarah.max() if counts_sarah.size else 0)

# choose dtick (tick spacing) reasonably
if max_count <= 10:
    y_dtick = 1
else:
    y_dtick = math.ceil(max_count / 10)

y_axis_config = dict(range=[0, max_count], tick0=0, dtick=y_dtick, title="Count")

# common layout styling
common_layout = dict(
    xaxis=dict(tickmode="array", tickvals=list(range(len(bin_labels))), ticktext=bin_labels, title="Year range"),
    yaxis=y_axis_config,
    bargap=0.1,
    margin=dict(l=50, r=20, t=40, b=120)  # leave room for long x tick labels
)

bar_color = "#db5049"

# --- Plot 1: Year ---
fig_year = go.Figure()
fig_year.add_trace(go.Bar(x=bin_labels, y=counts_year, marker_color=bar_color, name="Year"))
fig_year.update_layout(title="Histogram of Year", **common_layout)

# --- Plot 2: Michael Time Guessed ---
fig_michael = go.Figure()
fig_michael.add_trace(go.Bar(x=bin_labels, y=counts_michael, marker_color=bar_color, name="Michael Time Guessed"))
fig_michael.update_layout(title="Histogram of Michael Time Guessed", **common_layout)

# --- Plot 3: Sarah Time Guessed ---
fig_sarah = go.Figure()
fig_sarah.add_trace(go.Bar(x=bin_labels, y=counts_sarah, marker_color=bar_color, name="Sarah Time Guessed"))
fig_sarah.update_layout(title="Histogram of Sarah Time Guessed", **common_layout)

# --- Display in Streamlit ---
st.plotly_chart(fig_year, use_container_width=True)
st.plotly_chart(fig_michael, use_container_width=True)
st.plotly_chart(fig_sarah, use_container_width=True)

# --- Scatterplot of time guessed vs actual year ---

# we need to align year, michael, sarah from the same rows (instead of independently dropping NaNs)
df_scatter = data[[col_year, col_michael, col_sarah]].copy()
df_scatter[col_year] = pd.to_numeric(df_scatter[col_year], errors="coerce")
df_scatter[col_michael] = pd.to_numeric(df_scatter[col_michael], errors="coerce")
df_scatter[col_sarah] = pd.to_numeric(df_scatter[col_sarah], errors="coerce")
df_scatter = df_scatter.dropna()

x_year = df_scatter[col_year].astype(float).values
y_michael = df_scatter[col_michael].astype(float).values
y_sarah = df_scatter[col_sarah].astype(float).values

# diagonal reference line (y = x)
line_x = np.linspace(min(x_year.min(), y_michael.min(), y_sarah.min()),
                     max(x_year.max(), y_michael.max(), y_sarah.max()),
                     200)

fig_scatter = go.Figure()

fig_scatter.add_trace(go.Scatter(
    x=x_year,
    y=y_michael,
    mode="markers",
    name="Michael Time Guessed",
    marker=dict(size=8, color="#221e8f")     # Michael = same red as bars
))

fig_scatter.add_trace(go.Scatter(
    x=x_year,
    y=y_sarah,
    mode="markers",
    name="Sarah Time Guessed",
    marker=dict(size=8, color="#8a005c")     # blue for contrast
))

fig_scatter.add_trace(go.Scatter(
    x=line_x,
    y=line_x,
    mode="lines",
    name="y = year",
    line=dict(color="black", width=2)
))

fig_scatter.update_layout(
    title="Time Guessed vs Actual Year",
    xaxis_title="Actual Year",
    yaxis_title="Guessed Year",
    margin=dict(l=50, r=20, t=40, b=40),
    showlegend=True
)

# Show in Streamlit
st.plotly_chart(fig_scatter, use_container_width=True)



# --- Boxplots of signed error by decade ---

df_box = data[[col_year, col_michael, col_sarah]].copy()
df_box[col_year] = pd.to_numeric(df_box[col_year], errors="coerce")
df_box[col_michael] = pd.to_numeric(df_box[col_michael], errors="coerce")
df_box[col_sarah] = pd.to_numeric(df_box[col_sarah], errors="coerce")
df_box = df_box.dropna()

# decade bucket
df_box["decade"] = (df_box[col_year] // 10 * 10).astype(int)

# signed errors
df_box["michael_err"] = df_box[col_michael] - df_box[col_year]
df_box["sarah_err"] = df_box[col_sarah] - df_box[col_year]

# sorted list of decades to keep ordering stable
decades = sorted(df_box["decade"].unique())

fig_box = go.Figure()

# Michael boxplots
for d in decades:
    fig_box.add_trace(go.Box(
        y=df_box.loc[df_box["decade"] == d, "michael_err"],
        x=[f"{d}s"] * len(df_box.loc[df_box["decade"] == d]),
        name=f"Michael {d}s",
        marker_color="#221e8f",
        boxmean="sd"
    ))

# Sarah boxplots
for d in decades:
    fig_box.add_trace(go.Box(
        y=df_box.loc[df_box["decade"] == d, "sarah_err"],
        x=[f"{d}s"] * len(df_box.loc[df_box["decade"] == d]),
        name=f"Sarah {d}s",
        marker_color="#8a005c",
        boxmean="sd"
    ))

# determine symmetric axis range
all_errors = pd.concat([
    df_box["michael_err"],
    df_box["sarah_err"]
])
max_abs = max(abs(all_errors.min()), abs(all_errors.max()))

fig_box.update_layout(
    title="Signed Error by Decade (Michael vs Sarah)",
    xaxis_title="Decade",
    yaxis_title="Guessed Year − Actual Year",
    boxmode="group",
    boxgap=0.3,          # <-- spacing inside each decade group
    boxgroupgap=0.6,     # <-- spacing between decades
    yaxis=dict(
        range=[-max_abs, max_abs],
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor="black"
    ),
    margin=dict(l=50, r=20, t=40, b=40)
)

st.plotly_chart(fig_box, use_container_width=True)