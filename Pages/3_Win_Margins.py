import streamlit as st
import base64
from PIL import Image

def get_base64_image(image_path):
    """
    Encodes an image to a Base64 string, using its detected format (e.g., PNG or JPEG) 
    when saving to the in-memory buffer.

    Args:
        image_path (str): Path to the image file (e.g., "Images/Sarah.jpg").

    Returns:
        str or None: The Base64 encoded string, or None if the file is not found.
    """
    try:
        # Open the image using PIL
        img = Image.open(image_path)
        
        # Determine the saving format. PIL reports 'JPEG' for .jpg/.jpeg files 
        # and 'PNG' for .png files. We use the detected format.
        file_format = img.format if img.format is not None else 'PNG'
        
        buffer = io.BytesIO()
        # Save the image into the buffer using its original format
        img.save(buffer, format=file_format)
        
        # Encode the buffer content to Base64
        return base64.b64encode(buffer.getvalue()).decode()
        
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None
    except Exception as e:
        print(f"An error occurred during image processing: {e}")
        return None

def set_lighter_background_image(base64_string, lightness_level=0.7):
    """
    Injects CSS to set the background image and applies a semi-transparent 
    white overlay using linear-gradient to make the image appear lighter.

    Args:
        base64_string (str): The Base64 encoded image string.
        lightness_level (float): The transparency/lightness of the white overlay (0.0=no overlay, 1.0=pure white).
    """
    if not base64_string:
        st.error("Could not load image for background.")
        return

    # Calculate the alpha value for the RGBA overlay
    # We use lightness_level for the alpha (A) component of RGBA(R, G, B, A)
    # The 'white' color is represented by 255, 255, 255
    rgba_overlay = f"rgba(255, 255, 255, {lightness_level})"

    css = f"""
    <style>
    .stApp {{
        /* Use linear-gradient to layer a semi-transparent white color over the image. */
        background-image: linear-gradient({rgba_overlay}, {rgba_overlay}), 
                          url("data:image/png;base64,{base64_string}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# --- Main Streamlit Script ---
import io

image_file_path = "Images/Sarah.jpg"

# 1. Get the base64 string
base64_img = get_base64_image(image_file_path)

# 2. Inject the CSS with a 70% lightness overlay
# Try adjusting the second argument (e.g., 0.3 for slightly lighter, 0.9 for very light)
set_lighter_background_image(base64_img, lightness_level=0.7)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
from typing import Tuple, List, Dict

# --- Configuration ---
st.set_page_config(page_title="Win Margins Dashboard", layout="wide")

# --- Load CSS ---
css_path = Path("styles.css")
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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

# --- Helper Functions ---
@st.cache_data
def load_data(filepath: str = "./Data/Timeguessr_Stats.csv") -> pd.DataFrame:
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
    
    # Determine x-axis tick positions at the start of each month
    month_starts = pd.date_range(
        start=mask_filtered["Date"].min().replace(day=1),
        end=mask_filtered["Date"].max(),
        freq="MS"  # Month start frequency
    )

    tick_indices = []
    tick_labels = []

    # For each month start, find where it would appear on the x-axis
    for m in month_starts:
        # Find the first date in the data that's in this month (or later)
        dates_in_month = mask_filtered[mask_filtered["Date"] >= m]
        if not dates_in_month.empty:
            first_date_idx = dates_in_month.index[0]
            tick_indices.append(mask_filtered.loc[first_date_idx, "x_index"])
            tick_labels.append(m.strftime("%b %Y"))

    
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
        tickangle=-45
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
        width: fit-content !important;          /* only as wide as text */
        min-width: 0 !important;
        overflow: visible !important;           /* prevent clipping */
    }

    /* Style visible select text */
    div[data-baseweb="select"] > div > div {
        height: auto !important;                /* allow natural height */
        min-height: 90px !important;            /* taller block */
        display: flex !important;
        align-items: flex-end !important;       /* align text visually bottom */
        padding: 8px 4px 14px 4px !important;   /* extra bottom padding */
        font-size: 46px !important;             /* large title font */
        font-weight: 800 !important;
        color: #db5049 !important;              /* your red */
        text-align: left !important;
        line-height: 1.2em !important;          /* prevent clipping */
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

page_type = st.selectbox(
    "",
    options=["Total Win Margins", "Time Win Margins", "Geography Win Margins"],
    index=0,
    key="page_selector",
)

# Load data
data = load_data()

# Conditional toggle for Time and Geography Margins
remove_estimated = False
if page_type in ["Time Win Margins", "Geography Win Margins"]:
    remove_estimated = st.toggle("Remove Estimated Scores", value=False, key="remove_estimated_toggle")

# Prepare data and win categories based on page type
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
    mask = prepare_time_margins_data(data, remove_estimated)
    win_categories = {
        "Massive Wins (>5k)": (5000, np.inf),
        "Big Wins (2.5–5k)": (2500, 5000),
        "Small Wins (1.25–2.5k)": (1250, 2500),
        "Close Wins (0.5–1.25k)": (500, 1250),
        "Very Close Wins (<0.5k)": (0, 500)
    }
else:  # Geography Win Margins
    mask = prepare_geography_margins_data(data, remove_estimated)
    win_categories = {
        "Massive Wins (>5k)": (5000, np.inf),
        "Big Wins (2.5–5k)": (2500, 5000),
        "Small Wins (1.25–2.5k)": (1250, 2500),
        "Close Wins (0.5–1.25k)": (500, 1250),
        "Very Close Wins (<0.5k)": (0, 500)
    }

# Date range
min_date, max_date = mask["Date"].min(), mask["Date"].max()

# Controls
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

st.audio("./Images/Sarah.mp3", start_time=0, autoplay=True)