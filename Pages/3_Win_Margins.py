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

# --- Win Summary Table ---

# Define win conditions
michael_wins = mask_filtered[mask_filtered["Score Diff"] > 0]
sarah_wins = mask_filtered[mask_filtered["Score Diff"] < 0]

def recent_date(series):
    return series.max().strftime("%Y-%m-%d") if not series.empty else "-"

# --- Helper function to compute category counts and dates ---
def get_win_stats(df, lower, upper, is_michael=True):
    if is_michael:
        cond = (df["Score Diff"] > lower) & (df["Score Diff"] <= upper)
    else:
        cond = (df["Score Diff"] < -lower) & (df["Score Diff"] >= -upper)
    subset = df[cond]
    return len(subset), recent_date(subset["Date"])

# --- Calculate all tiers ---
michael_win_count = len(michael_wins)
sarah_win_count = len(sarah_wins)
michael_recent_win = recent_date(michael_wins["Date"])
sarah_recent_win = recent_date(sarah_wins["Date"])

michael_over_10k, michael_recent_10k = get_win_stats(michael_wins, 10000, np.inf, True)
sarah_over_10k, sarah_recent_10k = get_win_stats(sarah_wins, 10000, np.inf, False)

michael_5_10k, michael_recent_5_10k = get_win_stats(michael_wins, 5000, 10000, True)
sarah_5_10k, sarah_recent_5_10k = get_win_stats(sarah_wins, 5000, 10000, False)

michael_2_5k, michael_recent_2_5k = get_win_stats(michael_wins, 2500, 5000, True)
sarah_2_5k, sarah_recent_2_5k = get_win_stats(sarah_wins, 2500, 5000, False)

michael_1_2_5k, michael_recent_1_2_5k = get_win_stats(michael_wins, 1000, 2500, True)
sarah_1_2_5k, sarah_recent_1_2_5k = get_win_stats(sarah_wins, 1000, 2500, False)

michael_under_1k, michael_recent_under_1k = get_win_stats(michael_wins, 0, 1000, True)
sarah_under_1k, sarah_recent_under_1k = get_win_stats(sarah_wins, 0, 1000, False)

# --- Largest and Smallest Wins ---
michael_largest_win = michael_wins["Score Diff"].max() if not michael_wins.empty else "-"
michael_largest_date = michael_wins.loc[michael_wins["Score Diff"].idxmax(), "Date"].strftime("%Y-%m-%d") if not michael_wins.empty else "-"
michael_smallest_win = michael_wins["Score Diff"].min() if not michael_wins.empty else "-"
michael_smallest_date = michael_wins.loc[michael_wins["Score Diff"].idxmin(), "Date"].strftime("%Y-%m-%d") if not michael_wins.empty else "-"

sarah_largest_win = sarah_wins["Score Diff"].min() if not sarah_wins.empty else "-"
sarah_largest_date = sarah_wins.loc[sarah_wins["Score Diff"].idxmin(), "Date"].strftime("%Y-%m-%d") if not sarah_wins.empty else "-"
sarah_smallest_win = sarah_wins["Score Diff"].max() if not sarah_wins.empty else "-"
sarah_smallest_date = sarah_wins.loc[sarah_wins["Score Diff"].idxmax(), "Date"].strftime("%Y-%m-%d") if not sarah_wins.empty else "-"

# --- Styled HTML Table ---
win_summary_html = f"""
<style>
.streaks-table tbody tr {{
    cursor: pointer;
    transition: background-color 0.2s;
}}
.streaks-table tbody tr:hover {{
    background-color: #e0e0d1;
}}
.streaks-table tbody tr.selected {{
    background-color: #c0c0b0;
}}
</style>

<table class="streaks-table" style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;">
    <thead>
        <tr style="background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;">
            <th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Category</th>
            <th style="padding: 10px; text-align: center; color: #221e8f; font-weight: 600;">Michael</th>
            <th style="padding: 10px; text-align: center; color: #221e8f; font-weight: 600;">Date</th>
            <th style="padding: 10px; text-align: center; color: #bf8f15; font-weight: 600;">Sarah</th>
            <th style="padding: 10px; text-align: center; color: #bf8f15; font-weight: 600;">Date</th>
        </tr>
    </thead>
    <tbody>
        <tr style="border-bottom: 1px solid #d9d7cc;">
            <td style="padding: 8px; color: #696761;">Wins</td>
            <td style="padding: 8px; text-align: center; color: #221e8f;">{michael_win_count}</td>
            <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_recent_win}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15;">{sarah_win_count}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_recent_win}</td>
        </tr>
        <tr style="border-bottom: 1px solid #d9d7cc;">
            <td style="padding: 8px; color: #696761;">Massive Wins (>10k)</td>
            <td style="padding: 8px; text-align: center; color: #221e8f;">{michael_over_10k}</td>
            <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_recent_10k}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15;">{sarah_over_10k}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_recent_10k}</td>
        </tr>
        <tr style="border-bottom: 1px solid #d9d7cc;">
            <td style="padding: 8px; color: #696761;">Big Wins (5–10k)</td>
            <td style="padding: 8px; text-align: center; color: #221e8f;">{michael_5_10k}</td>
            <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_recent_5_10k}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15;">{sarah_5_10k}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_recent_5_10k}</td>
        </tr>
        <tr style="border-bottom: 1px solid #d9d7cc;">
            <td style="padding: 8px; color: #696761;">Small Wins (2.5–5k)</td>
            <td style="padding: 8px; text-align: center; color: #221e8f;">{michael_2_5k}</td>
            <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_recent_2_5k}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15;">{sarah_2_5k}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_recent_2_5k}</td>
        </tr>
        <tr style="border-bottom: 1px solid #d9d7cc;">
            <td style="padding: 8px; color: #696761;">Close Wins (1–2.5k)</td>
            <td style="padding: 8px; text-align: center; color: #221e8f;">{michael_1_2_5k}</td>
            <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_recent_1_2_5k}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15;">{sarah_1_2_5k}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_recent_1_2_5k}</td>
        </tr>
        <tr style="border-bottom: 1px solid #d9d7cc;">
            <td style="padding: 8px; color: #696761;">Very CLose Wins (&lt;1k)</td>
            <td style="padding: 8px; text-align: center; color: #221e8f;">{michael_under_1k}</td>
            <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_recent_under_1k}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15;">{sarah_under_1k}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_recent_under_1k}</td>
        </tr>
        <tr style="border-bottom: 1px solid #d9d7cc;">
            <td style="padding: 8px; color: #696761;">Largest Win</td>
            <td style="padding: 8px; text-align: center; color: #221e8f;">{michael_largest_win}</td>
            <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_largest_date}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15;">{abs(sarah_largest_win) if sarah_largest_win != '-' else '-'}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_largest_date}</td>
        </tr>
        <tr style="border-bottom: 1px solid #d9d7cc;">
            <td style="padding: 8px; color: #696761;">Smallest Win</td>
            <td style="padding: 8px; text-align: center; color: #221e8f;">{michael_smallest_win}</td>
            <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_smallest_date}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15;">{abs(sarah_smallest_win) if sarah_smallest_win != '-' else '-'}</td>
            <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_smallest_date}</td>
        </tr>
    </tbody>
</table>
"""

st.markdown(win_summary_html, unsafe_allow_html=True)

