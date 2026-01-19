import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

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
        .stMarkdown p, label, h1, h2, h3, h4, h5, h6, .stTabs button, .stDataFrame, .stPlotlyChart {
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
        
        # Filter for valid rows (where both played)
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
st.markdown("### Day of the Week Performance")
st.markdown("Analyzing performance patterns across weekdays (Mon-Fri).", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

df = load_data()

if df is not None and not df.empty:
    # --- Data Processing ---
    df['Day'] = df['Date'].dt.day_name()
    
    # Filter only Mon-Fri
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    df = df[df['Day'].isin(days_order)].copy()
    df['Day'] = pd.Categorical(df['Day'], categories=days_order, ordered=True)
    
    # Calculate Wins & Margins
    df['Michael Win'] = (df['Michael Total Score'] > df['Sarah Total Score']).astype(int)
    df['Sarah Win'] = (df['Sarah Total Score'] > df['Michael Total Score']).astype(int)
    # Positive margin = Michael leads, Negative = Sarah leads
    df['Score Margin'] = df['Michael Total Score'] - df['Sarah Total Score'] 
    df['Abs Margin'] = df['Score Margin'].abs()
    
    # Aggregation
    daily_stats = df.groupby('Day', observed=False).agg({
        'Michael Total Score': 'mean',
        'Sarah Total Score': 'mean',
        'Michael Win': 'sum',
        'Sarah Win': 'sum',
        'Score Margin': 'mean', # Net Average Margin
        'Date': 'count'
    }).reset_index()
    
    daily_stats.rename(columns={
        'Michael Total Score': 'Michael Avg',
        'Sarah Total Score': 'Sarah Avg',
        'Score Margin': 'Avg Margin',
        'Date': 'Games Played'
    }, inplace=True)

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
        fig_avg.update_layout(
            font=dict(color="black", family="Poppins"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None, font=dict(color="black")),
            margin=dict(l=20, r=20, t=30, b=20),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', title="Average Score", title_font=dict(color="black"), tickfont=dict(color="black")),
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

    # --- 2. STATISTICAL ANALYSIS ---
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("#### 📐 Statistical Analysis")

    # -- Global Tests --
    m_p, m_sig = perform_kruskal_test(df, 'Michael Total Score')
    s_p, s_sig = perform_kruskal_test(df, 'Sarah Total Score')
    margin_p, margin_sig = perform_kruskal_test(df, 'Score Margin')

    # -- Identify Extremes (Michael) --
    m_best_row = daily_stats.loc[daily_stats['Michael Avg'].idxmax()]
    m_best_day = m_best_row['Day']
    m_worst_row = daily_stats.loc[daily_stats['Michael Avg'].idxmin()]
    m_worst_day = m_worst_row['Day']
    
    m_best_p, m_best_sig = perform_mannwhitney_test(df, 'Michael Total Score', m_best_day)
    m_worst_p, m_worst_sig = perform_mannwhitney_test(df, 'Michael Total Score', m_worst_day)

    # -- Identify Extremes (Sarah) --
    s_best_row = daily_stats.loc[daily_stats['Sarah Avg'].idxmax()]
    s_best_day = s_best_row['Day']
    s_worst_row = daily_stats.loc[daily_stats['Sarah Avg'].idxmin()]
    s_worst_day = s_worst_row['Day']
    
    s_best_p, s_best_sig = perform_mannwhitney_test(df, 'Sarah Total Score', s_best_day)
    s_worst_p, s_worst_sig = perform_mannwhitney_test(df, 'Sarah Total Score', s_worst_day)

    # -- Identify Extremes (Margin Gap - Based on Net Margin) --
    # Largest Gap = Largest absolute value of Avg Margin
    gap_largest_day = daily_stats.loc[daily_stats['Avg Margin'].abs().idxmax()]['Day']
    # Smallest Gap = Smallest absolute value of Avg Margin
    gap_smallest_day = daily_stats.loc[daily_stats['Avg Margin'].abs().idxmin()]['Day']
    
    # Testing Absolute Margin distributions for these specific days vs others
    # (Checking if the "tightness" of the game is significantly different on these days)
    df['Abs Margin'] = df['Score Margin'].abs()
    gap_largest_p, gap_largest_sig = perform_mannwhitney_test(df, 'Abs Margin', gap_largest_day)
    gap_smallest_p, gap_smallest_sig = perform_mannwhitney_test(df, 'Abs Margin', gap_smallest_day)

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

else:
    st.info("No data available to analyze.")