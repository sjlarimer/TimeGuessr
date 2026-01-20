import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import numpy as np

# --- Configuration ---
st.set_page_config(page_title="Analysis", layout="wide")

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
        /* Global Font */
        .stMarkdown p, label, h1, h2, h3, h4, h5, h6, .stTabs button, .stDataFrame, .stPlotlyChart, .stRadio label {
            font-family: 'Poppins', sans-serif !important;
        }
        h1, h2, h3 {
            color: #db5049 !important;
        }
        
        /* Container Styling */
        .analysis-container {
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            border: 1px solid rgba(0,0,0,0.05);
            background-color: white;
        }
        
        .stat-card {
            background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(245,245,255,0.9));
            border-radius: 10px;
            padding: 12px;
            text-align: center;
            border: 1px solid rgba(0,0,0,0.05);
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 10px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100px;
        }
        
        .stat-value {
            font-size: 1.2rem;
            font-weight: 800;
            color: #333;
            margin-bottom: 4px;
        }
        
        .stat-label {
            font-size: 0.7rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 2px;
        }

        /* Player Colors */
        .michael-text { color: #221e8f; font-weight: bold; }
        .sarah-text { color: #8a005c; font-weight: bold; }
        
        /* Significance Badge inside Card */
        .sig-badge-yes {
            background-color: #d4edda;
            color: #155724;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            margin-top: 4px;
            line-height: 1.2;
        }
        .sig-badge-no {
            background-color: #f8f9fa;
            color: #6c757d;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            margin-top: 4px;
            line-height: 1.2;
        }
        
        /* Mini Table Styling */
        .mini-table {
            background: #f9f9f9; 
            padding: 10px; 
            border-radius: 8px; 
            border: 1px solid #eee;
            margin-top: 15px;
        }
        .mini-table-header {
            font-size: 0.8rem; 
            text-transform: uppercase; 
            color: #666; 
            margin-bottom: 5px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 2px;
        }
        .mini-table-row {
            display: flex; 
            justify-content: space-between; 
            font-size: 0.85rem; 
            margin-bottom: 4px;
        }
        
        /* Divider for sections */
        .section-divider {
            margin-top: 30px; 
            margin-bottom: 20px; 
            border-bottom: 1px solid #eee;
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
        
        # Component Scores - Load and calculate Average of Min/Max
        df['Michael Geography Score (Min)'] = clean_col('Michael Geography Score (Min)')
        df['Michael Geography Score (Max)'] = clean_col('Michael Geography Score (Max)')
        df['Sarah Geography Score (Min)'] = clean_col('Sarah Geography Score (Min)')
        df['Sarah Geography Score (Max)'] = clean_col('Sarah Geography Score (Max)')
        
        df['M_Geo_Row'] = (df['Michael Geography Score (Min)'] + df['Michael Geography Score (Max)']) / 2
        df['S_Geo_Row'] = (df['Sarah Geography Score (Min)'] + df['Sarah Geography Score (Max)']) / 2

        df['Michael Time Score (Min)'] = clean_col('Michael Time Score (Min)')
        df['Michael Time Score (Max)'] = clean_col('Michael Time Score (Max)')
        df['Sarah Time Score (Min)'] = clean_col('Sarah Time Score (Min)')
        df['Sarah Time Score (Max)'] = clean_col('Sarah Time Score (Max)')

        df['M_Time_Row'] = (df['Michael Time Score (Min)'] + df['Michael Time Score (Max)']) / 2
        df['S_Time_Row'] = (df['Sarah Time Score (Min)'] + df['Sarah Time Score (Max)']) / 2
        
        # Filter for rows where data exists (Based on Total Score Presence)
        df = df[(df['Michael Total Score'] > 0) & (df['Sarah Total Score'] > 0)].copy()
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def perform_kruskal_test(df, col_name):
    """
    Performs Kruskal-Wallis H-test to see if scores differ significantly by Day.
    Returns p-value and a boolean for significance.
    """
    groups = []
    # Only analyze weekdays
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    for day in days_order:
        scores = df[df['Day'] == day][col_name].values
        if len(scores) > 0:
            groups.append(scores)
            
    if len(groups) < 2:
        return 1.0, False # Not enough data
        
    stat, p_value = stats.kruskal(*groups)
    return p_value, p_value < 0.05

def perform_mannwhitney_test(df, col_name, target_day):
    """
    Performs Mann-Whitney U test comparing target_day vs all other days.
    """
    group_target = df[df['Day'] == target_day][col_name].dropna().values
    group_others = df[df['Day'] != target_day][col_name].dropna().values
    
    if len(group_target) < 2 or len(group_others) < 2:
        return 1.0, False
        
    stat, p_value = stats.mannwhitneyu(group_target, group_others)
    return p_value, p_value < 0.05

def create_stat_card(label, value, sig_bool, sig_p, positive_msg, negative_msg):
    """Generates HTML for a stat card with integrated significance badge."""
    
    if sig_bool:
        badge_html = f'<div class="sig-badge-yes">{positive_msg} (p={sig_p:.3f})</div>'
    else:
        badge_html = f'<div class="sig-badge-no">{negative_msg} (p={sig_p:.3f})</div>'
        
    return f"""
    <div class="stat-card">
        <div class="stat-label">{label}</div>
        <div class="stat-value">{value}</div>
        {badge_html}
    </div>
    """

# --- Main Layout ---
st.title("Analysis")

# --- Metric Selector ---
metric_option = st.radio(
    "Select Metric to Analyze:",
    ("Total Score", "Geography Score", "Time Score"),
    horizontal=True
)

df_raw = load_data()

if df_raw is not None and not df_raw.empty:
    
    # --- CRITICAL STEP: Aggregate to Daily Level based on Selection ---
    # The raw data contains rows per round. We aggregate to 1 row per Calendar Date.
    
    if metric_option == "Total Score":
        # Total score is already a daily sum in the raw data (populated on every row)
        agg_cols = {'Michael Total Score': 'max', 'Sarah Total Score': 'max'}
        rename_map = {'Michael Total Score': 'Michael Score', 'Sarah Total Score': 'Sarah Score'}
    elif metric_option == "Geography Score":
        # Component scores are per-row, so we SUM them for the daily total
        agg_cols = {'M_Geo_Row': 'sum', 'S_Geo_Row': 'sum'}
        rename_map = {'M_Geo_Row': 'Michael Score', 'S_Geo_Row': 'Sarah Score'}
    else: # Time Score
        agg_cols = {'M_Time_Row': 'sum', 'S_Time_Row': 'sum'}
        rename_map = {'M_Time_Row': 'Michael Score', 'S_Time_Row': 'Sarah Score'}

    df = df_raw.groupby('Date').agg(agg_cols).reset_index()
    df.rename(columns=rename_map, inplace=True)

    # --- Data Processing on DAILY DataFrame ---
    df['Day'] = df['Date'].dt.day_name()
    
    # Filter only Mon-Fri for Day Analysis
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    df_weekdays = df[df['Day'].isin(days_order)].copy()
    df_weekdays['Day'] = pd.Categorical(df_weekdays['Day'], categories=days_order, ordered=True)
    
    # Calculate Wins & Margins
    df['Michael Win'] = (df['Michael Score'] > df['Sarah Score']).astype(int)
    df['Sarah Win'] = (df['Sarah Score'] > df['Michael Score']).astype(int)
    df['Score Margin'] = df['Michael Score'] - df['Sarah Score'] 
    df['Abs Margin'] = df['Score Margin'].abs()
    
    # Sync cols to df_weekdays
    df_weekdays['Michael Win'] = df['Michael Win']
    df_weekdays['Sarah Win'] = df['Sarah Win']
    df_weekdays['Score Margin'] = df['Score Margin']
    df_weekdays['Abs Margin'] = df['Abs Margin']

    # Aggregation for Charts
    daily_stats = df_weekdays.groupby('Day', observed=False).agg({
        'Michael Score': 'mean',
        'Sarah Score': 'mean',
        'Michael Win': 'sum',
        'Sarah Win': 'sum',
        'Score Margin': 'mean', # Net Average Margin
        'Date': 'count'
    }).reset_index()
    
    daily_stats.rename(columns={
        'Michael Score': 'Michael Avg',
        'Sarah Score': 'Sarah Avg',
        'Score Margin': 'Avg Margin',
        'Date': 'Games Played'
    }, inplace=True)

    # ==========================================
    # SECTION 1: DAY OF THE WEEK ANALYSIS
    # ==========================================
    st.markdown(f"### Day of the Week Performance ({metric_option})")
    st.markdown("Analyzing performance patterns across weekdays (Mon-Fri).", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- 1. VISUALS (Plotly) ---
    
    # Prepare Data for Charts (Long Format)
    score_melted = daily_stats.melt(id_vars=['Day'], value_vars=['Michael Avg', 'Sarah Avg'], var_name='Player', value_name='Score')
    score_melted['Player'] = score_melted['Player'].str.replace(' Avg', '')
    
    wins_melted = daily_stats.melt(id_vars=['Day'], value_vars=['Michael Win', 'Sarah Win'], var_name='Player', value_name='Wins')
    wins_melted['Player'] = wins_melted['Player'].str.replace(' Win', '')

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 📊 Average Score by Day")
        fig_avg = px.bar(
            score_melted, 
            x="Day", 
            y="Score", 
            color="Player", 
            barmode="group",
            # Removed text="Score" to remove numbers from bars
            color_discrete_map={'Michael': '#221e8f', 'Sarah': '#8a005c'},
            height=350
        )
        fig_avg.update_traces(textposition='none')
        fig_avg.update_layout(
            font=dict(color="black", family="Poppins"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None, font=dict(color="black")),
            margin=dict(l=20, r=20, t=30, b=20),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', title=f"Average {metric_option}", title_font=dict(color="black"), tickfont=dict(color="black")),
            xaxis=dict(title=None, tickfont=dict(color="black"))
        )
        st.plotly_chart(fig_avg, use_container_width=True)

    with col2:
        st.markdown("##### 🏆 Total Wins by Day")
        fig_wins = px.bar(
            wins_melted, 
            x="Day", 
            y="Wins", 
            color="Player", 
            barmode="group",
            # Removed text="Wins" to remove numbers from bars
            color_discrete_map={'Michael': '#221e8f', 'Sarah': '#8a005c'},
            height=350
        )
        fig_wins.update_traces(textposition='none')
        fig_wins.update_layout(
            font=dict(color="black", family="Poppins"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None, font=dict(color="black")),
            margin=dict(l=20, r=20, t=30, b=20),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', title="Total Wins", title_font=dict(color="black"), tickfont=dict(color="black")),
            xaxis=dict(title=None, tickfont=dict(color="black"))
        )
        st.plotly_chart(fig_wins, use_container_width=True)

    # --- 2. DETAILED STATS (Integrated) ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 0.9rem; color: #555; margin-bottom: 20px;">
    Statistical tests (Kruskal-Wallis & Mann-Whitney U) check if performance differences are real or just luck. 
    A <b>significant</b> result (p < 0.05) means the day of the week likely matters.
    </div>
    """, unsafe_allow_html=True)

    # -- Global Tests --
    m_p, m_sig = perform_kruskal_test(df_weekdays, 'Michael Score')
    s_p, s_sig = perform_kruskal_test(df_weekdays, 'Sarah Score')
    margin_p, margin_sig = perform_kruskal_test(df_weekdays, 'Score Margin')

    # -- Identify Extremes (Michael) --
    m_best_row = daily_stats.loc[daily_stats['Michael Avg'].idxmax()]
    m_best_day = m_best_row['Day']
    m_worst_row = daily_stats.loc[daily_stats['Michael Avg'].idxmin()]
    m_worst_day = m_worst_row['Day']
    
    m_best_p, m_best_sig = perform_mannwhitney_test(df_weekdays, 'Michael Score', m_best_day)
    m_worst_p, m_worst_sig = perform_mannwhitney_test(df_weekdays, 'Michael Score', m_worst_day)

    # -- Identify Extremes (Sarah) --
    s_best_row = daily_stats.loc[daily_stats['Sarah Avg'].idxmax()]
    s_best_day = s_best_row['Day']
    s_worst_row = daily_stats.loc[daily_stats['Sarah Avg'].idxmin()]
    s_worst_day = s_worst_row['Day']
    
    s_best_p, s_best_sig = perform_mannwhitney_test(df_weekdays, 'Sarah Score', s_best_day)
    s_worst_p, s_worst_sig = perform_mannwhitney_test(df_weekdays, 'Sarah Score', s_worst_day)

    # -- Identify Extremes (Margin Gap - Based on Net Margin) --
    gap_largest_day = daily_stats.loc[daily_stats['Avg Margin'].abs().idxmax()]['Day']
    gap_smallest_day = daily_stats.loc[daily_stats['Avg Margin'].abs().idxmin()]['Day']
    
    gap_largest_p, gap_largest_sig = perform_mannwhitney_test(df_weekdays, 'Abs Margin', gap_largest_day)
    gap_smallest_p, gap_smallest_sig = perform_mannwhitney_test(df_weekdays, 'Abs Margin', gap_smallest_day)

    # -- Display Cards --
    col1, col2, col3 = st.columns(3, gap="medium")

    # PLAYER 1 STATS
    with col1:
        st.markdown(f'<div class="michael-text" style="font-size:1.2rem; border-bottom: 2px solid #221e8f; padding-bottom: 5px; margin-bottom: 10px;">Michael</div>', unsafe_allow_html=True)
        
        # Overall
        st.markdown("**Does day matter overall?**")
        if m_sig:
            st.markdown(f'<div class="sig-badge-yes">Yes (p={m_p:.3f})</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="sig-badge-no">No (p={m_p:.3f})</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Best/Worst Cards
        st.markdown(create_stat_card("Best Day", m_best_day, m_best_sig, m_best_p, "Significantly better!", "Just a lucky trend"), unsafe_allow_html=True)
        st.markdown(create_stat_card("Worst Day", m_worst_day, m_worst_sig, m_worst_p, "Significantly worse!", "Just a slump"), unsafe_allow_html=True)

        # Mini Table
        m_table_html = ""
        for index, row in daily_stats.iterrows():
            m_table_html += f"<div class='mini-table-row'><span>{row['Day']}</span><span style='font-weight:bold;'>{row['Michael Avg']:,.0f}</span></div>"
        
        st.markdown(f"""
        <div class="mini-table">
            <div class="mini-table-header">Avg Score by Day</div>
            {m_table_html}
        </div>
        """, unsafe_allow_html=True)

    # PLAYER 2 STATS
    with col2:
        st.markdown(f'<div class="sarah-text" style="font-size:1.2rem; border-bottom: 2px solid #8a005c; padding-bottom: 5px; margin-bottom: 10px;">Sarah</div>', unsafe_allow_html=True)
        
        # Overall
        st.markdown("**Does day matter overall?**")
        if s_sig:
            st.markdown(f'<div class="sig-badge-yes">Yes (p={s_p:.3f})</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="sig-badge-no">No (p={s_p:.3f})</div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Best/Worst Cards
        st.markdown(create_stat_card("Best Day", s_best_day, s_best_sig, s_best_p, "Significantly better!", "Just a lucky trend"), unsafe_allow_html=True)
        st.markdown(create_stat_card("Worst Day", s_worst_day, s_worst_sig, s_worst_p, "Significantly worse!", "Just a slump"), unsafe_allow_html=True)

        # Mini Table
        s_table_html = ""
        for index, row in daily_stats.iterrows():
            s_table_html += f"<div class='mini-table-row'><span>{row['Day']}</span><span style='font-weight:bold;'>{row['Sarah Avg']:,.0f}</span></div>"
        
        st.markdown(f"""
        <div class="mini-table">
            <div class="mini-table-header">Avg Score by Day</div>
            {s_table_html}
        </div>
        """, unsafe_allow_html=True)

    # MARGIN STATS
    with col3:
        st.markdown(f'<div style="color:#333; font-weight:bold; font-size:1.2rem; border-bottom: 2px solid #333; padding-bottom: 5px; margin-bottom: 10px;">Head-to-Head Margin</div>', unsafe_allow_html=True)
        
        st.markdown("**Does gap vary by day?**")
        if margin_sig:
            st.markdown(f'<div class="sig-badge-yes">Yes (p={margin_p:.3f})</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="sig-badge-no">No (p={margin_p:.3f})</div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gap Cards
        st.markdown(create_stat_card("Largest Gap", gap_largest_day, gap_largest_sig, gap_largest_p, "Truly a blowout!", "Just variance"), unsafe_allow_html=True)
        st.markdown(create_stat_card("Smallest Gap", gap_smallest_day, gap_smallest_sig, gap_smallest_p, "Consistently tight!", "Randomly close"), unsafe_allow_html=True)
        
        # Mini Table (Margin)
        daily_margin_html = ""
        for index, row in daily_stats.iterrows():
            d = row['Day']
            marg = row['Avg Margin']
            color = "#221e8f" if marg > 0 else "#8a005c"
            player = "Michael" if marg > 0 else "Sarah"
            daily_margin_html += f"<div class='mini-table-row'><span>{d}</span><span style='color:{color}; font-weight:bold;'>{player} +{abs(marg):.0f}</span></div>"
        
        st.markdown(f"""
        <div class="mini-table">
            <div class="mini-table-header">Avg Lead by Day</div>
            {daily_margin_html}
        </div>
        """, unsafe_allow_html=True)

    # ==========================================
    # SECTION 2: RUST FACTOR ANALYSIS
    # ==========================================
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### ⚙️ Rust Factor Analysis")
    st.markdown("""
    <div style="font-size: 0.9rem; color: #555; margin-bottom: 20px;">
    Does taking a break affect performance? We analyze scores based on the gap since the last game played.
    <br><b>Flow</b>: Consecutive business days (Weekends ignored). <b>Short Break</b>: 1-4 missed business days. <b>Long Break</b>: 5+ missed business days.
    </div>
    """, unsafe_allow_html=True)

    # Sort by date
    df_rust = df.sort_values('Date').copy()
    
    # Calculate Business Days Diff using numpy
    dates = df_rust['Date'].values.astype('datetime64[D]')
    # Create shifted array for previous dates
    prev_dates = np.roll(dates, 1)
    prev_dates[0] = dates[0] # Handle first element to avoid massive diff
    
    # np.busday_count calculates [start, end) excluding end.
    # Consecutive days (Fri -> Mon) gives 1.
    # Mon -> Tue gives 1.
    # Mon -> Thu gives 3.
    
    # We apply busday_count to the full arrays
    # Note: busday_count raises error if dates are not valid dates (NaT). data is clean here.
    bus_diffs = np.busday_count(prev_dates, dates)
    
    # First element diff is invalid, set to 1 (Flow) or 0
    bus_diffs[0] = 1 
    
    df_rust['Bus_Diff'] = bus_diffs

    # Define categories based on business day difference
    def get_break_category(diff):
        if diff <= 1: return 'Flow' # Consecutive business days (0 missed)
        if 2 <= diff <= 5: return 'Short Break' # 1 to 4 missed days
        if diff >= 6: return 'Long Break' # 5+ missed days
        return 'N/A'

    df_rust['State'] = df_rust['Bus_Diff'].apply(get_break_category)
    df_rust = df_rust[df_rust['State'] != 'N/A']
    
    # Define order
    state_order = ['Flow', 'Short Break', 'Long Break']
    df_rust['State'] = pd.Categorical(df_rust['State'], categories=state_order, ordered=True)

    # Group Stats
    rust_stats = df_rust.groupby('State', observed=False).agg({
        'Michael Score': 'mean',
        'Sarah Score': 'mean',
        'Date': 'count'
    }).reset_index()
    
    # Extract counts safely for display
    def get_count(state_name):
        row = rust_stats[rust_stats['State'] == state_name]
        return row['Date'].values[0] if not row.empty else 0

    n_flow = get_count('Flow')
    n_short = get_count('Short Break')
    n_long = get_count('Long Break')

    st.markdown(f"""
    <div style="font-size:0.85rem; color:#666; margin-bottom:15px;">
        <span style="background:#eafaf1; padding:2px 6px; border-radius:4px; border:1px solid #2ECC71; margin-right:5px;">Flow: {n_flow} games</span>
        <span style="background:#fef5e7; padding:2px 6px; border-radius:4px; border:1px solid #F39C12; margin-right:5px;">Short Break: {n_short} games</span>
        <span style="background:#fdedec; padding:2px 6px; border-radius:4px; border:1px solid #E74C3C;">Long Break: {n_long} games</span>
    </div>
    """, unsafe_allow_html=True)

    # Reshape for Plotly
    rust_melted = rust_stats.melt(id_vars=['State'], value_vars=['Michael Score', 'Sarah Score'], var_name='Player', value_name='Avg Score')
    rust_melted['Player'] = rust_melted['Player'].str.replace(' Score', '')

    col_rust1, col_rust2 = st.columns([2, 1])

    with col_rust1:
        fig_rust = px.bar(
            rust_melted,
            x="Player",
            y="Avg Score",
            color="State",
            barmode="group",
            color_discrete_map={
                'Flow': '#2ECC71', 
                'Short Break': '#F39C12', 
                'Long Break': '#E74C3C'
            },
            height=350
        )
        fig_rust.update_traces(textposition='none') # Removes text from bars
        fig_rust.update_layout(
            font=dict(color="black", family="Poppins"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None, font=dict(color="black")),
            margin=dict(l=20, r=20, t=30, b=20),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', title="Average Score", title_font=dict(color="black"), tickfont=dict(color="black")),
            xaxis=dict(title=None, tickfont=dict(color="black"))
        )
        st.plotly_chart(fig_rust, use_container_width=True)

    with col_rust2:
        st.markdown("#### Impact Analysis")
        
        # We compare Breaks vs Flow
        for player, col in [("Michael", 'Michael Score'), ("Sarah", 'Sarah Score')]:
            # Determine player text class
            player_class = "michael-text" if player == "Michael" else "sarah-text"
            st.markdown(f'<div class="{player_class}" style="font-size:1rem; margin-top:10px; border-bottom:1px solid #eee;">{player}</div>', unsafe_allow_html=True)
            
            flow_scores = df_rust[df_rust['State'] == 'Flow'][col]
            avg_flow = flow_scores.mean() if not flow_scores.empty else 0
            
            # Compare Short Break (Weekend-Long)
            short_scores = df_rust[df_rust['State'] == 'Short Break'][col]
            if len(flow_scores) > 1 and len(short_scores) > 1:
                stat, p_val = stats.mannwhitneyu(short_scores, flow_scores)
                diff = short_scores.mean() - avg_flow
                color = "#d9534f" if diff < 0 else "#5cb85c"
                sig_text = f"(p={p_val:.3f})" if p_val < 0.05 else ""
                
                st.markdown(f"""
                <div style="font-size:0.85rem; display:flex; justify-content:space-between;">
                    <span>vs Short:</span>
                    <span style="color:{color}; font-weight:bold;">{diff:+,.0f} {sig_text}</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Compare Long Break
            long_scores = df_rust[df_rust['State'] == 'Long Break'][col]
            if len(flow_scores) > 1 and len(long_scores) > 1:
                stat, p_val = stats.mannwhitneyu(long_scores, flow_scores)
                diff = long_scores.mean() - avg_flow
                color = "#d9534f" if diff < 0 else "#5cb85c"
                sig_text = f"(p={p_val:.3f})" if p_val < 0.05 else ""
                
                st.markdown(f"""
                <div style="font-size:0.85rem; display:flex; justify-content:space-between;">
                    <span>vs Long:</span>
                    <span style="color:{color}; font-weight:bold;">{diff:+,.0f} {sig_text}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                 st.markdown(f"<div style='font-size:0.8rem; color:#999;'>Not enough data for long breaks</div>", unsafe_allow_html=True)

    # ==========================================
    # SECTION 3: HOT HAND FALLACY
    # ==========================================
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 🎲 Hot Hand Fallacy Check")
    st.markdown("""
    <div style="font-size: 0.9rem; color: #555; margin-bottom: 20px;">
    Does winning yesterday increase the chances of winning today (Momentum)? Or does it make a loss more likely (Bounce Back)?
    We compare win rates immediately following a <b>Win</b> vs. immediately following a <b>Loss</b>.
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("ℹ️ How to interpret these numbers?"):
        st.markdown("""
        * **The Comparison:** We compare **Win Rate after a Win** vs. **Win Rate after a Loss**.
        * **Momentum (Green):** If you are *more likely* to win after winning than after losing (e.g., 30% vs 10%), that is a momentum effect, even if the absolute win rate (30%) is low.
        * **Bounce Back (Red):** If you are *more likely* to win after losing than after winning (e.g., winning after a loss is 60%, but after a win is only 40%), that suggests an alternating pattern.
        * **Why is it identical for both players?** In a zero-sum game (Win/Loss), momentum is mathematically symmetrical. If Player A has momentum (likely to win after winning), Player B must effectively be likely to lose after losing (which is the same state). The numbers mirror each other perfectly.
        """)

    # Sort by date (using the DAILY df)
    df_streak = df.sort_values('Date').copy()

    # Calculate lagged wins (1 day)
    df_streak['Michael Prev Win'] = df_streak['Michael Win'].shift(1)
    df_streak['Sarah Prev Win'] = df_streak['Sarah Win'].shift(1)
    
    # Calculate lagged wins (2 days)
    df_streak['Michael Prev Win 2'] = df_streak['Michael Win'].shift(2)
    df_streak['Sarah Prev Win 2'] = df_streak['Sarah Win'].shift(2)

    # Calculate lagged wins (3 days)
    df_streak['Michael Prev Win 3'] = df_streak['Michael Win'].shift(3)
    df_streak['Sarah Prev Win 3'] = df_streak['Sarah Win'].shift(3)

    # Calculate lagged wins (4 days)
    df_streak['Michael Prev Win 4'] = df_streak['Michael Win'].shift(4)
    df_streak['Sarah Prev Win 4'] = df_streak['Sarah Win'].shift(4)

    # Drop rows where lag 2 is NaN (first 2 rows) to ensure consistent data for all metrics if desired,
    # but to maximize data for 1-lag, we can just filter. Let's just filter in loop.

    col_hot1, col_hot2 = st.columns([2, 1])

    hot_data = []
    
    # Calculate stats
    for player, win_col, prev1, prev2, prev3, prev4 in [
        ("Michael", "Michael Win", "Michael Prev Win", "Michael Prev Win 2", "Michael Prev Win 3", "Michael Prev Win 4"), 
        ("Sarah", "Sarah Win", "Sarah Prev Win", "Sarah Prev Win 2", "Sarah Prev Win 3", "Sarah Prev Win 4")
    ]:
        # Helper function
        def get_rate_count(mask):
            subset = df_streak[mask]
            count = len(subset)
            rate = subset[win_col].mean() * 100 if count > 0 else 0
            return rate, count

        # 1. After 1 Win
        rate_1w, count_1w = get_rate_count(df_streak[prev1] == 1)
        
        # 2. After 1 Loss
        rate_1l, count_1l = get_rate_count(df_streak[prev1] == 0)
        
        # 3. After 2 Wins
        rate_2w, count_2w = get_rate_count((df_streak[prev1] == 1) & (df_streak[prev2] == 1))
        
        # 4. After 2 Losses
        rate_2l, count_2l = get_rate_count((df_streak[prev1] == 0) & (df_streak[prev2] == 0))

        # 5. After 3 Wins
        rate_3w, count_3w = get_rate_count((df_streak[prev1] == 1) & (df_streak[prev2] == 1) & (df_streak[prev3] == 1))

        # 6. After 3 Losses
        rate_3l, count_3l = get_rate_count((df_streak[prev1] == 0) & (df_streak[prev2] == 0) & (df_streak[prev3] == 0))

        # 7. After 4 Wins
        rate_4w, count_4w = get_rate_count((df_streak[prev1] == 1) & (df_streak[prev2] == 1) & (df_streak[prev3] == 1) & (df_streak[prev4] == 1))

        # 8. After 4 Losses
        rate_4l, count_4l = get_rate_count((df_streak[prev1] == 0) & (df_streak[prev2] == 0) & (df_streak[prev3] == 0) & (df_streak[prev4] == 0))
        
        # Helper to format text
        def fmt(rate, count):
            return f"{rate:.1f}% (n={count})"

        hot_data.append({'Player': player, 'Context': 'After 1 Win', 'Win Rate': rate_1w, 'Label': fmt(rate_1w, count_1w)})
        hot_data.append({'Player': player, 'Context': 'After 2 Wins', 'Win Rate': rate_2w, 'Label': fmt(rate_2w, count_2w)})
        hot_data.append({'Player': player, 'Context': 'After 3 Wins', 'Win Rate': rate_3w, 'Label': fmt(rate_3w, count_3w)})
        
        hot_data.append({'Player': player, 'Context': 'After 1 Loss', 'Win Rate': rate_1l, 'Label': fmt(rate_1l, count_1l)})
        hot_data.append({'Player': player, 'Context': 'After 2 Losses', 'Win Rate': rate_2l, 'Label': fmt(rate_2l, count_2l)})
        hot_data.append({'Player': player, 'Context': 'After 3 Losses', 'Win Rate': rate_3l, 'Label': fmt(rate_3l, count_3l)})

    hot_df = pd.DataFrame(hot_data)

    # Force order of bars
    cat_order = [
        'After 1 Win', 'After 2 Wins', 'After 3 Wins',
        'After 1 Loss', 'After 2 Losses', 'After 3 Losses'
    ]
    hot_df['Context'] = pd.Categorical(hot_df['Context'], categories=cat_order, ordered=True)
    hot_df = hot_df.sort_values('Context')

    with col_hot1:
        fig_hot = px.bar(
            hot_df,
            x="Player",
            y="Win Rate",
            color="Context",
            barmode="group",
            text="Label",
            color_discrete_map={
                'After 1 Win': '#2ECC71', 
                'After 2 Wins': '#27AE60', # Darker Green
                'After 3 Wins': '#229954', # Even Darker Green
                'After 1 Loss': '#E74C3C',
                'After 2 Losses': '#C0392B', # Darker Red
                'After 3 Losses': '#922B21' # Even Darker Red
            },
            height=500 
        )
        fig_hot.update_traces(textposition='outside', textfont_color="black")
        fig_hot.update_layout(
            font=dict(color="black", family="Poppins"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None, font=dict(color="black")),
            margin=dict(l=20, r=20, t=30, b=20),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', title="Win Rate (%)", title_font=dict(color="black"), tickfont=dict(color="black")),
            xaxis=dict(title=None, tickfont=dict(color="black"))
        )
        st.plotly_chart(fig_hot, use_container_width=True)

    with col_hot2:
        st.markdown("#### Momentum Analysis")
        st.markdown("<div style='font-size:0.8rem; color:#666; margin-bottom:10px;'>Comparing 1-day, 2-day, and 3-day lag effects.</div>", unsafe_allow_html=True)
        
        for player, win_col, prev_win_col, prev_win_col2, prev_win_col3 in [
            ("Michael", "Michael Win", "Michael Prev Win", "Michael Prev Win 2", "Michael Prev Win 3"), 
            ("Sarah", "Sarah Win", "Sarah Prev Win", "Sarah Prev Win 2", "Sarah Prev Win 3")
        ]:
            player_class = "michael-text" if player == "Michael" else "sarah-text"
            st.markdown(f'<div class="{player_class}" style="font-size:1rem; margin-top:10px; border-bottom:1px solid #eee;">{player}</div>', unsafe_allow_html=True)
            
            # --- 1 Day Analysis ---
            wins_after_win = df_streak[df_streak[prev_win_col] == 1][win_col]
            wins_after_loss = df_streak[df_streak[prev_win_col] == 0][win_col]
            
            ww = wins_after_win.sum()
            lw = wins_after_win.count() - ww
            wl = wins_after_loss.sum()
            ll = wins_after_loss.count() - wl
            
            contingency = [[ww, lw], [wl, ll]]
            
            n_after_win = ww + lw
            n_after_loss = wl + ll
            
            rate_ww = (ww / n_after_win) * 100 if n_after_win > 0 else 0
            rate_wl = (wl / n_after_loss) * 100 if n_after_loss > 0 else 0
            diff = rate_ww - rate_wl
            
            try:
                chi2, p_val, dof, ex = stats.chi2_contingency(contingency)
            except:
                p_val = 1.0
            
            trend = "Momentum" if diff > 0 else "Bounce Back"
            color = "#2ECC71" if diff > 0 else "#E74C3C" 
            
            st.markdown(f"""
            <div style="font-size:0.85rem; margin-bottom:8px; padding-bottom:4px; border-bottom:1px solid #f0f0f0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span><b>1-Day Trend:</b></span>
                    <span style="font-weight:bold; color:{color};">{trend}</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span>Effect:</span>
                    <span>{diff:+.1f}% (p={p_val:.3f})</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- 2 Day Analysis ---
            mask_2w = (df_streak[prev_win_col] == 1) & (df_streak[prev_win_col2] == 1)
            mask_2l = (df_streak[prev_win_col] == 0) & (df_streak[prev_win_col2] == 0)
            
            wins_after_2w = df_streak[mask_2w][win_col]
            wins_after_2l = df_streak[mask_2l][win_col]
            
            w2w = wins_after_2w.sum()
            l2w = wins_after_2w.count() - w2w
            w2l = wins_after_2l.sum()
            l2l = wins_after_2l.count() - w2l
            
            contingency2 = [[w2w, l2w], [w2l, l2l]]
            
            rate_2w = (w2w / (w2w + l2w)) * 100 if (w2w + l2w) > 0 else 0
            rate_2l = (w2l / (w2l + l2l)) * 100 if (w2l + l2l) > 0 else 0
            diff2 = rate_2w - rate_2l
            
            try:
                chi2_2, p_val_2, dof_2, ex_2 = stats.chi2_contingency(contingency2)
            except:
                p_val_2 = 1.0
                
            trend2 = "Momentum" if diff2 > 0 else "Bounce Back"
            color2 = "#2ECC71" if diff2 > 0 else "#E74C3C"
            
            st.markdown(f"""
            <div style="font-size:0.85rem; margin-bottom:8px; padding-bottom:4px; border-bottom:1px solid #f0f0f0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span><b>2-Day Trend:</b></span>
                    <span style="font-weight:bold; color:{color2};">{trend2}</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span>Effect:</span>
                    <span>{diff2:+.1f}% (p={p_val_2:.3f})</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- 3 Day Analysis ---
            mask_3w = (df_streak[prev_win_col] == 1) & (df_streak[prev_win_col2] == 1) & (df_streak[prev_win_col3] == 1)
            mask_3l = (df_streak[prev_win_col] == 0) & (df_streak[prev_win_col2] == 0) & (df_streak[prev_win_col3] == 0)
            
            wins_after_3w = df_streak[mask_3w][win_col]
            wins_after_3l = df_streak[mask_3l][win_col]
            
            w3w = wins_after_3w.sum()
            l3w = wins_after_3w.count() - w3w
            w3l = wins_after_3l.sum()
            l3l = wins_after_3l.count() - w3l
            
            contingency3 = [[w3w, l3w], [w3l, l3l]]
            
            rate_3w = (w3w / (w3w + l3w)) * 100 if (w3w + l3w) > 0 else 0
            rate_3l = (w3l / (w3l + l3l)) * 100 if (w3l + l3l) > 0 else 0
            diff3 = rate_3w - rate_3l
            
            try:
                chi2_3, p_val_3, dof_3, ex_3 = stats.chi2_contingency(contingency3)
            except:
                p_val_3 = 1.0
                
            trend3 = "Momentum" if diff3 > 0 else "Bounce Back"
            color3 = "#2ECC71" if diff3 > 0 else "#E74C3C"
            
            st.markdown(f"""
            <div style="font-size:0.85rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span><b>3-Day Trend:</b></span>
                    <span style="font-weight:bold; color:{color3};">{trend3}</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span>Effect:</span>
                    <span>{diff3:+.1f}% (p={p_val_3:.3f})</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Overall Sig Badge
            if p_val < 0.05 or p_val_2 < 0.05 or p_val_3 < 0.05:
                 st.markdown(f'<div class="sig-badge-yes" style="margin-top:5px;">Significant!</div>', unsafe_allow_html=True)
            else:
                 st.markdown(f'<div class="sig-badge-no" style="margin-top:5px;">Not Significant</div>', unsafe_allow_html=True)

else:
    st.info("No data available to analyze.")