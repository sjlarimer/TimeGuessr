import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import datetime
import country_converter as coco

# --- Configuration ---
st.set_page_config(page_title="The Daily Guessr", layout="wide")

# --- Load External CSS ---
css_path = Path("styles.css")
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Internal Styling ---
NEWS_STYLES = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@500;600;700;800;900&display=swap');
        
        html { scroll-behavior: smooth; }
        .news-container { max-width: 800px; margin: 0 auto; padding: 40_px 20px; }
        
        .back-to-top { position: fixed; bottom: 30px; right: 30px; background-color: #333; color: white !important; width: 50px; height: 50px; border-radius: 25px; display: flex; align-items: center; justify-content: center; text-decoration: none !important; font-size: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 1000; transition: transform 0.2s, background-color 0.2s; }
        .back-to-top:hover { transform: scale(1.1); background-color: #000; color: white !important; }

        .page-header { text-align: center; margin-bottom: 40px; border-bottom: 4px double #ccc; padding-bottom: 30px; }
        .page-title { font-family: 'Poppins', sans-serif; font-weight: 900; font-size: 48px; color: #111; letter-spacing: -1px; margin: 0; text-transform: uppercase; }
        .page-subtitle { font-family: 'Inter', sans-serif; color: #666; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; margin-top: 12px; }
        
        /* FORECAST SECTION */
        .forecast-container { max-width: 1000px; margin: 0 auto 60px auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; }
        .forecast-card { background-color: #fff; border-radius: 12px; padding: 0; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #f0f0f0; overflow: hidden; display: flex; flex-direction: column; }
        .fc-header { padding: 16px 20px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #eee; }
        .fc-icon { font-size: 20px; }
        .fc-title { font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 16px; text-transform: uppercase; letter-spacing: 0.5px; color: #333; }
        
        .fc-momentum-grid { display: grid; grid-template-columns: 1fr 1fr; border-bottom: 1px solid #eee; }
        .fc-mom-box { padding: 15px; text-align: center; border-right: 1px solid #eee; }
        .fc-mom-box:last-child { border-right: none; }
        .fc-mom-label { font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
        .fc-mom-leader { font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 14px; margin-bottom: 4px; }
        .fc-mom-detail { font-family: 'Inter', sans-serif; font-size: 11px; color: #666; line-height: 1.3; }
        
        .fc-streaks { padding: 16px 20px; background-color: #fafafa; flex-grow: 1; }
        .fc-streaks-title { font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 700; color: #555; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 0.5px; }
        .fc-streak-item { display: flex; align-items: center; justify-content: space-between; font-family: 'Inter', sans-serif; font-size: 12px; margin-bottom: 6px; padding-bottom: 6px; border-bottom: 1px dashed #e0e0e0; }
        .fc-streak-item:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
        .fc-streak-name { font-weight: 600; color: #333; }
        .fc-streak-val { font-weight: 700; color: #000; }
        .fc-streak-meta { font-size: 10px; color: #888; }
        
        .target-hl { background-color: #fff9c4; padding: 0 3px; border-radius: 2px; font-weight: 600; color: #333; }
        .border-total { border-top: 5px solid #f1c40f; }
        .border-time { border-top: 5px solid #8e44ad; }
        .border-geo { border-top: 5px solid #27ae60; }
        
        /* DAILY FEED */
        .daily-card { background: #fff; border: 1px solid #ddd; border-top: 4px solid #333; border-radius: 8px; margin-bottom: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); scroll-margin-top: 50px; overflow: hidden; }
        .daily-header { background-color: #fcfcfc; padding: 16px 24px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .daily-date { font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 18px; color: #111; }
        .daily-badge { font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 700; background: #eee; color: #555; padding: 4px 10px; border: 1px solid #ccc; text-transform: uppercase; letter-spacing: 1px; border-radius: 4px; }
        
        .event-row { padding: 20px 24px; border-bottom: 1px solid #f0f0f0; display: flex; align-items: flex-start; gap: 24px; transition: background-color 0.2s; }
        .event-row:last-child { border-bottom: none; }
        
        .row-winner-Michael { background-color: rgba(34, 30, 143, 0.03); border-left: 4px solid #221e8f; }
        .row-winner-Sarah { background-color: rgba(138, 0, 92, 0.03); border-left: 4px solid #8a005c; }
        .row-winner-Tie { background-color: #fafafa; border-left: 4px solid #999; }
        .row-streak { background-color: #fffbf0; border-left: 4px solid #f1c40f; }
        .row-broken { background-color: #fff5f5; border-left: 4px solid #c0392b; }
        .row-discovery { background-color: #f0fbfd; border-left: 4px solid #00acc1; }
        .row-capture { background-color: #fffaf0; border-left: 5px solid #f39c12; }
        .row-record-max { background-color: #f6fff8; border-left: 5px solid #27ae60; }
        .row-record-min { background-color: #f0f8ff; border-left: 5px solid #1565C0; }
        .row-record-near { background-color: #fefefe; border-left: 5px solid #bdc3c7; }
        .row-score-max { background-color: #fcf9ff; border-left: 5px solid #8e44ad; }
        .row-score-min { background-color: #f7f9f9; border-left: 5px solid #95a5a6; }
        .row-score-beat-opp { background-color: #fff0f6; border-left: 5px solid #e91e63; }
        .row-score-streak-hot { background-color: #fff5eb; border-left: 5px solid #ff5722; }
        .row-score-streak-cold { background-color: #f4faff; border-left: 5px solid #3498db; }
        .row-milestone { background-color: #f3e5f5; border-left: 5px solid #9c27b0; }

        .category-box { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; width: 60px; min-width: 60px; text-align: center; margin-top: 4px; }
        .cat-icon { font-size: 24px; margin-bottom: 6px; }
        .cat-name { font-family: 'Inter', sans-serif; font-size: 9px; font-weight: 800; text-transform: uppercase; color: #999; letter-spacing: 1px; }
        .content-box { flex-grow: 1; }
        
        .event-title { font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 700; color: #d63031; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        .event-title-streak { color: #b7950b; }
        .event-title-broken { color: #c0392b; }
        .event-title-discovery { color: #00838f; }
        .event-title-capture { color: #d35400; }
        .event-title-record-max { color: #27ae60; }
        .event-title-record-min { color: #1565C0; }
        .event-title-record-near { color: #7f8c8d; }
        .event-title-score-max { color: #8e44ad; }
        .event-title-score-min { color: #7f8c8d; }
        .event-title-score-beat { color: #e91e63; }
        .event-title-hot { color: #ff5722; }
        .event-title-cold { color: #3498db; }
        .event-title-milestone { color: #9c27b0; }

        .change-visual { font-family: 'Poppins', sans-serif; font-size: 20px; line-height: 1.3; color: #333; display: block; }
        .player-name { font-weight: 700; }
        .p-michael { color: #221e8f; }
        .p-sarah { color: #8a005c; }
        .p-tie { color: #666; }
        .arrow { color: #ccc; margin: 0 8px; }
        
        .record-detail { color: #555; font-size: 14px; font-weight: 500; display: block; margin-top: 4px; }
        .streak-highlight { color: #444; font-weight: 500; font-size: 16px; margin-left: 8px; }
        .broken-detail { color: #666; font-weight: 400; font-size: 14px; margin-left: 8px; font-style: italic; }
        .discovery-highlight { color: #006064; font-weight: 700; font-size: 18px; }
        .discovery-subtext { font-size: 14px; color: #555; font-weight: 400; margin-left: 6px; }
        .milestone-highlight { color: #6a1b9a; font-weight: 700; font-size: 18px; }
        .all-time-badge { background-color: #2c3e50; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 800; text-transform: uppercase; margin-left: 8px; vertical-align: middle; }
        
        .discovery-stats-box { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
        .stat-chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 6px; background: white; border: 1px solid #e0e0e0; font-family: 'Inter', sans-serif; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .stat-chip.winner-michael { border-left: 3px solid #221e8f; }
        .stat-chip.winner-sarah { border-left: 3px solid #8a005c; }
        .stat-chip.winner-tie { border-left: 3px solid #999; }
        .stat-chip.cat-total { background-color: #fffdf0; }
        .stat-chip.cat-geography { background-color: #f0fff4; }
        .stat-chip.cat-time { background-color: #f5f3ff; }
        .stat-icon { font-size: 14px; }
        .stat-content { display: flex; flex-direction: column; justify-content: center; }
        .stat-type { font-size: 8px; font-weight: 800; color: #888; text-transform: uppercase; line-height: 1; margin-bottom: 2px; }
        .stat-winner { font-size: 11px; font-weight: 800; text-transform: uppercase; line-height: 1; }
        
        @media (max-width: 800px) { .forecast-container { grid-template-columns: 1fr; } }
    </style>
"""
st.markdown(NEWS_STYLES, unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data
def load_data(filepath: str = "./Data/Timeguessr_Stats.csv") -> pd.DataFrame:
    try:
        data = pd.read_csv(filepath)
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
        data = data.sort_values("Date").reset_index(drop=True)
        for p in ["Michael", "Sarah"]:
            t_col = f"{p} Total Score"
            if t_col in data.columns and data[t_col].dtype == object:
                 data[t_col] = data[t_col].astype(str).str.replace(',', '')
            if t_col in data.columns: 
                data[t_col] = pd.to_numeric(data[t_col], errors='coerce')
            for cat in ["Geography", "Time"]:
                min_c, max_c = f"{p} {cat} Score (Min)", f"{p} {cat} Score (Max)"
                for col in [min_c, max_c]:
                     if col in data.columns and data[col].dtype == object:
                         data[col] = data[col].astype(str).str.replace(',', '')
                if min_c in data.columns and max_c in data.columns:
                    data[min_c] = pd.to_numeric(data[min_c], errors='coerce')
                    data[max_c] = pd.to_numeric(data[max_c], errors='coerce')
                    data[f"{p} {cat} Score"] = (data[min_c] + data[max_c]) / 2
            
            if f"{p} Total Score" not in data.columns or data[f"{p} Total Score"].isna().all():
                data[f"{p} Total Score"] = data[f"{p} Geography Score"] + data[f"{p} Time Score"]

        m_dates = data[data['Michael Total Score'].notna()]['Date'].dt.date.unique()
        s_dates = data[data['Sarah Total Score'].notna()]['Date'].dt.date.unique()
        shared = set(m_dates).intersection(set(s_dates))
        data = data[data['Date'].dt.date.isin(shared)].copy()
        
        if "Year" in data.columns:
            data["Year"] = pd.to_numeric(data["Year"], errors='coerce')

        return data
    except Exception as e:
        st.error(f"Error loading data: {e}"); return pd.DataFrame()

def prepare_total_margins_data(df):
    d = df.groupby("Date")[["Michael Total Score", "Sarah Total Score"]].first().reset_index()
    d = d.sort_values("Date").reset_index(drop=True)
    d["Score Diff"] = d["Michael Total Score"] - d["Sarah Total Score"]
    return d

def prepare_time_margins_data(df):
    d = df.groupby("Date")[["Michael Time Score", "Sarah Time Score"]].sum().reset_index()
    d = d.sort_values("Date").reset_index(drop=True)
    d["Score Diff"] = d["Michael Time Score"] - d["Sarah Time Score"]
    return d

def prepare_geography_margins_data(df):
    d = df.groupby("Date")[["Michael Geography Score", "Sarah Geography Score"]].sum().reset_index()
    d = d.sort_values("Date").reset_index(drop=True)
    d["Score Diff"] = d["Michael Geography Score"] - d["Sarah Geography Score"]
    return d

# --- Logic ---
def get_leader_state(d): return "Michael" if d > 0 else ("Sarah" if d < 0 else "Tie")

def generate_news_events(df, cat, window=5):
    """
    Tracks Momentum Flips with added lead sizes.
    """
    if len(df) < window: return []
    t = df.copy()
    t["Rolling"] = t["Score Diff"].rolling(window=window).mean()
    
    evs, prev_state, prev_val = [], None, None
    for _, r in t.iterrows():
        if pd.isna(r["Rolling"]): continue
        curr_state = get_leader_state(r["Rolling"])
        curr_val = r["Rolling"]
        
        if prev_state is not None and curr_state != prev_state:
            evs.append({
                "date": r["Date"], 
                "category": cat, 
                "event_type": "flip", 
                "window": window, 
                "prev_state": prev_state, 
                "current_state": curr_state, 
                "prev_val": prev_val,
                "curr_val": curr_val
            })
        prev_state = curr_state
        prev_val = curr_val
    return evs

def generate_streak_events(df, cat, min_streak=3):
    if df.empty: return []
    events = []
    personal_bests = {"Michael": 0, "Sarah": 0}
    current_winner = None
    current_streak = 0
    
    for _, row in df.iterrows():
        diff, date = row["Score Diff"], row["Date"]
        winner = "Michael" if diff > 0 else ("Sarah" if diff < 0 else "Tie")
            
        if winner == current_winner and winner != "Tie":
            current_streak += 1
            pb = personal_bests[winner]
            if current_streak > pb and pb > 0:
                personal_bests[winner] = current_streak
                events.append({"date": date, "category": cat, "event_type": "streak", "subtype": "new_record", "player": winner, "count": current_streak})
            elif current_streak == pb and current_streak >= min_streak:
                events.append({"date": date, "category": cat, "event_type": "streak", "subtype": "matched_record", "player": winner, "count": current_streak})
            elif current_streak >= min_streak:
                events.append({"date": date, "category": cat, "event_type": "streak", "subtype": "active", "player": winner, "count": current_streak})
        else:
            if current_winner and current_winner != "Tie":
                pb = personal_bests[current_winner]
                if current_streak >= min_streak or (pb > 0 and current_streak >= (pb - 1)):
                    sub = "denied_break" if current_streak == pb else ("denied_match" if current_streak == pb - 1 else "significant_break")
                    events.append({"date": date, "category": cat, "event_type": "streak_broken", "subtype": sub, "player": current_winner, "breaker": winner, "count": current_streak, "record": pb})
            if winner != "Tie":
                current_winner, current_streak = winner, 1
                if personal_bests[winner] == 0: personal_bests[winner] = 1
            else:
                current_winner, current_streak = "Tie", 0
    return events

def generate_margin_record_events(df, category_name):
    if df.empty: return []
    events = []
    records = {"Michael": {"max": 0, "min": float('inf')}, "Sarah": {"max": 0, "min": float('inf')}}
    for idx, row in df.iterrows():
        diff, date = row["Score Diff"], row["Date"]
        if diff == 0: continue
        winner = "Michael" if diff > 0 else "Sarah"
        margin = abs(diff)
        opponent = "Sarah" if winner == "Michael" else "Michael"
        p_max, p_min = records[winner]["max"], records[winner]["min"]
        
        if p_max == 0: records[winner]["max"] = margin
        else:
            if margin > p_max:
                is_all_time = margin > records[opponent]["max"]
                events.append({"date": date, "category": category_name, "event_type": "margin_record", "subtype": "max_win", "player": winner, "margin": margin, "is_all_time": is_all_time, "prev_record": p_max})
                records[winner]["max"] = margin
            elif margin >= (0.90 * p_max):
                events.append({"date": date, "category": category_name, "event_type": "margin_near_record", "subtype": "near_max", "player": winner, "margin": margin, "prev_record": p_max})
        
        if p_min == float('inf'): records[winner]["min"] = margin
        else:
            if margin < p_min:
                is_all_time = margin < records[opponent]["min"]
                events.append({"date": date, "category": category_name, "event_type": "margin_record", "subtype": "min_win", "player": winner, "margin": margin, "is_all_time": is_all_time, "prev_record": p_min})
                records[winner]["min"] = margin
            elif margin <= (1.10 * p_min):
                events.append({"date": date, "category": category_name, "event_type": "margin_near_record", "subtype": "near_min", "player": winner, "margin": margin, "prev_record": p_min})
    return events

def generate_score_record_events(df, category_name):
    if df.empty: return []
    events = []
    
    # Store history for Top 10 logic
    score_history = {"Michael": [], "Sarah": []}
    rival_pb = {"Michael": 0, "Sarah": 0}

    for idx, row in df.iterrows():
        date = row["Date"]
        for player in ["Michael", "Sarah"]:
            score = row[f"{player} {category_name}"]
            if pd.isna(score): continue
            
            opponent = "Sarah" if player == "Michael" else "Michael"
            
            # --- Top 10 Logic ---
            # Compare current score to player's history up to this date
            # History is empty on the first day
            current_leaderboard = sorted(score_history[player], reverse=True)
            
            # Calculate Rank
            rank = 1
            for prev_score in current_leaderboard:
                if score < prev_score:
                    rank += 1
                else:
                    break
            
            if rank <= 10:
                events.append({
                    "date": date, 
                    "category": category_name, 
                    "event_type": "score_top_10", 
                    "player": player, 
                    "score": score, 
                    "rank": rank,
                    "is_all_time": rank == 1 and len(score_history[player]) > 0
                })

            # --- Beat Opponent's PB Logic ---
            opp_record = rival_pb[opponent]
            if opp_record > 0 and score > opp_record:
                events.append({
                    "date": date, 
                    "category": category_name, 
                    "event_type": "score_vs_opp", 
                    "subtype": "surpass_opp_max", 
                    "player": player, 
                    "score": score, 
                    "opponent": opponent, 
                    "opp_record": opp_record
                })

            # Update histories for next day processing
            score_history[player].append(score)
            if score > rival_pb[player]:
                rival_pb[player] = score
                
    return events

def generate_score_threshold_streaks(df):
    if df.empty: return []
    events = []
    configs = [
        {"cat": "Total Score", "fmt": "{p} Total Score", "th": [{"id": "tgt45", "lbl": ">45k", "chk": lambda s: s>45000, "min": 2, "typ": "hot"}, {"id": "tgt40", "lbl": ">40k", "chk": lambda s: s>40000, "min": 5, "typ": "hot"}, {"id": "tlt40", "lbl": "<40k", "chk": lambda s: s<40000, "min": 5, "typ": "cold"}, {"id": "tlt35", "lbl": "<35k", "chk": lambda s: s<35000, "min": 2, "typ": "cold"}]},
        {"cat": "Time Score", "fmt": "{p} Time Score", "th": [{"id": "tmgt20", "lbl": ">20k", "chk": lambda s: s>20000, "min": 2, "typ": "hot"}, {"id": "time_lt_20k", "lbl": "<20k", "chk": lambda s: s<20000, "min": 5, "typ": "cold"}]},
        {"cat": "Geography Score", "fmt": "{p} Geography Score", "th": [{"id": "ggt225", "lbl": ">22.5k", "chk": lambda s: s>22500, "min": 5, "typ": "hot"}, {"id": "geo_lt_225k", "lbl": "<22.5k", "chk": lambda s: s<22500, "min": 5, "typ": "cold"}]}
    ]
    stt = {}
    for c in configs: stt[c['cat']] = {p: {t['id']: {'cur': 0, 'max': 0} for t in c['th']} for p in ["Michael", "Sarah"]}
    for idx, row in df.iterrows():
        date = row["Date"]
        for c in configs:
            cat = c['cat']
            for p in ["Michael", "Sarah"]:
                col = c['fmt'].format(p=p)
                if col not in df.columns: continue
                s = row[col]
                for t in c['th']:
                    tid, trk = t['id'], stt[cat][p][t['id']]
                    if t['chk'](s):
                        trk['cur'] += 1
                        cu, mx = trk['cur'], trk['max']
                        if cu > mx:
                            trk['max'] = cu
                            if cu >= t['min']: events.append({"date": date, "category": cat, "event_type": "score_streak", "subtype": "new_record", "player": p, "count": cu, "threshold_label": t['lbl'], "streak_type": t['typ']})
                        elif cu == mx and cu >= t['min']:
                             events.append({"date": date, "category": cat, "event_type": "score_streak", "subtype": "matched_record", "player": p, "count": cu, "threshold_label": t['lbl'], "streak_type": t['typ']})
                        elif cu >= t['min']:
                             events.append({"date": date, "category": cat, "event_type": "score_streak", "subtype": "active", "player": p, "count": cu, "threshold_label": t['lbl'], "streak_type": t['typ']})
                    else:
                        if trk['cur'] > 0:
                            cu, mx = trk['cur'], trk['max']
                            if cu >= t['min'] or cu == mx or cu == mx - 1:
                                sub = "denied_break" if cu == mx else ("denied_match" if cu == mx - 1 else "significant_break")
                                if cu >= t['min'] or sub != "significant_break":
                                    events.append({"date": date, "category": cat, "event_type": "score_streak_broken", "subtype": sub, "player": p, "count": cu, "record": mx, "threshold_label": t['lbl'], "streak_type": t['typ']})
                        trk['cur'] = 0
    return events

def generate_milestone_events(df):
    if df.empty: return []
    evs = []
    dec, yr, loc = {}, {}, {}
    seen_dates = set()
    total_days = 0
    
    uc = df["Country"].dropna().unique()
    iso = dict(zip(uc, coco.CountryConverter().convert(names=uc, to='ISO3', not_found=None)))
    ui = [i for i in set(iso.values()) if i]
    reg = dict(zip(ui, coco.CountryConverter().convert(names=ui, to="UNregion")))
    con = dict(zip(ui, coco.CountryConverter().convert(names=ui, to="continent")))
    
    TH = {"total": 25, "decade": 25, "year": 10, "continent": 25, "region": 10, "country": 10, "subdivision": 10}
    
    for _, r in df.sort_values("Date").iterrows():
        dt = r["Date"]
        if dt not in seen_dates:
            seen_dates.add(dt)
            total_days += 1
            if total_days > 0 and total_days % TH["total"] == 0:
                evs.append({"date": dt, "category": "Milestone", "event_type": "milestone", "subtype": "total", "name": "Total Games", "count": total_days})
        
        y = r.get("Year")
        if pd.notna(y):
            ystr = str(int(y))
            yr[ystr] = yr.get(ystr, 0) + 1
            if yr[ystr] % TH["year"] == 0: evs.append({"date": dt, "category": "Milestone", "event_type": "milestone", "subtype": "year", "name": ystr, "count": yr[ystr]})
            try: dstr = str(int(y // 10) * 10) + "s"
            except: dstr = None
            if dstr:
                dec[dstr] = dec.get(dstr, 0) + 1
                if dec[dstr] % TH["decade"] == 0: evs.append({"date": dt, "category": "Milestone", "event_type": "milestone", "subtype": "decade", "name": dstr, "count": dec[dstr]})
        
        c, s = r.get("Country"), r.get("Subdivision")
        ccl = str(c).strip() if pd.notna(c) else "Unknown"
        isoc = iso.get(ccl)
        rg, cn = reg.get(isoc, "Unknown"), con.get(isoc, "Unknown")
        
        for kt, kn, th in [("continent", cn, TH["continent"]), ("region", rg, TH["region"]), ("country", ccl, TH["country"])]:
            if kn and kn != "Unknown":
                k = (kt, kn)
                loc[k] = loc.get(k, 0) + 1
                if loc[k] % th == 0: evs.append({"date": dt, "category": "Milestone", "event_type": "milestone", "subtype": kt, "name": kn, "count": loc[k]})
        
        if pd.notna(s) and str(s).strip():
             k = ("subdivision", str(s).strip())
             loc[k] = loc.get(k, 0) + 1
             if loc[k] % TH["subdivision"] == 0: evs.append({"date": dt, "category": "Milestone", "event_type": "milestone", "subtype": "subdivision", "name": str(s).strip(), "count": loc[k]})
    return evs

cc_obj = coco.CountryConverter()
@st.cache_data
def get_flag_html(name):
    if not name or pd.isna(name) or str(name).strip().lower() == "unknown": return "🏳️"
    try:
        iso2 = cc_obj.convert(names=str(name).strip(), to='ISO2', not_found=None)
        if iso2 and isinstance(iso2, str) and len(iso2) == 2:
            cp = "-".join([f"1f1{format(ord(c) - ord('A') + 0xE6, 'x')}" for c in iso2.upper()])
            return f'<img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/svg/{cp}.svg" width="24" style="vertical-align:middle; margin-right:4px;"/>'
    except: pass
    return "🏳️"

def generate_location_events(df):
    if df.empty: return []
    events, seen_cont, seen_r = [], set(), set()
    perf_data = df.copy()
    for p in ["Michael", "Sarah"]: perf_data[f"{p} Total Score"] = perf_data[f"{p} Geography Score"] + perf_data[f"{p} Time Score"]
    
    def get_lead(sub):
        r = {}
        for m in ["Total", "Geography", "Time"]:
            ms, ss = sub[f"Michael {m} Score"].sum(), sub[f"Sarah {m} Score"].sum()
            r[m] = "Michael" if ms > ss else ("Sarah" if ss > ms else "Tie")
        return r

    hist_loc, hist_reg, hist_cont = {}, {}, {}
    uc = df["Country"].dropna().unique()
    iso = dict(zip(uc, cc_obj.convert(names=uc, to='ISO3', not_found=None)))
    ui = [i for i in set(iso.values()) if i]
    reg = dict(zip(ui, cc_obj.convert(names=ui, to="UNregion")))
    con = dict(zip(ui, cc_obj.convert(names=ui, to="continent")))

    for _, r in perf_data.sort_values("Date").iterrows():
        dt, c, s = r["Date"], r.get("Country"), r.get("Subdivision")
        ccl = str(c).strip() if pd.notna(c) else "Unknown"
        scl = str(s).strip() if pd.notna(s) else None
        isoc = iso.get(ccl)
        rg, cn = reg.get(isoc, "Unknown"), con.get(isoc, "Unknown")
        
        if cn != "Unknown" and cn not in seen_cont: seen_cont.add(cn); events.append({"date": dt, "category": "Discovery", "event_type": "discovery", "subtype": "new_continent", "name": cn})
        if rg != "Unknown" and rg not in seen_r: seen_r.add(rg); events.append({"date": dt, "category": "Discovery", "event_type": "discovery", "subtype": "new_un_region", "name": rg})
        
        keys = []
        if ccl != "Unknown": keys.append(("new_country", ccl, None))
        if scl: keys.append(("new_subdivision", ccl, scl))
        
        for kt, kc, ks in keys:
            k = (kc, ks)
            if k not in hist_loc:
                hist_loc[k] = {"Total": "Tie", "Geography": "Tie", "Time": "Tie", "Michael": {"Total": 0, "Geography": 0, "Time": 0}, "Sarah": {"Total": 0, "Geography": 0, "Time": 0}}
                for p in ["Michael", "Sarah"]: 
                    for m in ["Total", "Geography", "Time"]: hist_loc[k][p][m] += r[f"{p} {m} Score"]
                sub = perf_data[perf_data["Country"] == kc] if not ks else perf_data[(perf_data["Country"] == kc) & (perf_data["Subdivision"] == ks)]
                perf = get_lead(sub[sub["Date"] <= dt])
                for m in ["Total", "Geography", "Time"]: hist_loc[k][m] = perf[m]
                events.append({"date": dt, "category": "Discovery", "event_type": "discovery", "subtype": kt, "name": ks if ks else kc, "country": kc if ks else "", "perf": perf})
            else:
                for p in ["Michael", "Sarah"]: 
                    for m in ["Total", "Geography", "Time"]: hist_loc[k][p][m] += r[f"{p} {m} Score"]
                for m in ["Total", "Geography", "Time"]:
                    mv, sv = hist_loc[k]["Michael"][m], hist_loc[k]["Sarah"][m]
                    new = "Michael" if mv > sv else ("Sarah" if sv > mv else "Tie")
                    old = hist_loc[k][m]
                    if new != old:
                        events.append({"date": dt, "category": "Discovery", "event_type": "location_flip", "subtype": f"{kt}_flip", "cat_type": m, "name": ks if ks else kc, "country": kc if ks else "", "prev_state": old, "current_state": new})
                        hist_loc[k][m] = new

        for zn, zh, zt in [(rg, hist_reg, "new_un_region_flip"), (cn, hist_cont, "new_continent_flip")]:
             if zn != "Unknown":
                if zn not in zh:
                    zh[zn] = {m: "Tie" for m in ["Total", "Geography", "Time"]}
                    zh[zn].update({f"{p}_{m}": 0 for p in ["Michael", "Sarah"] for m in ["Total", "Geography", "Time"]})
                for p in ["Michael", "Sarah"]:
                    for m in ["Total", "Geography", "Time"]: zh[zn][f"{p}_{m}"] += r[f"{p} {m} Score"]
                for m in ["Total", "Geography", "Time"]:
                    mv, sv = zh[zn][f"Michael_{m}"], zh[zn][f"Sarah_{m}"]
                    new = "Michael" if mv > sv else ("Sarah" if sv > mv else "Tie")
                    old = zh[zn][m]
                    if new != old:
                        events.append({"date": dt, "category": "Discovery", "event_type": "location_flip", "subtype": zt, "cat_type": m, "name": zn, "country": "", "prev_state": old, "current_state": new})
                        zh[zn][m] = new
    return events

def generate_year_events(df):
    if df.empty: return []
    events, seen = [], set()
    perf_data = df.copy()
    hist = {}
    for _, r in perf_data.sort_values("Date").iterrows():
        dt, y = r["Date"], r.get("Year")
        if pd.isna(y): continue
        ystr = str(int(y))
        cat = "Time"
        if ystr not in seen:
            seen.add(ystr)
            hist[ystr] = {"Time": "Tie", "Michael": {"Time": 0}, "Sarah": {"Time": 0}}
            for p in ["Michael", "Sarah"]: hist[ystr][p][cat] += r[f"{p} {cat} Score"]
            mv, sv = hist[ystr]["Michael"][cat], hist[ystr]["Sarah"][cat]
            ld = "Michael" if mv > sv else ("Sarah" if sv > mv else "Tie")
            hist[ystr][cat] = ld
            perf = {"Time": ld, "Total": "Tie", "Geography": "Tie"}
            events.append({"date": dt, "category": "Year", "event_type": "year_discovery", "subtype": "new_year", "name": ystr, "perf": perf})
        else:
            for p in ["Michael", "Sarah"]: hist[ystr][p][cat] += r[f"{p} {cat} Score"]
            mv, sv = hist[ystr]["Michael"][cat], hist[ystr]["Sarah"][cat]
            new = "Michael" if mv > sv else ("Sarah" if sv > mv else "Tie")
            old = hist[ystr][cat]
            if new != old:
                events.append({"date": dt, "category": "Year", "event_type": "year_flip", "subtype": "year_flip", "cat_type": cat, "name": ystr, "prev_state": old, "current_state": new})
                hist[ystr][cat] = new
    return events

def generate_decade_events(df):
    if df.empty: return []
    events, seen = [], set()
    perf_data = df.copy()
    hist = {}
    for _, r in perf_data.sort_values("Date").iterrows():
        dt, y = r["Date"], r.get("Year")
        if pd.isna(y): continue
        dstr = str(int(y // 10) * 10) + "s"
        cat = "Time"
        if dstr not in seen:
            seen.add(dstr)
            hist[dstr] = {"Time": "Tie", "Michael": {"Time": 0}, "Sarah": {"Time": 0}}
            for p in ["Michael", "Sarah"]: hist[dstr][p][cat] += r[f"{p} {cat} Score"]
            mv, sv = hist[dstr]["Michael"][cat], hist[dstr]["Sarah"][cat]
            ld = "Michael" if mv > sv else ("Sarah" if sv > mv else "Tie")
            hist[dstr][cat] = ld
            perf = {"Time": ld}
            events.append({"date": dt, "category": "Decade", "event_type": "decade_discovery", "subtype": "new_decade", "name": dstr, "perf": perf})
        else:
            for p in ["Michael", "Sarah"]: hist[dstr][p][cat] += r[f"{p} {cat} Score"]
            mv, sv = hist[dstr]["Michael"][cat], hist[dstr]["Sarah"][cat]
            new = "Michael" if mv > sv else ("Sarah" if sv > mv else "Tie")
            old = hist[dstr][cat]
            if new != old:
                events.append({"date": dt, "category": "Decade", "event_type": "decade_flip", "subtype": "decade_flip", "cat_type": cat, "name": dstr, "prev_state": old, "current_state": new})
                hist[dstr][cat] = new
    return events

def get_full_category_forecast(df, cat):
    if len(df) < 5: return None
    r5 = df["Score Diff"].rolling(window=5).mean().iloc[-1]
    r10 = df["Score Diff"].rolling(window=10).mean().iloc[-1] if len(df) >= 10 else None
    
    if pd.notna(r5):
        l5 = get_leader_state(r5)
        b5 = -df.tail(4)["Score Diff"].sum()
        if l5 == "Michael": m5 = f"Sarah flips with win of <span class='target-hl'>{abs(b5):,.0f}+</span>" if b5 < 0 else "Sarah flips with <span class='target-hl'>any win</span>"
        elif l5 == "Sarah": m5 = f"Michael flips with win of <span class='target-hl'>{b5:,.0f}+</span>" if b5 > 0 else "Michael flips with <span class='target-hl'>any win</span>"
        else: m5 = "Next winner takes the lead."
    else: l5, m5 = "N/A", "Not enough data"

    if pd.notna(r10):
        l10 = get_leader_state(r10)
        b10 = -df.tail(9)["Score Diff"].sum()
        if l10 == "Michael": m10 = f"Sarah flips with win of <span class='target-hl'>{abs(b10):,.0f}+</span>" if b10 < 0 else "Sarah flips with <span class='target-hl'>any win</span>"
        elif l10 == "Sarah": m10 = f"Michael flips with win of <span class='target-hl'>{b10:,.0f}+</span>" if b10 > 0 else "Michael flips with <span class='target-hl'>any win</span>"
        else: m10 = "Next winner takes the lead."
    else: l10, m10 = "N/A", "Not enough data"
    
    ms, sw, cs = {"Michael": 0, "Sarah": 0}, None, 0
    for _, r in df.iterrows():
        d = r["Score Diff"]
        w = "Michael" if d > 0 else ("Sarah" if d < 0 else "Tie")
        if w == "Tie": continue
        if w == sw: cs += 1
        else: sw, cs = w, 1
        if cs > ms[w]: ms[w] = cs
    
    sh = ""
    if sw:
        opp = "Sarah" if sw == "Michael" else "Michael"
        rec = ms[sw]
        if cs == rec: t_str = f"<span style='color:#27ae60; font-weight:700;'>Record Streak!</span>"
        else: t_str = f"Matches PB in <b>{rec - cs}</b>"
        sh += f"""<div class="fc-streak-item"><span class="fc-streak-name">Win Streak ({sw})</span> <span class="fc-streak-val">{cs}</span> <span class="fc-streak-meta">{t_str}</span></div>"""
    
    cth = {
        "Total Score": [{"id": ">45k", "label": ">45k", "check": lambda s: s > 45000}, {"id": ">40k", "label": ">40k", "check": lambda s: s > 40000}, {"id": "<40k", "label": "<40k", "check": lambda s: s < 40000}, {"id": "<35k", "label": "<35k", "check": lambda s: s < 35000}],
        "Time Score": [{"id": ">20k", "label": ">20k", "check": lambda s: s > 20000}, {"id": "<20k", "label": "<20k", "check": lambda s: s < 20000}],
        "Geography Score": [{"id": ">22.5k", "label": ">22.5k", "check": lambda s: s > 22500}, {"id": "<22.5k", "label": "<22.5k", "check": lambda s: s < 22500}]
    }
    
    if cat in cth:
        th = cth[cat]
        cmax = {p: {t['id']: 0 for t in th} for p in ["Michael", "Sarah"]}
        crun = {p: {t['id']: 0 for t in th} for p in ["Michael", "Sarah"]}
        for _, r in df.iterrows():
            for p in ["Michael", "Sarah"]:
                col_name = f"{p} {cat}"
                if col_name not in df.columns: continue
                sc = r[col_name]
                for t in th:
                    tid = t['id']
                    if t['check'](sc): crun[p][tid] += 1
                    else:
                        if crun[p][tid] > cmax[p][tid]: cmax[p][tid] = crun[p][tid]
                        crun[p][tid] = 0
        acts = []
        for p in ["Michael", "Sarah"]:
            for t in th:
                tid, cur, rec = t['id'], crun[p][tid], cmax[p][tid]
                if cur > 0:
                     c = "#e67e22" if ">" in tid else "#3498db"
                     rt = f"<span style='color:#27ae60; font-weight:700;'>New Record!</span>" if cur > rec else (f"<span style='color:#d35400; font-weight:700;'>Matches PB!</span>" if cur == rec else f"Matches PB in {rec - cur}")
                     acts.append(f"<div class='fc-streak-item'><span class='fc-streak-name' style='color:{c}'>{p} {t['label']}</span> <span class='fc-streak-val'>{cur}</span> <span class='fc-streak-meta'>{rt}</span></div>")
        if acts: sh += f"""<div style="margin-top:10px; padding-top:10px; border-top:1px dashed #ccc;"><div style="font-size:10px; font-weight:700; color:#999; margin-bottom:5px; text-transform:uppercase;">Active Score Runs</div>{''.join(acts)}</div>"""
    return {"category": cat, "l5": l5, "m5": m5, "l10": l10, "m10": m10, "streaks_html": sh}

def render_forecast_section(fs_list):
    html = '<div class="forecast-container">'
    icons = {"Total Score": "🏆", "Time Score": "⏱️", "Geography Score": "🌍"}
    borders = {"Total Score": "border-total", "Time Score": "border-time", "Geography Score": "border-geo"}
    for f in fs_list:
        if not f: continue
        cat, ic, bc = f['category'], icons.get(f['category'], "📊"), borders.get(f['category'], "")
        def lc(l): return "#221e8f" if l == "Michael" else ("#8a005c" if l == "Sarah" else "#999")
        html += f"""<div class="forecast-card {bc}"><div class="fc-header"><span class="fc-icon">{ic}</span><span class="fc-title">{cat}</span></div><div class="fc-momentum-grid"><div class="fc-mom-box"><div class="fc-mom-label">5-Game Avg</div><div class="fc-mom-leader" style="color: {lc(f['l5'])}">{f['l5']}</div><div class="fc-mom-detail">{f['m5']}</div></div><div class="fc-mom-box"><div class="fc-mom-label">10-Game Avg</div><div class="fc-mom-leader" style="color: {lc(f['l10'])}">{f['l10']}</div><div class="fc-mom-detail">{f['m10']}</div></div></div><div class="fc-streaks"><div class="fc-streaks-title">Active Streaks</div>{f['streaks_html'] if f['streaks_html'] else '<div style="font-size:11px; color:#999; font-style:italic;">No active streaks.</div>'}</div></div>"""
    return html + '</div>'

def render_daily_news(dt, evs):
    ds, ec, rh = dt.strftime("%A, %B %d, %Y"), len(evs), ""
    day_id = f"day-{dt.strftime('%Y-%m-%d')}"
    
    def get_ordinal(n):
        if 11 <= (n % 100) <= 13: suffix = 'th'
        else: suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"

    rmap = {('milestone', 'total'): 1, ('milestone', 'continent'): 2, ('milestone', 'region'): 2, ('milestone', 'country'): 2, ('milestone', 'subdivision'): 2, ('milestone', 'decade'): 3, ('milestone', 'year'): 3, ('score_top_10', ''): 4, ('margin_record', 'max_win'): 5, ('margin_record', 'min_win'): 5, ('discovery', 'new_continent'): 6, ('discovery', 'new_un_region'): 6, ('discovery', 'new_country'): 6, ('discovery', 'new_subdivision'): 6, ('streak', 'new_record'): 7, ('streak', 'matched_record'): 8, ('streak_broken', ''): 9, ('score_streak', 'new_record'): 10, ('score_streak', 'matched_record'): 11, ('score_streak', 'active'): 12, ('score_streak_broken', ''): 13, ('flip', 10): 14, ('flip', 5): 15, ('score_vs_opp', ''): 16, ('location_flip', ''): 17, ('year_discovery', ''): 18, ('decade_discovery', ''): 18, ('year_flip', ''): 19, ('decade_flip', ''): 19, ('margin_near_record', ''): 20}
    
    def gr(e):
        t, s, w = e.get('event_type'), e.get('subtype', ''), e.get('window')
        if t == 'flip': return 14 if w == 10 else 15
        if t in ['streak_broken', 'score_streak_broken', 'score_vs_opp', 'location_flip', 'year_discovery', 'decade_discovery', 'year_flip', 'decade_flip', 'margin_near_record', 'score_top_10']: return rmap.get((t, ''), 99)
        return rmap.get((t, s), 99)
    evs.sort(key=gr)

    for e in evs:
        cat, et, ic, cs = e['category'], e.get('event_type'), "📰", e['category']
        if cat == "Total Score": ic, cs = "🏆", "Total"
        elif cat == "Time Score": ic, cs = "⏱️", "Time"
        elif cat == "Geography Score": ic, cs = "🌍", "Geo"
        elif cat == "Discovery": ic, cs = "🗺️", "Map"
        elif cat == "Year": ic, cs = "📅", "Year"
        elif cat == "Decade": ic, cs = "🗓️", "Decade"
        elif cat == "Milestone": ic, cs = "🎉", "Milestone"
        
        def pc(n): return "p-michael" if n == "Michael" else ("p-sarah" if n == "Sarah" else "p-tie")
        rc, ct = "row-winner-Tie", ""

        if et == 'flip':
            p, c, w = e['prev_state'], e['current_state'], e['window']
            pv, cv = abs(e['prev_val']), abs(e['curr_val'])
            txt = "DROPS TO TIE" if c == "Tie" else ("BREAKS TIE" if p == "Tie" else "TAKES THE LEAD")
            lead_info = f"Lead was {int(pv):,} pts → now {int(cv):,} pts"
            ct = f"""<div class="event-title">{w}-GAME AVG: {cs} Score &middot; {txt}</div>
                     <div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="arrow">➜</span><span class="player-name {pc(c)}">{c.upper()}</span></div>
                     <div class="record-detail" style="margin-top:6px; font-size:13px;">
                        <div>{lead_info}</div>
                     </div>"""
            rc = f"row-winner-{c}"
        elif et == 'streak':
            p, cnt, sub = e['player'], e['count'], e['subtype']
            txt = "NEW RECORD STREAK" if sub == "new_record" else ("MATCHED RECORD STREAK" if sub == "matched_record" else "ACTIVE STREAK")
            ic, rc = "🔥", "row-streak"
            ct = f"""<div class="event-title event-title-streak">{cs} &middot; {txt}</div><div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="streak-highlight">&middot; {'First time reaching' if sub == 'new_record' else ('Matches record of' if sub == 'matched_record' else 'Reached')} <b>{cnt}</b> days</span></div>"""
        elif et == 'streak_broken':
            p, b, cnt, sub = e['player'], e['breaker'], e['count'], e['subtype']
            ic, rc = "🛑", "row-broken"
            breaker_text = f"by {b.upper()}" if b != "Tie" else "by a TIE"
            det = f"Ends {p}'s <b>{cnt}</b>-game run {breaker_text}."
            if sub == 'denied_break': det += " One game short of a new record!"
            ct = f"""<div class="event-title event-title-broken">{cs} &middot; STREAK SNAPPED</div><div class="change-visual"><span class="player-name {pc(b)}">{b.upper() if b != 'Tie' else 'TIE'}</span><span class="broken-detail">{det}</span></div>"""
        elif et == 'score_streak':
            p, cnt, sub, lbl, stype = e['player'], e['count'], e['subtype'], e['threshold_label'], e['streak_type']
            ic, rc = ("🔥", "row-score-streak-hot") if stype == "hot" else ("❄️", "row-score-streak-cold")
            title_cl = "event-title-hot" if stype == "hot" else "event-title-cold"
            if sub == "new_record": txt, det = f"NEW RECORD: {lbl.upper()} STREAK", f"First time reaching <b>{cnt}</b> days"
            elif sub == "matched_record": txt, det = f"MATCHED RECORD: {lbl.upper()} STREAK", f"Matches record of <b>{cnt}</b> days"
            else: txt, det = f"ACTIVE: {lbl.upper()} STREAK", f"Streak continues for <b>{cnt}</b> days"
            ct = f"""<div class="event-title {title_cl}">{txt}</div><div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="streak-highlight">&middot; {det}</span></div>"""
        elif et == 'score_streak_broken':
            p, cnt, sub, lbl = e['player'], e['count'], e['subtype'], e['threshold_label']
            ic, rc = "🛑", "row-broken"
            det = f"Ends run of <b>{cnt}</b> days" + (" (was about to break record)" if sub == "denied_break" else (" (was about to match record)" if sub == "denied_match" else ""))
            ct = f"""<div class="event-title event-title-broken">{lbl} STREAK ENDED</div><div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="broken-detail">{det}</span></div>"""
        elif et == 'margin_record':
            p, sub, m = e['player'], e['subtype'], e['margin']
            ic, rc = ("📈", "row-record-max") if sub == "max_win" else ("🤏", "row-record-min")
            tt, cl = ("RECORD WIN MARGIN", "event-title-record-max") if sub == "max_win" else ("RECORD TIGHTEST WIN", "event-title-record-min")
            at_badge = '<span class="all-time-badge">ALL-TIME RECORD</span>' if e.get('is_all_time') else ""
            ct = f"""<div class="event-title {cl}">{cs} &middot; {tt} {at_badge}</div><div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="record-detail">Margin: {int(m):,} pts (Beats {int(e['prev_record']):,})</span></div>"""
        elif et == 'margin_near_record':
            p, sub, m = e['player'], e['subtype'], e['margin']
            ic, rc = "🎯", "row-record-near"
            tt, cl, det = "NEAR RECORD MARGIN", "event-title-record-near", ("Tightest" if sub == "near_min" else "Largest")
            ct = f"""<div class="event-title {cl}">{cs} &middot; {tt}</div><div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="record-detail">Margin: {int(m):,} pts (Near {det} PB: {int(e['prev_record']):,})</span></div>"""
        elif et == 'score_top_10':
            p, s, r = e['player'], e['score'], e['rank']
            is_pb = r == 1
            ic = "👑" if is_pb else "🏅"
            rc = "row-score-max" if is_pb else "row-score-min"
            ord_rank = get_ordinal(r)
            tt = "NEW ALL-TIME RECORD" if is_pb else f"TOP 10 PERFORMANCE ({ord_rank})"
            cl = "event-title-score-max" if is_pb else "event-title-score-min"
            ct = f"""<div class="event-title {cl}">{cs} &middot; {tt}</div>
                     <div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span>
                     <span class="record-detail">Score: {int(s):,} pts &middot; Ranked {ord_rank} highest all-time as of this date</span></div>"""
        elif et == 'score_vs_opp':
            p, sub, s = e['player'], e['subtype'], e['score']
            opp, opp_rec = e['opponent'], e['opp_record']
            ic, rc = "⚔️", "row-score-beat-opp"
            tt, cl = ("BEAT OPPONENT'S PB", "event-title-score-beat") if sub == "surpass_opp_max" else ("LOWER THAN OPPONENT'S WORST", "event-title-score-beat")
            det_txt = f"Score: {int(s):,} pts (Surpassed {opp}'s best of {int(opp_rec):,})" if sub == "surpass_opp_max" else f"Score: {int(s):,} pts (Lower than {opp}'s worst of {int(opp_rec):,})"
            ct = f"""<div class="event-title {cl}">{cs} &middot; {tt}</div><div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="record-detail">{det_txt}</span></div>"""
        elif et == 'discovery':
            n, sub = e['name'], e['subtype']
            if sub in ["new_country", "new_subdivision"]:
                txt = "NEW COUNTRY" if sub == "new_country" else "NEW SUBDIVISION"
                ic = get_flag_html(n) if sub == "new_country" else f"{get_flag_html(e.get('country', ''))} 📍"
                stats, lbls = e.get('perf', {}), {"Total": ("🏆", "Total"), "Geography": ("🌍", "Geo"), "Time": ("⏱️", "Time")}
                sh = "".join([f'<div class="stat-chip cat-{m.lower()} winner-{stats[m].lower()}"><span class="stat-icon">{lbls[m][0]}</span> <div class="stat-content"><span class="stat-type">{lbls[m][1]}</span><span class="stat-winner {pc(stats[m])}">{stats[m].upper()}</span></div></div>' for m in ["Total", "Geography", "Time"]])
                det_txt = f'<span class="discovery-subtext">in {e.get("country", "")}</span>' if sub == "new_subdivision" else ""
                ct = f"""<div class="event-title event-title-discovery">{txt}</div><div class="change-visual"><span class="discovery-highlight">{n}</span>{det_txt}</div><div class="discovery-stats-box">{sh}</div>"""
                rc = "row-discovery"
            elif sub == "new_un_region":
                ic, rc = "🌐", "row-discovery"
                ct = f"""<div class="event-title event-title-discovery">NEW UN REGION</div><div class="change-visual"><span class="discovery-highlight">{n}</span></div>"""
            elif sub == "new_continent":
                ic, rc = "🌏", "row-discovery"
                ct = f"""<div class="event-title event-title-discovery">NEW CONTINENT</div><div class="change-visual"><span class="discovery-highlight">{n}</span></div>"""
        elif et == 'year_discovery':
            n, stt = e['name'], e['perf']
            txt, ic, rc = "NEW YEAR", "📅", "row-discovery"
            lbls = {"Time": ("⏱️", "Time")}
            sh = "".join([f'<div class="stat-chip cat-{m.lower()} winner-{stt[m].lower()}"><span class="stat-icon">{lbls[m][0]}</span> <div class="stat-content"><span class="stat-type">{lbls[m][1]}</span><span class="stat-winner {pc(stt[m])}">{stt[m].upper()}</span></div></div>' for m in ["Time"]])
            ct = f"""<div class="event-title event-title-discovery">{txt}</div><div class="change-visual"><span class="discovery-highlight">{n}</span></div><div class="discovery-stats-box">{sh}</div>"""
        elif et == 'decade_discovery':
            n, stt = e['name'], e['perf']
            txt, ic, rc = "NEW DECADE", "🗓️", "row-discovery"
            lbls = {"Time": ("⏱️", "Time")}
            sh = "".join([f'<div class="stat-chip cat-{m.lower()} winner-{stt[m].lower()}"><span class="stat-icon">{lbls[m][0]}</span> <div class="stat-content"><span class="stat-type">{lbls[m][1]}</span><span class="stat-winner {pc(stt[m])}">{stt[m].upper()}</span></div></div>' for m in ["Time"]])
            ct = f"""<div class="event-title event-title-discovery">{txt}</div><div class="change-visual"><span class="discovery-highlight">{n}</span></div><div class="discovery-stats-box">{sh}</div>"""
        elif et == 'year_flip':
            ctype, p, c, n = e['cat_type'], e['prev_state'], e['current_state'], e['name']
            ic, rc = "📅", "row-capture"
            ct = f"""<div class="event-title event-title-capture">⏱️ CONTROL FLIP: YEAR {ctype.upper()}</div><div class="change-visual"><span class="discovery-highlight">{n}</span><span class="arrow" style="margin-left:10px;">➔</span> <span class="player-name {pc(p)}">{p.upper()}</span> <span class="arrow">➜</span> <span class="player-name {pc(c)}">{c.upper()}</span></div>"""
        elif et == 'decade_flip':
            ctype, p, c, n = e['cat_type'], e['prev_state'], e['current_state'], e['name']
            ic, rc = "🗓️", "row-capture"
            ct = f"""<div class="event-title event-title-capture">⏱️ CONTROL FLIP: DECADE {ctype.upper()}</div><div class="change-visual"><span class="discovery-highlight">{n}</span><span class="arrow" style="margin-left:10px;">➔</span> <span class="player-name {pc(p)}">{p.upper()}</span> <span class="arrow">➜</span> <span class="player-name {pc(c)}">{c.upper()}</span></div>"""
        elif et == 'location_flip':
            ctype, p, c, n, sub = e['cat_type'], e['prev_state'], e['current_state'], e['name'], e['subtype']
            lt = "COUNTRY" if "country" in sub else ("SUBDIVISION" if "subdivision" in sub else ("REGION" if "region" in sub else ("CONTINENT" if "continent" in sub else "LOCATION")))
            ic = get_flag_html(n) if "country" in sub else (f"{get_flag_html(e.get('country', ''))} 📍" if "subdivision" in sub else ("🌐" if "region" in sub else "🌏"))
            ico = {"Total": "🏆", "Geography": "🌍", "Time": "⏱️"}.get(ctype, "📍")
            ct = f"""<div class="event-title event-title-capture">{ico} CONTROL FLIP: {lt} {ctype.upper()}</div><div class="change-visual"><span class="discovery-highlight">{n}</span><span class="arrow" style="margin-left:10px;">➔</span> <span class="player-name {pc(p)}">{p.upper()}</span> <span class="arrow">➜</span> <span class="player-name {pc(c)}">{c.upper()}</span></div>"""
            rc = "row-capture"
        elif et == 'milestone':
            sub, n, cnt = e['subtype'], e['name'], e['count']
            ic, rc = "🎉", "row-milestone"
            lbl = f"{n.upper()}" if sub in ["continent", "region", "country", "subdivision"] else (f"{n} DECADE" if sub == "decade" else (f"{n} YEAR" if sub == "year" else "TOTAL GAMES"))
            det = f"{cnt} Games in {n}" if sub != "total" else f"{cnt} Games Played"
            ct = f"""<div class="event-title event-title-milestone">MILESTONE REACHED</div><div class="change-visual"><span class="discovery-highlight">{lbl}</span><span class="record-detail">{det}</span></div>"""
        rh += f"""<div class="event-row {rc}"><div class="category-box"><div class="cat-icon">{ic}</div><div class="cat-name">{cs}</div></div><div class="content-box">{ct}</div></div>"""
    return f"""<div class="daily-card" id="{day_id}"><div class="daily-header"><span class="daily-date">{ds}</span><span class="daily-badge">{ec} Updates</span></div><div class="events-list">{rh}</div></div>"""

raw_data = load_data()
if not raw_data.empty:
    df_t, df_tm, df_g = prepare_total_margins_data(raw_data), prepare_time_margins_data(raw_data), prepare_geography_margins_data(raw_data)
    all_evs = []
    all_evs.extend(generate_news_events(df_t, "Total Score", 5))
    all_evs.extend(generate_news_events(df_t, "Total Score", 10))
    all_evs.extend(generate_news_events(df_tm, "Time Score", 5))
    all_evs.extend(generate_news_events(df_tm, "Time Score", 10))
    all_evs.extend(generate_news_events(df_g, "Geography Score", 5))
    all_evs.extend(generate_news_events(df_g, "Geography Score", 10))
    all_evs.extend(generate_streak_events(df_t, "Total Score"))
    all_evs.extend(generate_streak_events(df_tm, "Time Score"))
    all_evs.extend(generate_streak_events(df_g, "Geography Score"))
    all_evs.extend(generate_score_threshold_streaks(df_t))
    all_evs.extend(generate_score_threshold_streaks(df_tm)) 
    all_evs.extend(generate_score_threshold_streaks(df_g)) 
    all_evs.extend(generate_margin_record_events(df_t, "Total Score"))
    all_evs.extend(generate_margin_record_events(df_tm, "Time Score"))
    all_evs.extend(generate_margin_record_events(df_g, "Geography Score"))
    all_evs.extend(generate_score_record_events(df_t, "Total Score"))
    all_evs.extend(generate_score_record_events(df_tm, "Time Score"))
    all_evs.extend(generate_score_record_events(df_g, "Geography Score"))
    all_evs.extend(generate_location_events(raw_data))
    all_evs.extend(generate_year_events(raw_data))
    all_evs.extend(generate_decade_events(raw_data))
    all_evs.extend(generate_milestone_events(raw_data))
    
    with st.sidebar:
        st.header("Feed Settings")
        fo = {"Momentum Shifts": ["flip"], "Win Streak Updates": ["streak", "streak_broken"], "Score Threshold Streaks": ["score_streak", "score_streak_broken"], "Win Margin Records": ["margin_record", "margin_near_record"], "Leaderboard Records": ["score_top_10", "score_vs_opp"], "Location Updates": ["discovery", "location_flip"], "Year Updates": ["year_discovery", "year_flip", "decade_discovery", "decade_flip"], "Milestones": ["milestone"]}
        sf = st.multiselect("Filter Event Types:", options=list(fo.keys()), default=list(fo.keys()))
        at = set()
        for f in sf: at.update(fo[f])

    fe = [e for e in all_evs if e.get('event_type', 'flip') in at]
    ev_d = {}
    for e in fe:
        d = e['date']
        if d not in ev_d: ev_d[d] = []
        ev_d[d].append(e)
    sd = sorted(ev_d.keys(), reverse=True)
    
    st.markdown('<div id="top"></div>', unsafe_allow_html=True)
    st.markdown("""<div class="page-header"><h1 class="page-title">The Daily Guessr</h1><div class="page-subtitle">Tracking Momentum & Leaderboard Shifts</div></div>""", unsafe_allow_html=True)
    st.markdown(render_forecast_section([get_full_category_forecast(df_t, "Total Score"), get_full_category_forecast(df_tm, "Time Score"), get_full_category_forecast(df_g, "Geography Score")]), unsafe_allow_html=True)
    st.markdown('<a href="#top" class="back-to-top">↑</a>', unsafe_allow_html=True)
    st.markdown('<div class="news-container">', unsafe_allow_html=True)
    if not sd: st.info("No news events detected.")
    else:
        for d in sd: st.markdown(render_daily_news(d, ev_d[d]), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
else: st.warning("Please ensure 'Timeguessr_Stats.csv' is in the 'Data' folder.")