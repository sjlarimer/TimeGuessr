import streamlit as st
import pandas as pd
from PIL import Image
import numpy as np

# --- Configuration ---
st.set_page_config(page_title="Welcome", layout='wide')

# --- Load Global CSS ---
try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# --- Custom Page Styles ---
st.markdown(
    """
    <style>
        /* Modern Card Styling */
        .info-card {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            border: 1px solid #eee;
            height: 100%; /* Fill flex container */
            box-sizing: border-box;
        }
        
        /* Flex Container for Equal Height Cards */
        .flex-row {
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
            margin-bottom: 2rem;
        }
        
        .flex-col-overview {
            flex: 1.4; /* Wider column */
            min-width: 300px;
        }
        
        .flex-col-legend {
            flex: 1; /* Narrower column */
            min-width: 300px;
        }
        
        .stat-card {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 5px solid #db5049;
            text-align: center;
        }
        
        /* Typography */
        h1, h2, h3 {
            font-family: 'Poppins', sans-serif;
            color: #db5049 !important;
        }
        
        .big-number {
            font-size: 2rem;
            font-weight: 700;
            color: #333;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Table Styling */
        .stat-table {
            width: 100%;
            font-family: 'Poppins', sans-serif;
            font-size: 16px;
            border-collapse: separate;
            border-spacing: 0;
            background-color: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin: 20px 0;
        }
        
        .stat-table th {
            text-align: center;
            padding: 15px;
            background-color: #db5049;
            color: white !important;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 14px;
            letter-spacing: 0.5px;
        }
        
        .stat-table th:first-child {
            text-align: left;
            padding-left: 20px;
        }
        
        .stat-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
            color: #444;
        }
        
        .stat-table tr:last-child td {
            border-bottom: none;
        }
        
        .stat-val {
            font-weight: 700;
            text-align: center;
            color: #222;
        }
        
        .stat-row-label {
            font-weight: 500;
            padding-left: 20px !important;
        }
        
        /* Compact Legend Table Styling */
        .compact-legend {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px; /* Slightly adjusted size */
            font-family: 'Poppins', sans-serif;
        }
        .compact-legend th {
            text-align: left;
            padding: 5px 8px;
            font-size: 11px;
            text-transform: uppercase;
            color: #999;
            border-bottom: 1px solid #eee;
            font-weight: 600;
        }
        .compact-legend td {
            padding: 4px 8px;
            color: #555;
            border-bottom: 1px solid #f5f5f5;
        }
        .compact-legend tr:last-child td {
            border-bottom: none;
        }
        .emoji-col {
            font-family: 'Segoe UI Emoji', 'Roboto', sans-serif;
            letter-spacing: 1px;
            font-size: 14px;
        }
        
        /* Activity Log Styling */
        .activity-table-container {
            max-height: 600px;
            overflow-y: auto;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border: 1px solid #eee;
            background: white;
        }
        .activity-table {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
        }
        .activity-table thead {
            position: sticky;
            top: 0;
            z-index: 10;
            background-color: #db5049;
        }
        .activity-table th {
            color: white !important;
            font-weight: 600;
            padding: 15px;
            text-align: left;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
        }
        .activity-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
            color: #444;
            vertical-align: middle;
        }
        /* Override inline style on hover with !important */
        .activity-table tr:hover td {
            background-color: #eaeaea !important; 
        }
        .loc-city {
            font-weight: 600;
            color: #333;
            display: block;
        }
        .loc-country {
            font-size: 12px;
            color: #888;
            display: block;
            margin-top: 2px;
        }
        .score-val {
            font-weight: 600;
            font-variant-numeric: tabular-nums;
        }
        .score-m { color: #221e8f; }
        .score-s { color: #8a005c; }
        
        /* Scrollbar Styling for Activity Log */
        .activity-table-container::-webkit-scrollbar {
            width: 8px;
        }
        .activity-table-container::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 0 12px 12px 0;
        }
        .activity-table-container::-webkit-scrollbar-thumb {
            background: #ccc;
            border-radius: 4px;
        }
        .activity-table-container::-webkit-scrollbar-thumb:hover {
            background: #bbb;
        }
        
        /* Link Styling */
        a {
            color: #db5049;
            text-decoration: none;
            transition: color 0.3s;
        }
        a:hover {
            color: #b03d36;
            text-decoration: underline;
        }

        /* --- Force Streamlit Columns to Equal Height --- */
        [data-testid="column"] {
            display: flex;
            flex-direction: column;
        }
        [data-testid="column"] > div {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        /* Target the internal markdown container */
        [data-testid="column"] > div > div {
            flex: 1;
        }
        /* Target the div wrapping the HTML content */
        [data-testid="column"] > div > div > div {
            height: 100%;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header Section (Centered) ---
head_c1, head_c2, head_c3 = st.columns([1, 2, 1])

with head_c2:
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem; margin-bottom: 10px;'>Michael & Sarah</h1>", unsafe_allow_html=True)

    # --- Top Image ---
    try:
        img = Image.open("Images/home.png")
        width, height = img.size
        crop_height = int(height * 0.75)
        img_cropped = img.crop((0, 0, width, crop_height))
        st.image(img_cropped, use_container_width=True)
    except FileNotFoundError:
        st.warning("Cover image not found.")
        
    st.markdown("<h1 style='text-align: center; margin-top: 0;'>Tracking</h1>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<br>", unsafe_allow_html=True)

# --- Combined Overview & Legend Section ---
st.markdown(
    """<div class="flex-row"><div class="flex-col-overview"><div class="info-card"><h2 style="margin-top: 0;">Overview</h2><div style='font-family: Poppins; font-size: 16px; line-height: 1.8; color: #444;'>TimeGuessr is a daily geography and history browser game that challenges players to identify the context of historical photographs.<br><br>Each day, players are presented with five rounds. In each round, an image is revealed, and the goal is to:<ul style="margin-bottom: 1rem;"><li><b>Guess the Location:</b> Pinpoint where the photo was taken on a world map.</li><li><b>Guess the Year:</b> Select the year the photo was taken on a timeline.</li></ul>Points are awarded based on the accuracy of both the location and the year. A perfect round yields <b>10,000 points</b>, for a maximum daily score of <b>50,000</b>.<br><br><div style="text-align: center; margin-top: 20px;"><a href="https://timeguessr.com/" target="_blank" style="background-color: #db5049; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold; text-decoration: none;">Play TimeGuessr</a></div></div></div></div><div class="flex-col-legend"><div class="info-card" style="padding: 1.5rem; display: flex; flex-direction: column; justify-content: center;"><h3 style="margin-top: 0; font-size: 1.1rem; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; text-align: center;">Score Legend</h3><div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;"><div style="flex: 1; min-width: 240px;"><div style="display: flex; align-items: center; border-bottom: 2px solid #db5049; padding-bottom: 5px; margin-bottom: 8px;"><span style="font-size: 1.1rem; margin-right: 8px;">🌍</span><span style="font-weight: 700; color: #db5049; font-size: 0.9rem; font-family: 'Poppins', sans-serif;">GEOGRAPHY</span></div><table class="compact-legend"><thead><tr><th>Pattern</th><th>Score</th><th>Dist</th></tr></thead><tbody><tr><td class="emoji-col">🟩🟩🟩</td><td style="text-align: center; font-weight: 600;">5,000</td><td style="text-align: right; color: #666;">< 50m</td></tr><tr><td class="emoji-col">🟩🟩🟨</td><td style="text-align: center;">4,750+</td><td style="text-align: right; color: #666;">< 37.5km</td></tr><tr><td class="emoji-col">🟩🟩⬛</td><td style="text-align: center;">4,500+</td><td style="text-align: right; color: #666;">< 100km</td></tr><tr><td class="emoji-col">🟩🟨⬛</td><td style="text-align: center;">4,250+</td><td style="text-align: right; color: #666;">< 250km</td></tr><tr><td class="emoji-col">🟩⬛⬛</td><td style="text-align: center;">3,500+</td><td style="text-align: right; color: #666;">< 1000km</td></tr><tr><td class="emoji-col">🟨⬛⬛</td><td style="text-align: center;">2,500+</td><td style="text-align: right; color: #666;">< 2000km</td></tr><tr><td class="emoji-col">⬛⬛⬛</td><td style="text-align: center;">< 2,500</td><td style="text-align: right; color: #666;">> 2000km</td></tr></tbody></table></div><div style="flex: 1; min-width: 240px;"><div style="display: flex; align-items: center; border-bottom: 2px solid #db5049; padding-bottom: 5px; margin-bottom: 8px;"><span style="font-size: 1.1rem; margin-right: 8px;">📅</span><span style="font-weight: 700; color: #db5049; font-size: 0.9rem; font-family: 'Poppins', sans-serif;">TIME</span></div><table class="compact-legend"><thead><tr><th>Pattern</th><th>Score</th><th>Diff</th></tr></thead><tbody><tr><td class="emoji-col">🟩🟩🟩</td><td style="text-align: center; font-weight: 600;">5,000</td><td style="text-align: right; color: #666;">0 yrs</td></tr><tr><td class="emoji-col">🟩🟩🟨</td><td style="text-align: center;">4,800+</td><td style="text-align: right; color: #666;">1-2 yrs</td></tr><tr><td class="emoji-col">🟩🟩⬛</td><td style="text-align: center;">4,300+</td><td style="text-align: right; color: #666;">3-4 yrs</td></tr><tr><td class="emoji-col">🟩🟨⬛</td><td style="text-align: center;">3,400+</td><td style="text-align: right; color: #666;">5-7 yrs</td></tr><tr><td class="emoji-col">🟩⬛⬛</td><td style="text-align: center;">2,000+</td><td style="text-align: right; color: #666;">8-15 yrs</td></tr><tr><td class="emoji-col">🟨⬛⬛</td><td style="text-align: center;">1,000</td><td style="text-align: right; color: #666;">16-20 yrs</td></tr><tr><td class="emoji-col">⬛⬛⬛</td><td style="text-align: center;">0</td><td style="text-align: right; color: #666;">21+ yrs</td></tr></tbody></table></div></div></div></div></div>""", 
    unsafe_allow_html=True
)

# --- Data Processing ---
try:
    data = pd.read_csv("./Data/Timeguessr_Stats.csv")
    data["Date"] = pd.to_datetime(data["Date"]).dt.date

    data["Michael Total Score"] = pd.to_numeric(data["Michael Total Score"], errors="coerce")
    data["Sarah Total Score"] = pd.to_numeric(data["Sarah Total Score"], errors="coerce")

    # Group by date
    daily = data.groupby("Date", as_index=False).agg(
        michael_played=("Michael Total Score", lambda x: x.notna().any()),
        sarah_played=("Sarah Total Score", lambda x: x.notna().any())
    )

    # --- CALCULATIONS ---
    date_1020 = pd.to_datetime("2025-10-20").date()
    date_1010 = pd.to_datetime("2025-10-10").date()

    daily_since_1020 = daily[daily["Date"] >= date_1020]
    daily_since_1010 = daily[daily["Date"] >= date_1010]

    def get_stats(df):
        total = len(df)
        both = ((df["michael_played"]) & (df["sarah_played"])).sum()
        m_only = ((df["michael_played"]) & (~df["sarah_played"])).sum()
        s_only = ((~df["michael_played"]) & (df["sarah_played"])).sum()
        return total, both, m_only, s_only

    all_total, all_both, all_m, all_s = get_stats(daily)
    s1020_total, s1020_both, s1020_m, s1020_s = get_stats(daily_since_1020)
    s1010_total, s1010_both, s1010_m, s1010_s = get_stats(daily_since_1010)

    # --- Statistics Section (Full Width) ---
    st.markdown("## Statistics")
    st.markdown(
        f"""
        <table class="stat-table">
            <thead>
                <tr>
                    <th style="width: 35%;">Metric</th>
                    <th style="width: 20%;">All Time</th>
                    <th style="width: 22.5%;">Post-Sarah<br><span style="font-size:10px; font-weight:400; opacity:0.8;">(Since 10/20/25)</span></th>
                    <th style="width: 22.5%;">Post-Michael<br><span style="font-size:10px; font-weight:400; opacity:0.8;">(Since 10/10/25)</span></th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="stat-row-label">Total Days Played</td>
                    <td class="stat-val">{all_total}</td>
                    <td class="stat-val">{s1020_total}</td>
                    <td class="stat-val">{s1010_total}</td>
                </tr>
                <tr>
                    <td class="stat-row-label">Days Both Played</td>
                    <td class="stat-val">{all_both}</td>
                    <td class="stat-val">{s1020_both}</td>
                    <td class="stat-val">{s1010_both}</td>
                </tr>
                <tr>
                    <td class="stat-row-label">Days Only Michael Played</td>
                    <td class="stat-val">{all_m}</td>
                    <td class="stat-val">{s1020_m}</td>
                    <td class="stat-val">{s1010_m}</td>
                </tr>
                <tr>
                    <td class="stat-row-label">Days Only Sarah Played</td>
                    <td class="stat-val">{all_s}</td>
                    <td class="stat-val">{s1020_s}</td>
                    <td class="stat-val">{s1010_s}</td>
                </tr>
            </tbody>
        </table>
        """,
        unsafe_allow_html=True
    )

    # --- Recent Activity Section ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## Recent Activity Log")
    
    display_data = data.iloc[::-1]
    
    # Generate Table Rows with Alternating Date Shading
    table_rows = ""
    last_date = None
    is_shaded = True # Start with True so the first toggle makes it False (White)
    
    for _, row in display_data.iterrows():
        # Track date changes for shading
        current_date = row['Date']
        if current_date != last_date:
            is_shaded = not is_shaded
            last_date = current_date
            
        bg_style = 'background-color: #f6f6f6;' if is_shaded else 'background-color: #ffffff;'
        
        # Format Date
        date_str = current_date.strftime('%b %d, %Y') if pd.notna(current_date) else ""
        
        # Format Location (Combine City and Country)
        city = str(row['City']).strip() if pd.notna(row['City']) else ""
        country = str(row['Country']).strip() if pd.notna(row['Country']) else ""
        
        if city and country:
            if city == country:
                loc_html = f'<span class="loc-city">{country}</span>'
            else:
                loc_html = f'<span class="loc-city">{city}</span><span class="loc-country">{country}</span>'
        elif country:
            loc_html = f'<span class="loc-city">{country}</span>'
        else:
            loc_html = "-"
            
        # Format Year
        year_str = str(int(row['Year'])) if pd.notna(row['Year']) else "-"
        
        # Format Scores
        def fmt_score(val):
            return f"{int(val):,}" if pd.notna(val) else "-"
            
        m_total = fmt_score(row['Michael Total Score'])
        s_total = fmt_score(row['Sarah Total Score'])
        m_round = fmt_score(row['Michael Round Score'])
        s_round = fmt_score(row['Sarah Round Score'])
        
        table_rows += f"""<tr style="{bg_style}"><td style="color: #666; font-size: 13px;">{date_str}</td><td>{loc_html}</td><td style="text-align: center; font-weight: 500;">{year_str}</td><td style="text-align: right;"><span class="score-val score-m">{m_round}</span></td><td style="text-align: right;"><span class="score-val score-s">{s_round}</span></td><td style="text-align: right;"><span class="score-val score-m" style="opacity: 0.6; font-size: 13px;">{m_total}</span></td><td style="text-align: right;"><span class="score-val score-s" style="opacity: 0.6; font-size: 13px;">{s_total}</span></td></tr>"""

    # Assemble HTML Table (Compact)
    # Adjusted widths: Narrowed Date (15->12%) and Year (10->8%), Widened Score cols (10->11%) and Location (35->36%)
    full_table_html = f"""<div class="activity-table-container"><table class="activity-table"><thead><tr><th style="width: 12%;">Date</th><th style="width: 36%;">Location</th><th style="width: 8%; text-align: center;">Year</th><th style="width: 11%; text-align: right;">Michael Round</th><th style="width: 11%; text-align: right;">Sarah Round</th><th style="width: 11%; text-align: right;">Michael Daily</th><th style="width: 11%; text-align: right;">Sarah Daily</th></tr></thead><tbody>{table_rows}</tbody></table></div>"""
    
    st.markdown(full_table_html, unsafe_allow_html=True)

except FileNotFoundError:
    st.error("Data file not found. Please ensure 'Data/Timeguessr_Stats.csv' exists.")