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
michael_thousand_bins = michael_scores // 1000
michael_modal_thousand = michael_thousand_bins.mode().iloc[0]
sarah_thousand_bins = sarah_scores // 1000
sarah_modal_thousand = sarah_thousand_bins.mode().iloc[0]


# Find dates for median, min, max
michael_median_date = michael_dates.iloc[(michael_scores - michael_median).abs().argmin()].strftime(date_format)
sarah_median_date = sarah_dates.iloc[(sarah_scores - sarah_median).abs().argmin()].strftime(date_format)
michael_min_date = michael_dates.iloc[michael_scores.argmin()].strftime(date_format)
sarah_min_date = sarah_dates.iloc[sarah_scores.argmin()].strftime(date_format)
michael_max_date = michael_dates.iloc[michael_scores.argmax()].strftime(date_format)
sarah_max_date = sarah_dates.iloc[sarah_scores.argmax()].strftime(date_format)

# Calculate score counts and find most recent dates for each range
michael_45k_mask = michael_scores >= 45000
sarah_45k_mask = sarah_scores >= 45000
michael_45k = michael_45k_mask.sum()
sarah_45k = sarah_45k_mask.sum()
michael_45k_date = michael_dates[michael_45k_mask].max().strftime(date_format) if michael_45k > 0 else '-'
sarah_45k_date = sarah_dates[sarah_45k_mask].max().strftime(date_format) if sarah_45k > 0 else '-'

michael_40_45k_mask = (michael_scores >= 40000) & (michael_scores < 45000)
sarah_40_45k_mask = (sarah_scores >= 40000) & (sarah_scores < 45000)
michael_40_45k = michael_40_45k_mask.sum()
sarah_40_45k = sarah_40_45k_mask.sum()
michael_40_45k_date = michael_dates[michael_40_45k_mask].max().strftime(date_format) if michael_40_45k > 0 else '-'
sarah_40_45k_date = sarah_dates[sarah_40_45k_mask].max().strftime(date_format) if sarah_40_45k > 0 else '-'

michael_35_40k_mask = (michael_scores >= 35000) & (michael_scores < 40000)
sarah_35_40k_mask = (sarah_scores >= 35000) & (sarah_scores < 40000)
michael_35_40k = michael_35_40k_mask.sum()
sarah_35_40k = sarah_35_40k_mask.sum()
michael_35_40k_date = michael_dates[michael_35_40k_mask].max().strftime(date_format) if michael_35_40k > 0 else '-'
sarah_35_40k_date = sarah_dates[sarah_35_40k_mask].max().strftime(date_format) if sarah_35_40k > 0 else '-'

michael_30_35k_mask = (michael_scores >= 30000) & (michael_scores < 35000)
sarah_30_35k_mask = (sarah_scores >= 30000) & (sarah_scores < 35000)
michael_30_35k = michael_30_35k_mask.sum()
sarah_30_35k = sarah_30_35k_mask.sum()
michael_30_35k_date = michael_dates[michael_30_35k_mask].max().strftime(date_format) if michael_30_35k > 0 else '-'
sarah_30_35k_date = sarah_dates[sarah_30_35k_mask].max().strftime(date_format) if sarah_30_35k > 0 else '-'

michael_25_30k_mask = (michael_scores >= 25000) & (michael_scores < 30000)
sarah_25_30k_mask = (sarah_scores >= 25000) & (sarah_scores < 30000)
michael_25_30k = michael_25_30k_mask.sum()
sarah_25_30k = sarah_25_30k_mask.sum()
michael_25_30k_date = michael_dates[michael_25_30k_mask].max().strftime(date_format) if michael_25_30k > 0 else '-'
sarah_25_30k_date = sarah_dates[sarah_25_30k_mask].max().strftime(date_format) if sarah_25_30k > 0 else '-'

michael_under25k_mask = michael_scores < 25000
sarah_under25k_mask = sarah_scores < 25000
michael_under25k = michael_under25k_mask.sum()
sarah_under25k = sarah_under25k_mask.sum()
michael_under25k_date = michael_dates[michael_under25k_mask].max().strftime(date_format) if michael_under25k > 0 else '-'
sarah_under25k_date = sarah_dates[sarah_under25k_mask].max().strftime(date_format) if sarah_under25k > 0 else '-'

michael_modal_mask = (michael_scores // 1000) == michael_modal_thousand
michael_modal_count = michael_modal_mask.sum()
michael_modal_date = michael_dates[michael_modal_mask].max().strftime(date_format) if michael_modal_count > 0 else '-'
sarah_modal_mask = (sarah_scores // 1000) == sarah_modal_thousand
sarah_modal_count = sarah_modal_mask.sum()
sarah_modal_date = sarah_dates[sarah_modal_mask].max().strftime(date_format) if sarah_modal_count > 0 else '-'

# Create two columns - table on left, empty on right
col1, col2 = st.columns(2)

with col1:
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
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Modal Thousand</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_modal_thousand > sarah_modal_thousand else ''}">{michael_modal_thousand:.0f}K</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_modal_date}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_modal_thousand > michael_modal_thousand else ''}">{sarah_modal_thousand:.0f}K</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_modal_date}</td>
            </tr>
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Scores 45k+</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_45k > sarah_45k else ''}">{michael_45k}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_45k_date}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_45k > michael_45k else ''}">{sarah_45k}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_45k_date}</td>
            </tr>
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Scores 40-45k</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_40_45k > sarah_40_45k else ''}">{michael_40_45k}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_40_45k_date}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_40_45k > michael_40_45k else ''}">{sarah_40_45k}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_40_45k_date}</td>
            </tr>
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Scores 35-40k</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_35_40k > sarah_35_40k else ''}">{michael_35_40k}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_35_40k_date}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_35_40k > michael_35_40k else ''}">{sarah_35_40k}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_35_40k_date}</td>
            </tr>
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Scores 30-35k</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_30_35k > sarah_30_35k else ''}">{michael_30_35k}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_30_35k_date}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_30_35k > michael_30_35k else ''}">{sarah_30_35k}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_30_35k_date}</td>
            </tr>
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Scores 25-30k</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_25_30k > sarah_25_30k else ''}">{michael_25_30k}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_25_30k_date}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_25_30k > michael_25_30k else ''}">{sarah_25_30k}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_25_30k_date}</td>
            </tr>
            <tr>
                <td style="padding: 8px; color: #696761;">Scores &lt;25k</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_under25k > sarah_under25k else ''}">{michael_under25k}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_under25k_date}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_under25k > michael_under25k else ''}">{sarah_under25k}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_under25k_date}</td>
            </tr>
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
    
    michael_streak_45k, michael_45k_start, michael_45k_end = calculate_streak_with_dates(
        michael_scores.values, michael_dates, 45000, above=True)
    sarah_streak_45k, sarah_45k_start, sarah_45k_end = calculate_streak_with_dates(
        sarah_scores.values, sarah_dates, 45000, above=True)
    
    michael_streak_40k, michael_40k_start, michael_40k_end = calculate_streak_with_dates(
        michael_scores.values, michael_dates, 40000, above=True)
    sarah_streak_40k, sarah_40k_start, sarah_40k_end = calculate_streak_with_dates(
        sarah_scores.values, sarah_dates, 40000, above=True)
    
    michael_streak_35k, michael_35k_start, michael_35k_end = calculate_streak_with_dates(
        michael_scores.values, michael_dates, 35000, above=True)
    sarah_streak_35k, sarah_35k_start, sarah_35k_end = calculate_streak_with_dates(
        sarah_scores.values, sarah_dates, 35000, above=True)
    
    michael_streak_under35k, michael_under35k_start, michael_under35k_end = calculate_streak_with_dates(
        michael_scores.values, michael_dates, 35000, above=False)
    sarah_streak_under35k, sarah_under35k_start, sarah_under35k_end = calculate_streak_with_dates(
        sarah_scores.values, sarah_dates, 35000, above=False)
    
    michael_streak_under30k, michael_under30k_start, michael_under30k_end = calculate_streak_with_dates(
        michael_scores.values, michael_dates, 30000, above=False)
    sarah_streak_under30k, sarah_under30k_start, sarah_under30k_end = calculate_streak_with_dates(
        sarah_scores.values, sarah_dates, 30000, above=False)
    
    # Calculate streaks relative to each player's average
    michael_streak_above_avg, michael_above_avg_start, michael_above_avg_end = calculate_streak_with_dates(
        michael_scores.values, michael_dates, michael_mean, above=True)
    sarah_streak_above_avg, sarah_above_avg_start, sarah_above_avg_end = calculate_streak_with_dates(
        sarah_scores.values, sarah_dates, sarah_mean, above=True)
    
    michael_streak_below_avg, michael_below_avg_start, michael_below_avg_end = calculate_streak_with_dates(
        michael_scores.values, michael_dates, michael_mean, above=False)
    sarah_streak_below_avg, sarah_below_avg_start, sarah_below_avg_end = calculate_streak_with_dates(
        sarah_scores.values, sarah_dates, sarah_mean, above=False)
    
    # Calculate streaks relative to opponent's average
    michael_streak_above_avg_opponent, michael_above_avg_opponent_start, michael_above_avg_opponent_end = calculate_streak_with_dates(
        michael_scores.values, michael_dates, sarah_mean, above=True)
    sarah_streak_above_avg_opponent, sarah_above_avg_opponent_start, sarah_above_avg_opponent_end = calculate_streak_with_dates(
        sarah_scores.values, sarah_dates, michael_mean, above=True)
    
    michael_streak_below_avg_opponent, michael_below_avg_opponent_start, michael_below_avg_opponent_end = calculate_streak_with_dates(
        michael_scores.values, michael_dates, sarah_mean, above=False)
    sarah_streak_below_avg_opponent, sarah_below_avg_opponent_start, sarah_below_avg_opponent_end = calculate_streak_with_dates(
        sarah_scores.values, sarah_dates, michael_mean, above=False)
    
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
    
    # Create streaks HTML table
    streaks_html = f"""
    <style>
    .streaks-table tbody tr {{
        cursor: pointer;
        transition: background-color 0.2s;
    }}
    .streaks-table tbody tr:hover {{
        background-color: #e0e0d1;  /* hover color */
    }}
    .streaks-table tbody tr.selected {{
        background-color: #c0c0b0;  /* clicked color */
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
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Above 45k</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_streak_45k > sarah_streak_45k else ''}">{michael_streak_45k}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">
                    {('-' if michael_streak_45k == 0 
                    else (michael_45k_start if michael_45k_start == michael_45k_end 
                            else f"{michael_45k_start}<br/>to {michael_45k_end}"))}
                </td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_streak_45k > michael_streak_45k else ''}">{sarah_streak_45k}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">{sarah_45k_start if sarah_streak_45k > 0 else '-'}<br/>to {sarah_45k_end if sarah_streak_45k > 0 else ''}</td>
            </tr>
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Above 40k</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_streak_40k > sarah_streak_40k else ''}">{michael_streak_40k}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">
                    {('-' if michael_streak_40k == 0 else (michael_40k_start if michael_40k_start == michael_40k_end else f"{michael_40k_start}<br/>to {michael_40k_end}"))}
                </td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_streak_40k > michael_streak_40k else ''}">{sarah_streak_40k}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">
                    {('-' if sarah_streak_40k == 0 else (sarah_40k_start if sarah_40k_start == sarah_40k_end else f"{sarah_40k_start}<br/>to {sarah_40k_end}"))}
                </td>
            </tr>
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Above 35k</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_streak_35k > sarah_streak_35k else ''}">{michael_streak_35k}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">
                    {('-' if michael_streak_35k == 0 else (michael_35k_start if michael_35k_start == michael_35k_end else f"{michael_35k_start}<br/>to {michael_35k_end}"))}
                </td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_streak_35k > michael_streak_35k else ''}">{sarah_streak_35k}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">
                    {('-' if sarah_streak_35k == 0 else (sarah_35k_start if sarah_35k_start == sarah_35k_end else f"{sarah_35k_start}<br/>to {sarah_35k_end}"))}
                </td>
            </tr>
            <tr style="border-bottom: 1px solid #d9d7cc;">
                <td style="padding: 8px; color: #696761;">Below 35k</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_streak_under35k > sarah_streak_under35k else ''}">{michael_streak_under35k}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">
                    {('-' if michael_streak_under35k == 0 else (michael_under35k_start if michael_under35k_start == michael_under35k_end else f"{michael_under35k_start}<br/>to {michael_under35k_end}"))}
                </td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_streak_under35k > michael_streak_under35k else ''}">{sarah_streak_under35k}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">
                    {('-' if sarah_streak_under35k == 0 else (sarah_under35k_start if sarah_under35k_start == sarah_under35k_end else f"{sarah_under35k_start}<br/>to {sarah_under35k_end}"))}
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; color: #696761;">Below 30k</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_streak_under30k > sarah_streak_under30k else ''}">{michael_streak_under30k}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">
                    {('-' if michael_streak_under30k == 0 else (michael_under30k_start if michael_under30k_start == michael_under30k_end else f"{michael_under30k_start}<br/>to {michael_under30k_end}"))}
                </td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_streak_under30k > michael_streak_under30k else ''}">{sarah_streak_under30k}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">
                    {('-' if sarah_streak_under30k == 0 else (sarah_under30k_start if sarah_under30k_start == sarah_under30k_end else f"{sarah_under30k_start}<br/>to {sarah_under30k_end}"))}
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; color: #696761;">Above Average</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_streak_above_avg > sarah_streak_above_avg else ''}">{michael_streak_above_avg}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">
                    {('-' if michael_streak_above_avg == 0 else (michael_above_avg_start if michael_above_avg_start == michael_above_avg_end else f"{michael_above_avg_start}<br/>to {michael_above_avg_end}"))}
                </td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_streak_above_avg > michael_streak_above_avg else ''}">{sarah_streak_above_avg}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">
                    {('-' if sarah_streak_above_avg == 0 else (sarah_above_avg_start if sarah_above_avg_start == sarah_above_avg_end else f"{sarah_above_avg_start}<br/>to {sarah_above_avg_end}"))}
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; color: #696761;">Below Average</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_streak_below_avg > sarah_streak_below_avg else ''}">{michael_streak_below_avg}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">
                    {('-' if michael_streak_below_avg == 0 else (michael_below_avg_start if michael_below_avg_start == michael_below_avg_end else f"{michael_below_avg_start}<br/>to {michael_below_avg_end}"))}
                </td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_streak_below_avg > michael_streak_below_avg else ''}">{sarah_streak_below_avg}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">
                    {('-' if sarah_streak_below_avg == 0 else (sarah_below_avg_start if sarah_below_avg_start == sarah_below_avg_end else f"{sarah_below_avg_start}<br/>to {sarah_below_avg_end}"))}
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; color: #696761;">Above Opponent's Average</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_streak_above_avg_opponent > sarah_streak_above_avg_opponent else ''}">{michael_streak_above_avg_opponent}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">
                    {('-' if michael_streak_above_avg_opponent == 0 else (michael_above_avg_opponent_start if michael_above_avg_opponent_start == michael_above_avg_opponent_end else f"{michael_above_avg_opponent_start}<br/>to {michael_above_avg_opponent_end}"))}
                </td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_streak_above_avg_opponent > michael_streak_above_avg_opponent else ''}">{sarah_streak_above_avg_opponent}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">
                    {('-' if sarah_streak_above_avg_opponent == 0 else (sarah_above_avg_opponent_start if sarah_above_avg_opponent_start == sarah_above_avg_opponent_end else f"{sarah_above_avg_opponent_start}<br/>to {sarah_above_avg_opponent_end}"))}
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; color: #696761;">Below Opponent's Average</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_streak_below_avg_opponent > sarah_streak_below_avg_opponent else ''}">{michael_streak_below_avg_opponent}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">
                    {('-' if michael_streak_below_avg_opponent == 0 else (michael_below_avg_opponent_start if michael_below_avg_opponent_start == michael_below_avg_opponent_end else f"{michael_below_avg_opponent_start}<br/>to {michael_below_avg_opponent_end}"))}
                </td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_streak_below_avg_opponent > michael_streak_below_avg_opponent else ''}">{sarah_streak_below_avg_opponent}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">
                    {('-' if sarah_streak_below_avg_opponent == 0 else (sarah_below_avg_opponent_start if sarah_below_avg_opponent_start == sarah_below_avg_opponent_end else f"{sarah_below_avg_opponent_start}<br/>to {sarah_below_avg_opponent_end}"))}
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; color: #696761;">Volatile (&gt;5000 change per day)</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_change_streak > sarah_change_streak else ''}">{michael_change_streak}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">
                    {('-' if michael_change_streak == 0 else (michael_change_start if michael_change_start == michael_change_end else f"{michael_change_start}<br/>to {michael_change_end}"))}
                </td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_change_streak > michael_change_streak else ''}">{sarah_change_streak}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">
                    {('-' if sarah_change_streak == 0 else (sarah_change_start if sarah_change_start == sarah_change_end else f"{sarah_change_start}<br/>to {sarah_change_end}"))}
                </td>
            </tr>
            <tr>
                <td style="padding: 8px; color: #696761;">Stable (&lt;5000 change per day)</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; {'font-weight: bold;' if michael_stable_streak > sarah_stable_streak else ''}">{michael_stable_streak}</td>
                <td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">
                    {('-' if michael_stable_streak == 0 else (michael_stable_start if michael_stable_start == michael_stable_end else f"{michael_stable_start}<br/>to {michael_stable_end}"))}
                </td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; {'font-weight: bold;' if sarah_stable_streak > michael_stable_streak else ''}">{sarah_stable_streak}</td>
                <td style="padding: 8px; text-align: center; color: #bf8f15; font-size: 11px;">
                    {('-' if sarah_stable_streak == 0 else (sarah_stable_start if sarah_stable_start == sarah_stable_end else f"{sarah_stable_start}<br/>to {sarah_stable_end}"))}
                </td>
            </tr>
        </tbody>
    </table>
    """
    
    st.markdown(streaks_html, unsafe_allow_html=True)
    