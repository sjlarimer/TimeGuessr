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
        
        /* Darker background for ties to distinguish them */
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

def calculate_monthly_trophies(df):
    if df is None or df.empty:
        return [], []

    # --- Step 1: Identify Valid Dates (Mutual Participation) ---
    # We strictly only count days where BOTH players have a non-zero Total score.
    daily_check = df.groupby('Date')[['Michael Total Score', 'Sarah Total Score']].first()
    valid_dates = daily_check[
        (daily_check['Michael Total Score'] > 0) & 
        (daily_check['Sarah Total Score'] > 0)
    ].index

    df_valid = df[df['Date'].isin(valid_dates)].copy()
    
    if df_valid.empty:
        return [], []

    df_valid['MonthPeriod'] = df_valid['Date'].dt.to_period('M')

    # --- Step 2: Calculate Row-Level Scores ---
    df_valid['M_Geo_Row'] = (df_valid['Michael Geography Score (Min)'] + df_valid['Michael Geography Score (Max)']) / 2
    df_valid['S_Geo_Row'] = (df_valid['Sarah Geography Score (Min)'] + df_valid['Sarah Geography Score (Max)']) / 2
    
    df_valid['M_Time_Row'] = (df_valid['Michael Time Score (Min)'] + df_valid['Michael Time Score (Max)']) / 2
    df_valid['S_Time_Row'] = (df_valid['Sarah Time Score (Min)'] + df_valid['Sarah Time Score (Max)']) / 2

    # --- Step 3: Aggregate to Daily Level ---
    daily_stats = df_valid.groupby(['Date', 'MonthPeriod']).agg({
        'Michael Total Score': 'first',
        'Sarah Total Score': 'first',
        'M_Geo_Row': 'sum',
        'S_Geo_Row': 'sum',
        'M_Time_Row': 'sum',
        'S_Time_Row': 'sum'
    }).reset_index()

    # --- Step 4: Calculate Daily Wins ---
    daily_stats['M_Total_Win'] = (daily_stats['Michael Total Score'] > daily_stats['Sarah Total Score']).astype(int)
    daily_stats['S_Total_Win'] = (daily_stats['Sarah Total Score'] > daily_stats['Michael Total Score']).astype(int)
    
    daily_stats['M_Geo_Win'] = (daily_stats['M_Geo_Row'] > daily_stats['S_Geo_Row']).astype(int)
    daily_stats['S_Geo_Win'] = (daily_stats['S_Geo_Row'] > daily_stats['M_Geo_Row']).astype(int)
    
    daily_stats['M_Time_Win'] = (daily_stats['M_Time_Row'] > daily_stats['S_Time_Row']).astype(int)
    daily_stats['S_Time_Win'] = (daily_stats['S_Time_Row'] > daily_stats['M_Time_Row']).astype(int)

    # --- Step 5: Aggregate to Monthly Level ---
    monthly_stats = daily_stats.groupby('MonthPeriod').agg({
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
        'Date': 'count' # Count of valid days played in the month
    }).reset_index()
    monthly_stats.rename(columns={'Date': 'DaysCount'}, inplace=True)

    monthly_stats['MonthLabel'] = monthly_stats['MonthPeriod'].dt.strftime('%B %Y')
    monthly_stats = monthly_stats.sort_values('MonthPeriod')

    trophies_m = []
    trophies_s = []

    for _, row in monthly_stats.iterrows():
        month_label = row['MonthLabel']
        total_days = row['DaysCount']
        
        # Threshold for Gold Rim (Days Won): At least 2/3 of games won
        dominance_threshold = total_days * (2/3)

        # Helper to check Silver Rim (Score Margin >= 10%)
        def check_silver(winner_score, loser_score):
            if loser_score == 0: return True # Infinite margin
            return (winner_score - loser_score) / loser_score >= 0.10

        # --- 1. Total Score Trophy (🌟) ---
        m_total = row['Michael Total Score']
        s_total = row['Sarah Total Score']
        
        if m_total > s_total:
            is_silver = check_silver(m_total, s_total)
            trophies_m.append({"icon": "🌟", "title": month_label, "desc": f"Total: {int(m_total):,}<br>Won by {int(m_total-s_total):,}", "is_tie": False, "is_silver": is_silver})
        elif s_total > m_total:
            is_silver = check_silver(s_total, m_total)
            trophies_s.append({"icon": "🌟", "title": month_label, "desc": f"Total: {int(s_total):,}<br>Won by {int(s_total-m_total):,}", "is_tie": False, "is_silver": is_silver})
        else:
            trophies_m.append({"icon": "🌟", "title": month_label, "desc": f"Tie: {int(m_total):,}", "is_tie": True})
            trophies_s.append({"icon": "🌟", "title": month_label, "desc": f"Tie: {int(s_total):,}", "is_tie": True})

        # --- 2. Total Days Won Trophy (🏆) ---
        m_days = row['M_Total_Win']
        s_days = row['S_Total_Win']
        
        if m_days > s_days:
            is_gold = m_days >= dominance_threshold
            trophies_m.append({"icon": "🏆", "title": month_label, "desc": f"Won {int(m_days)} days<br>(vs {int(s_days)})", "is_tie": False, "is_gold": is_gold})
        elif s_days > m_days:
            is_gold = s_days >= dominance_threshold
            trophies_s.append({"icon": "🏆", "title": month_label, "desc": f"Won {int(s_days)} days<br>(vs {int(m_days)})", "is_tie": False, "is_gold": is_gold})
        else:
            trophies_m.append({"icon": "🏆", "title": month_label, "desc": f"Days Tied: {int(m_days)}", "is_tie": True})
            trophies_s.append({"icon": "🏆", "title": month_label, "desc": f"Days Tied: {int(s_days)}", "is_tie": True})

        # --- 3. Geography Score Trophy (🗺️) ---
        m_geo = row['M_Geo_Row']
        s_geo = row['S_Geo_Row']
        
        if m_geo > s_geo:
            is_silver = check_silver(m_geo, s_geo)
            trophies_m.append({"icon": "🗺️", "title": month_label, "desc": f"Geo: {int(m_geo):,}<br>Won by {int(m_geo-s_geo):,}", "is_tie": False, "is_silver": is_silver})
        elif s_geo > m_geo:
            is_silver = check_silver(s_geo, m_geo)
            trophies_s.append({"icon": "🗺️", "title": month_label, "desc": f"Geo: {int(s_geo):,}<br>Won by {int(s_geo-m_geo):,}", "is_tie": False, "is_silver": is_silver})
        else:
            trophies_m.append({"icon": "🗺️", "title": month_label, "desc": f"Tie: {int(m_geo):,}", "is_tie": True})
            trophies_s.append({"icon": "🗺️", "title": month_label, "desc": f"Tie: {int(s_geo):,}", "is_tie": True})

        # --- 4. Geography Days Won Trophy (🌍) ---
        m_geo_days = row['M_Geo_Win']
        s_geo_days = row['S_Geo_Win']

        if m_geo_days > s_geo_days:
            is_gold = m_geo_days >= dominance_threshold
            trophies_m.append({"icon": "🌍", "title": month_label, "desc": f"Geo Days: {int(m_geo_days)}<br>(vs {int(s_geo_days)})", "is_tie": False, "is_gold": is_gold})
        elif s_geo_days > m_geo_days:
            is_gold = s_geo_days >= dominance_threshold
            trophies_s.append({"icon": "🌍", "title": month_label, "desc": f"Geo Days: {int(s_geo_days)}<br>(vs {int(m_geo_days)})", "is_tie": False, "is_gold": is_gold})
        else:
            trophies_m.append({"icon": "🌍", "title": month_label, "desc": f"Geo Days Tied: {int(m_geo_days)}", "is_tie": True})
            trophies_s.append({"icon": "🌍", "title": month_label, "desc": f"Geo Days Tied: {int(s_geo_days)}", "is_tie": True})

        # --- 5. Time Score Trophy (🕰️) ---
        m_time = row['M_Time_Row']
        s_time = row['S_Time_Row']
        
        if m_time > s_time:
            is_silver = check_silver(m_time, s_time)
            trophies_m.append({"icon": "🕰️", "title": month_label, "desc": f"Time: {int(m_time):,}<br>Won by {int(m_time-s_time):,}", "is_tie": False, "is_silver": is_silver})
        elif s_time > m_time:
            is_silver = check_silver(s_time, m_time)
            trophies_s.append({"icon": "🕰️", "title": month_label, "desc": f"Time: {int(s_time):,}<br>Won by {int(s_time-m_time):,}", "is_tie": False, "is_silver": is_silver})
        else:
            trophies_m.append({"icon": "🕰️", "title": month_label, "desc": f"Tie: {int(m_time):,}", "is_tie": True})
            trophies_s.append({"icon": "🕰️", "title": month_label, "desc": f"Tie: {int(s_time):,}", "is_tie": True})

        # --- 6. Time Days Won Trophy (📆) ---
        m_time_days = row['M_Time_Win']
        s_time_days = row['S_Time_Win']

        if m_time_days > s_time_days:
            is_gold = m_time_days >= dominance_threshold
            trophies_m.append({"icon": "📆", "title": month_label, "desc": f"Time Days: {int(m_time_days)}<br>(vs {int(s_time_days)})", "is_tie": False, "is_gold": is_gold})
        elif s_time_days > m_time_days:
            is_gold = s_time_days >= dominance_threshold
            trophies_s.append({"icon": "📆", "title": month_label, "desc": f"Time Days: {int(s_time_days)}<br>(vs {int(m_time_days)})", "is_tie": False, "is_gold": is_gold})
        else:
            trophies_m.append({"icon": "📆", "title": month_label, "desc": f"Time Days Tied: {int(m_time_days)}", "is_tie": True})
            trophies_s.append({"icon": "📆", "title": month_label, "desc": f"Time Days Tied: {int(s_time_days)}", "is_tie": True})

    return trophies_m, trophies_s

def create_trophy_html(icon, title, desc, is_tie=False, is_gold=False, is_silver=False):
    tie_class = " tie" if is_tie else ""
    gold_class = " gold-rim" if is_gold else ""
    silver_class = " silver-rim" if is_silver else ""
    return f'<div class="trophy-card{tie_class}{gold_class}{silver_class}"><div class="trophy-icon">{icon}</div><div class="trophy-title">{title}</div><div class="trophy-desc">{desc}</div></div>'

# --- Header ---
st.title("Hall of Fame")
st.markdown("### Monthly Trophies")
st.markdown("<br>", unsafe_allow_html=True)

# --- Data Loading & Processing ---
df = load_data()
trophies_m, trophies_s = calculate_monthly_trophies(df)

# --- Layout ---
col1, col2 = st.columns(2, gap="large")

# --- Michael's Cabinet ---
with col1:
    if trophies_m:
        m_html = "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t.get('is_gold', False), t.get('is_silver', False)) for t in trophies_m])
    else:
        m_html = "<div style='text-align:center; color:#666; width:100%; padding: 20px;'>No monthly trophies yet.</div>"
    
    st.markdown(
        f'<div class="cabinet-container michael-theme"><div class="cabinet-header michael-text">Michael</div><div class="trophy-grid">{m_html}</div></div>',
        unsafe_allow_html=True
    )

# --- Sarah's Cabinet ---
with col2:
    if trophies_s:
        s_html = "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t.get('is_gold', False), t.get('is_silver', False)) for t in trophies_s])
    else:
        s_html = "<div style='text-align:center; color:#666; width:100%; padding: 20px;'>No monthly trophies yet.</div>"
    
    st.markdown(
        f'<div class="cabinet-container sarah-theme"><div class="cabinet-header sarah-text">Sarah</div><div class="trophy-grid">{s_html}</div></div>',
        unsafe_allow_html=True
    )