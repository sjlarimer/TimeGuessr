import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
from typing import Tuple

# --- Configuration ---
st.set_page_config(page_title="Timeguessr Dashboard", layout="wide")

# --- Constants ---
COLORS = {
    'michael': '#221e8f',
    'michael_light': '#bcb0ff',
    'sarah': "#8a005c",
    'sarah_light': "#ff94bd",
    'time': '#007006',
    'time_light': '#7ccc80',
    'geography': '#9e5400',
    'geography_light': '#d1a971',
    'bg_paper': '#eae8dc',
    'bg_plot': '#d9d7cc',
    'grid': '#bdbbb1',
    'text': '#696761',
    'line': '#8f8d85'
}

FONT_CONFIG = dict(family='Poppins, Arial, sans-serif', size=14, color='#000000')

# --- Load CSS ---
css_path = Path("styles.css")
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Custom Styling ---
CUSTOM_STYLES = """
    <style>
        /* Slider labels and tooltips */
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
"""
st.markdown(CUSTOM_STYLES, unsafe_allow_html=True)

# --- Helper Functions ---
@st.cache_data
def load_data(filepath: str = "./Data/Timeguessr_Stats.csv") -> pd.DataFrame:
    """Load and preprocess data with caching."""
    try:
        data = pd.read_csv(filepath)
        data["Date"] = pd.to_datetime(data["Date"])
        data = data.sort_values("Date").reset_index(drop=True)
        return data
    except FileNotFoundError:
        st.error(f"Data file not found at {filepath}")
        st.stop()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

def prepare_player_data(data: pd.DataFrame, player: str, remove_estimated: bool = False) -> pd.DataFrame:
    """Prepare time and geography data for a specific player."""
    data = data.copy()
    
    # Filter out estimated scores if toggle is on
    if remove_estimated:
        time_min_col = f"{player} Time Score (Min)"
        time_max_col = f"{player} Time Score (Max)"
        geo_min_col = f"{player} Geography Score (Min)"
        geo_max_col = f"{player} Geography Score (Max)"
        
        # Remove dates with estimated time scores
        estimated_time_dates = data[data[time_min_col] != data[time_max_col]]["Date"].unique()
        data.loc[data["Date"].isin(estimated_time_dates), [time_min_col, time_max_col]] = np.nan
        
        # Remove dates with estimated geography scores
        estimated_geo_dates = data[data[geo_min_col] != data[geo_max_col]]["Date"].unique()
        data.loc[data["Date"].isin(estimated_geo_dates), [geo_min_col, geo_max_col]] = np.nan
    
    # Compute midpoints per round
    data[f"{player} Time Midpoint"] = (
        data[f"{player} Time Score (Min)"] + data[f"{player} Time Score (Max)"]
    ) / 2
    data[f"{player} Geography Midpoint"] = (
        data[f"{player} Geography Score (Min)"] + data[f"{player} Geography Score (Max)"]
    ) / 2
    
    # Sum midpoints per day
    daily_cols = [f"{player} Time Midpoint", f"{player} Geography Midpoint"]
    df_daily = (
        data.groupby("Date")[daily_cols]
        .sum(min_count=1)
        .reset_index()
    )
    
    df_daily = df_daily.sort_values("Date").reset_index(drop=True)
    
    # Only include days where the player has both time and geography scores
    mask = df_daily[
        df_daily[f"{player} Time Midpoint"].notna() & 
        df_daily[f"{player} Geography Midpoint"].notna()
    ].copy()
    
    return mask

def calculate_rolling_averages(df: pd.DataFrame, window_length: int, player: str) -> pd.DataFrame:
    """Calculate rolling and cumulative averages for time and geography."""
    df = df.copy()
    
    time_col = f"{player} Time Midpoint"
    geo_col = f"{player} Geography Midpoint"
    
    if time_col in df.columns:
        df[f"{player} Time Rolling Avg"] = df[time_col].rolling(window=window_length, min_periods=1).mean()
        df[f"{player} Time Cumulative Avg"] = df[time_col].expanding().mean()
    
    if geo_col in df.columns:
        df[f"{player} Geography Rolling Avg"] = df[geo_col].rolling(window=window_length, min_periods=1).mean()
        df[f"{player} Geography Cumulative Avg"] = df[geo_col].expanding().mean()
    
    return df

def create_plotly_figure(df: pd.DataFrame, window_length: int, player: str) -> go.Figure:
    """Create the main Plotly figure showing time vs geography."""
    fig = go.Figure()
    
    player_color = COLORS['michael'] if player == "Michael" else COLORS['sarah']
    player_light = COLORS['michael_light'] if player == "Michael" else COLORS['sarah_light']
    
    time_col = f"{player} Time Midpoint"
    geo_col = f"{player} Geography Midpoint"
    
    # Always use sequential integers for equal spacing
    x_values = list(range(len(df)))
    
    # Create custom tick positions for first day of each month
    df_copy = df.copy()
    df_copy['month_year'] = df_copy['Date'].dt.to_period('M')
    first_of_month_indices = df_copy.groupby('month_year').head(1).index.tolist()
    
    tickvals = [i for i, idx in enumerate(df.index) if idx in first_of_month_indices]
    ticktext = [df.iloc[i]['Date'].strftime('%b %Y') for i in tickvals]

    # Scatter plots for Time
    fig.add_trace(go.Scatter(
        x=x_values, y=df[time_col],
        mode='markers', name='Time Score',
        marker=dict(color=COLORS['time_light'], size=8),
        customdata=df["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Time Score: %{y}<extra></extra>'
    ))
    
    # Scatter plots for Geography
    fig.add_trace(go.Scatter(
        x=x_values, y=df[geo_col],
        mode='markers', name='Geography Score',
        marker=dict(color=COLORS['geography_light'], size=8),
        customdata=df["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Geography Score: %{y}<extra></extra>'
    ))

    # Rolling average lines for Time
    fig.add_trace(go.Scatter(
        x=x_values, y=df[f"{player} Time Rolling Avg"],
        mode='lines', name=f'Time {window_length}-game Avg',
        line=dict(color=COLORS['time'], width=2.5),
        customdata=df["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Time Rolling Avg: %{y:.0f}<extra></extra>'
    ))
    
    # Rolling average lines for Geography
    fig.add_trace(go.Scatter(
        x=x_values, y=df[f"{player} Geography Rolling Avg"],
        mode='lines', name=f'Geography {window_length}-game Avg',
        line=dict(color=COLORS['geography'], width=2.5),
        customdata=df["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Geography Rolling Avg: %{y:.0f}<extra></extra>'
    ))

    # Cumulative average lines for Time
    fig.add_trace(go.Scatter(
        x=x_values, y=df[f"{player} Time Cumulative Avg"],
        mode='lines', name='Time Cumulative Avg',
        line=dict(color=COLORS['time'], width=1.5, dash='dot'),
        opacity=0.7,
        customdata=df["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Time Cumulative Avg: %{y:.0f}<extra></extra>'
    ))
    
    # Cumulative average lines for Geography
    fig.add_trace(go.Scatter(
        x=x_values, y=df[f"{player} Geography Cumulative Avg"],
        mode='lines', name='Geography Cumulative Avg',
        line=dict(color=COLORS['geography'], width=1.5, dash='dot'),
        opacity=0.7,
        customdata=df["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Geography Cumulative Avg: %{y:.0f}<extra></extra>'
    ))

    # Layout
    fig.update_layout(
        xaxis_title='Date', 
        yaxis_title='Score',
        width=1400, height=600, hovermode='closest',
        font=FONT_CONFIG,
        paper_bgcolor=COLORS['bg_paper'],
        plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=40, t=60, b=60),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02,
            xanchor='right', x=1,
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text'])
        ),
    )

    # Gridlines and axes
    axis_config = dict(
        showgrid=True, gridcolor=COLORS['grid'],
        zeroline=False, linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text'])
    )
    
    # X-axis with custom month ticks
    fig.update_xaxes(
        **axis_config,
        tickmode='array',
        tickvals=tickvals,
        ticktext=ticktext
    )
    
    fig.update_yaxes(**axis_config)

    return fig

# --- Main App ---

st.markdown(
    """
    <style>
    /* Hide the label */
    div[data-testid="stSelectbox"] > label {
        display: none !important;
    }

    /* Remove default Streamlit select styling */
    div[data-baseweb="select"] > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        width: fit-content !important;
        min-width: 0 !important;
        overflow: visible !important;
    }

    /* Style visible select text */
    div[data-baseweb="select"] > div > div {
        height: auto !important;
        min-height: 90px !important;
        display: flex !important;
        align-items: flex-end !important;
        padding: 8px 4px 14px 4px !important;
        font-size: 46px !important;
        font-weight: 800 !important;
        color: #db5049 !important;
        text-align: left !important;
        line-height: 1.2em !important;
        width: fit-content !important;
        overflow: visible !important;
    }

    /* Make sure dropdown list aligns left */
    div[data-baseweb="popover"] {
        text-align: left !important;
    }

    /* Adjust dropdown arrow */
    div[data-baseweb="select"] svg {
        width: 24px !important;
        height: 24px !important;
        margin-left: 6px;
    }

    /* Prevent container clipping */
    div[data-testid="stSelectbox"] {
        display: inline-block !important;
        width: auto !important;
        overflow: visible !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

player = st.selectbox(
    "",
    options=["Michael", "Sarah"],
    index=0,
    key="player_selector",
)

# Load data
data = load_data()

# Toggle for removing estimated scores
remove_estimated = st.toggle("Remove Estimated Scores", value=False, key="remove_estimated_toggle")

# Prepare data for selected player
player_data = prepare_player_data(data, player, remove_estimated)

# Date range
min_date, max_date = player_data["Date"].min(), player_data["Date"].max()

# Controls
window_length = st.slider(
    "Rolling Average Window (Games):",
    min_value=1, max_value=30, value=5, step=1
)

# Date range slider
start_date, end_date = st.slider(
    "Select Date Range:",
    min_value=min_date.to_pydatetime(),
    max_value=max_date.to_pydatetime(),
    value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
    format="YYYY-MM-DD"
)

# Filter data by date range
player_data_filtered = player_data[(player_data["Date"] >= start_date) & (player_data["Date"] <= end_date)].copy()

# Calculate averages
player_data_filtered = calculate_rolling_averages(player_data_filtered, window_length, player)

def create_win_margins_figure(mask_filtered: pd.DataFrame, window_length: int, player: str) -> go.Figure:
    """Create the win margins Plotly figure for Time vs Geography."""
    fig = go.Figure()
    
    # Create equidistant x-axis indices
    mask_filtered = mask_filtered.copy()
    mask_filtered["x_index"] = np.arange(len(mask_filtered))
    
    # Scatter points for each game
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"],
        y=mask_filtered["Score Diff"],
        mode="markers",
        marker=dict(
            color="gray",
            opacity=0.4,
            size=7
        ),
        name="Game Result (Time − Geography)",
        customdata=mask_filtered["Date"],
        hovertemplate="Date: %{customdata|%Y-%m-%d}<br>Score Diff: %{y}<extra></extra>"
    ))
    
    # Shaded win regions
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"],
        y=np.where(mask_filtered["Score Diff"] > 0, mask_filtered["Score Diff"], 0),
        fill='tozeroy',
        mode='none',
        fillcolor='rgba(152, 223, 138, 0.6)',  # Green for time wins
        name='Time Wins'
    ))
    
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"],
        y=np.where(mask_filtered["Score Diff"] < 0, mask_filtered["Score Diff"], 0),
        fill='tozeroy',
        mode='none',
        fillcolor='rgba(255, 187, 120, 0.6)',  # Orange for geography wins
        name='Geography Wins'
    ))
    
    # Cumulative average line
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"],
        y=mask_filtered["Cumulative Diff"],
        mode="lines",
        name="Cumulative Avg",
        line=dict(color="black", width=1.5, dash="dot"),
        opacity=0.7,
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Cumulative Avg: %{y:.1f}<extra></extra>'
    ))
    
    # Rolling average - positive segment (time winning)
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"],
        y=mask_filtered["Rolling Diff Pos"],
        mode="lines",
        name=f"{window_length}-Game Rolling Avg",
        line=dict(color=COLORS['time'], width=2.5),
        opacity=0.8,
        showlegend=False,
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Rolling Avg: %{y:.1f}<extra></extra>'
    ))
    
    # Rolling average - negative segment (geography winning)
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"],
        y=mask_filtered["Rolling Diff Neg"],
        mode="lines",
        name=f"{window_length}-Game Rolling Avg",
        line=dict(color=COLORS['geography'], width=2.5),
        opacity=0.8,
        showlegend=False,
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Rolling Avg: %{y:.1f}<extra></extra>'
    ))
    
    # Determine symmetric y-axis range
    y_max = max(
        abs(mask_filtered["Score Diff"].max()),
        abs(mask_filtered["Score Diff"].min()),
        abs(mask_filtered["Rolling Diff"].max()),
        abs(mask_filtered["Rolling Diff"].min()),
        abs(mask_filtered["Cumulative Diff"].max()),
        abs(mask_filtered["Cumulative Diff"].min())
    )
    
    # Round y_max up to nearest 2500
    y_max = np.ceil(y_max / 2500) * 2500
    tick_vals = np.arange(-y_max, y_max + 1, 2500)
    tick_text = [str(abs(int(t))) for t in tick_vals]
    
    # Layout
    fig.add_hline(y=0, line=dict(color="#8f8d85", dash="dash", width=1))
    
    # Determine x-axis tick positions at the start of each month
    df_copy = mask_filtered.copy()
    df_copy['month_year'] = df_copy['Date'].dt.to_period('M')
    first_of_month_indices = df_copy.groupby('month_year').head(1).index.tolist()
    
    tickvals = [mask_filtered.loc[idx, "x_index"] for idx in first_of_month_indices]
    ticktext = [mask_filtered.loc[idx, 'Date'].strftime('%b %Y') for idx in first_of_month_indices]
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Score Difference (Time − Geography)",
        width=1400,
        height=600,
        hovermode="closest",
        font=FONT_CONFIG,
        paper_bgcolor=COLORS['bg_paper'],
        plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=40, t=60, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            font=dict(color=COLORS['text'])
        ),
    )
    
    # Axes styling
    fig.update_xaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=False,
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        tickmode='array',
        tickvals=tickvals,
        ticktext=ticktext,
        tickangle=-45
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=False,
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        tickvals=tick_vals,
        ticktext=tick_text,
        range=[-y_max, y_max]
    )
    
    return fig

def add_zero_crossing_interpolation(mask_filtered: pd.DataFrame, window_length: int) -> pd.DataFrame:
    """Add interpolated zero-crossing points for smooth line transitions."""
    mask_filtered = mask_filtered.reset_index(drop=True)
    
    y = mask_filtered["Rolling Diff"]
    dates = mask_filtered["Date"]
    new_points = []
    
    # Detect sign changes
    crossings_mask = np.sign(y.shift(1) * y).fillna(1) < 0
    crossing_indices = mask_filtered[crossings_mask].index.tolist()
    
    # Calculate exact zero-crossing points
    for i in crossing_indices:
        if i == 0:
            continue
            
        y1 = y.iloc[i-1]
        x1 = dates.iloc[i-1]
        y2 = y.iloc[i]
        x2 = dates.iloc[i]
        
        cum1 = mask_filtered["Cumulative Diff"].iloc[i-1]
        cum2 = mask_filtered["Cumulative Diff"].iloc[i]
        
        score1 = mask_filtered["Score Diff"].iloc[i-1]
        score2 = mask_filtered["Score Diff"].iloc[i]
        
        date_diff_seconds = (x2 - x1).total_seconds()
        
        if y2 - y1 != 0:
            fraction = (0 - y1) / (y2 - y1)
            
            time_at_zero_seconds = date_diff_seconds * fraction
            x_zero = x1 + pd.Timedelta(time_at_zero_seconds, unit='s')
            
            cum_zero = cum1 + fraction * (cum2 - cum1)
            score_zero = score1 + fraction * (score2 - score1)
            
            new_points.append({
                "Date": x_zero, 
                "Rolling Diff": 0.0,
                "Score Diff": score_zero,
                "Cumulative Diff": cum_zero
            })
    
    # Combine and sort
    if new_points:
        df_new_points = pd.DataFrame(new_points)
        mask_filtered = pd.concat([mask_filtered, df_new_points], ignore_index=True)
        mask_filtered = mask_filtered.sort_values(by="Date").reset_index(drop=True)
    
    # Create positive and negative traces
    mask_filtered['Rolling Diff Pos'] = np.where(
        mask_filtered['Rolling Diff'] >= 0,
        mask_filtered['Rolling Diff'],
        np.nan
    )
    mask_filtered['Rolling Diff Neg'] = np.where(
        mask_filtered['Rolling Diff'] <= 0,
        mask_filtered['Rolling Diff'],
        np.nan
    )
    
    return mask_filtered

# Display main chart
fig = create_plotly_figure(player_data_filtered, window_length, player)
st.plotly_chart(fig, use_container_width=True, key="main_chart")

# Prepare margin data
margin_data = player_data_filtered.copy()
margin_data["Score Diff"] = margin_data[f"{player} Time Midpoint"] - margin_data[f"{player} Geography Midpoint"]
margin_data["Rolling Diff"] = margin_data["Score Diff"].rolling(window=window_length, min_periods=1).mean()
margin_data["Cumulative Diff"] = margin_data["Score Diff"].expanding().mean()

# Add zero-crossing interpolation
margin_data = add_zero_crossing_interpolation(margin_data, window_length)

# Create and display margin figure
margin_fig = create_win_margins_figure(margin_data, window_length, player)
st.plotly_chart(margin_fig, use_container_width=True, key="margin_chart")