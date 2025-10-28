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
st.plotly_chart(fig, use_container_width=True, key="total_scores_chart")

# --- Statistics section ---
st.markdown("---")
st.subheader("Statistics Summary")

# Add slider for bin size selection
bin_size = st.slider(
    "Select Score Bucket Size",
    min_value=1000,
    max_value=15000,
    value=5000,
    step=500,
    help="Adjust the size of score ranges in the statistics table"
)

# Calculate statistics for Michael and Sarah
michael_scores = df_daily_filtered["Michael Total Score"].dropna()
sarah_scores = df_daily_filtered["Sarah Total Score"].dropna()
michael_dates = df_daily_filtered[df_daily_filtered["Michael Total Score"].notna()]["Date"]
sarah_dates = df_daily_filtered[df_daily_filtered["Sarah Total Score"].notna()]["Date"]

# --- Determine if month/day format is safe ---
def can_use_month_day_format(dates):
    # Build (month -> set of years) mapping
    month_years = dates.dt.to_period("M")
    month_to_years = {}
    for period in month_years:
        month = period.month
        year = period.year
        month_to_years.setdefault(month, set()).add(year)
    # If any month appears in more than one year, not safe
    return all(len(years) == 1 for years in month_to_years.values())

use_md_format = can_use_month_day_format(michael_dates) and can_use_month_day_format(sarah_dates)
date_format = "%b %d" if use_md_format else "%Y-%m-%d"

# Calculate all statistics
michael_mean = michael_scores.mean()
sarah_mean = sarah_scores.mean()
michael_median = michael_scores.median()
sarah_median = sarah_scores.median()
michael_std = michael_scores.std()
sarah_std = sarah_scores.std()
michael_min = michael_scores.min()
sarah_min = sarah_scores.min()
michael_max = michael_scores.max()
sarah_max = sarah_scores.max()


# Find dates for median, min, max
michael_median_date = michael_dates.iloc[(michael_scores - michael_median).abs().argmin()].strftime(date_format)
sarah_median_date = sarah_dates.iloc[(sarah_scores - sarah_median).abs().argmin()].strftime(date_format)
michael_min_date = michael_dates.iloc[michael_scores.argmin()].strftime(date_format)
sarah_min_date = sarah_dates.iloc[sarah_scores.argmin()].strftime(date_format)
michael_max_date = michael_dates.iloc[michael_scores.argmax()].strftime(date_format)
sarah_max_date = sarah_dates.iloc[sarah_scores.argmax()].strftime(date_format)

# Generate dynamic buckets based on bin_size (starting from ceiling)
ceiling = 50000
buckets = []
current_upper = ceiling

while current_upper > 0:
    current_lower = max(current_upper - bin_size, 0)
    
    # Calculate counts for this bucket
    if current_upper == ceiling:
        # Top bucket includes ceiling
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
        
        # Format bucket label
        if current_upper == ceiling:
            # Top bucket
            if current_lower % 1000 == 0:
                label = f"Scores {current_lower//1000}k+"
            else:
                label = f"Scores {current_lower/1000:.1f}k+"
        elif bin_size == 1000:
            # For 1k bins, show single value
            if current_lower % 1000 == 0:
                label = f"Scores {current_lower//1000}k"
            else:
                label = f"Scores {current_lower/1000:.1f}k"
        else:
            # Range format
            lower_str = f"{current_lower//1000}k" if current_lower % 1000 == 0 else f"{current_lower/1000:.1f}k"
            upper_str = f"{current_upper//1000}k" if current_upper % 1000 == 0 else f"{current_upper/1000:.1f}k"
            label = f"Scores {lower_str}-{upper_str}"
        
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


# Create two columns - table on left, empty on right
col1, col2 = st.columns(2)

with col1:
    # Build bucket rows HTML
    bucket_rows = ""
    for i, bucket in enumerate(buckets):
        border_style = "" if i == len(buckets) - 1 else "border-bottom: 1px solid #d9d7cc;"
        michael_bold = "font-weight: bold;" if bucket['michael_count'] > bucket['sarah_count'] else ""
        sarah_bold = "font-weight: bold;" if bucket['sarah_count'] > bucket['michael_count'] else ""
        
        bucket_rows += f"""<tr style="{border_style}">
    <td style="padding: 8px; color: #696761;">{bucket['label']}</td>
    <td style="padding: 8px; text-align: center; color: #221e8f; {michael_bold}">{bucket['michael_count']}</td>
    <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{bucket['michael_date']}</td>
    <td style="padding: 8px; text-align: center; color: #bf8f15; {sarah_bold}">{bucket['sarah_count']}</td>
    <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{bucket['sarah_date']}</td>
    </tr>"""
    
    # Create HTML table
    stats_html = f"""
    <style>
    .stats-table tbody tr {{
        cursor: pointer;
        transition: background-color 0.2s;
    }}
    .stats-table tbody tr:hover {{
        background-color: #e0e0d1;  /* hover color */
    }}
    .stats-table tbody tr.selected {{
        background-color: #c0c0b0;  /* clicked color */
    }}
    </style>
    <table class="stats-table" style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;">
        <thead>
            <tr style="background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;">
                <th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Statistic</th>
                <th style="padding: 10px; text-align: center; color: #221e8f; font-weight: 600;">Michael</th>
                <th style="padding: 10px; text-align: center; color: #221e8f; font-weight: 600;">Date</th>
                <th style="padding: 10px; text-align: center; color: #bf8f15; font-weight: 600;">Sarah</th>
                <th style="padding: 10px; text-align: center; color: #bf8f15; font-weight: 600;">Date</th>
            </tr>
        </thead>
        <tbody>
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Mean</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_mean > sarah_mean else ''}">{michael_mean:.0f}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">-</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_mean > michael_mean else ''}">{sarah_mean:.0f}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">-</td>
            </tr>
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Median</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_median > sarah_median else ''}">{michael_median:.0f}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_median_date}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_median > michael_median else ''}">{sarah_median:.0f}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_median_date}</td>
            </tr>
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Standard Deviation</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_std > sarah_std else ''}">{michael_std:.0f}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">-</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_std > michael_std else ''}">{sarah_std:.0f}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">-</td>
            </tr>
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Min</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_min > sarah_min else ''}">{michael_min:.0f}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_min_date}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_min > michael_min else ''}">{sarah_min:.0f}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_min_date}</td>
            </tr>
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Max</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_max > sarah_max else ''}">{michael_max:.0f}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_max_date}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_max > michael_max else ''}">{sarah_max:.0f}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_max_date}</td>
            </tr>
            {bucket_rows}
        </tbody>
    </table>
    """
    
    st.markdown(stats_html, unsafe_allow_html=True)

with col2:
    # Calculate streaks with dates
    def calculate_streak_with_dates(scores, dates, threshold, above=True):
        """Calculate longest streak above or below threshold with date range.
        If multiple streaks have the same length, return the most recent one."""
        max_streak = 0
        current_streak = 0
        max_start_idx = 0
        max_end_idx = 0
        current_start_idx = 0

        for i, score in enumerate(scores):
            if (above and score >= threshold) or (not above and score < threshold):
                if current_streak == 0:
                    current_start_idx = i
                current_streak += 1

                # Update rule: prefer *later* streaks if same length
                if (current_streak > max_streak) or (
                    current_streak == max_streak and i > max_end_idx
                ):
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
    
    def calculate_cumulative_avg_streak(scores, dates, above=True):
        """Calculate longest streak above or below cumulative average with date range.
        Cumulative average at index i = mean of scores[0:i+1]
        If multiple streaks have the same length, return the most recent one."""
        if len(scores) == 0:
            return 0, "", ""
        
        # Convert to numpy array for easier indexing
        scores_array = scores.values if hasattr(scores, 'values') else scores
            
        max_streak = 0
        current_streak = 0
        max_start_idx = 0
        max_end_idx = 0
        current_start_idx = 0

        for i in range(len(scores_array)):
            # Calculate cumulative average up to and including current point
            cumulative_avg = scores_array[:i+1].mean()
            
            if (above and scores_array[i] >= cumulative_avg) or (not above and scores_array[i] < cumulative_avg):
                if current_streak == 0:
                    current_start_idx = i
                current_streak += 1

                # Update rule: prefer *later* streaks if same length
                if (current_streak > max_streak) or (
                    current_streak == max_streak and i > max_end_idx
                ):
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
    
    def calculate_score_change_streak(scores, dates, threshold, mode="change"):
        """
        Calculate the longest streak based on daily score changes.

        Parameters
        ----------
        scores : array-like
            Sequence of scores (in chronological order).
        dates : pandas Series
            Corresponding dates for each score.
        threshold : int or float
            Change threshold (e.g., 10000 for big change, 1000 for small stability).
        mode : str
            "change" → streak where |Δscore| >= threshold
            "stable" → streak where |Δscore| <= threshold

        Returns
        -------
        (streak_length, start_date, end_date)
        """
        if len(scores) < 2:
            return 0, "", ""

        max_streak = 0
        current_streak = 0
        max_start_idx = 0
        max_end_idx = 0
        current_start_idx = 0

        for i in range(1, len(scores)):
            diff = abs(scores[i] - scores[i - 1])

            if (mode == "change" and diff >= threshold) or (mode == "stable" and diff <= threshold):
                if current_streak == 0:
                    current_start_idx = i - 1
                current_streak += 1

                # Prefer more recent streaks if tied
                if (current_streak > max_streak) or (
                    current_streak == max_streak and i > max_end_idx
                ):
                    max_streak = current_streak
                    max_start_idx = current_start_idx
                    max_end_idx = i
            else:
                current_streak = 0  # reset streak

        if max_streak > 0:
            start_date = dates.iloc[max_start_idx].strftime("%Y-%m-%d")
            end_date = dates.iloc[max_end_idx].strftime("%Y-%m-%d")
            return max_streak, start_date, end_date

        return 0, "", ""
    
    # Generate streak thresholds based on bin_size (starting from ceiling)
    ceiling = 50000
    streak_thresholds = []
    current_upper = ceiling

    while current_upper > 0:
        current_lower = max(current_upper - bin_size, 0)
        
        # Check if there's any data in this range for either player
        if current_upper == ceiling:
            michael_has_data = (michael_scores >= current_lower).any()
            sarah_has_data = (sarah_scores >= current_lower).any()
        else:
            michael_has_data = ((michael_scores >= current_lower) & (michael_scores < current_upper)).any()
            sarah_has_data = ((sarah_scores >= current_lower) & (sarah_scores < current_upper)).any()
        
        if michael_has_data or sarah_has_data:
            # Check if ALL scores are above or below this threshold
            michael_all_above = (michael_scores >= current_lower).all()
            michael_all_below = (michael_scores < current_lower).all()
            sarah_all_above = (sarah_scores >= current_lower).all()
            sarah_all_below = (sarah_scores < current_lower).all()
            
            # Only include if not all data is on one side for both players
            if not ((michael_all_above and sarah_all_above) or (michael_all_below and sarah_all_below)):
                streak_thresholds.append(current_lower)
        
        current_upper = current_lower
        if current_lower == 0:
            break

    # Calculate streaks for each threshold
    streak_data = []
    for threshold in streak_thresholds:
        michael_streak, michael_start, michael_end = calculate_streak_with_dates(
            michael_scores.values, michael_dates, threshold, above=True)
        sarah_streak, sarah_start, sarah_end = calculate_streak_with_dates(
            sarah_scores.values, sarah_dates, threshold, above=True)
        
        # Format label
        if threshold % 1000 == 0:
            label = f"Above {threshold//1000}k"
        else:
            label = f"Above {threshold/1000:.1f}k"
        
        streak_data.append({
            'label': label,
            'michael_streak': michael_streak,
            'michael_start': michael_start,
            'michael_end': michael_end,
            'sarah_streak': sarah_streak,
            'sarah_start': sarah_start,
            'sarah_end': sarah_end
        })

    # Add below streaks (reversed order)
    for threshold in reversed(streak_thresholds):
        michael_streak, michael_start, michael_end = calculate_streak_with_dates(
            michael_scores.values, michael_dates, threshold, above=False)
        sarah_streak, sarah_start, sarah_end = calculate_streak_with_dates(
            sarah_scores.values, sarah_dates, threshold, above=False)
        
        # Format label
        if threshold % 1000 == 0:
            label = f"Below {threshold//1000}k"
        else:
            label = f"Below {threshold/1000:.1f}k"
        
        streak_data.append({
            'label': label,
            'michael_streak': michael_streak,
            'michael_start': michael_start,
            'michael_end': michael_end,
            'sarah_streak': sarah_streak,
            'sarah_start': sarah_start,
            'sarah_end': sarah_end
        })
    
    # Calculate streaks relative to each player's average
    michael_streak_above_avg, michael_above_avg_start, michael_above_avg_end = calculate_cumulative_avg_streak(
        michael_scores, michael_dates, above=True)
    sarah_streak_above_avg, sarah_above_avg_start, sarah_above_avg_end = calculate_cumulative_avg_streak(
        sarah_scores, sarah_dates, above=True)
    
    michael_streak_below_avg, michael_below_avg_start, michael_below_avg_end = calculate_streak_with_dates(
        michael_scores.values, michael_dates, michael_mean, above=False)
    sarah_streak_below_avg, sarah_below_avg_start, sarah_below_avg_end = calculate_streak_with_dates(
        sarah_scores.values, sarah_dates, sarah_mean, above=False)
    
    # Longest streak where score changes by ≥ 10k each day
    michael_change_streak, michael_change_start, michael_change_end = calculate_score_change_streak(
        michael_scores.values, michael_dates, threshold=5000, mode="change")
    sarah_change_streak, sarah_change_start, sarah_change_end = calculate_score_change_streak(
        sarah_scores.values, sarah_dates, threshold=5000, mode="change")

    # Longest streak where score changes by ≤ 1k each day
    michael_stable_streak, michael_stable_start, michael_stable_end = calculate_score_change_streak(
        michael_scores.values, michael_dates, threshold=5000, mode="stable")
    sarah_stable_streak, sarah_stable_start, sarah_stable_end = calculate_score_change_streak(
        sarah_scores.values, sarah_dates, threshold=5000, mode="stable")
    
    # Build streak rows HTML
    streak_rows = ""
    for i, streak in enumerate(streak_data):
        michael_bold = "font-weight: bold;" if streak['michael_streak'] > streak['sarah_streak'] else ""
        sarah_bold = "font-weight: bold;" if streak['sarah_streak'] > streak['michael_streak'] else ""
        
        michael_dates_str = '-' if streak['michael_streak'] == 0 else (streak['michael_start'] if streak['michael_start'] == streak['michael_end'] else f"{streak['michael_start']}<br/>to {streak['michael_end']}")
        sarah_dates_str = '-' if streak['sarah_streak'] == 0 else (streak['sarah_start'] if streak['sarah_start'] == streak['sarah_end'] else f"{streak['sarah_start']}<br/>to {streak['sarah_end']}")
        
        streak_rows += f"""<tr style="border-bottom: 1px solid #d9d7cc;">
    <td style="padding: 8px; color: #696761;">{streak['label']}</td>
    <td style="padding: 8px; text-align: center; color: #221e8f; {michael_bold}">{streak['michael_streak']}</td>
    <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_dates_str}</td>
    <td style="padding: 8px; text-align: center; color: #bf8f15; {sarah_bold}">{streak['sarah_streak']}</td>
    <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_dates_str}</td>
    </tr>"""

    # Add cumulative average streaks
    michael_above_dates = '-' if michael_streak_above_avg == 0 else (michael_above_avg_start if michael_above_avg_start == michael_above_avg_end else f"{michael_above_avg_start}<br/>to {michael_above_avg_end}")
    sarah_above_dates = '-' if sarah_streak_above_avg == 0 else (sarah_above_avg_start if sarah_above_avg_start == sarah_above_avg_end else f"{sarah_above_avg_start}<br/>to {sarah_above_avg_end}")

    streak_rows += f"""<tr style="border-bottom: 1px solid #d9d7cc;">
    <td style="padding: 8px; color: #696761;">Above Cumulative Average</td>
    <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_streak_above_avg > sarah_streak_above_avg else ''}">{michael_streak_above_avg}</td>
    <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_above_dates}</td>
    <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_streak_above_avg > michael_streak_above_avg else ''}">{sarah_streak_above_avg}</td>
    <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_above_dates}</td>
    </tr>"""

    michael_below_dates = '-' if michael_streak_below_avg == 0 else (michael_below_avg_start if michael_below_avg_start == michael_below_avg_end else f"{michael_below_avg_start}<br/>to {michael_below_avg_end}")
    sarah_below_dates = '-' if sarah_streak_below_avg == 0 else (sarah_below_avg_start if sarah_below_avg_start == sarah_below_avg_end else f"{sarah_below_avg_start}<br/>to {sarah_below_avg_end}")

    streak_rows += f"""<tr style="border-bottom: 1px solid #d9d7cc;">
    <td style="padding: 8px; color: #696761;">Below Cumulative Average</td>
    <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_streak_below_avg > sarah_streak_below_avg else ''}">{michael_streak_below_avg}</td>
    <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_below_dates}</td>
    <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_streak_below_avg > michael_streak_below_avg else ''}">{sarah_streak_below_avg}</td>
    <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_below_dates}</td>
    </tr>"""

    # Add volatile and stable streaks
    michael_change_dates = '-' if michael_change_streak == 0 else (michael_change_start if michael_change_start == michael_change_end else f"{michael_change_start}<br/>to {michael_change_end}")
    sarah_change_dates = '-' if sarah_change_streak == 0 else (sarah_change_start if sarah_change_start == sarah_change_end else f"{sarah_change_start}<br/>to {sarah_change_end}")

    streak_rows += f"""<tr style="border-bottom: 1px solid #d9d7cc;">
    <td style="padding: 8px; color: #696761;">Volatile (&gt;5000 change per day)</td>
    <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_change_streak > sarah_change_streak else ''}">{michael_change_streak}</td>
    <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_change_dates}</td>
    <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_change_streak > michael_change_streak else ''}">{sarah_change_streak}</td>
    <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_change_dates}</td>
    </tr>"""

    michael_stable_dates = '-' if michael_stable_streak == 0 else (michael_stable_start if michael_stable_start == michael_stable_end else f"{michael_stable_start}<br/>to {michael_stable_end}")
    sarah_stable_dates = '-' if sarah_stable_streak == 0 else (sarah_stable_start if sarah_stable_start == sarah_stable_end else f"{sarah_stable_start}<br/>to {sarah_stable_end}")

    streak_rows += f"""<tr>
    <td style="padding: 8px; color: #696761;">Stable (&lt;5000 change per day)</td>
    <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_stable_streak > sarah_stable_streak else ''}">{michael_stable_streak}</td>
    <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_stable_dates}</td>
    <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_stable_streak > michael_stable_streak else ''}">{sarah_stable_streak}</td>
    <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_stable_dates}</td>
    </tr>"""

    # Create streaks HTML table
    streaks_html = f"""
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
    <th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Streak Type</th>
    <th style="padding: 10px; text-align: center; color: #221e8f; font-weight: 600;">Michael</th>
    <th style="padding: 10px; text-align: center; color: #221e8f; font-weight: 600;">Dates</th>
    <th style="padding: 10px; text-align: center; color: #bf8f15; font-weight: 600;">Sarah</th>
    <th style="padding: 10px; text-align: center; color: #bf8f15; font-weight: 600;">Dates</th>
    </tr>
    </thead>
    <tbody>
    {streak_rows}
    </tbody>
    </table>
    """
    
    st.markdown(streaks_html, unsafe_allow_html=True)
    