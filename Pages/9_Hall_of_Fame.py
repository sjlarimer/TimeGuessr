import streamlit as st
import pandas as pd
from PIL import Image

# --- Configuration ---
st.set_page_config(page_title="Hall of Fame", layout="wide")

# --- Load Global CSS ---
try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# --- Custom Styling ---
st.markdown(
    """
    <style>
        /* Global Font & Colors */
        .stMarkdown p, label, h1, h2, h3, h4, h5, h6 {
            font-family: 'Poppins', sans-serif !important;
        }
        h1, h2, h3 {
            color: #db5049 !important;
        }
        
        /* Trophy Cabinet Container */
        .cabinet-container {
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            border: 1px solid rgba(0,0,0,0.05);
            min-height: 400px;
        }
        
        .cabinet-header {
            font-family: 'Poppins', sans-serif;
            font-weight: 800;
            font-size: 2rem;
            text-align: center;
            margin-bottom: 25px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 2px solid rgba(0,0,0,0.1);
            padding-bottom: 15px;
        }

        /* Grid for Trophies */
        .trophy-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }

        /* Individual Trophy Card */
        .trophy-card {
            background: rgba(255, 255, 255, 0.7);
            border-radius: 10px;
            padding: 15px 10px;
            text-align: center;
            transition: transform 0.2s, background 0.2s;
            border: 1px solid rgba(0,0,0,0.05);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 160px;
            cursor: default;
            position: relative;
        }
        
        .trophy-card:hover {
            transform: translateY(-3px);
            background: rgba(255, 255, 255, 0.95);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        /* Yearly Trophy Styling */
        .trophy-card.yearly {
            background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(245,245,255,0.85));
            border: 2px solid rgba(0,0,0,0.08);
        }
        
        /* Darker background for ties */
        .trophy-card.tie {
            background: rgba(230, 230, 230, 0.6);
            border: 1px solid rgba(0,0,0,0.15);
        }
        .trophy-card.tie:hover {
            background: rgba(230, 230, 230, 0.9);
        }

        /* Golden Rim for Dominant Wins (>= 2/3 Days) */
        .trophy-card.gold-rim {
            border: 3px solid #FFD700 !important;
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
            background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,250,230,0.95) 100%);
        }
        .trophy-card.gold-rim:hover {
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.6);
            transform: translateY(-3px) scale(1.02);
        }

        /* Silver Rim for High Score Margin (>= 10%) */
        .trophy-card.silver-rim {
            border: 3px solid #C0C0C0 !important;
            box-shadow: 0 0 15px rgba(192, 192, 192, 0.4);
            background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(245,245,250,0.95) 100%);
        }
        .trophy-card.silver-rim:hover {
            box-shadow: 0 0 20px rgba(192, 192, 192, 0.6);
            transform: translateY(-3px) scale(1.02);
        }

        .trophy-icon {
            font-size: 3rem;
            margin-bottom: 10px;
            filter: drop-shadow(0 2px 2px rgba(0,0,0,0.15));
            line-height: 1;
        }

        .trophy-title {
            font-weight: 700;
            font-size: 0.9rem;
            color: #333;
            margin-bottom: 5px;
            line-height: 1.2;
        }

        .trophy-desc {
            font-size: 0.75rem;
            color: #666;
            line-height: 1.2;
        }
        
        /* Player Specific Colors */
        .michael-theme {
            background-color: #dde5eb; /* Light Blue */
        }
        .michael-text {
            color: #221e8f;
        }
        
        .sarah-theme {
            background-color: #edd3df; /* Light Pink */
        }
        .sarah-text {
            color: #8a005c;
        }

        /* Sidebar Styling (Consistency) */
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3 {
            color: white !important;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown p {
            color: #696761 !important;
        }
        
        /* Section Dividers */
        .trophy-divider {
            width: 100%;
            height: 1px;
            background: rgba(0,0,0,0.1);
            margin: 20px 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .trophy-divider span {
            background: rgba(255,255,255,0.8);
            padding: 0 10px;
            color: #888;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Helper Functions ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("./Data/Timeguessr_Stats.csv")
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Helper to clean numeric columns
        def clean_col(col_name):
            if col_name in df.columns:
                return pd.to_numeric(df[col_name], errors='coerce').fillna(0)
            return pd.Series(0, index=df.index)

        # Totals
        df['Michael Total Score'] = clean_col('Michael Total Score')
        df['Sarah Total Score'] = clean_col('Sarah Total Score')
        
        # Component Scores (Min/Max)
        df['Michael Geography Score (Min)'] = clean_col('Michael Geography Score (Min)')
        df['Michael Geography Score (Max)'] = clean_col('Michael Geography Score (Max)')
        df['Sarah Geography Score (Min)'] = clean_col('Sarah Geography Score (Min)')
        df['Sarah Geography Score (Max)'] = clean_col('Sarah Geography Score (Max)')
        
        df['Michael Time Score (Min)'] = clean_col('Michael Time Score (Min)')
        df['Michael Time Score (Max)'] = clean_col('Michael Time Score (Max)')
        df['Sarah Time Score (Min)'] = clean_col('Sarah Time Score (Min)')
        df['Sarah Time Score (Max)'] = clean_col('Sarah Time Score (Max)')

        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def check_silver(winner_score, loser_score):
    """Helper to check Silver Rim (Score Margin >= 10%)"""
    if loser_score == 0: return True # Infinite margin
    return (winner_score - loser_score) / loser_score >= 0.10

def generate_trophies_for_period(row, daily_data_for_period, period_label, is_yearly=False):
    """Generates the list of trophies for a specific period (Month, Quarter, or Year)."""
    t_m = []
    t_s = []
    
    total_days = row['DaysCount']
    dominance_threshold = total_days * (2/3)

    # --- 1. Total Score Trophy (🌟) ---
    m_total = row['Michael Total Score']
    s_total = row['Sarah Total Score']
    
    if m_total > s_total:
        is_silver = check_silver(m_total, s_total)
        t_m.append({"icon": "🌟", "title": period_label, "desc": f"Total: {int(m_total):,}<br>Won by {int(m_total-s_total):,}", "is_tie": False, "is_silver": is_silver, "is_yearly": is_yearly})
    elif s_total > m_total:
        is_silver = check_silver(s_total, m_total)
        t_s.append({"icon": "🌟", "title": period_label, "desc": f"Total: {int(s_total):,}<br>Won by {int(s_total-m_total):,}", "is_tie": False, "is_silver": is_silver, "is_yearly": is_yearly})
    else:
        t_m.append({"icon": "🌟", "title": period_label, "desc": f"Tie: {int(m_total):,}", "is_tie": True, "is_yearly": is_yearly})
        t_s.append({"icon": "🌟", "title": period_label, "desc": f"Tie: {int(s_total):,}", "is_tie": True, "is_yearly": is_yearly})

    # --- 2. Total Days Won Trophy (🏆) ---
    m_days = row['M_Total_Win']
    s_days = row['S_Total_Win']
    
    if m_days > s_days:
        is_gold = m_days >= dominance_threshold
        t_m.append({"icon": "🏆", "title": period_label, "desc": f"Won {int(m_days)} days<br>(vs {int(s_days)})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly})
    elif s_days > m_days:
        is_gold = s_days >= dominance_threshold
        t_s.append({"icon": "🏆", "title": period_label, "desc": f"Won {int(s_days)} days<br>(vs {int(m_days)})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly})
    else:
        t_m.append({"icon": "🏆", "title": period_label, "desc": f"Days Tied: {int(m_days)}", "is_tie": True, "is_yearly": is_yearly})
        t_s.append({"icon": "🏆", "title": period_label, "desc": f"Days Tied: {int(s_days)}", "is_tie": True, "is_yearly": is_yearly})

    # --- 3. Geography Score Trophy (🗺️) ---
    m_geo = row['M_Geo_Row']
    s_geo = row['S_Geo_Row']
    
    if m_geo > s_geo:
        is_silver = check_silver(m_geo, s_geo)
        t_m.append({"icon": "🗺️", "title": period_label, "desc": f"Geo: {int(m_geo):,}<br>Won by {int(m_geo-s_geo):,}", "is_tie": False, "is_silver": is_silver, "is_yearly": is_yearly})
    elif s_geo > m_geo:
        is_silver = check_silver(s_geo, m_geo)
        t_s.append({"icon": "🗺️", "title": period_label, "desc": f"Geo: {int(s_geo):,}<br>Won by {int(s_geo-m_geo):,}", "is_tie": False, "is_silver": is_silver, "is_yearly": is_yearly})
    else:
        t_m.append({"icon": "🗺️", "title": period_label, "desc": f"Tie: {int(m_geo):,}", "is_tie": True, "is_yearly": is_yearly})
        t_s.append({"icon": "🗺️", "title": period_label, "desc": f"Tie: {int(s_geo):,}", "is_tie": True, "is_yearly": is_yearly})

    # --- 4. Geography Days Won Trophy (🌍) ---
    m_geo_days = row['M_Geo_Win']
    s_geo_days = row['S_Geo_Win']

    if m_geo_days > s_geo_days:
        is_gold = m_geo_days >= dominance_threshold
        t_m.append({"icon": "🌍", "title": period_label, "desc": f"Geo Days: {int(m_geo_days)}<br>(vs {int(s_geo_days)})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly})
    elif s_geo_days > m_geo_days:
        is_gold = s_geo_days >= dominance_threshold
        t_s.append({"icon": "🌍", "title": period_label, "desc": f"Geo Days: {int(s_geo_days)}<br>(vs {int(m_geo_days)})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly})
    else:
        t_m.append({"icon": "🌍", "title": period_label, "desc": f"Geo Days Tied: {int(m_geo_days)}", "is_tie": True, "is_yearly": is_yearly})
        t_s.append({"icon": "🌍", "title": period_label, "desc": f"Geo Days Tied: {int(s_geo_days)}", "is_tie": True, "is_yearly": is_yearly})

    # --- 5. Time Score Trophy (🕰️) ---
    m_time = row['M_Time_Row']
    s_time = row['S_Time_Row']
    
    if m_time > s_time:
        is_silver = check_silver(m_time, s_time)
        t_m.append({"icon": "🕰️", "title": period_label, "desc": f"Time: {int(m_time):,}<br>Won by {int(m_time-s_time):,}", "is_tie": False, "is_silver": is_silver, "is_yearly": is_yearly})
    elif s_time > m_time:
        is_silver = check_silver(s_time, m_time)
        t_s.append({"icon": "🕰️", "title": period_label, "desc": f"Time: {int(s_time):,}<br>Won by {int(s_time-m_time):,}", "is_tie": False, "is_silver": is_silver, "is_yearly": is_yearly})
    else:
        t_m.append({"icon": "🕰️", "title": period_label, "desc": f"Tie: {int(m_time):,}", "is_tie": True, "is_yearly": is_yearly})
        t_s.append({"icon": "🕰️", "title": period_label, "desc": f"Tie: {int(s_time):,}", "is_tie": True, "is_yearly": is_yearly})

    # --- 6. Time Days Won Trophy (📆) ---
    m_time_days = row['M_Time_Win']
    s_time_days = row['S_Time_Win']

    if m_time_days > s_time_days:
        is_gold = m_time_days >= dominance_threshold
        t_m.append({"icon": "📆", "title": period_label, "desc": f"Time Days: {int(m_time_days)}<br>(vs {int(s_time_days)})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly})
    elif s_time_days > m_time_days:
        is_gold = s_time_days >= dominance_threshold
        t_s.append({"icon": "📆", "title": period_label, "desc": f"Time Days: {int(s_time_days)}<br>(vs {int(m_time_days)})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly})
    else:
        t_m.append({"icon": "📆", "title": period_label, "desc": f"Time Days Tied: {int(m_time_days)}", "is_tie": True, "is_yearly": is_yearly})
        t_s.append({"icon": "📆", "title": period_label, "desc": f"Time Days Tied: {int(s_time_days)}", "is_tie": True, "is_yearly": is_yearly})

    # --- 7. Highest Daily Total Score (🚀) ---
    if not daily_data_for_period.empty:
        m_high_total = daily_data_for_period['Michael Total Score'].max()
        s_high_total = daily_data_for_period['Sarah Total Score'].max()
        
        m_high_date_row = daily_data_for_period.loc[daily_data_for_period['Michael Total Score'].idxmax()]
        s_high_date_row = daily_data_for_period.loc[daily_data_for_period['Sarah Total Score'].idxmax()]
        
        m_date_str = m_high_date_row['Date'].strftime('%b %d')
        s_date_str = s_high_date_row['Date'].strftime('%b %d')

        if m_high_total > s_high_total:
            margin = int(m_high_total - s_high_total)
            is_silver = check_silver(m_high_total, s_high_total)
            t_m.append({"icon": "🚀", "title": period_label, "desc": f"High: {int(m_high_total):,}<br>+{margin:,} ({m_date_str})", "is_tie": False, "is_silver": is_silver, "is_yearly": is_yearly})
        elif s_high_total > m_high_total:
            margin = int(s_high_total - m_high_total)
            is_silver = check_silver(s_high_total, m_high_total)
            t_s.append({"icon": "🚀", "title": period_label, "desc": f"High: {int(s_high_total):,}<br>+{margin:,} ({s_date_str})", "is_tie": False, "is_silver": is_silver, "is_yearly": is_yearly})
        else:
            t_m.append({"icon": "🚀", "title": period_label, "desc": f"Tie High: {int(m_high_total):,}", "is_tie": True, "is_yearly": is_yearly})
            t_s.append({"icon": "🚀", "title": period_label, "desc": f"Tie High: {int(s_high_total):,}", "is_tie": True, "is_yearly": is_yearly})

        # --- 8. Highest Daily Geography Score (🏔️) ---
        m_high_geo = daily_data_for_period['M_Geo_Row'].max()
        s_high_geo = daily_data_for_period['S_Geo_Row'].max()
        
        m_high_geo_date = daily_data_for_period.loc[daily_data_for_period['M_Geo_Row'].idxmax()]['Date'].strftime('%b %d')
        s_high_geo_date = daily_data_for_period.loc[daily_data_for_period['S_Geo_Row'].idxmax()]['Date'].strftime('%b %d')

        if m_high_geo > s_high_geo:
            margin = int(m_high_geo - s_high_geo)
            is_silver = check_silver(m_high_geo, s_high_geo)
            t_m.append({"icon": "🏔️", "title": period_label, "desc": f"High Geo: {int(m_high_geo):,}<br>+{margin:,} ({m_high_geo_date})", "is_tie": False, "is_silver": is_silver, "is_yearly": is_yearly})
        elif s_high_geo > m_high_geo:
            margin = int(s_high_geo - m_high_geo)
            is_silver = check_silver(s_high_geo, m_high_geo)
            t_s.append({"icon": "🏔️", "title": period_label, "desc": f"High Geo: {int(s_high_geo):,}<br>+{margin:,} ({s_high_geo_date})", "is_tie": False, "is_silver": is_silver, "is_yearly": is_yearly})
        else:
            t_m.append({"icon": "🏔️", "title": period_label, "desc": f"Tie High Geo: {int(m_high_geo):,}", "is_tie": True, "is_yearly": is_yearly})
            t_s.append({"icon": "🏔️", "title": period_label, "desc": f"Tie High Geo: {int(s_high_geo):,}", "is_tie": True, "is_yearly": is_yearly})

        # --- 9. Highest Daily Time Score (⏱️) ---
        m_high_time = daily_data_for_period['M_Time_Row'].max()
        s_high_time = daily_data_for_period['S_Time_Row'].max()
        
        m_high_time_date = daily_data_for_period.loc[daily_data_for_period['M_Time_Row'].idxmax()]['Date'].strftime('%b %d')
        s_high_time_date = daily_data_for_period.loc[daily_data_for_period['S_Time_Row'].idxmax()]['Date'].strftime('%b %d')

        if m_high_time > s_high_time:
            margin = int(m_high_time - s_high_time)
            is_silver = check_silver(m_high_time, s_high_time)
            t_m.append({"icon": "⏱️", "title": period_label, "desc": f"High Time: {int(m_high_time):,}<br>+{margin:,} ({m_high_time_date})", "is_tie": False, "is_silver": is_silver, "is_yearly": is_yearly})
        elif s_high_time > m_high_time:
            margin = int(s_high_time - m_high_time)
            is_silver = check_silver(s_high_time, m_high_time)
            t_s.append({"icon": "⏱️", "title": period_label, "desc": f"High Time: {int(s_high_time):,}<br>+{margin:,} ({s_high_time_date})", "is_tie": False, "is_silver": is_silver, "is_yearly": is_yearly})
        else:
            t_m.append({"icon": "⏱️", "title": period_label, "desc": f"Tie High Time: {int(m_high_time):,}", "is_tie": True, "is_yearly": is_yearly})
            t_s.append({"icon": "⏱️", "title": period_label, "desc": f"Tie High Time: {int(s_high_time):,}", "is_tie": True, "is_yearly": is_yearly})

    # --- 10. Most Perfect Rounds (Total) 🟩 ---
    m_perfect_total = row['M_Total_Perf']
    s_perfect_total = row['S_Total_Perf']

    if m_perfect_total > 0 or s_perfect_total > 0:
        if m_perfect_total > s_perfect_total:
            diff = int(m_perfect_total - s_perfect_total)
            t_m.append({"icon": "🟩", "title": period_label, "desc": f"Perfect Rounds: {int(m_perfect_total)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly})
        elif s_perfect_total > m_perfect_total:
            diff = int(s_perfect_total - m_perfect_total)
            t_s.append({"icon": "🟩", "title": period_label, "desc": f"Perfect Rounds: {int(s_perfect_total)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly})
        else:
            t_m.append({"icon": "🟩", "title": period_label, "desc": f"Tie Perfect: {int(m_perfect_total)}", "is_tie": True, "is_yearly": is_yearly})
            t_s.append({"icon": "🟩", "title": period_label, "desc": f"Tie Perfect: {int(s_perfect_total)}", "is_tie": True, "is_yearly": is_yearly})

    # --- 11. Most Perfect Geo Rounds 🌍🟩 ---
    m_perfect_geo = row['M_Geo_Perf']
    s_perfect_geo = row['S_Geo_Perf']

    if m_perfect_geo > 0 or s_perfect_geo > 0:
        if m_perfect_geo > s_perfect_geo:
            diff = int(m_perfect_geo - s_perfect_geo)
            t_m.append({"icon": "🌍🟩", "title": period_label, "desc": f"Perfect Geo: {int(m_perfect_geo)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly})
        elif s_perfect_geo > m_perfect_geo:
            diff = int(s_perfect_geo - m_perfect_geo)
            t_s.append({"icon": "🌍🟩", "title": period_label, "desc": f"Perfect Geo: {int(s_perfect_geo)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly})
        else:
            t_m.append({"icon": "🌍🟩", "title": period_label, "desc": f"Tie Perf Geo: {int(m_perfect_geo)}", "is_tie": True, "is_yearly": is_yearly})
            t_s.append({"icon": "🌍🟩", "title": period_label, "desc": f"Tie Perf Geo: {int(s_perfect_geo)}", "is_tie": True, "is_yearly": is_yearly})

    # --- 12. Most Perfect Time Rounds 📆🟩 ---
    m_perfect_time = row['M_Time_Perf']
    s_perfect_time = row['S_Time_Perf']

    if m_perfect_time > 0 or s_perfect_time > 0:
        if m_perfect_time > s_perfect_time:
            diff = int(m_perfect_time - s_perfect_time)
            t_m.append({"icon": "📆🟩", "title": period_label, "desc": f"Perfect Time: {int(m_perfect_time)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly})
        elif s_perfect_time > m_perfect_time:
            diff = int(s_perfect_time - m_perfect_time)
            t_s.append({"icon": "📆🟩", "title": period_label, "desc": f"Perfect Time: {int(s_perfect_time)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly})
        else:
            t_m.append({"icon": "📆🟩", "title": period_label, "desc": f"Tie Perf Time: {int(m_perfect_time)}", "is_tie": True, "is_yearly": is_yearly})
            t_s.append({"icon": "📆🟩", "title": period_label, "desc": f"Tie Perf Time: {int(s_perfect_time)}", "is_tie": True, "is_yearly": is_yearly})

    return t_m, t_s

def calculate_trophies(df):
    """Calculates Monthly, Quarterly, and Yearly trophies."""
    if df is None or df.empty:
        return [], [], [], [], [], []

    # --- Step 1: Identify Valid Dates (Mutual Participation) ---
    daily_check = df.groupby('Date')[['Michael Total Score', 'Sarah Total Score']].first()
    valid_dates = daily_check[
        (daily_check['Michael Total Score'] > 0) & 
        (daily_check['Sarah Total Score'] > 0)
    ].index

    df_valid = df[df['Date'].isin(valid_dates)].copy()
    if df_valid.empty:
        return [], [], [], [], [], []

    # --- Step 2: Calculate Row-Level & Daily Stats (Base Data) ---
    df_valid['M_Geo_Row'] = (df_valid['Michael Geography Score (Min)'] + df_valid['Michael Geography Score (Max)']) / 2
    df_valid['S_Geo_Row'] = (df_valid['Sarah Geography Score (Min)'] + df_valid['Sarah Geography Score (Max)']) / 2
    df_valid['M_Time_Row'] = (df_valid['Michael Time Score (Min)'] + df_valid['Michael Time Score (Max)']) / 2
    df_valid['S_Time_Row'] = (df_valid['Sarah Time Score (Min)'] + df_valid['Sarah Time Score (Max)']) / 2

    # Calculate Perfect Rounds at Row Level
    df_valid['M_Geo_Perf'] = (df_valid['M_Geo_Row'] == 5000).astype(int)
    df_valid['S_Geo_Perf'] = (df_valid['S_Geo_Row'] == 5000).astype(int)
    df_valid['M_Time_Perf'] = (df_valid['M_Time_Row'] == 5000).astype(int)
    df_valid['S_Time_Perf'] = (df_valid['S_Time_Row'] == 5000).astype(int)
    df_valid['M_Total_Perf'] = ((df_valid['M_Geo_Row'] == 5000) & (df_valid['M_Time_Row'] == 5000)).astype(int)
    df_valid['S_Total_Perf'] = ((df_valid['S_Geo_Row'] == 5000) & (df_valid['S_Time_Row'] == 5000)).astype(int)

    # Aggregate to Daily
    daily_stats = df_valid.groupby('Date').agg({
        'Michael Total Score': 'first',
        'Sarah Total Score': 'first',
        'M_Geo_Row': 'sum',
        'S_Geo_Row': 'sum',
        'M_Time_Row': 'sum',
        'S_Time_Row': 'sum',
        'M_Geo_Perf': 'sum',
        'S_Geo_Perf': 'sum',
        'M_Time_Perf': 'sum',
        'S_Time_Perf': 'sum',
        'M_Total_Perf': 'sum',
        'S_Total_Perf': 'sum'
    }).reset_index()

    # Calculate Wins
    daily_stats['M_Total_Win'] = (daily_stats['Michael Total Score'] > daily_stats['Sarah Total Score']).astype(int)
    daily_stats['S_Total_Win'] = (daily_stats['Sarah Total Score'] > daily_stats['Michael Total Score']).astype(int)
    daily_stats['M_Geo_Win'] = (daily_stats['M_Geo_Row'] > daily_stats['S_Geo_Row']).astype(int)
    daily_stats['S_Geo_Win'] = (daily_stats['S_Geo_Row'] > daily_stats['M_Geo_Row']).astype(int)
    daily_stats['M_Time_Win'] = (daily_stats['M_Time_Row'] > daily_stats['S_Time_Row']).astype(int)
    daily_stats['S_Time_Win'] = (daily_stats['S_Time_Row'] > daily_stats['M_Time_Row']).astype(int)

    yearly_m, yearly_s = [], []
    quarterly_m, quarterly_s = [], []
    monthly_m, monthly_s = [], []

    # --- YEARLY TROPHIES ---
    daily_stats['Year'] = daily_stats['Date'].dt.year
    yearly_agg = daily_stats.groupby('Year').agg({
        'Michael Total Score': 'sum',
        'Sarah Total Score': 'sum',
        'M_Geo_Row': 'sum',
        'S_Geo_Row': 'sum',
        'M_Time_Row': 'sum',
        'S_Time_Row': 'sum',
        'M_Total_Win': 'sum',
        'S_Total_Win': 'sum',
        'M_Geo_Win': 'sum',
        'S_Geo_Win': 'sum',
        'M_Time_Win': 'sum',
        'S_Time_Win': 'sum',
        'M_Geo_Perf': 'sum',
        'S_Geo_Perf': 'sum',
        'M_Time_Perf': 'sum',
        'S_Time_Perf': 'sum',
        'M_Total_Perf': 'sum',
        'S_Total_Perf': 'sum',
        'Date': 'count'
    }).reset_index()
    yearly_agg.rename(columns={'Date': 'DaysCount'}, inplace=True)
    yearly_agg = yearly_agg.sort_values('Year', ascending=False)

    for _, row in yearly_agg.iterrows():
        year_val = row['Year']
        daily_for_year = daily_stats[daily_stats['Year'] == year_val]
        
        t_m, t_s = generate_trophies_for_period(row, daily_for_year, str(int(year_val)), is_yearly=True)
        yearly_m.extend(t_m)
        yearly_s.extend(t_s)

    # --- QUARTERLY TROPHIES ---
    daily_stats['Quarter'] = daily_stats['Date'].dt.to_period('Q')
    quarterly_agg = daily_stats.groupby('Quarter').agg({
        'Michael Total Score': 'sum',
        'Sarah Total Score': 'sum',
        'M_Geo_Row': 'sum',
        'S_Geo_Row': 'sum',
        'M_Time_Row': 'sum',
        'S_Time_Row': 'sum',
        'M_Total_Win': 'sum',
        'S_Total_Win': 'sum',
        'M_Geo_Win': 'sum',
        'S_Geo_Win': 'sum',
        'M_Time_Win': 'sum',
        'S_Time_Win': 'sum',
        'M_Geo_Perf': 'sum',
        'S_Geo_Perf': 'sum',
        'M_Time_Perf': 'sum',
        'S_Time_Perf': 'sum',
        'M_Total_Perf': 'sum',
        'S_Total_Perf': 'sum',
        'Date': 'count'
    }).reset_index()
    quarterly_agg.rename(columns={'Date': 'DaysCount'}, inplace=True)
    quarterly_agg = quarterly_agg.sort_values('Quarter', ascending=False)

    for _, row in quarterly_agg.iterrows():
        q_period = row['Quarter']
        daily_for_q = daily_stats[daily_stats['Quarter'] == q_period]
        q_label = f"Q{q_period.quarter} {q_period.year}"
        
        t_m, t_s = generate_trophies_for_period(row, daily_for_q, q_label, is_yearly=False)
        quarterly_m.extend(t_m)
        quarterly_s.extend(t_s)

    # --- MONTHLY TROPHIES ---
    daily_stats['MonthPeriod'] = daily_stats['Date'].dt.to_period('M')
    monthly_agg = daily_stats.groupby('MonthPeriod').agg({
        'Michael Total Score': 'sum',
        'Sarah Total Score': 'sum',
        'M_Geo_Row': 'sum',
        'S_Geo_Row': 'sum',
        'M_Time_Row': 'sum',
        'S_Time_Row': 'sum',
        'M_Total_Win': 'sum',
        'S_Total_Win': 'sum',
        'M_Geo_Win': 'sum',
        'S_Geo_Win': 'sum',
        'M_Time_Win': 'sum',
        'S_Time_Win': 'sum',
        'M_Geo_Perf': 'sum',
        'S_Geo_Perf': 'sum',
        'M_Time_Perf': 'sum',
        'S_Time_Perf': 'sum',
        'M_Total_Perf': 'sum',
        'S_Total_Perf': 'sum',
        'Date': 'count'
    }).reset_index()
    monthly_agg.rename(columns={'Date': 'DaysCount'}, inplace=True)
    monthly_agg['MonthLabel'] = monthly_agg['MonthPeriod'].dt.strftime('%B %Y')
    monthly_agg = monthly_agg.sort_values('MonthPeriod', ascending=False)

    for _, row in monthly_agg.iterrows():
        month_period = row['MonthPeriod']
        daily_for_month = daily_stats[daily_stats['MonthPeriod'] == month_period]
        
        t_m, t_s = generate_trophies_for_period(row, daily_for_month, row['MonthLabel'], is_yearly=False)
        monthly_m.extend(t_m)
        monthly_s.extend(t_s)

    return yearly_m, quarterly_m, monthly_m, yearly_s, quarterly_s, monthly_s

def create_trophy_html(icon, title, desc, is_tie=False, is_gold=False, is_silver=False, is_yearly=False):
    tie_class = " tie" if is_tie else ""
    gold_class = " gold-rim" if is_gold else ""
    silver_class = " silver-rim" if is_silver else ""
    yearly_class = " yearly" if is_yearly else ""
    return f'<div class="trophy-card{tie_class}{gold_class}{silver_class}{yearly_class}"><div class="trophy-icon">{icon}</div><div class="trophy-title">{title}</div><div class="trophy-desc">{desc}</div></div>'

# --- Header ---
st.title("Hall of Fame")
st.markdown("### Trophy Cabinet")
st.markdown("<br>", unsafe_allow_html=True)

# --- Data Loading & Processing ---
df = load_data()
yearly_m, quarterly_m, monthly_m, yearly_s, quarterly_s, monthly_s = calculate_trophies(df)

# --- Layout ---
col1, col2 = st.columns(2, gap="large")

# --- Helper to create separator ---
def get_separator(text):
    return f"""
    <div class="trophy-divider">
        <span>{text}</span>
    </div>
    """

# --- Michael's Cabinet ---
with col1:
    m_html = ""
    has_content = False
    
    if yearly_m:
         m_html += get_separator("Yearly")
         m_html += '<div class="trophy-grid">' + "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t.get('is_gold', False), t.get('is_silver', False), t.get('is_yearly', False)) for t in yearly_m]) + '</div>'
         has_content = True
         
    if quarterly_m:
         if has_content: m_html += get_separator("Quarterly")
         m_html += '<div class="trophy-grid">' + "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t.get('is_gold', False), t.get('is_silver', False), t.get('is_yearly', False)) for t in quarterly_m]) + '</div>'
         has_content = True

    if monthly_m:
         if has_content: m_html += get_separator("Monthly")
         m_html += '<div class="trophy-grid">' + "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t.get('is_gold', False), t.get('is_silver', False), t.get('is_yearly', False)) for t in monthly_m]) + '</div>'
         has_content = True
    
    if not has_content:
        m_html = "<div style='text-align:center; color:#666; width:100%; padding: 20px;'>No trophies yet.</div>"
    
    st.markdown(
        f'<div class="cabinet-container michael-theme"><div class="cabinet-header michael-text">Michael</div>{m_html}</div>',
        unsafe_allow_html=True
    )

# --- Sarah's Cabinet ---
with col2:
    s_html = ""
    has_content = False
    
    if yearly_s:
         s_html += get_separator("Yearly")
         s_html += '<div class="trophy-grid">' + "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t.get('is_gold', False), t.get('is_silver', False), t.get('is_yearly', False)) for t in yearly_s]) + '</div>'
         has_content = True
         
    if quarterly_s:
         if has_content: s_html += get_separator("Quarterly")
         s_html += '<div class="trophy-grid">' + "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t.get('is_gold', False), t.get('is_silver', False), t.get('is_yearly', False)) for t in quarterly_s]) + '</div>'
         has_content = True

    if monthly_s:
         if has_content: s_html += get_separator("Monthly")
         s_html += '<div class="trophy-grid">' + "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t.get('is_gold', False), t.get('is_silver', False), t.get('is_yearly', False)) for t in monthly_s]) + '</div>'
         has_content = True
    
    if not has_content:
        s_html = "<div style='text-align:center; color:#666; width:100%; padding: 20px;'>No trophies yet.</div>"
    
    st.markdown(
        f'<div class="cabinet-container sarah-theme"><div class="cabinet-header sarah-text">Sarah</div>{s_html}</div>',
        unsafe_allow_html=True
    )