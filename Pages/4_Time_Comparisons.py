import streamlit as st
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.title("Time Scores")

# --- Load data ---
data = pd.read_csv("./Data/Timeguessr_Stats.csv")

# Ensure Date column is datetime
data["Date"] = pd.to_datetime(data["Date"])
data = data.sort_values("Date").reset_index(drop=True)

# --- Toggle for removing estimated scores ---
remove_estimated = st.toggle("Remove Estimated Scores", value=False, key="remove_estimated_toggle")

# --- Filter out estimated scores if toggle is on ---
if remove_estimated:
    # For each player, mark rows where min != max as estimated
    for player in ["Michael", "Sarah"]:
        min_col = f"{player} Time Score (Min)"
        max_col = f"{player} Time Score (Max)"
        
        # Identify dates where ANY round has min != max for this player
        estimated_dates = data[data[min_col] != data[max_col]]["Date"].unique()
        
        # Set those scores to NaN for that player on those dates
        data.loc[data["Date"].isin(estimated_dates), [min_col, max_col]] = np.nan

# --- Compute midpoints per round ---
for player in ["Michael", "Sarah"]:
    data[f"{player} Time Midpoint"] = (
        data[f"{player} Time Score (Min)"] + data[f"{player} Time Score (Max)"]
    ) / 2

# --- Sum midpoints per day ---
daily_cols = ["Michael Time Midpoint", "Sarah Time Midpoint"]

df_daily = (
    data.groupby("Date")[daily_cols]
    .sum(min_count=1)
    .reset_index()
)

# Sort by date
df_daily = df_daily.sort_values("Date").reset_index(drop=True)

# --- Create separate columns for averaging (only days where BOTH players have data) ---
df_daily["Michael Time For Avg"] = df_daily["Michael Time Midpoint"].where(
    df_daily["Sarah Time Midpoint"].notna()
)
df_daily["Sarah Time For Avg"] = df_daily["Sarah Time Midpoint"].where(
    df_daily["Michael Time Midpoint"].notna()
)

# --- Get available date range (dates with at least one player's data) ---
available_dates = df_daily[
    df_daily["Michael Time Midpoint"].notna() | df_daily["Sarah Time Midpoint"].notna()
]["Date"]

min_date, max_date = available_dates.min(), available_dates.max()

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
    "Rolling Average Window (Days):",
    min_value=1,
    max_value=30,
    value=5,
    step=1,
    key="time_window_slider"
)

# --- Date range slider ---
start_date, end_date = st.slider(
    "Select Date Range:",
    min_value=min_date.to_pydatetime(),
    max_value=max_date.to_pydatetime(),
    value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
    format="YYYY-MM-DD",
    key="time_date_slider"
)

# --- Filter data based on slider selection ---
df_daily_filtered = df_daily[(df_daily["Date"] >= start_date) & (df_daily["Date"] <= end_date)].copy()

# --- Further filter to only dates with at least one player's data ---
df_daily_filtered = df_daily_filtered[
    df_daily_filtered["Michael Time Midpoint"].notna() | df_daily_filtered["Sarah Time Midpoint"].notna()
]

# --- Get actual plot range with buffer ---
if len(df_daily_filtered) > 0:
    plot_min_date = df_daily_filtered["Date"].min()
    plot_max_date = df_daily_filtered["Date"].max()
    
    # Add 2% buffer on each side
    date_range = (plot_max_date - plot_min_date).total_seconds()
    buffer = pd.Timedelta(seconds=date_range * 0.02)
    
    plot_min_date = plot_min_date - buffer
    plot_max_date = plot_max_date + buffer
else:
    plot_min_date = start_date
    plot_max_date = end_date

# --- Recalculate rolling & cumulative averages on filtered data (using For Avg columns) ---
for player in ["Michael", "Sarah"]:
    col = f"{player} Time For Avg"
    df_daily_filtered[f"{player} Time Rolling Avg"] = df_daily_filtered[col].rolling(window=window_length, min_periods=1).mean()
    df_daily_filtered[f"{player} Time Cumulative Avg"] = df_daily_filtered[col].expanding(min_periods=1).mean()

# --- Create figure ---
fig = go.Figure()

# --- Scatter plots of daily sums (using original midpoint, not For Avg) ---
fig.add_trace(go.Scatter(
    x=df_daily_filtered["Date"],
    y=df_daily_filtered["Michael Time Midpoint"],
    mode='markers',
    name='Michael Daily Sum',
    marker=dict(color='#bcb0ff', size=8),
    hovertemplate='Date: %{x}<br>Score: %{y}<extra></extra>'
))

fig.add_trace(go.Scatter(
    x=df_daily_filtered["Date"],
    y=df_daily_filtered["Sarah Time Midpoint"],
    mode='markers',
    name='Sarah Daily Sum',
    marker=dict(color='#fce4a7', size=8),
    hovertemplate='Date: %{x}<br>Score: %{y}<extra></extra>'
))

# --- Rolling average lines ---
fig.add_trace(go.Scatter(
    x=df_daily_filtered["Date"],
    y=df_daily_filtered["Michael Time Rolling Avg"],
    mode='lines',
    name=f'Michael {window_length}-day Avg',
    line=dict(color='#221e8f', width=2.5),
    hovertemplate='Date: %{x}<br>Rolling Avg: %{y:.0f}<extra></extra>'
))

fig.add_trace(go.Scatter(
    x=df_daily_filtered["Date"],
    y=df_daily_filtered["Sarah Time Rolling Avg"],
    mode='lines',
    name=f'Sarah {window_length}-day Avg',
    line=dict(color='#bf8f15', width=2.5),
    hovertemplate='Date: %{x}<br>Rolling Avg: %{y:.0f}<extra></extra>'
))

# --- Cumulative average lines (dotted) ---
fig.add_trace(go.Scatter(
    x=df_daily_filtered["Date"],
    y=df_daily_filtered["Michael Time Cumulative Avg"],
    mode='lines',
    name='Michael Cumulative Avg',
    line=dict(color='#221e8f', width=1.5, dash='dot'),
    opacity=0.7
))

fig.add_trace(go.Scatter(
    x=df_daily_filtered["Date"],
    y=df_daily_filtered["Sarah Time Cumulative Avg"],
    mode='lines',
    name='Sarah Cumulative Avg',
    line=dict(color='#bf8f15', width=1.5, dash='dot'),
    opacity=0.7
))

# --- Layout styled like FiveThirtyEight ---
fig.update_layout(
    xaxis_title='Date',
    yaxis_title='Time Score',
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
    title_font=dict(color='#696761'),
    range=[plot_min_date, plot_max_date]  # Set x-axis range with buffer
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
st.plotly_chart(fig, use_container_width=True, key="time_scores_chart")