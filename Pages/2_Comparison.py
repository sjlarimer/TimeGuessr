import os
import streamlit as st
from background import set_random_sarah_background

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from typing import Tuple, List, Dict
import time
import scipy.stats as stats

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
CEILING_TOTAL = 50000
CEILING_TIME = 25000
CEILING_GEOGRAPHY = 25000

# --- Load CSS ---
from utils import load_css
load_css()

# --- Custom Styling ---
CUSTOM_STYLES = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800;900&display=swap');

        /* Main view title (Total/Time/Geography Scores, Win Margins, or
           "<Player> Scores"), styled to match the Edition Date title on the
           Daily page — same bold uppercase Poppins treatment and the double-
           line underline, so both pages' top headers read as one family. */
        .page-title { font-family: 'Poppins', sans-serif; font-weight: 900; font-size: 48px; color: #111; letter-spacing: -1px; margin: 0; text-transform: uppercase; text-align: center; }
        .page-title-stack { width: max-content; max-width: 95%; margin: 0 auto 20px auto; padding-bottom: 10px; border-bottom: 4px double #ccc; }

        /* Slider labels and tooltips */
        div[data-testid="stSlider"] > label,
        div[data-testid="stSelectSlider"] > label {
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
        
        /* Table styling */
        .stats-table tbody tr, .streaks-table tbody tr {
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .stats-table tbody tr:hover, .streaks-table tbody tr:hover {
            background-color: #e0e0d1;
        }
        .stats-table tbody tr.selected, .streaks-table tbody tr.selected {
            background-color: #c0c0b0;
        }
        /* Toggle label styling */
        [data-testid="stSidebar"] div[data-testid="stToggle"] label p,
        [data-testid="stSidebar"] div[data-testid="stCheckbox"] label p {
            color: #696761 !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }
        /* View mode pill toggle buttons */
        [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
        [data-testid="stSidebar"] button[kind="primary"] {
            background-color: #3a3935 !important;
            color: #eae8dc !important;
            border-color: #3a3935 !important;
            border-radius: 20px !important;
            font-weight: 600 !important;
        }
        [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
        [data-testid="stSidebar"] button[kind="secondary"] {
            background-color: #d9d7cc !important;
            color: #696761 !important;
            border-color: #d9d7cc !important;
            border-radius: 20px !important;
            font-weight: 500 !important;
        }
        [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover,
        [data-testid="stSidebar"] button[kind="secondary"]:hover {
            background-color: #c8c6bb !important;
            color: #3a3935 !important;
            border-color: #8f8d85 !important;
        }
        /* The sidebar's blanket `* { color: white }` rule (styles.css) targets
           these buttons' inner label text directly, which beats the color set
           on the <button> itself via inheritance — so it has to be re-asserted
           on the descendants too, or secondary (light pill) labels render
           invisible white-on-light. */
        [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] *,
        [data-testid="stSidebar"] button[kind="primary"] * {
            color: #eae8dc !important;
        }
        [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] *,
        [data-testid="stSidebar"] button[kind="secondary"] * {
            color: #696761 !important;
        }
        [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover *,
        [data-testid="stSidebar"] button[kind="secondary"]:hover * {
            color: #3a3935 !important;
        }
        /* Plotly chart rounded container — same border/radius/spacing as the
           Momentum box and other HTML cards (COLORS['bg_plot'] = #d9d7cc) */
        div[data-testid="stPlotlyChart"] {
            border-radius: 12px !important;
            border: 1px solid #d9d7cc !important;
            overflow: hidden !important;
            margin-top: 20px !important;
        }
        /* Cumulative Average Streak card: a real bordered container (not just
           a plotly card) so its mode toggle + slider can sit inside the same
           box as the chart, top-right, instead of floating above it. */
        .st-key-cumavg_streak_box {
            margin-top: 20px;
            padding: 15px;
            background-color: #eae8dc;
            border-radius: 12px;
            border: 1px solid #d9d7cc;
        }
        /* The chart nested inside already has the card's own border/background,
           so drop its separate card styling to avoid a box-in-a-box look. */
        .st-key-cumavg_streak_box div[data-testid="stPlotlyChart"] {
            border: none !important;
            margin-top: 0 !important;
        }
        /* Combined ≥X / ≤X box: two related charts side by side in one card,
           each keeping its own in-chart title, with an Above/Below toggle. */
        .st-key-threshold_pair_box {
            margin-top: 20px;
            padding: 15px;
            background-color: #eae8dc;
            border-radius: 12px;
            border: 1px solid #d9d7cc;
        }
        .st-key-threshold_pair_box div[data-testid="stPlotlyChart"] {
            border: none !important;
            margin-top: 0 !important;
        }
        /* Compact mode toggle buttons within a card header — plain black/white,
           overriding Streamlit's default red primary color */
        .st-key-cumavg_streak_toggle button,
        .st-key-threshold_pair_toggle button {
            padding: 2px 6px !important;
            min-height: 0 !important;
            font-size: 11px !important;
            white-space: nowrap !important;
        }
        .st-key-cumavg_streak_toggle button[kind="primary"],
        .st-key-threshold_pair_toggle button[kind="primary"] {
            background-color: #3a3935 !important;
            color: #eae8dc !important;
            border-color: #3a3935 !important;
        }
        .st-key-cumavg_streak_toggle button[kind="secondary"],
        .st-key-threshold_pair_toggle button[kind="secondary"] {
            background-color: #eae8dc !important;
            color: #3a3935 !important;
            border-color: #8f8d85 !important;
        }
        .st-key-cumavg_streak_toggle button[kind="secondary"]:hover,
        .st-key-threshold_pair_toggle button[kind="secondary"]:hover {
            background-color: #d9d7cc !important;
            color: #3a3935 !important;
            border-color: #696761 !important;
        }
        /* Any card-header slider (container key ending "_slider") — plain
           black/white instead of Streamlit's default red track fill/thumb.
           A single attribute-contains selector instead of one clause per
           key, so a new "..._slider" container picks this up automatically. */
        div[class*="st-key-"][class*="_slider"] div[data-baseweb="slider"] [role="slider"] {
            background-color: #3a3935 !important;
            border-color: #3a3935 !important;
            box-shadow: none !important;
        }
        /* The track's filled/unfilled split is painted as a two-color
           linear-gradient (background-image, not background-color) on this
           specific div (identified by its inline height), so it needs its
           own targeted override — flattened to one plain gray bar. Earlier
           this used a broad "> div > div" selector that also (wrongly)
           painted a gray box behind the min/max tick labels below it. */
        div[class*="st-key-"][class*="_slider"] div[data-baseweb="slider"] div[style*="0.25rem"] {
            background-image: none !important;
            background-color: #c8c6bb !important;
        }
        div[class*="st-key-"][class*="_slider"] div[data-testid="stSliderTickBar"],
        div[class*="st-key-"][class*="_slider"] div[data-testid="stSliderTickBar"] div {
            background-color: transparent !important;
        }
        div[class*="st-key-"][class*="_slider"] div[data-testid="stSliderTickBar"] p,
        div[class*="st-key-"][class*="_slider"] div[data-testid="stSliderThumbValue"] p {
            color: #696761 !important;
            background-color: transparent !important;
        }
        /* Main chart box — wraps the top scatter/rolling-average chart so its
           own rolling-window slider can sit top-right, inside the same card. */
        .st-key-main_chart_box {
            margin-top: 20px;
            padding: 15px;
            background-color: #eae8dc;
            border-radius: 12px;
            border: 1px solid #d9d7cc;
        }
        .st-key-main_chart_box div[data-testid="stPlotlyChart"] {
            border: none !important;
            margin-top: 0 !important;
        }
        /* Momentum box — now a real container (not raw HTML) so the games
           slider can live inside it alongside the title/score summary. */
        .st-key-momentum_box {
            margin-top: 20px;
            padding: 15px;
            background-color: #eae8dc;
            border-radius: 12px;
            border: 1px solid #d9d7cc;
        }
        /* Full-width Score Distribution box, matching the other cards */
        .st-key-score_dist_box {
            margin-top: 20px;
            padding: 15px;
            background-color: #eae8dc;
            border-radius: 12px;
            border: 1px solid #d9d7cc;
        }
        .st-key-score_dist_box div[data-testid="stPlotlyChart"] {
            border: none !important;
            margin-top: 0 !important;
        }
        /* Combined Instability / Stability box: two related charts side by
           side in one card, each keeping its own in-chart title. */
        .st-key-stability_pair_box {
            margin-top: 20px;
            padding: 15px;
            background-color: #eae8dc;
            border-radius: 12px;
            border: 1px solid #d9d7cc;
        }
        .st-key-stability_pair_box div[data-testid="stPlotlyChart"] {
            border: none !important;
            margin-top: 0 !important;
        }
    </style>
"""
st.markdown(CUSTOM_STYLES, unsafe_allow_html=True)

set_random_sarah_background(__file__, lightness_level=0.7)

# --- Helper Functions ---
@st.cache_data
def load_data(filepath: str = "./Data/Timeguessr_Stats.csv", mtime: float = 0) -> pd.DataFrame:
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

def filter_by_score_range(df: pd.DataFrame, score_min: int, score_max: int, score_type: str = "total", include_single: bool = False) -> pd.DataFrame:
    """Filter dataframe by score range for both players."""
    df = df.copy()
    
    if score_type == "total":
        michael_col = "Michael Total Score"
        sarah_col = "Sarah Total Score"
    elif score_type == "time":
        michael_col = "Michael Time Midpoint"
        sarah_col = "Sarah Time Midpoint"
    else:  # geography
        michael_col = "Michael Geography Midpoint"
        sarah_col = "Sarah Geography Midpoint"
    
    if include_single:
        # Keep rows where at least one player's score is within range
        # But set out-of-range scores to NaN
        mask = (
            ((df[michael_col] >= score_min) & (df[michael_col] <= score_max)) |
            ((df[sarah_col] >= score_min) & (df[sarah_col] <= score_max))
        )
        
        df = df[mask].copy()
        
        # Set out-of-range scores to NaN
        df.loc[(df[michael_col] < score_min) | (df[michael_col] > score_max), michael_col] = np.nan
        df.loc[(df[sarah_col] < score_min) | (df[sarah_col] > score_max), sarah_col] = np.nan
    else:
        # Remove entire day if ANY score is outside range
        # Only keep days where BOTH players have scores AND both are in range
        mask = (
            (df[michael_col].notna()) & 
            (df[sarah_col].notna()) &
            (df[michael_col] >= score_min) & (df[michael_col] <= score_max) &
            (df[sarah_col] >= score_min) & (df[sarah_col] <= score_max)
        )
        
        df = df[mask].copy()
    
    return df

def prepare_total_scores_data(data: pd.DataFrame, include_single: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare data for Total Scores view."""
    df_daily = data.groupby("Timeguessr Day").first().reset_index()
    
    community_col = ["Community Average"] if "Community Average" in df_daily.columns else []

    if include_single:
        # Include all days with at least one score
        mask = df_daily[
            df_daily["Michael Total Score"].notna() | df_daily["Sarah Total Score"].notna()
        ][["Date", "Michael Total Score", "Sarah Total Score"] + community_col].copy()
    else:
        # Only include days where BOTH players have scores
        mask = df_daily[
            df_daily["Michael Total Score"].notna() & df_daily["Sarah Total Score"].notna()
        ][["Date", "Michael Total Score", "Sarah Total Score"] + community_col].copy()
    
    mask = mask.sort_values("Date").reset_index(drop=True)
    return df_daily, mask

def prepare_time_scores_data(data: pd.DataFrame, remove_estimated: bool = False, include_single: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare data for Time Scores view."""
    data = data.copy()
    
    # Filter out estimated scores if toggle is on
    if remove_estimated:
        for player in ["Michael", "Sarah"]:
            min_col = f"{player} Time Score (Min)"
            max_col = f"{player} Time Score (Max)"
            
            estimated_dates = data[data[min_col] != data[max_col]]["Date"].unique()
            data.loc[data["Date"].isin(estimated_dates), [min_col, max_col]] = np.nan
    
    # Compute midpoints per round
    for player in ["Michael", "Sarah"]:
        data[f"{player} Time Midpoint"] = (
            data[f"{player} Time Score (Min)"] + data[f"{player} Time Score (Max)"]
        ) / 2
    
    # Sum midpoints per day
    daily_cols = ["Michael Time Midpoint", "Sarah Time Midpoint"]
    df_daily = (
        data.groupby("Date")[daily_cols]
        .sum(min_count=1)
        .reset_index()
    )
    
    df_daily = df_daily.sort_values("Date").reset_index(drop=True)
    
    if include_single:
        # Include all days with at least one score
        mask = df_daily[
            df_daily["Michael Time Midpoint"].notna() | df_daily["Sarah Time Midpoint"].notna()
        ][["Date", "Michael Time Midpoint", "Sarah Time Midpoint"]].copy()
    else:
        # Only include days where BOTH players have data
        mask = df_daily[
            df_daily["Michael Time Midpoint"].notna() & df_daily["Sarah Time Midpoint"].notna()
        ][["Date", "Michael Time Midpoint", "Sarah Time Midpoint"]].copy()
    
    mask = mask.sort_values("Date").reset_index(drop=True)
    return df_daily, mask

def prepare_geography_scores_data(data: pd.DataFrame, remove_estimated: bool = False, include_single: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare data for Geography Scores view."""
    data = data.copy()
    
    # Filter out estimated scores if toggle is on
    if remove_estimated:
        for player in ["Michael", "Sarah"]:
            min_col = f"{player} Geography Score (Min)"
            max_col = f"{player} Geography Score (Max)"
            
            estimated_dates = data[data[min_col] != data[max_col]]["Date"].unique()
            data.loc[data["Date"].isin(estimated_dates), [min_col, max_col]] = np.nan
    
    # Compute midpoints per round
    for player in ["Michael", "Sarah"]:
        data[f"{player} Geography Midpoint"] = (
            data[f"{player} Geography Score (Min)"] + data[f"{player} Geography Score (Max)"]
        ) / 2
    
    # Sum midpoints per day
    daily_cols = ["Michael Geography Midpoint", "Sarah Geography Midpoint"]
    df_daily = (
        data.groupby("Date")[daily_cols]
        .sum(min_count=1)
        .reset_index()
    )
    
    df_daily = df_daily.sort_values("Date").reset_index(drop=True)
    
    if include_single:
        # Include all days with at least one score
        mask = df_daily[
            df_daily["Michael Geography Midpoint"].notna() | df_daily["Sarah Geography Midpoint"].notna()
        ][["Date", "Michael Geography Midpoint", "Sarah Geography Midpoint"]].copy()
    else:
        # Only include days where BOTH players have data
        mask = df_daily[
            df_daily["Michael Geography Midpoint"].notna() & df_daily["Sarah Geography Midpoint"].notna()
        ][["Date", "Michael Geography Midpoint", "Sarah Geography Midpoint"]].copy()
    
    mask = mask.sort_values("Date").reset_index(drop=True)
    return df_daily, mask

def get_daily_data(data: pd.DataFrame) -> pd.DataFrame:
    """Get first row for each Timeguessr Day."""
    df_daily = data.groupby("Timeguessr Day").first().reset_index()
    mask = df_daily[["Date", "Michael Total Score", "Sarah Total Score"]].dropna()
    return mask.sort_values("Date").reset_index(drop=True)

def calculate_rolling_averages(df: pd.DataFrame, window_length: int, score_type: str = "total") -> pd.DataFrame:
    """Calculate rolling and cumulative averages."""
    df = df.copy()
    
    if score_type == "total":
        columns = {
            "Michael": "Michael Total Score",
            "Sarah": "Sarah Total Score",
            "Community": "Community Average"
        }
    elif score_type == "time":
        columns = {
            "Michael": "Michael Time Midpoint",
            "Sarah": "Sarah Time Midpoint"
        }
    else:  # geography
        columns = {
            "Michael": "Michael Geography Midpoint",
            "Sarah": "Sarah Geography Midpoint"
        }
    
    for player, col in columns.items():
        if col in df.columns:
            df[f"{player} Rolling Avg"] = df[col].rolling(window=window_length, min_periods=1).mean()
            df[f"{player} Cumulative Avg"] = df[col].expanding().mean()
    
    return df

def can_use_month_day_format(dates: pd.Series) -> bool:
    """Check if month-day format is unambiguous."""
    month_years = dates.dt.to_period("M")
    month_to_years = {}
    for period in month_years:
        month_to_years.setdefault(period.month, set()).add(period.year)
    return all(len(years) == 1 for years in month_to_years.values())

def calculate_streak_with_dates(scores: np.ndarray, dates: pd.Series,
                                threshold: float, above: bool = True, 
                                date_format: str = "%b %d, %Y") -> Tuple[int, str, str]:
    """Calculate longest streak above/below threshold with date range."""
    max_streak = 0
    current_streak = 0
    max_start_idx = 0
    max_end_idx = 0
    current_start_idx = 0

    for i, score in enumerate(scores):
        condition = (above and score >= threshold) or (not above and score < threshold)
        
        if condition:
            if current_streak == 0:
                current_start_idx = i
            current_streak += 1

            if current_streak > max_streak or (current_streak == max_streak and i > max_end_idx):
                max_streak = current_streak
                max_start_idx = current_start_idx
                max_end_idx = i
        else:
            current_streak = 0

    if max_streak > 0:
        start_date = dates.iloc[max_start_idx].strftime(date_format)
        end_date = dates.iloc[max_end_idx].strftime(date_format)
        return max_streak, start_date, end_date

    return 0, "", ""

def format_bucket_label(lower: int, upper: int, bin_size: int, is_top: bool = False) -> str:
    """Format bucket label based on range. Always spells out the full
    lower-upper span (e.g. "41k-42k", not just "41k") so it's unambiguous
    whether a single value or a bucket is being described — a bare "41k"
    previously stood in for "41k-42k" whenever bin_size was exactly 1000,
    which read like an exact score rather than a range."""
    if is_top:
        return f"Scores {lower//1000}k+" if lower % 1000 == 0 else f"Scores {lower/1000:.1f}k+"
    else:
        lower_str = f"{lower//1000}k" if lower % 1000 == 0 else f"{lower/1000:.1f}k"
        upper_str = f"{upper//1000}k" if upper % 1000 == 0 else f"{upper/1000:.1f}k"
        return f"Scores {lower_str}-{upper_str}"

def compute_modal_bucket(scores: pd.Series, ceiling: int, bin_size: int) -> str:
    """Label (without the leading 'Scores ') of the bucket of width `bin_size`,
    anchored from `ceiling` the same way `create_score_histogram` buckets its
    bars, that contains the most scores — i.e. the tallest bar's range."""
    scores_arr = scores.dropna().to_numpy()
    if len(scores_arr) == 0:
        return "-"
    best_count = -1
    best_label = "-"
    for lower, upper, is_top in generate_bucket_edges(ceiling, bin_size):
        count = int((scores_arr >= lower).sum()) if is_top else int(((scores_arr >= lower) & (scores_arr < upper)).sum())
        if count > best_count:
            best_count = count
            best_label = format_bucket_label(lower, upper, bin_size, is_top)
    return best_label.replace("Scores ", "", 1) if best_count > 0 else "-"

def create_plotly_figure(df_daily: pd.DataFrame, mask_filtered: pd.DataFrame,
                        window_length: int, score_type: str = "total",
                        show_single_player_days: bool = False) -> go.Figure:
    """Create the main Plotly figure."""
    fig = go.Figure()
    
    if score_type == "total":
        michael_col = "Michael Total Score"
        sarah_col = "Sarah Total Score"
    elif score_type == "time":
        michael_col = "Michael Time Midpoint"
        sarah_col = "Sarah Time Midpoint"
    else:  # geography
        michael_col = "Michael Geography Midpoint"
        sarah_col = "Sarah Geography Midpoint"

    # Always use sequential integers for equal spacing
    x_values = list(range(len(mask_filtered)))
    
    # Create custom tick positions for first day of each month
    mask_filtered_copy = mask_filtered.copy()
    mask_filtered_copy['month_year'] = mask_filtered_copy['Date'].dt.to_period('M')
    first_of_month_indices = mask_filtered_copy.groupby('month_year').head(1).index.tolist()
    
    tickvals = [i for i, idx in enumerate(mask_filtered.index) if idx in first_of_month_indices]
    ticktext = [mask_filtered.iloc[i]['Date'].strftime('%b %Y') for i in tickvals]

    # Add vertical line for Score Tracking Start (October 20, 2025)
    score_tracking_date = pd.Timestamp('2025-10-20')
    
    # Only show if tracking date is within the visible range (and dataset is not empty)
    if not mask_filtered.empty and mask_filtered['Date'].min() < score_tracking_date <= mask_filtered['Date'].max():
        # Find the first date >= tracking date
        dates_ge = mask_filtered[mask_filtered['Date'] >= score_tracking_date]
        if not dates_ge.empty:
            # Get the index label
            target_idx = dates_ge.index[0]
            # Get integer position (0..N)
            score_tracking_pos = mask_filtered.index.get_loc(target_idx)
            
            # Add vertical line
            fig.add_vline(
                x=score_tracking_pos,
                line=dict(color="#696761", width=1.5, dash="dash"),
            )
            
            # Add to tick labels to format similarly to months and prevent overlap
            if score_tracking_pos in tickvals:
                # Append to existing label if it overlaps exactly
                idx_pos = tickvals.index(score_tracking_pos)
                ticktext[idx_pos] += "<br>Tracking Start"
            else:
                tickvals.append(score_tracking_pos)
                ticktext.append("Tracking Start")
            
            # Sort ticks by position
            combined = sorted(zip(tickvals, ticktext))
            tickvals, ticktext = zip(*combined)
            tickvals = list(tickvals)
            ticktext = list(ticktext)

    # TimeGuessr Survey vertical line (May 18, 2026)
    survey_date = pd.Timestamp('2026-05-18')
    if not mask_filtered.empty and mask_filtered['Date'].min() < survey_date <= mask_filtered['Date'].max():
        dates_ge = mask_filtered[mask_filtered['Date'] >= survey_date]
        if not dates_ge.empty:
            target_idx = dates_ge.index[0]
            survey_pos = mask_filtered.index.get_loc(target_idx)
            fig.add_vline(x=survey_pos, line=dict(color="#696761", width=1.5, dash="dash"))
            if survey_pos in tickvals:
                idx_pos = tickvals.index(survey_pos)
                ticktext[idx_pos] += "<br>TimeGuessr Survey"
            else:
                tickvals.append(survey_pos)
                ticktext.append("TimeGuessr Survey")
            combined = sorted(zip(tickvals, ticktext))
            tickvals, ticktext = zip(*combined)
            tickvals = list(tickvals)
            ticktext = list(ticktext)

    # Add shaded rectangles for single-player days if toggle is on
    if show_single_player_days:
        for i in range(len(mask_filtered)):
            michael_val = mask_filtered.iloc[i][michael_col]
            sarah_val = mask_filtered.iloc[i][sarah_col]
            
            # Check if only one player has data
            if pd.isna(michael_val) and not pd.isna(sarah_val):
                # Only Sarah played - pinkish tint
                fig.add_shape(
                    type="rect",
                    x0=i - 0.5,
                    x1=i + 0.5,
                    y0=0,
                    y1=1,
                    yref="paper",
                    fillcolor="#d4c5cf",  # darker gray with pinkish tint
                    opacity=0.4,
                    layer="below",
                    line_width=0,
                )
            elif pd.isna(sarah_val) and not pd.isna(michael_val):
                # Only Michael played - bluish tint
                fig.add_shape(
                    type="rect",
                    x0=i - 0.5,
                    x1=i + 0.5,
                    y0=0,
                    y1=1,
                    yref="paper",
                    fillcolor="#c5c9d4",  # darker gray with bluish tint
                    opacity=0.4,
                    layer="below",
                    line_width=0,
                )

    # Scatter plots
    fig.add_trace(go.Scatter(
        x=x_values, y=mask_filtered[michael_col],
        mode='markers', name=f'Michael {score_type.title()} Score',
        marker=dict(color=COLORS['michael_light'], size=8),
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%b %d, %Y}<br>Score: %{y}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=x_values, y=mask_filtered[sarah_col],
        mode='markers', name=f'Sarah {score_type.title()} Score',
        marker=dict(color=COLORS['sarah_light'], size=8),
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%b %d, %Y}<br>Score: %{y}<extra></extra>'
    ))

    if score_type == "total" and "Community Average" in mask_filtered.columns:
        fig.add_trace(go.Scatter(
            x=x_values, y=mask_filtered["Community Average"],
            mode='markers', name='Community Average Score',
            marker=dict(color="#4d4d4d", size=7, opacity=0.85),
            customdata=mask_filtered["Date"],
            hovertemplate='Date: %{customdata|%b %d, %Y}<br>Community Avg: %{y}<extra></extra>'
        ))

    # Rolling average lines
    fig.add_trace(go.Scatter(
        x=x_values, y=mask_filtered["Michael Rolling Avg"],
        mode='lines', name=f'Michael {window_length}-game Avg',
        line=dict(color=COLORS['michael'], width=2.5),
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%b %d, %Y}<br>Rolling Avg: %{y:.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=x_values, y=mask_filtered["Sarah Rolling Avg"],
        mode='lines', name=f'Sarah {window_length}-game Avg',
        line=dict(color=COLORS['sarah'], width=2.5),
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%b %d, %Y}<br>Rolling Avg: %{y:.0f}<extra></extra>'
    ))

    if score_type == "total" and "Community Rolling Avg" in mask_filtered.columns:
        fig.add_trace(go.Scatter(
            x=x_values, y=mask_filtered["Community Rolling Avg"],
            mode='lines', name=f'Community {window_length}-game Avg',
            line=dict(color="black", width=2.5),
            customdata=mask_filtered["Date"],
            hovertemplate='Date: %{customdata|%b %d, %Y}<br>Rolling Avg: %{y:.0f}<extra></extra>'
        ))

    # Cumulative average lines
    fig.add_trace(go.Scatter(
        x=x_values, y=mask_filtered["Michael Cumulative Avg"],
        mode='lines', name='Michael Cumulative Avg',
        line=dict(color=COLORS['michael'], width=1.5, dash='dot'),
        opacity=0.7,
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%b %d, %Y}<br>Cumulative Avg: %{y:.0f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=x_values, y=mask_filtered["Sarah Cumulative Avg"],
        mode='lines', name='Sarah Cumulative Avg',
        line=dict(color=COLORS['sarah'], width=1.5, dash='dot'),
        opacity=0.7,
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%b %d, %Y}<br>Cumulative Avg: %{y:.0f}<extra></extra>'
    ))
    if score_type == "total" and "Community Cumulative Avg" in mask_filtered.columns:
        fig.add_trace(go.Scatter(
            x=x_values, y=mask_filtered["Community Cumulative Avg"],
            mode='lines', name='Community Cumulative Avg',
            line=dict(color="black", width=1.5, dash='dot'),
            opacity=0.7,
            customdata=mask_filtered["Date"],
            hovertemplate='Date: %{customdata|%b %d, %Y}<br>Cumulative Avg: %{y:.0f}<extra></extra>'
        ))
    # Best / worst reference lines
    m_vals = mask_filtered[michael_col].dropna()
    s_vals = mask_filtered[sarah_col].dropna()
    if not m_vals.empty:
        fig.add_hline(y=m_vals.max(), line=dict(color=COLORS['michael'], width=1, dash='dash'), opacity=0.45)
        fig.add_hline(y=m_vals.min(), line=dict(color=COLORS['michael'], width=1, dash='dash'), opacity=0.45)
    if not s_vals.empty:
        fig.add_hline(y=s_vals.max(), line=dict(color=COLORS['sarah'], width=1, dash='dash'), opacity=0.45)
        fig.add_hline(y=s_vals.min(), line=dict(color=COLORS['sarah'], width=1, dash='dash'), opacity=0.45)
    if score_type == "total" and "Community Average" in mask_filtered.columns:
        c_vals = mask_filtered["Community Average"].dropna()
        if not c_vals.empty:
            fig.add_hline(y=c_vals.max(), line=dict(color="black", width=1, dash='dash'), opacity=0.45)
            fig.add_hline(y=c_vals.min(), line=dict(color="black", width=1, dash='dash'), opacity=0.45)

    # Layout
    fig.update_layout(
        xaxis_title='Date', 
        yaxis_title=f'{score_type.title()} Score',
        width=1400, height=600, hovermode='closest',
        font=FONT_CONFIG,
        paper_bgcolor=COLORS['bg_paper'],
        plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=20, t=60, b=60),
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
        ticktext=ticktext,
        tickangle=-45,
        range=[-0.5, len(mask_filtered) - 0.5]
    )
    
    fig.update_yaxes(**axis_config)

    return fig

def create_momentum_html(data: pd.DataFrame, n_days: int, score_type: str) -> Tuple[str, float, float, float, float, str, str]:
    """Paired vertical bar chart per game showing Michael vs Sarah scores, for
    the most recent `n_days` games. Returns just the bars + date-range footer
    (no title, no score summary, no outer card) since those are rendered as
    real Streamlit elements inside the same bordered container by the caller
    — along with the two totals/means/weights the caller needs for that
    summary, so they aren't computed twice."""

    def hex_to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def interpolate_color(c_start, c_end, factor):
        c1, c2 = hex_to_rgb(c_start), hex_to_rgb(c_end)
        return '#{:02x}{:02x}{:02x}'.format(
            int(c1[0] + (c2[0] - c1[0]) * factor),
            int(c1[1] + (c2[1] - c1[1]) * factor),
            int(c1[2] + (c2[2] - c1[2]) * factor),
        )

    recent_data = data.tail(n_days).reset_index(drop=True)
    if len(recent_data) == 0:
        return "", 0.0, 0.0, 0.0, 0.0, "400", "400"

    if score_type == "total":
        m_col, s_col = "Michael Total Score", "Sarah Total Score"
    elif score_type == "time":
        m_col, s_col = "Michael Time Midpoint", "Sarah Time Midpoint"
    else:
        m_col, s_col = "Michael Geography Midpoint", "Sarah Geography Midpoint"

    m_valid = recent_data[m_col].dropna()
    m_valid = m_valid[m_valid > 0]
    s_valid = recent_data[s_col].dropna()
    s_valid = s_valid[s_valid > 0]
    m_min, m_max = (m_valid.min(), m_valid.max()) if len(m_valid) > 0 else (0, 1)
    s_min, s_max = (s_valid.min(), s_valid.max()) if len(s_valid) > 0 else (0, 1)

    all_scores = pd.concat([recent_data[m_col], recent_data[s_col]]).dropna()
    all_scores = all_scores[all_scores > 0]
    combined_min = all_scores.min() if len(all_scores) > 0 else 0
    combined_max = all_scores.max() if len(all_scores) > 0 else 1
    score_range = combined_max - combined_min if combined_max != combined_min else 1
    MIN_HEIGHT_PCT = 10
    slot_pct = 100 / len(recent_data)
    segments = []

    for _, row in recent_data.iterrows():
        m_score = np.nan_to_num(row[m_col])
        s_score = np.nan_to_num(row[s_col])
        date_str = row['Date'].strftime('%b %d, %Y')

        m_h = (MIN_HEIGHT_PCT + (100 - MIN_HEIGHT_PCT) * (m_score - combined_min) / score_range) if m_score > 0 else 0
        s_h = (MIN_HEIGHT_PCT + (100 - MIN_HEIGHT_PCT) * (s_score - combined_min) / score_range) if s_score > 0 else 0

        m_factor = 1.0 if m_max == m_min else (m_score - m_min) / (m_max - m_min)
        s_factor = 1.0 if s_max == s_min else (s_score - s_min) / (s_max - s_min)
        m_color = interpolate_color(COLORS['michael_light'], COLORS['michael'], m_factor) if m_score > 0 else 'transparent'
        s_color = interpolate_color(COLORS['sarah_light'], COLORS['sarah'], s_factor) if s_score > 0 else 'transparent'

        segments.append(
            f'<div style="width:{slot_pct}%;display:flex;flex-direction:column;height:100%;box-sizing:border-box;padding:0 1px;">'
            f'<div style="flex:1;display:flex;align-items:flex-end;">'
            f'<div style="width:100%;height:{m_h:.1f}%;background-color:{m_color};border-radius:3px 3px 0 0;" title="{date_str}: Michael {m_score:,.0f}"></div>'
            f'</div>'
            f'<div style="flex:1;display:flex;align-items:flex-start;">'
            f'<div style="width:100%;height:{s_h:.1f}%;background-color:{s_color};border-radius:0 0 3px 3px;" title="{date_str}: Sarah {s_score:,.0f}"></div>'
            f'</div>'
            f'</div>'
        )

    m_total = recent_data[m_col].sum()
    s_total = recent_data[s_col].sum()
    m_mean = recent_data[m_col].mean()
    s_mean = recent_data[s_col].mean()
    m_weight = "800" if m_total >= s_total else "400"
    s_weight = "800" if s_total > m_total else "400"

    html = f"""
<div style="width:100%;height:48px;border-radius:6px;overflow:hidden;display:flex;background-color:transparent;">
{"".join(segments)}
</div>
<div style="display:flex;justify-content:space-between;margin-top:4px;color:{COLORS['line']};font-size:10px;">
<span>{recent_data.iloc[0]['Date'].strftime('%b %d')}</span><span>{recent_data.iloc[-1]['Date'].strftime('%b %d')}</span>
</div>"""
    return html, m_total, s_total, m_mean, s_mean, m_weight, s_weight

def apply_chart_title(fig: go.Figure, title: str, subtitle: str = "", top_margin: int = None) -> go.Figure:
    """Puts a Momentum-box-style title (bold caps, plus an optional lighter
    subtitle line for charts whose meaning isn't obvious from the title alone)
    inside the chart's own card instead of a separate header div above it —
    plotly titles render on the same paper_bgcolor/bordered container as the
    plot, so title and chart end up visually as a single box, not two stacked
    ones. The plots below Momentum otherwise have only their axis labels to
    say what they show.

    Growing margin.t alone would eat into the plot area and squeeze the
    x-axis title off the bottom of the chart's fixed height, so the figure's
    `height` is grown by the same amount instead — the plot area (and
    everything below the title) keeps the size the chart function gave it."""
    if top_margin is None:
        top_margin = 75 if subtitle else 56
    text = f"<b style='letter-spacing:1px'>{title.upper()}</b>"
    if subtitle:
        text += f"<br><span style='font-size:12px;font-weight:400;opacity:0.8;text-transform:none'>{subtitle}</span>"
    current_margin_t = (fig.layout.margin.t if fig.layout.margin and fig.layout.margin.t is not None else 40)
    current_height = fig.layout.height if fig.layout.height else 350
    extra = max(top_margin - current_margin_t, 0)
    fig.update_layout(
        title=dict(
            text=text,
            x=0.03, xanchor='left', y=1, yanchor='top', pad=dict(t=16),
            font=dict(family="Poppins, Arial, sans-serif", size=16, color=COLORS['text'])
        ),
        margin=dict(t=top_margin),
        height=current_height + extra
    )
    return fig

def generate_bucket_edges(ceiling: int, bin_size: int) -> List[Tuple[int, int, bool]]:
    """Score buckets of width `bin_size`, anchored downward from `ceiling` (so the
    top bucket is open-ended and a partial bucket can only occur at the bottom,
    near 0) — the same anchoring `generate_buckets` uses for the stats table,
    returned in ascending order as (lower, upper, is_top)."""
    edges = []
    current_upper = ceiling
    while True:
        current_lower = max(current_upper - bin_size, 0)
        edges.append((current_lower, current_upper, current_upper == ceiling))
        if current_lower == 0:
            break
        current_upper = current_lower
    return list(reversed(edges))

def create_score_histogram(series_list, ceiling: int, bin_size: int,
                           trim_bin_size: int = None, label: str = "Score") -> go.Figure:
    """Overlapping skyline histogram of raw score counts per bucket of width
    `bin_size`, using the same top-down bucket anchoring as the stats table
    below it. Drawn as a filled step line rather than discrete bars, so equal-
    height neighboring buckets merge into one solid mass with no gap or
    dividing line between them — only the top of each bucket and any edge
    where the height actually changes gets a visible (solid-color) line.

    The displayed x-range is trimmed to where data actually exists, but that
    trim is computed against `trim_bin_size` (the largest bucket size offered
    for this score type) rather than `bin_size` itself — so the axis stays in
    the same place as the user picks a finer bucket size, instead of jumping
    around as empty buckets shrink.
    `series_list` is a list of (scores: pd.Series, dates: pd.Series, name: str, color: str)."""
    fig = go.Figure()

    non_empty = [(s, d, n, c) for s, d, n, c in series_list if len(s) > 0]
    if not non_empty:
        return fig

    def hex_to_rgba(hex_color, alpha=0.4):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'rgba({r},{g},{b},{alpha})'

    all_scores = pd.concat([s for s, _, _, _ in non_empty]).dropna().to_numpy()
    trim_edges = generate_bucket_edges(ceiling, trim_bin_size or bin_size)
    x_start, x_end = None, None
    for lower, upper, is_top in trim_edges:
        count = (all_scores >= lower).sum() if is_top else ((all_scores >= lower) & (all_scores < upper)).sum()
        if count > 0:
            if x_start is None:
                x_start = lower
            x_end = upper
    if x_start is None:
        x_start, x_end = trim_edges[0][0], ceiling

    edges = generate_bucket_edges(ceiling, bin_size)
    edges = [e for e in edges if e[1] > x_start and e[0] < x_end] or edges
    centers = [(lower + upper) / 2 for lower, upper, _ in edges]
    labels = [format_bucket_label(lower, upper, bin_size, is_top) for lower, upper, is_top in edges]

    # One point per bucket's lower edge plus a trailing point at the final
    # upper edge — with shape='hv' that traces a flat top across each bucket's
    # full span and a vertical jump only where the next bucket's count differs.
    x_line = [lower for lower, _, _ in edges] + [edges[-1][1]]

    for scores, dates, name, color in non_empty:
        scores_clean = scores.dropna()
        dates_clean = dates.loc[scores_clean.index].to_numpy()
        scores_arr = scores_clean.to_numpy()
        counts = []
        recent_dates = []
        for lower, upper, is_top in edges:
            bucket_mask = (scores_arr >= lower) if is_top else ((scores_arr >= lower) & (scores_arr < upper))
            counts.append(int(bucket_mask.sum()))
            recent_dates.append(pd.Timestamp(dates_clean[bucket_mask].max()).strftime('%b %d, %Y') if bucket_mask.any() else '-')
        y_line = counts + [counts[-1]]

        fig.add_trace(go.Scatter(
            x=x_line,
            y=y_line,
            name=name,
            mode='lines',
            line=dict(color=color, width=3, shape='hv'),
            fill='tozeroy',
            fillcolor=hex_to_rgba(color, 0.4),
            hoverinfo='skip'
        ))
        # Invisible marker at each bucket's actual center — the line above has
        # no data point there (its points sit at bucket edges), so without this
        # the hover would snap to an edge instead of the middle of the bucket.
        fig.add_trace(go.Scatter(
            x=centers,
            y=counts,
            mode='markers',
            marker=dict(color=color, opacity=0),
            showlegend=False,
            customdata=list(zip(labels, recent_dates)),
            hovertemplate=f'{name}<br>' + '%{customdata[0]}<br>Days: %{y}<br>Most Recent: %{customdata[1]}<extra></extra>'
        ))

        # Median / Min / Max reference lines, styled the same way as on the
        # ≥X / ≤X plots: a distinct dash per line plus a visible top marker
        # carrying the hover (Min/Max also show the date they happened on).
        top_y = max(counts) if counts else 0
        median_val = scores.median()
        min_idx = scores.argmin()
        max_idx = scores.argmax()
        min_val = scores.iloc[min_idx]
        max_val = scores.iloc[max_idx]
        min_date = dates.iloc[min_idx].strftime('%b %d, %Y')
        max_date = dates.iloc[max_idx].strftime('%b %d, %Y')

        reference_lines = [
            (median_val, 'dash', 'diamond', f'{name} Median: ' + '%{x:,.0f}<extra></extra>'),
            (max_val, 'dot', 'triangle-up', f'{name} Max: ' + '%{x:,.0f}' + f'<br>{max_date}<extra></extra>'),
            (min_val, 'dashdot', 'triangle-down', f'{name} Min: ' + '%{x:,.0f}' + f'<br>{min_date}<extra></extra>'),
        ]
        for x_pos, dash_style, symbol, hover_tmpl in reference_lines:
            if not (x_start <= x_pos <= x_end):
                continue
            fig.add_vline(
                x=x_pos,
                line=dict(color=color, width=1.5, dash=dash_style),
                opacity=0.7
            )
            fig.add_trace(go.Scatter(
                x=[x_pos],
                y=[top_y],
                mode='markers',
                marker=dict(color=color, size=9, opacity=0.9, symbol=symbol,
                           line=dict(color=COLORS['bg_paper'], width=1)),
                showlegend=False,
                hovertemplate=hover_tmpl
            ))

    fig.update_layout(
        xaxis_title=f'{label}',
        yaxis_title='Days',
        height=350,
        font=dict(family='Poppins, Arial, sans-serif', size=12, color='#000000'),
        paper_bgcolor=COLORS['bg_paper'],
        plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=40, t=40, b=60),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text'])
        ),
        hovermode='x unified'
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=False,
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        range=[x_start, x_end]
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=True,
        zerolinecolor=COLORS['line'],
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        rangemode='tozero'
    )

    return fig

def create_cumulative_histogram(series_list, ceiling: int, reverse: bool = False, label: str = "Score") -> go.Figure:
    """Overlapping step histogram: for every integer threshold X in [x_start, ceiling],
    how many days had a score >= X (or <= X when reverse=True), where x_start is the
    nearest multiple of 5,000 at or below the combined minimum score across all series.
    `series_list` is a list of (scores: pd.Series, dates: pd.Series, name: str, color: str)."""
    fig = go.Figure()

    non_empty = [(s, d, n, c) for s, d, n, c in series_list if len(s) > 0]
    if not non_empty:
        return fig

    all_scores = pd.concat([s for s, _, _, _ in non_empty]).dropna()
    x_start = max(0, int(np.floor(all_scores.min() / 5000) * 5000)) if not all_scores.empty else 0
    x_vals = np.arange(x_start, ceiling + 1, 1)

    def hex_to_rgba(hex_color, alpha=0.4):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'rgba({r},{g},{b},{alpha})'

    def day_counts(scores):
        sorted_scores = np.sort(scores.dropna().to_numpy())
        if reverse:
            # Days with Score <= X
            return np.searchsorted(sorted_scores, x_vals, side='right')
        # Days with Score >= X
        return len(sorted_scores) - np.searchsorted(sorted_scores, x_vals, side='left')

    def most_recent_dates(scores, dates, counts):
        # Rank days by how soon they qualify as the threshold tightens: for ">= X" the
        # highest scores qualify first (sort descending), for "<= X" the lowest scores
        # qualify first (ascending). counts[i] is exactly how many ranked days qualify
        # at x_vals[i], so a running max of date over that ranking, indexed by count,
        # gives the most recent qualifying day at every threshold.
        valid = scores.notna()
        s = scores[valid].to_numpy()
        d = pd.to_datetime(dates[valid]).to_numpy().astype('datetime64[ns]').astype('int64')
        order = np.argsort(s) if reverse else np.argsort(-s)
        running_max = np.maximum.accumulate(d[order])
        result = np.full(len(x_vals), '—', dtype=object)
        has_any = counts > 0
        recent_ts = pd.to_datetime(running_max[counts[has_any] - 1])
        result[has_any] = recent_ts.strftime('%b %d, %Y')
        return result

    op_symbol = '≤' if reverse else '≥'

    for scores, dates, name, color in non_empty:
        if len(scores) > 0:
            counts = day_counts(scores)
            recent_dates = most_recent_dates(scores, dates, counts)
            sorted_scores = np.sort(scores.dropna().to_numpy())
            total = len(sorted_scores)
            # Percentile rank of the threshold itself (% of days at or below X) —
            # a stable definition independent of which direction is being plotted.
            percentile = np.searchsorted(sorted_scores, x_vals, side='right') / total * 100
            customdata = np.stack([percentile.astype(object), recent_dates], axis=1)
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=counts,
                name=name,
                mode='lines',
                line=dict(color=color, width=3, shape='hv'),
                fill='tozeroy',
                fillcolor=hex_to_rgba(color, 0.4),
                customdata=customdata,
                hovertemplate=(f'{label} {op_symbol} ' + '%{x:,.0f}<br>Days: %{y}<br>Percentile: %{customdata[0]:.1f}'
                                '<br>Most Recent: %{customdata[1]}<extra></extra>')
            ))

            # Median / Min / Max each get their own dash style and marker shape so
            # they're visually distinct, plus a visible marker at the top carrying
            # the hover (a bare vline shape can't be hovered, and a zero-width
            # vertical "lines" trace breaks Plotly's unified hoverlabel positioning —
            # it throws on the degenerate bounding box). Min/Max also show the date
            # they happened on; Median has no single associated date.
            median_val = scores.median()
            min_idx = scores.argmin()
            max_idx = scores.argmax()
            min_val = scores.iloc[min_idx]
            max_val = scores.iloc[max_idx]
            min_date = dates.iloc[min_idx].strftime('%b %d, %Y')
            max_date = dates.iloc[max_idx].strftime('%b %d, %Y')

            reference_lines = [
                (median_val, 'dash', 'diamond', f'{name} Median: ' + '%{x:,.0f}<extra></extra>'),
                (max_val, 'dot', 'triangle-up', f'{name} Max: ' + '%{x:,.0f}' + f'<br>{max_date}<extra></extra>'),
                (min_val, 'dashdot', 'triangle-down', f'{name} Min: ' + '%{x:,.0f}' + f'<br>{min_date}<extra></extra>'),
            ]
            for x_pos, dash_style, symbol, hover_tmpl in reference_lines:
                fig.add_vline(
                    x=x_pos,
                    line=dict(color=color, width=1.5, dash=dash_style),
                    opacity=0.7
                )
                fig.add_trace(go.Scatter(
                    x=[x_pos],
                    y=[total],
                    mode='markers',
                    marker=dict(color=color, size=9, opacity=0.9, symbol=symbol,
                               line=dict(color=COLORS['bg_paper'], width=1)),
                    showlegend=False,
                    hovertemplate=hover_tmpl
                ))

    fig.update_layout(
        xaxis_title=f'{label} Threshold (X)',
        yaxis_title='Days',
        height=350,
        font=dict(family='Poppins, Arial, sans-serif', size=12, color='#000000'),
        paper_bgcolor=COLORS['bg_paper'],
        plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=40, t=40, b=60),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text'])
        ),
        hovermode='x unified'
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=False,
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        range=[x_start, ceiling]
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=True,
        zerolinecolor=COLORS['line'],
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        rangemode='tozero'
    )

    return fig

def create_streak_score_histogram(series_list, ceiling: int, reverse: bool = False, label: str = "Score") -> go.Figure:
    """Companion plot to create_cumulative_histogram: for every integer threshold X,
    what's the longest streak of consecutive days (in sequence order) with score >= X
    (or <= X when reverse=True).
    `series_list` is a list of (scores: pd.Series, dates: pd.Series, name: str, color: str)."""
    fig = go.Figure()

    non_empty = [(s, d, n, c) for s, d, n, c in series_list if len(s) > 0]
    if not non_empty:
        return fig

    all_scores = pd.concat([s for s, _, _, _ in non_empty]).dropna()
    x_start = max(0, int(np.floor(all_scores.min() / 5000) * 5000)) if not all_scores.empty else 0
    x_vals = np.arange(x_start, ceiling + 1, 1)

    def hex_to_rgba(hex_color, alpha=0.4):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'rgba({r},{g},{b},{alpha})'

    def streak_curve(scores, dates):
        # The longest-streak function only changes value at the distinct score values
        # themselves, so evaluate it once per distinct score (a handful of calls) instead of
        # once per integer threshold, then broadcast across x_vals via searchsorted.
        scores_arr = scores.to_numpy()
        breakpoints = np.unique(scores_arr[~np.isnan(scores_arr)])
        breakpoints = breakpoints[(breakpoints >= x_start) & (breakpoints <= ceiling)]
        if len(breakpoints) == 0:
            return np.zeros(len(x_vals), dtype=int), np.full(len(x_vals), '—', dtype=object)

        if reverse:
            # score <= v  <=>  -score >= -v, so negate both sides to reuse the
            # inclusive >= comparison (calculate_streak_with_dates's above=False
            # is a strict <, which would wrongly exclude days scoring exactly v).
            streak_info = [
                calculate_streak_with_dates(-scores_arr, dates, -v, above=True)
                for v in breakpoints
            ]
        else:
            streak_info = [
                calculate_streak_with_dates(scores_arr, dates, v, above=True)
                for v in breakpoints
            ]
        f_vals = np.array([length for length, _, _ in streak_info])
        # calculate_streak_with_dates already picks the most recent occurrence among
        # ties, so this is the most recent date range achieving that streak length.
        f_ranges = np.array([
            start if start == end else f'{start} - {end}'
            for _, start, end in streak_info
        ], dtype=object)

        result = np.zeros(len(x_vals), dtype=int)
        range_result = np.full(len(x_vals), '—', dtype=object)
        if reverse:
            # Longest streak with score <= X is non-decreasing in X, constant at f(v) for
            # X in [v, next breakpoint) — use the largest breakpoint <= X.
            idx = np.searchsorted(breakpoints, x_vals, side='right')
            valid = idx > 0
            result[valid] = f_vals[idx[valid] - 1]
            range_result[valid] = f_ranges[idx[valid] - 1]
        else:
            # Longest streak with score >= X is non-increasing in X, constant at f(v) for
            # X in (prev breakpoint, v] — use the smallest breakpoint >= X.
            idx = np.searchsorted(breakpoints, x_vals, side='left')
            valid = idx < len(breakpoints)
            result[valid] = f_vals[idx[valid]]
            range_result[valid] = f_ranges[idx[valid]]
        return result, range_result

    op_symbol = '≤' if reverse else '≥'

    for scores, dates, name, color in non_empty:
        y_vals, range_vals = streak_curve(scores, dates)
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            name=name,
            mode='lines',
            line=dict(color=color, width=3, shape='hv'),
            fill='tozeroy',
            fillcolor=hex_to_rgba(color, 0.4),
            customdata=range_vals,
            hovertemplate=(f'{label} {op_symbol} ' + '%{x:,.0f}<br>Longest Streak: %{y} days'
                            '<br>Most Recent: %{customdata}<extra></extra>')
        ))

    fig.update_layout(
        xaxis_title=f'{label} Threshold (X)',
        yaxis_title='Streak (days)',
        height=350,
        font=dict(family='Poppins, Arial, sans-serif', size=12, color='#000000'),
        paper_bgcolor=COLORS['bg_paper'],
        plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=40, t=40, b=60),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text'])
        ),
        hovermode='x unified'
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=False,
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        range=[x_start, ceiling]
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=True,
        zerolinecolor=COLORS['line'],
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        rangemode='tozero'
    )

    return fig

def calculate_streak_from_mask(mask: np.ndarray, dates: pd.Series,
                               date_format: str = "%b %d, %Y") -> Tuple[int, str, str]:
    """Longest streak of consecutive True values in `mask`, in sequence order."""
    max_streak = 0
    current_streak = 0
    max_start_idx = 0
    max_end_idx = 0
    current_start_idx = 0

    for i, m in enumerate(mask):
        if m:
            if current_streak == 0:
                current_start_idx = i
            current_streak += 1

            if current_streak > max_streak or (current_streak == max_streak and i > max_end_idx):
                max_streak = current_streak
                max_start_idx = current_start_idx
                max_end_idx = i
        else:
            current_streak = 0

    if max_streak > 0:
        start_date = dates.iloc[max_start_idx].strftime(date_format)
        end_date = dates.iloc[max_end_idx].strftime(date_format)
        return max_streak, start_date, end_date

    return 0, "", ""

def calculate_band_hop_streak(above_mask: np.ndarray, below_mask: np.ndarray, dates: pd.Series,
                              date_format: str = "%b %d, %Y") -> Tuple[int, str, str]:
    """Longest streak of consecutive days (in sequence order) alternating
    between clearly above (`above_mask`) and clearly below (`below_mask`) —
    a day that's neither (inside the buffer zone between the two masks)
    breaks the streak, the same as a day that repeats the same side."""
    max_streak = 0
    current_streak = 0
    max_start_idx = 0
    max_end_idx = 0
    current_start_idx = 0
    prev_side = None

    for i in range(len(above_mask)):
        if above_mask[i]:
            side = True
        elif below_mask[i]:
            side = False
        else:
            side = None

        if side is None:
            current_streak = 0
            prev_side = None
            continue

        if prev_side is None or side == prev_side:
            current_streak = 1
            current_start_idx = i
        else:
            current_streak += 1
        prev_side = side

        if current_streak > max_streak or (current_streak == max_streak and i > max_end_idx):
            max_streak = current_streak
            max_start_idx = current_start_idx
            max_end_idx = i

    if max_streak > 0:
        start_date = dates.iloc[max_start_idx].strftime(date_format)
        end_date = dates.iloc[max_end_idx].strftime(date_format)
        return max_streak, start_date, end_date

    return 0, "", ""

def create_streak_instability_histogram(series_list, ceiling: int, band: int = 5000, label: str = "Score") -> go.Figure:
    """Companion plot to create_streak_band_histogram: where that plot measures
    stability (longest streak staying within `band` of X), this measures
    instability — the longest streak of consecutive days (in sequence order)
    hopping back and forth across X using the same buffer, one day clearly
    above (score >= X + band), the next clearly below (score <= X - band),
    and so on. A day inside the buffer (within `band` of X, i.e. "stable" by
    the other plot's definition) breaks the hop streak, same as repeating the
    same side twice in a row.
    `series_list` is a list of (scores: pd.Series, dates: pd.Series, name: str, color: str)."""
    fig = go.Figure()

    non_empty = [(s, d, n, c) for s, d, n, c in series_list if len(s) > 0]
    if not non_empty:
        return fig

    all_scores = pd.concat([s for s, _, _, _ in non_empty]).dropna()
    x_start = max(0, int(np.floor(all_scores.min() / 5000) * 5000)) if not all_scores.empty else 0
    x_vals = np.arange(x_start, ceiling + 1, 1)

    def hop_curve(scores, dates):
        # A day's side (clearly above X+band, clearly below X-band, or inside
        # the buffer) only changes at X = score - band (loses "above") and
        # X = score + band (gains "below"), so the streak only needs
        # recomputing at those breakpoints, not at every X.
        scores_arr = scores.to_numpy()
        valid_scores = np.unique(scores_arr[~np.isnan(scores_arr)])
        if len(valid_scores) == 0:
            return np.zeros(len(x_vals), dtype=int), np.full(len(x_vals), '—', dtype=object)

        breakpoints = np.unique(np.concatenate([[x_start], valid_scores - band, valid_scores + band + 1]))
        breakpoints = breakpoints[(breakpoints >= x_start) & (breakpoints <= ceiling)]

        f_vals = np.empty(len(breakpoints), dtype=int)
        f_ranges = np.empty(len(breakpoints), dtype=object)
        for i, bp in enumerate(breakpoints):
            above_mask = scores_arr >= bp + band
            below_mask = scores_arr <= bp - band
            length, start, end = calculate_band_hop_streak(above_mask, below_mask, dates)
            f_vals[i] = length
            f_ranges[i] = '—' if length == 0 else (start if start == end else f'{start} - {end}')

        idx = np.clip(np.searchsorted(breakpoints, x_vals, side='right') - 1, 0, len(breakpoints) - 1)
        return f_vals[idx], f_ranges[idx]

    def hex_to_rgba(hex_color, alpha=0.4):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'rgba({r},{g},{b},{alpha})'

    # The score range a point represents (X-band to X+band), shown in the
    # hover instead of "X ± band" — same for every trace since x_vals/band
    # are shared, so it's built once.
    score_range_strs = np.array([f'{x - band:,.0f} - {x + band:,.0f}' for x in x_vals], dtype=object)

    for scores, dates, name, color in non_empty:
        y_vals, range_vals = hop_curve(scores, dates)
        customdata = np.stack([score_range_strs, range_vals], axis=1)
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            name=name,
            mode='lines',
            line=dict(color=color, width=3, shape='hv'),
            fill='tozeroy',
            fillcolor=hex_to_rgba(color, 0.4),
            hoveron='points+fills',
            customdata=customdata,
            hovertemplate=('%{customdata[0]}' +
                            f'<br>{label} Longest Hop Streak: ' + '%{y} days<br>Most Recent: %{customdata[1]}<extra></extra>')
        ))

    fig.update_layout(
        xaxis_title=f'{label} (X)',
        yaxis_title='Streak (days)',
        height=350,
        font=dict(family='Poppins, Arial, sans-serif', size=12, color='#000000'),
        paper_bgcolor=COLORS['bg_paper'],
        plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=40, t=40, b=60),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text'])
        ),
        hovermode='closest'
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=False,
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        range=[x_start, ceiling]
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=True,
        zerolinecolor=COLORS['line'],
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        rangemode='tozero'
    )

    return fig

def create_streak_band_histogram(series_list, ceiling: int, band: int = 5000, label: str = "Score") -> go.Figure:
    """Companion plot to create_streak_score_histogram: for every integer score X,
    what's the longest streak of consecutive days (in sequence order) with score
    within `band` of X (i.e. X - band <= score <= X + band).
    Unlike the >= X / <= X streak plots, this isn't monotonic in X, so it's drawn
    as points at each whole-number X rather than a step line.
    `series_list` is a list of (scores: pd.Series, dates: pd.Series, name: str, color: str)."""
    fig = go.Figure()

    non_empty = [(s, d, n, c) for s, d, n, c in series_list if len(s) > 0]
    if not non_empty:
        return fig

    all_scores = pd.concat([s for s, _, _, _ in non_empty]).dropna()
    x_start = max(0, int(np.floor(all_scores.min() / 5000) * 5000)) if not all_scores.empty else 0
    x_vals = np.arange(x_start, ceiling + 1, 1)

    def band_curve(scores, dates):
        # The window [X-band, X+band] only changes which scores it contains at
        # X = score - band (score enters) and X = score + band + 1 (score leaves),
        # so the streak only needs recomputing at those breakpoints, not at every X.
        scores_arr = scores.to_numpy()
        valid_scores = np.unique(scores_arr[~np.isnan(scores_arr)])
        if len(valid_scores) == 0:
            return np.zeros(len(x_vals), dtype=int), np.full(len(x_vals), '—', dtype=object)

        breakpoints = np.unique(np.concatenate([[x_start], valid_scores - band, valid_scores + band + 1]))
        breakpoints = breakpoints[(breakpoints >= x_start) & (breakpoints <= ceiling)]

        f_vals = np.empty(len(breakpoints), dtype=int)
        f_ranges = np.empty(len(breakpoints), dtype=object)
        for i, bp in enumerate(breakpoints):
            mask = (scores_arr >= bp - band) & (scores_arr <= bp + band)
            length, start, end = calculate_streak_from_mask(mask, dates)
            f_vals[i] = length
            f_ranges[i] = '—' if length == 0 else (start if start == end else f'{start} - {end}')

        idx = np.clip(np.searchsorted(breakpoints, x_vals, side='right') - 1, 0, len(breakpoints) - 1)
        return f_vals[idx], f_ranges[idx]

    def hex_to_rgba(hex_color, alpha=0.4):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'rgba({r},{g},{b},{alpha})'

    # The score range a point represents (X-band to X+band), shown in the
    # hover instead of "X ± band" — same for every trace since x_vals/band
    # are shared, so it's built once.
    score_range_strs = np.array([f'{x - band:,.0f} - {x + band:,.0f}' for x in x_vals], dtype=object)

    for scores, dates, name, color in non_empty:
        y_vals, range_vals = band_curve(scores, dates)
        customdata = np.stack([score_range_strs, range_vals], axis=1)
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            name=name,
            mode='lines',
            line=dict(color=color, width=3, shape='hv'),
            fill='tozeroy',
            fillcolor=hex_to_rgba(color, 0.4),
            hoveron='points+fills',
            customdata=customdata,
            hovertemplate=('%{customdata[0]}' +
                            f'<br>{label} Longest Streak: ' + '%{y} days<br>Most Recent: %{customdata[1]}<extra></extra>')
        ))

    fig.update_layout(
        xaxis_title=f'{label} (X)',
        yaxis_title='Streak (days)',
        height=350,
        font=dict(family='Poppins, Arial, sans-serif', size=12, color='#000000'),
        paper_bgcolor=COLORS['bg_paper'],
        plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=40, t=40, b=60),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text'])
        ),
        hovermode='closest'
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=False,
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        range=[x_start, ceiling]
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=True,
        zerolinecolor=COLORS['line'],
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        rangemode='tozero'
    )

    return fig

def create_cumulative_avg_streak_momentum_chart(series_list, label: str = "Score",
                                                mode: str = "cumavg", threshold: float = None) -> go.Figure:
    """Visualizes the above/below streak over time: each streak is drawn as a
    single bar spanning its full date range, at its peak (final) length — so
    hovering anywhere over a streak's bar shows that whole streak's date range
    and length in one tooltip, rather than a separate tooltip per day.
    `mode="cumavg"` (default) compares each day's score to that player's own
    running average up to and including that day; `mode="score"` instead
    compares every day to the fixed `threshold` score.
    Each player gets its own stacked row (sharing the date axis) so the two
    don't overlap and obscure each other.

    The x-axis uses the same sequential-integer-with-month-start-labels
    scheme as the main Scores chart (`create_plotly_figure`), built from the
    union of every date appearing across `series_list`, rather than a raw
    date axis — so the bars pack edge-to-edge with no missing-day gaps and
    no Plotly autorange padding, matching that chart's width exactly.
    `series_list` is a list of (scores: pd.Series, dates: pd.Series, name: str, color: str)."""
    non_empty = [(s, d, n, c) for s, d, n, c in series_list if len(s) > 0]

    n_rows = max(len(non_empty), 1)
    fig = make_subplots(
        rows=n_rows, cols=1, shared_xaxes=True,
        vertical_spacing=0.22,
        subplot_titles=[name for _, _, name, _ in non_empty]
    )

    if non_empty:
        all_dates = pd.concat([d for _, d, _, _ in non_empty]).drop_duplicates().sort_values().reset_index(drop=True)
    else:
        all_dates = pd.Series([], dtype='datetime64[ns]')
    date_to_pos = {d: i for i, d in enumerate(all_dates)}
    n_total = max(len(all_dates), 1)

    month_year = all_dates.dt.to_period('M')
    first_of_month_positions = month_year.drop_duplicates().index.tolist()
    # drop_duplicates on the period series keeps the first occurrence's
    # original (0-based, already sequential) position, so these ARE the tick
    # x-positions directly.
    tickvals = first_of_month_positions
    ticktext = [all_dates.iloc[i].strftime('%b %Y') for i in tickvals]

    # First pass: compute every row's streak blocks so the largest streak
    # across ALL rows can set a single shared y-axis range — otherwise each
    # player's row autoscales independently, making the two heights
    # impossible to compare at a glance.
    row_data = []
    y_max = 0
    for scores, dates, name, color in non_empty:
        scores_arr = scores.reset_index(drop=True)
        dates_arr = dates.reset_index(drop=True)
        if mode == "score":
            above = (scores_arr >= threshold).to_numpy()
        else:
            cumavg = scores_arr.expanding().mean()
            above = (scores_arr >= cumavg).to_numpy()

        # Group consecutive same-side days into blocks, one bar per streak —
        # spanning that streak's full date range — instead of one point per day.
        blocks = []
        i = 0
        n_days = len(above)
        while i < n_days:
            j = i
            while j + 1 < n_days and above[j + 1] == above[i]:
                j += 1
            blocks.append((i, j))
            i = j + 1

        centers, widths, values, range_strs = [], [], [], []
        for start_idx, end_idx in blocks:
            start_date = dates_arr.iloc[start_idx]
            end_date = dates_arr.iloc[end_idx]
            length = end_idx - start_idx + 1
            left_edge = date_to_pos[start_date] - 0.5
            right_edge = date_to_pos[end_date] + 0.5
            widths.append(right_edge - left_edge)
            centers.append(left_edge + (right_edge - left_edge) / 2)
            values.append(length if above[start_idx] else -length)
            range_strs.append(start_date.strftime('%b %d, %Y') if start_date == end_date
                              else f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}")

        if values:
            y_max = max(y_max, max(abs(v) for v in values))
        row_data.append((name, color, centers, widths, values, range_strs))

    y_max = y_max * 1.05 if y_max > 0 else 1

    for row, (name, color, centers, widths, values, range_strs) in enumerate(row_data, start=1):
        fig.add_trace(go.Bar(
            x=centers, y=values, width=widths,
            name=name,
            marker=dict(color=color, opacity=0.65, line=dict(width=0)),
            customdata=range_strs,
            showlegend=False,
            hovertemplate=(f'{name}<br>' + '%{customdata}<br>Streak: %{y} days<extra></extra>')
        ), row=row, col=1)

        fig.add_hline(y=0, line=dict(color=COLORS['line'], width=1), row=row, col=1)

        fig.update_yaxes(
            title_text='Streak (days)',
            showgrid=True,
            gridcolor=COLORS['grid'],
            zeroline=True,
            zerolinecolor=COLORS['line'],
            linecolor=COLORS['line'],
            tickcolor=COLORS['line'],
            tickfont=dict(color=COLORS['text']),
            title_font=dict(color=COLORS['text']),
            range=[-y_max, y_max],
            row=row, col=1
        )
        fig.update_xaxes(
            showgrid=True,
            gridcolor=COLORS['grid'],
            zeroline=False,
            linecolor=COLORS['line'],
            tickcolor=COLORS['line'],
            tickfont=dict(color=COLORS['text']),
            title_font=dict(color=COLORS['text']),
            title_text='Date' if row == n_rows else None,
            tickmode='array',
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=-45,
            range=[-0.5, n_total - 0.5],
            row=row, col=1
        )

    for annotation in fig['layout']['annotations']:
        annotation['font'] = dict(family='Poppins, Arial, sans-serif', size=13, color=COLORS['text'])
        # Push each "Michael"/"Sarah" subplot title further above its own bars —
        # Plotly's default placement sits right on top of the plot area.
        annotation['yshift'] = 14

    fig.update_layout(
        height=210 * n_rows,
        bargap=0,
        font=dict(family='Poppins, Arial, sans-serif', size=12, color='#000000'),
        paper_bgcolor=COLORS['bg_paper'],
        plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=40, t=30, b=60),
        showlegend=False,
        hovermode='closest'
    )

    return fig

def create_win_streak_chart(dates: pd.Series, score_diff: pd.Series,
                            name_above: str = "Michael", name_below: str = "Sarah",
                            color_above: str = None, color_below: str = None) -> go.Figure:
    """Win Margins counterpart to create_cumulative_avg_streak_momentum_chart:
    visualizes consecutive-win streaks over time as a single bar strip, one
    bar per streak at its peak (final) length — positive for `name_above`
    (days `score_diff` > 0), negative for `name_below`. Only one row is
    needed here (unlike the per-player Score Streaks chart) because a win
    for one side is, by definition, always a loss for the other — it's the
    same signal drawn once and mirrored, not two independent ones.
    Uses the same sequential-integer-with-month-start-labels x-axis as the
    main Scores/Win Margins chart."""
    color_above = color_above or COLORS['michael']
    color_below = color_below or COLORS['sarah']
    fig = go.Figure()

    dates_arr = dates.reset_index(drop=True)
    diff_arr = score_diff.reset_index(drop=True)
    if len(diff_arr) == 0:
        return fig

    above = (diff_arr > 0).to_numpy()

    all_dates = dates_arr.drop_duplicates().sort_values().reset_index(drop=True)
    date_to_pos = {d: i for i, d in enumerate(all_dates)}
    n_total = max(len(all_dates), 1)

    month_year = all_dates.dt.to_period('M')
    first_of_month_positions = month_year.drop_duplicates().index.tolist()
    tickvals = first_of_month_positions
    ticktext = [all_dates.iloc[i].strftime('%b %Y') for i in tickvals]

    blocks = []
    i = 0
    n_days = len(above)
    while i < n_days:
        j = i
        while j + 1 < n_days and above[j + 1] == above[i]:
            j += 1
        blocks.append((i, j))
        i = j + 1

    centers, widths, values, colors, customdata = [], [], [], [], []
    for start_idx, end_idx in blocks:
        start_date = dates_arr.iloc[start_idx]
        end_date = dates_arr.iloc[end_idx]
        length = end_idx - start_idx + 1
        left_edge = date_to_pos[start_date] - 0.5
        right_edge = date_to_pos[end_date] + 0.5
        widths.append(right_edge - left_edge)
        centers.append(left_edge + (right_edge - left_edge) / 2)
        is_above = above[start_idx]
        values.append(length if is_above else -length)
        colors.append(color_above if is_above else color_below)
        range_str = (start_date.strftime('%b %d, %Y') if start_date == end_date
                    else f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}")
        customdata.append((name_above if is_above else name_below, range_str))

    fig.add_trace(go.Bar(
        x=centers, y=values, width=widths,
        marker=dict(color=colors, opacity=0.65, line=dict(width=0)),
        customdata=customdata,
        showlegend=False,
        hovertemplate='%{customdata[0]}<br>%{customdata[1]}<br>Streak: %{y} days<extra></extra>'
    ))

    fig.add_hline(y=0, line=dict(color=COLORS['line'], width=1))

    fig.update_yaxes(
        title_text='Streak (days)',
        showgrid=True, gridcolor=COLORS['grid'], zeroline=True, zerolinecolor=COLORS['line'],
        linecolor=COLORS['line'], tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']), title_font=dict(color=COLORS['text'])
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=COLORS['grid'], zeroline=False, linecolor=COLORS['line'],
        tickcolor=COLORS['line'], tickfont=dict(color=COLORS['text']), title_font=dict(color=COLORS['text']),
        title_text='Date',
        tickmode='array', tickvals=tickvals, ticktext=ticktext, tickangle=-45,
        range=[-0.5, n_total - 0.5]
    )

    fig.update_layout(
        height=260,
        bargap=0,
        font=dict(family='Poppins, Arial, sans-serif', size=12, color='#000000'),
        paper_bgcolor=COLORS['bg_paper'],
        plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=40, t=20, b=60),
        showlegend=False,
        hovermode='closest'
    )

    return fig

def create_streak_count_histogram(streaks_list) -> go.Figure:
    """Companion plot to the Streaks table: for every integer streak length X
    from 1 to the longest streak observed, how many completed win streaks
    (of either player) were at least X days long — each streak counted once
    per threshold it qualifies for, never split into sub-streaks.
    `streaks_list` is a list of (streaks: list[(length: int, end_date)], name: str, color: str)."""
    fig = go.Figure()

    non_empty = [(s, n, c) for s, n, c in streaks_list if s]
    if not non_empty:
        return fig

    max_len = max(max(length for length, _ in s) for s, _, _ in non_empty)
    x_vals = np.arange(1, max_len + 1)

    def hex_to_rgba(hex_color, alpha=0.4):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'rgba({r},{g},{b},{alpha})'

    # Each integer X gets its own "bar" of the step — shift the plotted step
    # half a unit to the left and append one trailing point so that bar spans
    # [X-0.5, X+0.5) and the tick at X sits at its center, not its left edge.
    x_plot = np.append(x_vals - 0.5, max_len + 0.5)

    for streaks, name, color in non_empty:
        lengths = np.array([length for length, _ in streaks])
        end_dates = np.array([pd.Timestamp(d) for _, d in streaks])
        sorted_lengths = np.sort(lengths)
        counts = len(sorted_lengths) - np.searchsorted(sorted_lengths, x_vals, side='left')
        y_plot = np.append(counts, counts[-1])
        fig.add_trace(go.Scatter(
            x=x_plot,
            y=y_plot,
            name=name,
            mode='lines',
            line=dict(color=color, width=3, shape='hv'),
            fill='tozeroy',
            fillcolor=hex_to_rgba(color, 0.4),
            hoverinfo='skip',
        ))
        # Most recent occurrence of a streak at least X days long — the
        # qualifying end dates shrink to a subset as X grows, so this is
        # just the max end date among streaks whose length clears X.
        recent_dates = []
        for x in x_vals:
            qualifying = end_dates[lengths >= x]
            recent_dates.append(qualifying.max().strftime('%b %d, %Y') if len(qualifying) else '-')

        # Invisible marker at each bar's actual center (an integer x) — the
        # line trace above has no data point there (its points sit at the
        # .5 edges), so without this the hover would snap to an edge instead
        # of the middle of the bar. hoverinfo is skipped on the line trace
        # above, leaving these as the only hoverable points.
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=counts,
            mode='markers',
            marker=dict(color=color, opacity=0),
            showlegend=False,
            customdata=recent_dates,
            hovertemplate='Streak ≥ %{x} days<br>Count: %{y}<br>Most Recent: %{customdata}<extra></extra>'
        ))

    fig.update_layout(
        xaxis_title='Streak Length (X, days)',
        yaxis_title='Streaks ≥ X (count)',
        height=350,
        font=dict(family='Poppins, Arial, sans-serif', size=12, color='#000000'),
        paper_bgcolor=COLORS['bg_paper'],
        plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=40, t=40, b=60),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text'])
        ),
        hovermode='x unified'
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=False,
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        range=[0.5, max_len + 0.5],
        tick0=1,
        dtick=1,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=COLORS['grid'],
        zeroline=True,
        zerolinecolor=COLORS['line'],
        linecolor=COLORS['line'],
        tickcolor=COLORS['line'],
        tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        rangemode='tozero'
    )

    return fig

def add_zero_crossing_interpolation(mask_filtered: pd.DataFrame, window_length: int) -> pd.DataFrame:
    """Add interpolated zero-crossing points for smooth rolling-avg line transitions."""
    mask_filtered = mask_filtered.reset_index(drop=True)
    y = mask_filtered["Rolling Diff"]
    dates = mask_filtered["Date"]
    new_points = []

    crossings_mask = np.sign(y.shift(1) * y).fillna(1) < 0
    crossing_indices = mask_filtered[crossings_mask].index.tolist()

    for i in crossing_indices:
        if i == 0:
            continue
        y1, x1 = y.iloc[i-1], dates.iloc[i-1]
        y2, x2 = y.iloc[i], dates.iloc[i]
        cum1, cum2 = mask_filtered["Cumulative Diff"].iloc[i-1], mask_filtered["Cumulative Diff"].iloc[i]
        score1, score2 = mask_filtered["Score Diff"].iloc[i-1], mask_filtered["Score Diff"].iloc[i]
        if y2 - y1 != 0:
            fraction = (0 - y1) / (y2 - y1)
            x_zero = x1 + pd.Timedelta((x2 - x1).total_seconds() * fraction, unit='s')
            new_points.append({
                "Date": x_zero,
                "Rolling Diff": 0.0,
                "Score Diff": score1 + fraction * (score2 - score1),
                "Cumulative Diff": cum1 + fraction * (cum2 - cum1)
            })

    if new_points:
        mask_filtered = pd.concat([mask_filtered, pd.DataFrame(new_points)], ignore_index=True)
        mask_filtered = mask_filtered.sort_values(by="Date").reset_index(drop=True)

    mask_filtered['Rolling Diff Pos'] = np.where(mask_filtered['Rolling Diff'] >= 0, mask_filtered['Rolling Diff'], np.nan)
    mask_filtered['Rolling Diff Neg'] = np.where(mask_filtered['Rolling Diff'] <= 0, mask_filtered['Rolling Diff'], np.nan)
    return mask_filtered


def create_win_margins_figure(mask_filtered: pd.DataFrame, window_length: int) -> go.Figure:
    """Create the win margins Plotly figure (Michael − Sarah)."""
    fig = go.Figure()
    mask_filtered = mask_filtered.copy()

    is_midnight = mask_filtered["Date"].dt.time == pd.Timestamp("00:00:00").time()
    mask_filtered.loc[is_midnight, "x_index"] = np.arange(is_midnight.sum(), dtype=float)
    mask_filtered["x_index"] = mask_filtered["x_index"].interpolate(method="linear")
    is_midnight = mask_filtered["Date"].dt.time == pd.Timestamp("00:00:00").time()

    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=mask_filtered["Score Diff"], mode="markers",
        marker=dict(color="gray", opacity=np.where(is_midnight, 0.4, 0), size=7),
        name="Game Result (Michael − Sarah)", customdata=mask_filtered["Date"],
        hovertemplate="Date: %{customdata|%b %d, %Y}<br>Score Diff: %{y}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=np.where(mask_filtered["Score Diff"] > 0, mask_filtered["Score Diff"], 0),
        fill='tozeroy', mode='none', fillcolor='rgba(188, 176, 255, 0.6)', name='Michael Wins'
    ))
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=np.where(mask_filtered["Score Diff"] < 0, mask_filtered["Score Diff"], 0),
        fill='tozeroy', mode='none', fillcolor='rgba(255, 148, 189, 0.6)', name='Sarah Wins'
    ))
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=mask_filtered["Cumulative Diff"], mode="lines",
        name="Cumulative Avg", line=dict(color="black", width=1.5, dash="dot"), opacity=0.7,
        customdata=mask_filtered["Date"], hovertemplate='Date: %{customdata|%b %d, %Y}<br>Cumulative Avg: %{y:.1f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=mask_filtered["Rolling Diff Pos"], mode="lines",
        name=f"{window_length}-Game Rolling Avg", line=dict(color=COLORS['michael'], width=2.5),
        opacity=0.8, showlegend=False, customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%b %d, %Y}<br>Rolling Avg: %{y:.1f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=mask_filtered["Rolling Diff Neg"], mode="lines",
        name=f"{window_length}-Game Rolling Avg", line=dict(color=COLORS['sarah'], width=2.5),
        opacity=0.8, showlegend=False, customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%b %d, %Y}<br>Rolling Avg: %{y:.1f}<extra></extra>'
    ))

    y_max = np.ceil(max(
        abs(mask_filtered["Score Diff"].max()), abs(mask_filtered["Score Diff"].min()),
        abs(mask_filtered["Rolling Diff"].max()), abs(mask_filtered["Rolling Diff"].min()),
        abs(mask_filtered["Cumulative Diff"].max()), abs(mask_filtered["Cumulative Diff"].min())
    ) / 5000) * 5000
    tick_vals = np.arange(-y_max, y_max + 1, 5000)
    tick_text = [str(abs(int(t))) for t in tick_vals]

    fig.add_hline(y=0, line=dict(color="#8f8d85", dash="dash", width=1))
    actual_diffs = mask_filtered.loc[is_midnight, "Score Diff"]
    if not actual_diffs.empty:
        fig.add_hline(y=actual_diffs.max(), line=dict(color=COLORS['michael'], width=1, dash='dash'), opacity=0.45)
        fig.add_hline(y=actual_diffs.min(), line=dict(color=COLORS['sarah'], width=1, dash='dash'), opacity=0.45)

    midnight_df = mask_filtered[is_midnight].copy()
    midnight_df['month_year'] = midnight_df['Date'].dt.to_period('M')
    first_of_month_indices = midnight_df.groupby('month_year').head(1).index.tolist()
    tick_indices = [mask_filtered.loc[idx, 'x_index'] for idx in first_of_month_indices]
    tick_labels = [mask_filtered.loc[idx, 'Date'].strftime('%b %Y') for idx in first_of_month_indices]

    for vline_date, vline_label in [
        (pd.Timestamp('2025-10-20'), "Tracking Start"),
        (pd.Timestamp('2026-05-18'), "TimeGuessr Survey"),
    ]:
        if not midnight_df.empty and midnight_df['Date'].min() < vline_date <= midnight_df['Date'].max():
            ge = midnight_df[midnight_df['Date'] >= vline_date]
            if not ge.empty:
                pos = mask_filtered.loc[ge.index[0], 'x_index']
                fig.add_vline(x=pos, line=dict(color="#696761", width=1.5, dash="dash"))
                if pos in tick_indices:
                    tick_labels[tick_indices.index(pos)] += f"<br>{vline_label}"
                else:
                    tick_indices.append(pos)
                    tick_labels.append(vline_label)
                combined = sorted(zip(tick_indices, tick_labels))
                tick_indices, tick_labels = [list(x) for x in zip(*combined)]

    fig.update_layout(
        xaxis_title="Date", yaxis_title="Score Difference (Michael − Sarah)",
        width=1400, height=600, hovermode="closest",
        font=FONT_CONFIG, paper_bgcolor=COLORS['bg_paper'], plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=20, t=60, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)", font=dict(color=COLORS['text'])),
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=COLORS['grid'], zeroline=False, linecolor=COLORS['line'],
        tickcolor=COLORS['line'], tickfont=dict(color=COLORS['text']), title_font=dict(color=COLORS['text']),
        tickmode='array', tickvals=tick_indices, ticktext=tick_labels, tickangle=-45,
        range=[-0.5, mask_filtered["x_index"].max() + 0.5]
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=COLORS['grid'], zeroline=False, linecolor=COLORS['line'],
        tickcolor=COLORS['line'], tickfont=dict(color=COLORS['text']), title_font=dict(color=COLORS['text']),
        tickvals=tick_vals, ticktext=tick_text, range=[-y_max, y_max]
    )
    return fig


def create_momentum_timeline(data: pd.DataFrame, n_days: int) -> Tuple[str, int, int]:
    """Win-margins counterpart to create_momentum_html: bars + date-range
    footer only (no title, no score summary, no outer card) for the most
    recent `n_days` games, plus the two win counts the caller needs for the
    score summary it renders separately inside the same bordered container."""
    recent_data = data.tail(n_days).reset_index(drop=True)
    if len(recent_data) == 0:
        return "", 0, 0

    diffs = recent_data['Score Diff'].fillna(0)
    max_abs = diffs.abs().max() or 1
    MIN_HEIGHT_PCT = 10
    slot_pct = 100 / len(recent_data)
    segments = []

    for _, row in recent_data.iterrows():
        diff = row['Score Diff']
        date_str = row['Date'].strftime('%b %d, %Y')
        height_pct = MIN_HEIGHT_PCT + (100 - MIN_HEIGHT_PCT) * min(1.0, abs(diff) / max_abs)
        if diff > 0:
            color, label = COLORS['michael'], f"Michael (+{diff:,.0f})"
        elif diff < 0:
            color, label = COLORS['sarah'], f"Sarah (+{abs(diff):,.0f})"
        else:
            color, label = COLORS['line'], "Tie"
        segments.append(
            f'<div style="width:{slot_pct}%;display:flex;align-items:center;justify-content:center;height:100%;box-sizing:border-box;padding:0 1px;">'
            f'<div style="width:100%;height:{height_pct:.1f}%;background-color:{color};border-radius:3px;" title="{date_str}: {label}"></div>'
            f'</div>'
        )

    m_wins = int((diffs > 0).sum())
    s_wins = int((diffs < 0).sum())
    html = f"""
<div style="width:100%;height:48px;border-radius:6px;overflow:hidden;display:flex;background-color:transparent;">
{"".join(segments)}
</div>
<div style="display:flex;justify-content:space-between;margin-top:4px;color:{COLORS['line']};font-size:10px;">
<span>{recent_data.iloc[0]['Date'].strftime('%b %d')}</span><span>{recent_data.iloc[-1]['Date'].strftime('%b %d')}</span>
</div>"""
    return html, m_wins, s_wins


def calculate_win_streaks(df: pd.DataFrame, name_above: str = "Michael", name_below: str = "Sarah") -> List[Dict]:
    """Calculate win streaks for `name_above` (Score Diff > 0) and `name_below`
    (Score Diff < 0) — defaults to Michael/Sarah, but Self passes Time/Geography."""
    # idx below is used as a positional index via .iloc, so a caller-supplied
    # frame with gaps in its index (e.g. from upstream filtering that wasn't
    # followed by reset_index) would throw — reset it locally instead of
    # relying on every caller to have already done so.
    df = df.reset_index(drop=True)
    streaks = []
    current_streak = 0
    current_winner = None
    streak_start = None

    for idx, row in df.iterrows():
        if row["Score Diff"] > 0:
            winner = name_above
        elif row["Score Diff"] < 0:
            winner = name_below
        else:
            winner = "Tie"
        # A tie is not a win for either side, so it breaks an active streak
        # instead of being skipped over (which let a streak survive across it).
        if winner == current_winner and winner != "Tie":
            current_streak += 1
        else:
            if current_winner is not None and current_winner != "Tie" and current_streak > 0:
                streaks.append({'winner': current_winner, 'length': current_streak,
                                'start_date': streak_start, 'end_date': df.iloc[idx-1]["Date"]})
            current_winner = winner
            current_streak = 1 if winner != "Tie" else 0
            streak_start = row["Date"]

    if current_winner is not None and current_winner != "Tie" and current_streak > 0:
        streaks.append({'winner': current_winner, 'length': current_streak,
                        'start_date': streak_start, 'end_date': df.iloc[-1]["Date"]})
    return streaks


# --- Self Comparison Helper Functions ---

def self_prepare_player_data(data: pd.DataFrame, player: str, remove_estimated: bool = False, include_single: bool = False) -> pd.DataFrame:
    data = data.copy()
    if player == "Combined":
        for metric in ["Time", "Geography"]:
            for bound in ["Min", "Max"]:
                data[f"Combined {metric} Score ({bound})"] = (
                    data[f"Michael {metric} Score ({bound})"] + data[f"Sarah {metric} Score ({bound})"]
                )
    if remove_estimated:
        for col_pair in [(f"{player} Time Score (Min)", f"{player} Time Score (Max)"),
                         (f"{player} Geography Score (Min)", f"{player} Geography Score (Max)")]:
            mask_est = data[col_pair[0]] != data[col_pair[1]]
            data.loc[mask_est, list(col_pair)] = np.nan
    subset_cols = [f"{player} Time Score (Min)", f"{player} Time Score (Max)",
                   f"{player} Geography Score (Min)", f"{player} Geography Score (Max)"]
    data = data.dropna(subset=subset_cols, how='all')
    data[f"{player} Time Midpoint"] = (data[f"{player} Time Score (Min)"] + data[f"{player} Time Score (Max)"]) / 2
    data[f"{player} Geography Midpoint"] = (data[f"{player} Geography Score (Min)"] + data[f"{player} Geography Score (Max)"]) / 2
    daily_cols = [f"{player} Time Midpoint", f"{player} Geography Midpoint"]
    df_daily = data.groupby("Date")[daily_cols].sum(min_count=1).reset_index().sort_values("Date").reset_index(drop=True)
    t_col, g_col = f"{player} Time Midpoint", f"{player} Geography Midpoint"
    if include_single:
        return df_daily[df_daily[t_col].notna() | df_daily[g_col].notna()].copy()
    # Exclude days where only one of Michael/Sarah played
    if player != "Combined":
        daily_totals = data.groupby("Date")[["Michael Total Score", "Sarah Total Score"]].first().reset_index()
        both_played = daily_totals[daily_totals["Michael Total Score"].notna() & daily_totals["Sarah Total Score"].notna()]["Date"]
        df_daily = df_daily[df_daily["Date"].isin(both_played)]
    return df_daily[df_daily[t_col].notna() & df_daily[g_col].notna()].copy()


def self_calculate_rolling_averages(df: pd.DataFrame, window_length: int, player: str) -> pd.DataFrame:
    df = df.copy()
    for metric in ["Time", "Geography"]:
        col = f"{player} {metric} Midpoint"
        if col in df.columns:
            df[f"{player} {metric} Rolling Avg"] = df[col].rolling(window=window_length, min_periods=1).mean()
            df[f"{player} {metric} Cumulative Avg"] = df[col].expanding().mean()
    return df


def self_create_plotly_figure(df: pd.DataFrame, window_length: int, player: str,
                              solo_dates: set = None) -> go.Figure:
    fig = go.Figure()
    time_col, geo_col = f"{player} Time Midpoint", f"{player} Geography Midpoint"
    x_values = list(range(len(df)))
    df_copy = df.copy()
    df_copy['month_year'] = df_copy['Date'].dt.to_period('M')
    first_of_month_indices = df_copy.groupby('month_year').head(1).index.tolist()
    tickvals = [i for i, idx in enumerate(df.index) if idx in first_of_month_indices]
    ticktext = [df.iloc[i]['Date'].strftime('%b %Y') for i in tickvals]

    for vline_date, vline_label in [(pd.Timestamp('2025-10-20'), "Tracking Start"), (pd.Timestamp('2026-05-18'), "TimeGuessr Survey")]:
        if not df.empty and df['Date'].min() < vline_date <= df['Date'].max():
            dates_ge = df[df['Date'] >= vline_date]
            if not dates_ge.empty:
                pos = df.index.get_loc(dates_ge.index[0])
                fig.add_vline(x=pos, line=dict(color="#696761", width=1.5, dash="dash"))
                if pos in tickvals:
                    ticktext[tickvals.index(pos)] += f"<br>{vline_label}"
                else:
                    tickvals.append(pos); ticktext.append(vline_label)
                combined = sorted(zip(tickvals, ticktext))
                tickvals, ticktext = [list(x) for x in zip(*combined)]

    if solo_dates:
        solo_tint = "#c5c9d4" if player == "Michael" else "#d4c5cf"
        for i in range(len(df)):
            if df.iloc[i]['Date'] in solo_dates:
                fig.add_shape(type="rect", x0=i - 0.5, x1=i + 0.5, y0=0, y1=1, yref="paper",
                              fillcolor=solo_tint, opacity=0.4, layer="below", line_width=0)

    fig.add_trace(go.Scatter(x=x_values, y=df[time_col], mode='markers', name='Time Score',
                             marker=dict(color=COLORS['time_light'], size=8), customdata=df["Date"],
                             hovertemplate='Date: %{customdata|%b %d, %Y}<br>Time Score: %{y}<extra></extra>'))
    fig.add_trace(go.Scatter(x=x_values, y=df[geo_col], mode='markers', name='Geography Score',
                             marker=dict(color=COLORS['geography_light'], size=8), customdata=df["Date"],
                             hovertemplate='Date: %{customdata|%b %d, %Y}<br>Geography Score: %{y}<extra></extra>'))
    fig.add_trace(go.Scatter(x=x_values, y=df[f"{player} Time Rolling Avg"], mode='lines',
                             name=f'Time {window_length}-game Avg', line=dict(color=COLORS['time'], width=2.5),
                             customdata=df["Date"], hovertemplate='Date: %{customdata|%b %d, %Y}<br>Time Rolling Avg: %{y:.0f}<extra></extra>'))
    fig.add_trace(go.Scatter(x=x_values, y=df[f"{player} Geography Rolling Avg"], mode='lines',
                             name=f'Geography {window_length}-game Avg', line=dict(color=COLORS['geography'], width=2.5),
                             customdata=df["Date"], hovertemplate='Date: %{customdata|%b %d, %Y}<br>Geography Rolling Avg: %{y:.0f}<extra></extra>'))
    fig.add_trace(go.Scatter(x=x_values, y=df[f"{player} Time Cumulative Avg"], mode='lines',
                             name='Time Cumulative Avg', line=dict(color=COLORS['time'], width=1.5, dash='dot'), opacity=0.7,
                             customdata=df["Date"], hovertemplate='Date: %{customdata|%b %d, %Y}<br>Time Cumulative Avg: %{y:.0f}<extra></extra>'))
    fig.add_trace(go.Scatter(x=x_values, y=df[f"{player} Geography Cumulative Avg"], mode='lines',
                             name='Geography Cumulative Avg', line=dict(color=COLORS['geography'], width=1.5, dash='dot'), opacity=0.7,
                             customdata=df["Date"], hovertemplate='Date: %{customdata|%b %d, %Y}<br>Geography Cumulative Avg: %{y:.0f}<extra></extra>'))
    for vals, color in [(df[time_col].dropna(), COLORS['time']), (df[geo_col].dropna(), COLORS['geography'])]:
        if not vals.empty:
            fig.add_hline(y=vals.max(), line=dict(color=color, width=1, dash='dash'), opacity=0.45)
            fig.add_hline(y=vals.min(), line=dict(color=color, width=1, dash='dash'), opacity=0.45)
    fig.update_layout(xaxis_title='Date', yaxis_title='Score', width=1400, height=600, hovermode='closest',
                      font=FONT_CONFIG, paper_bgcolor=COLORS['bg_paper'], plot_bgcolor=COLORS['bg_plot'],
                      margin=dict(l=60, r=20, t=60, b=40),
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                                  bgcolor='rgba(0,0,0,0)', bordercolor='rgba(0,0,0,0)', font=dict(color=COLORS['text'])))
    ax = dict(showgrid=True, gridcolor=COLORS['grid'], zeroline=False, linecolor=COLORS['line'],
              tickcolor=COLORS['line'], tickfont=dict(color=COLORS['text']), title_font=dict(color=COLORS['text']))
    fig.update_xaxes(**ax, tickmode='array', tickvals=tickvals, ticktext=ticktext, tickangle=-45,
                     range=[-0.5, len(df) - 0.5])
    fig.update_yaxes(**ax)
    return fig


def self_create_win_margins_figure(mask_filtered: pd.DataFrame, window_length: int, player: str,
                                   solo_dates: set = None) -> go.Figure:
    fig = go.Figure()
    mask_filtered = mask_filtered.copy()
    mask_filtered["x_index"] = np.arange(len(mask_filtered))
    fig.add_trace(go.Scatter(x=mask_filtered["x_index"], y=mask_filtered["Score Diff"], mode="markers",
                             marker=dict(color="gray", opacity=0.4, size=7), name="Game Result (Time − Geography)",
                             customdata=mask_filtered["Date"],
                             hovertemplate="Date: %{customdata|%b %d, %Y}<br>Score Diff: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=mask_filtered["x_index"],
                             y=np.where(mask_filtered["Score Diff"] > 0, mask_filtered["Score Diff"], 0),
                             fill='tozeroy', mode='none', fillcolor='rgba(152, 223, 138, 0.6)', name='Time Wins'))
    fig.add_trace(go.Scatter(x=mask_filtered["x_index"],
                             y=np.where(mask_filtered["Score Diff"] < 0, mask_filtered["Score Diff"], 0),
                             fill='tozeroy', mode='none', fillcolor='rgba(255, 187, 120, 0.6)', name='Geography Wins'))
    fig.add_trace(go.Scatter(x=mask_filtered["x_index"], y=mask_filtered["Cumulative Diff"], mode="lines",
                             name="Cumulative Avg", line=dict(color="black", width=1.5, dash="dot"), opacity=0.7,
                             customdata=mask_filtered["Date"],
                             hovertemplate='Date: %{customdata|%b %d, %Y}<br>Cumulative Avg: %{y:.1f}<extra></extra>'))
    fig.add_trace(go.Scatter(x=mask_filtered["x_index"], y=mask_filtered["Rolling Diff Pos"], mode="lines",
                             name=f"{window_length}-Game Rolling Avg", line=dict(color=COLORS['time'], width=2.5),
                             opacity=0.8, showlegend=False, customdata=mask_filtered["Date"],
                             hovertemplate='Date: %{customdata|%b %d, %Y}<br>Rolling Avg: %{y:.1f}<extra></extra>'))
    fig.add_trace(go.Scatter(x=mask_filtered["x_index"], y=mask_filtered["Rolling Diff Neg"], mode="lines",
                             name=f"{window_length}-Game Rolling Avg", line=dict(color=COLORS['geography'], width=2.5),
                             opacity=0.8, showlegend=False, customdata=mask_filtered["Date"],
                             hovertemplate='Date: %{customdata|%b %d, %Y}<br>Rolling Avg: %{y:.1f}<extra></extra>'))
    y_max = np.ceil(max(abs(mask_filtered["Score Diff"].max()), abs(mask_filtered["Score Diff"].min()),
                        abs(mask_filtered["Rolling Diff"].max()), abs(mask_filtered["Rolling Diff"].min()),
                        abs(mask_filtered["Cumulative Diff"].max()), abs(mask_filtered["Cumulative Diff"].min())) / 5000) * 5000
    tick_vals = np.arange(-y_max, y_max + 1, 5000)
    fig.add_hline(y=0, line=dict(color="#8f8d85", dash="dash", width=1))
    actual_diffs = mask_filtered["Score Diff"]
    if not actual_diffs.empty:
        fig.add_hline(y=actual_diffs.max(), line=dict(color=COLORS['time'], width=1, dash='dash'), opacity=0.45)
        fig.add_hline(y=actual_diffs.min(), line=dict(color=COLORS['geography'], width=1, dash='dash'), opacity=0.45)
    df_copy = mask_filtered.copy()
    df_copy['month_year'] = df_copy['Date'].dt.to_period('M')
    first_of_month_indices = df_copy.groupby('month_year').head(1).index.tolist()
    tickvals = [mask_filtered.loc[idx, "x_index"] for idx in first_of_month_indices]
    ticktext = [mask_filtered.loc[idx, 'Date'].strftime('%b %Y') for idx in first_of_month_indices]
    if solo_dates:
        solo_tint = "#c5c9d4" if player == "Michael" else "#d4c5cf"
        for _, row in mask_filtered.iterrows():
            if row['Date'] in solo_dates:
                x = row['x_index']
                fig.add_shape(type="rect", x0=x - 0.5, x1=x + 0.5, y0=0, y1=1, yref="paper",
                              fillcolor=solo_tint, opacity=0.4, layer="below", line_width=0)
    for vline_date, vline_label in [(pd.Timestamp('2025-10-20'), "Tracking Start"), (pd.Timestamp('2026-05-18'), "TimeGuessr Survey")]:
        if not mask_filtered.empty and mask_filtered['Date'].min() < vline_date <= mask_filtered['Date'].max():
            dates_ge = mask_filtered[mask_filtered['Date'] >= vline_date]
            if not dates_ge.empty:
                pos = mask_filtered.loc[dates_ge.index[0], 'x_index']
                fig.add_vline(x=pos, line=dict(color="#696761", width=1.5, dash="dash"))
                if pos in tickvals:
                    ticktext[tickvals.index(pos)] += f"<br>{vline_label}"
                else:
                    tickvals.append(pos); ticktext.append(vline_label)
                combined = sorted(zip(tickvals, ticktext))
                tickvals, ticktext = [list(x) for x in zip(*combined)]
    fig.update_layout(xaxis_title="Date", yaxis_title="Score Difference (Time − Geography)",
                      width=1400, height=600, hovermode="closest",
                      font=FONT_CONFIG, paper_bgcolor=COLORS['bg_paper'], plot_bgcolor=COLORS['bg_plot'],
                      margin=dict(l=60, r=20, t=60, b=60),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                                  bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)", font=dict(color=COLORS['text'])))
    ax = dict(showgrid=True, gridcolor=COLORS['grid'], zeroline=False, linecolor=COLORS['line'],
              tickcolor=COLORS['line'], tickfont=dict(color=COLORS['text']), title_font=dict(color=COLORS['text']))
    fig.update_xaxes(**ax, tickmode='array', tickvals=tickvals, ticktext=ticktext, tickangle=-45,
                     range=[-0.5, len(mask_filtered) - 0.5])
    fig.update_yaxes(**ax, tickvals=tick_vals, ticktext=[str(abs(int(t))) for t in tick_vals], range=[-y_max, y_max])
    return fig


def self_create_momentum_timeline(data: pd.DataFrame, n_days: int) -> Tuple[str, int, int]:
    """Self-page counterpart to create_momentum_timeline: bars + date-range
    footer only (no title, no score summary, no outer card) for the most
    recent `n_days` games, plus the two win counts the caller needs for the
    score summary it renders separately inside the same bordered container."""
    recent_data = data.tail(n_days).reset_index(drop=True)
    if len(recent_data) == 0:
        return "", 0, 0
    diffs = recent_data['Score Diff'].fillna(0)
    max_abs = diffs.abs().max() or 1
    MIN_HEIGHT_PCT = 10
    slot_pct = 100 / len(recent_data)
    segments = []
    for _, row in recent_data.iterrows():
        diff = row['Score Diff']
        date_str = row['Date'].strftime('%b %d, %Y')
        height_pct = MIN_HEIGHT_PCT + (100 - MIN_HEIGHT_PCT) * min(1.0, abs(diff) / max_abs)
        if diff > 0:
            color, label = COLORS['time'], f"Time (+{diff:,.0f})"
        elif diff < 0:
            color, label = COLORS['geography'], f"Geography (+{abs(diff):,.0f})"
        else:
            color, label = COLORS['line'], "Tie"
        segments.append(f'<div style="width:{slot_pct}%;display:flex;align-items:center;justify-content:center;height:100%;box-sizing:border-box;padding:0 1px;">'
                        f'<div style="width:100%;height:{height_pct:.1f}%;background-color:{color};border-radius:3px;" title="{date_str}: {label}"></div></div>')
    t_wins, g_wins = int((diffs > 0).sum()), int((diffs < 0).sum())
    html = (f'<div style="width:100%;height:48px;border-radius:6px;overflow:hidden;display:flex;background-color:transparent;">{"".join(segments)}</div>'
            f'<div style="display:flex;justify-content:space-between;margin-top:4px;color:{COLORS["line"]};font-size:10px;">'
            f'<span>{recent_data.iloc[0]["Date"].strftime("%b %d")}</span><span>{recent_data.iloc[-1]["Date"].strftime("%b %d")}</span></div>')
    return html, t_wins, g_wins


def self_create_scores_momentum_html(data: pd.DataFrame, player: str, n_days: int) -> Tuple[str, float, float, float, float, str, str]:
    """Self-page counterpart to create_momentum_html: bars + date-range footer
    only (no title, no score summary, no outer card) for the most recent
    `n_days` games, plus the two totals/means/weights the caller needs for
    the score summary it renders separately inside the same bordered
    container."""
    def hex_to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    def interpolate_color(c_start, c_end, factor):
        c1, c2 = hex_to_rgb(c_start), hex_to_rgb(c_end)
        return '#{:02x}{:02x}{:02x}'.format(int(c1[0]+(c2[0]-c1[0])*factor), int(c1[1]+(c2[1]-c1[1])*factor), int(c1[2]+(c2[2]-c1[2])*factor))
    recent_data = data.tail(n_days).reset_index(drop=True)
    if len(recent_data) == 0:
        return "", 0.0, 0.0, 0.0, 0.0, "400", "400"
    time_col, geo_col = f"{player} Time Midpoint", f"{player} Geography Midpoint"
    t_valid = recent_data[time_col].dropna(); t_valid = t_valid[t_valid > 0]
    g_valid = recent_data[geo_col].dropna(); g_valid = g_valid[g_valid > 0]
    t_min, t_max = (t_valid.min(), t_valid.max()) if len(t_valid) > 0 else (0, 1)
    g_min, g_max = (g_valid.min(), g_valid.max()) if len(g_valid) > 0 else (0, 1)
    all_s = pd.concat([recent_data[time_col], recent_data[geo_col]]).dropna()
    all_s = all_s[all_s > 0]
    c_min = all_s.min() if len(all_s) > 0 else 0
    c_max = all_s.max() if len(all_s) > 0 else 1
    s_range = c_max - c_min if c_max != c_min else 1
    MIN_H = 10
    slot_pct = 100 / len(recent_data)
    segments = []
    for _, row in recent_data.iterrows():
        t_s = np.nan_to_num(row[time_col]); g_s = np.nan_to_num(row[geo_col])
        date_str = row['Date'].strftime('%b %d, %Y')
        t_h = (MIN_H + (100 - MIN_H) * (t_s - c_min) / s_range) if t_s > 0 else 0
        g_h = (MIN_H + (100 - MIN_H) * (g_s - c_min) / s_range) if g_s > 0 else 0
        t_f = 1.0 if t_max == t_min else (t_s - t_min) / (t_max - t_min)
        g_f = 1.0 if g_max == g_min else (g_s - g_min) / (g_max - g_min)
        t_color = interpolate_color(COLORS['time_light'], COLORS['time'], t_f) if t_s > 0 else 'transparent'
        g_color = interpolate_color(COLORS['geography_light'], COLORS['geography'], g_f) if g_s > 0 else 'transparent'
        segments.append(f'<div style="width:{slot_pct}%;display:flex;flex-direction:column;height:100%;box-sizing:border-box;padding:0 1px;">'
                        f'<div style="flex:1;display:flex;align-items:flex-end;"><div style="width:100%;height:{t_h:.1f}%;background-color:{t_color};border-radius:3px 3px 0 0;" title="{date_str}: Time {t_s:,.0f}"></div></div>'
                        f'<div style="flex:1;display:flex;align-items:flex-start;"><div style="width:100%;height:{g_h:.1f}%;background-color:{g_color};border-radius:0 0 3px 3px;" title="{date_str}: Geography {g_s:,.0f}"></div></div></div>')
    t_total, g_total = recent_data[time_col].sum(), recent_data[geo_col].sum()
    t_mean, g_mean = recent_data[time_col].mean(), recent_data[geo_col].mean()
    t_weight = "800" if t_total >= g_total else "400"
    g_weight = "800" if g_total > t_total else "400"
    html = (f'<div style="width:100%;height:48px;border-radius:6px;overflow:hidden;display:flex;background-color:transparent;">{"".join(segments)}</div>'
            f'<div style="display:flex;justify-content:space-between;margin-top:4px;color:{COLORS["line"]};font-size:10px;">'
            f'<span>{recent_data.iloc[0]["Date"].strftime("%b %d")}</span><span>{recent_data.iloc[-1]["Date"].strftime("%b %d")}</span></div>')
    return html, t_total, g_total, t_mean, g_mean, t_weight, g_weight


# --- Main App ---

# Load data
stats_mtime = os.path.getmtime("./Data/Timeguessr_Stats.csv") if os.path.exists("./Data/Timeguessr_Stats.csv") else 0
data = load_data(mtime=stats_mtime)

# Render Sidebar Controls
with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>Settings</h2>", unsafe_allow_html=True)

    _ct = st.session_state.get('cc_comp_type', 'Cross')
    _ctc1, _ctc2 = st.columns(2)
    with _ctc1:
        if st.button("Cross", key="cc_btn_cross", use_container_width=True,
                     type="primary" if _ct == "Cross" else "secondary"):
            st.session_state['cc_comp_type'] = 'Cross'
            st.rerun()
    with _ctc2:
        if st.button("Self", key="cc_btn_self", use_container_width=True,
                     type="primary" if _ct == "Self" else "secondary"):
            st.session_state['cc_comp_type'] = 'Self'
            st.rerun()
    comp_type = _ct

    st.markdown('<hr style="border:none;border-top:1px solid #d9d7cc;margin:1px 24px 12px 24px;">', unsafe_allow_html=True)

    _vm = st.session_state.get('cc_view_mode', 'Scores')
    _c1, _c2 = st.columns(2)
    with _c1:
        if st.button("Scores", key="cc_btn_scores", use_container_width=True,
                     type="primary" if _vm == "Scores" else "secondary"):
            st.session_state['cc_view_mode'] = 'Scores'
            st.rerun()
    with _c2:
        if st.button("Win Margins", key="cc_btn_margins", use_container_width=True,
                     type="primary" if _vm == "Win Margins" else "secondary"):
            st.session_state['cc_view_mode'] = 'Win Margins'
            st.rerun()
    view_mode = st.session_state.get('cc_view_mode', 'Scores')

    st.markdown('<hr style="border:none;border-top:1px solid #d9d7cc;margin:1px 24px 12px 24px;">', unsafe_allow_html=True)

    if comp_type == 'Cross':
        _pt_labels = {"Total": "Total Scores", "Geo": "Geography Scores", "Time": "Time Scores"}
        _pt = st.session_state.get('cc_page_type', 'Total')
        _ptc1, _ptc2, _ptc3 = st.columns(3)
        with _ptc1:
            if st.button("Total", key="cc_btn_total", use_container_width=True,
                         type="primary" if _pt == "Total" else "secondary"):
                st.session_state['cc_page_type'] = 'Total'
                st.rerun()
        with _ptc2:
            if st.button("Geo", key="cc_btn_geo", use_container_width=True,
                         type="primary" if _pt == "Geo" else "secondary"):
                st.session_state['cc_page_type'] = 'Geo'
                st.rerun()
        with _ptc3:
            if st.button("Time", key="cc_btn_time", use_container_width=True,
                         type="primary" if _pt == "Time" else "secondary"):
                st.session_state['cc_page_type'] = 'Time'
                st.rerun()
        page_type = _pt_labels[_pt]
    else:
        _pl_labels = {"Both": "Combined", "Mike": "Michael", "Sarah": "Sarah"}
        _pl = st.session_state.get('cc_player', 'Both')
        _plc1, _plc2, _plc3 = st.columns(3)
        with _plc1:
            if st.button("Both", key="cc_btn_both", use_container_width=True,
                         type="primary" if _pl == "Both" else "secondary"):
                st.session_state['cc_player'] = 'Both'
                st.rerun()
        with _plc2:
            if st.button("M", key="cc_btn_michael", use_container_width=True,
                         type="primary" if _pl == "Mike" else "secondary"):
                st.session_state['cc_player'] = 'Mike'
                st.rerun()
        with _plc3:
            if st.button("S", key="cc_btn_sarah", use_container_width=True,
                         type="primary" if _pl == "Sarah" else "secondary"):
                st.session_state['cc_player'] = 'Sarah'
                st.rerun()
        player = _pl_labels[_pl]

    st.markdown('<hr style="border:none;border-top:1px solid #d9d7cc;margin:1px 24px 12px 24px;">', unsafe_allow_html=True)

    _ptr = st.session_state.get('cc_pre_tracking', False)
    _psr = st.session_state.get('cc_pre_survey', False)
    _psm = st.session_state.get('cc_pre_summary', False)
    _tg1, _tg2 = st.columns(2)
    with _tg1:
        if st.button("Post-Track", key="cc_btn_pretracking", use_container_width=True,
                     type="primary" if _ptr else "secondary"):
            st.session_state['cc_pre_tracking'] = not _ptr
            st.rerun()
    with _tg2:
        if st.button("Post-Survey", key="cc_btn_presurvey", use_container_width=True,
                     type="primary" if _psr else "secondary"):
            st.session_state['cc_pre_survey'] = not _psr
            st.rerun()
    if st.button("Post-Summary", key="cc_btn_presummary", use_container_width=True,
                 type="primary" if _psm else "secondary"):
        st.session_state['cc_pre_summary'] = not _psm
        st.rerun()
    remove_pre_tracking = _ptr
    remove_pre_survey = _psr
    remove_pre_summary = _psm

    _d_min = data["Date"].min().to_pydatetime()
    if remove_pre_tracking:
        _d_min = max(_d_min, pd.Timestamp('2025-10-20').to_pydatetime())
    if remove_pre_survey:
        _d_min = max(_d_min, pd.Timestamp('2026-05-18').to_pydatetime())
    if remove_pre_summary:
        _d_min = max(_d_min, pd.Timestamp('2026-07-27').to_pydatetime())
    _d_max = data["Date"].max().to_pydatetime()
    start_date, end_date = st.slider(
        "Date Range",
        min_value=_d_min, max_value=_d_max,
        value=(_d_min, _d_max),
        format="MMM DD, YYYY",
        key=f"cc_date_range_{_ptr}_{_psr}_{_psm}",
        label_visibility="collapsed"
    )

    st.markdown('<hr style="border:none;border-top:1px solid #d9d7cc;margin:8px 24px 12px 24px;">', unsafe_allow_html=True)

    # Every view (Scores and Win Margins, Cross and Self) now has its own
    # rolling-window control inside its own box, top-right — none of them
    # need a sidebar slider anymore.
    window_length = 5
    bin_size = 1000

    if comp_type == 'Cross' and view_mode == "Scores":
        _ispd = st.session_state.get('cc_include_single', False)
        if st.button("Single-Player Days", key="cc_btn_single", use_container_width=True,
                     type="primary" if _ispd else "secondary"):
            st.session_state['cc_include_single'] = not _ispd
            st.rerun()
        include_single_player_days = _ispd
    else:
        include_single_player_days = False

    include_self_single = False
    if comp_type == 'Self' and player != 'Combined' and view_mode in ('Scores', 'Win Margins'):
        _iss = st.session_state.get('cc_self_single', False)
        if st.button("Single-Player Days", key="cc_btn_self_single", use_container_width=True,
                     type="primary" if _iss else "secondary"):
            st.session_state['cc_self_single'] = not _iss
            st.rerun()
        include_self_single = _iss

    if comp_type == 'Self':
        player_data = self_prepare_player_data(data, player, False, include_self_single)
        if remove_pre_tracking:
            player_data = player_data[player_data['Date'] >= pd.Timestamp('2025-10-20')].copy()
        if remove_pre_survey:
            player_data = player_data[player_data['Date'] >= pd.Timestamp('2026-05-18')].copy()
        if remove_pre_summary:
            player_data = player_data[player_data['Date'] >= pd.Timestamp('2026-07-27')].copy()
        if player_data.empty:
            st.warning("No data available for selected options.")
            st.stop()

# --- Main Area ---

if comp_type == 'Cross':
    # Prepare data based on page type
    if page_type == "Total Scores":
        df_daily, mask = prepare_total_scores_data(data, include_single_player_days)
        ceiling = CEILING_TOTAL
        score_type = "total"
    elif page_type == "Time Scores":
        df_daily, mask = prepare_time_scores_data(data, False, include_single_player_days)
        ceiling = CEILING_TIME
        score_type = "time"
    else:
        df_daily, mask = prepare_geography_scores_data(data, False, include_single_player_days)
        ceiling = CEILING_GEOGRAPHY
        score_type = "geography"

    if remove_pre_tracking:
        mask = mask[mask['Date'] >= pd.Timestamp('2025-10-20')].copy()
        df_daily = df_daily[df_daily['Date'] >= pd.Timestamp('2025-10-20')].copy()
    if remove_pre_survey:
        mask = mask[mask['Date'] >= pd.Timestamp('2026-05-18')].copy()
        df_daily = df_daily[df_daily['Date'] >= pd.Timestamp('2026-05-18')].copy()
    if remove_pre_summary:
        mask = mask[mask['Date'] >= pd.Timestamp('2026-07-27')].copy()
        df_daily = df_daily[df_daily['Date'] >= pd.Timestamp('2026-07-27')].copy()

    view_label = page_type if view_mode == "Scores" else page_type.replace("Scores", "Win Margins")
    st.markdown(f'<div class="page-title-stack"><div class="page-title">{view_label}</div></div>', unsafe_allow_html=True)

    mask_filtered = mask[(mask["Date"] >= start_date) & (mask["Date"] <= end_date)].copy()
    df_daily_filtered = df_daily[(df_daily["Date"] >= start_date) & (df_daily["Date"] <= end_date)].copy()

    if view_mode == "Scores":
        with st.container(key="main_chart_box"):
            _mc_title_col, _mc_score_col, _mc_slider_outer = st.columns([1.3, 1.6, 1.3])
            with _mc_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Scores</h4>',
                    unsafe_allow_html=True
                )
            if score_type == "total":
                _mc_m_col, _mc_s_col = "Michael Total Score", "Sarah Total Score"
            elif score_type == "time":
                _mc_m_col, _mc_s_col = "Michael Time Midpoint", "Sarah Time Midpoint"
            else:
                _mc_m_col, _mc_s_col = "Michael Geography Midpoint", "Sarah Geography Midpoint"
            _mc_m_total = mask_filtered[_mc_m_col].sum()
            _mc_s_total = mask_filtered[_mc_s_col].sum()
            _mc_m_mean = mask_filtered[_mc_m_col].mean()
            _mc_s_mean = mask_filtered[_mc_s_col].mean()
            _mc_m_weight = "800" if _mc_m_total >= _mc_s_total else "400"
            _mc_s_weight = "800" if _mc_s_total > _mc_m_total else "400"
            with _mc_score_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["michael"]};font-weight:{_mc_m_weight};">Michael: {_mc_m_total:,.0f}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["sarah"]};font-weight:{_mc_s_weight};">Sarah: {_mc_s_total:,.0f}</span>'
                    f'</div>'
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:11px;'
                    f'opacity:0.75;white-space:nowrap;margin-top:2px;">'
                    f'<span style="color:{COLORS["michael"]};">Avg {_mc_m_mean:,.0f}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["sarah"]};">Avg {_mc_s_mean:,.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with _mc_slider_outer:
                _mc_sl_spacer, _mc_sl_narrow = st.columns([0.3, 0.7])
                with _mc_sl_narrow:
                    with st.container(key="main_chart_rolling_slider"):
                        window_length = st.slider(
                            "Rolling Window", min_value=1, max_value=30, value=5, step=1,
                            key=f"cc_main_rolling_window_{score_type}", label_visibility="collapsed"
                        )

            mask_filtered = calculate_rolling_averages(mask_filtered, window_length, score_type)
            fig = create_plotly_figure(df_daily_filtered, mask_filtered, window_length, score_type,
                                       show_single_player_days=include_single_player_days)
            st.plotly_chart(fig, use_container_width=True, key="main_chart")

        with st.container(key="momentum_box"):
            mom_title_col, mom_score_col, mom_slider_col = st.columns([1.3, 1.6, 1.3])
            with mom_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Momentum</h4>',
                    unsafe_allow_html=True
                )
            with mom_slider_col:
                _sl_spacer, _sl_narrow = st.columns([0.3, 0.7])
                with _sl_narrow:
                    with st.container(key="momentum_games_slider"):
                        slider_max = min(max(len(mask_filtered), 5), 100)
                        n_days = st.slider(
                            "Games", min_value=5, max_value=slider_max, value=min(20, slider_max),
                            key=f"cc_momentum_games_{score_type}", label_visibility="collapsed"
                        )

            bars_html, m_total, s_total, m_mean, s_mean, m_weight, s_weight = create_momentum_html(mask_filtered, n_days, score_type)
            with mom_score_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["michael"]};font-weight:{m_weight};">Michael: {m_total:,.0f}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["sarah"]};font-weight:{s_weight};">Sarah: {s_total:,.0f}</span>'
                    f'</div>'
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:11px;'
                    f'opacity:0.75;white-space:nowrap;margin-top:2px;">'
                    f'<span style="color:{COLORS["michael"]};">Avg {m_mean:,.0f}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["sarah"]};">Avg {s_mean:,.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.markdown(bars_html, unsafe_allow_html=True)

        if score_type == "total":
            michael_scores = mask_filtered["Michael Total Score"].dropna()
            sarah_scores = mask_filtered["Sarah Total Score"].dropna()
            michael_dates = mask_filtered[mask_filtered["Michael Total Score"].notna()]["Date"]
            sarah_dates = mask_filtered[mask_filtered["Sarah Total Score"].notna()]["Date"]
        elif score_type == "time":
            michael_scores = mask_filtered["Michael Time Midpoint"].dropna()
            sarah_scores = mask_filtered["Sarah Time Midpoint"].dropna()
            michael_dates = mask_filtered[mask_filtered["Michael Time Midpoint"].notna()]["Date"]
            sarah_dates = mask_filtered[mask_filtered["Sarah Time Midpoint"].notna()]["Date"]
        else:
            michael_scores = mask_filtered["Michael Geography Midpoint"].dropna()
            sarah_scores = mask_filtered["Sarah Geography Midpoint"].dropna()
            michael_dates = mask_filtered[mask_filtered["Michael Geography Midpoint"].notna()]["Date"]
            sarah_dates = mask_filtered[mask_filtered["Sarah Geography Midpoint"].notna()]["Date"]

        _streak_mode_key = f'cc_streak_mode_{score_type}'
        streak_mode = st.session_state.get(_streak_mode_key, 'cumavg')

        with st.container(key="cumavg_streak_box"):
            title_col, slider_col, btn_col = st.columns([1.8, 1.5, 1.8])
            with title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Score Streaks</h4>',
                    unsafe_allow_html=True
                )

            threshold_score = None
            with slider_col:
                if streak_mode == "score":
                    with st.container(key="cumavg_streak_slider"):
                        combined_scores = pd.concat([michael_scores, sarah_scores])
                        slider_min = int(np.floor(combined_scores.min() / 50) * 50)
                        slider_max = int(np.ceil(combined_scores.max() / 50) * 50)
                        default_threshold = {"total": 42500, "time": 20000, "geography": 22500}[score_type]
                        default_threshold = min(max(default_threshold, slider_min), slider_max)
                        threshold_score = st.slider(
                            "Score Threshold", min_value=slider_min, max_value=slider_max,
                            value=default_threshold, step=50, key=f"cc_streak_threshold_{score_type}",
                            label_visibility="collapsed"
                        )

            with btn_col:
                _btn_sl_spacer, _btn_sl_narrow = st.columns([0.1, 0.9])
                with _btn_sl_narrow:
                    with st.container(key="cumavg_streak_toggle"):
                        _streak_tc1, _streak_tc2 = st.columns(2)
                        with _streak_tc1:
                            if st.button("Cum Avg", key=f"cc_streak_btn_avg_{score_type}", use_container_width=True,
                                         type="primary" if streak_mode == "cumavg" else "secondary"):
                                st.session_state[_streak_mode_key] = "cumavg"
                                st.rerun()
                        with _streak_tc2:
                            if st.button("Score", key=f"cc_streak_btn_score_{score_type}", use_container_width=True,
                                         type="primary" if streak_mode == "score" else "secondary"):
                                st.session_state[_streak_mode_key] = "score"
                                st.rerun()

            st.plotly_chart(create_cumulative_avg_streak_momentum_chart(
                [(michael_scores, michael_dates, 'Michael', COLORS['michael']),
                 (sarah_scores, sarah_dates, 'Sarah', COLORS['sarah'])], label=score_type.title(),
                mode=streak_mode, threshold=threshold_score
            ), use_container_width=True, key="cumulative_avg_streak_momentum_chart")

        _threshold_dir_key = f'cc_threshold_dir_{score_type}'
        threshold_dir = st.session_state.get(_threshold_dir_key, 'above')

        with st.container(key="score_dist_box"):
            dist_title_col, dist_modal_col, dist_slider_outer = st.columns([1.8, 1.5, 1.8])
            with dist_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Score Distribution</h4>',
                    unsafe_allow_html=True
                )
            with dist_slider_outer:
                _dist_sl_spacer, _dist_sl_narrow = st.columns([0.3, 0.7])
                with _dist_sl_narrow:
                    with st.container(key="score_dist_slider"):
                        _is_total_bucket = score_type == "total"
                        _bin_opts, _bin_def = (([250, 500, 1000, 2500], 1000) if _is_total_bucket
                                               else ([250, 500, 1250], 500))
                        bin_size = st.select_slider(
                            "Bucket Size", options=_bin_opts, value=_bin_def,
                            key=f"cc_bucket_{score_type}", label_visibility="collapsed"
                        )

            _dist_m_modal = compute_modal_bucket(michael_scores, ceiling, bin_size)
            _dist_s_modal = compute_modal_bucket(sarah_scores, ceiling, bin_size)
            with dist_modal_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:10px;'
                    f'color:#8f8d85;text-transform:uppercase;letter-spacing:1px;">Mode</div>'
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["michael"]};">Michael: {_dist_m_modal}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["sarah"]};">Sarah: {_dist_s_modal}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.plotly_chart(create_score_histogram(
                [(michael_scores, michael_dates, 'Michael', COLORS['michael']),
                 (sarah_scores, sarah_dates, 'Sarah', COLORS['sarah'])], ceiling, bin_size,
                trim_bin_size=2500 if score_type == "total" else 1250,
                label=score_type.title()
            ), use_container_width=True, key="score_histogram_chart")

        with st.container(key="threshold_pair_box"):
            _tp_title_col, _tp_btn_col = st.columns([3, 1.8])
            with _tp_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Score Thresholds</h4>',
                    unsafe_allow_html=True
                )
            with _tp_btn_col:
                _tp_sl_spacer, _tp_sl_narrow = st.columns([0.1, 0.9])
                with _tp_sl_narrow:
                    with st.container(key="threshold_pair_toggle"):
                        _tp_c1, _tp_c2 = st.columns(2)
                        with _tp_c1:
                            if st.button("Above", key=f"cc_threshold_btn_above_{score_type}", use_container_width=True,
                                         type="primary" if threshold_dir == "above" else "secondary"):
                                st.session_state[_threshold_dir_key] = "above"
                                st.rerun()
                        with _tp_c2:
                            if st.button("Below", key=f"cc_threshold_btn_below_{score_type}", use_container_width=True,
                                         type="primary" if threshold_dir == "below" else "secondary"):
                                st.session_state[_threshold_dir_key] = "below"
                                st.rerun()

            _is_below = threshold_dir == "below"
            pair_c1, pair_c2 = st.columns(2)
            with pair_c1:
                st.plotly_chart(apply_chart_title(create_cumulative_histogram(
                    [(michael_scores, michael_dates, 'Michael', COLORS['michael']),
                     (sarah_scores, sarah_dates, 'Sarah', COLORS['sarah'])], ceiling, reverse=_is_below
                ), f"Days At Or {'Below' if _is_below else 'Above'} Threshold X"
                ), use_container_width=True, key="cumulative_histogram_chart")
            with pair_c2:
                st.plotly_chart(apply_chart_title(create_streak_score_histogram(
                    [(michael_scores, michael_dates, 'Michael', COLORS['michael']),
                     (sarah_scores, sarah_dates, 'Sarah', COLORS['sarah'])], ceiling, reverse=_is_below
                ), f"Longest Streak At Or {'Below' if _is_below else 'Above'} X"
                ), use_container_width=True, key="streak_score_histogram_chart")

        with st.container(key="stability_pair_box"):
            _buf_title_col, _buf_sd_col, _buf_slider_outer = st.columns([1.8, 1.5, 1.8])
            with _buf_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Score Volatility</h4>',
                    unsafe_allow_html=True
                )
            with _buf_slider_outer:
                _buf_sl_spacer, _buf_sl_narrow = st.columns([0.3, 0.7])
                with _buf_sl_narrow:
                    with st.container(key="stability_buffer_slider"):
                        if score_type == "total":
                            _buf_min, _buf_max, _buf_step, _buf_def = 250, 5000, 250, 2500
                        else:
                            _buf_min, _buf_max, _buf_step, _buf_def = 125, 2500, 125, 1250
                        band_threshold = st.slider(
                            "Buffer", min_value=_buf_min, max_value=_buf_max, value=_buf_def, step=_buf_step,
                            key=f"cc_stability_buffer_{score_type}", label_visibility="collapsed"
                        )

            _buf_m_sd = michael_scores.std() if len(michael_scores) > 0 else 0
            _buf_s_sd = sarah_scores.std() if len(sarah_scores) > 0 else 0
            with _buf_sd_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:10px;'
                    f'color:#8f8d85;text-transform:uppercase;letter-spacing:1px;">Standard Deviation</div>'
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["michael"]};">Michael: {_buf_m_sd:,.0f}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["sarah"]};">Sarah: {_buf_s_sd:,.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            band_label = f"{band_threshold:,.0f}"
            instability_band = band_threshold // 2
            instability_band_label = f"{instability_band:,.0f}"

            stab_c1, stab_c2 = st.columns(2)
            with stab_c1:
                st.plotly_chart(apply_chart_title(create_streak_band_histogram(
                    [(michael_scores, michael_dates, 'Michael', COLORS['michael']),
                     (sarah_scores, sarah_dates, 'Sarah', COLORS['sarah'])], ceiling, band=band_threshold
                ), "Stability",
                  f"Longest streak staying within ±{band_label} of X"
                ), use_container_width=True, key="streak_band_histogram_chart")
            with stab_c2:
                st.plotly_chart(apply_chart_title(create_streak_instability_histogram(
                    [(michael_scores, michael_dates, 'Michael', COLORS['michael']),
                     (sarah_scores, sarah_dates, 'Sarah', COLORS['sarah'])], ceiling, band=instability_band
                ), "Instability",
                  f"Longest streak hopping between above and below X, ±{instability_band_label} buffer"
                ), use_container_width=True, key="streak_instability_histogram_chart")

    else:
        if score_type == "total":
            margin_mask = mask_filtered[mask_filtered["Michael Total Score"].notna() & mask_filtered["Sarah Total Score"].notna()].copy()
            margin_mask["Score Diff"] = margin_mask["Michael Total Score"] - margin_mask["Sarah Total Score"]
        elif score_type == "time":
            margin_mask = mask_filtered[mask_filtered["Michael Time Midpoint"].notna() & mask_filtered["Sarah Time Midpoint"].notna()].copy()
            margin_mask["Score Diff"] = margin_mask["Michael Time Midpoint"] - margin_mask["Sarah Time Midpoint"]
        else:
            margin_mask = mask_filtered[mask_filtered["Michael Geography Midpoint"].notna() & mask_filtered["Sarah Geography Midpoint"].notna()].copy()
            margin_mask["Score Diff"] = margin_mask["Michael Geography Midpoint"] - margin_mask["Sarah Geography Midpoint"]

        with st.container(key="main_chart_box"):
            _mc_title_col, _mc_score_col, _mc_slider_outer = st.columns([1.3, 1.6, 1.3])
            with _mc_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Win Margins</h4>',
                    unsafe_allow_html=True
                )
            _mc_m_wins = (margin_mask["Score Diff"] > 0).sum()
            _mc_s_wins = (margin_mask["Score Diff"] < 0).sum()
            _mc_m_weight = "800" if _mc_m_wins >= _mc_s_wins else "400"
            _mc_s_weight = "800" if _mc_s_wins > _mc_m_wins else "400"
            with _mc_score_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["michael"]};font-weight:{_mc_m_weight};">Michael: {_mc_m_wins}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["sarah"]};font-weight:{_mc_s_weight};">Sarah: {_mc_s_wins}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with _mc_slider_outer:
                _mc_sl_spacer, _mc_sl_narrow = st.columns([0.3, 0.7])
                with _mc_sl_narrow:
                    with st.container(key="main_chart_rolling_slider"):
                        window_length = st.slider(
                            "Rolling Window", min_value=1, max_value=30, value=5, step=1,
                            key=f"cc_margin_rolling_window_{score_type}", label_visibility="collapsed"
                        )

            margin_mask["Rolling Diff"] = margin_mask["Score Diff"].rolling(window=window_length, min_periods=1).mean()
            margin_mask["Cumulative Diff"] = margin_mask["Score Diff"].expanding().mean()
            margin_mask = add_zero_crossing_interpolation(margin_mask, window_length)

            st.plotly_chart(create_win_margins_figure(margin_mask, window_length),
                            use_container_width=True, key="win_margins_chart")

        margin_original = margin_mask[margin_mask["Date"].dt.time == pd.Timestamp("00:00:00").time()].copy().reset_index(drop=True)

        # Each player's winning margin on the days they actually won (mirrors the
        # raw per-player score series used by the Scores tab's histograms above).
        # Used for the cumulative histogram, where only the count of qualifying
        # days matters, not their order.
        michael_margins = margin_original.loc[margin_original["Score Diff"] > 0, "Score Diff"]
        sarah_margins = -margin_original.loc[margin_original["Score Diff"] < 0, "Score Diff"]
        michael_margin_dates = margin_original.loc[michael_margins.index, "Date"]
        sarah_margin_dates = margin_original.loc[sarah_margins.index, "Date"]

        # Margins run far smaller than the full score ceiling, so scale the x-axis
        # to the data itself — the nearest 5,000 at or above the largest margin —
        # instead of stretching it out to the score ceiling.
        max_margin = pd.concat([michael_margins, sarah_margins]).max() if (len(michael_margins) or len(sarah_margins)) else 0
        margin_ceiling = int(np.ceil(max(max_margin, 1) / 5000) * 5000)

        with st.container(key="momentum_box"):
            mom_title_col, mom_score_col, mom_slider_col = st.columns([1.3, 1.6, 1.3])
            with mom_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Momentum</h4>',
                    unsafe_allow_html=True
                )
            with mom_slider_col:
                _sl_spacer, _sl_narrow = st.columns([0.3, 0.7])
                with _sl_narrow:
                    with st.container(key="momentum_games_slider"):
                        slider_max = min(max(len(margin_original), 5), 100)
                        n_days = st.slider(
                            "Games", min_value=5, max_value=slider_max, value=min(20, slider_max),
                            key=f"cc_margin_momentum_games_{score_type}", label_visibility="collapsed"
                        )

            bars_html, m_wins, s_wins = create_momentum_timeline(margin_original, n_days)
            with mom_score_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["michael"]};">Michael: {m_wins}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["sarah"]};">Sarah: {s_wins}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.markdown(bars_html, unsafe_allow_html=True)

        # Completed win streaks, used for the "Streaks >= X" count plot below
        # the main win-streak bar strip — each streak counted once per length
        # threshold it qualifies for, not split into sub-streaks.
        win_streaks = calculate_win_streaks(margin_original)
        michael_streak_lengths = [(s['length'], s['end_date']) for s in win_streaks if s['winner'] == 'Michael']
        sarah_streak_lengths = [(s['length'], s['end_date']) for s in win_streaks if s['winner'] == 'Sarah']

        with st.container(key="cumavg_streak_box"):
            st.markdown(
                f'<h4 style="margin:4px 0 10px 0;color:{COLORS["text"]};font-size:16px;'
                f'text-transform:uppercase;letter-spacing:1px;">Win Streaks</h4>',
                unsafe_allow_html=True
            )
            st.plotly_chart(create_win_streak_chart(
                margin_original["Date"], margin_original["Score Diff"],
                name_above="Michael", name_below="Sarah",
                color_above=COLORS['michael'], color_below=COLORS['sarah']
            ), use_container_width=True, key="win_streak_chart")
            st.plotly_chart(create_streak_count_histogram(
                [(michael_streak_lengths, 'Michael', COLORS['michael']),
                 (sarah_streak_lengths, 'Sarah', COLORS['sarah'])]
            ), use_container_width=True, key="margin_streak_count_histogram_chart")

        with st.container(key="score_dist_box"):
            _wd_title_col, _wd_modal_col, _wd_slider_outer = st.columns([1.8, 1.5, 1.8])
            with _wd_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Win Distribution</h4>',
                    unsafe_allow_html=True
                )
            with _wd_slider_outer:
                _wd_sl_spacer, _wd_sl_narrow = st.columns([0.3, 0.7])
                with _wd_sl_narrow:
                    with st.container(key="score_dist_slider"):
                        _wd_bin_opts, _wd_bin_def = [250, 500, 1000, 2500], 500
                        wd_bin_size = st.select_slider(
                            "Bucket Size", options=_wd_bin_opts, value=_wd_bin_def,
                            key=f"cc_margin_bucket_{score_type}", label_visibility="collapsed"
                        )

            _wd_m_modal = compute_modal_bucket(michael_margins, margin_ceiling, wd_bin_size)
            _wd_s_modal = compute_modal_bucket(sarah_margins, margin_ceiling, wd_bin_size)
            with _wd_modal_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:10px;'
                    f'color:#8f8d85;text-transform:uppercase;letter-spacing:1px;">Mode</div>'
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["michael"]};">Michael: {_wd_m_modal}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["sarah"]};">Sarah: {_wd_s_modal}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.plotly_chart(create_score_histogram(
                [(michael_margins, michael_margin_dates, 'Michael', COLORS['michael']),
                 (sarah_margins, sarah_margin_dates, 'Sarah', COLORS['sarah'])], margin_ceiling, wd_bin_size,
                trim_bin_size=max(_wd_bin_opts), label="Margin"
            ), use_container_width=True, key="margin_distribution_chart")

        # The streak histogram needs actual day-to-day adjacency, so it can't use
        # the win-only series above (that silently skips every day the OTHER
        # player won, which would let a streak jump across a loss). Instead, walk
        # every played day in order and give a non-winning day a margin of 0 —
        # below any positive threshold — so it correctly breaks the streak.
        # -1 (not 0) for a non-winning day: a threshold of X=0 would otherwise count
        # as "margin >= 0" for every non-winning day too (losses and ties alike),
        # inflating the streak with days that were never wins at all.
        _score_diff = margin_original["Score Diff"]
        michael_streak_margins = _score_diff.where(_score_diff > 0, -1)
        sarah_streak_margins = (-_score_diff).where(_score_diff < 0, -1)
        streak_dates = margin_original["Date"]

        _margin_threshold_dir_key = f'cc_margin_threshold_dir_{score_type}'
        margin_threshold_dir = st.session_state.get(_margin_threshold_dir_key, 'above')

        with st.container(key="threshold_pair_box"):
            _mtp_title_col, _mtp_btn_col = st.columns([3, 1.8])
            with _mtp_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Win Thresholds</h4>',
                    unsafe_allow_html=True
                )
            with _mtp_btn_col:
                _mtp_sl_spacer, _mtp_sl_narrow = st.columns([0.1, 0.9])
                with _mtp_sl_narrow:
                    with st.container(key="threshold_pair_toggle"):
                        _mtp_c1, _mtp_c2 = st.columns(2)
                        with _mtp_c1:
                            if st.button("Above", key=f"cc_margin_threshold_btn_above_{score_type}", use_container_width=True,
                                         type="primary" if margin_threshold_dir == "above" else "secondary"):
                                st.session_state[_margin_threshold_dir_key] = "above"
                                st.rerun()
                        with _mtp_c2:
                            if st.button("Below", key=f"cc_margin_threshold_btn_below_{score_type}", use_container_width=True,
                                         type="primary" if margin_threshold_dir == "below" else "secondary"):
                                st.session_state[_margin_threshold_dir_key] = "below"
                                st.rerun()

            _mtp_is_below = margin_threshold_dir == "below"
            mtp_c1, mtp_c2 = st.columns(2)
            with mtp_c1:
                st.plotly_chart(apply_chart_title(create_cumulative_histogram(
                    [(michael_margins, michael_margin_dates, 'Michael', COLORS['michael']),
                     (sarah_margins, sarah_margin_dates, 'Sarah', COLORS['sarah'])], margin_ceiling,
                    reverse=_mtp_is_below, label="Margin"
                ), f"Days At Or {'Below' if _mtp_is_below else 'Above'} Threshold X"
                ), use_container_width=True, key="margin_cumulative_histogram_chart")
            with mtp_c2:
                st.plotly_chart(apply_chart_title(create_streak_score_histogram(
                    [(michael_streak_margins, streak_dates, 'Michael', COLORS['michael']),
                     (sarah_streak_margins, streak_dates, 'Sarah', COLORS['sarah'])], margin_ceiling,
                    reverse=_mtp_is_below, label="Margin"
                ), f"Longest Streak At Or {'Below' if _mtp_is_below else 'Above'} X"
                ), use_container_width=True, key="margin_streak_histogram_chart")

else:
    # --- Self Comparison ---
    player_data_filtered = player_data[(player_data["Date"] >= start_date) & (player_data["Date"] <= end_date)].copy()
    player_data_filtered = self_calculate_rolling_averages(player_data_filtered, window_length, player)

    time_col = f"{player} Time Midpoint"
    geo_col = f"{player} Geography Midpoint"

    if player == "Combined":
        streak_ceiling = 50000
    else:
        streak_ceiling = 25000

    solo_dates = set()
    if include_self_single and player != "Combined":
        daily_totals = data.groupby("Date")[["Michael Total Score", "Sarah Total Score"]].first()
        other = "Sarah Total Score" if player == "Michael" else "Michael Total Score"
        self_col = "Michael Total Score" if player == "Michael" else "Sarah Total Score"
        solo_days = daily_totals[daily_totals[self_col].notna() & daily_totals[other].isna()].index
        solo_dates = set(solo_days)

    if view_mode == "Scores":
        st.markdown(f'<div class="page-title-stack"><div class="page-title">{player} Scores</div></div>', unsafe_allow_html=True)
        with st.container(key="main_chart_box"):
            _mc_title_col, _mc_score_col, _mc_slider_outer = st.columns([1.3, 1.6, 1.3])
            with _mc_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Scores</h4>',
                    unsafe_allow_html=True
                )
            _mc_t_total = player_data_filtered[time_col].sum()
            _mc_g_total = player_data_filtered[geo_col].sum()
            _mc_t_mean = player_data_filtered[time_col].mean()
            _mc_g_mean = player_data_filtered[geo_col].mean()
            _mc_t_weight = "800" if _mc_t_total >= _mc_g_total else "400"
            _mc_g_weight = "800" if _mc_g_total > _mc_t_total else "400"
            with _mc_score_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["time"]};font-weight:{_mc_t_weight};">Time: {_mc_t_total:,.0f}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["geography"]};font-weight:{_mc_g_weight};">Geography: {_mc_g_total:,.0f}</span>'
                    f'</div>'
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:11px;'
                    f'opacity:0.75;white-space:nowrap;margin-top:2px;">'
                    f'<span style="color:{COLORS["time"]};">Avg {_mc_t_mean:,.0f}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["geography"]};">Avg {_mc_g_mean:,.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with _mc_slider_outer:
                _mc_sl_spacer, _mc_sl_narrow = st.columns([0.3, 0.7])
                with _mc_sl_narrow:
                    with st.container(key="main_chart_rolling_slider"):
                        window_length = st.slider(
                            "Rolling Window", min_value=1, max_value=30, value=5, step=1,
                            key=f"self_main_rolling_window_{player}", label_visibility="collapsed"
                        )

            player_data_filtered = self_calculate_rolling_averages(player_data_filtered, window_length, player)
            fig = self_create_plotly_figure(player_data_filtered, window_length, player, solo_dates=solo_dates)
            st.plotly_chart(fig, use_container_width=True, key="self_main_chart")

        with st.container(key="momentum_box"):
            mom_title_col, mom_score_col, mom_slider_col = st.columns([1.3, 1.6, 1.3])
            with mom_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Momentum</h4>',
                    unsafe_allow_html=True
                )
            with mom_slider_col:
                _sl_spacer, _sl_narrow = st.columns([0.3, 0.7])
                with _sl_narrow:
                    with st.container(key="momentum_games_slider"):
                        slider_max = min(max(len(player_data_filtered), 5), 100)
                        n_days = st.slider(
                            "Games", min_value=5, max_value=slider_max, value=min(20, slider_max),
                            key=f"self_momentum_games_{player}", label_visibility="collapsed"
                        )

            bars_html, t_total, g_total, t_mean, g_mean, t_weight, g_weight = self_create_scores_momentum_html(
                player_data_filtered, player, n_days
            )
            with mom_score_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["time"]};font-weight:{t_weight};">Time: {t_total:,.0f}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["geography"]};font-weight:{g_weight};">Geography: {g_total:,.0f}</span>'
                    f'</div>'
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:11px;'
                    f'opacity:0.75;white-space:nowrap;margin-top:2px;">'
                    f'<span style="color:{COLORS["time"]};">Avg {t_mean:,.0f}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["geography"]};">Avg {g_mean:,.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.markdown(bars_html, unsafe_allow_html=True)

        time_scores = player_data_filtered[time_col].dropna()
        geo_scores = player_data_filtered[geo_col].dropna()
        time_dates = player_data_filtered[player_data_filtered[time_col].notna()]["Date"]
        geo_dates = player_data_filtered[player_data_filtered[geo_col].notna()]["Date"]

        _streak_mode_key = f'self_streak_mode_{player}'
        streak_mode = st.session_state.get(_streak_mode_key, 'cumavg')

        with st.container(key="cumavg_streak_box"):
            title_col, slider_col, btn_col = st.columns([1.8, 1.5, 1.8])
            with title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Score Streaks</h4>',
                    unsafe_allow_html=True
                )

            threshold_score = None
            with slider_col:
                if streak_mode == "score":
                    with st.container(key="cumavg_streak_slider"):
                        combined_scores = pd.concat([time_scores, geo_scores])
                        slider_min = int(np.floor(combined_scores.min() / 50) * 50)
                        slider_max = int(np.ceil(combined_scores.max() / 50) * 50)
                        default_threshold = int(round(streak_ceiling * 0.85 / 50) * 50)
                        default_threshold = min(max(default_threshold, slider_min), slider_max)
                        threshold_score = st.slider(
                            "Score Threshold", min_value=slider_min, max_value=slider_max,
                            value=default_threshold, step=50, key=f"self_streak_threshold_{player}",
                            label_visibility="collapsed"
                        )

            with btn_col:
                _btn_sl_spacer, _btn_sl_narrow = st.columns([0.1, 0.9])
                with _btn_sl_narrow:
                    with st.container(key="cumavg_streak_toggle"):
                        _streak_tc1, _streak_tc2 = st.columns(2)
                        with _streak_tc1:
                            if st.button("Cum Avg", key=f"self_streak_btn_avg_{player}", use_container_width=True,
                                         type="primary" if streak_mode == "cumavg" else "secondary"):
                                st.session_state[_streak_mode_key] = "cumavg"
                                st.rerun()
                        with _streak_tc2:
                            if st.button("Score", key=f"self_streak_btn_score_{player}", use_container_width=True,
                                         type="primary" if streak_mode == "score" else "secondary"):
                                st.session_state[_streak_mode_key] = "score"
                                st.rerun()

            st.plotly_chart(create_cumulative_avg_streak_momentum_chart(
                [(time_scores, time_dates, 'Time', COLORS['time']),
                 (geo_scores, geo_dates, 'Geography', COLORS['geography'])], label="Score",
                mode=streak_mode, threshold=threshold_score
            ), use_container_width=True, key="cumulative_avg_streak_momentum_chart")

        _threshold_dir_key = f'self_threshold_dir_{player}'
        threshold_dir = st.session_state.get(_threshold_dir_key, 'above')

        with st.container(key="score_dist_box"):
            dist_title_col, dist_modal_col, dist_slider_outer = st.columns([1.8, 1.5, 1.8])
            with dist_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Score Distribution</h4>',
                    unsafe_allow_html=True
                )
            with dist_slider_outer:
                _dist_sl_spacer, _dist_sl_narrow = st.columns([0.3, 0.7])
                with _dist_sl_narrow:
                    with st.container(key="score_dist_slider"):
                        _is_combined_bucket = player == "Combined"
                        _bin_opts, _bin_def = (([500, 1000, 2000, 5000], 2000) if _is_combined_bucket
                                               else ([250, 500, 1250], 500))
                        bin_size = st.select_slider(
                            "Bucket Size", options=_bin_opts, value=_bin_def,
                            key=f"self_bucket_{player}", label_visibility="collapsed"
                        )

            _dist_t_modal = compute_modal_bucket(time_scores, streak_ceiling, bin_size)
            _dist_g_modal = compute_modal_bucket(geo_scores, streak_ceiling, bin_size)
            with dist_modal_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:10px;'
                    f'color:#8f8d85;text-transform:uppercase;letter-spacing:1px;">Mode</div>'
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["time"]};">Time: {_dist_t_modal}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["geography"]};">Geography: {_dist_g_modal}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.plotly_chart(create_score_histogram(
                [(time_scores, time_dates, 'Time', COLORS['time']),
                 (geo_scores, geo_dates, 'Geography', COLORS['geography'])], streak_ceiling, bin_size,
                trim_bin_size=5000 if _is_combined_bucket else 1250,
                label="Score"
            ), use_container_width=True, key="score_histogram_chart")

        with st.container(key="threshold_pair_box"):
            _tp_title_col, _tp_btn_col = st.columns([3, 1.8])
            with _tp_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Score Thresholds</h4>',
                    unsafe_allow_html=True
                )
            with _tp_btn_col:
                _tp_sl_spacer, _tp_sl_narrow = st.columns([0.1, 0.9])
                with _tp_sl_narrow:
                    with st.container(key="threshold_pair_toggle"):
                        _tp_c1, _tp_c2 = st.columns(2)
                        with _tp_c1:
                            if st.button("Above", key=f"self_threshold_btn_above_{player}", use_container_width=True,
                                         type="primary" if threshold_dir == "above" else "secondary"):
                                st.session_state[_threshold_dir_key] = "above"
                                st.rerun()
                        with _tp_c2:
                            if st.button("Below", key=f"self_threshold_btn_below_{player}", use_container_width=True,
                                         type="primary" if threshold_dir == "below" else "secondary"):
                                st.session_state[_threshold_dir_key] = "below"
                                st.rerun()

            _is_below = threshold_dir == "below"
            pair_c1, pair_c2 = st.columns(2)
            with pair_c1:
                st.plotly_chart(apply_chart_title(create_cumulative_histogram(
                    [(time_scores, time_dates, 'Time', COLORS['time']),
                     (geo_scores, geo_dates, 'Geography', COLORS['geography'])], streak_ceiling, reverse=_is_below
                ), f"Days At Or {'Below' if _is_below else 'Above'} Threshold X"
                ), use_container_width=True, key="cumulative_histogram_chart")
            with pair_c2:
                st.plotly_chart(apply_chart_title(create_streak_score_histogram(
                    [(time_scores, time_dates, 'Time', COLORS['time']),
                     (geo_scores, geo_dates, 'Geography', COLORS['geography'])], streak_ceiling, reverse=_is_below
                ), f"Longest Streak At Or {'Below' if _is_below else 'Above'} X"
                ), use_container_width=True, key="streak_score_histogram_chart")

        with st.container(key="stability_pair_box"):
            _buf_title_col, _buf_sd_col, _buf_slider_outer = st.columns([1.8, 1.5, 1.8])
            with _buf_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Score Volatility</h4>',
                    unsafe_allow_html=True
                )
            with _buf_slider_outer:
                _buf_sl_spacer, _buf_sl_narrow = st.columns([0.3, 0.7])
                with _buf_sl_narrow:
                    with st.container(key="stability_buffer_slider"):
                        if player == "Combined":
                            _buf_min, _buf_max, _buf_step, _buf_def = 250, 5000, 250, 2500
                        else:
                            _buf_min, _buf_max, _buf_step, _buf_def = 125, 2500, 125, 1250
                        band_threshold = st.slider(
                            "Buffer", min_value=_buf_min, max_value=_buf_max, value=_buf_def, step=_buf_step,
                            key=f"self_stability_buffer_{player}", label_visibility="collapsed"
                        )

            _buf_t_sd = time_scores.std() if len(time_scores) > 0 else 0
            _buf_g_sd = geo_scores.std() if len(geo_scores) > 0 else 0
            with _buf_sd_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:10px;'
                    f'color:#8f8d85;text-transform:uppercase;letter-spacing:1px;">Standard Deviation</div>'
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["time"]};">Time: {_buf_t_sd:,.0f}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["geography"]};">Geography: {_buf_g_sd:,.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            band_label = f"{band_threshold:,.0f}"
            instability_band = band_threshold // 2
            instability_band_label = f"{instability_band:,.0f}"

            stab_c1, stab_c2 = st.columns(2)
            with stab_c1:
                st.plotly_chart(apply_chart_title(create_streak_band_histogram(
                    [(time_scores, time_dates, 'Time', COLORS['time']),
                     (geo_scores, geo_dates, 'Geography', COLORS['geography'])], streak_ceiling, band=band_threshold
                ), "Stability",
                  f"Longest streak staying within ±{band_label} of X"
                ), use_container_width=True, key="streak_band_histogram_chart")
            with stab_c2:
                st.plotly_chart(apply_chart_title(create_streak_instability_histogram(
                    [(time_scores, time_dates, 'Time', COLORS['time']),
                     (geo_scores, geo_dates, 'Geography', COLORS['geography'])], streak_ceiling, band=instability_band
                ), "Instability",
                  f"Longest streak hopping between above and below X, ±{instability_band_label} buffer"
                ), use_container_width=True, key="streak_instability_histogram_chart")

    else:
        # Win Margins requires both scores — filter to days where both are present
        margin_data = player_data_filtered[player_data_filtered[time_col].notna() & player_data_filtered[geo_col].notna()].copy().reset_index(drop=True)
        margin_data["Score Diff"] = margin_data[time_col] - margin_data[geo_col]

        with st.container(key="main_chart_box"):
            _mc_title_col, _mc_score_col, _mc_slider_outer = st.columns([1.3, 1.6, 1.3])
            with _mc_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Win Margins</h4>',
                    unsafe_allow_html=True
                )
            _mc_t_wins = (margin_data["Score Diff"] > 0).sum()
            _mc_g_wins = (margin_data["Score Diff"] < 0).sum()
            _mc_t_weight = "800" if _mc_t_wins >= _mc_g_wins else "400"
            _mc_g_weight = "800" if _mc_g_wins > _mc_t_wins else "400"
            with _mc_score_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["time"]};font-weight:{_mc_t_weight};">Time: {_mc_t_wins}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["geography"]};font-weight:{_mc_g_weight};">Geography: {_mc_g_wins}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with _mc_slider_outer:
                _mc_sl_spacer, _mc_sl_narrow = st.columns([0.3, 0.7])
                with _mc_sl_narrow:
                    with st.container(key="main_chart_rolling_slider"):
                        window_length = st.slider(
                            "Rolling Window", min_value=1, max_value=30, value=5, step=1,
                            key=f"self_margin_rolling_window_{player}", label_visibility="collapsed"
                        )

            margin_data["Rolling Diff"] = margin_data["Score Diff"].rolling(window=window_length, min_periods=1).mean()
            margin_data["Cumulative Diff"] = margin_data["Score Diff"].expanding().mean()
            margin_data_original = margin_data.copy()
            margin_data = add_zero_crossing_interpolation(margin_data, window_length)

            st.plotly_chart(self_create_win_margins_figure(margin_data, window_length, player, solo_dates=solo_dates),
                            use_container_width=True, key="self_margin_chart")

        with st.container(key="momentum_box"):
            mom_title_col, mom_score_col, mom_slider_col = st.columns([1.3, 1.6, 1.3])
            with mom_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Momentum</h4>',
                    unsafe_allow_html=True
                )
            with mom_slider_col:
                _sl_spacer, _sl_narrow = st.columns([0.3, 0.7])
                with _sl_narrow:
                    with st.container(key="momentum_games_slider"):
                        slider_max = min(max(len(margin_data_original), 5), 100)
                        n_days = st.slider(
                            "Games", min_value=5, max_value=slider_max, value=min(20, slider_max),
                            key=f"self_margin_momentum_games_{player}", label_visibility="collapsed"
                        )

            bars_html, t_wins, g_wins = self_create_momentum_timeline(margin_data_original, n_days)
            with mom_score_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["time"]};">Time: {t_wins}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["geography"]};">Geography: {g_wins}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.markdown(bars_html, unsafe_allow_html=True)

        # Completed win streaks, used for the "Streaks >= X" count plot below
        # the main win-streak bar strip — each streak counted once per length
        # threshold it qualifies for, not split into sub-streaks.
        self_win_streaks = calculate_win_streaks(margin_data_original, name_above="Time", name_below="Geography")
        time_streak_lengths = [(s['length'], s['end_date']) for s in self_win_streaks if s['winner'] == 'Time']
        geo_streak_lengths = [(s['length'], s['end_date']) for s in self_win_streaks if s['winner'] == 'Geography']

        with st.container(key="cumavg_streak_box"):
            st.markdown(
                f'<h4 style="margin:4px 0 10px 0;color:{COLORS["text"]};font-size:16px;'
                f'text-transform:uppercase;letter-spacing:1px;">Win Streaks</h4>',
                unsafe_allow_html=True
            )
            st.plotly_chart(create_win_streak_chart(
                margin_data_original["Date"], margin_data_original["Score Diff"],
                name_above="Time", name_below="Geography",
                color_above=COLORS['time'], color_below=COLORS['geography']
            ), use_container_width=True, key="self_win_streak_chart")
            st.plotly_chart(create_streak_count_histogram(
                [(time_streak_lengths, 'Time', COLORS['time']),
                 (geo_streak_lengths, 'Geography', COLORS['geography'])]
            ), use_container_width=True, key="self_margin_streak_count_histogram_chart")

        # Each metric's winning margin on the days it actually won — mirrors the
        # raw per-metric score series used by the Scores tab's histograms.
        time_margins = margin_data_original.loc[margin_data_original["Score Diff"] > 0, "Score Diff"]
        geo_margins = -margin_data_original.loc[margin_data_original["Score Diff"] < 0, "Score Diff"]
        time_margin_dates = margin_data_original.loc[time_margins.index, "Date"]
        geo_margin_dates = margin_data_original.loc[geo_margins.index, "Date"]
        max_self_margin = pd.concat([time_margins, geo_margins]).max() if (len(time_margins) or len(geo_margins)) else 0
        self_margin_ceiling = int(np.ceil(max(max_self_margin, 1) / 5000) * 5000)

        with st.container(key="score_dist_box"):
            _wd_title_col, _wd_modal_col, _wd_slider_outer = st.columns([1.8, 1.5, 1.8])
            with _wd_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Win Distribution</h4>',
                    unsafe_allow_html=True
                )
            with _wd_slider_outer:
                _wd_sl_spacer, _wd_sl_narrow = st.columns([0.3, 0.7])
                with _wd_sl_narrow:
                    with st.container(key="score_dist_slider"):
                        _wd_bin_opts, _wd_bin_def = [250, 500, 1000, 2500], 500
                        wd_bin_size = st.select_slider(
                            "Bucket Size", options=_wd_bin_opts, value=_wd_bin_def,
                            key=f"self_margin_bucket_{player}", label_visibility="collapsed"
                        )

            _wd_t_modal = compute_modal_bucket(time_margins, self_margin_ceiling, wd_bin_size)
            _wd_g_modal = compute_modal_bucket(geo_margins, self_margin_ceiling, wd_bin_size)
            with _wd_modal_col:
                st.markdown(
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:10px;'
                    f'color:#8f8d85;text-transform:uppercase;letter-spacing:1px;">Mode</div>'
                    f'<div style="font-family:\'Poppins\',sans-serif;text-align:center;font-size:14px;'
                    f'font-weight:600;white-space:nowrap;">'
                    f'<span style="color:{COLORS["time"]};">Time: {_wd_t_modal}</span>'
                    f'<span style="color:#b0afaa;margin:0 8px;">|</span>'
                    f'<span style="color:{COLORS["geography"]};">Geography: {_wd_g_modal}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.plotly_chart(create_score_histogram(
                [(time_margins, time_margin_dates, 'Time', COLORS['time']),
                 (geo_margins, geo_margin_dates, 'Geography', COLORS['geography'])], self_margin_ceiling, wd_bin_size,
                trim_bin_size=max(_wd_bin_opts), label="Margin"
            ), use_container_width=True, key="self_margin_distribution_chart")

        # The streak histogram needs actual day-to-day adjacency, so it can't use
        # the win-only series above (that silently skips every day the OTHER
        # metric won, which would let a streak jump across a loss). Instead, walk
        # every played day in order and give a non-winning day a margin of 0 —
        # below any positive threshold — so it correctly breaks the streak.
        _self_score_diff = margin_data_original["Score Diff"]
        time_streak_margins = _self_score_diff.where(_self_score_diff > 0, -1)
        geo_streak_margins = (-_self_score_diff).where(_self_score_diff < 0, -1)
        self_streak_dates = margin_data_original["Date"]

        _self_margin_threshold_dir_key = f'self_margin_threshold_dir_{player}'
        self_margin_threshold_dir = st.session_state.get(_self_margin_threshold_dir_key, 'above')

        with st.container(key="threshold_pair_box"):
            _mtp_title_col, _mtp_btn_col = st.columns([3, 1.8])
            with _mtp_title_col:
                st.markdown(
                    f'<h4 style="margin:4px 0 0 0;color:{COLORS["text"]};font-size:16px;'
                    f'text-transform:uppercase;letter-spacing:1px;">Win Thresholds</h4>',
                    unsafe_allow_html=True
                )
            with _mtp_btn_col:
                _mtp_sl_spacer, _mtp_sl_narrow = st.columns([0.1, 0.9])
                with _mtp_sl_narrow:
                    with st.container(key="threshold_pair_toggle"):
                        _mtp_c1, _mtp_c2 = st.columns(2)
                        with _mtp_c1:
                            if st.button("Above", key=f"self_margin_threshold_btn_above_{player}", use_container_width=True,
                                         type="primary" if self_margin_threshold_dir == "above" else "secondary"):
                                st.session_state[_self_margin_threshold_dir_key] = "above"
                                st.rerun()
                        with _mtp_c2:
                            if st.button("Below", key=f"self_margin_threshold_btn_below_{player}", use_container_width=True,
                                         type="primary" if self_margin_threshold_dir == "below" else "secondary"):
                                st.session_state[_self_margin_threshold_dir_key] = "below"
                                st.rerun()

            _mtp_is_below = self_margin_threshold_dir == "below"
            mtp_c1, mtp_c2 = st.columns(2)
            with mtp_c1:
                st.plotly_chart(apply_chart_title(create_cumulative_histogram(
                    [(time_margins, time_margin_dates, 'Time', COLORS['time']),
                     (geo_margins, geo_margin_dates, 'Geography', COLORS['geography'])], self_margin_ceiling,
                    reverse=_mtp_is_below, label="Margin"
                ), f"Days At Or {'Below' if _mtp_is_below else 'Above'} Threshold X"
                ), use_container_width=True, key="self_margin_cumulative_histogram_chart")
            with mtp_c2:
                st.plotly_chart(apply_chart_title(create_streak_score_histogram(
                    [(time_streak_margins, self_streak_dates, 'Time', COLORS['time']),
                     (geo_streak_margins, self_streak_dates, 'Geography', COLORS['geography'])], self_margin_ceiling,
                    reverse=_mtp_is_below, label="Margin"
                ), f"Longest Streak At Or {'Below' if _mtp_is_below else 'Above'} X"
                ), use_container_width=True, key="self_margin_streak_histogram_chart")