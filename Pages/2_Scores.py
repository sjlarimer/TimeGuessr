import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
from typing import Tuple, List, Dict
import time

# --- Configuration ---
st.set_page_config(page_title="Timeguessr Dashboard", layout="wide")

from PIL import Image
img = Image.open("Images/outage.png")
st.image(img, use_container_width=True)

# # --- Constants ---
# COLORS = {
#     'michael': '#221e8f',
#     'michael_light': '#bcb0ff',
#     'sarah': "#8a005c",
#     'sarah_light': "#ff70a7",
#     'bg_paper': '#eae8dc',
#     'bg_plot': '#d9d7cc',
#     'grid': '#bdbbb1',
#     'text': '#696761',
#     'line': '#8f8d85'
# }

# FONT_CONFIG = dict(family='Poppins, Arial, sans-serif', size=14, color='#000000')
# CEILING_TOTAL = 50000
# CEILING_TIME = 25000
# CEILING_GEOGRAPHY = 25000

# # --- Load CSS ---
# css_path = Path("styles.css")
# if css_path.exists():
#     with open(css_path) as f:
#         st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# # --- Custom Styling ---
# CUSTOM_STYLES = """
#     <style>
#         /* Slider labels and tooltips */
#         div[data-testid="stSlider"] > label {
#             color: #696761 !important;
#             font-weight: 600;
#         }
#         div[data-baseweb="slider"] div[data-testid="stTooltipContent"] {
#             color: #696761 !important;
#             background-color: #f2f1ea !important;
#             border: 1px solid #d9d7cc !important;
#             font-weight: 500;
#         }
#         div[data-baseweb="slider"] div[data-testid="stTooltipContent"]::before {
#             background-color: #f2f1ea !important;
#             border: 1px solid #d9d7cc !important;
#         }
        
#         /* Table styling */
#         .stats-table tbody tr, .streaks-table tbody tr {
#             cursor: pointer;
#             transition: background-color 0.2s;
#         }
#         .stats-table tbody tr:hover, .streaks-table tbody tr:hover {
#             background-color: #e0e0d1;
#         }
#         .stats-table tbody tr.selected, .streaks-table tbody tr.selected {
#             background-color: #c0c0b0;
#         }
#     </style>
# """
# st.markdown(CUSTOM_STYLES, unsafe_allow_html=True)

# # --- Helper Functions ---
# @st.cache_data
# def load_data(filepath: str = "./Data/Timeguessr_Stats.csv") -> pd.DataFrame:
#     """Load and preprocess data with caching."""
#     try:
#         data = pd.read_csv(filepath)
#         data["Date"] = pd.to_datetime(data["Date"])
#         data = data.sort_values("Date").reset_index(drop=True)
#         return data
#     except FileNotFoundError:
#         st.error(f"Data file not found at {filepath}")
#         st.stop()
#     except Exception as e:
#         st.error(f"Error loading data: {e}")
#         st.stop()

# def filter_by_score_range(df: pd.DataFrame, score_min: int, score_max: int, score_type: str = "total", include_single: bool = False) -> pd.DataFrame:
#     """Filter dataframe by score range for both players."""
#     df = df.copy()
    
#     if score_type == "total":
#         michael_col = "Michael Total Score"
#         sarah_col = "Sarah Total Score"
#     elif score_type == "time":
#         michael_col = "Michael Time Midpoint"
#         sarah_col = "Sarah Time Midpoint"
#     else:  # geography
#         michael_col = "Michael Geography Midpoint"
#         sarah_col = "Sarah Geography Midpoint"
    
#     if include_single:
#         # Keep rows where at least one player's score is within range
#         # But set out-of-range scores to NaN
#         mask = (
#             ((df[michael_col] >= score_min) & (df[michael_col] <= score_max)) |
#             ((df[sarah_col] >= score_min) & (df[sarah_col] <= score_max))
#         )
        
#         df = df[mask].copy()
        
#         # Set out-of-range scores to NaN
#         df.loc[(df[michael_col] < score_min) | (df[michael_col] > score_max), michael_col] = np.nan
#         df.loc[(df[sarah_col] < score_min) | (df[sarah_col] > score_max), sarah_col] = np.nan
#     else:
#         # Remove entire day if ANY score is outside range
#         # Only keep days where BOTH players have scores AND both are in range
#         mask = (
#             (df[michael_col].notna()) & 
#             (df[sarah_col].notna()) &
#             (df[michael_col] >= score_min) & (df[michael_col] <= score_max) &
#             (df[sarah_col] >= score_min) & (df[sarah_col] <= score_max)
#         )
        
#         df = df[mask].copy()
    
#     return df

# def prepare_total_scores_data(data: pd.DataFrame, include_single: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
#     """Prepare data for Total Scores view."""
#     df_daily = data.groupby("Timeguessr Day").first().reset_index()
    
#     if include_single:
#         # Include all days with at least one score
#         mask = df_daily[
#             df_daily["Michael Total Score"].notna() | df_daily["Sarah Total Score"].notna()
#         ][["Date", "Michael Total Score", "Sarah Total Score"]].copy()
#     else:
#         # Only include days where BOTH players have scores
#         mask = df_daily[
#             df_daily["Michael Total Score"].notna() & df_daily["Sarah Total Score"].notna()
#         ][["Date", "Michael Total Score", "Sarah Total Score"]].copy()
    
#     mask = mask.sort_values("Date").reset_index(drop=True)
#     return df_daily, mask

# def prepare_time_scores_data(data: pd.DataFrame, remove_estimated: bool = False, include_single: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
#     """Prepare data for Time Scores view."""
#     data = data.copy()
    
#     # Filter out estimated scores if toggle is on
#     if remove_estimated:
#         for player in ["Michael", "Sarah"]:
#             min_col = f"{player} Time Score (Min)"
#             max_col = f"{player} Time Score (Max)"
            
#             estimated_dates = data[data[min_col] != data[max_col]]["Date"].unique()
#             data.loc[data["Date"].isin(estimated_dates), [min_col, max_col]] = np.nan
    
#     # Compute midpoints per round
#     for player in ["Michael", "Sarah"]:
#         data[f"{player} Time Midpoint"] = (
#             data[f"{player} Time Score (Min)"] + data[f"{player} Time Score (Max)"]
#         ) / 2
    
#     # Sum midpoints per day
#     daily_cols = ["Michael Time Midpoint", "Sarah Time Midpoint"]
#     df_daily = (
#         data.groupby("Date")[daily_cols]
#         .sum(min_count=1)
#         .reset_index()
#     )
    
#     df_daily = df_daily.sort_values("Date").reset_index(drop=True)
    
#     if include_single:
#         # Include all days with at least one score
#         mask = df_daily[
#             df_daily["Michael Time Midpoint"].notna() | df_daily["Sarah Time Midpoint"].notna()
#         ][["Date", "Michael Time Midpoint", "Sarah Time Midpoint"]].copy()
#     else:
#         # Only include days where BOTH players have data
#         mask = df_daily[
#             df_daily["Michael Time Midpoint"].notna() & df_daily["Sarah Time Midpoint"].notna()
#         ][["Date", "Michael Time Midpoint", "Sarah Time Midpoint"]].copy()
    
#     mask = mask.sort_values("Date").reset_index(drop=True)
#     return df_daily, mask

# def prepare_geography_scores_data(data: pd.DataFrame, remove_estimated: bool = False, include_single: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
#     """Prepare data for Geography Scores view."""
#     data = data.copy()
    
#     # Filter out estimated scores if toggle is on
#     if remove_estimated:
#         for player in ["Michael", "Sarah"]:
#             min_col = f"{player} Geography Score (Min)"
#             max_col = f"{player} Geography Score (Max)"
            
#             estimated_dates = data[data[min_col] != data[max_col]]["Date"].unique()
#             data.loc[data["Date"].isin(estimated_dates), [min_col, max_col]] = np.nan
    
#     # Compute midpoints per round
#     for player in ["Michael", "Sarah"]:
#         data[f"{player} Geography Midpoint"] = (
#             data[f"{player} Geography Score (Min)"] + data[f"{player} Geography Score (Max)"]
#         ) / 2
    
#     # Sum midpoints per day
#     daily_cols = ["Michael Geography Midpoint", "Sarah Geography Midpoint"]
#     df_daily = (
#         data.groupby("Date")[daily_cols]
#         .sum(min_count=1)
#         .reset_index()
#     )
    
#     df_daily = df_daily.sort_values("Date").reset_index(drop=True)
    
#     if include_single:
#         # Include all days with at least one score
#         mask = df_daily[
#             df_daily["Michael Geography Midpoint"].notna() | df_daily["Sarah Geography Midpoint"].notna()
#         ][["Date", "Michael Geography Midpoint", "Sarah Geography Midpoint"]].copy()
#     else:
#         # Only include days where BOTH players have data
#         mask = df_daily[
#             df_daily["Michael Geography Midpoint"].notna() & df_daily["Sarah Geography Midpoint"].notna()
#         ][["Date", "Michael Geography Midpoint", "Sarah Geography Midpoint"]].copy()
    
#     mask = mask.sort_values("Date").reset_index(drop=True)
#     return df_daily, mask

# def get_daily_data(data: pd.DataFrame) -> pd.DataFrame:
#     """Get first row for each Timeguessr Day."""
#     df_daily = data.groupby("Timeguessr Day").first().reset_index()
#     mask = df_daily[["Date", "Michael Total Score", "Sarah Total Score"]].dropna()
#     return mask.sort_values("Date").reset_index(drop=True)

# def calculate_rolling_averages(df: pd.DataFrame, window_length: int, score_type: str = "total") -> pd.DataFrame:
#     """Calculate rolling and cumulative averages."""
#     df = df.copy()
    
#     if score_type == "total":
#         columns = {
#             "Michael": "Michael Total Score",
#             "Sarah": "Sarah Total Score"
#         }
#     elif score_type == "time":
#         columns = {
#             "Michael": "Michael Time Midpoint",
#             "Sarah": "Sarah Time Midpoint"
#         }
#     else:  # geography
#         columns = {
#             "Michael": "Michael Geography Midpoint",
#             "Sarah": "Sarah Geography Midpoint"
#         }
    
#     for player, col in columns.items():
#         if col in df.columns:
#             df[f"{player} Rolling Avg"] = df[col].rolling(window=window_length, min_periods=1).mean()
#             df[f"{player} Cumulative Avg"] = df[col].expanding().mean()
    
#     return df

# def can_use_month_day_format(dates: pd.Series) -> bool:
#     """Check if month-day format is unambiguous."""
#     month_years = dates.dt.to_period("M")
#     month_to_years = {}
#     for period in month_years:
#         month_to_years.setdefault(period.month, set()).add(period.year)
#     return all(len(years) == 1 for years in month_to_years.values())

# def get_date_bold_style(date1: str, date2: str, date_format: str) -> Tuple[str, str]:
#     """Return bold style for more recent date."""
#     if date1 == '-' and date2 == '-':
#         return "", ""
#     if date1 == '-':
#         return "", "font-weight: bold;"
#     if date2 == '-':
#         return "font-weight: bold;", ""
    
#     try:
#         # Extract the end date from ranges (e.g., "Sep 15 to Sep 16" -> "Sep 16")
#         date1_end = date1.split(' to ')[-1].strip()
#         date2_end = date2.split(' to ')[-1].strip()
        
#         d1 = pd.to_datetime(date1_end, format=date_format)
#         d2 = pd.to_datetime(date2_end, format=date_format)
#         if d1 > d2:
#             return "font-weight: bold;", ""
#         elif d2 > d1:
#             return "", "font-weight: bold;"
#     except:
#         pass
#     return "", ""

# def calculate_streak_with_dates(scores: np.ndarray, dates: pd.Series, 
#                                 threshold: float, above: bool = True, 
#                                 date_format: str = "%b %d") -> Tuple[int, str, str]:
#     """Calculate longest streak above/below threshold with date range."""
#     max_streak = 0
#     current_streak = 0
#     max_start_idx = 0
#     max_end_idx = 0
#     current_start_idx = 0

#     for i, score in enumerate(scores):
#         condition = (above and score >= threshold) or (not above and score < threshold)
        
#         if condition:
#             if current_streak == 0:
#                 current_start_idx = i
#             current_streak += 1

#             if current_streak > max_streak or (current_streak == max_streak and i > max_end_idx):
#                 max_streak = current_streak
#                 max_start_idx = current_start_idx
#                 max_end_idx = i
#         else:
#             current_streak = 0

#     if max_streak > 0:
#         start_date = dates.iloc[max_start_idx].strftime(date_format)
#         end_date = dates.iloc[max_end_idx].strftime(date_format)
#         return max_streak, start_date, end_date

#     return 0, "", ""

# def calculate_cumulative_avg_streak(scores: pd.Series, dates: pd.Series, 
#                                    above: bool = True, 
#                                    date_format: str = "%b %d") -> Tuple[int, str, str]:
#     """Calculate longest streak relative to cumulative average."""
#     if len(scores) == 0:
#         return 0, "", ""
    
#     scores_array = scores.values if hasattr(scores, 'values') else scores
#     max_streak = 0
#     current_streak = 0
#     max_start_idx = 0
#     max_end_idx = 0
#     current_start_idx = 0

#     for i in range(len(scores_array)):
#         cumulative_avg = scores_array[:i+1].mean()
#         condition = (above and scores_array[i] >= cumulative_avg) or (not above and scores_array[i] < cumulative_avg)
        
#         if condition:
#             if current_streak == 0:
#                 current_start_idx = i
#             current_streak += 1

#             if current_streak > max_streak or (current_streak == max_streak and i > max_end_idx):
#                 max_streak = current_streak
#                 max_start_idx = current_start_idx
#                 max_end_idx = i
#         else:
#             current_streak = 0

#     if max_streak > 0:
#         start_date = dates.iloc[max_start_idx].strftime(date_format)
#         end_date = dates.iloc[max_end_idx].strftime(date_format)
#         return max_streak, start_date, end_date

#     return 0, "", ""

# def calculate_score_change_streak(scores: np.ndarray, dates: pd.Series, 
#                                   threshold: float, mode: str = "change", 
#                                   date_format: str = "%b %d") -> Tuple[int, str, str]:
#     """Calculate streak based on daily score changes."""
#     if len(scores) < 2:
#         return 0, "", ""

#     max_streak = 0
#     current_streak = 0
#     max_start_idx = 0
#     max_end_idx = 0
#     current_start_idx = 0

#     for i in range(1, len(scores)):
#         diff = abs(scores[i] - scores[i - 1])
#         condition = (mode == "change" and diff >= threshold) or (mode == "stable" and diff <= threshold)

#         if condition:
#             if current_streak == 0:
#                 current_start_idx = i - 1
#             current_streak += 1

#             if current_streak > max_streak or (current_streak == max_streak and i > max_end_idx):
#                 max_streak = current_streak
#                 max_start_idx = current_start_idx
#                 max_end_idx = i
#         else:
#             current_streak = 0

#     if max_streak > 0:
#         start_date = dates.iloc[max_start_idx].strftime(date_format)
#         end_date = dates.iloc[max_end_idx].strftime(date_format)
#         return max_streak, start_date, end_date

#     return 0, "", ""

# def format_bucket_label(lower: int, upper: int, bin_size: int, is_top: bool = False) -> str:
#     """Format bucket label based on range."""
#     if is_top:
#         return f"Scores {lower//1000}k+" if lower % 1000 == 0 else f"Scores {lower/1000:.1f}k+"
#     elif bin_size == 1000:
#         return f"Scores {lower//1000}k" if lower % 1000 == 0 else f"Scores {lower/1000:.1f}k"
#     else:
#         lower_str = f"{lower//1000}k" if lower % 1000 == 0 else f"{lower/1000:.1f}k"
#         upper_str = f"{upper//1000}k" if upper % 1000 == 0 else f"{upper/1000:.1f}k"
#         return f"Scores {lower_str}-{upper_str}"

# def generate_buckets(michael_scores: pd.Series, sarah_scores: pd.Series, 
#                     michael_dates: pd.Series, sarah_dates: pd.Series,
#                     bin_size: int, date_format: str, ceiling: int) -> List[Dict]:
#     """Generate score buckets with counts and dates."""
#     buckets = []
#     current_upper = ceiling

#     while current_upper > 0:
#         current_lower = max(current_upper - bin_size, 0)
        
#         # Calculate masks
#         if current_upper == ceiling:
#             michael_mask = michael_scores >= current_lower
#             sarah_mask = sarah_scores >= current_lower
#         else:
#             michael_mask = (michael_scores >= current_lower) & (michael_scores < current_upper)
#             sarah_mask = (sarah_scores >= current_lower) & (sarah_scores < current_upper)
        
#         michael_count = michael_mask.sum()
#         sarah_count = sarah_mask.sum()
        
#         # Only include bucket if either player has scores in it
#         if michael_count > 0 or sarah_count > 0:
#             michael_date = michael_dates[michael_mask].max().strftime(date_format) if michael_count > 0 else '-'
#             sarah_date = sarah_dates[sarah_mask].max().strftime(date_format) if sarah_count > 0 else '-'
            
#             label = format_bucket_label(current_lower, current_upper, bin_size, current_upper == ceiling)
            
#             buckets.append({
#                 'label': label,
#                 'michael_count': michael_count,
#                 'michael_date': michael_date,
#                 'sarah_count': sarah_count,
#                 'sarah_date': sarah_date
#             })
        
#         current_upper = current_lower
#         if current_lower == 0:
#             break

#     return buckets

# def create_table_row(label: str, michael_val: str, sarah_val: str, 
#                     michael_date: str, sarah_date: str, date_format: str,
#                     border: bool = True, compare_values: bool = True) -> str:
#     """Create HTML table row with proper styling."""
#     border_style = "border-bottom: 1px solid #d9d7cc;" if border else ""
    
#     # Value comparison for bolding
#     michael_bold = ""
#     sarah_bold = ""
#     if compare_values and michael_val != '-' and sarah_val != '-':
#         try:
#             m_val = float(michael_val)
#             s_val = float(sarah_val)
#             michael_bold = "font-weight: bold;" if m_val > s_val else ""
#             sarah_bold = "font-weight: bold;" if s_val > m_val else ""
#         except:
#             pass
    
#     # Date comparison for bolding
#     michael_date_bold, sarah_date_bold = get_date_bold_style(michael_date, sarah_date, date_format)
    
#     return f"""<tr style="{border_style}">
#         <td style="padding: 8px; color: #696761;">{label}</td>
#         <td style="padding: 8px; text-align: center; color: {COLORS['michael']}; {michael_bold}">{michael_val}</td>
#         <td style="padding: 8px; text-align: center; color: {COLORS['sarah']}; {sarah_bold}">{sarah_val}</td>
#         <td style="padding: 8px; text-align: center; color: {COLORS['michael']}; font-size: 11px; {michael_date_bold}">{michael_date}</td>
#         <td style="padding: 8px; text-align: center; color: {COLORS['sarah']}; font-size: 11px; {sarah_date_bold}">{sarah_date}</td>
#     </tr>"""

# def create_stats_table_html(michael_scores: pd.Series, sarah_scores: pd.Series,
#                            michael_dates: pd.Series, sarah_dates: pd.Series,
#                            bin_size: int, date_format: str, ceiling: int) -> str:
#     """Create complete statistics table HTML."""
#     # Check if we have any data
#     if len(michael_scores) == 0 and len(sarah_scores) == 0:
#         return "<p>No data available for the selected date range.</p>"
    
#     # Calculate statistics
#     michael_sum = michael_scores.sum() if len(michael_scores) > 0 else 0
#     sarah_sum = sarah_scores.sum() if len(sarah_scores) > 0 else 0
#     michael_mean = michael_scores.mean() if len(michael_scores) > 0 else 0
#     sarah_mean = sarah_scores.mean() if len(sarah_scores) > 0 else 0
#     michael_std = michael_scores.std() if len(michael_scores) > 0 else 0
#     sarah_std = sarah_scores.std() if len(sarah_scores) > 0 else 0
#     michael_median = michael_scores.median() if len(michael_scores) > 0 else 0
#     sarah_median = sarah_scores.median() if len(sarah_scores) > 0 else 0
#     michael_min = michael_scores.min() if len(michael_scores) > 0 else 0
#     sarah_min = sarah_scores.min() if len(sarah_scores) > 0 else 0
#     michael_max = michael_scores.max() if len(michael_scores) > 0 else 0
#     sarah_max = sarah_scores.max() if len(sarah_scores) > 0 else 0
    
#     # Find dates (with safety checks)
#     michael_median_date = michael_dates.iloc[(michael_scores - michael_median).abs().argmin()].strftime(date_format) if len(michael_scores) > 0 else "-"
#     sarah_median_date = sarah_dates.iloc[(sarah_scores - sarah_median).abs().argmin()].strftime(date_format) if len(sarah_scores) > 0 else "-"
#     michael_min_date = michael_dates.iloc[michael_scores.argmin()].strftime(date_format) if len(michael_scores) > 0 else "-"
#     sarah_min_date = sarah_dates.iloc[sarah_scores.argmin()].strftime(date_format) if len(sarah_scores) > 0 else "-"
#     michael_max_date = michael_dates.iloc[michael_scores.argmax()].strftime(date_format) if len(michael_scores) > 0 else "-"
#     sarah_max_date = sarah_dates.iloc[sarah_scores.argmax()].strftime(date_format) if len(sarah_scores) > 0 else "-"
    
#     # Build rows
#     rows = []
#     rows.append(create_table_row("Sum", f"{int(michael_sum):,}", f"{int(sarah_sum):,}", "-", "-", date_format))
#     rows.append(create_table_row("Mean", f"{michael_mean:.0f}", f"{sarah_mean:.0f}", "-", "-", date_format))
#     rows.append(create_table_row("Standard Deviation", f"{michael_std:.0f}", f"{sarah_std:.0f}", "-", "-", date_format))
#     rows.append(create_table_row("Max", f"{michael_max:.0f}", f"{sarah_max:.0f}", michael_max_date, sarah_max_date, date_format))
#     rows.append(create_table_row("Median", f"{michael_median:.0f}", f"{sarah_median:.0f}", michael_median_date, sarah_median_date, date_format))
#     rows.append(create_table_row("Min", f"{michael_min:.0f}", f"{sarah_min:.0f}", michael_min_date, sarah_min_date, date_format))
    
#     # Add buckets if bin_size >= 2500 (for total scores) or bin_size >= 500 (for time scores)
#     min_bin_threshold = 500 if ceiling <= 25000 else 2500
#     if bin_size >= min_bin_threshold:
#         buckets = generate_buckets(michael_scores, sarah_scores, michael_dates, sarah_dates, bin_size, date_format, ceiling)
#         for i, bucket in enumerate(buckets):
#             is_last = i == len(buckets) - 1
#             rows.append(create_table_row(
#                 bucket['label'],
#                 str(bucket['michael_count']),
#                 str(bucket['sarah_count']),
#                 bucket['michael_date'],
#                 bucket['sarah_date'],
#                 date_format,
#                 border=not is_last
#             ))
    
#     return f"""
#     <table class="stats-table" style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;">
#         <thead>
#             <tr style="background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;">
#                 <th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Statistic</th>
#                 <th style="padding: 10px; text-align: center; color: {COLORS['michael']}; font-weight: 600;">Michael</th>
#                 <th style="padding: 10px; text-align: center; color: {COLORS['sarah']}; font-weight: 600;">Sarah</th>
#                 <th style="padding: 10px; text-align: center; color: {COLORS['michael']}; font-weight: 600;">Date</th>
#                 <th style="padding: 10px; text-align: center; color: {COLORS['sarah']}; font-weight: 600;">Date</th>
#             </tr>
#         </thead>
#         <tbody>
#             {''.join(rows)}
#         </tbody>
#     </table>
#     """

# def format_streak_dates(streak_count: int, start_date: str, end_date: str) -> str:
#     """Format streak dates for display."""
#     if streak_count == 0:
#         return '-'
#     return start_date if start_date == end_date else f"{start_date}<br/>to {end_date}"

# def generate_streak_thresholds(michael_scores: pd.Series, sarah_scores: pd.Series, bin_size: int, ceiling: int) -> List[int]:
#     """Generate streak thresholds based on bin size."""
#     streak_thresholds = []
#     current_upper = ceiling

#     while current_upper > 0:
#         current_lower = max(current_upper - bin_size, 0)
        
#         # Check if there's any data in this range
#         if current_upper == ceiling:
#             michael_has_data = (michael_scores >= current_lower).any()
#             sarah_has_data = (sarah_scores >= current_lower).any()
#         else:
#             michael_has_data = ((michael_scores >= current_lower) & (michael_scores < current_upper)).any()
#             sarah_has_data = ((sarah_scores >= current_lower) & (sarah_scores < current_upper)).any()
        
#         if michael_has_data or sarah_has_data:
#             michael_all_above = (michael_scores >= current_lower).all()
#             michael_all_below = (michael_scores < current_lower).all()
#             sarah_all_above = (sarah_scores >= current_lower).all()
#             sarah_all_below = (sarah_scores < current_lower).all()
            
#             if not ((michael_all_above and sarah_all_above) or (michael_all_below and sarah_all_below)):
#                 streak_thresholds.append(current_lower)
        
#         current_upper = current_lower
#         if current_lower == 0:
#             break

#     return streak_thresholds

# def create_streaks_table_html(michael_scores: pd.Series, sarah_scores: pd.Series,
#                               michael_dates: pd.Series, sarah_dates: pd.Series,
#                               bin_size: int, date_format: str, ceiling: int, 
#                               change_threshold: int = 5000) -> str:
#     """Create complete streaks table HTML."""
#     streak_thresholds = generate_streak_thresholds(michael_scores, sarah_scores, bin_size, ceiling)
    
#     rows = []
    
#     # Above threshold streaks
#     for threshold in streak_thresholds:
#         michael_streak, michael_start, michael_end = calculate_streak_with_dates(
#             michael_scores.values, michael_dates, threshold, above=True, date_format=date_format)
#         sarah_streak, sarah_start, sarah_end = calculate_streak_with_dates(
#             sarah_scores.values, sarah_dates, threshold, above=True, date_format=date_format)
        
#         label = format_bucket_label(threshold, threshold + bin_size, bin_size).replace("Scores ", "Above ")
#         if threshold % 1000 == 0:
#             label = f"Above {threshold//1000}k"
#         else:
#             label = f"Above {threshold/1000:.1f}k"
        
#         michael_dates_str = format_streak_dates(michael_streak, michael_start, michael_end)
#         sarah_dates_str = format_streak_dates(sarah_streak, sarah_start, sarah_end)
        
#         rows.append(create_table_row(label, str(michael_streak), str(sarah_streak), 
#                                      michael_dates_str.replace('<br/>', ' '), 
#                                      sarah_dates_str.replace('<br/>', ' '), 
#                                      date_format))
    
#     # Below threshold streaks
#     for threshold in reversed(streak_thresholds):
#         michael_streak, michael_start, michael_end = calculate_streak_with_dates(
#             michael_scores.values, michael_dates, threshold, above=False, date_format=date_format)
#         sarah_streak, sarah_start, sarah_end = calculate_streak_with_dates(
#             sarah_scores.values, sarah_dates, threshold, above=False, date_format=date_format)
        
#         if threshold % 1000 == 0:
#             label = f"Below {threshold//1000}k"
#         else:
#             label = f"Below {threshold/1000:.1f}k"
        
#         michael_dates_str = format_streak_dates(michael_streak, michael_start, michael_end)
#         sarah_dates_str = format_streak_dates(sarah_streak, sarah_start, sarah_end)
        
#         rows.append(create_table_row(label, str(michael_streak), str(sarah_streak),
#                                      michael_dates_str.replace('<br/>', ' '),
#                                      sarah_dates_str.replace('<br/>', ' '),
#                                      date_format))
    
#     # Cumulative average streaks
#     michael_mean = michael_scores.mean()
#     sarah_mean = sarah_scores.mean()
    
#     michael_streak_above_avg, michael_above_start, michael_above_end = calculate_cumulative_avg_streak(
#         michael_scores, michael_dates, above=True, date_format=date_format)
#     sarah_streak_above_avg, sarah_above_start, sarah_above_end = calculate_cumulative_avg_streak(
#         sarah_scores, sarah_dates, above=True, date_format=date_format)
    
#     michael_above_dates = format_streak_dates(michael_streak_above_avg, michael_above_start, michael_above_end)
#     sarah_above_dates = format_streak_dates(sarah_streak_above_avg, sarah_above_start, sarah_above_end)
    
#     rows.append(create_table_row("Above Cumulative Average", str(michael_streak_above_avg), str(sarah_streak_above_avg),
#                                  michael_above_dates.replace('<br/>', ' '),
#                                  sarah_above_dates.replace('<br/>', ' '),
#                                  date_format))
    
#     michael_streak_below_avg, michael_below_start, michael_below_end = calculate_streak_with_dates(
#         michael_scores.values, michael_dates, michael_mean, above=False, date_format=date_format)
#     sarah_streak_below_avg, sarah_below_start, sarah_below_end = calculate_streak_with_dates(
#         sarah_scores.values, sarah_dates, sarah_mean, above=False, date_format=date_format)
    
#     michael_below_dates = format_streak_dates(michael_streak_below_avg, michael_below_start, michael_below_end)
#     sarah_below_dates = format_streak_dates(sarah_streak_below_avg, sarah_below_start, sarah_below_end)
    
#     rows.append(create_table_row("Below Cumulative Average", str(michael_streak_below_avg), str(sarah_streak_below_avg),
#                                  michael_below_dates.replace('<br/>', ' '),
#                                  sarah_below_dates.replace('<br/>', ' '),
#                                  date_format))
    
#     # Volatile and stable streaks
#     michael_change_streak, michael_change_start, michael_change_end = calculate_score_change_streak(
#         michael_scores.values, michael_dates, threshold=change_threshold, mode="change", date_format=date_format)
#     sarah_change_streak, sarah_change_start, sarah_change_end = calculate_score_change_streak(
#         sarah_scores.values, sarah_dates, threshold=change_threshold, mode="change", date_format=date_format)
    
#     michael_change_dates = format_streak_dates(michael_change_streak, michael_change_start, michael_change_end)
#     sarah_change_dates = format_streak_dates(sarah_change_streak, sarah_change_start, sarah_change_end)
    
#     rows.append(create_table_row(f"Volatile (&gt;{change_threshold} change per day)", str(michael_change_streak), str(sarah_change_streak),
#                                  michael_change_dates.replace('<br/>', ' '),
#                                  sarah_change_dates.replace('<br/>', ' '),
#                                  date_format))
    
#     michael_stable_streak, michael_stable_start, michael_stable_end = calculate_score_change_streak(
#         michael_scores.values, michael_dates, threshold=change_threshold, mode="stable", date_format=date_format)
#     sarah_stable_streak, sarah_stable_start, sarah_stable_end = calculate_score_change_streak(
#         sarah_scores.values, sarah_dates, threshold=change_threshold, mode="stable", date_format=date_format)
    
#     michael_stable_dates = format_streak_dates(michael_stable_streak, michael_stable_start, michael_stable_end)
#     sarah_stable_dates = format_streak_dates(sarah_stable_streak, sarah_stable_start, sarah_stable_end)
    
#     rows.append(create_table_row(f"Stable (&lt;{change_threshold} change per day)", str(michael_stable_streak), str(sarah_stable_streak),
#                                  michael_stable_dates.replace('<br/>', ' '),
#                                  sarah_stable_dates.replace('<br/>', ' '),
#                                  date_format,
#                                  border=False))
    
#     return f"""
#     <table class="streaks-table" style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;">
#         <thead>
#             <tr style="background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;">
#                 <th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Streak Type</th>
#                 <th style="padding: 10px; text-align: center; color: {COLORS['michael']}; font-weight: 600;">Michael</th>
#                 <th style="padding: 10px; text-align: center; color: {COLORS['sarah']}; font-weight: 600;">Sarah</th>
#                 <th style="padding: 10px; text-align: center; color: {COLORS['michael']}; font-weight: 600;">Date</th>
#                 <th style="padding: 10px; text-align: center; color: {COLORS['sarah']}; font-weight: 600;">Date</th>
#             </tr>
#         </thead>
#         <tbody>
#             {''.join(rows)}
#         </tbody>
#     </table>
#     """

# def create_plotly_figure(df_daily: pd.DataFrame, mask_filtered: pd.DataFrame, 
#                         window_length: int, score_type: str = "total",
#                         show_single_player_days: bool = False) -> go.Figure:
#     """Create the main Plotly figure."""
#     fig = go.Figure()
    
#     if score_type == "total":
#         michael_col = "Michael Total Score"
#         sarah_col = "Sarah Total Score"
#     elif score_type == "time":
#         michael_col = "Michael Time Midpoint"
#         sarah_col = "Sarah Time Midpoint"
#     else:  # geography
#         michael_col = "Michael Geography Midpoint"
#         sarah_col = "Sarah Geography Midpoint"

#     # Always use sequential integers for equal spacing
#     x_values = list(range(len(mask_filtered)))
    
#     # Create custom tick positions for first day of each month
#     mask_filtered_copy = mask_filtered.copy()
#     mask_filtered_copy['month_year'] = mask_filtered_copy['Date'].dt.to_period('M')
#     first_of_month_indices = mask_filtered_copy.groupby('month_year').head(1).index.tolist()
    
#     tickvals = [i for i, idx in enumerate(mask_filtered.index) if idx in first_of_month_indices]
#     ticktext = [mask_filtered.iloc[i]['Date'].strftime('%b %Y') for i in tickvals]

#     # Add shaded rectangles for single-player days if toggle is on
#     if show_single_player_days:
#         for i in range(len(mask_filtered)):
#             michael_val = mask_filtered.iloc[i][michael_col]
#             sarah_val = mask_filtered.iloc[i][sarah_col]
            
#             # Check if only one player has data
#             if pd.isna(michael_val) and not pd.isna(sarah_val):
#                 # Only Sarah played - pinkish tint
#                 fig.add_shape(
#                     type="rect",
#                     x0=i - 0.5,
#                     x1=i + 0.5,
#                     y0=0,
#                     y1=1,
#                     yref="paper",
#                     fillcolor="#d4c5cf",  # darker gray with pinkish tint
#                     opacity=0.4,
#                     layer="below",
#                     line_width=0,
#                 )
#             elif pd.isna(sarah_val) and not pd.isna(michael_val):
#                 # Only Michael played - bluish tint
#                 fig.add_shape(
#                     type="rect",
#                     x0=i - 0.5,
#                     x1=i + 0.5,
#                     y0=0,
#                     y1=1,
#                     yref="paper",
#                     fillcolor="#c5c9d4",  # darker gray with bluish tint
#                     opacity=0.4,
#                     layer="below",
#                     line_width=0,
#                 )

#     # Scatter plots
#     fig.add_trace(go.Scatter(
#         x=x_values, y=mask_filtered[michael_col],
#         mode='markers', name=f'Michael {score_type.title()} Score',
#         marker=dict(color=COLORS['michael_light'], size=8),
#         customdata=mask_filtered["Date"],
#         hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Score: %{y}<extra></extra>'
#     ))
    
#     fig.add_trace(go.Scatter(
#         x=x_values, y=mask_filtered[sarah_col],
#         mode='markers', name=f'Sarah {score_type.title()} Score',
#         marker=dict(color=COLORS['sarah_light'], size=8),
#         customdata=mask_filtered["Date"],
#         hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Score: %{y}<extra></extra>'
#     ))

#     # Rolling average lines
#     fig.add_trace(go.Scatter(
#         x=x_values, y=mask_filtered["Michael Rolling Avg"],
#         mode='lines', name=f'Michael {window_length}-game Avg',
#         line=dict(color=COLORS['michael'], width=2.5),
#         customdata=mask_filtered["Date"],
#         hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Rolling Avg: %{y:.0f}<extra></extra>'
#     ))
    
#     fig.add_trace(go.Scatter(
#         x=x_values, y=mask_filtered["Sarah Rolling Avg"],
#         mode='lines', name=f'Sarah {window_length}-game Avg',
#         line=dict(color=COLORS['sarah'], width=2.5),
#         customdata=mask_filtered["Date"],
#         hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Rolling Avg: %{y:.0f}<extra></extra>'
#     ))

#     # Cumulative average lines
#     fig.add_trace(go.Scatter(
#         x=x_values, y=mask_filtered["Michael Cumulative Avg"],
#         mode='lines', name='Michael Cumulative Avg',
#         line=dict(color=COLORS['michael'], width=1.5, dash='dot'),
#         opacity=0.7,
#         customdata=mask_filtered["Date"],
#         hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Cumulative Avg: %{y:.0f}<extra></extra>'
#     ))
    
#     fig.add_trace(go.Scatter(
#         x=x_values, y=mask_filtered["Sarah Cumulative Avg"],
#         mode='lines', name='Sarah Cumulative Avg',
#         line=dict(color=COLORS['sarah'], width=1.5, dash='dot'),
#         opacity=0.7,
#         customdata=mask_filtered["Date"],
#         hovertemplate='Date: %{customdata|%Y-%m-%d}<br>Cumulative Avg: %{y:.0f}<extra></extra>'
#     ))

#     # Layout
#     fig.update_layout(
#         xaxis_title='Date', 
#         yaxis_title=f'{score_type.title()} Score',
#         width=1400, height=600, hovermode='closest',
#         font=FONT_CONFIG,
#         paper_bgcolor=COLORS['bg_paper'],
#         plot_bgcolor=COLORS['bg_plot'],
#         margin=dict(l=60, r=40, t=60, b=60),
#         legend=dict(
#             orientation='h', yanchor='bottom', y=1.02,
#             xanchor='right', x=1,
#             bgcolor='rgba(0,0,0,0)',
#             bordercolor='rgba(0,0,0,0)',
#             font=dict(color=COLORS['text'])
#         ),
#     )

#     # Gridlines and axes
#     axis_config = dict(
#         showgrid=True, gridcolor=COLORS['grid'],
#         zeroline=False, linecolor=COLORS['line'],
#         tickcolor=COLORS['line'],
#         tickfont=dict(color=COLORS['text']),
#         title_font=dict(color=COLORS['text'])
#     )
    
#     # X-axis with custom month ticks
#     fig.update_xaxes(
#         **axis_config,
#         tickmode='array',
#         tickvals=tickvals,
#         ticktext=ticktext
#     )
    
#     fig.update_yaxes(**axis_config)

#     return fig

# def create_histogram(michael_scores: pd.Series, sarah_scores: pd.Series, 
#                     bin_size: int, ceiling: int) -> go.Figure:
#     """Create histogram figure."""
#     hist_fig = go.Figure()
    
#     # Check if we have any data
#     if len(michael_scores) == 0 and len(sarah_scores) == 0:
#         return hist_fig
    
#     # Calculate bin alignment
#     min_score = min(michael_scores.min() if len(michael_scores) > 0 else ceiling, 
#                    sarah_scores.min() if len(sarah_scores) > 0 else ceiling)
#     bins_needed = int(np.ceil((ceiling - min_score) / bin_size))
#     tick_start = ceiling - (bins_needed * bin_size)
    
#     # Create histograms
#     if len(michael_scores) > 0:
#         hist_fig.add_trace(go.Histogram(
#             x=michael_scores,
#             name='Michael',
#             marker_color=COLORS['michael'],
#             opacity=0.7,
#             xbins=dict(
#                 size=bin_size,
#                 start=tick_start,
#                 end=ceiling
#             )
#         ))
    
#     if len(sarah_scores) > 0:
#         hist_fig.add_trace(go.Histogram(
#             x=sarah_scores,
#             name='Sarah',
#             marker_color=COLORS['sarah'],
#             opacity=0.7,
#             xbins=dict(
#                 size=bin_size,
#                 start=tick_start,
#                 end=ceiling
#             )
#         ))
    
#     # Generate tick values
#     tick_values = list(range(tick_start, ceiling + 1, bin_size))
    
#     hist_fig.update_layout(
#         barmode='overlay',
#         xaxis_title='Score',
#         yaxis_title='Count',
#         height=400,
#         font=dict(family='Poppins, Arial, sans-serif', size=12, color='#000000'),
#         paper_bgcolor=COLORS['bg_paper'],
#         plot_bgcolor=COLORS['bg_plot'],
#         margin=dict(l=60, r=40, t=40, b=60),
#         legend=dict(
#             orientation='h',
#             yanchor='bottom',
#             y=1.02,
#             xanchor='right',
#             x=1,
#             bgcolor='rgba(0,0,0,0)',
#             bordercolor='rgba(0,0,0,0)',
#             font=dict(color=COLORS['text'])
#         ),
#     )
    
#     hist_fig.update_xaxes(
#         showgrid=True,
#         gridcolor=COLORS['grid'],
#         zeroline=False,
#         linecolor=COLORS['line'],
#         tickcolor=COLORS['line'],
#         tickfont=dict(color=COLORS['text']),
#         title_font=dict(color=COLORS['text']),
#         tickmode='array',
#         tickvals=tick_values
#     )
#     hist_fig.update_yaxes(
#         showgrid=True,
#         gridcolor=COLORS['grid'],
#         zeroline=False,
#         linecolor=COLORS['line'],
#         tickcolor=COLORS['line'],
#         tickfont=dict(color=COLORS['text']),
#         title_font=dict(color=COLORS['text'])
#     )
    
#     return hist_fig

# # --- Main App ---

# st.markdown(
#     """
#     <style>
#     /* Hide the label */
#     div[data-testid="stSelectbox"] > label {
#         display: none !important;
#     }

#     /* Remove default Streamlit select styling */
#     div[data-baseweb="select"] > div {
#         background: transparent !important;
#         border: none !important;
#         box-shadow: none !important;
#         padding: 0 !important;
#         width: fit-content !important;          /* only as wide as text */
#         min-width: 0 !important;
#         overflow: visible !important;           /* prevent clipping */
#     }

#     /* Style visible select text */
#     div[data-baseweb="select"] > div > div {
#         height: auto !important;                /* allow natural height */
#         min-height: 90px !important;            /* taller block */
#         display: flex !important;
#         align-items: flex-end !important;       /* align text visually bottom */
#         padding: 8px 4px 14px 4px !important;   /* extra bottom padding */
#         font-size: 46px !important;             /* large title font */
#         font-weight: 800 !important;
#         color: #db5049 !important;              /* your red */
#         text-align: left !important;
#         line-height: 1.2em !important;          /* prevent clipping */
#         width: fit-content !important;
#         overflow: visible !important;
#     }

#     /* Make sure dropdown list aligns left */
#     div[data-baseweb="popover"] {
#         text-align: left !important;
#     }

#     /* Adjust dropdown arrow */
#     div[data-baseweb="select"] svg {
#         width: 24px !important;
#         height: 24px !important;
#         margin-left: 6px;
#     }

#     /* Prevent container clipping */
#     div[data-testid="stSelectbox"] {
#         display: inline-block !important;
#         width: auto !important;
#         overflow: visible !important;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# page_type = st.selectbox(
#     "",
#     options=["Total Scores", "Time Scores", "Geography Scores"],
#     index=0,
#     key="page_selector",
# )

# # Load data
# data = load_data()

# # After the conditional toggle for estimated scores
# remove_estimated = False
# if page_type in ["Time Scores", "Geography Scores"]:
#     remove_estimated = st.toggle("Remove Estimated Scores", value=False, key="remove_estimated_toggle")

# # Add this new toggle for all page types
# include_single_player_days = st.toggle("Include days where only one person played", value=False, key="include_single_player_toggle")


# # Prepare data based on page type
# if page_type == "Total Scores":
#     df_daily, mask = prepare_total_scores_data(data, include_single_player_days)
#     ceiling = CEILING_TOTAL
#     score_type = "total"
#     default_bin_size = 5000
#     bin_options = [1000, 2000, 2500, 3000, 4000, 5000, 7500, 10000, 15000]
#     change_threshold = 5000
# elif page_type == "Time Scores":
#     df_daily, mask = prepare_time_scores_data(data, remove_estimated, include_single_player_days)
#     ceiling = 25000
#     score_type = "time"
#     default_bin_size = 2500
#     bin_options = [500, 1000, 2000, 2500, 3000, 4000, 5000, 7500]
#     change_threshold = 2500
# else:  # Geography Scores
#     df_daily, mask = prepare_geography_scores_data(data, remove_estimated, include_single_player_days)
#     ceiling = 25000
#     score_type = "geography"
#     default_bin_size = 2500
#     bin_options = [500, 1000, 2000, 2500, 3000, 4000, 5000, 7500]
#     change_threshold = 2500

# # Date range
# min_date, max_date = mask["Date"].min(), mask["Date"].max()

# # Controls
# window_length = st.slider(
#     "Rolling Average Window (Games):",
#     min_value=1, max_value=30, value=5, step=1
# )

# # Date range slider
# start_date, end_date = st.slider(
#     "Select Date Range:",
#     min_value=min_date.to_pydatetime(),
#     max_value=max_date.to_pydatetime(),
#     value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
#     format="YYYY-MM-DD"
# )

# # Score range slider
# score_min, score_max = st.slider(
#     "Select Score Range:",
#     min_value=0,
#     max_value=ceiling,
#     value=(0, ceiling),
#     step=100 if ceiling == CEILING_TOTAL else 50
# )

# # Filter data by date range
# mask_filtered = mask[(mask["Date"] >= start_date) & (mask["Date"] <= end_date)].copy()
# df_daily_filtered = df_daily[(df_daily["Date"] >= start_date) & (df_daily["Date"] <= end_date)].copy()

# # Filter data by score range
# mask_filtered = filter_by_score_range(mask_filtered, score_min, score_max, score_type, include_single_player_days)
# df_daily_filtered = filter_by_score_range(df_daily_filtered, score_min, score_max, score_type, include_single_player_days)

# # Calculate averages
# mask_filtered = calculate_rolling_averages(mask_filtered, window_length, score_type)

# # Calculate averages
# mask_filtered = calculate_rolling_averages(mask_filtered, window_length, score_type)

# # Display main chart
# fig = create_plotly_figure(df_daily_filtered, mask_filtered, window_length, score_type, 
#                           show_single_player_days=include_single_player_days)
# st.plotly_chart(fig, use_container_width=True, key="main_chart")

# # Statistics section
# st.markdown("---")
# st.subheader("Statistics Summary")

# bin_size = st.select_slider(
#     "Select Score Bucket Size",
#     options=bin_options,
#     value=default_bin_size,
#     help="Adjust the size of score ranges in the statistics table"
# )

# # Extract player data based on score type - ONLY from days where BOTH have data (mask_filtered)
# if score_type == "total":
#     michael_scores = mask_filtered["Michael Total Score"].dropna()
#     sarah_scores = mask_filtered["Sarah Total Score"].dropna()
#     michael_dates = mask_filtered[mask_filtered["Michael Total Score"].notna()]["Date"]
#     sarah_dates = mask_filtered[mask_filtered["Sarah Total Score"].notna()]["Date"]
# elif score_type == "time":
#     michael_scores = mask_filtered["Michael Time Midpoint"].dropna()
#     sarah_scores = mask_filtered["Sarah Time Midpoint"].dropna()
#     michael_dates = mask_filtered[mask_filtered["Michael Time Midpoint"].notna()]["Date"]
#     sarah_dates = mask_filtered[mask_filtered["Sarah Time Midpoint"].notna()]["Date"]
# else:  # geography
#     michael_scores = mask_filtered["Michael Geography Midpoint"].dropna()
#     sarah_scores = mask_filtered["Sarah Geography Midpoint"].dropna()
#     michael_dates = mask_filtered[mask_filtered["Michael Geography Midpoint"].notna()]["Date"]
#     sarah_dates = mask_filtered[mask_filtered["Sarah Geography Midpoint"].notna()]["Date"]

# # Determine date format
# use_md_format = can_use_month_day_format(michael_dates) and can_use_month_day_format(sarah_dates)
# date_format = "%b %d" if use_md_format else "%Y-%m-%d"

# # Create two columns
# col1, col2 = st.columns(2)

# with col1:
#     # Display statistics table
#     stats_html = create_stats_table_html(michael_scores, sarah_scores, 
#                                         michael_dates, sarah_dates, 
#                                         bin_size, date_format, ceiling)
#     st.markdown(stats_html, unsafe_allow_html=True)
    
#     # Display histogram
#     st.markdown("<br>", unsafe_allow_html=True)
#     hist_fig = create_histogram(michael_scores, sarah_scores, bin_size, ceiling)
#     st.plotly_chart(hist_fig, use_container_width=True, key="histogram_chart")

# with col2:
#     # Display streaks table
#     streaks_html = create_streaks_table_html(michael_scores, sarah_scores,
#                                              michael_dates, sarah_dates,
#                                              bin_size, date_format, ceiling,
#                                              change_threshold)
#     st.markdown(streaks_html, unsafe_allow_html=True)