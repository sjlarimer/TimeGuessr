import streamlit as st
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime

st.title("Total Scores")

# --- Load data ---
data = pd.read_csv("./Data/Timeguessr_Stats.csv")

# Ensure Date column is datetime
data["Date"] = pd.to_datetime(data["Date"])

# --- Get only the first row for each Timeguessr Day ---
df_daily = data.groupby("Timeguessr Day").first().reset_index()

# Drop NaN values for each player separately
mask = df_daily[["Date", "Michael Total Score", "Sarah Total Score"]].dropna()

# Sort by date
mask = mask.sort_values("Date").reset_index(drop=True)

# --- Sidebar or top slider for date range ---
min_date, max_date = mask["Date"].min(), mask["Date"].max()

# --- Custom slider label color ---
st.markdown("""
    <style>
        /* Make slider labels and tooltips styled */
        div[data-testid="stSlider"] > label {
            color: #696761 !important;
            font-weight: 600;
        }
        div[data-baseweb="slider"] div[data-testid="stTooltipContent"] {
            color: #696761 !important;
            background-color: #f2f1ea !important;
            border: 1px solid #d9d7cc !important;
            font-weight: 500;
        }
        div[data-baseweb="slider"] div[data-testid="stTooltipContent"]::before {
            background-color: #f2f1ea !important;
            border: 1px solid #d9d7cc !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- Rolling average window length slider ---
window_length = st.slider(
    "Rolling Average Window (Games):",
    min_value=1,
    max_value=30,
    value=5,
    step=1
)

# --- Date range slider ---
start_date, end_date = st.slider(
    "Select Date Range:",
    min_value=min_date.to_pydatetime(),
    max_value=max_date.to_pydatetime(),
    value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
    format="YYYY-MM-DD"
)

# --- Filter data based on slider selection FIRST ---
mask_filtered = mask[(mask["Date"] >= start_date) & (mask["Date"] <= end_date)].copy()
df_daily_filtered = df_daily[(df_daily["Date"] >= start_date) & (df_daily["Date"] <= end_date)].copy()

# --- Recalculate rolling & cumulative averages on filtered data ---
mask_filtered["Michael Rolling Avg"] = mask_filtered["Michael Total Score"].rolling(window=window_length, min_periods=1).mean()
mask_filtered["Sarah Rolling Avg"] = mask_filtered["Sarah Total Score"].rolling(window=window_length, min_periods=1).mean()

mask_filtered["Michael Cumulative Avg"] = mask_filtered["Michael Total Score"].expanding().mean()
mask_filtered["Sarah Cumulative Avg"] = mask_filtered["Sarah Total Score"].expanding().mean()

# --- Create figure ---
fig = go.Figure()

# --- Scatter plots of scores ---
fig.add_trace(go.Scatter(
    x=df_daily_filtered["Date"],
    y=df_daily_filtered["Michael Total Score"],
    mode='markers',
    name='Michael Total Score',
    marker=dict(color='#bcb0ff', size=8),
    hovertemplate='Date: %{x}<br>Score: %{y}<extra></extra>'
))

fig.add_trace(go.Scatter(
    x=df_daily_filtered["Date"],
    y=df_daily_filtered["Sarah Total Score"],
    mode='markers',
    name='Sarah Total Score',
    marker=dict(color='#fce4a7', size=8),
    hovertemplate='Date: %{x}<br>Score: %{y}<extra></extra>'
))

# --- Rolling average lines ---
fig.add_trace(go.Scatter(
    x=mask_filtered["Date"],
    y=mask_filtered["Michael Rolling Avg"],
    mode='lines',
    name=f'Michael {window_length}-game Avg',
    line=dict(color='#221e8f', width=2.5),
    hovertemplate='Date: %{x}<br>Rolling Avg: %{y:.0f}<extra></extra>'
))

fig.add_trace(go.Scatter(
    x=mask_filtered["Date"],
    y=mask_filtered["Sarah Rolling Avg"],
    mode='lines',
    name=f'Sarah {window_length}-game Avg',
    line=dict(color='#bf8f15', width=2.5),
    hovertemplate='Date: %{x}<br>Rolling Avg: %{y:.0f}<extra></extra>'
))

# --- Cumulative average lines (dotted) ---
fig.add_trace(go.Scatter(
    x=mask_filtered["Date"],
    y=mask_filtered["Michael Cumulative Avg"],
    mode='lines',
    name='Michael Cumulative Avg',
    line=dict(color='#221e8f', width=1.5, dash='dot'),
    opacity=0.7
))

fig.add_trace(go.Scatter(
    x=mask_filtered["Date"],
    y=mask_filtered["Sarah Cumulative Avg"],
    mode='lines',
    name='Sarah Cumulative Avg',
    line=dict(color='#bf8f15', width=1.5, dash='dot'),
    opacity=0.7
))

# --- Layout styled like FiveThirtyEight ---
fig.update_layout(
    xaxis_title='Date',
    yaxis_title='Total Score',
    width=1400,
    height=600,
    hovermode='closest',
    font=dict(family='Poppins, Arial, sans-serif', size=14, color='#000000'),
    paper_bgcolor='#eae8dc',
    plot_bgcolor='#d9d7cc',
    margin=dict(l=60, r=40, t=60, b=60),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='right',
        x=1,
        bgcolor='rgba(0,0,0,0)',
        bordercolor='rgba(0,0,0,0)',
        font=dict(color='#696761')
    ),
)

# --- Gridlines and axes ---
fig.update_xaxes(
    showgrid=True,
    gridcolor='#bdbbb1',
    zeroline=False,
    linecolor='#8f8d85',
    tickcolor='#8f8d85',
    tickfont=dict(color='#696761'),
    title_font=dict(color='#696761')
)
fig.update_yaxes(
    showgrid=True,
    gridcolor='#bdbbb1',
    zeroline=False,
    linecolor='#8f8d85',
    tickcolor='#8f8d85',
    tickfont=dict(color='#696761'),
    title_font=dict(color='#696761')
)

# --- Display plot ---
st.plotly_chart(fig, use_container_width=True)