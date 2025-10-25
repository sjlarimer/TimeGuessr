import streamlit as st
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
import numpy as np
import plotly.graph_objects as go



st.title("Total Scores")
data = pd.read_csv("./Data/Timeguessr_Stats_Final.csv")

# Get only the first row for each Timeguessr Day
df_daily = data.groupby("Timeguessr Day").first().reset_index()

# Drop NaN values for each player separately
mask = df_daily[["Date", "Michael Total Score", "Sarah Total Score"]].dropna()

# Sort by date (important for rolling calculations)
mask = mask.sort_values("Date").reset_index(drop=True)

# --- Rolling averages (5 games each) ---
mask["Michael Rolling Avg"] = mask["Michael Total Score"].rolling(window=5, min_periods=1).mean()
mask["Sarah Rolling Avg"] = mask["Sarah Total Score"].rolling(window=5, min_periods=1).mean()

# --- Cumulative averages (average of all games up to that point) ---
mask["Michael Cumulative Avg"] = mask["Michael Total Score"].expanding().mean()
mask["Sarah Cumulative Avg"] = mask["Sarah Total Score"].expanding().mean()

# Calculate wins (only for dates where both players have scores)
score_diff = mask["Michael Total Score"] - mask["Sarah Total Score"]

# Create wins_array: 'M' for Michael win, 'S' for Sarah win, 'T' for tie
wins_array = []
for diff in score_diff:
    if diff > 0:
        wins_array.append('M')
    elif diff < 0:
        wins_array.append('S')
    else:
        wins_array.append('T')

# Michael wins
michael_massive_wins = (score_diff > 10000).sum()
michael_big_wins = ((score_diff > 5000) & (score_diff <= 10000)).sum()
michael_small_wins = ((score_diff > 2500) & (score_diff <= 5000)).sum()
michael_close_wins = ((score_diff > 1000) & (score_diff <= 2500)).sum()
michael_very_close_wins = ((score_diff > 0) & (score_diff <= 1000)).sum()

# Sarah wins
sarah_massive_wins = (score_diff < -10000).sum()
sarah_big_wins = ((score_diff < -5000) & (score_diff >= -10000)).sum()
sarah_small_wins = ((score_diff < -2500) & (score_diff >= -5000)).sum()
sarah_close_wins = ((score_diff < -1000) & (score_diff >= -2500)).sum()
sarah_very_close_wins = ((score_diff < 0) & (score_diff >= -1000)).sum()

# Ties
ties = (score_diff == 0).sum()

# Total wins
michael_wins = michael_massive_wins + michael_big_wins + michael_small_wins + michael_close_wins + michael_very_close_wins
sarah_wins = sarah_massive_wins + sarah_big_wins + sarah_small_wins + sarah_close_wins + sarah_very_close_wins

# Create figure
fig = go.Figure()

# --- Scatter plots of scores ---
fig.add_trace(go.Scatter(
    x=df_daily["Date"],
    y=df_daily["Michael Total Score"],
    mode='markers',
    name='Michael Total Score',
    marker=dict(color='#6baed6', size=8),
    hovertemplate='Date: %{x}<br>Score: %{y}<extra></extra>'
))

fig.add_trace(go.Scatter(
    x=df_daily["Date"],
    y=df_daily["Sarah Total Score"],
    mode='markers',
    name='Sarah Total Score',
    marker=dict(color='#fd8d3c', size=8),
    hovertemplate='Date: %{x}<br>Score: %{y}<extra></extra>'
))

# --- Rolling average lines ---
fig.add_trace(go.Scatter(
    x=mask["Date"],
    y=mask["Michael Rolling Avg"],
    mode='lines',
    name='Michael 5-game Avg',
    line=dict(color='#08306b', width=2),
    hovertemplate='Date: %{x}<br>5-game Avg: %{y:.0f}<extra></extra>'
))

fig.add_trace(go.Scatter(
    x=mask["Date"],
    y=mask["Sarah Rolling Avg"],
    mode='lines',
    name='Sarah 5-game Avg',
    line=dict(color='#a63603', width=2),
    hovertemplate='Date: %{x}<br>5-game Avg: %{y:.0f}<extra></extra>'
))

# --- Faint dotted cumulative average lines ---
fig.add_trace(go.Scatter(
    x=mask["Date"],
    y=mask["Michael Cumulative Avg"],
    mode='lines',
    name='Michael Cumulative Avg',
    line=dict(color='#08306b', width=1.5, dash='dot'),
    opacity=0.7,
    hovertemplate='Date: %{x}<br>Cumulative Avg: %{y:.0f}<extra></extra>'
))

fig.add_trace(go.Scatter(
    x=mask["Date"],
    y=mask["Sarah Cumulative Avg"],
    mode='lines',
    name='Sarah Cumulative Avg',
    line=dict(color='#a63603', width=1.5, dash='dot'),
    opacity=0.7,
    hovertemplate='Date: %{x}<br>Cumulative Avg: %{y:.0f}<extra></extra>'
))

# Update layout
fig.update_layout(
    xaxis_title='Date',
    yaxis_title='Total Score',
    width=1400,
    height=600,
    hovermode='closest',
    template='plotly_white',
    showlegend=False,
    plot_bgcolor='#3d3d3d'
)

# Add grid
fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#575757')
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#575757')

# Display in Streamlit
st.plotly_chart(fig)