import os
import streamlit as st
from background import set_random_sarah_background

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
from typing import Tuple, List, Dict

# --- Configuration ---
st.set_page_config(page_title="Win Margins Dashboard", layout="wide")

# --- Load CSS ---
from utils import load_css
load_css()

# --- Custom Styling ---
CUSTOM_STYLES = """
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
        .streaks-table tbody tr {
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .streaks-table tbody tr:hover {
            background-color: #e0e0d1;
        }
        .streaks-table tbody tr.selected {
            background-color: #c0c0b0;
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
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
        data = data.sort_values("Date").reset_index(drop=True)
        return data
    except FileNotFoundError:
        st.error(f"Data file not found at {filepath}")
        st.stop()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

def prepare_total_margins_data(data: pd.DataFrame) -> pd.DataFrame:
    """Prepare data for Total Win Margins."""
    df_daily = data.groupby("Timeguessr Day").first().reset_index()
    mask = df_daily[["Date", "Michael Total Score", "Sarah Total Score"]].dropna()
    mask = mask.sort_values("Date").reset_index(drop=True)
    mask["Score Diff"] = mask["Michael Total Score"] - mask["Sarah Total Score"]
    return mask

def prepare_time_margins_data(data: pd.DataFrame, remove_estimated: bool = False) -> pd.DataFrame:
    """Prepare data for Time Win Margins."""
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
    df_daily = data.groupby("Date")[daily_cols].sum(min_count=1).reset_index()
    df_daily = df_daily.sort_values("Date").reset_index(drop=True)
    
    # Keep only days where BOTH players have data
    mask = df_daily[
        df_daily["Michael Time Midpoint"].notna() & df_daily["Sarah Time Midpoint"].notna()
    ].copy()
    mask["Score Diff"] = mask["Michael Time Midpoint"] - mask["Sarah Time Midpoint"]
    return mask

def prepare_geography_margins_data(data: pd.DataFrame, remove_estimated: bool = False) -> pd.DataFrame:
    """Prepare data for Geography Win Margins."""
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
    df_daily = data.groupby("Date")[daily_cols].sum(min_count=1).reset_index()
    df_daily = df_daily.sort_values("Date").reset_index(drop=True)
    
    # Keep only days where BOTH players have data
    mask = df_daily[
        df_daily["Michael Geography Midpoint"].notna() & df_daily["Sarah Geography Midpoint"].notna()
    ].copy()
    mask["Score Diff"] = mask["Michael Geography Midpoint"] - mask["Sarah Geography Midpoint"]
    return mask

def add_zero_crossing_interpolation(mask_filtered: pd.DataFrame, window_length: int) -> pd.DataFrame:
    """Add interpolated zero-crossing points for smooth line transitions."""
    # Reset index to ensure we can use integer-based indexing
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
            continue  # Skip if crossing at first index
            
        y1 = y.iloc[i-1]
        x1 = dates.iloc[i-1]
        y2 = y.iloc[i]
        x2 = dates.iloc[i]
        
        # Get cumulative diff values for interpolation
        cum1 = mask_filtered["Cumulative Diff"].iloc[i-1]
        cum2 = mask_filtered["Cumulative Diff"].iloc[i]
        
        # Get score diff values for interpolation
        score1 = mask_filtered["Score Diff"].iloc[i-1]
        score2 = mask_filtered["Score Diff"].iloc[i]
        
        date_diff_seconds = (x2 - x1).total_seconds()
        
        if y2 - y1 != 0:
            # Calculate the fraction of the way across the segment where rolling avg crosses zero
            fraction = (0 - y1) / (y2 - y1)
            
            time_at_zero_seconds = date_diff_seconds * fraction
            x_zero = x1 + pd.Timedelta(time_at_zero_seconds, unit='s')
            
            # Interpolate cumulative diff at the crossing point
            cum_zero = cum1 + fraction * (cum2 - cum1)
            
            # Interpolate score diff at the crossing point
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

def create_win_margins_figure(mask_filtered: pd.DataFrame, window_length: int) -> go.Figure:
    """Create the win margins Plotly figure."""
    fig = go.Figure()
    
    # Create equidistant x-axis indices based only on visible (midnight) dots
    mask_filtered = mask_filtered.copy()
    is_midnight = mask_filtered["Date"].dt.time == pd.Timestamp("00:00:00").time()

    # Assign indices only for visible (midnight) entries
    visible_indices = np.arange(is_midnight.sum())
    mask_filtered.loc[is_midnight, "x_index"] = visible_indices

    # Fill missing x_index values for hidden dots via interpolation
    mask_filtered["x_index"] = mask_filtered["x_index"].interpolate(method="linear")
    
    # Scatter points for each game — only show markers at 00:00
    is_midnight = mask_filtered["Date"].dt.time == pd.Timestamp("00:00:00").time()
    marker_opacity = np.where(is_midnight, 0.4, 0)  # show only 00:00 points

    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"],
        y=mask_filtered["Score Diff"],
        mode="markers",
        marker=dict(
            color="gray",
            opacity=marker_opacity,
            size=7
        ),
        name="Game Result (Michael − Sarah)",
        customdata=mask_filtered["Date"],
        hovertemplate="Date: %{customdata}<br>Score Diff: %{y}<extra></extra>"
    ))

    
    # Shaded win regions
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"],
        y=np.where(mask_filtered["Score Diff"] > 0, mask_filtered["Score Diff"], 0),
        fill='tozeroy',
        mode='none',
        fillcolor='rgba(188, 176, 255, 0.6)',
        name='Michael Wins'
    ))
    
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"],
        y=np.where(mask_filtered["Score Diff"] < 0, mask_filtered["Score Diff"], 0),
        fill='tozeroy',
        mode='none',
        fillcolor='rgba(255, 148, 189, 0.6)',
        name='Sarah Wins'
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
        hovertemplate='Date: %{customdata}<br>Cumulative Avg: %{y:.1f}<extra></extra>'
    ))
    # Rolling average - positive segment
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"],
        y=mask_filtered["Rolling Diff Pos"],
        mode="lines",
        name=f"{window_length}-Game Rolling Avg",
        line=dict(color="#221e8f", width=2.5),
        opacity=0.8,
        showlegend=False,
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata}<br>Rolling Avg: %{y:.1f}<extra></extra>'
    ))
    
    # Rolling average - negative segment
    fig.add_trace(go.Scatter(
        x=mask_filtered["x_index"],
        y=mask_filtered["Rolling Diff Neg"],
        mode="lines",
        name=f"{window_length}-Game Rolling Avg",
        line=dict(color="#8a005c", width=2.5),
        opacity=0.8,
        showlegend=False,
        customdata=mask_filtered["Date"],
        hovertemplate='Date: %{customdata}<br>Rolling Avg: %{y:.1f}<extra></extra>'
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
    
    # Round y_max up to nearest 5000
    y_max = np.ceil(y_max / 5000) * 5000
    tick_vals = np.arange(-y_max, y_max + 1, 5000)
    tick_text = [str(abs(int(t))) for t in tick_vals]
    
    # Layout
    fig.add_hline(y=0, line=dict(color="#8f8d85", dash="dash", width=1))

    # Best reference lines (midnight points only)
    actual_diffs = mask_filtered.loc[is_midnight, "Score Diff"]
    if not actual_diffs.empty:
        m_best = actual_diffs.max()
        s_best = actual_diffs.min()
        fig.add_hline(y=m_best, line=dict(color="#221e8f", width=1, dash='dash'), opacity=0.45)
        fig.add_hline(y=s_best, line=dict(color="#8a005c", width=1, dash='dash'), opacity=0.45)

    # Determine x-axis tick positions (first data point per month, midnight only)
    midnight_df = mask_filtered[is_midnight].copy()
    midnight_df['month_year'] = midnight_df['Date'].dt.to_period('M')
    first_of_month_indices = midnight_df.groupby('month_year').head(1).index.tolist()
    tick_indices = [mask_filtered.loc[idx, 'x_index'] for idx in first_of_month_indices]
    tick_labels = [mask_filtered.loc[idx, 'Date'].strftime('%b %Y') for idx in first_of_month_indices]

    # Score Tracking Start vertical line
    score_tracking_date = pd.Timestamp('2025-10-20')
    if not midnight_df.empty and midnight_df['Date'].min() <= score_tracking_date <= midnight_df['Date'].max():
        midnight_ge = midnight_df[midnight_df['Date'] >= score_tracking_date]
        if not midnight_ge.empty:
            target_idx = midnight_ge.index[0]
            score_tracking_pos = mask_filtered.loc[target_idx, 'x_index']
            fig.add_vline(x=score_tracking_pos, line=dict(color="#696761", width=1.5, dash="dash"))
            if score_tracking_pos in tick_indices:
                i = tick_indices.index(score_tracking_pos)
                tick_labels[i] += "<br>Tracking Start"
            else:
                tick_indices.append(score_tracking_pos)
                tick_labels.append("Tracking Start")
            combined = sorted(zip(tick_indices, tick_labels))
            tick_indices, tick_labels = [list(x) for x in zip(*combined)]

    # TimeGuessr Survey vertical line (May 18, 2026)
    survey_date = pd.Timestamp('2026-05-18')
    if not midnight_df.empty and midnight_df['Date'].min() <= survey_date <= midnight_df['Date'].max():
        midnight_ge = midnight_df[midnight_df['Date'] >= survey_date]
        if not midnight_ge.empty:
            target_idx = midnight_ge.index[0]
            survey_pos = mask_filtered.loc[target_idx, 'x_index']
            fig.add_vline(x=survey_pos, line=dict(color="#696761", width=1.5, dash="dash"))
            if survey_pos in tick_indices:
                i = tick_indices.index(survey_pos)
                tick_labels[i] += "<br>TimeGuessr Survey"
            else:
                tick_indices.append(survey_pos)
                tick_labels.append("TimeGuessr Survey")
            combined = sorted(zip(tick_indices, tick_labels))
            tick_indices, tick_labels = [list(x) for x in zip(*combined)]

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Score Difference (Michael − Sarah)",
        width=1400,
        height=600,
        hovermode="closest",
        font=dict(family="Poppins, Arial, sans-serif", size=14, color="#000000"),
        paper_bgcolor="#eae8dc",
        plot_bgcolor="#d9d7cc",
        margin=dict(l=60, r=20, t=60, b=60),
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

    # Axes styling
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#bdbbb1",
        zeroline=False,
        linecolor="#8f8d85",
        tickcolor="#8f8d85",
        tickfont=dict(color="#696761"),
        title_font=dict(color="#696761"),
        tickmode='array',
        tickvals=tick_indices,
        ticktext=tick_labels,
        tickangle=-45,
        range=[-0.5, mask_filtered["x_index"].max() + 0.5]
    )
    
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
    
    return fig

def create_momentum_timeline(data: pd.DataFrame, window_length: int) -> str:
    """
    Generates a bar chart strip for the last (window_length * 4) games.
    Each game is a bar whose height is proportional to the win margin.
    """
    n_games = window_length * 4
    recent_data = data.tail(n_games).reset_index(drop=True)

    if len(recent_data) == 0:
        return ""

    COLOR_MICHAEL = '#221e8f'
    COLOR_SARAH   = '#8a005c'
    COLOR_TIE     = '#8f8d85'
    COLOR_TEXT    = '#696761'
    MIN_HEIGHT_PCT = 10  # minimum fill height so even small margins are visible

    diffs = recent_data['Score Diff'].fillna(0)
    max_abs = diffs.abs().max() or 1

    segments = []
    slot_pct = 100 / len(recent_data)

    for _, row in recent_data.iterrows():
        diff = row['Score Diff']
        date_str = row['Date'].strftime('%b %d')
        intensity = min(1.0, abs(diff) / max_abs)
        height_pct = MIN_HEIGHT_PCT + (100 - MIN_HEIGHT_PCT) * intensity

        if diff > 0:
            color = COLOR_MICHAEL
            label = f"Michael (+{diff:,.0f})"
        elif diff < 0:
            color = COLOR_SARAH
            label = f"Sarah (+{abs(diff):,.0f})"
        else:
            color = COLOR_TIE
            label = "Tie"

        segments.append(
            f'<div style="width:{slot_pct}%;display:flex;align-items:center;justify-content:center;height:100%;box-sizing:border-box;padding:0 1px;">'
            f'<div style="width:100%;height:{height_pct:.1f}%;background-color:{color};border-radius:3px;" title="{date_str}: {label}"></div>'
            f'</div>'
        )

    m_wins = (diffs > 0).sum()
    s_wins = (diffs < 0).sum()
    start_date = recent_data.iloc[0]['Date'].strftime('%b %d')
    end_date   = recent_data.iloc[-1]['Date'].strftime('%b %d')
    bar_segments = "".join(segments)

    html = f"""
<div style="font-family:'Poppins',sans-serif;margin-top:20px;padding:15px;background-color:#eae8dc;border-radius:12px;border:1px solid #d9d7cc;">
<div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:10px;">
<h4 style="margin:0;color:{COLOR_TEXT};font-size:16px;text-transform:uppercase;letter-spacing:1px;">
Momentum <span style="font-size:12px;text-transform:none;opacity:0.8;">(Last {n_games} Games)</span>
</h4>
<div style="font-size:12px;font-weight:600;">
<span style="color:{COLOR_MICHAEL};">Michael: {m_wins}</span>
<span style="color:#b0afaa;margin:0 6px;">|</span>
<span style="color:{COLOR_SARAH};">Sarah: {s_wins}</span>
</div>
</div>
<div style="width:100%;height:48px;border-radius:6px;overflow:hidden;display:flex;background-color:transparent;">
{bar_segments}
</div>
<div style="display:flex;justify-content:space-between;margin-top:4px;color:#8f8d85;font-size:10px;">
<span>{start_date}</span><span>{end_date}</span>
</div>
</div>
"""
    return html

def get_win_stats(df: pd.DataFrame, lower: float, upper: float, is_michael: bool = True) -> Tuple[int, str]:
    """Calculate win counts and most recent date for a margin category."""
    if is_michael:
        cond = (df["Score Diff"] > lower) & (df["Score Diff"] <= upper)
    else:
        cond = (df["Score Diff"] < -lower) & (df["Score Diff"] >= -upper)
    
    subset = df[cond]
    count = len(subset)
    recent = subset["Date"].max().strftime("%Y-%m-%d") if not subset.empty else "-"
    return count, recent

def calculate_streaks(df: pd.DataFrame) -> List[Dict]:
    """Calculate win streaks for both players."""
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
                streaks.append({
                    'winner': current_winner,
                    'length': current_streak,
                    'start_date': streak_start,
                    'end_date': df.iloc[idx-1]["Date"]
                })
            current_winner = winner
            current_streak = 1
            streak_start = row["Date"]
    
    # Add final streak
    if current_winner is not None and current_streak > 0:
        streaks.append({
            'winner': current_winner,
            'length': current_streak,
            'start_date': streak_start,
            'end_date': df.iloc[-1]["Date"]
        })
    
    return streaks

def create_win_summary_table(mask_filtered: pd.DataFrame, win_categories: Dict) -> str:
    """Create win summary HTML table."""
    michael_wins = mask_filtered[mask_filtered["Score Diff"] > 0]
    sarah_wins = mask_filtered[mask_filtered["Score Diff"] < 0]
    
    # Calculate stats for each category
    stats = {}
    for category, (lower, upper) in win_categories.items():
        m_count, m_date = get_win_stats(michael_wins, lower, upper, True)
        s_count, s_date = get_win_stats(sarah_wins, lower, upper, False)
        stats[category] = (m_count, m_date, s_count, s_date)
    
    # Total wins
    michael_win_count = len(michael_wins)
    sarah_win_count = len(sarah_wins)
    michael_recent_win = michael_wins["Date"].max().strftime("%Y-%m-%d") if not michael_wins.empty else "-"
    sarah_recent_win = sarah_wins["Date"].max().strftime("%Y-%m-%d") if not sarah_wins.empty else "-"
    
    # Largest and smallest wins
    michael_largest = michael_wins["Score Diff"].max() if not michael_wins.empty else "-"
    michael_largest_date = michael_wins.loc[michael_wins["Score Diff"].idxmax(), "Date"].strftime("%Y-%m-%d") if not michael_wins.empty else "-"
    michael_smallest = michael_wins["Score Diff"].min() if not michael_wins.empty else "-"
    michael_smallest_date = michael_wins.loc[michael_wins["Score Diff"].idxmin(), "Date"].strftime("%Y-%m-%d") if not michael_wins.empty else "-"
    
    sarah_largest = sarah_wins["Score Diff"].min() if not sarah_wins.empty else "-"
    sarah_largest_date = sarah_wins.loc[sarah_wins["Score Diff"].idxmin(), "Date"].strftime("%Y-%m-%d") if not sarah_wins.empty else "-"
    sarah_smallest = sarah_wins["Score Diff"].max() if not sarah_wins.empty else "-"
    sarah_smallest_date = sarah_wins.loc[sarah_wins["Score Diff"].idxmax(), "Date"].strftime("%Y-%m-%d") if not sarah_wins.empty else "-"
    
    # Build HTML
    rows = f"""<tr style="border-bottom: 1px solid #d9d7cc;"><td style="padding: 8px; color: #696761;">Wins</td><td style="padding: 8px; text-align: center; color: #221e8f;">{michael_win_count}</td><td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_recent_win}</td><td style="padding: 8px; text-align: center; color: #8a005c;">{sarah_win_count}</td><td style="padding: 8px; text-align: center; color: #8a005c; font-size: 11px;">{sarah_recent_win}</td></tr>"""
    
    for label, (m_count, m_date, s_count, s_date) in stats.items():
        rows += f"""<tr style="border-bottom: 1px solid #d9d7cc;"><td style="padding: 8px; color: #696761;">{label}</td><td style="padding: 8px; text-align: center; color: #221e8f;">{m_count}</td><td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{m_date}</td><td style="padding: 8px; text-align: center; color: #8a005c;">{s_count}</td><td style="padding: 8px; text-align: center; color: #8a005c; font-size: 11px;">{s_date}</td></tr>"""
    
    rows += f"""<tr style="border-bottom: 1px solid #d9d7cc;"><td style="padding: 8px; color: #696761;">Largest Win</td><td style="padding: 8px; text-align: center; color: #221e8f;">{michael_largest}</td><td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_largest_date}</td><td style="padding: 8px; text-align: center; color: #8a005c;">{abs(sarah_largest) if sarah_largest != '-' else '-'}</td><td style="padding: 8px; text-align: center; color: #8a005c; font-size: 11px;">{sarah_largest_date}</td></tr><tr style="border-bottom: 1px solid #d9d7cc;"><td style="padding: 8px; color: #696761;">Smallest Win</td><td style="padding: 8px; text-align: center; color: #221e8f;">{michael_smallest}</td><td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_smallest_date}</td><td style="padding: 8px; text-align: center; color: #8a005c;">{abs(sarah_smallest) if sarah_smallest != '-' else '-'}</td><td style="padding: 8px; text-align: center; color: #8a005c; font-size: 11px;">{sarah_smallest_date}</td></tr>"""
    
    html = f"""<table class="streaks-table" style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;"><thead><tr style="background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;"><th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Category</th><th style="padding: 10px; text-align: center; color: #221e8f; font-weight: 600;">Michael</th><th style="padding: 10px; text-align: center; color: #221e8f; font-weight: 600;">Date</th><th style="padding: 10px; text-align: center; color: #8a005c; font-weight: 600;">Sarah</th><th style="padding: 10px; text-align: center; color: #8a005c; font-weight: 600;">Date</th></tr></thead><tbody>{rows}</tbody></table>"""
    
    return html

def create_streaks_table(mask_filtered: pd.DataFrame) -> str:
    """Create streaks HTML table."""
    streaks = calculate_streaks(mask_filtered)
    
    michael_streaks = [s for s in streaks if s['winner'] == 'Michael']
    sarah_streaks = [s for s in streaks if s['winner'] == 'Sarah']
    
    # Longest streaks
    michael_longest = max(michael_streaks, key=lambda x: x['length']) if michael_streaks else None
    sarah_longest = max(sarah_streaks, key=lambda x: x['length']) if sarah_streaks else None
    
    michael_longest_length = michael_longest['length'] if michael_longest else "-"
    michael_longest_date = f"{michael_longest['start_date'].strftime('%Y-%m-%d')} to {michael_longest['end_date'].strftime('%Y-%m-%d')}" if michael_longest else "-"
    
    sarah_longest_length = sarah_longest['length'] if sarah_longest else "-"
    sarah_longest_date = f"{sarah_longest['start_date'].strftime('%Y-%m-%d')} to {sarah_longest['end_date'].strftime('%Y-%m-%d')}" if sarah_longest else "-"
    
    # Current streak
    current_streak_winner = streaks[-1]['winner'] if streaks else None
    current_streak_length = streaks[-1]['length'] if streaks else 0
    current_streak_start = streaks[-1]['start_date'].strftime('%Y-%m-%d') if streaks else "-"
    
    michael_current_streak = current_streak_length if current_streak_winner == "Michael" else 0
    michael_current_date = current_streak_start if current_streak_winner == "Michael" else "-"
    
    sarah_current_streak = current_streak_length if current_streak_winner == "Sarah" else 0
    sarah_current_date = current_streak_start if current_streak_winner == "Sarah" else "-"
    
    # Build streak count rows
    max_streak = max([s['length'] for s in streaks]) if streaks else 0
    streak_rows = ""
    
    for streak_len in range(max_streak, 0, -1):
        michael_count = sum(1 for s in michael_streaks if s['length'] >= streak_len)
        sarah_count = sum(1 for s in sarah_streaks if s['length'] >= streak_len)
        
        michael_recent_streaks = [s for s in michael_streaks if s['length'] >= streak_len]
        sarah_recent_streaks = [s for s in sarah_streaks if s['length'] >= streak_len]
        
        michael_recent = max([s['end_date'] for s in michael_recent_streaks]).strftime('%Y-%m-%d') if michael_recent_streaks else "-"
        sarah_recent = max([s['end_date'] for s in sarah_recent_streaks]).strftime('%Y-%m-%d') if sarah_recent_streaks else "-"
        
        streak_rows += f"""<tr style="border-bottom: 1px solid #d9d7cc;"><td style="padding: 8px; color: #696761;">Streaks ≥ {streak_len}</td><td style="padding: 8px; text-align: center; color: #221e8f;">{michael_count}</td><td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_recent}</td><td style="padding: 8px; text-align: center; color: #8a005c;">{sarah_count}</td><td style="padding: 8px; text-align: center; color: #8a005c; font-size: 11px;">{sarah_recent}</td></tr>"""
    
    html = f"""<table class="streaks-table" style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;"><thead><tr style="background-color: #d9d7cc; border-bottom: 2px solid #8f8d85;"><th style="padding: 10px; text-align: left; color: #696761; font-weight: 600;">Streak Type</th><th style="padding: 10px; text-align: center; color: #221e8f; font-weight: 600;">Michael</th><th style="padding: 10px; text-align: center; color: #221e8f; font-weight: 600;">Date(s)</th><th style="padding: 10px; text-align: center; color: #8a005c; font-weight: 600;">Sarah</th><th style="padding: 10px; text-align: center; color: #8a005c; font-weight: 600;">Date(s)</th></tr></thead><tbody><tr style="border-bottom: 1px solid #d9d7cc;"><td style="padding: 8px; color: #696761;">Current Streak</td><td style="padding: 8px; text-align: center; color: #221e8f;">{michael_current_streak}</td><td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_current_date}</td><td style="padding: 8px; text-align: center; color: #8a005c;">{sarah_current_streak}</td><td style="padding: 8px; text-align: center; color: #8a005c; font-size: 11px;">{sarah_current_date}</td></tr><tr style="border-bottom: 1px solid #d9d7cc;"><td style="padding: 8px; color: #696761;">Longest Streak</td><td style="padding: 8px; text-align: center; color: #221e8f;">{michael_longest_length}</td><td style="padding: 8px; text-align: center; color: #221e8f; font-size: 11px;">{michael_longest_date}</td><td style="padding: 8px; text-align: center; color: #8a005c;">{sarah_longest_length}</td><td style="padding: 8px; text-align: center; color: #8a005c; font-size: 11px;">{sarah_longest_date}</td></tr>{streak_rows}</tbody></table>"""
    
    return html


# --- Main App ---

# Load data
stats_mtime = os.path.getmtime("./Data/Timeguessr_Stats.csv") if os.path.exists("./Data/Timeguessr_Stats.csv") else 0
data = load_data(mtime=stats_mtime)

# Render Sidebar Controls
with st.sidebar:
    st.header("Settings")
    
    page_type = st.radio(
        "Margin Type:",
        options=["Total Win Margins", "Time Win Margins", "Geography Win Margins"],
        index=0,
        key="page_selector"
    )

    remove_pre_tracking = st.toggle("Remove Pre-Tracking Scores", value=False, key="remove_pre_tracking_toggle")
    remove_pre_survey = st.toggle("Remove Pre-Survey Scores", value=False, key="remove_pre_survey_toggle")

# Prepare data and win categories based on page type selection
if page_type == "Total Win Margins":
    mask = prepare_total_margins_data(data)
    win_categories = {
        "Massive Wins (>10k)": (10000, np.inf),
        "Big Wins (5–10k)": (5000, 10000),
        "Small Wins (2.5–5k)": (2500, 5000),
        "Close Wins (1–2.5k)": (1000, 2500),
        "Very Close Wins (<1k)": (0, 1000)
    }
elif page_type == "Time Win Margins":
    mask = prepare_time_margins_data(data, False)
    win_categories = {
        "Massive Wins (>5k)": (5000, np.inf),
        "Big Wins (2.5–5k)": (2500, 5000),
        "Small Wins (1.25–2.5k)": (1250, 2500),
        "Close Wins (0.5–1.25k)": (500, 1250),
        "Very Close Wins (<0.5k)": (0, 500)
    }
else:  # Geography Win Margins
    mask = prepare_geography_margins_data(data, False)
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
if remove_pre_survey:
    mask = mask[mask['Date'] >= pd.Timestamp('2026-05-18')].copy()

# Date range limits based on current mask
min_date, max_date = mask["Date"].min(), mask["Date"].max()

# Render remaining Sidebar Controls
with st.sidebar:
    window_length = st.slider(
        "Rolling Average Window (Games):",
        min_value=1,
        max_value=30,
        value=5,
        step=1
    )

    start_date, end_date = st.slider(
        "Select Date Range:",
        min_value=min_date.to_pydatetime(),
        max_value=max_date.to_pydatetime(),
        value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
        format="YYYY-MM-DD"
    )

# Render main area Header
st.markdown(f"## {page_type}")

# Filter data
mask_filtered = mask[(mask["Date"] >= start_date) & (mask["Date"] <= end_date)].copy()

# Calculate rolling and cumulative differences
mask_filtered["Rolling Diff"] = mask_filtered["Score Diff"].rolling(window=window_length, min_periods=1).mean()
mask_filtered["Cumulative Diff"] = mask_filtered["Score Diff"].expanding().mean()

# Add zero-crossing interpolation
mask_filtered = add_zero_crossing_interpolation(mask_filtered, window_length)

# Create and display figure
fig = create_win_margins_figure(mask_filtered, window_length)
st.plotly_chart(fig, use_container_width=True, key="win_margins_chart")

mask_original = mask_filtered[mask_filtered["Date"].dt.time == pd.Timestamp("00:00:00").time()].copy()
mask_original = mask_original.reset_index(drop=True)
st.markdown(create_momentum_timeline(mask_original, window_length), unsafe_allow_html=True)

# Create tables
col1, col2 = st.columns(2)

# Filter to only original midnight points for stats
mask_original = mask_filtered[mask_filtered["Date"].dt.time == pd.Timestamp("00:00:00").time()].copy()
mask_original = mask_original.reset_index(drop=True)  # Reset index for calculate_streaks

with col1:
    st.markdown("### Win Summary")
    win_summary_html = create_win_summary_table(mask_original, win_categories)
    st.markdown(win_summary_html, unsafe_allow_html=True)

with col2:
    st.markdown("### Streaks")
    streaks_html = create_streaks_table(mask_original)
    st.markdown(streaks_html, unsafe_allow_html=True)

