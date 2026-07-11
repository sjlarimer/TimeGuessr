import os
import streamlit as st
from background import set_random_sarah_background

import pandas as pd
import numpy as np
import plotly.graph_objects as go
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
        /* View mode pill toggle buttons */
        div[data-testid="stSidebar"] button[data-testid="baseButton-primary"],
        div[data-testid="stSidebar"] button[kind="primary"] {
            background-color: #3a3935 !important;
            color: #eae8dc !important;
            border-color: #3a3935 !important;
            border-radius: 20px !important;
            font-weight: 600 !important;
        }
        div[data-testid="stSidebar"] button[data-testid="baseButton-secondary"],
        div[data-testid="stSidebar"] button[kind="secondary"] {
            background-color: #d9d7cc !important;
            color: #696761 !important;
            border-color: #d9d7cc !important;
            border-radius: 20px !important;
            font-weight: 500 !important;
        }
        div[data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover,
        div[data-testid="stSidebar"] button[kind="secondary"]:hover {
            background-color: #c8c6bb !important;
            color: #3a3935 !important;
            border-color: #8f8d85 !important;
        }
    </style>
"""
st.markdown(CUSTOM_STYLES, unsafe_allow_html=True)

set_random_sarah_background(lightness_level=0.7)

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
    
    if include_single:
        # Include all days with at least one score
        mask = df_daily[
            df_daily["Michael Total Score"].notna() | df_daily["Sarah Total Score"].notna()
        ][["Date", "Michael Total Score", "Sarah Total Score"]].copy()
    else:
        # Only include days where BOTH players have scores
        mask = df_daily[
            df_daily["Michael Total Score"].notna() & df_daily["Sarah Total Score"].notna()
        ][["Date", "Michael Total Score", "Sarah Total Score"]].copy()
    
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
            "Sarah": "Sarah Total Score"
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

def get_date_bold_style(date1: str, date2: str, date_format: str) -> Tuple[str, str]:
    """Return bold style for more recent date."""
    if date1 == '-' and date2 == '-':
        return "", ""
    if date1 == '-':
        return "", "font-weight: bold;"
    if date2 == '-':
        return "font-weight: bold;", ""
    
    try:
        # Extract the end date from ranges (e.g., "Sep 15 to Sep 16" -> "Sep 16")
        date1_end = date1.split(' to ')[-1].strip()
        date2_end = date2.split(' to ')[-1].strip()
        
        d1 = pd.to_datetime(date1_end, format=date_format)
        d2 = pd.to_datetime(date2_end, format=date_format)
        if d1 > d2:
            return "font-weight: bold;", ""
        elif d2 > d1:
            return "", "font-weight: bold;"
    except:
        pass
    return "", ""

def calculate_streak_with_dates(scores: np.ndarray, dates: pd.Series, 
                                threshold: float, above: bool = True, 
                                date_format: str = "%b %d") -> Tuple[int, str, str]:
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

def calculate_cumulative_avg_streak(scores: pd.Series, dates: pd.Series, 
                                   above: bool = True, 
                                   date_format: str = "%b %d") -> Tuple[int, str, str]:
    """Calculate longest streak relative to cumulative average."""
    if len(scores) == 0:
        return 0, "", ""
    
    scores_array = scores.values if hasattr(scores, 'values') else scores
    max_streak = 0
    current_streak = 0
    max_start_idx = 0
    max_end_idx = 0
    current_start_idx = 0

    for i in range(len(scores_array)):
        cumulative_avg = scores_array[:i+1].mean()
        condition = (above and scores_array[i] >= cumulative_avg) or (not above and scores_array[i] < cumulative_avg)
        
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

def calculate_score_change_streak(scores: np.ndarray, dates: pd.Series, 
                                  threshold: float, mode: str = "change", 
                                  date_format: str = "%b %d") -> Tuple[int, str, str]:
    """Calculate streak based on daily score changes."""
    if len(scores) < 2:
        return 0, "", ""

    max_streak = 0
    current_streak = 0
    max_start_idx = 0
    max_end_idx = 0
    current_start_idx = 0

    for i in range(1, len(scores)):
        diff = abs(scores[i] - scores[i - 1])
        condition = (mode == "change" and diff >= threshold) or (mode == "stable" and diff <= threshold)

        if condition:
            if current_streak == 0:
                current_start_idx = i - 1
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
    """Format bucket label based on range."""
    if is_top:
        return f"Scores {lower//1000}k+" if lower % 1000 == 0 else f"Scores {lower/1000:.1f}k+"
    elif bin_size == 1000:
        return f"Scores {lower//1000}k" if lower % 1000 == 0 else f"Scores {lower/1000:.1f}k"
    else:
        lower_str = f"{lower//1000}k" if lower % 1000 == 0 else f"{lower/1000:.1f}k"
        upper_str = f"{upper//1000}k" if upper % 1000 == 0 else f"{upper/1000:.1f}k"
        return f"Scores {lower_str}-{upper_str}"

def generate_buckets(michael_scores: pd.Series, sarah_scores: pd.Series, 
                    michael_dates: pd.Series, sarah_dates: pd.Series,
                    bin_size: int, date_format: str, ceiling: int) -> List[Dict]:
    """Generate score buckets with counts and dates."""
    buckets = []
    current_upper = ceiling

    while current_upper > 0:
        current_lower = max(current_upper - bin_size, 0)
        
        # Calculate masks
        if current_upper == ceiling:
            michael_mask = michael_scores >= current_lower
            sarah_mask = sarah_scores >= current_lower
        else:
            michael_mask = (michael_scores >= current_lower) & (michael_scores < current_upper)
            sarah_mask = (sarah_scores >= current_lower) & (sarah_scores < current_upper)
        
        michael_count = michael_mask.sum()
        sarah_count = sarah_mask.sum()
        
        # Only include bucket if either player has scores in it
        if michael_count > 0 or sarah_count > 0:
            michael_date = michael_dates[michael_mask].max().strftime(date_format) if michael_count > 0 else '-'
            sarah_date = sarah_dates[sarah_mask].max().strftime(date_format) if sarah_count > 0 else '-'
            
            label = format_bucket_label(current_lower, current_upper, bin_size, current_upper == ceiling)
            
            buckets.append({
                'label': label,
                'michael_count': michael_count,
                'michael_date': michael_date,
                'sarah_count': sarah_count,
                'sarah_date': sarah_date
            })
        
        current_upper = current_lower
        if current_lower == 0:
            break

    return buckets

def create_table_row(label: str, michael_val: str, sarah_val: str, 
                    michael_date: str, sarah_date: str, date_format: str,
                    border: bool = True, compare_values: bool = True) -> str:
    """Create HTML table row with proper styling."""
    border_style = "border-bottom: 1px solid #d9d7cc;" if border else ""
    
    # Value comparison for bolding
    michael_bold = ""
    sarah_bold = ""
    if compare_values and michael_val != '-' and sarah_val != '-':
        try:
            m_val = float(michael_val.replace(',', ''))
            s_val = float(sarah_val.replace(',', ''))
            michael_bold = "font-weight: bold;" if m_val > s_val else ""
            sarah_bold = "font-weight: bold;" if s_val > m_val else ""
        except:
            pass
    
    # Date comparison for bolding
    michael_date_bold, sarah_date_bold = get_date_bold_style(michael_date, sarah_date, date_format)
    
    return f"""<tr style="{border_style}">
        <td style="padding: 8px; color: #696761;">{label}</td>
        <td style="padding: 8px; text-align: center; color: {COLORS['michael']}; {michael_bold}">{michael_val}</td>
        <td style="padding: 8px; text-align: center; color: {COLORS['sarah']}; {sarah_bold}">{sarah_val}</td>
        <td style="padding: 8px; text-align: center; color: {COLORS['michael']}; font-size: 11px; {michael_date_bold}">{michael_date}</td>
        <td style="padding: 8px; text-align: center; color: {COLORS['sarah']}; font-size: 11px; {sarah_date_bold}">{sarah_date}</td>
    </tr>"""

def create_stats_table_html(michael_scores: pd.Series, sarah_scores: pd.Series,
                           michael_dates: pd.Series, sarah_dates: pd.Series,
                           bin_size: int, date_format: str, ceiling: int) -> str:
    """Create complete statistics table HTML."""
    # Check if we have any data
    if len(michael_scores) == 0 and len(sarah_scores) == 0:
        return "<p>No data available for the selected date range.</p>"
    
    # Calculate statistics
    michael_sum = michael_scores.sum() if len(michael_scores) > 0 else 0
    sarah_sum = sarah_scores.sum() if len(sarah_scores) > 0 else 0
    michael_mean = michael_scores.mean() if len(michael_scores) > 0 else 0
    sarah_mean = sarah_scores.mean() if len(sarah_scores) > 0 else 0
    michael_std = michael_scores.std() if len(michael_scores) > 0 else 0
    sarah_std = sarah_scores.std() if len(sarah_scores) > 0 else 0
    michael_median = michael_scores.median() if len(michael_scores) > 0 else 0
    sarah_median = sarah_scores.median() if len(sarah_scores) > 0 else 0
    michael_min = michael_scores.min() if len(michael_scores) > 0 else 0
    sarah_min = sarah_scores.min() if len(sarah_scores) > 0 else 0
    michael_max = michael_scores.max() if len(michael_scores) > 0 else 0
    sarah_max = sarah_scores.max() if len(sarah_scores) > 0 else 0
    
    # Find dates (with safety checks)
    michael_median_date = michael_dates.iloc[(michael_scores - michael_median).abs().argmin()].strftime(date_format) if len(michael_scores) > 0 else "-"
    sarah_median_date = sarah_dates.iloc[(sarah_scores - sarah_median).abs().argmin()].strftime(date_format) if len(sarah_scores) > 0 else "-"
    michael_min_date = michael_dates.iloc[michael_scores.argmin()].strftime(date_format) if len(michael_scores) > 0 else "-"
    sarah_min_date = sarah_dates.iloc[sarah_scores.argmin()].strftime(date_format) if len(sarah_scores) > 0 else "-"
    michael_max_date = michael_dates.iloc[michael_scores.argmax()].strftime(date_format) if len(michael_scores) > 0 else "-"
    sarah_max_date = sarah_dates.iloc[sarah_scores.argmax()].strftime(date_format) if len(sarah_scores) > 0 else "-"
    
    # Build rows
    rows = []
    rows.append(create_table_row("Sum", f"{int(michael_sum):,}", f"{int(sarah_sum):,}", "-", "-", date_format))
    rows.append(create_table_row("Mean", f"{michael_mean:.0f}", f"{sarah_mean:.0f}", "-", "-", date_format))
    rows.append(create_table_row("Standard Deviation", f"{michael_std:.0f}", f"{sarah_std:.0f}", "-", "-", date_format))
    rows.append(create_table_row("Max", f"{michael_max:.0f}", f"{sarah_max:.0f}", michael_max_date, sarah_max_date, date_format))
    rows.append(create_table_row("Median", f"{michael_median:.0f}", f"{sarah_median:.0f}", michael_median_date, sarah_median_date, date_format))
    rows.append(create_table_row("Min", f"{michael_min:.0f}", f"{sarah_min:.0f}", michael_min_date, sarah_min_date, date_format))
    
    # Add buckets if bin_size >= 2500 (for total scores) or bin_size >= 500 (for time scores)
    min_bin_threshold = 500 if ceiling <= 25000 else 2500
    if bin_size >= min_bin_threshold:
        buckets = generate_buckets(michael_scores, sarah_scores, michael_dates, sarah_dates, bin_size, date_format, ceiling)
        for i, bucket in enumerate(buckets):
            is_last = i == len(buckets) - 1
            rows.append(create_table_row(
                bucket['label'],
                str(bucket['michael_count']),
                str(bucket['sarah_count']),
                bucket['michael_date'],
                bucket['sarah_date'],
                date_format,
                border=not is_last
            ))
    
    return f"""
    <table class="stats-table" style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;">
        <thead>
            <tr style="background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;">
                <th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Statistic</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['michael']}; font-weight: 600;">Michael</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['sarah']}; font-weight: 600;">Sarah</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['michael']}; font-weight: 600;">Date</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['sarah']}; font-weight: 600;">Date</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """

def format_streak_dates(streak_count: int, start_date: str, end_date: str) -> str:
    """Format streak dates for display."""
    if streak_count == 0:
        return '-'
    return start_date if start_date == end_date else f"{start_date}<br/>to {end_date}"

def generate_streak_thresholds(michael_scores: pd.Series, sarah_scores: pd.Series, bin_size: int, ceiling: int) -> List[int]:
    """Generate streak thresholds based on bin size."""
    streak_thresholds = []
    current_upper = ceiling

    while current_upper > 0:
        current_lower = max(current_upper - bin_size, 0)
        
        # Check if there's any data in this range
        if current_upper == ceiling:
            michael_has_data = (michael_scores >= current_lower).any()
            sarah_has_data = (sarah_scores >= current_lower).any()
        else:
            michael_has_data = ((michael_scores >= current_lower) & (michael_scores < current_upper)).any()
            sarah_has_data = ((sarah_scores >= current_lower) & (sarah_scores < current_upper)).any()
        
        if michael_has_data or sarah_has_data:
            michael_all_above = (michael_scores >= current_lower).all()
            michael_all_below = (michael_scores < current_lower).all()
            sarah_all_above = (sarah_scores >= current_lower).all()
            sarah_all_below = (sarah_scores < current_lower).all()
            
            if not ((michael_all_above and sarah_all_above) or (michael_all_below and sarah_all_below)):
                streak_thresholds.append(current_lower)
        
        current_upper = current_lower
        if current_lower == 0:
            break

    return streak_thresholds

def create_streaks_table_html(michael_scores: pd.Series, sarah_scores: pd.Series,
                             michael_dates: pd.Series, sarah_dates: pd.Series,
                             bin_size: int, date_format: str, ceiling: int, 
                             change_threshold: int = 5000) -> str:
    """Create complete streaks table HTML."""
    streak_thresholds = generate_streak_thresholds(michael_scores, sarah_scores, bin_size, ceiling)
    
    rows = []
    
    # Above threshold streaks
    for threshold in streak_thresholds:
        michael_streak, michael_start, michael_end = calculate_streak_with_dates(
            michael_scores.values, michael_dates, threshold, above=True, date_format=date_format)
        sarah_streak, sarah_start, sarah_end = calculate_streak_with_dates(
            sarah_scores.values, sarah_dates, threshold, above=True, date_format=date_format)
        
        label = format_bucket_label(threshold, threshold + bin_size, bin_size).replace("Scores ", "Above ")
        if threshold % 1000 == 0:
            label = f"Above {threshold//1000}k"
        else:
            label = f"Above {threshold/1000:.1f}k"
        
        michael_dates_str = format_streak_dates(michael_streak, michael_start, michael_end)
        sarah_dates_str = format_streak_dates(sarah_streak, sarah_start, sarah_end)
        
        rows.append(create_table_row(label, str(michael_streak), str(sarah_streak), 
                                     michael_dates_str.replace('<br/>', ' '), 
                                     sarah_dates_str.replace('<br/>', ' '), 
                                     date_format))
    
    # Below threshold streaks
    for threshold in reversed(streak_thresholds):
        michael_streak, michael_start, michael_end = calculate_streak_with_dates(
            michael_scores.values, michael_dates, threshold, above=False, date_format=date_format)
        sarah_streak, sarah_start, sarah_end = calculate_streak_with_dates(
            sarah_scores.values, sarah_dates, threshold, above=False, date_format=date_format)
        
        if threshold % 1000 == 0:
            label = f"Below {threshold//1000}k"
        else:
            label = f"Below {threshold/1000:.1f}k"
        
        michael_dates_str = format_streak_dates(michael_streak, michael_start, michael_end)
        sarah_dates_str = format_streak_dates(sarah_streak, sarah_start, sarah_end)
        
        rows.append(create_table_row(label, str(michael_streak), str(sarah_streak),
                                     michael_dates_str.replace('<br/>', ' '),
                                     sarah_dates_str.replace('<br/>', ' '),
                                     date_format))
    
    # Cumulative average streaks
    michael_mean = michael_scores.mean()
    sarah_mean = sarah_scores.mean()
    
    michael_streak_above_avg, michael_above_start, michael_above_end = calculate_cumulative_avg_streak(
        michael_scores, michael_dates, above=True, date_format=date_format)
    sarah_streak_above_avg, sarah_above_start, sarah_above_end = calculate_cumulative_avg_streak(
        sarah_scores, sarah_dates, above=True, date_format=date_format)
    
    michael_above_dates = format_streak_dates(michael_streak_above_avg, michael_above_start, michael_above_end)
    sarah_above_dates = format_streak_dates(sarah_streak_above_avg, sarah_above_start, sarah_above_end)
    
    rows.append(create_table_row("Above Cumulative Average", str(michael_streak_above_avg), str(sarah_streak_above_avg),
                                 michael_above_dates.replace('<br/>', ' '),
                                 sarah_above_dates.replace('<br/>', ' '),
                                 date_format))
    
    michael_streak_below_avg, michael_below_start, michael_below_end = calculate_streak_with_dates(
        michael_scores.values, michael_dates, michael_mean, above=False, date_format=date_format)
    sarah_streak_below_avg, sarah_below_start, sarah_below_end = calculate_streak_with_dates(
        sarah_scores.values, sarah_dates, sarah_mean, above=False, date_format=date_format)
    
    michael_below_dates = format_streak_dates(michael_streak_below_avg, michael_below_start, michael_below_end)
    sarah_below_dates = format_streak_dates(sarah_streak_below_avg, sarah_below_start, sarah_below_end)
    
    rows.append(create_table_row("Below Cumulative Average", str(michael_streak_below_avg), str(sarah_streak_below_avg),
                                 michael_below_dates.replace('<br/>', ' '),
                                 sarah_below_dates.replace('<br/>', ' '),
                                 date_format))
    
    # Volatile and stable streaks
    michael_change_streak, michael_change_start, michael_change_end = calculate_score_change_streak(
        michael_scores.values, michael_dates, threshold=change_threshold, mode="change", date_format=date_format)
    sarah_change_streak, sarah_change_start, sarah_change_end = calculate_score_change_streak(
        sarah_scores.values, sarah_dates, threshold=change_threshold, mode="change", date_format=date_format)
    
    michael_change_dates = format_streak_dates(michael_change_streak, michael_change_start, michael_change_end)
    sarah_change_dates = format_streak_dates(sarah_change_streak, sarah_change_start, sarah_change_end)
    
    rows.append(create_table_row(f"Volatile (&gt;{change_threshold} change per day)", str(michael_change_streak), str(sarah_change_streak),
                                 michael_change_dates.replace('<br/>', ' '),
                                 sarah_change_dates.replace('<br/>', ' '),
                                 date_format))
    
    michael_stable_streak, michael_stable_start, michael_stable_end = calculate_score_change_streak(
        michael_scores.values, michael_dates, threshold=change_threshold, mode="stable", date_format=date_format)
    sarah_stable_streak, sarah_stable_start, sarah_stable_end = calculate_score_change_streak(
        sarah_scores.values, sarah_dates, threshold=change_threshold, mode="stable", date_format=date_format)
    
    michael_stable_dates = format_streak_dates(michael_stable_streak, michael_stable_start, michael_stable_end)
    sarah_stable_dates = format_streak_dates(sarah_stable_streak, sarah_stable_start, sarah_stable_end)
    
    rows.append(create_table_row(f"Stable (&lt;{change_threshold} change per day)", str(michael_stable_streak), str(sarah_stable_streak),
                                 michael_stable_dates.replace('<br/>', ' '),
                                 sarah_stable_dates.replace('<br/>', ' '),
                                 date_format,
                                 border=False))
    
    return f"""
    <table class="streaks-table" style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;">
        <thead>
            <tr style="background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;">
                <th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Streak Type</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['michael']}; font-weight: 600;">Michael</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['sarah']}; font-weight: 600;">Sarah</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['michael']}; font-weight: 600;">Date</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['sarah']}; font-weight: 600;">Date</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """

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
    if not mask_filtered.empty and mask_filtered['Date'].min() <= score_tracking_date <= mask_filtered['Date'].max():
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
    if not mask_filtered.empty and mask_filtered['Date'].min() <= survey_date <= mask_filtered['Date'].max():
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
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Score: %{y}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=x_values, y=mask_filtered[sarah_col],
        mode='markers', name=f'Sarah {score_type.title()} Score',
        marker=dict(color=COLORS['sarah_light'], size=8),
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Score: %{y}<extra></extra>'
    ))

    # Rolling average lines
    fig.add_trace(go.Scatter(
        x=x_values, y=mask_filtered["Michael Rolling Avg"],
        mode='lines', name=f'Michael {window_length}-game Avg',
        line=dict(color=COLORS['michael'], width=2.5),
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Rolling Avg: %{y:.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=x_values, y=mask_filtered["Sarah Rolling Avg"],
        mode='lines', name=f'Sarah {window_length}-game Avg',
        line=dict(color=COLORS['sarah'], width=2.5),
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Rolling Avg: %{y:.0f}<extra></extra>'
    ))

    # Cumulative average lines
    fig.add_trace(go.Scatter(
        x=x_values, y=mask_filtered["Michael Cumulative Avg"],
        mode='lines', name='Michael Cumulative Avg',
        line=dict(color=COLORS['michael'], width=1.5, dash='dot'),
        opacity=0.7,
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Cumulative Avg: %{y:.0f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=x_values, y=mask_filtered["Sarah Cumulative Avg"],
        mode='lines', name='Sarah Cumulative Avg',
        line=dict(color=COLORS['sarah'], width=1.5, dash='dot'),
        opacity=0.7,
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Cumulative Avg: %{y:.0f}<extra></extra>'
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

def create_momentum_html(data: pd.DataFrame, window_length: int, score_type: str, ceiling: int) -> str:
    """Paired vertical bar chart per game showing Michael vs Sarah scores."""

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

    n_days = window_length * 4
    recent_data = data.tail(n_days).reset_index(drop=True)
    if len(recent_data) == 0:
        return ""

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
        date_str = row['Date'].strftime('%b %d')

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
    m_weight = "800" if m_total >= s_total else "400"
    s_weight = "800" if s_total > m_total else "400"

    return f"""
<div style="font-family:'Poppins',sans-serif;margin-top:20px;padding:15px;background-color:{COLORS['bg_paper']};border-radius:12px;border:1px solid {COLORS['bg_plot']};">
<div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:10px;">
<h4 style="margin:0;color:{COLORS['text']};font-size:16px;text-transform:uppercase;letter-spacing:1px;">
Momentum <span style="font-size:12px;text-transform:none;opacity:0.8;">(Last {n_days} Games)</span>
</h4>
<div style="font-size:12px;font-weight:600;">
<span style="color:{COLORS['michael']};font-weight:{m_weight};">Michael: {m_total:,.0f}</span>
<span style="color:#b0afaa;margin:0 6px;">|</span>
<span style="color:{COLORS['sarah']};font-weight:{s_weight};">Sarah: {s_total:,.0f}</span>
</div>
</div>
<div style="width:100%;height:48px;border-radius:6px;overflow:hidden;display:flex;background-color:transparent;">
{"".join(segments)}
</div>
<div style="display:flex;justify-content:space-between;margin-top:4px;color:{COLORS['line']};font-size:10px;">
<span>{recent_data.iloc[0]['Date'].strftime('%b %d')}</span><span>{recent_data.iloc[-1]['Date'].strftime('%b %d')}</span>
</div>
</div>"""

def create_density_plot(michael_scores: pd.Series, sarah_scores: pd.Series, avg_scores: pd.Series, ceiling: int) -> go.Figure:
    """Create density plot figure without discrete buckets."""
    fig = go.Figure()
    
    # Check if we have any data
    if len(michael_scores) == 0 and len(sarah_scores) == 0:
        return fig
        
    # Calculate x-axis range
    min_score = min(michael_scores.min() if len(michael_scores) > 0 else ceiling, 
                    sarah_scores.min() if len(sarah_scores) > 0 else ceiling,
                    avg_scores.min() if len(avg_scores) > 0 else ceiling)
    
    # Set bounds, allowing some breathing room below the minimum score
    x_min = max(0, min_score - (ceiling * 0.05))
    x_max = ceiling
    x_vals = np.linspace(x_min, x_max, 500)
    
    def hex_to_rgba(hex_color, alpha=0.4):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'rgba({r},{g},{b},{alpha})'
        
    if len(michael_scores) > 1:
        try:
            kde_m = stats.gaussian_kde(michael_scores)
            y_m = kde_m(x_vals)
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_m,
                name='Michael',
                mode='lines',
                line=dict(color=COLORS['michael'], width=3),
                fill='tozeroy',
                fillcolor=hex_to_rgba(COLORS['michael'], 0.4),
                hovertemplate='Score: %{x:.0f}<br>Density: %{y:.6f}<extra></extra>'
            ))
        except Exception:
            pass # Catch instances of zero variance (LinAlgError)
            
    if len(sarah_scores) > 1:
        try:
            kde_s = stats.gaussian_kde(sarah_scores)
            y_s = kde_s(x_vals)
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_s,
                name='Sarah',
                mode='lines',
                line=dict(color=COLORS['sarah'], width=3),
                fill='tozeroy',
                fillcolor=hex_to_rgba(COLORS['sarah'], 0.4),
                hovertemplate='Score: %{x:.0f}<br>Density: %{y:.6f}<extra></extra>'
            ))
        except Exception:
            pass
            
    if len(avg_scores) > 1:
        try:
            kde_a = stats.gaussian_kde(avg_scores)
            y_a = kde_a(x_vals)
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_a,
                name='Average',
                mode='lines',
                line=dict(color='black', width=2, dash='dash'),
                fill='tozeroy',
                fillcolor=hex_to_rgba('#000000', 0.1),
                hovertemplate='Score: %{x:.0f}<br>Density: %{y:.6f}<extra></extra>'
            ))
            
            # Add percentile lines based on the average scores
            percentiles = [20, 40, 60, 80, 90]
            plotted_vals = set()
            avg_clean = avg_scores.dropna()
            
            for p in percentiles:
                exact_val = np.percentile(avg_clean, p)
                rounded_val = round(exact_val / 500) * 500
                
                # Prevent duplicate lines if multiple targets snap to the same 500 interval
                if rounded_val not in plotted_vals:
                    plotted_vals.add(rounded_val)
                    
                    # Calculate what the true percentile is for this rounded score
                    actual_p = stats.percentileofscore(avg_clean, rounded_val)
                    
                    fig.add_vline(
                        x=rounded_val,
                        line_width=1,
                        line_dash="dot",
                        line_color="#8f8d85",
                        opacity=0.7,
                        annotation_text=f"{actual_p:.1f}th ({int(rounded_val):,})",
                        annotation_position="top right",
                        annotation_textangle=-90,
                        annotation_font=dict(size=10, color="#696761")
                    )
        except Exception:
            pass
    
    fig.update_layout(
        xaxis_title='Score',
        yaxis_title='Density',
        height=400,
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
        range=[x_min, x_max]
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
        rangemode='tozero',
        showticklabels=False # Absolute density values are relative and not strictly necessary
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
        hovertemplate="Date: %{customdata|%Y-%m-%d}<br>Score Diff: %{y}<extra></extra>"
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
        customdata=mask_filtered["Date"], hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Cumulative Avg: %{y:.1f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=mask_filtered["Rolling Diff Pos"], mode="lines",
        name=f"{window_length}-Game Rolling Avg", line=dict(color=COLORS['michael'], width=2.5),
        opacity=0.8, showlegend=False, customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Rolling Avg: %{y:.1f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=mask_filtered["Rolling Diff Neg"], mode="lines",
        name=f"{window_length}-Game Rolling Avg", line=dict(color=COLORS['sarah'], width=2.5),
        opacity=0.8, showlegend=False, customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Rolling Avg: %{y:.1f}<extra></extra>'
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
        if not midnight_df.empty and midnight_df['Date'].min() <= vline_date <= midnight_df['Date'].max():
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


def create_momentum_timeline(data: pd.DataFrame, window_length: int) -> str:
    """Bar strip for the last (window_length * 4) games showing Michael vs Sarah margins."""
    n_games = window_length * 4
    recent_data = data.tail(n_games).reset_index(drop=True)
    if len(recent_data) == 0:
        return ""

    diffs = recent_data['Score Diff'].fillna(0)
    max_abs = diffs.abs().max() or 1
    MIN_HEIGHT_PCT = 10
    slot_pct = 100 / len(recent_data)
    segments = []

    for _, row in recent_data.iterrows():
        diff = row['Score Diff']
        date_str = row['Date'].strftime('%b %d')
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

    m_wins = (diffs > 0).sum()
    s_wins = (diffs < 0).sum()
    return f"""
<div style="font-family:'Poppins',sans-serif;margin-top:20px;padding:15px;background-color:{COLORS['bg_paper']};border-radius:12px;border:1px solid {COLORS['bg_plot']};">
<div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:10px;">
<h4 style="margin:0;color:{COLORS['text']};font-size:16px;text-transform:uppercase;letter-spacing:1px;">
Momentum <span style="font-size:12px;text-transform:none;opacity:0.8;">(Last {n_games} Games)</span>
</h4>
<div style="font-size:12px;font-weight:600;">
<span style="color:{COLORS['michael']};">Michael: {m_wins}</span>
<span style="color:#b0afaa;margin:0 6px;">|</span>
<span style="color:{COLORS['sarah']};">Sarah: {s_wins}</span>
</div>
</div>
<div style="width:100%;height:48px;border-radius:6px;overflow:hidden;display:flex;background-color:transparent;">
{"".join(segments)}
</div>
<div style="display:flex;justify-content:space-between;margin-top:4px;color:{COLORS['line']};font-size:10px;">
<span>{recent_data.iloc[0]['Date'].strftime('%b %d')}</span><span>{recent_data.iloc[-1]['Date'].strftime('%b %d')}</span>
</div>
</div>"""


def get_win_stats_margin(df: pd.DataFrame, lower: float, upper: float, is_michael: bool = True) -> Tuple[int, str]:
    """Calculate win counts and most recent date for a margin category."""
    if is_michael:
        cond = (df["Score Diff"] > lower) & (df["Score Diff"] <= upper)
    else:
        cond = (df["Score Diff"] < -lower) & (df["Score Diff"] >= -upper)
    subset = df[cond]
    count = len(subset)
    recent = subset["Date"].max().strftime("%Y-%m-%d") if not subset.empty else "-"
    return count, recent


def calculate_win_streaks(df: pd.DataFrame) -> List[Dict]:
    """Calculate win streaks for Michael and Sarah."""
    streaks = []
    current_streak = 0
    current_winner = None
    streak_start = None

    for idx, row in df.iterrows():
        if row["Score Diff"] > 0:
            winner = "Michael"
        elif row["Score Diff"] < 0:
            winner = "Sarah"
        else:
            continue
        if winner == current_winner:
            current_streak += 1
        else:
            if current_winner is not None and current_streak > 0:
                streaks.append({'winner': current_winner, 'length': current_streak,
                                'start_date': streak_start, 'end_date': df.iloc[idx-1]["Date"]})
            current_winner = winner
            current_streak = 1
            streak_start = row["Date"]

    if current_winner is not None and current_streak > 0:
        streaks.append({'winner': current_winner, 'length': current_streak,
                        'start_date': streak_start, 'end_date': df.iloc[-1]["Date"]})
    return streaks


def create_win_summary_table(mask_filtered: pd.DataFrame, win_categories: Dict) -> str:
    """Create win summary HTML table (Michael vs Sarah)."""
    michael_wins = mask_filtered[mask_filtered["Score Diff"] > 0]
    sarah_wins = mask_filtered[mask_filtered["Score Diff"] < 0]

    m_win_count = len(michael_wins)
    s_win_count = len(sarah_wins)
    m_recent = michael_wins["Date"].max().strftime("%Y-%m-%d") if not michael_wins.empty else "-"
    s_recent = sarah_wins["Date"].max().strftime("%Y-%m-%d") if not sarah_wins.empty else "-"

    rows = (f'<tr style="border-bottom: 1px solid #d9d7cc;">'
            f'<td style="padding: 8px; color: #696761;">Wins</td>'
            f'<td style="padding: 8px; text-align: center; color: {COLORS["michael"]};">{m_win_count}</td>'
            f'<td style="padding: 8px; text-align: center; color: {COLORS["michael"]}; font-size: 11px;">{m_recent}</td>'
            f'<td style="padding: 8px; text-align: center; color: {COLORS["sarah"]};">{s_win_count}</td>'
            f'<td style="padding: 8px; text-align: center; color: {COLORS["sarah"]}; font-size: 11px;">{s_recent}</td></tr>')

    for label, (lower, upper) in win_categories.items():
        m_count, m_date = get_win_stats_margin(michael_wins, lower, upper, True)
        s_count, s_date = get_win_stats_margin(sarah_wins, lower, upper, False)
        rows += (f'<tr style="border-bottom: 1px solid #d9d7cc;">'
                 f'<td style="padding: 8px; color: #696761;">{label}</td>'
                 f'<td style="padding: 8px; text-align: center; color: {COLORS["michael"]};">{m_count}</td>'
                 f'<td style="padding: 8px; text-align: center; color: {COLORS["michael"]}; font-size: 11px;">{m_date}</td>'
                 f'<td style="padding: 8px; text-align: center; color: {COLORS["sarah"]};">{s_count}</td>'
                 f'<td style="padding: 8px; text-align: center; color: {COLORS["sarah"]}; font-size: 11px;">{s_date}</td></tr>')

    m_large = int(michael_wins["Score Diff"].max()) if not michael_wins.empty else "-"
    m_large_date = michael_wins.loc[michael_wins["Score Diff"].idxmax(), "Date"].strftime("%Y-%m-%d") if not michael_wins.empty else "-"
    s_large = int(abs(sarah_wins["Score Diff"].min())) if not sarah_wins.empty else "-"
    s_large_date = sarah_wins.loc[sarah_wins["Score Diff"].idxmin(), "Date"].strftime("%Y-%m-%d") if not sarah_wins.empty else "-"
    m_small = int(michael_wins["Score Diff"].min()) if not michael_wins.empty else "-"
    m_small_date = michael_wins.loc[michael_wins["Score Diff"].idxmin(), "Date"].strftime("%Y-%m-%d") if not michael_wins.empty else "-"
    s_small = int(abs(sarah_wins["Score Diff"].max())) if not sarah_wins.empty else "-"
    s_small_date = sarah_wins.loc[sarah_wins["Score Diff"].idxmax(), "Date"].strftime("%Y-%m-%d") if not sarah_wins.empty else "-"

    for row_label, m_val, m_date, s_val, s_date in [
        ("Largest Win", m_large, m_large_date, s_large, s_large_date),
        ("Smallest Win", m_small, m_small_date, s_small, s_small_date),
    ]:
        rows += (f'<tr style="border-bottom: 1px solid #d9d7cc;">'
                 f'<td style="padding: 8px; color: #696761;">{row_label}</td>'
                 f'<td style="padding: 8px; text-align: center; color: {COLORS["michael"]};">{m_val}</td>'
                 f'<td style="padding: 8px; text-align: center; color: {COLORS["michael"]}; font-size: 11px;">{m_date}</td>'
                 f'<td style="padding: 8px; text-align: center; color: {COLORS["sarah"]};">{s_val}</td>'
                 f'<td style="padding: 8px; text-align: center; color: {COLORS["sarah"]}; font-size: 11px;">{s_date}</td></tr>')

    return (f'<table class="streaks-table" style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;">'
            f'<thead><tr style="background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;">'
            f'<th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Category</th>'
            f'<th style="padding: 10px; text-align: center; color: {COLORS["michael"]}; font-weight: 600;">Michael</th>'
            f'<th style="padding: 10px; text-align: center; color: {COLORS["michael"]}; font-weight: 600;">Date</th>'
            f'<th style="padding: 10px; text-align: center; color: {COLORS["sarah"]}; font-weight: 600;">Sarah</th>'
            f'<th style="padding: 10px; text-align: center; color: {COLORS["sarah"]}; font-weight: 600;">Date</th>'
            f'</tr></thead><tbody>{rows}</tbody></table>')


def create_win_streaks_table(mask_filtered: pd.DataFrame) -> str:
    """Create win streaks HTML table (Michael vs Sarah)."""
    streaks = calculate_win_streaks(mask_filtered)
    michael_streaks = [s for s in streaks if s['winner'] == 'Michael']
    sarah_streaks = [s for s in streaks if s['winner'] == 'Sarah']

    m_longest = max(michael_streaks, key=lambda x: x['length']) if michael_streaks else None
    s_longest = max(sarah_streaks, key=lambda x: x['length']) if sarah_streaks else None

    m_longest_len = m_longest['length'] if m_longest else "-"
    m_longest_date = f"{m_longest['start_date'].strftime('%Y-%m-%d')} to {m_longest['end_date'].strftime('%Y-%m-%d')}" if m_longest else "-"
    s_longest_len = s_longest['length'] if s_longest else "-"
    s_longest_date = f"{s_longest['start_date'].strftime('%Y-%m-%d')} to {s_longest['end_date'].strftime('%Y-%m-%d')}" if s_longest else "-"

    current = streaks[-1] if streaks else None
    m_current = current['length'] if current and current['winner'] == 'Michael' else 0
    m_current_date = current['start_date'].strftime('%Y-%m-%d') if current and current['winner'] == 'Michael' else "-"
    s_current = current['length'] if current and current['winner'] == 'Sarah' else 0
    s_current_date = current['start_date'].strftime('%Y-%m-%d') if current and current['winner'] == 'Sarah' else "-"

    streak_rows = ""
    max_streak = max([s['length'] for s in streaks]) if streaks else 0
    for streak_len in range(max_streak, 0, -1):
        m_subs = [s for s in michael_streaks if s['length'] >= streak_len]
        s_subs = [s for s in sarah_streaks if s['length'] >= streak_len]
        m_recent = max([s['end_date'] for s in m_subs]).strftime('%Y-%m-%d') if m_subs else "-"
        s_recent = max([s['end_date'] for s in s_subs]).strftime('%Y-%m-%d') if s_subs else "-"
        streak_rows += (f'<tr style="border-bottom: 1px solid #d9d7cc;">'
                        f'<td style="padding: 8px; color: #696761;">Streaks ≥ {streak_len}</td>'
                        f'<td style="padding: 8px; text-align: center; color: {COLORS["michael"]};">{len(m_subs)}</td>'
                        f'<td style="padding: 8px; text-align: center; color: {COLORS["michael"]}; font-size: 11px;">{m_recent}</td>'
                        f'<td style="padding: 8px; text-align: center; color: {COLORS["sarah"]};">{len(s_subs)}</td>'
                        f'<td style="padding: 8px; text-align: center; color: {COLORS["sarah"]}; font-size: 11px;">{s_recent}</td></tr>')

    return (f'<table class="streaks-table" style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;">'
            f'<thead><tr style="background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;">'
            f'<th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Streak Type</th>'
            f'<th style="padding: 10px; text-align: center; color: {COLORS["michael"]}; font-weight: 600;">Michael</th>'
            f'<th style="padding: 10px; text-align: center; color: {COLORS["michael"]}; font-weight: 600;">Date(s)</th>'
            f'<th style="padding: 10px; text-align: center; color: {COLORS["sarah"]}; font-weight: 600;">Sarah</th>'
            f'<th style="padding: 10px; text-align: center; color: {COLORS["sarah"]}; font-weight: 600;">Date(s)</th>'
            f'</tr></thead><tbody>'
            f'<tr style="border-bottom: 1px solid #d9d7cc;"><td style="padding: 8px; color: #696761;">Current Streak</td>'
            f'<td style="padding: 8px; text-align: center; color: {COLORS["michael"]};">{m_current}</td>'
            f'<td style="padding: 8px; text-align: center; color: {COLORS["michael"]}; font-size: 11px;">{m_current_date}</td>'
            f'<td style="padding: 8px; text-align: center; color: {COLORS["sarah"]};">{s_current}</td>'
            f'<td style="padding: 8px; text-align: center; color: {COLORS["sarah"]}; font-size: 11px;">{s_current_date}</td></tr>'
            f'<tr style="border-bottom: 1px solid #d9d7cc;"><td style="padding: 8px; color: #696761;">Longest Streak</td>'
            f'<td style="padding: 8px; text-align: center; color: {COLORS["michael"]};">{m_longest_len}</td>'
            f'<td style="padding: 8px; text-align: center; color: {COLORS["michael"]}; font-size: 11px;">{m_longest_date}</td>'
            f'<td style="padding: 8px; text-align: center; color: {COLORS["sarah"]};">{s_longest_len}</td>'
            f'<td style="padding: 8px; text-align: center; color: {COLORS["sarah"]}; font-size: 11px;">{s_longest_date}</td></tr>'
            f'{streak_rows}</tbody></table>')


# --- Main App ---

# Load data
stats_mtime = os.path.getmtime("./Data/Timeguessr_Stats.csv") if os.path.exists("./Data/Timeguessr_Stats.csv") else 0
data = load_data(mtime=stats_mtime)

# Render Sidebar Controls (Top)
with st.sidebar:
    st.header("Settings")

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

    if view_mode == "Scores":
        include_single_player_days = st.toggle("Include single-player days", value=False, key="include_single_player_toggle")
    else:
        include_single_player_days = False

    remove_pre_tracking = st.toggle("Remove Pre-Tracking Scores", value=False, key="remove_pre_tracking_toggle")
    remove_pre_survey = st.toggle("Remove Pre-Survey Scores", value=False, key="remove_pre_survey_toggle")

# Prepare data based on page type
if page_type == "Total Scores":
    df_daily, mask = prepare_total_scores_data(data, include_single_player_days)
    ceiling = CEILING_TOTAL
    score_type = "total"
    default_bin_size = 5000
    bin_options = [1000, 2500, 5000, 10000]
    change_threshold = 5000
    win_categories = {
        "Massive Wins (>10k)": (10000, np.inf),
        "Big Wins (5–10k)": (5000, 10000),
        "Small Wins (2.5–5k)": (2500, 5000),
        "Close Wins (1–2.5k)": (1000, 2500),
        "Very Close Wins (<1k)": (0, 1000)
    }
elif page_type == "Time Scores":
    df_daily, mask = prepare_time_scores_data(data, False, include_single_player_days)
    ceiling = CEILING_TIME
    score_type = "time"
    default_bin_size = 2500
    bin_options = [500, 1250, 2500, 5000]
    change_threshold = 2500
    win_categories = {
        "Massive Wins (>5k)": (5000, np.inf),
        "Big Wins (2.5–5k)": (2500, 5000),
        "Small Wins (1.25–2.5k)": (1250, 2500),
        "Close Wins (0.5–1.25k)": (500, 1250),
        "Very Close Wins (<0.5k)": (0, 500)
    }
else:  # Geography Scores
    df_daily, mask = prepare_geography_scores_data(data, False, include_single_player_days)
    ceiling = CEILING_GEOGRAPHY
    score_type = "geography"
    default_bin_size = 2500
    bin_options = [500, 1250, 2500, 5000]
    change_threshold = 2500
    win_categories = {
        "Massive Wins (>5k)": (5000, np.inf),
        "Big Wins (2.5–5k)": (2500, 5000),
        "Small Wins (1.25–2.5k)": (1250, 2500),
        "Close Wins (0.5–1.25k)": (500, 1250),
        "Very Close Wins (<0.5k)": (0, 500)
    }

# Apply pre-tracking / pre-survey filters
if remove_pre_tracking:
    mask = mask[mask['Date'] >= pd.Timestamp('2025-10-20')].copy()
    df_daily = df_daily[df_daily['Date'] >= pd.Timestamp('2025-10-20')].copy()
if remove_pre_survey:
    mask = mask[mask['Date'] >= pd.Timestamp('2026-05-18')].copy()
    df_daily = df_daily[df_daily['Date'] >= pd.Timestamp('2026-05-18')].copy()

# Date range logic
if not mask.empty:
    min_date, max_date = mask["Date"].min(), mask["Date"].max()
else:
    min_date, max_date = data["Date"].min(), data["Date"].max()

# Render remaining Sidebar Controls (Bottom)
with st.sidebar:
    window_length = st.slider(
        "Rolling Average Window (Games):",
        min_value=1, max_value=30, value=5, step=1
    )

    start_date, end_date = st.slider(
        "Select Date Range:",
        min_value=min_date.to_pydatetime(),
        max_value=max_date.to_pydatetime(),
        value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
        format="YYYY-MM-DD"
    )

    if view_mode == "Scores":
        bin_size = st.select_slider(
            "Select Score Bucket Size",
            options=bin_options,
            value=default_bin_size,
            help="Adjust the size of score ranges in the statistics table"
        )

# Render main area Header
view_label = page_type if view_mode == "Scores" else page_type.replace("Scores", "Win Margins")
st.markdown(f"## {view_label}")

# Filter data by date range
mask_filtered = mask[(mask["Date"] >= start_date) & (mask["Date"] <= end_date)].copy()
df_daily_filtered = df_daily[(df_daily["Date"] >= start_date) & (df_daily["Date"] <= end_date)].copy()

if view_mode == "Scores":
    # --- Scores View ---
    mask_filtered = calculate_rolling_averages(mask_filtered, window_length, score_type)

    fig = create_plotly_figure(df_daily_filtered, mask_filtered, window_length, score_type,
                               show_single_player_days=include_single_player_days)
    st.plotly_chart(fig, use_container_width=True, key="main_chart")

    momentum_html = create_momentum_html(mask_filtered, window_length, score_type, ceiling)
    st.markdown(momentum_html, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Statistics Summary")

    if score_type == "total":
        michael_scores = mask_filtered["Michael Total Score"].dropna()
        sarah_scores = mask_filtered["Sarah Total Score"].dropna()
        avg_scores = ((mask_filtered["Michael Total Score"] + mask_filtered["Sarah Total Score"]) / 2).dropna()
        michael_dates = mask_filtered[mask_filtered["Michael Total Score"].notna()]["Date"]
        sarah_dates = mask_filtered[mask_filtered["Sarah Total Score"].notna()]["Date"]
    elif score_type == "time":
        michael_scores = mask_filtered["Michael Time Midpoint"].dropna()
        sarah_scores = mask_filtered["Sarah Time Midpoint"].dropna()
        avg_scores = ((mask_filtered["Michael Time Midpoint"] + mask_filtered["Sarah Time Midpoint"]) / 2).dropna()
        michael_dates = mask_filtered[mask_filtered["Michael Time Midpoint"].notna()]["Date"]
        sarah_dates = mask_filtered[mask_filtered["Sarah Time Midpoint"].notna()]["Date"]
    else:
        michael_scores = mask_filtered["Michael Geography Midpoint"].dropna()
        sarah_scores = mask_filtered["Sarah Geography Midpoint"].dropna()
        avg_scores = ((mask_filtered["Michael Geography Midpoint"] + mask_filtered["Sarah Geography Midpoint"]) / 2).dropna()
        michael_dates = mask_filtered[mask_filtered["Michael Geography Midpoint"].notna()]["Date"]
        sarah_dates = mask_filtered[mask_filtered["Sarah Geography Midpoint"].notna()]["Date"]

    use_md_format = can_use_month_day_format(michael_dates) and can_use_month_day_format(sarah_dates)
    date_format = "%b %d" if use_md_format else "%Y-%m-%d"

    col1, col2 = st.columns(2)

    with col1:
        stats_html = create_stats_table_html(michael_scores, sarah_scores,
                                             michael_dates, sarah_dates,
                                             bin_size, date_format, ceiling)
        st.markdown(stats_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        density_fig = create_density_plot(michael_scores, sarah_scores, avg_scores, ceiling)
        st.plotly_chart(density_fig, use_container_width=True, key="density_chart")

    with col2:
        streaks_html = create_streaks_table_html(michael_scores, sarah_scores,
                                                 michael_dates, sarah_dates,
                                                 bin_size, date_format, ceiling,
                                                 change_threshold)
        st.markdown(streaks_html, unsafe_allow_html=True)

else:
    # --- Win Margins View ---
    if score_type == "total":
        margin_mask = mask_filtered[
            mask_filtered["Michael Total Score"].notna() & mask_filtered["Sarah Total Score"].notna()
        ].copy()
        margin_mask["Score Diff"] = margin_mask["Michael Total Score"] - margin_mask["Sarah Total Score"]
    elif score_type == "time":
        margin_mask = mask_filtered[
            mask_filtered["Michael Time Midpoint"].notna() & mask_filtered["Sarah Time Midpoint"].notna()
        ].copy()
        margin_mask["Score Diff"] = margin_mask["Michael Time Midpoint"] - margin_mask["Sarah Time Midpoint"]
    else:
        margin_mask = mask_filtered[
            mask_filtered["Michael Geography Midpoint"].notna() & mask_filtered["Sarah Geography Midpoint"].notna()
        ].copy()
        margin_mask["Score Diff"] = margin_mask["Michael Geography Midpoint"] - margin_mask["Sarah Geography Midpoint"]

    margin_mask["Rolling Diff"] = margin_mask["Score Diff"].rolling(window=window_length, min_periods=1).mean()
    margin_mask["Cumulative Diff"] = margin_mask["Score Diff"].expanding().mean()
    margin_mask = add_zero_crossing_interpolation(margin_mask, window_length)

    fig = create_win_margins_figure(margin_mask, window_length)
    st.plotly_chart(fig, use_container_width=True, key="win_margins_chart")

    margin_original = margin_mask[margin_mask["Date"].dt.time == pd.Timestamp("00:00:00").time()].copy()
    margin_original = margin_original.reset_index(drop=True)
    st.markdown(create_momentum_timeline(margin_original, window_length), unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Win Summary")
        st.markdown(create_win_summary_table(margin_original, win_categories), unsafe_allow_html=True)

    with col2:
        st.markdown("### Streaks")
        st.markdown(create_win_streaks_table(margin_original), unsafe_allow_html=True)