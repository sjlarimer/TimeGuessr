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
        .stMarkdown p, label, h1, h2, h3, h4, h5, h6, .stTabs button {
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
            min-height: 250px; /* Reduced min-height for split cabinets */
        }
        
        .cabinet-header {
            font-family: 'Poppins', sans-serif;
            font-weight: 800;
            font-size: 1.5rem; /* Slightly smaller for tabbed view */
            text-align: center;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 2px solid rgba(0,0,0,0.1);
            padding-bottom: 10px;
        }

        /* Grid for Trophies */
        .trophy-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); /* Responsive grid */
            gap: 12px;
        }

        /* Individual Trophy Card */
        .trophy-card {
            background: rgba(255, 255, 255, 0.7);
            border-radius: 10px;
            padding: 10px 5px;
            text-align: center;
            transition: transform 0.2s, background 0.2s;
            border: 1px solid rgba(0,0,0,0.05);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 140px;
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

        /* Golden Rim for Dominant Wins OR High Margins */
        .trophy-card.gold-rim {
            border: 3px solid #FFD700 !important;
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
            background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,250,230,0.95) 100%);
        }
        .trophy-card.gold-rim:hover {
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.6);
            transform: translateY(-3px) scale(1.02);
        }

        /* Ongoing / Live Period Styling */
        .trophy-card.ongoing::after {
            content: "LIVE";
            position: absolute;
            top: 6px;
            right: 6px;
            font-size: 9px;
            font-weight: 800;
            color: white;
            background-color: #db5049; /* Red Badge to match headers */
            padding: 2px 5px;
            border-radius: 4px;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            animation: pulse-live 2.5s infinite;
            z-index: 10;
        }
        
        @keyframes pulse-live {
            0% { opacity: 0.85; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.05); }
            100% { opacity: 0.85; transform: scale(1); }
        }

        .trophy-icon {
            font-size: 2.5rem;
            margin-bottom: 8px;
            filter: drop-shadow(0 2px 2px rgba(0,0,0,0.15));
            line-height: 1;
        }

        .trophy-title {
            font-weight: 700;
            font-size: 0.8rem;
            color: #333;
            margin-bottom: 4px;
            line-height: 1.2;
        }

        .trophy-desc {
            font-size: 0.7rem;
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
            margin: 15px 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .trophy-divider span {
            background: rgba(255,255,255,0.8);
            padding: 0 10px;
            color: #888;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-radius: 4px;
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
        # In case file is missing for first run
        st.error(f"Error loading data: {e}")
        return None

def check_gold_margin(winner_score, loser_score):
    """Helper to check Gold Rim Criteria (Score Margin >= 10%)"""
    if loser_score == 0: return True # Infinite margin
    return (winner_score - loser_score) / loser_score >= 0.10

def generate_trophies_for_period(row, daily_data_for_period, period_label, is_yearly=False, is_ongoing=False):
    """Generates the list of trophies for a specific period (Month, Quarter, or Year)."""
    t_m = []
    t_s = []
    
    total_days = row['DaysCount']
    dominance_threshold = total_days * (2/3)

    # --- CATEGORY 1: TOTAL / OVERALL ---

    # 1. Total Score Trophy (🌟)
    m_total = row['Michael Total Score']
    s_total = row['Sarah Total Score']
    
    if m_total > s_total:
        is_gold = check_gold_margin(m_total, s_total)
        t_m.append({"icon": "🌟", "title": period_label, "desc": f"Total: {int(m_total):,}<br>Won by {int(m_total-s_total):,}", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
    elif s_total > m_total:
        is_gold = check_gold_margin(s_total, m_total)
        t_s.append({"icon": "🌟", "title": period_label, "desc": f"Total: {int(s_total):,}<br>Won by {int(s_total-m_total):,}", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
    else:
        t_m.append({"icon": "🌟", "title": period_label, "desc": f"Tie: {int(m_total):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
        t_s.append({"icon": "🌟", "title": period_label, "desc": f"Tie: {int(s_total):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})

    # 2. Total Days Won Trophy (🏆)
    m_days = row['M_Total_Win']
    s_days = row['S_Total_Win']
    
    if m_days > s_days:
        is_gold = m_days >= dominance_threshold
        t_m.append({"icon": "🏆", "title": period_label, "desc": f"Won {int(m_days)} days<br>(vs {int(s_days)})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
    elif s_days > m_days:
        is_gold = s_days >= dominance_threshold
        t_s.append({"icon": "🏆", "title": period_label, "desc": f"Won {int(s_days)} days<br>(vs {int(m_days)})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
    else:
        t_m.append({"icon": "🏆", "title": period_label, "desc": f"Days Tied: {int(m_days)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
        t_s.append({"icon": "🏆", "title": period_label, "desc": f"Days Tied: {int(s_days)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})

    # 7. Highest Daily Total Score (🚀)
    if not daily_data_for_period.empty:
        m_high_total = daily_data_for_period['Michael Total Score'].max()
        s_high_total = daily_data_for_period['Sarah Total Score'].max()
        
        m_high_date_row = daily_data_for_period.loc[daily_data_for_period['Michael Total Score'].idxmax()]
        s_high_date_row = daily_data_for_period.loc[daily_data_for_period['Sarah Total Score'].idxmax()]
        
        m_date_str = m_high_date_row['Date'].strftime('%b %d')
        s_date_str = s_high_date_row['Date'].strftime('%b %d')

        if m_high_total > s_high_total:
            margin = int(m_high_total - s_high_total)
            is_gold = check_gold_margin(m_high_total, s_high_total)
            t_m.append({"icon": "🚀", "title": period_label, "desc": f"High: {int(m_high_total):,}<br>+{margin:,} ({m_date_str})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
        elif s_high_total > m_high_total:
            margin = int(s_high_total - m_high_total)
            is_gold = check_gold_margin(s_high_total, m_high_total)
            t_s.append({"icon": "🚀", "title": period_label, "desc": f"High: {int(s_high_total):,}<br>+{margin:,} ({s_date_str})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
        else:
            t_m.append({"icon": "🚀", "title": period_label, "desc": f"Tie High: {int(m_high_total):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
            t_s.append({"icon": "🚀", "title": period_label, "desc": f"Tie High: {int(s_high_total):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})

    # 10. Most Perfect Rounds (Total) 🟩
    m_perfect_total = row['M_Total_Perf']
    s_perfect_total = row['S_Total_Perf']

    if m_perfect_total > 0 or s_perfect_total > 0:
        if m_perfect_total > s_perfect_total:
            diff = int(m_perfect_total - s_perfect_total)
            t_m.append({"icon": "🟩", "title": period_label, "desc": f"Perfect Rounds: {int(m_perfect_total)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
        elif s_perfect_total > m_perfect_total:
            diff = int(s_perfect_total - m_perfect_total)
            t_s.append({"icon": "🟩", "title": period_label, "desc": f"Perfect Rounds: {int(s_perfect_total)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
        else:
            t_m.append({"icon": "🟩", "title": period_label, "desc": f"Tie Perfect: {int(m_perfect_total)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
            t_s.append({"icon": "🟩", "title": period_label, "desc": f"Tie Perfect: {int(s_perfect_total)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})

    # --- CATEGORY 2: GEOGRAPHY ---

    # 3. Geography Score Trophy (🗺️)
    m_geo = row['M_Geo_Row']
    s_geo = row['S_Geo_Row']
    
    if m_geo > s_geo:
        is_gold = check_gold_margin(m_geo, s_geo)
        t_m.append({"icon": "🗺️", "title": period_label, "desc": f"Geo: {int(m_geo):,}<br>Won by {int(m_geo-s_geo):,}", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
    elif s_geo > m_geo:
        is_gold = check_gold_margin(s_geo, m_geo)
        t_s.append({"icon": "🗺️", "title": period_label, "desc": f"Geo: {int(s_geo):,}<br>Won by {int(s_geo-m_geo):,}", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
    else:
        t_m.append({"icon": "🗺️", "title": period_label, "desc": f"Tie: {int(m_geo):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
        t_s.append({"icon": "🗺️", "title": period_label, "desc": f"Tie: {int(s_geo):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})

    # 4. Geography Days Won Trophy (🌍)
    m_geo_days = row['M_Geo_Win']
    s_geo_days = row['S_Geo_Win']

    if m_geo_days > s_geo_days:
        is_gold = m_geo_days >= dominance_threshold
        t_m.append({"icon": "🌍", "title": period_label, "desc": f"Geo Days: {int(m_geo_days)}<br>(vs {int(s_geo_days)})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
    elif s_geo_days > m_geo_days:
        is_gold = s_geo_days >= dominance_threshold
        t_s.append({"icon": "🌍", "title": period_label, "desc": f"Geo Days: {int(s_geo_days)}<br>(vs {int(m_geo_days)})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
    else:
        t_m.append({"icon": "🌍", "title": period_label, "desc": f"Geo Days Tied: {int(m_geo_days)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
        t_s.append({"icon": "🌍", "title": period_label, "desc": f"Geo Days Tied: {int(s_geo_days)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})

    # 8. Highest Daily Geography Score (🏔️)
    if not daily_data_for_period.empty:
        m_high_geo = daily_data_for_period['M_Geo_Row'].max()
        s_high_geo = daily_data_for_period['S_Geo_Row'].max()
        
        m_high_geo_date = daily_data_for_period.loc[daily_data_for_period['M_Geo_Row'].idxmax()]['Date'].strftime('%b %d')
        s_high_geo_date = daily_data_for_period.loc[daily_data_for_period['S_Geo_Row'].idxmax()]['Date'].strftime('%b %d')

        if m_high_geo > s_high_geo:
            margin = int(m_high_geo - s_high_geo)
            is_gold = check_gold_margin(m_high_geo, s_high_geo)
            t_m.append({"icon": "🏔️", "title": period_label, "desc": f"High Geo: {int(m_high_geo):,}<br>+{margin:,} ({m_high_geo_date})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
        elif s_high_geo > m_high_geo:
            margin = int(s_high_geo - m_high_geo)
            is_gold = check_gold_margin(s_high_geo, m_high_geo)
            t_s.append({"icon": "🏔️", "title": period_label, "desc": f"High Geo: {int(s_high_geo):,}<br>+{margin:,} ({s_high_geo_date})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
        else:
            t_m.append({"icon": "🏔️", "title": period_label, "desc": f"Tie High Geo: {int(m_high_geo):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
            t_s.append({"icon": "🏔️", "title": period_label, "desc": f"Tie High Geo: {int(s_high_geo):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})

    # 11. Most Perfect Geo Rounds 🌍🟩
    m_perfect_geo = row['M_Geo_Perf']
    s_perfect_geo = row['S_Geo_Perf']

    if m_perfect_geo > 0 or s_perfect_geo > 0:
        if m_perfect_geo > s_perfect_geo:
            diff = int(m_perfect_geo - s_perfect_geo)
            t_m.append({"icon": "🌍🟩", "title": period_label, "desc": f"Perfect Geo: {int(m_perfect_geo)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
        elif s_perfect_geo > m_perfect_geo:
            diff = int(s_perfect_geo - m_perfect_geo)
            t_s.append({"icon": "🌍🟩", "title": period_label, "desc": f"Perfect Geo: {int(s_perfect_geo)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
        else:
            t_m.append({"icon": "🌍🟩", "title": period_label, "desc": f"Tie Perf Geo: {int(m_perfect_geo)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
            t_s.append({"icon": "🌍🟩", "title": period_label, "desc": f"Tie Perf Geo: {int(s_perfect_geo)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})

    # --- CATEGORY 3: TIME ---

    # 5. Time Score Trophy (🕰️)
    m_time = row['M_Time_Row']
    s_time = row['S_Time_Row']
    
    if m_time > s_time:
        is_gold = check_gold_margin(m_time, s_time)
        t_m.append({"icon": "🕰️", "title": period_label, "desc": f"Time: {int(m_time):,}<br>Won by {int(m_time-s_time):,}", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
    elif s_time > m_time:
        is_gold = check_gold_margin(s_time, m_time)
        t_s.append({"icon": "🕰️", "title": period_label, "desc": f"Time: {int(s_time):,}<br>Won by {int(s_time-m_time):,}", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
    else:
        t_m.append({"icon": "🕰️", "title": period_label, "desc": f"Tie: {int(m_time):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
        t_s.append({"icon": "🕰️", "title": period_label, "desc": f"Tie: {int(s_time):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})

    # 6. Time Days Won Trophy (📆)
    m_time_days = row['M_Time_Win']
    s_time_days = row['S_Time_Win']

    if m_time_days > s_time_days:
        is_gold = m_time_days >= dominance_threshold
        t_m.append({"icon": "📆", "title": period_label, "desc": f"Time Days: {int(m_time_days)}<br>(vs {int(s_time_days)})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
    elif s_time_days > m_time_days:
        is_gold = s_time_days >= dominance_threshold
        t_s.append({"icon": "📆", "title": period_label, "desc": f"Time Days: {int(s_time_days)}<br>(vs {int(m_time_days)})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
    else:
        t_m.append({"icon": "📆", "title": period_label, "desc": f"Time Days Tied: {int(m_time_days)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
        t_s.append({"icon": "📆", "title": period_label, "desc": f"Time Days Tied: {int(s_time_days)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})

    # 9. Highest Daily Time Score (⏱️)
    if not daily_data_for_period.empty:
        m_high_time = daily_data_for_period['M_Time_Row'].max()
        s_high_time = daily_data_for_period['S_Time_Row'].max()
        
        m_high_time_date = daily_data_for_period.loc[daily_data_for_period['M_Time_Row'].idxmax()]['Date'].strftime('%b %d')
        s_high_time_date = daily_data_for_period.loc[daily_data_for_period['S_Time_Row'].idxmax()]['Date'].strftime('%b %d')

        if m_high_time > s_high_time:
            margin = int(m_high_time - s_high_time)
            is_gold = check_gold_margin(m_high_time, s_high_time)
            t_m.append({"icon": "⏱️", "title": period_label, "desc": f"High Time: {int(m_high_time):,}<br>+{margin:,} ({m_high_time_date})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
        elif s_high_time > m_high_time:
            margin = int(s_high_time - m_high_time)
            is_gold = check_gold_margin(s_high_time, m_high_time)
            t_s.append({"icon": "⏱️", "title": period_label, "desc": f"High Time: {int(s_high_time):,}<br>+{margin:,} ({s_high_time_date})", "is_tie": False, "is_gold": is_gold, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
        else:
            t_m.append({"icon": "⏱️", "title": period_label, "desc": f"Tie High Time: {int(m_high_time):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
            t_s.append({"icon": "⏱️", "title": period_label, "desc": f"Tie High Time: {int(s_high_time):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})

    # 12. Most Perfect Time Rounds 📆🟩
    m_perfect_time = row['M_Time_Perf']
    s_perfect_time = row['S_Time_Perf']

    if m_perfect_time > 0 or s_perfect_time > 0:
        if m_perfect_time > s_perfect_time:
            diff = int(m_perfect_time - s_perfect_time)
            t_m.append({"icon": "📆🟩", "title": period_label, "desc": f"Perfect Time: {int(m_perfect_time)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
        elif s_perfect_time > m_perfect_time:
            diff = int(s_perfect_time - m_perfect_time)
            t_s.append({"icon": "📆🟩", "title": period_label, "desc": f"Perfect Time: {int(s_perfect_time)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
        else:
            t_m.append({"icon": "📆🟩", "title": period_label, "desc": f"Tie Perf Time: {int(m_perfect_time)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
            t_s.append({"icon": "📆🟩", "title": period_label, "desc": f"Tie Perf Time: {int(s_perfect_time)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})

    return t_m, t_s

def calculate_trophies(df):
    """Calculates Monthly, Quarterly, and Yearly trophies."""
    if df is None or df.empty:
        return [], [], [], [], [], []

    # Get Current Real-Time Date
    current_now = pd.Timestamp.now()
    current_year = current_now.year
    current_quarter = current_now.to_period('Q')
    current_month = current_now.to_period('M')

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

    # Pre-calculate periods for filtering checks later
    daily_stats['Year'] = daily_stats['Date'].dt.year
    daily_stats['Quarter'] = daily_stats['Date'].dt.to_period('Q')
    daily_stats['MonthPeriod'] = daily_stats['Date'].dt.to_period('M')

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
        
        # VISIBILITY CHECK: Only show year if it has data from > 1 Quarter
        if daily_for_year['Quarter'].nunique() < 2:
            continue
        
        # Check if year is ongoing (Current Year)
        is_ongoing = (year_val == current_year)

        t_m, t_s = generate_trophies_for_period(row, daily_for_year, str(int(year_val)), is_yearly=True, is_ongoing=is_ongoing)
        yearly_m.extend(t_m)
        yearly_s.extend(t_s)

    # --- QUARTERLY TROPHIES ---
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
        
        # VISIBILITY CHECK: Only show quarter if it has data from > 1 Month
        if daily_for_q['MonthPeriod'].nunique() < 2:
            continue
        
        # Check if quarter is ongoing
        is_ongoing = (q_period == current_quarter)
        
        q_label = f"Q{q_period.quarter} {q_period.year}"
        
        t_m, t_s = generate_trophies_for_period(row, daily_for_q, q_label, is_yearly=False, is_ongoing=is_ongoing)
        quarterly_m.extend(t_m)
        quarterly_s.extend(t_s)

    # --- MONTHLY TROPHIES ---
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
        
        # Check if month is ongoing
        is_ongoing = (month_period == current_month)
        
        t_m, t_s = generate_trophies_for_period(row, daily_for_month, row['MonthLabel'], is_yearly=False, is_ongoing=is_ongoing)
        monthly_m.extend(t_m)
        monthly_s.extend(t_s)

    return yearly_m, quarterly_m, monthly_m, yearly_s, quarterly_s, monthly_s

def create_trophy_html(icon, title, desc, is_tie=False, is_gold=False, is_yearly=False, is_ongoing=False):
    tie_class = " tie" if is_tie else ""
    gold_class = " gold-rim" if is_gold else ""
    yearly_class = " yearly" if is_yearly else ""
    ongoing_class = " ongoing" if is_ongoing else ""
    return f'<div class="trophy-card{tie_class}{gold_class}{yearly_class}{ongoing_class}"><div class="trophy-icon">{icon}</div><div class="trophy-title">{title}</div><div class="trophy-desc">{desc}</div></div>'

def render_cabinet(player_name, trophies_yearly, trophies_quarterly, trophies_monthly, category_filter, theme_class, text_class):
    """Renders a single cabinet for a specific player and category."""
    
    # Filter trophies by category
    y_filtered = [t for t in trophies_yearly if t.get('category') == category_filter]
    q_filtered = [t for t in trophies_quarterly if t.get('category') == category_filter]
    m_filtered = [t for t in trophies_monthly if t.get('category') == category_filter]

    html_content = ""
    has_content = False

    # Helper for Separator
    def get_separator(text):
        return f'<div class="trophy-divider"><span>{text}</span></div>'

    # Helper to group by period title and render separate grids
    def render_grouped_grids(trophies):
        if not trophies:
            return ""
        
        # Group by title (e.g., "2024", "Q1 2024", "Jan 2024")
        # List is already sorted by date descending from calculate_trophies
        groups = {}
        for t in trophies:
            title = t['title']
            if title not in groups:
                groups[title] = []
            groups[title].append(t)
        
        html = ""
        for title in groups:
            # Render all trophies for this specific period
            group_html = "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t.get('is_gold', False), t.get('is_yearly', False), t.get('is_ongoing', False)) for t in groups[title]])
            # Wrap them in their own grid so they stand alone on a "line" (row block)
            html += f'<div class="trophy-grid" style="margin-bottom: 15px;">{group_html}</div>'
        return html

    if y_filtered:
         html_content += get_separator("Yearly")
         html_content += render_grouped_grids(y_filtered)
         has_content = True
         
    if q_filtered:
         if has_content: html_content += get_separator("Quarterly")
         html_content += render_grouped_grids(q_filtered)
         has_content = True

    if m_filtered:
         if has_content: html_content += get_separator("Monthly")
         html_content += render_grouped_grids(m_filtered)
         has_content = True
    
    if not has_content:
        html_content = "<div style='text-align:center; color:#666; width:100%; padding: 40px 20px; font-style: italic;'>No trophies in this category yet.</div>"
    
    st.markdown(
        f'<div class="cabinet-container {theme_class}"><div class="cabinet-header {text_class}">{player_name}</div>{html_content}</div>',
        unsafe_allow_html=True
    )

# --- Header ---
st.title("Hall of Fame")
st.markdown("### Trophy Cabinet")
st.markdown("<br>", unsafe_allow_html=True)

# --- Data Loading & Processing ---
df = load_data()
yearly_m, quarterly_m, monthly_m, yearly_s, quarterly_s, monthly_s = calculate_trophies(df)

# --- Tabs for Category Organization ---
tab1, tab2, tab3 = st.tabs(["🏆 Overall & Total", "🌍 Geography", "🕰️ Time"])

# --- TAB 1: TOTAL ---
with tab1:
    col1, col2 = st.columns(2, gap="large")
    with col1:
        render_cabinet("Michael", yearly_m, quarterly_m, monthly_m, "total", "michael-theme", "michael-text")
    with col2:
        render_cabinet("Sarah", yearly_s, quarterly_s, monthly_s, "total", "sarah-theme", "sarah-text")

# --- TAB 2: GEOGRAPHY ---
with tab2:
    col1, col2 = st.columns(2, gap="large")
    with col1:
        render_cabinet("Michael", yearly_m, quarterly_m, monthly_m, "geo", "michael-theme", "michael-text")
    with col2:
        render_cabinet("Sarah", yearly_s, quarterly_s, monthly_s, "geo", "sarah-theme", "sarah-text")

# --- TAB 3: TIME ---
with tab3:
    col1, col2 = st.columns(2, gap="large")
    with col1:
        render_cabinet("Michael", yearly_m, quarterly_m, monthly_m, "time", "michael-theme", "michael-text")
    with col2:
        render_cabinet("Sarah", yearly_s, quarterly_s, monthly_s, "time", "sarah-theme", "sarah-text")