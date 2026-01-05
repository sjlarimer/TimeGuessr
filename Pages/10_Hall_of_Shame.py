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

        /* Grid for Trophies (4 per row) */
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

        /* Yearly Styling (Same size as others) */
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
        
        /* Sidebar Styling */
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

def generate_shame_trophies_for_period(row, daily_data, period_label, is_yearly=False):
    """Generates the list of lowest score 'awards' for a specific period."""
    if daily_data.empty:
        return [], []

    t_m = []
    t_s = []
    
    # --- 1. Lowest Daily Total Score (📉) ---
    # Find min scores for the period
    m_min_idx = daily_data['Michael Total Score'].idxmin()
    s_min_idx = daily_data['Sarah Total Score'].idxmin()
    
    m_min_val = daily_data.loc[m_min_idx, 'Michael Total Score']
    s_min_val = daily_data.loc[s_min_idx, 'Sarah Total Score']
    
    m_date = daily_data.loc[m_min_idx, 'Date'].strftime('%b %d')
    s_date = daily_data.loc[s_min_idx, 'Date'].strftime('%b %d')
    
    # Compare who had the absolute lowest score
    if m_min_val < s_min_val:
        diff = int(s_min_val - m_min_val)
        t_m.append({"icon": "📉", "title": period_label, "desc": f"Low Total: {int(m_min_val):,}<br>-{diff:,} ({m_date})", "is_tie": False, "is_yearly": is_yearly})
    elif s_min_val < m_min_val:
        diff = int(m_min_val - s_min_val)
        t_s.append({"icon": "📉", "title": period_label, "desc": f"Low Total: {int(s_min_val):,}<br>-{diff:,} ({s_date})", "is_tie": False, "is_yearly": is_yearly})
    else:
        # Tie for lowest
        t_m.append({"icon": "📉", "title": period_label, "desc": f"Tie Low: {int(m_min_val):,}", "is_tie": True, "is_yearly": is_yearly})
        t_s.append({"icon": "📉", "title": period_label, "desc": f"Tie Low: {int(s_min_val):,}", "is_tie": True, "is_yearly": is_yearly})

    # --- 2. Lowest Daily Geography Score (🏚️) ---
    m_geo_min_idx = daily_data['M_Geo_Row'].idxmin()
    s_geo_min_idx = daily_data['S_Geo_Row'].idxmin()
    
    m_geo_min = daily_data.loc[m_geo_min_idx, 'M_Geo_Row']
    s_geo_min = daily_data.loc[s_geo_min_idx, 'S_Geo_Row']
    
    m_geo_date = daily_data.loc[m_geo_min_idx, 'Date'].strftime('%b %d')
    s_geo_date = daily_data.loc[s_geo_min_idx, 'Date'].strftime('%b %d')
    
    if m_geo_min < s_geo_min:
        diff = int(s_geo_min - m_geo_min)
        t_m.append({"icon": "🏚️", "title": period_label, "desc": f"Low Geo: {int(m_geo_min):,}<br>-{diff:,} ({m_geo_date})", "is_tie": False, "is_yearly": is_yearly})
    elif s_geo_min < m_geo_min:
        diff = int(m_geo_min - s_geo_min)
        t_s.append({"icon": "🏚️", "title": period_label, "desc": f"Low Geo: {int(s_geo_min):,}<br>-{diff:,} ({s_geo_date})", "is_tie": False, "is_yearly": is_yearly})
    else:
        t_m.append({"icon": "🏚️", "title": period_label, "desc": f"Tie Low Geo: {int(m_geo_min):,}", "is_tie": True, "is_yearly": is_yearly})
        t_s.append({"icon": "🏚️", "title": period_label, "desc": f"Tie Low Geo: {int(s_geo_min):,}", "is_tie": True, "is_yearly": is_yearly})

    # --- 3. Lowest Daily Time Score (🐌) ---
    m_time_min_idx = daily_data['M_Time_Row'].idxmin()
    s_time_min_idx = daily_data['S_Time_Row'].idxmin()
    
    m_time_min = daily_data.loc[m_time_min_idx, 'M_Time_Row']
    s_time_min = daily_data.loc[s_time_min_idx, 'S_Time_Row']
    
    m_time_date = daily_data.loc[m_time_min_idx, 'Date'].strftime('%b %d')
    s_time_date = daily_data.loc[s_time_min_idx, 'Date'].strftime('%b %d')
    
    if m_time_min < s_time_min:
        diff = int(s_time_min - m_time_min)
        t_m.append({"icon": "🐌", "title": period_label, "desc": f"Low Time: {int(m_time_min):,}<br>-{diff:,} ({m_time_date})", "is_tie": False, "is_yearly": is_yearly})
    elif s_time_min < m_time_min:
        diff = int(m_time_min - s_time_min)
        t_s.append({"icon": "🐌", "title": period_label, "desc": f"Low Time: {int(s_time_min):,}<br>-{diff:,} ({s_time_date})", "is_tie": False, "is_yearly": is_yearly})
    else:
        t_m.append({"icon": "🐌", "title": period_label, "desc": f"Tie Low Time: {int(m_time_min):,}", "is_tie": True, "is_yearly": is_yearly})
        t_s.append({"icon": "🐌", "title": period_label, "desc": f"Tie Low Time: {int(s_time_min):,}", "is_tie": True, "is_yearly": is_yearly})

    # --- 4. Most Black Square Total Rounds (Total Fail) ⬛ ---
    m_fail_total = row['M_Total_Fail']
    s_fail_total = row['S_Total_Fail']

    if m_fail_total > 0 or s_fail_total > 0:
        # Winner is whoever has MORE black squares
        if m_fail_total > s_fail_total:
            diff = int(m_fail_total - s_fail_total)
            t_m.append({"icon": "⬛", "title": period_label, "desc": f"Double Black: {int(m_fail_total)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly})
        elif s_fail_total > m_fail_total:
            diff = int(s_fail_total - m_fail_total)
            t_s.append({"icon": "⬛", "title": period_label, "desc": f"Double Black: {int(s_fail_total)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly})
        else:
            t_m.append({"icon": "⬛", "title": period_label, "desc": f"Tie Black: {int(m_fail_total)}", "is_tie": True, "is_yearly": is_yearly})
            t_s.append({"icon": "⬛", "title": period_label, "desc": f"Tie Black: {int(s_fail_total)}", "is_tie": True, "is_yearly": is_yearly})

    # --- 5. Most Black Square Geo Rounds (Geo Fail) 🌍⬛ ---
    m_fail_geo = row['M_Geo_Fail']
    s_fail_geo = row['S_Geo_Fail']

    if m_fail_geo > 0 or s_fail_geo > 0:
        if m_fail_geo > s_fail_geo:
            diff = int(m_fail_geo - s_fail_geo)
            t_m.append({"icon": "🌍⬛", "title": period_label, "desc": f"Geo Black: {int(m_fail_geo)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly})
        elif s_fail_geo > m_fail_geo:
            diff = int(s_fail_geo - m_fail_geo)
            t_s.append({"icon": "🌍⬛", "title": period_label, "desc": f"Geo Black: {int(s_fail_geo)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly})
        else:
            t_m.append({"icon": "🌍⬛", "title": period_label, "desc": f"Tie Geo Black: {int(m_fail_geo)}", "is_tie": True, "is_yearly": is_yearly})
            t_s.append({"icon": "🌍⬛", "title": period_label, "desc": f"Tie Geo Black: {int(s_fail_geo)}", "is_tie": True, "is_yearly": is_yearly})

    # --- 6. Most Black Square Time Rounds (Time Fail) 📆⬛ ---
    m_fail_time = row['M_Time_Fail']
    s_fail_time = row['S_Time_Fail']

    if m_fail_time > 0 or s_fail_time > 0:
        if m_fail_time > s_fail_time:
            diff = int(m_fail_time - s_fail_time)
            t_m.append({"icon": "📆⬛", "title": period_label, "desc": f"Time Black: {int(m_fail_time)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly})
        elif s_fail_time > m_fail_time:
            diff = int(s_fail_time - m_fail_time)
            t_s.append({"icon": "📆⬛", "title": period_label, "desc": f"Time Black: {int(s_fail_time)}<br>+{diff}", "is_tie": False, "is_yearly": is_yearly})
        else:
            t_m.append({"icon": "📆⬛", "title": period_label, "desc": f"Tie Time Black: {int(m_fail_time)}", "is_tie": True, "is_yearly": is_yearly})
            t_s.append({"icon": "📆⬛", "title": period_label, "desc": f"Tie Time Black: {int(s_fail_time)}", "is_tie": True, "is_yearly": is_yearly})

    return t_m, t_s

def calculate_shame(df):
    """Calculates Monthly, Quarterly, and Yearly shame stats."""
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
        agg_row = yearly_agg[yearly_agg['Year'] == year_val].iloc[0]
        
        t_m, t_s = generate_shame_trophies_for_period(agg_row, daily_subset, str(int(year_val)), is_yearly=True)
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
        agg_row = quarterly_agg[quarterly_agg['Quarter'] == q_period].iloc[0]
        q_label = f"Q{q_period.quarter} {q_period.year}"
        
        t_m, t_s = generate_shame_trophies_for_period(agg_row, daily_subset, q_label, is_yearly=False)
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
        
        t_m, t_s = generate_shame_trophies_for_period(agg_row, daily_subset, m_label, is_yearly=False)
        monthly_m.extend(t_m)
        monthly_s.extend(t_s)

    return yearly_m, quarterly_m, monthly_m, yearly_s, quarterly_s, monthly_s

def create_trophy_html(icon, title, desc, is_tie=False, is_yearly=False):
    tie_class = " tie" if is_tie else ""
    yearly_class = " yearly" if is_yearly else ""
    return f'<div class="trophy-card{tie_class}{yearly_class}"><div class="trophy-icon">{icon}</div><div class="trophy-title">{title}</div><div class="trophy-desc">{desc}</div></div>'

# --- Header ---
st.title("Hall of Shame")
st.markdown("### The Wall of Misery")
st.markdown("<br>", unsafe_allow_html=True)

# --- Data Loading & Processing ---
df = load_data()
yearly_m, quarterly_m, monthly_m, yearly_s, quarterly_s, monthly_s = calculate_shame(df)

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
         m_html += '<div class="trophy-grid">' + "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t['is_yearly']) for t in yearly_m]) + '</div>'
         has_content = True
         
    if quarterly_m:
         m_html += get_separator("Quarterly")
         m_html += '<div class="trophy-grid">' + "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t['is_yearly']) for t in quarterly_m]) + '</div>'
         has_content = True

    if monthly_m:
         m_html += get_separator("Monthly")
         m_html += '<div class="trophy-grid">' + "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t['is_yearly']) for t in monthly_m]) + '</div>'
         has_content = True
    
    if not has_content:
        m_html = "<div style='text-align:center; color:#666; width:100%; padding: 20px;'>No shame found (yet).</div>"
    
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
         s_html += '<div class="trophy-grid">' + "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t['is_yearly']) for t in yearly_s]) + '</div>'
         has_content = True
         
    if quarterly_s:
         s_html += get_separator("Quarterly")
         s_html += '<div class="trophy-grid">' + "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t['is_yearly']) for t in quarterly_s]) + '</div>'
         has_content = True

    if monthly_s:
         s_html += get_separator("Monthly")
         s_html += '<div class="trophy-grid">' + "".join([create_trophy_html(t['icon'], t['title'], t['desc'], t['is_tie'], t['is_yearly']) for t in monthly_s]) + '</div>'
         has_content = True
    
    if not has_content:
        s_html = "<div style='text-align:center; color:#666; width:100%; padding: 20px;'>No shame found (yet).</div>"
    
    st.markdown(
        f'<div class="cabinet-container sarah-theme"><div class="cabinet-header sarah-text">Sarah</div>{s_html}</div>',
        unsafe_allow_html=True
    )