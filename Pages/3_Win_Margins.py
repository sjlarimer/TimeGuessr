import streamlit as st
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime

st.title("Win Margins")

# --- Load data ---
data = pd.read_csv("./Data/Timeguessr_Stats.csv")

# Ensure Date column is datetime
data["Date"] = pd.to_datetime(data["Date"], errors="coerce")

# --- Get only the first row for each Timeguessr Day ---
df_daily = data.groupby("Timeguessr Day").first().reset_index()

# --- Drop NaN values for both players ---
mask = df_daily[["Date", "Michael Total Score", "Sarah Total Score"]].dropna()
mask = mask.sort_values("Date").reset_index(drop=True)

# --- Compute score difference (Michael − Sarah) ---
mask["Score Diff"] = mask["Michael Total Score"] - mask["Sarah Total Score"]

# --- Sidebar or top sliders ---
min_date, max_date = mask["Date"].min(), mask["Date"].max()

# --- Custom slider label color ---
st.markdown("""
    <style>
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

# --- Rolling average window slider ---
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

# --- Filter data ---
mask_filtered = mask[(mask["Date"] >= start_date) & (mask["Date"] <= end_date)].copy()

# --- Recalculate rolling & cumulative diffs ---
mask_filtered["Rolling Diff"] = mask_filtered["Score Diff"].rolling(window=window_length, min_periods=1).mean()
mask_filtered["Cumulative Diff"] = mask_filtered["Score Diff"].expanding().mean()

# --- Create figure ---
fig = go.Figure()

# --- Scatter points for each game ---
fig.add_trace(go.Scatter(
    x=mask_filtered["Date"],
    y=mask_filtered["Score Diff"],
    mode="markers",
    marker=dict(color="gray", opacity=0.4, size=7),
    name="Game Result (Michael − Sarah)",
    hovertemplate="Date: %{x}<br>Score Diff: %{y}<extra></extra>"
))

# --- Shaded win regions ---
fig.add_trace(go.Scatter(
    x=mask_filtered["Date"],
    y=np.where(mask_filtered["Score Diff"] > 0, mask_filtered["Score Diff"], 0),
    fill='tozeroy',
    mode='none',
    fillcolor='rgba(188, 176, 255, 0.6)',
    name='Michael Wins'
))

fig.add_trace(go.Scatter(
    x=mask_filtered["Date"],
    y=np.where(mask_filtered["Score Diff"] < 0, mask_filtered["Score Diff"], 0),
    fill='tozeroy',
    mode='none',
    fillcolor='rgba(252, 228, 167, 0.6)',
    name='Sarah Wins'
))

# --- Cumulative average line ---
fig.add_trace(go.Scatter(
    x=mask_filtered["Date"],
    y=mask_filtered["Cumulative Diff"],
    mode="lines",
    name="Cumulative Avg",
    line=dict(color="black", width=1.5, dash="dot"),
    opacity=0.7
))


# --- Data Segmentation Logic (Updated for Zero-Crossing Interpolation) ---

y = mask_filtered["Rolling Diff"]
dates = mask_filtered["Date"]
new_points = []

# 1. Detect sign changes between consecutive points
# Check where the product of consecutive y-values is negative (meaning a crossing occurred)
crossings = mask_filtered[np.sign(y.shift(1) * y).fillna(1) < 0].index

# 2. Calculate the exact zero-crossing point for each segment
for i in crossings:
    # Points involved are the previous index (i-1) and the current index (i)
    y1 = y.loc[i-1]
    x1 = dates.loc[i-1]
    y2 = y.loc[i]
    x2 = dates.loc[i]
    
    # Linear interpolation formula for x where y=0:
    # x0 = x1 - y1 * (x2 - x1) / (y2 - y1)
    
    # Convert date differences to total seconds for linear calculation
    date_diff_seconds = (x2 - x1).total_seconds()
    
    # Calculate the fraction of the way across the segment where y=0
    if y2 - y1 != 0:
        time_at_zero_seconds = date_diff_seconds * (0 - y1) / (y2 - y1)
        
        # Calculate the zero-crossing date (x1 + time_at_zero_seconds)
        x_zero = x1 + pd.Timedelta(time_at_zero_seconds, unit='s')
        
        new_row = {
            "Date": x_zero, 
            "Rolling Diff": 0.0,
            "Window Length": window_length
        }
        new_points.append(new_row)

# 3. Combine interpolated points with original data
if new_points:
    df_new_points = pd.DataFrame(new_points)
    mask_filtered = pd.concat([mask_filtered, df_new_points], ignore_index=True)
    # Sort by date to ensure line segments are drawn correctly
    mask_filtered = mask_filtered.sort_values(by="Date").reset_index(drop=True)

# 4. Apply the masking logic to the newly interpolated DataFrame
# Trace A: Blue when positive (Y >= 0)
# We include 0 in the positive trace to ensure continuity at the crossing point.
mask_filtered['Rolling Diff Pos'] = np.where(
    mask_filtered['Rolling Diff'] >= 0,
    mask_filtered['Rolling Diff'],
    np.nan
)

# Trace B: Red when negative (Y <= 0)
# We include 0 in the negative trace to ensure continuity at the crossing point.
mask_filtered['Rolling Diff Neg'] = np.where(
    mask_filtered['Rolling Diff'] <= 0,
    mask_filtered['Rolling Diff'],
    np.nan
)


# --- New Conditional Traces ---

# Trace 1: Blue when positive (Y >= 0)
fig.add_trace(go.Scatter(
    x=mask_filtered["Date"],
    y=mask_filtered["Rolling Diff Pos"],
    mode="lines",
    name=f"{window_length}-Game Rolling Avg (Positive)",
    line=dict(color="#221e8f", width=2.5),
    opacity=0.8,
    # Hide this specific trace from the legend since we are representing a single metric
    showlegend=False,
    hovertemplate='Date: %{x}<br>Rolling Avg: %{y:.1f}<extra></extra>'
))

# Trace 2: Red when negative (Y <= 0)
fig.add_trace(go.Scatter(
    x=mask_filtered["Date"],
    y=mask_filtered["Rolling Diff Neg"],
    mode="lines",
    name=f"{window_length}-Game Rolling Avg (Negative)",
    line=dict(color="#bf8f15", width=2.5),
    opacity=0.8,
    showlegend=False,
    hovertemplate='Date: %{x}<br>Rolling Avg: %{y:.1f}<extra></extra>'
))

# --- Formatting / Layout (FiveThirtyEight-like) ---
fig.add_hline(y=0, line=dict(color="#8f8d85", dash="dash", width=1))
fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Score Difference (Michael − Sarah)",
    width=1400,
    height=600,
    hovermode="closest",
    font=dict(family="Poppins, Arial, sans-serif", size=14, color="#000000"),
    paper_bgcolor="#eae8dc",
    plot_bgcolor="#d9d7cc",
    margin=dict(l=60, r=40, t=60, b=60),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(0,0,0,0)",
        font=dict(color="#696761")
    ),
)

# --- Gridlines and axes styling ---
fig.update_xaxes(
    showgrid=True,
    gridcolor="#bdbbb1",
    zeroline=False,
    linecolor="#8f8d85",
    tickcolor="#8f8d85",
    tickfont=dict(color="#696761"),
    title_font=dict(color="#696761")
)
# --- Determine symmetric y-axis range ---
y_max = max(abs(mask_filtered["Score Diff"].max()), abs(mask_filtered["Score Diff"].min()),
            abs(mask_filtered["Rolling Diff"].max()), abs(mask_filtered["Rolling Diff"].min()),
            abs(mask_filtered["Cumulative Diff"].max()), abs(mask_filtered["Cumulative Diff"].min()))

# Round y_max up to nearest 5000 for nicer ticks
y_max = np.ceil(y_max / 5000) * 5000

# Generate ticks every 5000, symmetric around 0
tick_vals = np.arange(-y_max, y_max + 1, 5000)
tick_text = [str(abs(int(t))) for t in tick_vals]

# Update y-axis
fig.update_yaxes(
    showgrid=True,
    gridcolor="#bdbbb1",
    zeroline=False,
    linecolor="#8f8d85",
    tickcolor="#8f8d85",
    tickfont=dict(color="#696761"),
    title_font=dict(color="#696761"),
    tickvals=tick_vals,
    ticktext=tick_text,
    range=[-y_max, y_max]
)



# --- Display in Streamlit ---
st.plotly_chart(fig, use_container_width=True, key="win_margins_chart")