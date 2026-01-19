import streamlit as st
import pandas as pd
from PIL import Image

# --- Configuration ---
st.set_page_config(page_title="Hall of Shame", layout="wide")

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
            min-height: 250px;
        }
        
        .cabinet-header {
            font-family: 'Poppins', sans-serif;
            font-weight: 800;
            font-size: 1.5rem;
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

        /* Ongoing / Live Period Styling */
        .trophy-card.ongoing::after {
            content: "LIVE";
            position: absolute;
            top: 6px;
            right: 6px;
            font-size: 9px;
            font-weight: 800;
            color: white;
            background-color: #db5049; /* Red Badge */
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
        st.error(f"Error loading data: {e}")
        return None

def check_gold_shame_margin(lower_score, higher_score):
    """
    Helper to check Gold Rim Criteria for Shame (Score Margin >= 10% lower).
    Calculates if the loser's score is >10% worse than the winner.
    """
    if lower_score == 0: return True # Infinite shame
    return (higher_score - lower_score) / lower_score >= 0.10

def generate_shame_trophies_for_period(row, daily_data, period_label, is_yearly=False, is_ongoing=False):
    """Generates the list of lowest score 'awards' for a specific period."""
    if daily_data.empty:
        return [], []

    # Sort to ensure diffs are chronological
    daily_data = daily_data.sort_values('Date')

    t_m = []
    t_s = []
    
    total_days = row['DaysCount']
    # Dominance logic removed for gold borders, but logic kept in case needed for calculations
    # dominance_threshold = total_days * (2/3) 

    # --- CATEGORY 1: TOTAL / OVERALL ---

    # 1. Lowest Daily Total Score (📉)
    m_min_idx = daily_data['Michael Total Score'].idxmin()
    s_min_idx = daily_data['Sarah Total Score'].idxmin()
    
    m_min_val = daily_data.loc[m_min_idx, 'Michael Total Score']
    s_min_val = daily_data.loc[s_min_idx, 'Sarah Total Score']
    
    m_date = daily_data.loc[m_min_idx, 'Date'].strftime('%b %d')
    s_date = daily_data.loc[s_min_idx, 'Date'].strftime('%b %d')
    
    if m_min_val < s_min_val:
        diff = int(s_min_val - m_min_val)
        t_m.append({"icon": "📉", "title": period_label, "desc": f"Low Total: {int(m_min_val):,}<br>-{diff:,} ({m_date})", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
    elif s_min_val < m_min_val:
        diff = int(m_min_val - s_min_val)
        t_s.append({"icon": "📉", "title": period_label, "desc": f"Low Total: {int(s_min_val):,}<br>-{diff:,} ({s_date})", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
    else:
        t_m.append({"icon": "📉", "title": period_label, "desc": f"Tie Low: {int(m_min_val):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
        t_s.append({"icon": "📉", "title": period_label, "desc": f"Tie Low: {int(s_min_val):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})

    # 2. Biggest Loss (Margin) 🤕
    # Find the day with the largest absolute difference between scores
    diffs = (daily_data['Michael Total Score'] - daily_data['Sarah Total Score']).abs()
    if not diffs.empty and diffs.max() > 0:
        max_diff_idx = diffs.idxmax()
        max_diff = int(diffs[max_diff_idx])
        
        row_max = daily_data.loc[max_diff_idx]
        m_score = row_max['Michael Total Score']
        s_score = row_max['Sarah Total Score']
        date_str = row_max['Date'].strftime('%b %d')
        
        if m_score < s_score:
            # Michael lost big
            t_m.append({"icon": "🤕", "title": period_label, "desc": f"Biggest Loss: -{max_diff:,}<br>({date_str})", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
        elif s_score < m_score:
            # Sarah lost big
            t_s.append({"icon": "🤕", "title": period_label, "desc": f"Biggest Loss: -{max_diff:,}<br>({date_str})", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})

    # 4. Most Black Square Total Rounds (Total Fail) ⬛
    m_fail_total = row['M_Total_Fail']
    s_fail_total = row['S_Total_Fail']

    if m_fail_total > 0 or s_fail_total > 0:
        if m_fail_total > s_fail_total:
            diff = int(m_fail_total - s_fail_total)
            t_m.append({"icon": "⬛", "title": period_label, "desc": f"Double Black: {int(m_fail_total)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
        elif s_fail_total > m_fail_total:
            diff = int(s_fail_total - m_fail_total)
            t_s.append({"icon": "⬛", "title": period_label, "desc": f"Double Black: {int(s_fail_total)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
        else:
            t_m.append({"icon": "⬛", "title": period_label, "desc": f"Tie Black: {int(m_fail_total)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})
            t_s.append({"icon": "⬛", "title": period_label, "desc": f"Tie Black: {int(s_fail_total)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "total"})

    # --- CATEGORY 2: GEOGRAPHY ---

    # 2. Lowest Daily Geography Score (🏚️)
    m_geo_min_idx = daily_data['M_Geo_Row'].idxmin()
    s_geo_min_idx = daily_data['S_Geo_Row'].idxmin()
    
    m_geo_min = daily_data.loc[m_geo_min_idx, 'M_Geo_Row']
    s_geo_min = daily_data.loc[s_geo_min_idx, 'S_Geo_Row']
    
    m_geo_date = daily_data.loc[m_geo_min_idx, 'Date'].strftime('%b %d')
    s_geo_date = daily_data.loc[s_geo_min_idx, 'Date'].strftime('%b %d')
    
    if m_geo_min < s_geo_min:
        diff = int(s_geo_min - m_geo_min)
        t_m.append({"icon": "🏚️", "title": period_label, "desc": f"Low Geo: {int(m_geo_min):,}<br>-{diff:,} ({m_geo_date})", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
    elif s_geo_min < m_geo_min:
        diff = int(m_geo_min - s_geo_min)
        t_s.append({"icon": "🏚️", "title": period_label, "desc": f"Low Geo: {int(s_geo_min):,}<br>-{diff:,} ({s_geo_date})", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
    else:
        t_m.append({"icon": "🏚️", "title": period_label, "desc": f"Tie Low Geo: {int(m_geo_min):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
        t_s.append({"icon": "🏚️", "title": period_label, "desc": f"Tie Low Geo: {int(s_geo_min):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})

    # 7. Biggest Geo Loss (Geo Margin) 🤕
    geo_diffs = (daily_data['M_Geo_Row'] - daily_data['S_Geo_Row']).abs()
    if not geo_diffs.empty and geo_diffs.max() > 0:
        max_geo_idx = geo_diffs.idxmax()
        max_geo_diff = int(geo_diffs[max_geo_idx])
        
        row_geo_max = daily_data.loc[max_geo_idx]
        m_geo_score = row_geo_max['M_Geo_Row']
        s_geo_score = row_geo_max['S_Geo_Row']
        date_str = row_geo_max['Date'].strftime('%b %d')
        
        if m_geo_score < s_geo_score:
            t_m.append({"icon": "🤕", "title": period_label, "desc": f"Biggest Geo Loss: -{max_geo_diff:,}<br>({date_str})", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
        elif s_geo_score < m_geo_score:
            t_s.append({"icon": "🤕", "title": period_label, "desc": f"Biggest Geo Loss: -{max_geo_diff:,}<br>({date_str})", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})

    # 5. Most Black Square Geo Rounds (Geo Fail) 🌍⬛
    m_fail_geo = row['M_Geo_Fail']
    s_fail_geo = row['S_Geo_Fail']

    if m_fail_geo > 0 or s_fail_geo > 0:
        if m_fail_geo > s_fail_geo:
            diff = int(m_fail_geo - s_fail_geo)
            t_m.append({"icon": "🌍⬛", "title": period_label, "desc": f"Geo Black: {int(m_fail_geo)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
        elif s_fail_geo > m_fail_geo:
            diff = int(s_fail_geo - m_fail_geo)
            t_s.append({"icon": "🌍⬛", "title": period_label, "desc": f"Geo Black: {int(s_fail_geo)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
        else:
            t_m.append({"icon": "🌍⬛", "title": period_label, "desc": f"Tie Geo Black: {int(m_fail_geo)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})
            t_s.append({"icon": "🌍⬛", "title": period_label, "desc": f"Tie Geo Black: {int(s_fail_geo)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "geo"})

    # --- CATEGORY 3: TIME ---

    # 3. Lowest Daily Time Score (🐌)
    m_time_min_idx = daily_data['M_Time_Row'].idxmin()
    s_time_min_idx = daily_data['S_Time_Row'].idxmin()
    
    m_time_min = daily_data.loc[m_time_min_idx, 'M_Time_Row']
    s_time_min = daily_data.loc[s_time_min_idx, 'S_Time_Row']
    
    m_time_date = daily_data.loc[m_time_min_idx, 'Date'].strftime('%b %d')
    s_time_date = daily_data.loc[s_time_min_idx, 'Date'].strftime('%b %d')
    
    if m_time_min < s_time_min:
        diff = int(s_time_min - m_time_min)
        t_m.append({"icon": "🐌", "title": period_label, "desc": f"Low Time: {int(m_time_min):,}<br>-{diff:,} ({m_time_date})", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
    elif s_time_min < m_time_min:
        diff = int(m_time_min - s_time_min)
        t_s.append({"icon": "🐌", "title": period_label, "desc": f"Low Time: {int(s_time_min):,}<br>-{diff:,} ({s_time_date})", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
    else:
        t_m.append({"icon": "🐌", "title": period_label, "desc": f"Tie Low Time: {int(m_time_min):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
        t_s.append({"icon": "🐌", "title": period_label, "desc": f"Tie Low Time: {int(s_time_min):,}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})

    # 8. Biggest Time Loss (Time Margin) 🤕
    time_diffs = (daily_data['M_Time_Row'] - daily_data['S_Time_Row']).abs()
    if not time_diffs.empty and time_diffs.max() > 0:
        max_time_idx = time_diffs.idxmax()
        max_time_diff = int(time_diffs[max_time_idx])
        
        row_time_max = daily_data.loc[max_time_idx]
        m_time_score = row_time_max['M_Time_Row']
        s_time_score = row_time_max['S_Time_Row']
        date_str = row_time_max['Date'].strftime('%b %d')
        
        if m_time_score < s_time_score:
            t_m.append({"icon": "🤕", "title": period_label, "desc": f"Biggest Time Loss: -{max_time_diff:,}<br>({date_str})", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
        elif s_time_score < m_time_score:
            t_s.append({"icon": "🤕", "title": period_label, "desc": f"Biggest Time Loss: -{max_time_diff:,}<br>({date_str})", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})

    # 6. Most Black Square Time Rounds (Time Fail) 📆⬛
    m_fail_time = row['M_Time_Fail']
    s_fail_time = row['S_Time_Fail']

    if m_fail_time > 0 or s_fail_time > 0:
        if m_fail_time > s_fail_time:
            diff = int(m_fail_time - s_fail_time)
            t_m.append({"icon": "📆⬛", "title": period_label, "desc": f"Time Black: {int(m_fail_time)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
        elif s_fail_time > m_fail_time:
            diff = int(s_fail_time - m_fail_time)
            t_s.append({"icon": "📆⬛", "title": period_label, "desc": f"Time Black: {int(s_fail_time)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
        else:
            t_m.append({"icon": "📆⬛", "title": period_label, "desc": f"Tie Time Black: {int(m_fail_time)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})
            t_s.append({"icon": "📆⬛", "title": period_label, "desc": f"Tie Time Black: {int(s_fail_time)}", "is_tie": True, "is_yearly": is_yearly, "is_ongoing": is_ongoing, "category": "time"})

    return t_m, t_s

def calculate_shame(df):
    """Calculates Monthly, Quarterly, and Yearly shame stats."""
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

    # --- Step 2: Calculate Row-Level Stats (Base Data) ---
    df_valid['M_Geo_Row'] = (df_valid['Michael Geography Score (Min)'] + df_valid['Michael Geography Score (Max)']) / 2
    df_valid['S_Geo_Row'] = (df_valid['Sarah Geography Score (Min)'] + df_valid['Sarah Geography Score (Max)']) / 2
    df_valid['M_Time_Row'] = (df_valid['Michael Time Score (Min)'] + df_valid['Michael Time Score (Max)']) / 2
    df_valid['S_Time_Row'] = (df_valid['Sarah Time Score (Min)'] + df_valid['Sarah Time Score (Max)']) / 2

    # Calculate Shame Rounds at Row Level
    # Geo < 2500, Time == 0
    df_valid['M_Geo_Fail'] = (df_valid['M_Geo_Row'] < 2500).astype(int)
    df_valid['S_Geo_Fail'] = (df_valid['S_Geo_Row'] < 2500).astype(int)
    df_valid['M_Time_Fail'] = (df_valid['M_Time_Row'] == 0).astype(int)
    df_valid['S_Time_Fail'] = (df_valid['S_Time_Row'] == 0).astype(int)
    df_valid['M_Total_Fail'] = ((df_valid['M_Geo_Row'] < 2500) & (df_valid['M_Time_Row'] == 0)).astype(int)
    df_valid['S_Total_Fail'] = ((df_valid['S_Geo_Row'] < 2500) & (df_valid['S_Time_Row'] == 0)).astype(int)

    # Aggregate to Daily
    daily_stats = df_valid.groupby('Date').agg({
        'Michael Total Score': 'first',
        'Sarah Total Score': 'first',
        'M_Geo_Row': 'sum',
        'S_Geo_Row': 'sum',
        'M_Time_Row': 'sum',
        'S_Time_Row': 'sum',
        'M_Geo_Fail': 'sum',
        'S_Geo_Fail': 'sum',
        'M_Time_Fail': 'sum',
        'S_Time_Fail': 'sum',
        'M_Total_Fail': 'sum',
        'S_Total_Fail': 'sum'
    }).reset_index()
    
    # Add Time Periods
    daily_stats['Year'] = daily_stats['Date'].dt.year
    daily_stats['Quarter'] = daily_stats['Date'].dt.to_period('Q')
    daily_stats['MonthPeriod'] = daily_stats['Date'].dt.to_period('M')

    yearly_m, yearly_s = [], []
    quarterly_m, quarterly_s = [], []
    monthly_m, monthly_s = [], []

    # --- YEARLY STATS ---
    unique_years = sorted(daily_stats['Year'].unique(), reverse=True)
    
    # Pre-calculate year aggregations for Fail counts
    yearly_agg = daily_stats.groupby('Year').agg({
        'M_Geo_Fail': 'sum',
        'S_Geo_Fail': 'sum',
        'M_Time_Fail': 'sum',
        'S_Time_Fail': 'sum',
        'M_Total_Fail': 'sum',
        'S_Total_Fail': 'sum',
        'Date': 'count'
    }).reset_index()
    yearly_agg.rename(columns={'Date': 'DaysCount'}, inplace=True)
    
    for year_val in unique_years:
        daily_subset = daily_stats[daily_stats['Year'] == year_val]
        
        # VISIBILITY CHECK: Only show year if it has data from > 1 Quarter
        if daily_subset['Quarter'].nunique() < 2:
            continue
        
        agg_row = yearly_agg[yearly_agg['Year'] == year_val].iloc[0]
        
        # Check if year is ongoing
        is_ongoing = (year_val == current_year)
        
        t_m, t_s = generate_shame_trophies_for_period(agg_row, daily_subset, str(int(year_val)), is_yearly=True, is_ongoing=is_ongoing)
        yearly_m.extend(t_m)
        yearly_s.extend(t_s)

    # --- QUARTERLY STATS ---
    unique_quarters = sorted(daily_stats['Quarter'].unique(), reverse=True)
    
    quarterly_agg = daily_stats.groupby('Quarter').agg({
        'M_Geo_Fail': 'sum',
        'S_Geo_Fail': 'sum',
        'M_Time_Fail': 'sum',
        'S_Time_Fail': 'sum',
        'M_Total_Fail': 'sum',
        'S_Total_Fail': 'sum',
        'Date': 'count'
    }).reset_index()
    quarterly_agg.rename(columns={'Date': 'DaysCount'}, inplace=True)
    
    for q_period in unique_quarters:
        daily_subset = daily_stats[daily_stats['Quarter'] == q_period]
        
        # VISIBILITY CHECK: Only show quarter if it has data from > 1 Month
        if daily_subset['MonthPeriod'].nunique() < 2:
            continue
            
        agg_row = quarterly_agg[quarterly_agg['Quarter'] == q_period].iloc[0]
        q_label = f"Q{q_period.quarter} {q_period.year}"
        
        # Check if quarter is ongoing
        is_ongoing = (q_period == current_quarter)
        
        t_m, t_s = generate_shame_trophies_for_period(agg_row, daily_subset, q_label, is_yearly=False, is_ongoing=is_ongoing)
        quarterly_m.extend(t_m)
        quarterly_s.extend(t_s)

    # --- MONTHLY STATS ---
    unique_months = sorted(daily_stats['MonthPeriod'].unique(), reverse=True)
    
    monthly_agg = daily_stats.groupby('MonthPeriod').agg({
        'M_Geo_Fail': 'sum',
        'S_Geo_Fail': 'sum',
        'M_Time_Fail': 'sum',
        'S_Time_Fail': 'sum',
        'M_Total_Fail': 'sum',
        'S_Total_Fail': 'sum',
        'Date': 'count'
    }).reset_index()
    monthly_agg.rename(columns={'Date': 'DaysCount'}, inplace=True)
    
    for m_period in unique_months:
        daily_subset = daily_stats[daily_stats['MonthPeriod'] == m_period]
        agg_row = monthly_agg[monthly_agg['MonthPeriod'] == m_period].iloc[0]
        m_label = m_period.strftime('%B %Y')
        
        # Check if month is ongoing
        is_ongoing = (m_period == current_month)
        
        t_m, t_s = generate_shame_trophies_for_period(agg_row, daily_subset, m_label, is_yearly=False, is_ongoing=is_ongoing)
        monthly_m.extend(t_m)
        monthly_s.extend(t_s)

    return yearly_m, quarterly_m, monthly_m, yearly_s, quarterly_s, monthly_s

def create_trophy_html(icon, title, desc, is_tie=False, is_yearly=False, is_ongoing=False):
    tie_class = " tie" if is_tie else ""
    yearly_class = " yearly" if is_yearly else ""
    ongoing_class = " ongoing" if is_ongoing else ""
    return f'<div class="trophy-card{tie_class}{yearly_class}{ongoing_class}"><div class="trophy-icon">{icon}</div><div class="trophy-title">{title}</div><div class="trophy-desc">{desc}</div></div>'

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
        
        # Group by title
        groups = {}
        for t in trophies:
            title = t['title']
            if title not in groups:
                groups[title] = []
            groups[title].append(t)
        
        html = ""
        for title in groups:
            # Render all trophies for this specific period
            group_html = "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t.get('is_yearly', False), t.get('is_ongoing', False)) for t in groups[title]])
            # Wrap them in their own grid
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
        html_content = "<div style='text-align:center; color:#666; width:100%; padding: 40px 20px; font-style: italic;'>No shame found (yet).</div>"
    
    st.markdown(
        f'<div class="cabinet-container {theme_class}"><div class="cabinet-header {text_class}">{player_name}</div>{html_content}</div>',
        unsafe_allow_html=True
    )

# --- Header ---
st.title("Hall of Shame")
st.markdown("### The Wall of Misery")
st.markdown("<br>", unsafe_allow_html=True)

# --- Data Loading & Processing ---
df = load_data()
yearly_m, quarterly_m, monthly_m, yearly_s, quarterly_s, monthly_s = calculate_shame(df)

# --- Tabs for Category Organization ---
tab1, tab2, tab3 = st.tabs(["📉 Overall & Total", "🏚️ Geography", "🐌 Time"])

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