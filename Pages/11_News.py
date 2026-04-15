import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import datetime
import country_converter as coco

# --- Configuration ---
st.set_page_config(page_title="The Daily Guessr", layout="wide")

# Global Initialization to drastically improve load speeds
cc_obj = coco.CountryConverter()

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
        .news-container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
        
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
        
        /* DAILY FEED / CATEGORY CARDS */
        .daily-card { background: #fff; border: 1px solid #ddd; border-top: 4px solid #333; border-radius: 8px; margin-bottom: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); scroll-margin-top: 50px; overflow: hidden; }
        .daily-header { background-color: #fcfcfc; padding: 16px 24px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .daily-date { font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 18px; color: #111; text-transform: uppercase; }
        .daily-badge { font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 700; background: #eee; color: #555; padding: 4px 10px; border: 1px solid #ccc; text-transform: uppercase; letter-spacing: 1px; border-radius: 4px; }
        
        .events-list { column-count: 2; column-gap: 24px; padding: 24px; background-color: #fafafa; }
        .news-category-block { break-inside: avoid-column; page-break-inside: avoid; display: inline-block; width: 100%; background: #fff; border: 1px solid #eaeaea; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
        .daily-section-header { font-family: 'Poppins', sans-serif; font-size: 12px; font-weight: 700; color: #555; text-transform: uppercase; padding: 12px 20px; background-color: #f8f9fa; border-bottom: 1px solid #eee; letter-spacing: 1px; border-radius: 8px 8px 0 0; }
        
        .event-row { padding: 16px 20px; border-bottom: 1px solid #f0f0f0; display: flex; align-items: flex-start; gap: 20px; transition: background-color 0.2s; }
        .event-row:last-child { border-bottom: none; border-radius: 0 0 8px 8px; }
        
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
        
        @media (max-width: 900px) { 
            .forecast-container { grid-template-columns: 1fr; } 
            .events-list { column-count: 1; padding: 16px; }
        }
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
                mean_c = f"{p} {cat} Score (Mean)"
                base_c = f"{p} {cat} Score"
                
                # Use the Mean column natively if available
                if mean_c in data.columns:
                    if data[mean_c].dtype == object:
                        data[mean_c] = data[mean_c].astype(str).str.replace(',', '')
                    data[base_c] = pd.to_numeric(data[mean_c], errors='coerce')
                # Fallback to the basic score column
                elif base_c in data.columns:
                    if data[base_c].dtype == object:
                        data[base_c] = data[base_c].astype(str).str.replace(',', '')
                    data[base_c] = pd.to_numeric(data[base_c], errors='coerce')
            
            if f"{p} Total Score" not in data.columns or data[f"{p} Total Score"].isna().all():
                data[f"{p} Total Score"] = data.groupby("Date")[f"{p} Geography Score"].transform('sum') + \
                                           data.groupby("Date")[f"{p} Time Score"].transform('sum')

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
    
    evs = []
    prev_state = None
    prev_val = None
    days_in_state = 0
    margin_history = {"Michael": [], "Sarah": []}
    
    for game_num, (idx, r) in enumerate(t.iterrows(), start=1):
        if pd.isna(r["Rolling"]): continue
        curr_state = get_leader_state(r["Rolling"])
        curr_val = r["Rolling"]
        date = r["Date"]
        
        if prev_state is None:
            prev_state = curr_state
            days_in_state = 1
        elif curr_state == prev_state:
            days_in_state += 1
        else:
            evs.append({
                "date": date, 
                "category": cat, 
                "event_type": "flip", 
                "window": window, 
                "prev_state": prev_state, 
                "current_state": curr_state, 
                "prev_val": prev_val,
                "curr_val": curr_val,
                "days_held": days_in_state
            })
            prev_state = curr_state
            days_in_state = 1
            
        prev_val = curr_val
        
        # --- Momentum Record Logic ---
        if curr_state == "Tie" or curr_val == 0: continue
        margin = abs(curr_val)
        winner = curr_state
        opponent = "Sarah" if winner == "Michael" else "Michael"
        
        current_largest = sorted(margin_history[winner], key=lambda x: x[0], reverse=True)
        rank_largest = 1
        for prev_m in current_largest:
            if margin < prev_m[0]: rank_largest += 1
            else: break
            
        days_since_largest = None
        ref_date_largest = None
        for i in range(len(margin_history[winner]) - 1, -1, -1):
            if margin_history[winner][i][0] >= margin:
                days_since_largest = game_num - margin_history[winner][i][2]
                ref_date_largest = margin_history[winner][i][1]
                break
                
        if days_since_largest is None:
            days_since_largest = game_num
            
        if rank_largest <= 10:
            player_max = current_largest[0][0] if current_largest else None
            is_pb_tie = player_max is not None and margin == player_max
            
            opp_max = max([m[0] for m in margin_history[opponent]]) if margin_history[opponent] else 0
            overall_max = max(player_max if player_max is not None else 0, opp_max)
            
            is_all_time_new = margin > overall_max
            is_all_time_tie = margin == overall_max and overall_max > 0
                
            evs.append({
                "date": date, "category": cat, "event_type": "momentum_record_largest", 
                "window": window,
                "player": winner, "margin": margin, "rank": rank_largest, 
                "days_since": days_since_largest, "ref_date": ref_date_largest, 
                "is_pb_tie": is_pb_tie,
                "is_all_time_new": is_all_time_new and len(margin_history[winner]) > 0,
                "is_all_time_tie": is_all_time_tie and len(margin_history[winner]) > 0
            })
            
        margin_history[winner].append((margin, date, game_num))
        
    return evs

def generate_streak_events(df, cat, min_streak=3):
    if df.empty: return []
    events = []
    personal_bests = {"Michael": 0, "Sarah": 0}
    completed_blocks = {"Michael": [], "Sarah": []}
    current_winner = None
    current_streak = 0
    prev_date = None
    
    for game_num, (idx, row) in enumerate(df.iterrows(), start=1):
        diff, date = row["Score Diff"], row["Date"]
        winner = "Michael" if diff > 0 else ("Sarah" if diff < 0 else "Tie")
            
        if winner == current_winner and winner != "Tie":
            current_streak += 1
        else:
            if current_winner and current_winner != "Tie" and current_streak > 0:
                completed_blocks[current_winner].append({'len': current_streak, 'end_game': game_num - 1, 'date': prev_date})
                
                pb = personal_bests[current_winner]
                if current_streak >= min_streak or (pb > 0 and current_streak >= (pb - 1)):
                    sub = "denied_break" if current_streak == pb else ("denied_match" if current_streak == pb - 1 else "significant_break")
                    events.append({"date": date, "category": cat, "event_type": "streak_broken", "subtype": sub, "player": current_winner, "breaker": winner, "count": current_streak, "record": pb})
            
            current_winner = winner
            current_streak = 1 if winner != "Tie" else 0
            
        if current_winner and current_winner != "Tie":
            if current_streak >= min_streak:
                past_blocks = [b for b in completed_blocks[current_winner] if b['len'] >= current_streak]
                times_reached = len(past_blocks) + 1
                last_end = past_blocks[-1]['end_game'] if past_blocks else None
                last_reached_date = past_blocks[-1]['date'] if past_blocks else None
                games_since = (game_num - last_end) if last_end else None
                
                pb = personal_bests[current_winner]
                if current_streak > pb:
                    sub = "new_record"
                elif current_streak == pb:
                    sub = "matched_record"
                else:
                    sub = "active"
                    
                events.append({"date": date, "category": cat, "event_type": "streak", "subtype": sub, "player": current_winner, "count": current_streak, "times_reached": times_reached, "days_since_last": games_since, "last_reached_date": last_reached_date})
                
            if current_streak > personal_bests[current_winner]:
                personal_bests[current_winner] = current_streak
        
        prev_date = date
                
    return events

def generate_margin_record_events(df, category_name):
    if df.empty: return []
    events = []
    margin_history = {"Michael": [], "Sarah": []}
    
    for game_num, (idx, row) in enumerate(df.iterrows(), start=1):
        diff, date = row["Score Diff"], row["Date"]
        if diff == 0: continue
        winner = "Michael" if diff > 0 else "Sarah"
        margin = abs(diff)
        opponent = "Sarah" if winner == "Michael" else "Michael"
        
        # --- Largest Win (Max Margin) Top 10 Logic ---
        current_largest = sorted(margin_history[winner], key=lambda x: x[0], reverse=True)
        rank_largest = 1
        for prev_m in current_largest:
            if margin < prev_m[0]: rank_largest += 1
            else: break
            
        days_since_largest = None
        ref_date_largest = None
        for i in range(len(margin_history[winner]) - 1, -1, -1):
            if margin_history[winner][i][0] >= margin:
                days_since_largest = game_num - margin_history[winner][i][2]
                ref_date_largest = margin_history[winner][i][1]
                break
                
        if days_since_largest is None:
            days_since_largest = game_num
            
        if rank_largest <= 10:
            player_max = current_largest[0][0] if current_largest else None
            is_pb_tie = player_max is not None and margin == player_max
            
            opp_max = max([m[0] for m in margin_history[opponent]]) if margin_history[opponent] else 0
            overall_max = max(player_max if player_max is not None else 0, opp_max)
            
            is_all_time_new = margin > overall_max
            is_all_time_tie = margin == overall_max and overall_max > 0
                
            events.append({
                "date": date, "category": category_name, "event_type": "margin_record_largest", 
                "player": winner, "margin": margin, "rank": rank_largest, 
                "days_since": days_since_largest, "ref_date": ref_date_largest, 
                "is_pb_tie": is_pb_tie,
                "is_all_time_new": is_all_time_new and len(margin_history[winner]) > 0,
                "is_all_time_tie": is_all_time_tie and len(margin_history[winner]) > 0
            })
            
        # --- Tightest Win (Min Margin) Top 10 Logic ---
        current_tightest = sorted(margin_history[winner], key=lambda x: x[0])
        rank_tightest = 1
        for prev_m in current_tightest:
            if margin > prev_m[0]: rank_tightest += 1
            else: break
            
        days_since_tightest = None
        ref_date_tightest = None
        for i in range(len(margin_history[winner]) - 1, -1, -1):
            if margin_history[winner][i][0] <= margin:
                days_since_tightest = game_num - margin_history[winner][i][2]
                ref_date_tightest = margin_history[winner][i][1]
                break
                
        if days_since_tightest is None:
            days_since_tightest = game_num
            
        if rank_tightest <= 10:
            player_min = current_tightest[0][0] if current_tightest else None
            is_pb_tie = player_min is not None and margin == player_min
            
            opp_min = min([m[0] for m in margin_history[opponent]]) if margin_history[opponent] else float('inf')
            overall_min = min(player_min if player_min is not None else float('inf'), opp_min)
            
            is_all_time_new = margin < overall_min
            is_all_time_tie = margin == overall_min and overall_min != float('inf')
                
            events.append({
                "date": date, "category": category_name, "event_type": "margin_record_tightest", 
                "player": winner, "margin": margin, "rank": rank_tightest, 
                "days_since": days_since_tightest, "ref_date": ref_date_tightest, 
                "is_pb_tie": is_pb_tie,
                "is_all_time_new": is_all_time_new and len(margin_history[winner]) > 0,
                "is_all_time_tie": is_all_time_tie and len(margin_history[winner]) > 0
            })
            
        margin_history[winner].append((margin, date, game_num))
        
    return events

def generate_score_record_events(df, category_name):
    if df.empty: return []
    events = []
    
    # Store history for Top 10 logic
    score_history = {"Michael": [], "Sarah": []}
    rival_pb = {"Michael": 0, "Sarah": 0}
    rival_worst = {"Michael": float('inf'), "Sarah": float('inf')}

    for idx, row in df.iterrows():
        date = row["Date"]
        for player in ["Michael", "Sarah"]:
            score = row[f"{player} {category_name}"]
            if pd.isna(score): continue
            
            opponent = "Sarah" if player == "Michael" else "Michael"
            
            # --- Top 10 Logic ---
            current_leaderboard = sorted(score_history[player], key=lambda x: x[0], reverse=True)
            
            # Calculate Rank
            rank = 1
            for prev_score in current_leaderboard:
                if score < prev_score[0]:
                    rank += 1
                else:
                    break
            
            # Calculate "Best score in X games"
            days_since = None
            ref_date = None
            for i in range(len(score_history[player]) - 1, -1, -1):
                if score_history[player][i][0] >= score:
                    days_since = len(score_history[player]) - i
                    ref_date = score_history[player][i][1]
                    break
            
            if days_since is None:
                # All-time record across all games played so far
                days_since = len(score_history[player]) + 1
            
            if rank <= 10:
                current_max = current_leaderboard[0][0] if current_leaderboard else None
                is_pb_tie = current_max is not None and score == current_max
                events.append({
                    "date": date, 
                    "category": category_name, 
                    "event_type": "score_top_10", 
                    "player": player, 
                    "score": score, 
                    "rank": rank,
                    "days_since": days_since,
                    "ref_date": ref_date,
                    "is_pb_tie": is_pb_tie,
                    "is_all_time": rank == 1 and len(score_history[player]) > 0
                })

            # --- Bottom 10 Logic ---
            bottom_days_since = None
            bottom_ref_date = None
            if len(score_history[player]) > 0:  # Skip game 1 so it doesn't trigger "All-Time Worst" on day 1
                current_bottom_leaderboard = sorted(score_history[player], key=lambda x: x[0])
                
                # Calculate Bottom Rank
                bottom_rank = 1
                for prev_score in current_bottom_leaderboard:
                    if score > prev_score[0]:
                        bottom_rank += 1
                    else:
                        break
                
                # Calculate "Worst score in X games"
                for i in range(len(score_history[player]) - 1, -1, -1):
                    if score_history[player][i][0] <= score:
                        bottom_days_since = len(score_history[player]) - i
                        bottom_ref_date = score_history[player][i][1]
                        break
                
                if bottom_days_since is None:
                    # All-time worst across all games played so far
                    bottom_days_since = len(score_history[player]) + 1
                
                if bottom_rank <= 10:
                    current_min = current_bottom_leaderboard[0][0] if current_bottom_leaderboard else None
                    is_worst_tie = current_min is not None and score == current_min
                    events.append({
                        "date": date, 
                        "category": category_name, 
                        "event_type": "score_bottom_10", 
                        "player": player, 
                        "score": score, 
                        "rank": bottom_rank,
                        "days_since": bottom_days_since,
                        "ref_date": bottom_ref_date,
                        "is_worst_tie": is_worst_tie,
                        "is_all_time": bottom_rank == 1
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
                    "opp_record": opp_record,
                    "days_since": days_since,
                    "ref_date": ref_date
                })
                
            # --- Worse Than Opponent's Worst Logic ---
            opp_worst = rival_worst[opponent]
            if opp_worst != float('inf') and score < opp_worst:
                events.append({
                    "date": date, 
                    "category": category_name, 
                    "event_type": "score_vs_opp", 
                    "subtype": "worse_than_opp_min", 
                    "player": player, 
                    "score": score, 
                    "opponent": opponent, 
                    "opp_record": opp_worst,
                    "days_since": bottom_days_since,
                    "ref_date": bottom_ref_date
                })

            # Update histories for next day processing
            score_history[player].append((score, date))
            if score > rival_pb[player]:
                rival_pb[player] = score
            if score < rival_worst[player]:
                rival_worst[player] = score
                
    return events

def generate_momentum_score_events(df, category_name, window=5):
    if len(df) < window: return []
    events = []
    t = df.copy()
    for p in ["Michael", "Sarah"]:
        t[f"{p}_rolling"] = t[f"{p} {category_name}"].rolling(window=window).mean()
        
    score_history = {"Michael": [], "Sarah": []}

    for game_num, (idx, row) in enumerate(t.iterrows(), start=1):
        date = row["Date"]
        for player in ["Michael", "Sarah"]:
            score = row[f"{player}_rolling"]
            if pd.isna(score): continue
            
            # --- Top 10 Logic ---
            current_leaderboard = sorted(score_history[player], key=lambda x: x[0], reverse=True)
            rank = 1
            for prev_score in current_leaderboard:
                if score < prev_score[0]: rank += 1
                else: break
            
            days_since = None
            ref_date = None
            for i in range(len(score_history[player]) - 1, -1, -1):
                if score_history[player][i][0] >= score:
                    days_since = game_num - score_history[player][i][2]
                    ref_date = score_history[player][i][1]
                    break
            
            if days_since is None:
                days_since = game_num
            
            if rank <= 10:
                current_max = current_leaderboard[0][0] if current_leaderboard else None
                is_pb_tie = current_max is not None and score == current_max
                events.append({
                    "date": date, 
                    "category": category_name, 
                    "event_type": "momentum_score_top_10", 
                    "window": window,
                    "player": player, 
                    "score": score, 
                    "rank": rank,
                    "days_since": days_since,
                    "ref_date": ref_date,
                    "is_pb_tie": is_pb_tie,
                    "is_all_time": rank == 1 and len(score_history[player]) > 0
                })

            # --- Bottom 10 Logic ---
            bottom_days_since = None
            bottom_ref_date = None
            if len(score_history[player]) > 0:
                current_bottom_leaderboard = sorted(score_history[player], key=lambda x: x[0])
                bottom_rank = 1
                for prev_score in current_bottom_leaderboard:
                    if score > prev_score[0]: bottom_rank += 1
                    else: break
                
                for i in range(len(score_history[player]) - 1, -1, -1):
                    if score_history[player][i][0] <= score:
                        bottom_days_since = game_num - score_history[player][i][2]
                        bottom_ref_date = score_history[player][i][1]
                        break
                
                if bottom_days_since is None:
                    bottom_days_since = game_num
                
                if bottom_rank <= 10:
                    current_min = current_bottom_leaderboard[0][0] if current_bottom_leaderboard else None
                    is_worst_tie = current_min is not None and score == current_min
                    events.append({
                        "date": date, 
                        "category": category_name, 
                        "event_type": "momentum_score_bottom_10", 
                        "window": window,
                        "player": player, 
                        "score": score, 
                        "rank": bottom_rank,
                        "days_since": bottom_days_since,
                        "ref_date": bottom_ref_date,
                        "is_worst_tie": is_worst_tie,
                        "is_all_time": bottom_rank == 1
                    })

            score_history[player].append((score, date, game_num))
            
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
    completed_blocks = {}
    for c in configs: 
        cat = c['cat']
        stt[cat] = {p: {t['id']: {'cur': 0, 'max': 0} for t in c['th']} for p in ["Michael", "Sarah"]}
        completed_blocks[cat] = {p: {t['id']: [] for t in c['th']} for p in ["Michael", "Sarah"]}
        
    prev_date = None
    for game_num, (idx, row) in enumerate(df.iterrows(), start=1):
        date = row["Date"]
        for c in configs:
            cat = c['cat']
            for p in ["Michael", "Sarah"]:
                col = c['fmt'].format(p=p)
                if col not in df.columns: continue
                s = row[col]
                for t in c['th']:
                    tid = t['id']
                    trk = stt[cat][p][tid]
                    blocks = completed_blocks[cat][p][tid]
                    
                    if t['chk'](s):
                        trk['cur'] += 1
                        cu = trk['cur']
                        mx = trk['max']
                        
                        if cu >= t['min']:
                            past_blocks = [b for b in blocks if b['len'] >= cu]
                            times_reached = len(past_blocks) + 1
                            last_end = past_blocks[-1]['end_game'] if past_blocks else None
                            last_reached_date = past_blocks[-1]['date'] if past_blocks else None
                            games_since = (game_num - last_end) if last_end else None
                            
                            if cu > mx:
                                sub = "new_record"
                            elif cu == mx:
                                sub = "matched_record"
                            else:
                                sub = "active"
                                
                            events.append({"date": date, "category": cat, "event_type": "score_streak", "subtype": sub, "player": p, "count": cu, "threshold_label": t['lbl'], "streak_type": t['typ'], "times_reached": times_reached, "days_since_last": games_since, "last_reached_date": last_reached_date})
                            
                        if cu > mx:
                            trk['max'] = cu
                    else:
                        if trk['cur'] > 0:
                            cu = trk['cur']
                            mx = trk['max']
                            blocks.append({'len': cu, 'end_game': game_num - 1, 'date': prev_date})
                            
                            if cu >= t['min'] or cu == mx or cu == mx - 1:
                                sub = "denied_break" if cu == mx else ("denied_match" if cu == mx - 1 else "significant_break")
                                if cu >= t['min'] or sub != "significant_break":
                                    events.append({"date": date, "category": cat, "event_type": "score_streak_broken", "subtype": sub, "player": p, "count": cu, "record": mx, "threshold_label": t['lbl'], "streak_type": t['typ']})
                        trk['cur'] = 0
        prev_date = date
    return events

def generate_milestone_events(df):
    if df.empty: return []
    evs = []
    dec, yr, loc = {}, {}, {}
    dec_years = {}
    cont_regions = {}
    reg_countries = {}
    country_subdivs = {}
    country_cities = {}
    subdiv_cities = {}
    seen_dates = set()
    total_days = 0
    
    uc = list(df["Country"].dropna().unique())
    iso_res = cc_obj.convert(names=uc, to='ISO3', not_found='Unknown') if uc else []
    if isinstance(iso_res, str): iso_res = [iso_res]
    iso = dict(zip(uc, iso_res))
    
    ui = [i for i in set(iso.values()) if i and i != 'Unknown']
    reg_res = cc_obj.convert(names=ui, to="UNregion", not_found="Unknown") if ui else []
    if isinstance(reg_res, str): reg_res = [reg_res]
    reg = dict(zip(ui, reg_res))
    
    con_res = cc_obj.convert(names=ui, to="continent", not_found="Unknown") if ui else []
    if isinstance(con_res, str): con_res = [con_res]
    con = dict(zip(ui, con_res))
    
    def is_milestone(n):
        return n in [5, 10, 15, 20, 25, 50, 75, 100] or (n > 100 and n % 50 == 0)
    
    for _, r in df.sort_values("Date").iterrows():
        dt = r["Date"]
        if dt not in seen_dates:
            seen_dates.add(dt)
            total_days += 1
            if is_milestone(total_days):
                evs.append({"date": dt, "category": "Milestone", "event_type": "milestone", "subtype": "total", "name": "Total Games", "count": total_days})
        
        y = r.get("Year")
        if pd.notna(y):
            ystr = str(int(y))
            yr[ystr] = yr.get(ystr, 0) + 1
            if is_milestone(yr[ystr]): evs.append({"date": dt, "category": "Milestone", "event_type": "milestone", "subtype": "year", "name": ystr, "count": yr[ystr]})
            try: dstr = str(int(y // 10) * 10) + "s"
            except: dstr = None
            if dstr:
                dec[dstr] = dec.get(dstr, 0) + 1
                if dstr not in dec_years: dec_years[dstr] = {}
                dec_years[dstr][ystr] = dec_years[dstr].get(ystr, 0) + 1
                
                if is_milestone(dec[dstr]): 
                    milestone_val = dec[dstr]
                    threshold = milestone_val * 0.1
                    sorted_years = sorted(dec_years[dstr].items(), key=lambda item: item[1], reverse=True)
                    
                    top_subitems = [x for x in sorted_years if x[1] >= threshold]
                    other_items = [x for x in sorted_years if x[1] < threshold]
                    
                    if len(other_items) == 1:
                        top_subitems.append(other_items[0])
                        other_count = 0
                    else:
                        other_count = sum(x[1] for x in other_items)
                        
                    evs.append({"date": dt, "category": "Milestone", "event_type": "milestone", "subtype": "decade", "name": dstr, "count": milestone_val, "top_subitems": top_subitems, "other_count": other_count, "subitems_label": "Top Years"})
        
        c, s = r.get("Country"), r.get("Subdivision")
        city = r.get("City")
        ccl = str(c).strip() if pd.notna(c) else "Unknown"
        scl = str(s).strip() if pd.notna(s) and str(s).strip() else None
        city_str = str(city).strip() if pd.notna(city) and str(city).strip() else None
        isoc = iso.get(ccl)
        rg, cn = reg.get(isoc, "Unknown"), con.get(isoc, "Unknown")
        
        if cn != "Unknown" and rg != "Unknown":
            if cn not in cont_regions: cont_regions[cn] = {}
            cont_regions[cn][rg] = cont_regions[cn].get(rg, 0) + 1
            
        if rg != "Unknown" and ccl != "Unknown":
            if rg not in reg_countries: reg_countries[rg] = {}
            reg_countries[rg][ccl] = reg_countries[rg].get(ccl, 0) + 1
            
        if ccl != "Unknown":
            if scl:
                if ccl not in country_subdivs: country_subdivs[ccl] = {}
                country_subdivs[ccl][scl] = country_subdivs[ccl].get(scl, 0) + 1
            if city_str:
                if ccl not in country_cities: country_cities[ccl] = {}
                country_cities[ccl][city_str] = country_cities[ccl].get(city_str, 0) + 1
                
        if scl and city_str:
            if scl not in subdiv_cities: subdiv_cities[scl] = {}
            subdiv_cities[scl][city_str] = subdiv_cities[scl].get(city_str, 0) + 1
        
        for kt, kn in [("continent", cn), ("region", rg), ("country", ccl), ("subdivision", scl)]:
            if kn and kn != "Unknown":
                k = (kt, kn)
                loc[k] = loc.get(k, 0) + 1
                if is_milestone(loc[k]): 
                    milestone_val = loc[k]
                    threshold = milestone_val * 0.1
                    event = {"date": dt, "category": "Milestone", "event_type": "milestone", "subtype": kt, "name": kn, "count": milestone_val}
                    
                    items_dict = None
                    sub_lbl = None
                    if kt == "continent" and kn in cont_regions:
                        items_dict = cont_regions[kn]
                        sub_lbl = "Top Regions"
                    elif kt == "region" and kn in reg_countries:
                        items_dict = reg_countries[kn]
                        sub_lbl = "Top Countries"
                    elif kt == "country":
                        if kn in country_subdivs:
                            items_dict = country_subdivs[kn]
                            sub_lbl = "Top Subdivisions"
                        elif kn in country_cities:
                            items_dict = country_cities[kn]
                            sub_lbl = "Top Cities"
                    elif kt == "subdivision" and kn in subdiv_cities:
                        items_dict = subdiv_cities[kn]
                        sub_lbl = "Top Cities"
                        
                    if items_dict:
                        sorted_items = sorted(items_dict.items(), key=lambda x: x[1], reverse=True)
                        top_subitems = [x for x in sorted_items if x[1] >= threshold]
                        other_items = [x for x in sorted_items if x[1] < threshold]
                        
                        if len(other_items) == 1:
                            top_subitems.append(other_items[0])
                            event["other_count"] = 0
                        else:
                            event["other_count"] = sum(x[1] for x in other_items)
                        event["top_subitems"] = top_subitems
                        event["subitems_label"] = sub_lbl
                        
                    evs.append(event)
    return evs

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
    events = []
    perf_data = df.copy()
    
    # Strictly base row "Total Score" on Geography + Time 
    # This prevents using the date-aggregated total for row-specific locations
    for p in ["Michael", "Sarah"]:
        geo_col = f"{p} Geography Score"
        time_col = f"{p} Time Score"
        if geo_col not in perf_data.columns: perf_data[geo_col] = 0
        if time_col not in perf_data.columns: perf_data[time_col] = 0
        perf_data[geo_col] = perf_data[geo_col].fillna(0)
        perf_data[time_col] = perf_data[time_col].fillna(0)
        perf_data[f"{p} Total Score"] = perf_data[geo_col] + perf_data[time_col]
                
    uc = list(df["Country"].dropna().unique())
    iso_res = cc_obj.convert(names=uc, to='ISO3', not_found='Unknown') if uc else []
    if isinstance(iso_res, str): iso_res = [iso_res]
    iso = dict(zip(uc, iso_res))
    
    ui = [i for i in set(iso.values()) if i and i != 'Unknown']
    reg_res = cc_obj.convert(names=ui, to="UNregion", not_found="Unknown") if ui else []
    if isinstance(reg_res, str): reg_res = [reg_res]
    reg = dict(zip(ui, reg_res))
    
    con_res = cc_obj.convert(names=ui, to="continent", not_found="Unknown") if ui else []
    if isinstance(con_res, str): con_res = [con_res]
    con = dict(zip(ui, con_res))

    locations_state = {"continent": {}, "region": {}, "country": {}, "subdivision": {}}
    last_seen_day = {"continent": {}, "region": {}, "country": {}, "subdivision": {}}
    appearances = {"continent": {}, "region": {}, "country": {}, "subdivision": {}}
    
    unique_dates = sorted(perf_data["Date"].unique())
    date_to_day = {d: i for i, d in enumerate(unique_dates, start=1)}

    for dt in unique_dates:
        day_data = perf_data[perf_data["Date"] == dt]
        current_day = date_to_day[dt]
        day_locs = {"continent": {}, "region": {}, "country": {}, "subdivision": {}}
        
        for _, r in day_data.iterrows():
            c, s = r.get("Country"), r.get("Subdivision")
            ccl = str(c).strip() if pd.notna(c) else "Unknown"
            scl = str(s).strip() if pd.notna(s) and str(s).strip() else None
            isoc = iso.get(ccl, "Unknown")
            rg = reg.get(isoc, "Unknown")
            cn = con.get(isoc, "Unknown")
            
            locs_to_update = []
            if cn != "Unknown": locs_to_update.append(("continent", cn, None, "new_continent"))
            if rg != "Unknown": locs_to_update.append(("region", rg, None, "new_un_region"))
            if ccl != "Unknown": locs_to_update.append(("country", ccl, None, "new_country"))
            if scl and ccl != "Unknown": locs_to_update.append(("subdivision", scl, ccl, "new_subdivision"))
            
            for l_type, l_name, parent, sub_str in locs_to_update:
                if l_name not in day_locs[l_type]:
                    day_locs[l_type][l_name] = {
                        "parent": parent, "sub_str": sub_str,
                        "Michael_Geography": 0, "Michael_Time": 0, "Michael_Total": 0,
                        "Sarah_Geography": 0, "Sarah_Time": 0, "Sarah_Total": 0
                    }
                dl = day_locs[l_type][l_name]
                for p in ["Michael", "Sarah"]:
                    dl[f"{p}_Geography"] += r[f"{p} Geography Score"]
                    dl[f"{p}_Time"] += r[f"{p} Time Score"]
                    dl[f"{p}_Total"] += r[f"{p} Total Score"]
                    
        for l_type, loc_dict in day_locs.items():
            for l_name, scores in loc_dict.items():
                parent = scores["parent"]
                sub_str = scores["sub_str"]
                
                prev_day = last_seen_day[l_type].get(l_name, 0)
                gap = current_day - prev_day if prev_day > 0 else 0
                last_seen_day[l_type][l_name] = current_day
                appearances[l_type][l_name] = appearances[l_type].get(l_name, 0) + 1
                app_count = appearances[l_type][l_name]
                
                if l_name not in locations_state[l_type]:
                    state = {
                        "Michael_Geography": 0, "Michael_Time": 0, "Michael_Total": 0,
                        "Sarah_Geography": 0, "Sarah_Time": 0, "Sarah_Total": 0,
                        "Geography": "Tie", "Time": "Tie", "Total": "Tie"
                    }
                    locations_state[l_type][l_name] = state
                    
                    for k in ["Michael_Geography", "Michael_Time", "Michael_Total", "Sarah_Geography", "Sarah_Time", "Sarah_Total"]:
                        state[k] += scores[k]
                        
                    perf = {}
                    for m in ["Geography", "Time", "Total"]:
                        m_score, s_score = state[f"Michael_{m}"], state[f"Sarah_{m}"]
                        w = "Michael" if m_score > s_score else ("Sarah" if s_score > m_score else "Tie")
                        state[m] = w
                        perf[m] = (w, abs(m_score - s_score))
                        
                    events.append({
                        "date": dt, "category": "Discovery", "event_type": "discovery",
                        "subtype": sub_str, "name": l_name, "country": parent if parent else "",
                        "perf": perf, "gap": gap
                    })
                else:
                    state = locations_state[l_type][l_name]
                    overall_perf = {}
                    flipped_metrics = []
                    
                    for m in ["Geography", "Time", "Total"]:
                        m_key, s_key = f"Michael_{m}", f"Sarah_{m}"
                        mb_old, sb_old = state[m_key], state[s_key]
                        old_w = state[m]
                        
                        state[m_key] += scores[m_key]
                        state[s_key] += scores[s_key]
                        ma_new, sa_new = state[m_key], state[s_key]
                        
                        new_w = "Michael" if ma_new > sa_new else ("Sarah" if sa_new > ma_new else "Tie")
                        
                        overall_perf[m] = {
                            "Michael": {"before": mb_old, "after": ma_new, "shift": scores[m_key]},
                            "Sarah": {"before": sb_old, "after": sa_new, "shift": scores[s_key]},
                            "old_leader": old_w, "new_leader": new_w, "did_flip": new_w != old_w
                        }
                        
                        if new_w != old_w:
                            flipped_metrics.append(m)
                            state[m] = new_w
                            
                    if flipped_metrics:
                        events.append({
                            "date": dt, "category": "Discovery", "event_type": "location_flip",
                            "subtype": l_type, "name": l_name, "country": parent if parent else "",
                            "overall_perf": overall_perf, "gap": gap, "is_rare": gap >= 25, "appearances": app_count
                        })
                    elif gap >= 25:
                        events.append({
                            "date": dt, "category": "Discovery", "event_type": "rare_location",
                            "subtype": l_type, "name": l_name, "country": parent if parent else "",
                            "overall_perf": overall_perf, "gap": gap, "appearances": app_count
                        })
                        
    return events

def generate_year_events(df):
    if df.empty: return []
    events = []
    perf_data = df.copy()
    
    # Strictly base row "Total Score" on Geography + Time 
    for p in ["Michael", "Sarah"]:
        geo_col = f"{p} Geography Score"
        time_col = f"{p} Time Score"
        if geo_col not in perf_data.columns: perf_data[geo_col] = 0
        if time_col not in perf_data.columns: perf_data[time_col] = 0
        perf_data[geo_col] = perf_data[geo_col].fillna(0)
        perf_data[time_col] = perf_data[time_col].fillna(0)
        perf_data[f"{p} Total Score"] = perf_data[geo_col] + perf_data[time_col]
            
    years_state = {}
    last_seen_day = {}
    appearances = {}
    
    unique_dates = sorted(perf_data["Date"].unique())
    date_to_day = {d: i for i, d in enumerate(unique_dates, start=1)}
    
    for dt in unique_dates:
        day_data = perf_data[perf_data["Date"] == dt]
        current_day = date_to_day[dt]
        day_years = {}
        
        for _, r in day_data.iterrows():
            y = r.get("Year")
            if pd.isna(y): continue
            ystr = str(int(y))
            
            if ystr not in day_years:
                day_years[ystr] = {
                    "Michael_Geography": 0, "Michael_Time": 0, "Michael_Total": 0,
                    "Sarah_Geography": 0, "Sarah_Time": 0, "Sarah_Total": 0
                }
            dl = day_years[ystr]
            for p in ["Michael", "Sarah"]:
                dl[f"{p}_Geography"] += r[f"{p} Geography Score"]
                dl[f"{p}_Time"] += r[f"{p} Time Score"]
                dl[f"{p}_Total"] += r[f"{p} Total Score"]
        
        for ystr, scores in day_years.items():
            prev_day = last_seen_day.get(ystr, 0)
            gap = current_day - prev_day if prev_day > 0 else 0
            last_seen_day[ystr] = current_day
            appearances[ystr] = appearances.get(ystr, 0) + 1
            app_count = appearances[ystr]
            
            if ystr not in years_state:
                state = {
                    "Michael_Geography": 0, "Michael_Time": 0, "Michael_Total": 0,
                    "Sarah_Geography": 0, "Sarah_Time": 0, "Sarah_Total": 0,
                    "Geography": "Tie", "Time": "Tie", "Total": "Tie"
                }
                years_state[ystr] = state
                
                for k in ["Michael_Geography", "Michael_Time", "Michael_Total", "Sarah_Geography", "Sarah_Time", "Sarah_Total"]:
                    state[k] += scores[k]
                    
                perf = {}
                for m in ["Geography", "Time", "Total"]:
                    m_score, s_score = state[f"Michael_{m}"], state[f"Sarah_{m}"]
                    w = "Michael" if m_score > s_score else ("Sarah" if s_score > m_score else "Tie")
                    state[m] = w
                    perf[m] = (w, abs(m_score - s_score))
                    
                events.append({
                    "date": dt, "category": "Year", "event_type": "year_discovery",
                    "subtype": "new_year", "name": ystr, "perf": perf, "gap": gap
                })
            else:
                state = years_state[ystr]
                overall_perf = {}
                flipped_metrics = []
                
                for m in ["Geography", "Time", "Total"]:
                    m_key, s_key = f"Michael_{m}", f"Sarah_{m}"
                    mb_old, sb_old = state[m_key], state[s_key]
                    old_w = state[m]
                    
                    state[m_key] += scores[m_key]
                    state[s_key] += scores[s_key]
                    ma_new, sa_new = state[m_key], state[s_key]
                    
                    new_w = "Michael" if ma_new > sa_new else ("Sarah" if sa_new > ma_new else "Tie")
                    
                    overall_perf[m] = {
                        "Michael": {"before": mb_old, "after": ma_new, "shift": scores[m_key]},
                        "Sarah": {"before": sb_old, "after": sa_new, "shift": scores[s_key]},
                        "old_leader": old_w, "new_leader": new_w, "did_flip": new_w != old_w
                    }
                    if new_w != old_w:
                        flipped_metrics.append(m)
                        state[m] = new_w
                        
                if flipped_metrics:
                    events.append({
                        "date": dt, "category": "Year", "event_type": "year_flip",
                        "subtype": "year", "name": ystr, "overall_perf": overall_perf, "gap": gap, "is_rare": gap >= 25, "appearances": app_count
                    })
                elif gap >= 25:
                    events.append({
                        "date": dt, "category": "Year", "event_type": "rare_year",
                        "subtype": "year", "name": ystr, "overall_perf": overall_perf, "gap": gap, "appearances": app_count
                    })
    return events

def generate_decade_events(df):
    if df.empty: return []
    events = []
    perf_data = df.copy()
    
    # Strictly base row "Total Score" on Geography + Time 
    for p in ["Michael", "Sarah"]:
        geo_col = f"{p} Geography Score"
        time_col = f"{p} Time Score"
        if geo_col not in perf_data.columns: perf_data[geo_col] = 0
        if time_col not in perf_data.columns: perf_data[time_col] = 0
        perf_data[geo_col] = perf_data[geo_col].fillna(0)
        perf_data[time_col] = perf_data[time_col].fillna(0)
        perf_data[f"{p} Total Score"] = perf_data[geo_col] + perf_data[time_col]
            
    decades_state = {}
    last_seen_day = {}
    appearances = {}
    
    unique_dates = sorted(perf_data["Date"].unique())
    date_to_day = {d: i for i, d in enumerate(unique_dates, start=1)}
    
    for dt in unique_dates:
        day_data = perf_data[perf_data["Date"] == dt]
        current_day = date_to_day[dt]
        day_decades = {}
        
        for _, r in day_data.iterrows():
            y = r.get("Year")
            if pd.isna(y): continue
            dstr = str(int(y // 10) * 10) + "s"
            
            if dstr not in day_decades:
                day_decades[dstr] = {
                    "Michael_Geography": 0, "Michael_Time": 0, "Michael_Total": 0,
                    "Sarah_Geography": 0, "Sarah_Time": 0, "Sarah_Total": 0
                }
            dl = day_decades[dstr]
            for p in ["Michael", "Sarah"]:
                dl[f"{p}_Geography"] += r[f"{p} Geography Score"]
                dl[f"{p}_Time"] += r[f"{p} Time Score"]
                dl[f"{p}_Total"] += r[f"{p} Total Score"]
        
        for dstr, scores in day_decades.items():
            prev_day = last_seen_day.get(dstr, 0)
            gap = current_day - prev_day if prev_day > 0 else 0
            last_seen_day[dstr] = current_day
            appearances[dstr] = appearances.get(dstr, 0) + 1
            app_count = appearances[dstr]
            
            if dstr not in decades_state:
                state = {
                    "Michael_Geography": 0, "Michael_Time": 0, "Michael_Total": 0,
                    "Sarah_Geography": 0, "Sarah_Time": 0, "Sarah_Total": 0,
                    "Geography": "Tie", "Time": "Tie", "Total": "Tie"
                }
                decades_state[dstr] = state
                
                for k in ["Michael_Geography", "Michael_Time", "Michael_Total", "Sarah_Geography", "Sarah_Time", "Sarah_Total"]:
                    state[k] += scores[k]
                    
                perf = {}
                for m in ["Geography", "Time", "Total"]:
                    m_score, s_score = state[f"Michael_{m}"], state[f"Sarah_{m}"]
                    w = "Michael" if m_score > s_score else ("Sarah" if s_score > m_score else "Tie")
                    state[m] = w
                    perf[m] = (w, abs(m_score - s_score))
                    
                events.append({
                    "date": dt, "category": "Decade", "event_type": "decade_discovery",
                    "subtype": "new_decade", "name": dstr, "perf": perf, "gap": gap
                })
            else:
                state = decades_state[dstr]
                overall_perf = {}
                flipped_metrics = []
                
                for m in ["Geography", "Time", "Total"]:
                    m_key, s_key = f"Michael_{m}", f"Sarah_{m}"
                    mb_old, sb_old = state[m_key], state[s_key]
                    old_w = state[m]
                    
                    state[m_key] += scores[m_key]
                    state[s_key] += scores[s_key]
                    ma_new, sa_new = state[m_key], state[s_key]
                    
                    new_w = "Michael" if ma_new > sa_new else ("Sarah" if sa_new > ma_new else "Tie")
                    
                    overall_perf[m] = {
                        "Michael": {"before": mb_old, "after": ma_new, "shift": scores[m_key]},
                        "Sarah": {"before": sb_old, "after": sa_new, "shift": scores[s_key]},
                        "old_leader": old_w, "new_leader": new_w, "did_flip": new_w != old_w
                    }
                    if new_w != old_w:
                        flipped_metrics.append(m)
                        state[m] = new_w
                        
                if flipped_metrics:
                    events.append({
                        "date": dt, "category": "Decade", "event_type": "decade_flip",
                        "subtype": "decade", "name": dstr, "overall_perf": overall_perf, "gap": gap, "is_rare": gap >= 25, "appearances": app_count
                    })
                elif gap >= 25:
                    events.append({
                        "date": dt, "category": "Decade", "event_type": "rare_decade",
                        "subtype": "decade", "name": dstr, "overall_perf": overall_perf, "gap": gap, "appearances": app_count
                    })
    return events

def get_full_category_forecast(df, cat):
    if len(df) < 5: return None
    r5 = df["Score Diff"].rolling(window=5).mean().iloc[-1]
    r10 = df["Score Diff"].rolling(window=10).mean().iloc[-1] if len(df) >= 10 else None
    
    if pd.notna(r5):
        l5 = get_leader_state(r5)
        b5 = -df.tail(4)["Score Diff"].sum()
        if l5 == "Michael": m5 = f"Sarah flips with win of <span class='target-hl'>{abs(b5):,.0f}+</span>" if b5 < 0 else f"Sarah flips with anything better than a loss of <span class='target-hl'>{abs(b5):,.0f}</span>"
        elif l5 == "Sarah": m5 = f"Michael flips with win of <span class='target-hl'>{b5:,.0f}+</span>" if b5 > 0 else f"Michael flips with anything better than a loss of <span class='target-hl'>{abs(b5):,.0f}</span>"
        else: m5 = "Next winner takes the lead."
    else: l5, m5 = "N/A", "Not enough data"

    if pd.notna(r10):
        l10 = get_leader_state(r10)
        b10 = -df.tail(9)["Score Diff"].sum()
        if l10 == "Michael": m10 = f"Sarah flips with win of <span class='target-hl'>{abs(b10):,.0f}+</span>" if b10 < 0 else f"Sarah flips with anything better than a loss of <span class='target-hl'>{abs(b10):,.0f}</span>"
        elif l10 == "Sarah": m10 = f"Michael flips with win of <span class='target-hl'>{b10:,.0f}+</span>" if b10 > 0 else f"Michael flips with anything better than a loss of <span class='target-hl'>{abs(b10):,.0f}</span>"
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
                tid = t['id']
                cur, rec = crun[p][tid], cmax[p][tid]
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

FEED_CATEGORIES = {
    "Momentum": ["flip", "momentum_record_largest", "momentum_score_top_10", "momentum_score_bottom_10"], 
    "Win Streak Updates": ["streak", "streak_broken"], 
    "Score Threshold Streaks": ["score_streak", "score_streak_broken"], 
    "Win Margin Records": ["margin_record_largest", "margin_record_tightest"], 
    "Leaderboard Records": ["score_top_10", "score_bottom_10", "score_vs_opp"], 
    "Location Updates": ["discovery", "location_flip", "rare_location"], 
    "Year Updates": ["year_discovery", "year_flip", "decade_discovery", "decade_flip", "rare_year", "rare_decade"], 
    "Milestones": ["milestone"]
}

def render_daily_news(dt, evs):
    ds, ec, rh = dt.strftime("%A, %B %d, %Y"), len(evs), ""
    day_id = f"day-{dt.strftime('%Y-%m-%d')}"
    
    def get_ordinal(n):
        if 11 <= (n % 100) <= 13: suffix = 'th'
        else: suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"

    rmap = {
        ('milestone', 'total'): 1, ('milestone', 'continent'): 2, ('milestone', 'region'): 3, ('milestone', 'country'): 4, ('milestone', 'subdivision'): 5, ('milestone', 'decade'): 6, ('milestone', 'year'): 7,
        ('score_top_10', ''): 10, ('score_bottom_10', ''): 11, ('margin_record_largest', ''): 12, ('margin_record_tightest', ''): 13, ('score_vs_opp', ''): 14,
        ('streak', 'new_record'): 20, ('streak', 'matched_record'): 21, ('streak', 'active'): 22, ('streak_broken', ''): 23, 
        ('score_streak', 'new_record'): 24, ('score_streak', 'matched_record'): 25, ('score_streak', 'active'): 26, ('score_streak_broken', ''): 27, 
        ('discovery', 'new_continent'): 30, ('discovery', 'new_un_region'): 31, ('discovery', 'new_country'): 32, ('discovery', 'new_subdivision'): 33, ('decade_discovery', 'new_decade'): 34, ('year_discovery', 'new_year'): 35,
        ('location_flip', 'continent'): 40, ('location_flip', 'region'): 41, ('location_flip', 'country'): 42, ('location_flip', 'subdivision'): 43, ('decade_flip', 'decade'): 44, ('year_flip', 'year'): 45,
        ('rare_location', 'continent'): 50, ('rare_location', 'region'): 51, ('rare_location', 'country'): 52, ('rare_location', 'subdivision'): 53, ('rare_decade', 'decade'): 54, ('rare_year', 'year'): 55,
        ('momentum_record_largest', ''): 62, ('momentum_score_top_10', ''): 63, ('momentum_score_bottom_10', ''): 64
    }
    
    def gr(e):
        t, s, w = e.get('event_type'), e.get('subtype', ''), e.get('window')
        if t == 'flip': return 60 if w == 10 else 61
        if t in ['score_top_10', 'score_bottom_10', 'margin_record_largest', 'margin_record_tightest', 'score_vs_opp', 'streak_broken', 'score_streak_broken', 'momentum_record_largest', 'momentum_score_top_10', 'momentum_score_bottom_10']: s = ''
        return rmap.get((t, s), 99)
    
    # Sort first by rank ascending
    evs.sort(key=gr)

    # Group events by category
    type_to_cat = {t: c for c, types in FEED_CATEGORIES.items() for t in types}
    events_by_sec = {c: [] for c in FEED_CATEGORIES.keys()}
    for e in evs:
        sec = type_to_cat.get(e.get('event_type'), "Other Updates")
        if sec in events_by_sec:
            events_by_sec[sec].append(e)
        else:
            if "Other Updates" not in events_by_sec: events_by_sec["Other Updates"] = []
            events_by_sec["Other Updates"].append(e)

    for sec_name in FEED_CATEGORIES.keys():
        sec_evs = events_by_sec.get(sec_name, [])
        if not sec_evs: continue
        
        rh += f'<div class="news-category-block"><div class="daily-section-header">{sec_name}</div>'

        for e in sec_evs:
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
                days_held = e.get('days_held', 0)
                
                txt = "DROPS TO TIE" if c == "Tie" else ("BREAKS TIE" if p == "Tie" else "TAKES THE LEAD")
                lead_info = f"Lead was {int(pv):,} pts → now {int(cv):,} pts"
                
                day_word = "day" if days_held == 1 else "days"
                held_str = f"Ended a {days_held}-day run by {p.upper()}" if p != "Tie" else f"After being tied for {days_held} {day_word}"
                
                ct = f"""<div class="event-title">{w}-GAME AVG: {cs} Score &middot; {txt}</div>
                         <div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="arrow">➜</span><span class="player-name {pc(c)}">{c.upper()}</span></div>
                         <div class="record-detail" style="margin-top:6px; font-size:13px;">
                            <div>{lead_info}</div>
                            <div style="color:#777; font-size:11.5px; font-weight:600; margin-top:3px;">{held_str}</div>
                         </div>"""
                rc = f"row-winner-{c}"
            elif et == 'momentum_record_largest':
                p, m, r, w = e['player'], e['margin'], e['rank'], e['window']
                is_pb = r == 1
                is_pb_tie = e.get('is_pb_tie', False)
                
                ic, rc = "🌊", "row-record-max"
                ord_rank = get_ordinal(r)
                days = e.get('days_since')
                ref_date = e.get('ref_date')
                ref_str = f" ({ref_date.strftime('%b %d, %Y').replace(' 0', ' ')})" if pd.notna(ref_date) else ""
                
                at_badge = ""
                if e.get('is_all_time_new'):
                    at_badge = '<span class="all-time-badge">ALL-TIME RECORD</span>'
                elif e.get('is_all_time_tie'):
                    at_badge = '<span class="all-time-badge" style="background-color:#7f8c8d;">TIED ALL-TIME RECORD</span>'
                
                tt = "TIED RECORD MOMENTUM" if (is_pb and is_pb_tie) else ("NEW RECORD MOMENTUM" if is_pb else f"TOP 10 BEST RUN ({ord_rank})")
                cl = "event-title-record-max"
                
                det_txt = f"Avg Margin: {int(m):,} pts &middot; Ranked {ord_rank} largest {w}-game average all-time"
                if days:
                    if days > 1:
                        if is_pb and not is_pb_tie: det_txt += f" &middot; Best {w}-game run in all {days} games played"
                        else: det_txt += f" &middot; Best {w}-game run in {days} games{ref_str}"
                    else:
                        det_txt += f" &middot; Best {w}-game run since yesterday"
                
                ct = f"""<div class="event-title {cl}">{w}-GAME AVG: {cs} Score &middot; {tt} {at_badge}</div>
                         <div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="record-detail">{det_txt}</span></div>"""
            elif et in ['momentum_score_top_10', 'momentum_score_bottom_10']:
                p, s, r, w = e['player'], e['score'], e['rank'], e['window']
                is_top = et == 'momentum_score_top_10'
                is_pb = r == 1
                is_pb_tie = e.get('is_pb_tie', False)
                ic = "👑" if (is_top and is_pb) else ("🏅" if is_top else ("📉" if is_pb else "⚠️"))
                rc = "row-score-max" if is_top else "row-score-min"
                ord_rank = get_ordinal(r)
                days = e.get('days_since')
                ref_date = e.get('ref_date')
                ref_str = f" ({ref_date.strftime('%b %d, %Y').replace(' 0', ' ')})" if pd.notna(ref_date) else ""
                
                if is_top:
                    tt = "TIED ALL-TIME RECORD" if (is_pb and is_pb_tie) else ("NEW ALL-TIME RECORD" if is_pb else f"TOP 10 BEST AVG ({ord_rank})")
                    cl = "event-title-score-max"
                    det_txt = f"Avg Score: {int(s):,} pts &middot; Ranked {ord_rank} highest {w}-game average all-time"
                else:
                    tt = "TIED ALL-TIME WORST" if (is_pb and is_pb_tie) else ("NEW ALL-TIME WORST" if is_pb else f"BOTTOM 10 WORST AVG ({ord_rank} Worst)")
                    cl = "event-title-score-min"
                    det_txt = f"Avg Score: {int(s):,} pts &middot; Ranked {ord_rank} lowest {w}-game average all-time"

                if days:
                    if days > 1:
                        if is_pb and not is_pb_tie:
                            det_txt += f" &middot; Best avg in all {days} games played" if is_top else f" &middot; Worst avg in all {days} games played"
                        else:
                            det_txt += f" &middot; Best avg in {days} games{ref_str}" if is_top else f" &middot; Worst avg in {days} games{ref_str}"
                    else:
                        det_txt += f" &middot; Best avg since yesterday" if is_top else f" &middot; Worst avg since yesterday"
                        
                ct = f"""<div class="event-title {cl}">{w}-GAME AVG: {cs} Score &middot; {tt}</div>
                         <div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span>
                         <span class="record-detail">{det_txt}</span></div>"""
            elif et == 'streak':
                p, cnt, sub = e['player'], e['count'], e['subtype']
                times = e.get('times_reached', 1)
                days = e.get('days_since_last')
                ref_date = e.get('last_reached_date')
                
                if sub == "new_record": 
                    txt = "NEW RECORD STREAK"
                    det = f"First time reaching <b>{cnt}</b> games"
                elif sub == "matched_record": 
                    txt = "MATCHED RECORD STREAK"
                    det = f"Matches record of <b>{cnt}</b> games"
                else: 
                    txt = "ACTIVE STREAK"
                    det = f"Reached <b>{cnt}</b> games"
                    
                if times > 1:
                    det += f" &middot; {get_ordinal(times)} time"
                    if days is not None:
                        ref_str = f" ({ref_date.strftime('%b %d, %Y').replace(' 0', ' ')})" if pd.notna(ref_date) else ""
                        if days > 1:
                            det += f" &middot; Last reached {days} games ago{ref_str}"
                        else:
                            det += f" &middot; Last reached yesterday{ref_str}"
                        
                ic, rc = "🔥", "row-streak"
                ct = f"""<div class="event-title event-title-streak">{cs} &middot; {txt}</div><div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="streak-highlight">&middot; {det}</span></div>"""
            elif et == 'streak_broken':
                p, b, cnt, sub = e['player'], e['breaker'], e['count'], e['subtype']
                ic, rc = "🛑", "row-broken"
                det = f"snaps {p}'s <b>{cnt}</b>-game win streak."
                if sub == 'denied_break': det += " One game short of a new record!"
                ct = f"""<div class="event-title event-title-broken">{cs} &middot; STREAK SNAPPED</div><div class="change-visual"><span class="player-name {pc(b)}">{b.upper() if b != 'Tie' else 'TIE'}</span><span class="broken-detail">{det}</span></div>"""
            elif et == 'score_streak':
                p, cnt, sub, lbl, stype = e['player'], e['count'], e['subtype'], e['threshold_label'], e['streak_type']
                times = e.get('times_reached', 1)
                days = e.get('days_since_last')
                ref_date = e.get('last_reached_date')
                
                ic, rc = ("🔥", "row-score-streak-hot") if stype == "hot" else ("❄️", "row-score-streak-cold")
                title_cl = "event-title-hot" if stype == "hot" else "event-title-cold"
                
                if sub == "new_record": 
                    txt = f"NEW RECORD {lbl.upper()} STREAK"
                    det = f"First time reaching <b>{cnt}</b> games"
                elif sub == "matched_record": 
                    txt = f"MATCHED RECORD {lbl.upper()} STREAK"
                    det = f"Matches record of <b>{cnt}</b> games"
                else: 
                    txt = f"ACTIVE {lbl.upper()} STREAK"
                    det = f"Reached <b>{cnt}</b> games"
                    
                if times > 1:
                    det += f" &middot; {get_ordinal(times)} time"
                    if days is not None:
                        ref_str = f" ({ref_date.strftime('%b %d, %Y').replace(' 0', ' ')})" if pd.notna(ref_date) else ""
                        if days > 1:
                            det += f" &middot; Last reached {days} games ago{ref_str}"
                        else:
                            det += f" &middot; Last reached yesterday{ref_str}"
                        
                ct = f"""<div class="event-title {title_cl}">{cs} &middot; {txt}</div><div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="streak-highlight">&middot; {det}</span></div>"""
            elif et == 'score_streak_broken':
                p, cnt, sub, lbl = e['player'], e['count'], e['subtype'], e['threshold_label']
                ic, rc = "🛑", "row-broken"
                det = f"snaps their <b>{cnt}</b>-game streak of {lbl}."
                if sub == 'denied_break': det += " One game short of a new record!"
                elif sub == 'denied_match': det += " One game short of matching record!"
                ct = f"""<div class="event-title event-title-broken">{cs} &middot; {lbl.upper()} STREAK SNAPPED</div><div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="broken-detail">{det}</span></div>"""
            elif et in ['margin_record_largest', 'margin_record_tightest']:
                p, m, r = e['player'], e['margin'], e['rank']
                is_pb = r == 1
                is_pb_tie = e.get('is_pb_tie', False)
                is_largest = et == 'margin_record_largest'
                
                ic = "📈" if is_largest else "🤏"
                rc = "row-record-max" if is_largest else "row-record-min"
                ord_rank = get_ordinal(r)
                days = e.get('days_since')
                ref_date = e.get('ref_date')
                ref_str = f" ({ref_date.strftime('%b %d, %Y').replace(' 0', ' ')})" if pd.notna(ref_date) else ""
                
                at_badge = ""
                if e.get('is_all_time_new'):
                    at_badge = '<span class="all-time-badge">ALL-TIME RECORD</span>'
                elif e.get('is_all_time_tie'):
                    at_badge = '<span class="all-time-badge" style="background-color:#7f8c8d;">TIED ALL-TIME RECORD</span>'
                
                if is_largest:
                    tt = "TIED RECORD WIN MARGIN" if (is_pb and is_pb_tie) else ("NEW RECORD WIN MARGIN" if is_pb else f"TOP 10 LARGEST WIN ({ord_rank})")
                    cl = "event-title-record-max"
                    det_txt = f"Margin: {int(m):,} pts &middot; Ranked {ord_rank} largest win all-time as of this date"
                    if days:
                        if days > 1:
                            if is_pb and not is_pb_tie: det_txt += f" &middot; Largest win in all {days} games played"
                            else: det_txt += f" &middot; Largest win in {days} games{ref_str}"
                        else:
                            det_txt += f" &middot; Largest win since yesterday"
                else:
                    tt = "TIED RECORD TIGHTEST WIN" if (is_pb and is_pb_tie) else ("NEW RECORD TIGHTEST WIN" if is_pb else f"TOP 10 TIGHTEST WIN ({ord_rank})")
                    cl = "event-title-record-min"
                    det_txt = f"Margin: {int(m):,} pts &middot; Ranked {ord_rank} tightest win all-time as of this date"
                    if days:
                        if days > 1:
                            if is_pb and not is_pb_tie: det_txt += f" &middot; Tightest win in all {days} games played"
                            else: det_txt += f" &middot; Tightest win in {days} games{ref_str}"
                        else:
                            det_txt += f" &middot; Tightest win since yesterday"
                
                ct = f"""<div class="event-title {cl}">{cs} &middot; {tt} {at_badge}</div>
                         <div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="record-detail">{det_txt}</span></div>"""
            elif et == 'score_top_10':
                p, s, r = e['player'], e['score'], e['rank']
                is_pb = r == 1
                is_pb_tie = e.get('is_pb_tie', False)
                ic = "👑" if is_pb else "🏅"
                rc = "row-score-max" if is_pb else "row-score-min"
                ord_rank = get_ordinal(r)
                days = e.get('days_since')
                ref_date = e.get('ref_date')
                ref_str = f" ({ref_date.strftime('%b %d, %Y').replace(' 0', ' ')})" if pd.notna(ref_date) else ""
                
                tt = "TIED ALL-TIME RECORD" if (is_pb and is_pb_tie) else ("NEW ALL-TIME RECORD" if is_pb else f"TOP 10 PERFORMANCE ({ord_rank})")
                cl = "event-title-score-max" if is_pb else "event-title-score-min"
                
                det_txt = f"Score: {int(s):,} pts &middot; Ranked {ord_rank} highest all-time as of this date"
                if days:
                    if days > 1:
                        if is_pb and not is_pb_tie:
                            det_txt += f" &middot; Best score in all {days} games played"
                        else:
                            det_txt += f" &middot; Best score in {days} games{ref_str}"
                    else:
                        det_txt += f" &middot; Best score since yesterday"
                        
                ct = f"""<div class="event-title {cl}">{cs} &middot; {tt}</div>
                         <div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span>
                         <span class="record-detail">{det_txt}</span></div>"""
            elif et == 'score_bottom_10':
                p, s, r = e['player'], e['score'], e['rank']
                is_worst = r == 1
                is_worst_tie = e.get('is_worst_tie', False)
                ic = "📉" if is_worst else "⚠️"
                rc = "row-score-min"
                ord_rank = get_ordinal(r)
                days = e.get('days_since')
                ref_date = e.get('ref_date')
                ref_str = f" ({ref_date.strftime('%b %d, %Y').replace(' 0', ' ')})" if pd.notna(ref_date) else ""
                
                tt = "TIED ALL-TIME WORST" if (is_worst and is_worst_tie) else ("NEW ALL-TIME WORST" if is_worst else f"BOTTOM 10 PERFORMANCE ({ord_rank} Worst)")
                cl = "event-title-score-min"
                
                det_txt = f"Score: {int(s):,} pts &middot; Ranked {ord_rank} lowest all-time as of this date"
                if days:
                    if days > 1:
                        if is_worst and not is_worst_tie:
                            det_txt += f" &middot; Worst score in all {days} games played"
                        else:
                            det_txt += f" &middot; Worst score in {days} games{ref_str}"
                    else:
                        det_txt += f" &middot; Worst score since yesterday"
                        
                ct = f"""<div class="event-title {cl}">{cs} &middot; {tt}</div>
                         <div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span>
                         <span class="record-detail">{det_txt}</span></div>"""
            elif et == 'score_vs_opp':
                p, sub, s = e['player'], e['subtype'], e['score']
                opp, opp_rec = e['opponent'], e['opp_record']
                days = e.get('days_since')
                ref_date = e.get('ref_date')
                ref_str = f" ({ref_date.strftime('%b %d, %Y').replace(' 0', ' ')})" if pd.notna(ref_date) else ""
                
                ic, rc = "⚔️", "row-score-beat-opp"
                tt, cl = ("BEAT OPPONENT'S PB", "event-title-score-beat") if sub == "surpass_opp_max" else ("LOWER THAN OPPONENT'S WORST", "event-title-score-beat")
                det_txt = f"Score: {int(s):,} pts (Surpassed {opp}'s best of {int(opp_rec):,})" if sub == "surpass_opp_max" else f"Score: {int(s):,} pts (Lower than {opp}'s worst of {int(opp_rec):,})"
                
                if days:
                    if days > 1:
                        if sub == "surpass_opp_max":
                            det_txt += f" &middot; Best score in {days} games{ref_str}"
                        else:
                            det_txt += f" &middot; Worst score in {days} games{ref_str}"
                    else:
                        if sub == "surpass_opp_max":
                            det_txt += f" &middot; Best score since yesterday"
                        else:
                            det_txt += f" &middot; Worst score since yesterday"
                
                ct = f"""<div class="event-title {cl}">{cs} &middot; {tt}</div><div class="change-visual"><span class="player-name {pc(p)}">{p.upper()}</span><span class="record-detail">{det_txt}</span></div>"""
            elif et == 'discovery':
                n, sub = e['name'], e['subtype']
                
                if sub in ["new_country", "new_subdivision", "new_un_region", "new_continent"]:
                    txt = "NEW COUNTRY" if sub == "new_country" else ("NEW SUBDIVISION" if sub == "new_subdivision" else ("NEW UN REGION" if sub == "new_un_region" else "NEW CONTINENT"))
                    
                    if sub == "new_country": ic = get_flag_html(n)
                    elif sub == "new_subdivision": ic = f"{get_flag_html(e.get('country', ''))} 📍"
                    elif sub == "new_un_region": ic = "🌐"
                    else: ic = "🌏"
                    
                    stats, lbls = e.get('perf', {}), {"Total": ("🏆", "Total"), "Geography": ("🌍", "Geo"), "Time": ("⏱️", "Time")}
                    
                    sh = ""
                    for m in ["Total", "Geography", "Time"]:
                        w_name, w_margin = stats.get(m, ("Tie", 0))
                        margin_str = f" (+{int(w_margin):,})" if w_name != "Tie" and w_margin > 0 else ""
                        w_disp = "TIE" if w_name == "Tie" else w_name[0].upper()
                        sh += f'<div class="stat-chip cat-{m.lower()} winner-{w_name.lower()}"><span class="stat-icon">{lbls[m][0]}</span> <div class="stat-content"><span class="stat-type">{lbls[m][1]}</span><span class="stat-winner {pc(w_name)}">{w_disp}{margin_str}</span></div></div>'
                        
                    det_txt = f'<span class="discovery-subtext">in {e.get("country", "")}</span>' if sub == "new_subdivision" else ""
                    ct = f"""<div class="event-title event-title-discovery">{txt}</div><div class="change-visual"><span class="discovery-highlight">{n}</span>{det_txt}</div><div class="discovery-stats-box">{sh}</div>"""
                    rc = "row-discovery"
            elif et == 'year_discovery':
                n, stt = e['name'], e['perf']
                txt, ic, rc = "NEW YEAR", "📅", "row-discovery"
                
                lbls = {"Total": ("🏆", "Total"), "Geography": ("🌍", "Geo"), "Time": ("⏱️", "Time")}
                sh = ""
                for m in ["Total", "Geography", "Time"]:
                    w_name, w_margin = stt.get(m, ("Tie", 0))
                    margin_str = f" (+{int(w_margin):,})" if w_name != "Tie" and w_margin > 0 else ""
                    w_disp = "TIE" if w_name == "Tie" else w_name[0].upper()
                    sh += f'<div class="stat-chip cat-{m.lower()} winner-{w_name.lower()}"><span class="stat-icon">{lbls[m][0]}</span> <div class="stat-content"><span class="stat-type">{lbls[m][1]}</span><span class="stat-winner {pc(w_name)}">{w_disp}{margin_str}</span></div></div>'
                    
                ct = f"""<div class="event-title event-title-discovery">{txt}</div><div class="change-visual"><span class="discovery-highlight">{n}</span></div><div class="discovery-stats-box">{sh}</div>"""
            elif et == 'decade_discovery':
                n, stt = e['name'], e['perf']
                txt, ic, rc = "NEW DECADE", "🗓️", "row-discovery"
                
                lbls = {"Total": ("🏆", "Total"), "Geography": ("🌍", "Geo"), "Time": ("⏱️", "Time")}
                sh = ""
                for m in ["Total", "Geography", "Time"]:
                    w_name, w_margin = stt.get(m, ("Tie", 0))
                    margin_str = f" (+{int(w_margin):,})" if w_name != "Tie" and w_margin > 0 else ""
                    w_disp = "TIE" if w_name == "Tie" else w_name[0].upper()
                    sh += f'<div class="stat-chip cat-{m.lower()} winner-{w_name.lower()}"><span class="stat-icon">{lbls[m][0]}</span> <div class="stat-content"><span class="stat-type">{lbls[m][1]}</span><span class="stat-winner {pc(w_name)}">{w_disp}{margin_str}</span></div></div>'
                    
                ct = f"""<div class="event-title event-title-discovery">{txt}</div><div class="change-visual"><span class="discovery-highlight">{n}</span></div><div class="discovery-stats-box">{sh}</div>"""
            elif et in ['rare_location', 'rare_year', 'rare_decade']:
                sub, n, gap = e['subtype'], e['name'], e['gap']
                app_count = e.get('appearances', 0)
                app_badge = f'<span style="font-size:12px; color:#888; font-weight:600; margin-left:10px; vertical-align:middle; background:#f0f0f0; padding:2px 6px; border-radius:4px;">Appearance #{app_count}</span>' if app_count > 1 else ""
                
                if sub == "country":
                    ic = get_flag_html(n)
                    lt = "COUNTRY"
                    det_txt = ""
                elif sub == "subdivision":
                    ic = f"{get_flag_html(e.get('country', ''))} 📍"
                    lt = "SUBDIVISION"
                    det_txt = f'<span class="discovery-subtext">in {e.get("country", "")}</span>'
                elif sub == "region":
                    ic = "🌐"
                    lt = "REGION"
                    det_txt = ""
                elif sub == "continent":
                    ic = "🌏"
                    lt = "CONTINENT"
                    det_txt = ""
                elif sub == "year":
                    ic = "📅"
                    lt = "YEAR"
                    det_txt = ""
                elif sub == "decade":
                    ic = "🗓️"
                    lt = "DECADE"
                    det_txt = ""

                rc = "row-discovery"
                tt = f"RARE {lt} APPEARANCE"
                rare_msg = f"Rare {sub} today! First time in {gap} games."
                
                overall_perf = e.get('overall_perf', {})
                metrics = ["Total", "Geography", "Time"]
                
                sh = ""
                if overall_perf:
                    for m in metrics:
                        mb = overall_perf[m]["Michael"]["before"]
                        ma = overall_perf[m]["Michael"]["after"]
                        sb = overall_perf[m]["Sarah"]["before"]
                        sa = overall_perf[m]["Sarah"]["after"]
                        
                        after_diff = ma - sa
                        w_after = "Michael" if after_diff > 0 else ("Sarah" if after_diff < 0 else "Tie")
                        m_after = abs(after_diff)
                        
                        before_diff = mb - sb
                        w_before = "Michael" if before_diff > 0 else ("Sarah" if before_diff < 0 else "Tie")
                        m_before = abs(before_diff)
                        
                        if w_before == "Tie": was_str = "Tie"
                        elif w_before == w_after: was_str = f"+{int(m_before):,}"
                        else: was_str = f"{w_before[0]} +{int(m_before):,}"
                        
                        if w_after == "Tie": main_str = "TIE"
                        else: main_str = f"{w_after[0].upper()} (+{int(m_after):,})"
                        
                        lbl = {"Total": ("🏆", "Total"), "Geography": ("🌍", "Geo"), "Time": ("⏱️", "Time")}[m]
                        
                        sh += f'<div class="stat-chip cat-{m.lower()} winner-{w_after.lower()}"><span class="stat-icon">{lbl[0]}</span> <div class="stat-content"><span class="stat-type">OVERALL {lbl[1]} MARGIN</span><span class="stat-winner {pc(w_after)}">{main_str} <span style="font-size:10px; color:#888; font-weight:600; text-transform:none; margin-left:3px;">(was {was_str})</span></span></div></div>'
                    sh = f'<div class="discovery-stats-box">{sh}</div>'
                
                ct = f"""<div class="event-title event-title-discovery">{cs} &middot; {tt}</div>
                         <div class="change-visual"><span class="discovery-highlight">{n}</span>{det_txt}{app_badge}</div>
                         {sh}
                         <div class="record-detail" style="color:#00838f; font-weight:600; margin-top:6px;">{rare_msg}</div>"""
            elif et in ['location_flip', 'year_flip', 'decade_flip']:
                sub, n = e.get('subtype', ''), e['name']
                app_count = e.get('appearances', 0)
                app_badge = f'<span style="font-size:12px; color:#888; font-weight:600; margin-left:10px; vertical-align:middle; background:#f0f0f0; padding:2px 6px; border-radius:4px;">Appearance #{app_count}</span>' if app_count > 1 else ""
                
                if et == 'location_flip':
                    if sub == "country":
                        ic = get_flag_html(n)
                        lt = "COUNTRY"
                        det_txt = ""
                    elif sub == "subdivision":
                        ic = f"{get_flag_html(e.get('country', ''))} 📍"
                        lt = "SUBDIVISION"
                        det_txt = f'<span class="discovery-subtext">in {e.get("country", "")}</span>'
                    elif sub == "region":
                        ic = "🌐"
                        lt = "REGION"
                        det_txt = ""
                    elif sub == "continent":
                        ic = "🌏"
                        lt = "CONTINENT"
                        det_txt = ""
                    else:
                        ic = "📍"
                        lt = "LOCATION"
                        det_txt = ""
                elif et == 'year_flip':
                    ic = "📅"
                    lt = "YEAR"
                    det_txt = ""
                elif et == 'decade_flip':
                    ic = "🗓️"
                    lt = "DECADE"
                    det_txt = ""

                rc = "row-capture"
                is_rare = e.get('is_rare', False)
                gap = e.get('gap', 0)
                
                tt = f"RARE {lt} FLIP" if is_rare else f"CONTROL FLIP: {lt}"
                rare_msg = f"Rare {sub} today! First time in {gap} games." if is_rare else ""
                rare_html = f'<div class="record-detail" style="color:#00838f; font-weight:600; margin-top:6px;">{rare_msg}</div>' if is_rare else ""
                
                overall_perf = e.get('overall_perf', {})
                metrics = ["Total", "Geography", "Time"]
                
                sh = ""
                if overall_perf:
                    for m in metrics:
                        perf = overall_perf.get(m)
                        if not perf: continue
                        
                        mb = perf["Michael"]["before"]
                        ma = perf["Michael"]["after"]
                        sb = perf["Sarah"]["before"]
                        sa = perf["Sarah"]["after"]
                        
                        old_w = perf["old_leader"]
                        new_w = perf["new_leader"]
                        did_flip = perf["did_flip"]
                        
                        after_diff = ma - sa
                        m_after = abs(after_diff)
                        
                        before_diff = mb - sb
                        m_before = abs(before_diff)
                        
                        if old_w == "Tie": was_str = "Tie"
                        elif old_w == new_w: was_str = f"+{int(m_before):,}"
                        else: was_str = f"{old_w[0]} +{int(m_before):,}"
                        
                        if new_w == "Tie": main_str = "TIE"
                        else: main_str = f"{new_w[0].upper()} (+{int(m_after):,})"
                        
                        lbl = {"Total": ("🏆", "Total"), "Geography": ("🌍", "Geo"), "Time": ("⏱️", "Time")}[m]
                        
                        dir_str = ""
                        if did_flip:
                            bg_col = "#221e8f" if new_w == "Michael" else ("#8a005c" if new_w == "Sarah" else "#999")
                            old_char = old_w[0].upper() if old_w != 'Tie' else 'TIE'
                            new_char = new_w[0].upper() if new_w != 'Tie' else 'TIE'
                            dir_str = f"<span style='background:{bg_col}; color:white; font-size:9px; padding:2px 4px; border-radius:3px; margin-left:4px; font-weight:800;'>{old_char}➔{new_char}</span>"
                            
                        sh += f'<div class="stat-chip cat-{m.lower()} winner-{new_w.lower()}"><span class="stat-icon">{lbl[0]}</span> <div class="stat-content"><span class="stat-type">OVERALL {lbl[1]} MARGIN</span><span class="stat-winner {pc(new_w)}">{main_str} <span style="font-size:10px; color:#888; font-weight:600; text-transform:none; margin-left:3px; margin-right:2px;">(was {was_str})</span>{dir_str}</span></div></div>'
                    sh = f'<div class="discovery-stats-box">{sh}</div>'
                
                ct = f"""<div class="event-title event-title-capture">{cs} &middot; {tt}</div>
                         <div class="change-visual"><span class="discovery-highlight">{n}</span>{det_txt}{app_badge}</div>
                         {sh}
                         {rare_html}"""
            elif et == 'milestone':
                sub, n, cnt = e['subtype'], e['name'], e['count']
                ic, rc = "🎉", "row-milestone"
                lbl = f"{n.upper()}" if sub in ["continent", "region", "country", "subdivision"] else (f"{n} DECADE" if sub == "decade" else (f"{n} YEAR" if sub == "year" else "TOTAL GAMES"))
                det = f"{cnt} Games in {n}" if sub != "total" else f"{cnt} Games Played"
                
                breakdown_html = ""
                if sub in ["decade", "continent", "region", "country", "subdivision"] and 'top_subitems' in e:
                    parts = [f"{item} ({count})" for item, count in e['top_subitems']]
                    if e.get('other_count', 0) > 0:
                        parts.append(f"Other ({e['other_count']})")
                    if parts:
                        top_lbl = e.get('subitems_label', 'Top')
                        breakdown_html = f"<div style='margin-top: 8px; font-size: 12px; color: #6a1b9a; background-color: #f3e5f5; padding: 4px 8px; border-radius: 4px; display: inline-block; font-weight: 500; border: 1px solid #e1bee7;'><b>{top_lbl}:</b> {' &middot; '.join(parts)}</div>"
                        
                ct = f"""<div class="event-title event-title-milestone">MILESTONE REACHED</div><div class="change-visual"><span class="discovery-highlight">{lbl}</span><span class="record-detail">{det}</span>{breakdown_html}</div>"""
            
            rh += f"""<div class="event-row {rc}"><div class="category-box"><div class="cat-icon">{ic}</div><div class="cat-name">{cs}</div></div><div class="content-box">{ct}</div></div>"""
            
        rh += '</div>'
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
    all_evs.extend(generate_momentum_score_events(df_t, "Total Score", 5))
    all_evs.extend(generate_momentum_score_events(df_t, "Total Score", 10))
    all_evs.extend(generate_momentum_score_events(df_tm, "Time Score", 5))
    all_evs.extend(generate_momentum_score_events(df_tm, "Time Score", 10))
    all_evs.extend(generate_momentum_score_events(df_g, "Geography Score", 5))
    all_evs.extend(generate_momentum_score_events(df_g, "Geography Score", 10))
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
        sf = st.multiselect("Filter Categories:", options=list(FEED_CATEGORIES.keys()), default=list(FEED_CATEGORIES.keys()))

    st.markdown('<div id="top"></div>', unsafe_allow_html=True)
    st.markdown("""<div class="page-header"><h1 class="page-title">The Daily Guessr</h1><div class="page-subtitle">Tracking Momentum & Leaderboard Shifts</div></div>""", unsafe_allow_html=True)
    st.markdown(render_forecast_section([get_full_category_forecast(df_t, "Total Score"), get_full_category_forecast(df_tm, "Time Score"), get_full_category_forecast(df_g, "Geography Score")]), unsafe_allow_html=True)
    st.markdown('<a href="#top" class="back-to-top">↑</a>', unsafe_allow_html=True)
    
    # Collect requested event types based on sidebar selection
    active_types = set()
    for cat_name in sf:
        active_types.update(FEED_CATEGORIES[cat_name])

    # Filter events and group by date
    fe = [e for e in all_evs if e.get('event_type') in active_types]
    ev_d = {}
    for e in fe:
        d = e['date']
        if d not in ev_d: ev_d[d] = []
        ev_d[d].append(e)
        
    sd = sorted(ev_d.keys(), reverse=True)
    
    if not sd: 
        st.markdown('<div class="news-container"><div style="text-align:center; padding:50px; color:#666; font-size: 18px;">No news events detected matching your filters.</div></div>', unsafe_allow_html=True)
    else:
        feed_html = '<div class="news-container">\n'
        for d in sd:
            feed_html += render_daily_news(d, ev_d[d]) + '\n'
        feed_html += '</div>'
        st.markdown(feed_html, unsafe_allow_html=True)

else: st.warning("Please ensure 'Timeguessr_Stats.csv' is in the 'Data' folder.")