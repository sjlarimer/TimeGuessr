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