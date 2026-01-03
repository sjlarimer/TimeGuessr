import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
from typing import Tuple, List, Dict

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
        /* Reduce vertical gap between charts */
        .stPlotlyChart {
            margin-bottom: -1rem;
        }
        .block-container {
            padding-bottom: 2rem;
        }
        /* Compact Radio Buttons */
        div[role="radiogroup"] {
            gap: 0.5rem !important; /* Reduce gap between options */
        }
        div[role="radiogroup"] label {
            padding-right: 0.5rem !important; /* Reduce internal padding */
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
    
    # Handle "Combined" player by creating synthetic columns
    if player == "Combined":
        for metric in ["Time", "Geography"]:
            for bound in ["Min", "Max"]:
                # Sum Michael and Sarah's scores
                data[f"Combined {metric} Score ({bound})"] = (
                    data[f"Michael {metric} Score ({bound})"] + 
                    data[f"Sarah {metric} Score ({bound})"]
                )

    # Filter out estimated scores if toggle is on
    if remove_estimated:
        time_min_col = f"{player} Time Score (Min)"
        time_max_col = f"{player} Time Score (Max)"
        geo_min_col = f"{player} Geography Score (Min)"
        geo_max_col = f"{player} Geography Score (Max)"
        
        estimated_time_mask = data[time_min_col] != data[time_max_col]
        data.loc[estimated_time_mask, [time_min_col, time_max_col]] = np.nan
        
        estimated_geo_mask = data[geo_min_col] != data[geo_max_col]
        data.loc[estimated_geo_mask, [geo_min_col, geo_max_col]] = np.nan
    
    # Explicitly drop rows where the player (or combined entity) has no data
    subset_cols = [
        f"{player} Time Score (Min)", f"{player} Time Score (Max)",
        f"{player} Geography Score (Min)", f"{player} Geography Score (Max)"
    ]
    data = data.dropna(subset=subset_cols, how='all')

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

# --- Shared Table Helpers ---

def get_date_bold_style(date1: str, date2: str, date_format: str) -> Tuple[str, str]:
    """Return bold style for more recent date."""
    if date1 == '-' or date2 == '-':
        return ("", "")
    
    try:
        # Extract end date from range if necessary (e.g. "2023-01-01 to 2023-01-05")
        date1_end = date1.split(' to ')[-1].strip()
        date2_end = date2.split(' to ')[-1].strip()
        
        # Handle cases where <br/> might have been replaced with space
        date1_end = date1_end.split(' ')[-1]
        date2_end = date2_end.split(' ')[-1]
        
        d1 = pd.to_datetime(date1_end, format=date_format)
        d2 = pd.to_datetime(date2_end, format=date_format)
        
        if d1 > d2:
            return "font-weight: bold;", ""
        elif d2 > d1:
            return "", "font-weight: bold;"
    except:
        pass
    return "", ""

def create_table_row(label: str, time_val: str, geo_val: str, 
                    time_date: str, geo_date: str, date_format: str,
                    border: bool = True, compare_values: bool = True,
                    center_label: bool = False, highlight_max: bool = True) -> str:
    """Create HTML table row with proper styling and bolding logic."""
    border_style = "border-bottom: 1px solid #d9d7cc;" if border else ""
    label_align = "center" if center_label else "left"
    
    time_bold = ""
    geo_bold = ""
    if compare_values and time_val != '-' and geo_val != '-':
        try:
            t_val = float(str(time_val).replace(',',''))
            g_val = float(str(geo_val).replace(',',''))
            
            if highlight_max:
                time_bold = "font-weight: bold;" if t_val > g_val else ""
                geo_bold = "font-weight: bold;" if g_val > t_val else ""
            else:
                # Highlight smaller value
                time_bold = "font-weight: bold;" if t_val < g_val else ""
                geo_bold = "font-weight: bold;" if g_val < t_val else ""
        except:
            pass
    
    time_date_bold, geo_date_bold = get_date_bold_style(time_date, geo_date, date_format)
    
    return f"""<tr style="{border_style}">
        <td style="padding: 8px; text-align: {label_align}; color: #696761;">{label}</td>
        <td style="padding: 8px; text-align: center; color: {COLORS['time']}; {time_bold}">{time_val}</td>
        <td style="padding: 8px; text-align: center; color: {COLORS['geography']}; {geo_bold}">{geo_val}</td>
        <td style="padding: 8px; text-align: center; color: {COLORS['time']}; font-size: 11px; {time_date_bold}">{time_date}</td>
        <td style="padding: 8px; text-align: center; color: {COLORS['geography']}; font-size: 11px; {geo_date_bold}">{geo_date}</td>
    </tr>"""

# --- Win Margin Logic ---

def get_win_stats(df: pd.DataFrame, lower: float, upper: float, is_time: bool = True) -> Tuple[int, str]:
    """Calculate win counts and most recent date for a margin category."""
    if is_time:
        cond = (df["Score Diff"] > lower) & (df["Score Diff"] <= upper)
    else:
        cond = (df["Score Diff"] < -lower) & (df["Score Diff"] >= -upper)
    
    subset = df[cond]
    count = len(subset)
    recent = subset["Date"].max().strftime("%Y-%m-%d") if not subset.empty else "-"
    return count, recent

def create_win_summary_table(mask_filtered: pd.DataFrame, win_categories: Dict) -> str:
    """Create win summary HTML table for Time vs Geography using standard row creator."""
    time_wins = mask_filtered[mask_filtered["Score Diff"] > 0]
    geo_wins = mask_filtered[mask_filtered["Score Diff"] < 0]
    ties = mask_filtered[mask_filtered["Score Diff"] == 0]
    
    rows = []
    
    # Total Wins
    t_total = len(time_wins)
    g_total = len(geo_wins)
    t_recent = time_wins["Date"].max().strftime("%Y-%m-%d") if not time_wins.empty else "-"
    g_recent = geo_wins["Date"].max().strftime("%Y-%m-%d") if not geo_wins.empty else "-"
    
    rows.append(create_table_row("Total Wins", str(t_total), str(g_total), t_recent, g_recent, "%Y-%m-%d"))
    
    # Ties Row (Custom manual row because of colspan)
    tie_count = len(ties)
    tie_recent = ties["Date"].max().strftime("%Y-%m-%d") if not ties.empty else "-"
    rows.append(f"""<tr style="border-bottom: 1px solid #d9d7cc;"><td style="padding: 8px; color: #696761;">Ties</td><td colspan="4" style="padding: 8px; text-align: center; color: #696761;">{tie_count} (Last: {tie_recent})</td></tr>""")
    
    # Categories
    for label, (lower, upper) in win_categories.items():
        t_count, t_date = get_win_stats(time_wins, lower, upper, True)
        g_count, g_date = get_win_stats(geo_wins, lower, upper, False)
        rows.append(create_table_row(label, str(t_count), str(g_count), t_date, g_date, "%Y-%m-%d"))
    
    # Largest/Smallest
    t_large = int(time_wins["Score Diff"].max()) if not time_wins.empty else "-"
    t_large_date = time_wins.loc[time_wins["Score Diff"].idxmax(), "Date"].strftime("%Y-%m-%d") if not time_wins.empty else "-"
    g_large = int(abs(geo_wins["Score Diff"].min())) if not geo_wins.empty else "-"
    g_large_date = geo_wins.loc[geo_wins["Score Diff"].idxmin(), "Date"].strftime("%Y-%m-%d") if not geo_wins.empty else "-"
    
    rows.append(create_table_row("Largest Win", str(t_large), str(g_large), t_large_date, g_large_date, "%Y-%m-%d"))
    
    t_small = int(time_wins["Score Diff"].min()) if not time_wins.empty else "-"
    t_small_date = time_wins.loc[time_wins["Score Diff"].idxmin(), "Date"].strftime("%Y-%m-%d") if not time_wins.empty else "-"
    g_small = int(abs(geo_wins["Score Diff"].max())) if not geo_wins.empty else "-"
    g_small_date = geo_wins.loc[geo_wins["Score Diff"].idxmax(), "Date"].strftime("%Y-%m-%d") if not geo_wins.empty else "-"
    
    # Highlight smallest win (highlight_max=False)
    rows.append(create_table_row("Smallest Win", str(t_small), str(g_small), t_small_date, g_small_date, "%Y-%m-%d", highlight_max=False))
    
    return f"""<table class="streaks-table" style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;"><thead><tr style="background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;"><th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Category</th><th style="padding: 10px; text-align: center; color: {COLORS['time']}; font-weight: 600;">Time</th><th style="padding: 10px; text-align: center; color: {COLORS['geography']}; font-weight: 600;">Geography</th><th style="padding: 10px; text-align: center; color: {COLORS['time']}; font-weight: 600;">Date</th><th style="padding: 10px; text-align: center; color: {COLORS['geography']}; font-weight: 600;">Date</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"""

# --- Score Stats Logic ---

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

def generate_buckets(time_scores: pd.Series, geo_scores: pd.Series, 
                    dates: pd.Series, bin_size: int, date_format: str, ceiling: int) -> List[Dict]:
    """Generate score buckets with counts and dates."""
    buckets = []
    current_upper = ceiling

    while current_upper > 0:
        current_lower = max(current_upper - bin_size, 0)
        
        if current_upper == ceiling:
            time_mask = time_scores >= current_lower
            geo_mask = geo_scores >= current_lower
        else:
            time_mask = (time_scores >= current_lower) & (time_scores < current_upper)
            geo_mask = (geo_scores >= current_lower) & (geo_scores < current_upper)
        
        time_count = time_mask.sum()
        geo_count = geo_mask.sum()
        
        if time_count > 0 or geo_count > 0:
            time_date = dates[time_mask].max().strftime(date_format) if time_count > 0 else '-'
            geo_date = dates[geo_mask].max().strftime(date_format) if geo_count > 0 else '-'
            
            label = format_bucket_label(current_lower, current_upper, bin_size, current_upper == ceiling)
            
            buckets.append({
                'label': label,
                'time_count': time_count,
                'time_date': time_date,
                'geo_count': geo_count,
                'geo_date': geo_date
            })
        
        current_upper = current_lower
        if current_lower == 0:
            break

    return buckets

def calculate_streak_with_dates(scores: np.ndarray, dates: pd.Series, 
                                threshold: float, above: bool = True, 
                                date_format: str = "%Y-%m-%d") -> Tuple[int, str, str]:
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

            if current_streak >= max_streak:
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
                                   date_format: str = "%Y-%m-%d") -> Tuple[int, str, str]:
    """Calculate longest streak relative to cumulative average."""
    if len(scores) == 0:
        return 0, "", ""
    
    # Calculate cumulative average up to each point
    cum_avg = scores.expanding().mean()
    
    max_streak = 0
    current_streak = 0
    max_start_idx = 0
    max_end_idx = 0
    current_start_idx = 0

    # Convert to numpy for iteration
    scores_arr = scores.values
    cum_avg_arr = cum_avg.values

    for i in range(len(scores_arr)):
        condition = (above and scores_arr[i] >= cum_avg_arr[i]) or (not above and scores_arr[i] < cum_avg_arr[i])
        
        if condition:
            if current_streak == 0:
                current_start_idx = i
            current_streak += 1

            if current_streak >= max_streak:
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
                                  date_format: str = "%Y-%m-%d") -> Tuple[int, str, str]:
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
        condition = (mode == "change" and diff >= threshold) or (mode == "stable" and diff < threshold)

        if condition:
            if current_streak == 0:
                current_start_idx = i 
            current_streak += 1

            if current_streak >= max_streak:
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

def format_streak_dates(streak_count: int, start_date: str, end_date: str) -> str:
    """Format streak dates for display."""
    if streak_count == 0:
        return '-'
    return start_date if start_date == end_date else f"{start_date}<br/>to {end_date}"

def generate_streak_thresholds(bin_size: int, ceiling: int) -> List[int]:
    """Generate fixed streak thresholds based on bin size and ceiling."""
    # Generate strict list: ceiling, ceiling-bin, ..., bin_size
    return list(range(ceiling, 0, -bin_size))

def create_scores_stats_table(time_scores: pd.Series, geo_scores: pd.Series, dates: pd.Series, bin_size: int, ceiling: int, date_format: str = "%Y-%m-%d") -> str:
    """Create summary statistics table for Scores tab."""
    if len(time_scores) == 0:
        return "<p>No data available.</p>"
    
    t_mean = time_scores.mean()
    g_mean = geo_scores.mean()
    t_std = time_scores.std()
    g_std = geo_scores.std()
    t_median = time_scores.median()
    g_median = geo_scores.median()
    t_max = time_scores.max()
    g_max = geo_scores.max()
    t_min = time_scores.min()
    g_min = geo_scores.min()
    
    t_med_date = dates.iloc[(time_scores - t_median).abs().argmin()].strftime(date_format)
    g_med_date = dates.iloc[(geo_scores - g_median).abs().argmin()].strftime(date_format)
    t_max_date = dates.iloc[time_scores.argmax()].strftime(date_format)
    g_max_date = dates.iloc[geo_scores.argmax()].strftime(date_format)
    t_min_date = dates.iloc[time_scores.argmin()].strftime(date_format)
    g_min_date = dates.iloc[geo_scores.argmin()].strftime(date_format)
    
    rows = []
    rows.append(create_table_row("Mean", f"{t_mean:.0f}", f"{g_mean:.0f}", "-", "-", date_format))
    rows.append(create_table_row("Std Dev", f"{t_std:.0f}", f"{g_std:.0f}", "-", "-", date_format))
    rows.append(create_table_row("Median", f"{t_median:.0f}", f"{g_median:.0f}", t_med_date, g_med_date, date_format))
    rows.append(create_table_row("Max", f"{t_max:.0f}", f"{g_max:.0f}", t_max_date, g_max_date, date_format))
    rows.append(create_table_row("Min", f"{t_min:.0f}", f"{g_min:.0f}", t_min_date, g_min_date, date_format))
    
    # Buckets
    buckets = generate_buckets(time_scores, geo_scores, dates, bin_size, date_format, ceiling)
    for i, bucket in enumerate(buckets):
        is_last = i == len(buckets) - 1
        rows.append(create_table_row(
            bucket['label'],
            str(bucket['time_count']),
            str(bucket['geo_count']),
            bucket['time_date'],
            bucket['geo_date'],
            date_format,
            border=not is_last
        ))
    
    return f"""
    <table class="stats-table" style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;">
        <thead>
            <tr style="background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;">
                <th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Statistic</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['time']}; font-weight: 600;">Time</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['geography']}; font-weight: 600;">Geography</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['time']}; font-weight: 600;">Date</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['geography']}; font-weight: 600;">Date</th>
            </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
    """

def create_scores_streaks_table(time_scores: pd.Series, geo_scores: pd.Series, dates: pd.Series, bin_size: int, ceiling: int, date_format: str = "%Y-%m-%d", change_threshold: int = 5000) -> str:
    """Create streaks table for Scores tab."""
    streak_thresholds = generate_streak_thresholds(bin_size, ceiling)
    rows = []
    
    # Above Thresholds
    for threshold in streak_thresholds:
        # Check if ALL data fits the streak (trivial)
        if (time_scores >= threshold).all() and (geo_scores >= threshold).all():
            continue

        t_streak, t_start, t_end = calculate_streak_with_dates(time_scores.values, dates, threshold, above=True, date_format=date_format)
        g_streak, g_start, g_end = calculate_streak_with_dates(geo_scores.values, dates, threshold, above=True, date_format=date_format)
        
        # Only show row if at least one player has a streak
        if t_streak == 0 and g_streak == 0:
            continue

        label = format_bucket_label(threshold, threshold + bin_size, bin_size).replace("Scores ", "Above ")
        if threshold % 1000 == 0:
            label = f"Above {threshold//1000}k"
        else:
            label = f"Above {threshold/1000:.1f}k"
            
        t_dates_str = format_streak_dates(t_streak, t_start, t_end)
        g_dates_str = format_streak_dates(g_streak, g_start, g_end)
        
        rows.append(create_table_row(label, str(t_streak), str(g_streak), 
                                   t_dates_str.replace('<br/>', ' '), 
                                   g_dates_str.replace('<br/>', ' '), 
                                   date_format))
    
    # Below Thresholds - Include all thresholds, but iterate low to high (reversed)
    for threshold in reversed(streak_thresholds):
        # Check if ALL data fits the streak (trivial)
        if (time_scores < threshold).all() and (geo_scores < threshold).all():
            continue

        t_streak, t_start, t_end = calculate_streak_with_dates(time_scores.values, dates, threshold, above=False, date_format=date_format)
        g_streak, g_start, g_end = calculate_streak_with_dates(geo_scores.values, dates, threshold, above=False, date_format=date_format)
        
        # Only show row if streak exists
        if t_streak == 0 and g_streak == 0:
            continue

        if threshold % 1000 == 0:
            label = f"Below {threshold//1000}k"
        else:
            label = f"Below {threshold/1000:.1f}k"
            
        t_dates_str = format_streak_dates(t_streak, t_start, t_end)
        g_dates_str = format_streak_dates(g_streak, g_start, g_end)
        
        rows.append(create_table_row(label, str(t_streak), str(g_streak), 
                                   t_dates_str.replace('<br/>', ' '), 
                                   g_dates_str.replace('<br/>', ' '), 
                                   date_format))
    
    # --- Cumulative Average Streaks ---
    t_streak_above, t_start_above, t_end_above = calculate_cumulative_avg_streak(time_scores, dates, above=True, date_format=date_format)
    g_streak_above, g_start_above, g_end_above = calculate_cumulative_avg_streak(geo_scores, dates, above=True, date_format=date_format)
    
    rows.append(create_table_row("Above Cumulative Avg", str(t_streak_above), str(g_streak_above), 
                               format_streak_dates(t_streak_above, t_start_above, t_end_above).replace('<br/>', ' '), 
                               format_streak_dates(g_streak_above, g_start_above, g_end_above).replace('<br/>', ' '), 
                               date_format))

    t_streak_below, t_start_below, t_end_below = calculate_cumulative_avg_streak(time_scores, dates, above=False, date_format=date_format)
    g_streak_below, g_start_below, g_end_below = calculate_cumulative_avg_streak(geo_scores, dates, above=False, date_format=date_format)
    
    rows.append(create_table_row("Below Cumulative Avg", str(t_streak_below), str(g_streak_below), 
                               format_streak_dates(t_streak_below, t_start_below, t_end_below).replace('<br/>', ' '), 
                               format_streak_dates(g_streak_below, g_start_below, g_end_below).replace('<br/>', ' '), 
                               date_format))

    # --- Volatility Streaks ---
    # Determine label string
    val_str = f"{change_threshold//1000}k" if change_threshold % 1000 == 0 else f"{change_threshold/1000}k"
    
    t_streak_vol, t_start_vol, t_end_vol = calculate_score_change_streak(time_scores.values, dates, change_threshold, mode="change", date_format=date_format)
    g_streak_vol, g_start_vol, g_end_vol = calculate_score_change_streak(geo_scores.values, dates, change_threshold, mode="change", date_format=date_format)
    
    rows.append(create_table_row(f"Volatile (>{val_str} change)", str(t_streak_vol), str(g_streak_vol), 
                               format_streak_dates(t_streak_vol, t_start_vol, t_end_vol).replace('<br/>', ' '), 
                               format_streak_dates(g_streak_vol, g_start_vol, g_end_vol).replace('<br/>', ' '), 
                               date_format))

    t_streak_stab, t_start_stab, t_end_stab = calculate_score_change_streak(time_scores.values, dates, change_threshold, mode="stable", date_format=date_format)
    g_streak_stab, g_start_stab, g_end_stab = calculate_score_change_streak(geo_scores.values, dates, change_threshold, mode="stable", date_format=date_format)
    
    rows.append(create_table_row(f"Stable (<{val_str} change)", str(t_streak_stab), str(g_streak_stab), 
                               format_streak_dates(t_streak_stab, t_start_stab, t_end_stab).replace('<br/>', ' '), 
                               format_streak_dates(g_streak_stab, g_start_stab, g_end_stab).replace('<br/>', ' '), 
                               date_format))

    return f"""
    <table class="streaks-table" style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;">
        <thead>
            <tr style="background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;">
                <th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Streak Type</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['time']}; font-weight: 600;">Time</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['geography']}; font-weight: 600;">Geography</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['time']}; font-weight: 600;">Date(s)</th>
                <th style="padding: 10px; text-align: center; color: {COLORS['geography']}; font-weight: 600;">Date(s)</th>
            </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
    """

def create_histogram(time_scores: pd.Series, geo_scores: pd.Series, bin_size: int, ceiling: int) -> go.Figure:
    """Create histogram figure for Time vs Geography."""
    hist_fig = go.Figure()
    
    if len(time_scores) == 0 and len(geo_scores) == 0:
        return hist_fig
    
    min_score = min(time_scores.min() if len(time_scores) > 0 else ceiling, 
                   geo_scores.min() if len(geo_scores) > 0 else ceiling)
    bins_needed = int(np.ceil((ceiling - min_score) / bin_size))
    tick_start = ceiling - (bins_needed * bin_size)
    
    if len(time_scores) > 0:
        hist_fig.add_trace(go.Histogram(
            x=time_scores,
            name='Time',
            marker_color=COLORS['time'],
            opacity=0.7,
            xbins=dict(size=bin_size, start=tick_start, end=ceiling)
        ))
    
    if len(geo_scores) > 0:
        hist_fig.add_trace(go.Histogram(
            x=geo_scores,
            name='Geography',
            marker_color=COLORS['geography'],
            opacity=0.7,
            xbins=dict(size=bin_size, start=tick_start, end=ceiling)
        ))
    
    tick_values = list(range(tick_start, ceiling + 1, bin_size))
    
    hist_fig.update_layout(
        barmode='overlay',
        xaxis_title='Score',
        yaxis_title='Count',
        height=400,
        font=dict(family='Poppins, Arial, sans-serif', size=12, color='#000000'),
        paper_bgcolor=COLORS['bg_paper'],
        plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=40, t=40, b=60),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
            bgcolor='rgba(0,0,0,0)', bordercolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text'])
        ),
    )
    
    hist_fig.update_xaxes(
        showgrid=True, gridcolor=COLORS['grid'],
        zeroline=False, linecolor=COLORS['line'],
        tickcolor=COLORS['line'], tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text']),
        tickmode='array', tickvals=tick_values
    )
    hist_fig.update_yaxes(
        showgrid=True, gridcolor=COLORS['grid'],
        zeroline=False, linecolor=COLORS['line'],
        tickcolor=COLORS['line'], tickfont=dict(color=COLORS['text']),
        title_font=dict(color=COLORS['text'])
    )
    
    return hist_fig

def create_plotly_figure(df: pd.DataFrame, window_length: int, player: str) -> go.Figure:
    """Create the main Plotly figure showing time vs geography."""
    fig = go.Figure()
    
    time_col = f"{player} Time Midpoint"
    geo_col = f"{player} Geography Midpoint"
    
    x_values = list(range(len(df)))
    
    df_copy = df.copy()
    df_copy['month_year'] = df_copy['Date'].dt.to_period('M')
    first_of_month_indices = df_copy.groupby('month_year').head(1).index.tolist()
    
    tickvals = [i for i, idx in enumerate(df.index) if idx in first_of_month_indices]
    ticktext = [df.iloc[i]['Date'].strftime('%b %Y') for i in tickvals]

    # Scatter plots
    fig.add_trace(go.Scatter(
        x=x_values, y=df[time_col], mode='markers', name='Time Score',
        marker=dict(color=COLORS['time_light'], size=8),
        customdata=df["Date"], hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Time Score: %{y}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=x_values, y=df[geo_col], mode='markers', name='Geography Score',
        marker=dict(color=COLORS['geography_light'], size=8),
        customdata=df["Date"], hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Geography Score: %{y}<extra></extra>'
    ))

    # Rolling average lines
    fig.add_trace(go.Scatter(
        x=x_values, y=df[f"{player} Time Rolling Avg"], mode='lines', name=f'Time {window_length}-game Avg',
        line=dict(color=COLORS['time'], width=2.5),
        customdata=df["Date"], hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Time Rolling Avg: %{y:.0f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=x_values, y=df[f"{player} Geography Rolling Avg"], mode='lines', name=f'Geography {window_length}-game Avg',
        line=dict(color=COLORS['geography'], width=2.5),
        customdata=df["Date"], hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Geography Rolling Avg: %{y:.0f}<extra></extra>'
    ))

    # Cumulative average lines
    fig.add_trace(go.Scatter(
        x=x_values, y=df[f"{player} Time Cumulative Avg"], mode='lines', name='Time Cumulative Avg',
        line=dict(color=COLORS['time'], width=1.5, dash='dot'), opacity=0.7,
        customdata=df["Date"], hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Time Cumulative Avg: %{y:.0f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=x_values, y=df[f"{player} Geography Cumulative Avg"], mode='lines', name='Geography Cumulative Avg',
        line=dict(color=COLORS['geography'], width=1.5, dash='dot'), opacity=0.7,
        customdata=df["Date"], hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Geography Cumulative Avg: %{y:.0f}<extra></extra>'
    ))

    # Layout
    fig.update_layout(
        xaxis_title='Date', yaxis_title='Score',
        width=1400, height=600, hovermode='closest',
        font=FONT_CONFIG, paper_bgcolor=COLORS['bg_paper'], plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=40, t=60, b=40),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                    bgcolor='rgba(0,0,0,0)', bordercolor='rgba(0,0,0,0)', font=dict(color=COLORS['text'])),
    )

    axis_config = dict(showgrid=True, gridcolor=COLORS['grid'], zeroline=False, linecolor=COLORS['line'],
                       tickcolor=COLORS['line'], tickfont=dict(color=COLORS['text']), title_font=dict(color=COLORS['text']))
    
    fig.update_xaxes(**axis_config, tickmode='array', tickvals=tickvals, ticktext=ticktext, tickangle=-45)
    fig.update_yaxes(**axis_config)

    return fig

def create_win_margins_figure(mask_filtered: pd.DataFrame, window_length: int, player: str) -> go.Figure:
    """Create the win margins Plotly figure for Time vs Geography."""
    fig = go.Figure()
    
    mask_filtered = mask_filtered.copy()
    mask_filtered["x_index"] = np.arange(len(mask_filtered))
    
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=mask_filtered["Score Diff"], mode="markers",
        marker=dict(color="gray", opacity=0.4, size=7),
        name="Game Result (Time − Geography)", customdata=mask_filtered["Date"],
        hovertemplate="Date: %{customdata|%Y-%m-%d}<br>Score Diff: %{y}<extra></extra>"
    ))
    
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=np.where(mask_filtered["Score Diff"] > 0, mask_filtered["Score Diff"], 0),
        fill='tozeroy', mode='none', fillcolor='rgba(152, 223, 138, 0.6)', name='Time Wins'
    ))
    
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=np.where(mask_filtered["Score Diff"] < 0, mask_filtered["Score Diff"], 0),
        fill='tozeroy', mode='none', fillcolor='rgba(255, 187, 120, 0.6)', name='Geography Wins'
    ))
    
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=mask_filtered["Cumulative Diff"], mode="lines",
        name="Cumulative Avg", line=dict(color="black", width=1.5, dash="dot"), opacity=0.7,
        customdata=mask_filtered["Date"], hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Cumulative Avg: %{y:.1f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=mask_filtered["Rolling Diff Pos"], mode="lines",
        name=f"{window_length}-Game Rolling Avg", line=dict(color=COLORS['time'], width=2.5), opacity=0.8, showlegend=False,
        customdata=mask_filtered["Date"], hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Rolling Avg: %{y:.1f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"], y=mask_filtered["Rolling Diff Neg"], mode="lines",
        name=f"{window_length}-Game Rolling Avg", line=dict(color=COLORS['geography'], width=2.5), opacity=0.8, showlegend=False,
        customdata=mask_filtered["Date"], hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Rolling Avg: %{y:.1f}<extra></extra>'
    ))
    
    y_max = max(
        abs(mask_filtered["Score Diff"].max()), abs(mask_filtered["Score Diff"].min()),
        abs(mask_filtered["Rolling Diff"].max()), abs(mask_filtered["Rolling Diff"].min()),
        abs(mask_filtered["Cumulative Diff"].max()), abs(mask_filtered["Cumulative Diff"].min())
    )
    y_max = np.ceil(y_max / 5000) * 5000
    tick_vals = np.arange(-y_max, y_max + 1, 5000)
    tick_text = [str(abs(int(t))) for t in tick_vals]
    
    fig.add_hline(y=0, line=dict(color="#8f8d85", dash="dash", width=1))
    
    df_copy = mask_filtered.copy()
    df_copy['month_year'] = df_copy['Date'].dt.to_period('M')
    first_of_month_indices = df_copy.groupby('month_year').head(1).index.tolist()
    
    tickvals = [mask_filtered.loc[idx, "x_index"] for idx in first_of_month_indices]
    ticktext = [mask_filtered.loc[idx, 'Date'].strftime('%b %Y') for idx in first_of_month_indices]
    
    fig.update_layout(
        xaxis_title="Date", yaxis_title="Score Difference (Time − Geography)",
        width=1400, height=600, hovermode="closest",
        font=FONT_CONFIG, paper_bgcolor=COLORS['bg_paper'], plot_bgcolor=COLORS['bg_plot'],
        margin=dict(l=60, r=40, t=60, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)", font=dict(color=COLORS['text'])),
    )
    
    fig.update_xaxes(showgrid=True, gridcolor=COLORS['grid'], zeroline=False, linecolor=COLORS['line'],
                     tickcolor=COLORS['line'], tickfont=dict(color=COLORS['text']), title_font=dict(color=COLORS['text']),
                     tickmode='array', tickvals=tickvals, ticktext=ticktext, tickangle=-45)
    
    fig.update_yaxes(showgrid=True, gridcolor=COLORS['grid'], zeroline=False, linecolor=COLORS['line'],
                     tickcolor=COLORS['line'], tickfont=dict(color=COLORS['text']), title_font=dict(color=COLORS['text']),
                     tickvals=tick_vals, ticktext=tick_text, range=[-y_max, y_max])
    
    return fig

def add_zero_crossing_interpolation(mask_filtered: pd.DataFrame, window_length: int) -> pd.DataFrame:
    """Add interpolated zero-crossing points for smooth line transitions."""
    mask_filtered = mask_filtered.reset_index(drop=True)
    y = mask_filtered["Rolling Diff"]
    dates = mask_filtered["Date"]
    new_points = []
    
    crossings_mask = np.sign(y.shift(1) * y).fillna(1) < 0
    crossing_indices = mask_filtered[crossings_mask].index.tolist()
    
    for i in crossing_indices:
        if i == 0: continue
        y1 = y.iloc[i-1]; x1 = dates.iloc[i-1]
        y2 = y.iloc[i]; x2 = dates.iloc[i]
        cum1 = mask_filtered["Cumulative Diff"].iloc[i-1]; cum2 = mask_filtered["Cumulative Diff"].iloc[i]
        score1 = mask_filtered["Score Diff"].iloc[i-1]; score2 = mask_filtered["Score Diff"].iloc[i]
        
        date_diff_seconds = (x2 - x1).total_seconds()
        
        if y2 - y1 != 0:
            fraction = (0 - y1) / (y2 - y1)
            time_at_zero_seconds = date_diff_seconds * fraction
            x_zero = x1 + pd.Timedelta(time_at_zero_seconds, unit='s')
            cum_zero = cum1 + fraction * (cum2 - cum1)
            score_zero = score1 + fraction * (score2 - score1)
            new_points.append({"Date": x_zero, "Rolling Diff": 0.0, "Score Diff": score_zero, "Cumulative Diff": cum_zero})
    
    if new_points:
        df_new_points = pd.DataFrame(new_points)
        mask_filtered = pd.concat([mask_filtered, df_new_points], ignore_index=True)
        mask_filtered = mask_filtered.sort_values(by="Date").reset_index(drop=True)
    
    mask_filtered['Rolling Diff Pos'] = np.where(mask_filtered['Rolling Diff'] >= 0, mask_filtered['Rolling Diff'], np.nan)
    mask_filtered['Rolling Diff Neg'] = np.where(mask_filtered['Rolling Diff'] <= 0, mask_filtered['Rolling Diff'], np.nan)
    
    return mask_filtered

# --- Main App ---

data = load_data()

with st.sidebar:
    st.header("Dashboard Settings")
    view_mode = st.radio("View Mode:", options=["Scores", "Win Margins"], horizontal=True, index=0, key="view_mode_toggle")
    player = st.radio("Select Player:", options=["Combined", "Michael", "Sarah"], horizontal=True, index=0, key="player_selector")
    remove_estimated = st.toggle("Remove Estimated Scores", value=False, key="remove_estimated_toggle")
    window_length = st.slider("Rolling Average Window", min_value=1, max_value=30, value=5, step=1)

    player_data = prepare_player_data(data, player, remove_estimated)

    if not player_data.empty:
        min_date, max_date = player_data["Date"].min(), player_data["Date"].max()
        start_date, end_date = st.slider("Select Date Range:", min_value=min_date.to_pydatetime(), max_value=max_date.to_pydatetime(), value=(min_date.to_pydatetime(), max_date.to_pydatetime()), format="YYYY-MM-DD")
    else:
        st.warning("No data available for selected options.")
        st.stop()

# --- Logic Processing ---

player_data_filtered = player_data[(player_data["Date"] >= start_date) & (player_data["Date"] <= end_date)].copy()
player_data_filtered = calculate_rolling_averages(player_data_filtered, window_length, player)

if view_mode == "Scores":
    st.subheader("Time vs Geography Scores")
    fig = create_plotly_figure(player_data_filtered, window_length, player)
    st.plotly_chart(fig, use_container_width=True, key="main_chart")
    
    st.divider()
    
    time_col = f"{player} Time Midpoint"
    geo_col = f"{player} Geography Midpoint"
    
    # Determine bucket settings
    if player == "Combined":
        streak_ceiling = 50000
        streak_bin = 5000
        change_threshold = 5000
    else:
        streak_ceiling = 25000
        streak_bin = 2500
        change_threshold = 2500
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Summary Statistics")
        stats_html = create_scores_stats_table(
            player_data_filtered[time_col], 
            player_data_filtered[geo_col],
            player_data_filtered["Date"],
            bin_size=streak_bin, 
            ceiling=streak_ceiling
        )
        st.markdown(stats_html, unsafe_allow_html=True)
        
        st.subheader("Score Distribution")
        hist_fig = create_histogram(
            player_data_filtered[time_col], 
            player_data_filtered[geo_col],
            bin_size=streak_bin, 
            ceiling=streak_ceiling
        )
        st.plotly_chart(hist_fig, use_container_width=True)
        
    with col2:
        st.subheader("Score Streaks")
        streaks_html = create_scores_streaks_table(
            player_data_filtered[time_col], 
            player_data_filtered[geo_col],
            player_data_filtered["Date"],
            bin_size=streak_bin, 
            ceiling=streak_ceiling,
            change_threshold=change_threshold
        )
        st.markdown(streaks_html, unsafe_allow_html=True)

else:
    margin_data = player_data_filtered.copy()
    margin_data["Score Diff"] = margin_data[f"{player} Time Midpoint"] - margin_data[f"{player} Geography Midpoint"]
    margin_data["Rolling Diff"] = margin_data["Score Diff"].rolling(window=window_length, min_periods=1).mean()
    margin_data["Cumulative Diff"] = margin_data["Score Diff"].expanding().mean()
    margin_data = add_zero_crossing_interpolation(margin_data, window_length)

    st.subheader("Score Differential (Time - Geography)")
    margin_fig = create_win_margins_figure(margin_data, window_length, player)
    st.plotly_chart(margin_fig, use_container_width=True, key="margin_chart")
    
    st.divider()
    
    if player == "Combined":
        win_categories = {
            "Massive Win (>10k)": (10000, 50000),
            "Big Win (5k-10k)": (5000, 10000),
            "Small Win (2.5k-5k)": (2500, 5000),
            "Close Win (1k-2.5k)": (1000, 2500),
            "Very Close Win (<1k)": (0, 1000)
        }
    else:
        win_categories = {
            "Massive Win (>5k)": (5000, 50000),
            "Big Win (2.5k-5k)": (2500, 5000),
            "Small Win (1.25k-2.5k)": (1250, 2500),
            "Close Win (0.5k-1.25k)": (500, 1250),
            "Very Close Win (<0.5k)": (0, 500)
        }
    
    st.subheader("Win Summary")
    win_html = create_win_summary_table(margin_data, win_categories)
    st.markdown(win_html, unsafe_allow_html=True)