import os
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import datetime
import json
import re
import country_converter as coco
from streamlit.components.v1 import html as components_html

# --- Configuration ---
st.set_page_config(page_title="The Daily Guessr", layout="wide")
from background import set_random_sarah_background
# True only on the run where the user just navigated onto this page (not on
# reruns triggered by interacting with a widget already on it) — used below
# to snap the Edition Date back to today every time the page is (re)entered.
just_entered_daily_page = set_random_sarah_background(__file__, lightness_level=0.7)

# Global Initialization to drastically improve load speeds. CountryConverter()
# parses a large name/alias lookup table on construction (tens of ms); cached
# as a resource so that cost is paid once per session instead of on every
# single rerun (every widget interaction reruns this whole script).
@st.cache_resource
def _get_country_converter():
    return coco.CountryConverter()

cc_obj = _get_country_converter()

# --- Load External CSS ---
from utils import load_css
load_css()

# --- Score Submission setup (merged from the old Score Submission page) ---
try:
    from Score_Update import score_update
except ImportError:
    def score_update(): pass

try:
    from aggregation import update_averages_csv_entry, update_community_averages_csv_entry
except ImportError:
    def update_averages_csv_entry(*args, **kwargs): pass
    def update_community_averages_csv_entry(*args, **kwargs): pass

try:
    with open("config.json", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

score_update()

# --- Internal Styling ---
NEWS_STYLES = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@500;600;700;800;900&display=swap');
        
        html { scroll-behavior: smooth; }
        .news-container { width: 100%; margin: 0 auto; padding: 40px 20px; box-sizing: border-box; }
        
        .back-to-top { position: fixed; bottom: 30px; right: 30px; background-color: #333; color: white !important; width: 50px; height: 50px; border-radius: 25px; display: flex; align-items: center; justify-content: center; text-decoration: none !important; font-size: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 1000; transition: transform 0.2s, background-color 0.2s; }
        .back-to-top:hover { transform: scale(1.1); background-color: #000; color: white !important; }

        .page-title { font-family: 'Poppins', sans-serif; font-weight: 900; font-size: 48px; color: #111; letter-spacing: -1px; margin: 0; text-transform: uppercase; text-align: center; }
        
        /* FORECAST SECTION — flat colour-tinted cards, no shadow/border/internal
           dividers, matching the Michael / Sarah / Community / Actuals boxes
           above (plain pastel background per card, no white sub-sections). */
        .forecast-container { width: 100%; margin: 0 auto 60px auto; box-sizing: border-box; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; }
        .forecast-card { border-radius: 12px; padding: 0; overflow: hidden; display: flex; flex-direction: column; }
        .fc-header { padding: 16px 20px 8px 20px; display: flex; align-items: center; gap: 10px; }
        .fc-icon { font-size: 20px; }
        .fc-title { font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 16px; text-transform: uppercase; letter-spacing: 0.5px; }

        /* Per-round M/S/C bars, embedded inside a forecast card */
        .hbar-group { padding: 8px 20px; }
        .hbar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
        .hbar-row:last-child { margin-bottom: 0; }
        .hbar-lbl { width: 16px; flex-shrink: 0; font-weight: 700; font-size: 0.8rem; text-align: center; }
        .hbar-track { flex: 1; min-width: 0; height: 16px; background-color: #b0afaa; border-radius: 5px; overflow: hidden; display: flex; flex-direction: row; }
        .bar-section-title { font-size: 10px; font-weight: 700; color: #767676; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
        .pct-bar-track { flex: 1; min-width: 0; height: 16px; background-color: #000; border-radius: 5px; overflow: hidden; }
        .pct-bar-fill { height: 100%; }

        .fc-momentum-grid { display: grid; grid-template-columns: 1fr 1fr; padding: 6px 8px 0 8px; }
        .fc-mom-box { padding: 9px 12px; text-align: center; }
        .fc-mom-label { font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 700; color: #767676; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
        .fc-mom-leader { font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 14px; margin-bottom: 4px; }
        .fc-mom-detail { font-family: 'Inter', sans-serif; font-size: 11px; color: #555; line-height: 1.3; }

        .fc-streaks { padding: 10px 20px 16px 20px; flex-grow: 1; }
        .fc-streaks-title { font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 700; color: #666; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 0.5px; }
        .fc-streak-item { display: flex; align-items: center; justify-content: space-between; font-family: 'Inter', sans-serif; font-size: 12px; margin-bottom: 6px; padding-bottom: 6px; border-bottom: 1px dashed rgba(0,0,0,0.12); }
        .fc-streak-item:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
        .fc-streak-name { font-weight: 600; color: #333; }
        .fc-streak-val { font-weight: 700; color: #000; }
        .fc-streak-meta { font-size: 10px; color: #767676; }

        .target-hl { background-color: rgba(255,255,255,0.65); padding: 0 3px; border-radius: 2px; font-weight: 600; color: #333; }
        .fc-cat-total { background-color: #f7f0d9; }
        .fc-cat-total .fc-title { color: #a5760a; }
        .fc-cat-time { background-color: #ece2f4; }
        .fc-cat-time .fc-title { color: #8e44ad; }
        .fc-cat-geo { background-color: #dcefdf; }
        .fc-cat-geo .fc-title { color: #1f8a4c; }
        
        /* DAILY FEED / CATEGORY CARDS */
        .daily-card { background: #fff; border: 1px solid #ddd; border-top: 4px solid #333; border-radius: 8px; margin-bottom: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); scroll-margin-top: 50px; overflow: hidden; }
        .daily-header { background-color: #fcfcfc; padding: 16px 24px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .daily-header-end { justify-content: flex-end; }
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
        .p-community { color: #6c757d; }
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
        
        /* ROUND-BY-ROUND TABLE (top of each edition): rounds = rows, dimensions = columns */
        .round-strip { padding: 20px 24px; background: #ffffff; border-bottom: 1px solid #eee; }
        .round-strip-title { font-family: 'Poppins', sans-serif; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #555; margin-bottom: 14px; }
        .rss-sub { font-weight: 500; text-transform: none; letter-spacing: 0; color: #999; font-size: 11px; margin-left: 8px; }
        .round-table-wrap { overflow-x: auto; border: 1px solid #e8e8e8; border-radius: 8px; }
        .round-table { width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; }
        .round-table th { background: #f4f4f6; font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; color: #999; padding: 10px 12px; text-align: left; border-bottom: 1px solid #e5e5e5; white-space: nowrap; }
        .round-table td { padding: 8px 9px; border-bottom: 1px solid #f0f0f0; border-left: 1px solid #f4f4f4; vertical-align: top; font-size: 10px; }
        .round-table td:first-child, .round-table th:first-child { border-left: none; }
        .round-table tr:last-child td { border-bottom: none; }
        .round-table tbody tr.alt td { background: #fbfbfb; }
        .round-table tbody tr.rt-hdrrow:not(:first-child) td { border-top: 2px solid #e2e2e2; }
        .rt-round { min-width: 190px; }
        .rt-cell { min-width: 104px; }
        /* per-round dimension header row (value + appearance count + Rare/New) */
        .round-table td.rt-dimhdr { border-bottom: 2px solid #e6e6e6; padding-bottom: 6px; }
        .rt-dh-val { display: block; font-size: 11px; font-weight: 800; color: #222; line-height: 1.15; margin-bottom: 3px; }
        .rt-appc { display: block; font-size: 8px; font-weight: 700; color: #9a9a9a; text-transform: uppercase; letter-spacing: 0.3px; }
        .rt-gap { display: block; font-size: 8px; font-weight: 700; color: #c47a1e; margin-top: 2px; }
        .rt-type-hdr { color: #bbb; font-size: 8px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.4px; }
        /* score-type sub-row column */
        .rt-type { min-width: 82px; }
        .rt-type-lbl { display: block; font-weight: 800; font-size: 10px; text-transform: uppercase; letter-spacing: 0.4px; color: #555; }
        .rt-type-swing { display: block; font-size: 9px; font-weight: 700; margin-top: 3px; color: #999; }
        .rt-type-total .rt-type-lbl { color: #444; }
        .rt-type-geo   .rt-type-lbl { color: #1b6b86; }
        .rt-type-time  .rt-type-lbl { color: #7a4f9e; }
        .round-table td.rt-type-geo  { box-shadow: inset 3px 0 0 #bcdbe5; }
        .round-table td.rt-type-time { box-shadow: inset 3px 0 0 #ddccea; }
        .rt-loc { display: block; font-size: 15px; font-weight: 600; color: #444; line-height: 1.3; margin: 0 0 4px; }
        .rt-loc img { width: 17px !important; height: auto; vertical-align: -2px; margin-right: 4px; }
        .rt-score-line { display: block; font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 11px; color: #333; white-space: nowrap; line-height: 1.6; }
        .rt-score-lbl { display: inline-block; width: 34px; color: #999; font-weight: 800; }
        .rt-extra { margin-top: 10px; padding-top: 8px; border-top: 1px dashed #e0e0e0; }
        /* value-level (New / Rare) markers, shown in the round's dimension header row */
        .rt-mk { display: inline-block; font-size: 8px; font-weight: 800; padding: 1px 5px; border-radius: 3px; color: #fff; margin: 3px 4px 0 0; text-transform: uppercase; letter-spacing: 0.4px; }
        .rt-mk-new  { background: #5db300; }
        .rt-mk-rare { background: #e8952e; }
        .rb-dash { color: #bbb; margin: 0 3px; }
        .rb-score-na { color: #aaa; font-weight: 500; font-style: italic; }
        .rb-approx { color: #b0a89e; font-weight: 700; margin-right: 1px; }
        .rt-state { display: block; font-size: 11px; font-weight: 700; color: #444; line-height: 1.4; }
        /* NEW / FLIP / RARE: prominent badge + whole-cell highlight (tint priority: new > flip > rare) */
        .round-table td.rt-cell-new  { background: #edf8db !important; box-shadow: inset 4px 0 0 #5db300; }
        .round-table td.rt-cell-flip { background: #fde3df !important; box-shadow: inset 4px 0 0 #c0392b; }
        .round-table td.rt-cell-rare { background: #fdf1de !important; box-shadow: inset 4px 0 0 #e8952e; }
        .rb-tag { display: inline-block; font-size: 9px; font-weight: 800; padding: 2px 6px; border-radius: 4px; margin: 5px 4px 0 0; letter-spacing: 0.6px; text-transform: uppercase; color: #fff; }
        .rb-tag-flip { background: #c0392b; box-shadow: 0 1px 3px rgba(192,57,43,0.4); }
        /* Missed flip: hollow "flip that didn't happen" — no cell tint, badge only */
        .rb-tag-missed { background: #fff; color: #c0392b; border: 1px dashed #c0392b; }
        .rt-dir { display: inline-block; font-size: 9px; font-weight: 800; padding: 2px 5px; border-radius: 3px; margin: 5px 0 0 0; letter-spacing: 0.5px; color: #fff; }
        .rt-dir-m { background: #221e8f; }
        .rt-dir-s { background: #8a005c; }
        .rt-dir-t { background: #999; }
        .rt-dir-missed { background: transparent; color: #b0453a; border: 1px dashed #cf9b95; }
        .rt-cell-new .rt-dh-val, .rt-cell-rare .rt-dh-val { color: #111; }
        .rb-swing { font-weight: 700; }
        .rb-was { display: block; font-size: 9px; color: #8a8a8a; font-weight: 600; font-style: italic; margin-top: 1px; }
        .rb-na { color: #ccc; }

        /* EDITION DATE SELECTOR: doubles as the page title. The real date_input
           is kept for click/keyboard behavior but made invisible; a prominent
           overlay (".page-title"-styled) showing the formatted date sits on
           top of it (clicking the text opens the native calendar).
           The overlay stays in normal flow (its text sizes the box); the
           invisible date input is absolutely positioned to exactly cover
           that box. This intentionally avoids CSS Grid's "1fr / 1/1" stacking
           trick — grid tracks auto-sized against percentage-width children
           are handled inconsistently enough across browser engines that it
           could size the real (invisible) input down to zero width on some
           machines, leaving nothing there to actually click. Plain absolute
           positioning against an explicit position:relative ancestor has no
           such ambiguity.
           The absolute positioning is applied to Streamlit's own element
           container (".st-key-edition_date_input", auto-named from the
           widget's key) rather than the "stDateInput" div nested inside it —
           that wrapper is itself "position: relative" by default, so it (not
           our outer stack) would otherwise become the real containing block;
           and since it's an empty shell with no in-flow content of its own
           once its only child is pulled out via position:absolute, it
           collapses to 0 height, taking our "top:0; bottom:0" stretch down
           to 0 with it. */
        .st-key-edition_date_stack {
            position: relative;
            width: max-content;
            max-width: 95%;
            margin: 0 auto 8px auto;
            padding-bottom: 10px;
            border-bottom: 4px double #ccc;
        }
        .st-key-edition_date_stack .st-key-edition_date_input {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 2;
        }
        .st-key-edition_date_stack div[data-testid="stDateInput"] {
            height: 100%;
            width: 100%;
            display: flex;
            align-items: center;
        }
        .st-key-edition_date_stack div[data-testid="stDateInput"] > label {
            display: none;
        }
        .st-key-edition_date_stack div[data-testid="stDateInput"] > div {
            height: 100%;
            width: 100%;
        }
        .st-key-edition_date_stack div[data-testid="stDateInput"] > div,
        .st-key-edition_date_stack div[data-baseweb="input"],
        .st-key-edition_date_stack div[data-baseweb="base-input"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            min-height: auto !important;
        }
        .st-key-edition_date_stack div[data-baseweb="input"],
        .st-key-edition_date_stack div[data-baseweb="base-input"] {
            display: flex !important;
            align-items: center !important;
            height: 100% !important;
            width: 100% !important;
        }
        .st-key-edition_date_stack input[data-testid="stDateInputField"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 0 !important;
            width: 100%;
            height: 100%;
            color: transparent !important;
            caret-color: transparent !important;
            cursor: pointer !important;
            text-align: center;
        }
        .st-key-edition_date_stack .edition-date-overlay {
            z-index: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            pointer-events: none;
            user-select: none;
            transition: color 0.15s;
        }
        .st-key-edition_date_stack:hover .edition-date-overlay {
            color: #b23931;
        }

        @media (max-width: 900px) {
            .forecast-container { grid-template-columns: 1fr; }
            .events-list { column-count: 1; padding: 16px; }
        }
    </style>
"""
st.markdown(NEWS_STYLES, unsafe_allow_html=True)

# --- Score Submission styles (merged from the old Score Submission page) ---
SUBMISSION_STYLES = """
    <style>
        /* Compact Toggles */
        .stToggle {
            margin-top: 0px !important;
        }

        /* Force color and alignment on Toggle Labels */
        div[data-testid="stToggle"] p,
        div[data-testid="stToggle"] label p,
        div[data-testid="stWidgetLabel"] p {
            font-size: 14px !important;
            font-weight: 400 !important;
            color: #db5049 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Responsive Score Box */
        .score-box {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 39px;
            padding: 0 10px;
            margin-top: 0px;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 600;
            box-sizing: border-box;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Section titles (Michael / Sarah / Community / Actuals) */
        .section-title {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 26px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            text-align: center;
            margin: 0;
        }

    </style>
"""
st.markdown(SUBMISSION_STYLES, unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data
def load_data(filepath: str = "./Data/Timeguessr_Stats.csv", mtime: float = 0, require_both: bool = True) -> pd.DataFrame:
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

        if require_both:
            # Used for historical momentum/streak/record tracking, which is only
            # meaningful for days both players actually completed.
            m_dates = data[data['Michael Total Score'].notna()]['Date'].dt.date.unique()
            s_dates = data[data['Sarah Total Score'].notna()]['Date'].dt.date.unique()
            shared = set(m_dates).intersection(set(s_dates))
            data = data[data['Date'].dt.date.isin(shared)].copy()

        if "Year" in data.columns:
            data["Year"] = pd.to_numeric(data["Year"], errors='coerce')

        return data
    except Exception as e:
        st.error(f"Error loading data: {e}"); return pd.DataFrame()

# --- Actuals helpers (merged from the old Score Submission page) ---
COUNTRY_ALIASES = {
    "Russia": "Russian Federation", "Ivory Coast": "Côte d'Ivoire",
    "South Korea": "Korea, Republic of", "North Korea": "Korea, Democratic People's Republic of",
    "Vietnam": "Viet Nam", "Syria": "Syrian Arab Republic",
    "Laos": "Lao People's Democratic Republic", "Bolivia": "Bolivia, Plurinational State of",
    "Venezuela": "Venezuela, Bolivarian Republic of", "Iran": "Iran, Islamic Republic of",
    "Moldova": "Moldova, Republic of", "Tanzania": "Tanzania, United Republic of",
    "Palestine": "Palestine, State of", "Brunei": "Brunei Darussalam",
    "Congo": "Congo, Republic of the", "Democratic Republic of the Congo": "Congo, The Democratic Republic of the",
    "Macau": "Macao", "Taiwan": "Taiwan, Province of China",
    "Cape Verde": "Cabo Verde", "Vatican City": "Holy See (Vatican City State)",
    "Turkey": "Türkiye", "Bosnia": "Bosnia and Herzegovina",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
}

def get_flag_emoji(country_name):
    import pycountry
    fallback = '<img src="https://twemoji.maxcdn.com/v/latest/svg/1f1fa-1f1f3.svg" width="20" style="vertical-align:middle;"/>'
    if not country_name or pd.isna(country_name): return fallback
    name_str = COUNTRY_ALIASES.get(country_name.strip(), country_name.strip())
    try:
        country = pycountry.countries.lookup(name_str)
        code = country.alpha_2.upper()
        codepoints = "-".join([f"1f1{format(ord(c) - ord('A') + 0xE6, 'x')}" for c in code])
        return f'<img src="https://twemoji.maxcdn.com/v/latest/svg/{codepoints}.svg" width="20" style="vertical-align:middle;"/>'
    except LookupError: return fallback

@st.cache_data
def load_map_subdivisions(mtime):
    _ = mtime  # cache-busting key only
    path = "./Data/Custom_World_Map_New.json"
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        gj = json.load(f)
    iso_to_names = {}
    for feature in gj.get('features', []):
        props = feature.get('properties', {})
        iso3 = str(props.get('ISO3', '')).strip()
        name = str(props.get('NAME', '')).strip()
        if iso3 and name:
            iso_to_names.setdefault(iso3, set()).add(name)
    return {iso: sorted(names) for iso, names in iso_to_names.items() if len(names) > 1}

def country_to_iso3(country_name):
    import pycountry
    if not country_name:
        return None
    name = COUNTRY_ALIASES.get(country_name.strip(), country_name.strip())
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return None

UNIT_ALIASES = {
    "ft": "ft", "feet": "ft", "foot": "ft",
    "mi": "mi", "mile": "mi", "miles": "mi",
    "m": "m", "meter": "m", "meters": "m", "metre": "m", "metres": "m",
    "km": "km", "kilometer": "km", "kilometers": "km", "kilometre": "km", "kilometres": "km",
}

def parse_distance_input(text, default_unit=None):
    """Parse text like '150 ft' or '0.5 kilometers' into (value, unit).
    unit is one of 'ft'/'mi'/'m'/'km'. If no unit letters were typed at all,
    `default_unit` is used instead (still None — i.e. missing — by default,
    which is what every caller except the Community distance field wants); a
    typo'd/unrecognized unit still comes back as unit=None either way, so it's
    still flagged rather than silently guessed."""
    if not text or not str(text).strip():
        return None, None
    match = re.match(r'^\s*([\d,]*\.?\d+)\s*([a-zA-Z]*)\s*$', str(text).strip())
    if not match:
        return None, None
    num_str, unit_str = match.groups()
    try:
        value = float(num_str.replace(',', ''))
    except ValueError:
        return None, None
    unit_str = unit_str.strip().lower()
    unit = UNIT_ALIASES.get(unit_str) if unit_str else default_unit
    return value, unit

def distance_to_meters(value, unit):
    if unit == "km": return value * 1000
    if unit == "mi": return value * 1609.344
    if unit == "ft": return value * 0.3048
    return value

# --- Daily Snapshot (Score Submission-style day view) ---
GEOGRAPHY_RANGES = {
    "OOO": (5000, 5000), "OO%": (4750, 4999), "OOX": (4500, 4749),
    "O%X": (4250, 4499), "OXX": (3500, 4249), "%XX": (2500, 3499), "XXX": (12, 2499)
}

TIME_RANGES = {
    "OOO": (5000, 5000), "OO%": (4800, 4950), "OOX": (4300, 4600),
    "O%X": (3400, 3900), "OXX": (2000, 2500), "%XX": (1000, 1000), "XXX": (0, 0)
}

def geography_score(x):
    if x <= 50: return 5000
    elif x <= 1000: return 5000 - (x * 0.02)
    elif x <= 5000: return 4980 - (x * 0.016)
    elif x <= 100000: return 4900 - (x * 0.004)
    elif x <= 1000000: return 4500 - (x * 0.001)
    elif x <= 2000000: return 3500 - (x * 0.0005)
    elif x <= 3000000: return 2500 - (x * 0.0003333)
    elif x <= 6000000: return 1500 - (x * 0.0002)
    else: return 12

def calculate_time_score(year_guessed, actual_year):
    if actual_year is None: return None
    years_off = abs(int(year_guessed) - actual_year)
    if years_off == 0: return 5000
    elif years_off == 1: return 4950
    elif years_off == 2: return 4800
    elif years_off == 3: return 4600
    elif years_off == 4: return 4300
    elif years_off == 5: return 3900
    elif years_off in [6, 7]: return 3400
    elif years_off in [8, 9, 10]: return 2500
    elif 10 < years_off < 16: return 2000
    elif 15 < years_off < 21: return 1000
    else: return 0

def half_bar_html(score, pattern=None, range_dict=GEOGRAPHY_RANGES):
    total = 5000
    if score is not None and not pd.isna(score):
        pct = min(max(float(score) / total * 100.0, 0.0), 100.0)
        return f'<div class="tg-bar-bg"><div class="tg-bar-fill" style="width:{pct:.2f}%; background:#db5049;"></div></div>'
    elif pattern and pattern in range_dict:
        min_val, max_val = range_dict[pattern]
        min_pct = min_val / total * 100
        max_pct = max_val / total * 100
        return f'''<div class="tg-bar-bg" style="position:relative;"><div style="position:absolute; left:0; width:{min_pct:.2f}%; height:100%; background:#db5049;"></div><div style="position:absolute; left:{min_pct:.2f}%; width:{max_pct - min_pct:.2f}%; height:100%; background:#d1d647;"></div><div style="position:absolute; left:{max_pct:.2f}%; width:{100 - max_pct:.2f}%; height:100%; background:#b0afaa;"></div></div>'''
    return '<div class="tg-bar-bg"><div class="tg-bar-fill" style="width:0%;"></div></div>'

def generate_player_html(player_name, date_rows, players, highlight=False):
    if len(date_rows) == 0: return ""
    row_0 = date_rows.iloc[0]
    total_score = row_0.get(f"{player_name} Total Score")
    all_rounds = date_rows[date_rows["Timeguessr Round"].between(1, 5)]

    geo_sum, time_sum = 0, 0
    for _, r in all_rounds.iterrows():
        gs = r.get(f"{player_name} Geography Score")
        gp = r.get(f"{player_name} Geography")
        ts = r.get(f"{player_name} Time Score")
        tp = r.get(f"{player_name} Time")

        if pd.notna(gs): geo_sum += gs
        elif gp in GEOGRAPHY_RANGES: geo_sum += sum(GEOGRAPHY_RANGES[gp])/2

        if pd.notna(ts): time_sum += ts
        elif tp in TIME_RANGES: time_sum += sum(TIME_RANGES[tp])/2

    total_text = "???" if pd.isna(total_score) else f"{int(total_score):,}/50,000"
    is_michael = player_name == "Michael"
    bg = "#dde5eb" if is_michael else "#edd3df"
    header = "#221e8f" if is_michael else "#8a005c"
    border = "border: 3px solid #db5049; box-shadow: 0 0 15px rgba(219,80,73,0.4);" if highlight else ""

    html = [f'<div class="tg-container" style="background-color: {bg}; {border}"><div class="tg-header" style="color: {header};">{player_name}</div><div class="tg-total">{total_text}</div>']

    if geo_sum == 0 and time_sum == 0:
        html.append('<div class="tg-sub">🌎 Geo: <b>???</b>/25,000</div><div class="tg-sub">📅 Time: <b>???</b>/25,000</div>')
    else:
        html.append(f'<div class="tg-sub">🌎 Geo: <b>{int(geo_sum):,}</b>/25,000</div><div class="tg-sub">📅 Time: <b>{int(time_sum):,}</b>/25,000</div>')

    html.append('<div class="tg-rounds-wrapper">')

    today_ts = pd.Timestamp(datetime.date.today())
    for r_num in range(1, 6):
        r_data = date_rows[date_rows["Timeguessr Round"] == r_num]
        geo_score = time_score = geo_pattern = time_pattern = country_name = None
        if len(r_data) > 0:
            row = r_data.iloc[0]
            geo_score = row.get(f"{player_name} Geography Score")
            time_score = row.get(f"{player_name} Time Score")
            geo_pattern = row.get(f"{player_name} Geography")
            time_pattern = row.get(f"{player_name} Time")
            country_name = row.get("Country")

        round_revealed = True
        if len(r_data) > 0:
            game_date = row_0["Date"]
            if game_date >= today_ts:
                for p in players:
                    if pd.isna(r_data.iloc[0].get(f"{p} Geography Score")):
                        round_revealed = False; break
        else: round_revealed = False

        flag = get_flag_html(country_name) if round_revealed else get_flag_html("United Nations")

        g_txt = f"{int(geo_score):,}/5k" if pd.notna(geo_score) else ("???/5k" if geo_pattern not in GEOGRAPHY_RANGES else f"{GEOGRAPHY_RANGES[geo_pattern][0]:,}-{GEOGRAPHY_RANGES[geo_pattern][1]:,}/5k")
        t_txt = f"{int(time_score):,}/5k" if pd.notna(time_score) else ("???/5k" if time_pattern not in TIME_RANGES else f"{TIME_RANGES[time_pattern][0]:,}-{TIME_RANGES[time_pattern][1]:,}/5k")

        html.append(f'<div class="tg-round"><div class="tg-row"><div class="tg-half"><div class="tg-score-note">{flag} <small>{g_txt}</small></div>{half_bar_html(geo_score, geo_pattern, GEOGRAPHY_RANGES)}</div><div class="tg-half"><div class="tg-score-note">📅 <small>{t_txt}</small></div>{half_bar_html(time_score, time_pattern, TIME_RANGES)}</div></div></div>')

    html.append('</div></div>')
    return "\n".join(html)

def generate_community_html(date_rows):
    if len(date_rows) == 0: return ""
    row_0 = date_rows.iloc[0]
    total_score = row_0.get("Community Average")
    total_text = "???" if pd.isna(total_score) else f"{int(total_score):,}/50,000"

    geo_sum_est, time_sum_est = 0, 0
    have_geo_est, have_time_est = False, False
    round_scores = []

    for r_num in range(1, 6):
        r_data = date_rows[date_rows["Timeguessr Round"] == r_num]
        row_r = r_data.iloc[0] if len(r_data) > 0 else None
        round_scores.append(row_r.get("Community Round Score") if row_r is not None else None)

        time_off = row_r.get("Community Time Distance") if row_r is not None else None
        if pd.notna(time_off):
            t_est = calculate_time_score(float(time_off), 0)
            if t_est is not None:
                time_sum_est += t_est
                have_time_est = True

        dist_m = row_r.get("Community Geography Distance") if row_r is not None else None
        if pd.notna(dist_m):
            geo_sum_est += geography_score(float(dist_m))
            have_geo_est = True

    html = [f'<div class="tg-container" style="background-color: #e9ecef;"><div class="tg-header" style="color: #495057;">Community</div><div class="tg-total">{total_text}</div>']

    geo_txt = f'"{int(geo_sum_est):,}"' if have_geo_est else '"???"'
    time_txt = f'"{int(time_sum_est):,}"' if have_time_est else '"???"'
    html.append(f'<div class="tg-sub">🌎 Geo: <b>{geo_txt}</b>/25,000</div><div class="tg-sub">📅 Time: <b>{time_txt}</b>/25,000</div>')

    html.append('<div class="tg-rounds-wrapper">')

    for r_num, round_score in zip(range(1, 6), round_scores):
        r_txt = f"{int(round_score):,}/10k" if pd.notna(round_score) else "???/10k"
        pct = min(max(float(round_score) / 10000 * 100.0, 0.0), 100.0) if pd.notna(round_score) else 0
        bar_html = f'<div class="tg-bar-bg"><div class="tg-bar-fill" style="width:{pct:.2f}%; background:#6c757d;"></div></div>'

        html.append(f'<div class="tg-round"><div class="tg-score-note">🏆 <small>{r_txt}</small></div>{bar_html}</div>')

    html.append('</div></div>')
    return "\n".join(html)

def get_bar_segments(scores, opponent_scores, max_score):
    bar_html = ""
    bright_palette = ["#db5049", "#fd7e14", "#fcc419", "#40c057", "#228be6"]
    pale_palette = ["#eba5a2", "#fecba6", "#ffe7a3", "#a7e0b0", "#9ccbf2"]
    for i, score in enumerate(scores):
        pct = (score / max_score) * 100
        if pct > 0:
            color = bright_palette[i] if score >= opponent_scores[i] else pale_palette[i]
            bar_html += f'<div style="width:{pct}%; height:100%; background-color:{color}; box-sizing: border-box;" title="Round {i+1}: {int(score)}"></div>'
    return bar_html

def get_community_bar_segments(c_scores, m_scores, s_scores, max_score):
    """Same per-round hues as the M/S bars, but shaded by how many opponents
    the community beat that round: neither = lightest, one = regular (the
    normal bright hue), both = darkest."""
    light_palette = ["#eba5a2", "#fecba6", "#ffe7a3", "#a7e0b0", "#9ccbf2"]
    regular_palette = ["#db5049", "#fd7e14", "#fcc419", "#40c057", "#228be6"]
    dark_palette = ["#a13228", "#c25a00", "#b8860b", "#2b8a3e", "#1864ab"]
    bar_html = ""
    for i, score in enumerate(c_scores):
        pct = (score / max_score) * 100
        if pct > 0:
            beat_count = int(score > m_scores[i]) + int(score > s_scores[i])
            palette = dark_palette if beat_count == 2 else (regular_palette if beat_count == 1 else light_palette)
            color = palette[i]
            bar_html += f'<div style="width:{pct}%; height:100%; background-color:{color}; box-sizing: border-box;" title="Round {i+1}: {int(score)}"></div>'
    return bar_html

def render_score_bars(date_rows):
    m_total_scores, s_total_scores, c_total_scores = [], [], []
    m_geo_scores, s_geo_scores, c_geo_scores = [], [], []
    m_time_scores, s_time_scores, c_time_scores = [], [], []

    for r in range(1, 6):
        r_data = date_rows[date_rows["Timeguessr Round"] == r]
        mg, mt, sg, s_time = 0, 0, 0, 0
        c_total, c_geo, c_time = 0, 0, 0
        if len(r_data) > 0:
            row = r_data.iloc[0]
            mg_val = row.get("Michael Geography Score", 0)
            mt_val = row.get("Michael Time Score", 0)
            sg_val = row.get("Sarah Geography Score", 0)
            st_val = row.get("Sarah Time Score", 0)

            if pd.notna(mg_val): mg = mg_val
            if pd.notna(mt_val): mt = mt_val
            if pd.notna(sg_val): sg = sg_val
            if pd.notna(st_val): s_time = st_val

            # Community: total uses the actual recorded round score, but geo/time
            # are only "estimated" (derived from the average distance/years-off),
            # same as the community score box above.
            c_round_val = row.get("Community Round Score")
            if pd.notna(c_round_val): c_total = c_round_val

            c_time_off = row.get("Community Time Distance")
            if pd.notna(c_time_off):
                est = calculate_time_score(float(c_time_off), 0)
                if est is not None: c_time = est

            c_dist_m = row.get("Community Geography Distance")
            if pd.notna(c_dist_m):
                c_geo = geography_score(float(c_dist_m))

        m_total_scores.append(mg + mt)
        s_total_scores.append(sg + s_time)
        c_total_scores.append(c_total)
        m_geo_scores.append(mg)
        s_geo_scores.append(sg)
        c_geo_scores.append(c_geo)
        m_time_scores.append(mt)
        s_time_scores.append(s_time)
        c_time_scores.append(c_time)

    m_tot_seg = get_bar_segments(m_total_scores, s_total_scores, 50000)
    s_tot_seg = get_bar_segments(s_total_scores, m_total_scores, 50000)
    c_tot_seg = get_community_bar_segments(c_total_scores, m_total_scores, s_total_scores, 50000)
    m_geo_seg = get_bar_segments(m_geo_scores, s_geo_scores, 25000)
    s_geo_seg = get_bar_segments(s_geo_scores, m_geo_scores, 25000)
    c_geo_seg = get_community_bar_segments(c_geo_scores, m_geo_scores, s_geo_scores, 25000)
    m_time_seg = get_bar_segments(m_time_scores, s_time_scores, 25000)
    s_time_seg = get_bar_segments(s_time_scores, m_time_scores, 25000)
    c_time_seg = get_community_bar_segments(c_time_scores, m_time_scores, s_time_scores, 25000)

    def hbar_row(label, color, seg_html):
        return f'<div class="hbar-row"><span class="hbar-lbl" style="color:{color};">{label}</span><div class="hbar-track">{seg_html}</div></div>'

    def hbar_group(m_seg, s_seg, c_seg):
        return f"""<div class="hbar-group"><div class="bar-section-title">Round Scores</div>
            {hbar_row("M", "#221e8f", m_seg)}
            {hbar_row("S", "#8a005c", s_seg)}
            {hbar_row("C", "#6c757d", c_seg)}
        </div>"""

    return {
        "Total Score": hbar_group(m_tot_seg, s_tot_seg, c_tot_seg),
        "Geography Score": hbar_group(m_geo_seg, s_geo_seg, c_geo_seg),
        "Time Score": hbar_group(m_time_seg, s_time_seg, c_time_seg),
    }

def render_percentile_bars(date_rows):
    """Where each player (and the community) ranked that day: Total uses
    TimeGuessr's own Percentile stat (community fixed at the 50th, since the
    community average defines the median); Time/Geo use the Years/Location
    percentile stats instead, with the community's own Years/Location average."""
    if len(date_rows) == 0: return {}
    row_0 = date_rows.iloc[0]

    def num(col, mult=1):
        v = row_0.get(col)
        return float(v) * mult if pd.notna(v) else None

    def pct_bar(label, color, value):
        pct = 0.0 if value is None else max(0.0, min(100.0, value))
        val_txt = "&mdash;" if value is None else f"{pct:.0f}%"
        return (f'<div class="hbar-row"><span class="hbar-lbl" style="color:{color};">{label}</span>'
                f'<div class="pct-bar-track"><div class="pct-bar-fill" style="width:{pct:.1f}%; background-color:{color};"></div></div>'
                f'<span class="hbar-lbl" style="width:32px; color:{color};">{val_txt}</span></div>')

    def build(m_val, s_val, c_val):
        return (f'<div class="hbar-group pct-bar-group"><div class="bar-section-title">Percentile</div>'
                f'{pct_bar("M", "#221e8f", m_val)}{pct_bar("S", "#8a005c", s_val)}{pct_bar("C", "#6c757d", c_val)}</div>')

    return {
        "Total Score": build(num("Michael Percentile", 100), num("Sarah Percentile", 100), 50.0),
        "Time Score": build(num("Michael Years"), num("Sarah Years"), num("Community Years Average")),
        "Geography Score": build(num("Michael Location"), num("Sarah Location"), num("Community Location Average")),
    }

DAILY_SNAPSHOT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
body { margin: 0; padding: 0; font-family: 'Poppins', sans-serif; }
.tg-container { position: relative; padding: 10px 12px; box-sizing: border-box; width: 100%; border-radius: 12px; margin-bottom: 0; }
.tg-header { font-weight:700; font-size:30px; margin:0 0 5px 0; line-height:1.1; }
.tg-total { color:#222; font-size:24px; font-weight:600; margin:0 0 7px 0; line-height:1.1; }
.tg-sub { font-size:20px; margin:0 0 7px 0; line-height:1.1; color:#333; }
.tg-rounds-wrapper { margin-top:7px; }
.tg-round { margin:7px 0; }
.tg-row { display:flex; gap:12px; align-items:center; flex-wrap:nowrap; }
.tg-half { width: 50%; flex: 1; }
.tg-bar-bg { background:#b0afaa; border-radius:10px; height:10px; overflow:hidden; width: 100%; position: relative; }
.tg-bar-fill { height:10px; border-radius:10px; background:#db5049; }
.tg-score-note { font-size:18px; margin:0 0 7px 0; white-space: nowrap; }
.tg-score-note small { color:#444; }
</style>
"""

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
    # "United Nations" is the sentinel for a round that isn't revealed yet
    # (e.g. only one player has completed it) — show the UN flag, matching the
    # Actuals box, rather than the plain white flag used for genuine unknowns.
    if name and str(name).strip().lower() == "united nations":
        return '<img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/svg/1f1fa-1f1f3.svg" width="24" style="vertical-align:middle; margin-right:4px;"/>'
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

def generate_round_updates(df):
    """Replay every round of every day in play order and record how that single
    round shifted the cumulative Michael-vs-Sarah head-to-head control of its
    continent / UN region / country / subdivision / year / decade — separately
    for total, geography and time points.

    Appearance count and the "rounds since last seen" gap (and therefore is_rare)
    are tracked round-by-round: every round a category shows up is its own
    appearance.

    Returns {pd.Timestamp: [round_dict, ...]} with rounds in Timeguessr Round order.
    Each round_dict has round / city / subdivision / country / year / the per-player
    total, geo and time round scores, and metric_rows -> a 3-item list (total, geo,
    time) each with {metric, label, swing, dims}, where dims is a per-dimension list
    of dicts (label, value, tracked, and when tracked: leader, margin, is_new,
    did_flip, is_rare, gap, appearances, prev_leader, prev_margin).
    """
    if df.empty or "Timeguessr Round" not in df.columns:
        return {}

    d = df.copy()
    for p in ["Michael", "Sarah"]:
        for c in ["Geography Score", "Time Score"]:
            for suffix in ["", " (Min)", " (Max)"]:
                col = f"{p} {c}{suffix}"
                if col in d.columns:
                    d[col] = pd.to_numeric(d[col], errors="coerce")
            # fall back to the (Min)+(Max)/2 midpoint when the exact round score
            # isn't known (early days only have the emoji-tier bounds)
            base, lo, hi = f"{p} {c}", f"{p} {c} (Min)", f"{p} {c} (Max)"
            if lo in d.columns and hi in d.columns:
                est = (d[lo] + d[hi]) / 2
                d[f"{base} _est"] = d[base].isna() & est.notna()
                d[base] = d[base].where(d[base].notna(), est)
            else:
                d[f"{base} _est"] = False

    # country -> UN region / continent (batch, once)
    uc = list(d["Country"].dropna().astype(str).str.strip().unique())
    iso_res = cc_obj.convert(names=uc, to="ISO3", not_found="Unknown") if uc else []
    if isinstance(iso_res, str): iso_res = [iso_res]
    iso = dict(zip(uc, iso_res))
    ui = [i for i in set(iso.values()) if i and i != "Unknown"]
    reg_res = cc_obj.convert(names=ui, to="UNregion", not_found="Unknown") if ui else []
    if isinstance(reg_res, str): reg_res = [reg_res]
    reg = dict(zip(ui, reg_res))
    con_res = cc_obj.convert(names=ui, to="continent", not_found="Unknown") if ui else []
    if isinstance(con_res, str): con_res = [con_res]
    con = dict(zip(ui, con_res))

    DIMS = ["continent", "region", "country", "subdivision", "year", "decade"]
    LABELS = {"continent": "Continent", "region": "UN Region", "country": "Country",
              "subdivision": "Subdivision", "year": "Year", "decade": "Decade"}
    METRICS = ["total", "geo", "time"]  # each round splits into these 3 sub-rows, in this order
    METRIC_LABEL = {"total": "Total", "geo": "Geography", "time": "Time"}
    RARE_GAP = 125  # rounds since last appearance (~25 days at 5 rounds/day)
    MAX_SCORE = {"total": 10000.0, "geo": 5000.0, "time": 5000.0}  # best possible round score per metric
    state = {m: {k: {} for k in DIMS} for m in METRICS}  # metric -> dim -> value -> {m, s}
    last_round = {k: {} for k in DIMS}    # dim -> value -> round index last seen
    appearances = {k: {} for k in DIMS}  # dim -> value -> count of rounds it has appeared in

    def leader(delta):
        return "Michael" if delta > 0 else ("Sarah" if delta < 0 else "Tie")

    out = {}
    round_no = 0
    for dt, day in d.groupby("Date", sort=True):
        rounds = []
        for _, r in day.sort_values("Timeguessr Round").iterrows():
            round_no += 1
            country = str(r["Country"]).strip() if pd.notna(r.get("Country")) else None
            subdiv = str(r["Subdivision"]).strip() if (pd.notna(r.get("Subdivision")) and str(r.get("Subdivision")).strip()) else None
            yr = r.get("Year")
            year_s = str(int(yr)) if pd.notna(yr) else None
            decade_s = (str(int(yr // 10) * 10) + "s") if pd.notna(yr) else None
            isoc = iso.get(country, "Unknown") if country else "Unknown"
            region = reg.get(isoc, "Unknown")
            continent = con.get(isoc, "Unknown")

            mg, mt = r.get("Michael Geography Score"), r.get("Michael Time Score")
            sg, stm = r.get("Sarah Geography Score"), r.get("Sarah Time Score")
            has = all(pd.notna(x) for x in (mg, mt, sg, stm))
            m_geo, s_geo = (float(mg), float(sg)) if has else (None, None)
            m_time, s_time = (float(mt), float(stm)) if has else (None, None)
            m_dist_raw, s_dist_raw = r.get("Michael Geography Distance"), r.get("Sarah Geography Distance")
            m_dist = float(m_dist_raw) if pd.notna(m_dist_raw) else None
            s_dist = float(s_dist_raw) if pd.notna(s_dist_raw) else None
            m_yr_guess_raw, s_yr_guess_raw = r.get("Michael Time Guessed"), r.get("Sarah Time Guessed")
            m_year_guess = int(m_yr_guess_raw) if pd.notna(m_yr_guess_raw) else None
            s_year_guess = int(s_yr_guess_raw) if pd.notna(s_yr_guess_raw) else None
            actual_year = int(yr) if pd.notna(yr) else None
            c_dist_raw = r.get("Community Geography Distance")
            c_dist = float(c_dist_raw) if pd.notna(c_dist_raw) else None
            c_yrs_off_raw = r.get("Community Time Distance")
            c_yrs_off = float(c_yrs_off_raw) if pd.notna(c_yrs_off_raw) else None
            c_round_raw = r.get("Community Round Score")
            c_round = float(c_round_raw) if pd.notna(c_round_raw) else None
            c_geo_est = geography_score(c_dist) if c_dist is not None else None
            c_time_est = calculate_time_score(c_yrs_off, 0) if c_yrs_off is not None else None
            m_round = m_geo + m_time if has else None
            s_round = s_geo + s_time if has else None
            estimated = has and bool(
                r.get("Michael Geography Score _est") or r.get("Michael Time Score _est")
                or r.get("Sarah Geography Score _est") or r.get("Sarah Time Score _est"))

            dim_value = {
                "continent": continent if continent != "Unknown" else None,
                "region": region if region != "Unknown" else None,
                "country": country if (country and country != "Unknown") else None,
                "subdivision": f"{subdiv} | {country}" if (subdiv and country) else None,
                "year": year_s,
                "decade": decade_s,
            }
            dim_display = {
                "continent": continent if continent != "Unknown" else "—",
                "region": region if region != "Unknown" else "—",
                "country": country or "—",
                "subdivision": subdiv or "—",
                "year": year_s or "—",
                "decade": decade_s or "—",
            }

            # per-dimension round-level facts (computed once per round, not per metric)
            dim_meta = {}
            for k in DIMS:
                v = dim_value[k]
                if v is None or not has:
                    dim_meta[k] = {"tracked": False}
                    continue
                prev_round = last_round[k].get(v)
                is_new = prev_round is None
                gap = 0 if is_new else (round_no - prev_round)
                appearances[k][v] = appearances[k].get(v, 0) + 1
                last_round[k][v] = round_no
                dim_meta[k] = {
                    "tracked": True, "is_new": is_new, "gap": gap,
                    "appearances": appearances[k][v],
                    "is_rare": (not is_new) and gap >= RARE_GAP,
                }

            metric_add = {"total": (m_round, s_round), "geo": (m_geo, s_geo), "time": (m_time, s_time)}
            metric_rows = []
            for mtr in METRICS:
                add_m, add_s = metric_add[mtr]
                dim_rows = []
                for k in DIMS:
                    v = dim_value[k]
                    dm = dim_meta[k]
                    row = {"key": k, "label": LABELS[k], "value": dim_display[k], "tracked": False}
                    if dm["tracked"]:
                        st = state[mtr][k]
                        prev = st.get(v)
                        pm, ps = (prev["m"], prev["s"]) if prev else (0.0, 0.0)
                        prev_leader = leader(pm - ps)
                        nm, ns = pm + add_m, ps + add_s
                        st[v] = {"m": nm, "s": ns}
                        new_leader = leader(nm - ns)
                        did_flip = (not dm["is_new"]) and new_leader != prev_leader
                        # "Missed flip": the leader ended this round ahead, but scored
                        # weakly enough that the trailing player, had they posted the
                        # maximum possible score, would have taken the lead — and didn't.
                        missed_flip = False
                        if (not did_flip) and (not dm["is_new"]) and new_leader != "Tie":
                            cap = MAX_SCORE[mtr]
                            if new_leader == "Michael":
                                missed_flip = (ps + cap) > nm
                            else:
                                missed_flip = (pm + cap) > ns
                        row.update({
                            "tracked": True,
                            "is_new": dm["is_new"],
                            "did_flip": did_flip,
                            "missed_flip": missed_flip,
                            "is_rare": dm["is_rare"],
                            "gap": dm["gap"],
                            "appearances": dm["appearances"],
                            "leader": new_leader,
                            "margin": abs(nm - ns),
                            "prev_leader": prev_leader,
                            "prev_margin": abs(pm - ps),
                        })
                    dim_rows.append(row)
                metric_rows.append({
                    "metric": mtr,
                    "label": METRIC_LABEL[mtr],
                    "swing": (add_m - add_s) if has else None,
                    "dims": dim_rows,
                })

            rn = r.get("Timeguessr Round")
            rounds.append({
                "round": int(rn) if pd.notna(rn) else len(rounds) + 1,
                "city": str(r["City"]).strip() if pd.notna(r.get("City")) else "—",
                "subdivision": subdiv or "",
                "country": country or "",
                "year": year_s or "",
                "m_round": m_round,
                "s_round": s_round,
                "m_geo": m_geo, "s_geo": s_geo,
                "m_time": m_time, "s_time": s_time,
                "m_dist": m_dist, "s_dist": s_dist,
                "m_year_guess": m_year_guess, "s_year_guess": s_year_guess, "actual_year": actual_year,
                "c_dist": c_dist, "c_yrs_off": c_yrs_off,
                "c_round": c_round, "c_geo_est": c_geo_est, "c_time_est": c_time_est,
                "estimated": estimated,
                "metric_rows": metric_rows,
            })
        out[pd.Timestamp(dt)] = rounds
    return out

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
        # A tie is not a win for either side, so it breaks an active streak
        # instead of being skipped over (which let a streak survive across it).
        if w == sw and w != "Tie": cs += 1
        else: sw, cs = w, (1 if w != "Tie" else 0)
        if w != "Tie" and cs > ms[w]: ms[w] = cs

    sh = ""
    if sw and sw != "Tie" and cs > 0:
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

def render_forecast_section(fs_list, bars_by_cat=None):
    bars_by_cat = bars_by_cat or {}
    html = '<div class="forecast-container">'
    icons = {"Total Score": "🏆", "Time Score": "⏱️", "Geography Score": "🌍"}
    borders = {"Total Score": "fc-cat-total", "Time Score": "fc-cat-time", "Geography Score": "fc-cat-geo"}
    for f in fs_list:
        if not f: continue
        cat, ic, bc = f['category'], icons.get(f['category'], "📊"), borders.get(f['category'], "")
        bars_html = bars_by_cat.get(cat, "")
        def lc(l): return "#221e8f" if l == "Michael" else ("#8a005c" if l == "Sarah" else "#999")
        html += f"""<div class="forecast-card {bc}"><div class="fc-header"><span class="fc-icon">{ic}</span><span class="fc-title">{cat}</span></div>{bars_html}<div class="fc-momentum-grid"><div class="fc-mom-box"><div class="fc-mom-label">5-Game Avg</div><div class="fc-mom-leader" style="color: {lc(f['l5'])}">{f['l5']}</div><div class="fc-mom-detail">{f['m5']}</div></div><div class="fc-mom-box"><div class="fc-mom-label">10-Game Avg</div><div class="fc-mom-leader" style="color: {lc(f['l10'])}">{f['l10']}</div><div class="fc-mom-detail">{f['m10']}</div></div></div><div class="fc-streaks"><div class="fc-streaks-title">Active Streaks</div>{f['streaks_html'] if f['streaks_html'] else '<div style="font-size:11px; color:#999; font-style:italic;">No active streaks.</div>'}</div></div>"""
    return html + '</div>'

FEED_CATEGORIES = {
    "Momentum": ["flip", "momentum_record_largest", "momentum_score_top_10", "momentum_score_bottom_10"], 
    "Win Streak Updates": ["streak", "streak_broken"], 
    "Score Threshold Streaks": ["score_streak", "score_streak_broken"], 
    "Win Margin Records": ["margin_record_largest", "margin_record_tightest"], 
    "Leaderboard Records": ["score_top_10", "score_bottom_10", "score_vs_opp"],
    "Milestones": ["milestone"]
}
# Location / year / decade discoveries, control flips and rare appearances are
# now covered by the round-by-round table at the top of each edition, so their
# feed sections were removed.

def render_round_strip(rounds):
    """Top-of-edition table. Per round: a slim header row (dimension value +
    appearance count + Rare/New marker with rounds-since-last) sitting above 3
    score-type rows (Total, Geography, Time). Rounds ordered by number, then by
    score type."""
    if not rounds or not any(dr.get("tracked")
                             for rd in rounds for mr in rd["metric_rows"] for dr in mr["dims"]):
        return ""
    pc_map = {"Michael": "p-michael", "Sarah": "p-sarah", "Tie": "p-tie"}
    dims0 = rounds[0]["metric_rows"][0]["dims"]

    def ordinal(n):
        suf = "th" if 11 <= (n % 100) <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suf}"

    def dim_header(dr):
        if not dr.get("tracked"):
            return '<td class="rt-cell rt-dimhdr"><span class="rt-dh-val rb-na">&mdash;</span></td>'
        ac = dr.get("appearances", 0)
        box_cls, meta = "", f'<span class="rt-appc">{ordinal(ac)} appearance</span>'
        if dr.get("is_new"):
            box_cls = " rt-cell-new"
            meta += '<span class="rt-mk rt-mk-new">New</span>'
        elif dr.get("is_rare"):
            box_cls = " rt-cell-rare"
            meta += ('<span class="rt-mk rt-mk-rare">Rare</span>'
                     f'<span class="rt-gap">first in {dr.get("gap", 0)} rounds</span>')
        return (f'<td class="rt-cell rt-dimhdr{box_cls}">'
                f'<span class="rt-dh-val">{dr["value"]}</span>{meta}</td>')

    def metric_cell(dr):
        if not dr.get("tracked"):
            return '<td class="rt-cell"><span class="rt-state rb-na">&mdash;</span></td>'
        ld = dr["leader"]
        lead_txt = ('<span class="p-tie">Tied</span>' if ld == "Tie"
                    else f'<span class="{pc_map[ld]}">{ld} +{dr["margin"]:,.0f}</span>')
        tag, was, box_cls = "", "", ""
        # a flip on this score type overrules the value-level (New / Rare) tint;
        # otherwise the whole column carries the New / Rare colour
        if dr["did_flip"]:
            box_cls = " rt-cell-flip"
            pl, nl = dr["prev_leader"], ld
            oc = "TIE" if pl == "Tie" else pl[0]
            nc = "TIE" if nl == "Tie" else nl[0]
            dcls = "m" if nl == "Michael" else ("s" if nl == "Sarah" else "t")
            tag = (f'<span class="rb-tag rb-tag-flip">Flip</span>'
                   f'<span class="rt-dir rt-dir-{dcls}">{oc}&#10132;{nc}</span>')
            was = ('<span class="rb-was">was Tied</span>' if pl == "Tie"
                   else f'<span class="rb-was">was {pl} +{dr["prev_margin"]:,.0f}</span>')
        elif dr.get("is_new"):
            box_cls = " rt-cell-new"
        elif dr.get("is_rare"):
            box_cls = " rt-cell-rare"
        # "Missed flip": trailing player had a max-score path to the lead this round
        # and didn't take it. Badge-only — composes with any column tint.
        if dr.get("missed_flip") and not dr["did_flip"] and ld != "Tie":
            trailer = "Sarah" if ld == "Michael" else "Michael"
            tag += ('<span class="rb-tag rb-tag-missed">Missed Flip</span>'
                    f'<span class="rt-dir rt-dir-missed">{ld[0]}&#10132;{trailer[0]}</span>')
        return (f'<td class="rt-cell{box_cls}"><span class="rt-state">{lead_txt}{was}</span>{tag}</td>')

    def swing_badge(val):
        if val is None:
            return ""
        if abs(val) < 1:
            return '<span class="rt-type-swing">even</span>'
        w = "Michael" if val > 0 else "Sarah"
        return f'<span class="rt-type-swing rb-swing {pc_map[w]}">{w[0]} +{abs(val):,.0f}</span>'

    def score_row(lbl, m, s, prefix="", c=None, c_is_est=False):
        if m is None:
            return ""
        c_part = ""
        if c is not None:
            c_txt = f'&quot;{c:,.0f}&quot;' if c_is_est else f'{c:,.0f}'
            c_part = f'<span class="rb-dash">&ndash;</span><b class="p-community">{c_txt}</b>'
        return (f'<span class="rt-score-line"><span class="rt-score-lbl">{lbl}</span>{prefix}'
                f'<b class="p-michael">{m:,.0f}</b><span class="rb-dash">&ndash;</span>'
                f'<b class="p-sarah">{s:,.0f}</b>{c_part}</span>')

    def format_km(dist_m):
        if dist_m is None: return "&mdash;"
        return f"{dist_m / 1000.0:.2f} km"

    def dist_row(m_dist, s_dist, c_dist):
        if m_dist is None and s_dist is None:
            return ""
        c_part = f'<span class="rb-dash">&ndash;</span><b class="p-community">{format_km(c_dist)}</b>' if c_dist is not None else ""
        return (f'<span class="rt-score-line"><span class="rt-score-lbl">Dist</span>'
                f'<b class="p-michael">{format_km(m_dist)}</b><span class="rb-dash">&ndash;</span>'
                f'<b class="p-sarah">{format_km(s_dist)}</b>{c_part}</span>')

    def format_year_guess(guess, actual):
        if guess is None or actual is None: return "&mdash;"
        diff = guess - actual
        if diff == 0: return f"{guess} (exact)"
        return f"{guess} (+{diff})" if diff > 0 else f"{guess} (&minus;{abs(diff)})"

    def year_row(m_guess, s_guess, actual, c_yrs_off):
        if m_guess is None and s_guess is None:
            return ""
        c_part = f'<span class="rb-dash">&ndash;</span><b class="p-community">{c_yrs_off:.1f} yrs</b>' if c_yrs_off is not None else ""
        return (f'<span class="rt-score-line"><span class="rt-score-lbl">Year</span>'
                f'<b class="p-michael">{format_year_guess(m_guess, actual)}</b><span class="rb-dash">&ndash;</span>'
                f'<b class="p-sarah">{format_year_guess(s_guess, actual)}</b>{c_part}</span>')

    body = ""
    for rd in rounds:
        loc = ", ".join([b for b in [rd["subdivision"], rd["country"]] if b]) or rd["city"]
        flag = get_flag_html(rd["country"]) if rd["country"] else ""
        yr = f" &middot; {rd['year']}" if rd["year"] else ""
        approx = '<span class="rb-approx" title="estimated from score tiers">~</span>' if rd.get("estimated") else ''
        if rd["m_round"] is not None:
            score = (score_row("Total", rd["m_round"], rd["s_round"], prefix=approx, c=rd.get("c_round"))
                     + score_row("Geo", rd["m_geo"], rd["s_geo"], c=rd.get("c_geo_est"), c_is_est=True)
                     + score_row("Time", rd["m_time"], rd["s_time"], c=rd.get("c_time_est"), c_is_est=True))
            extra = (dist_row(rd.get("m_dist"), rd.get("s_dist"), rd.get("c_dist"))
                     + year_row(rd.get("m_year_guess"), rd.get("s_year_guess"), rd.get("actual_year"), rd.get("c_yrs_off")))
            if extra:
                score += f'<div class="rt-extra">{extra}</div>'
        else:
            score = '<span class="rb-score-na">no scores</span>'
        round_cell = (f'<td class="rt-round" rowspan="4">'
                      f'<span class="rt-loc">{flag}{loc}{yr}</span>{score}</td>')
        alt = " alt" if rd["round"] % 2 == 0 else ""

        vdims = rd["metric_rows"][0]["dims"]
        hdr_cells = "".join(dim_header(dr) for dr in vdims)
        body += (f'<tr class="rt-hdrrow{alt}">{round_cell}'
                 f'<td class="rt-type rt-type-hdr">Standing</td>{hdr_cells}</tr>')
        for mr in rd["metric_rows"]:
            cells = "".join(metric_cell(dr) for dr in mr["dims"])
            type_cell = (f'<td class="rt-type rt-type-{mr["metric"]}">'
                         f'<span class="rt-type-lbl">{mr["label"]}</span>{swing_badge(mr["swing"])}</td>')
            body += f'<tr class="rt-mrow{alt}">{type_cell}{cells}</tr>'

    head = "".join(f'<th>{dr["label"]}</th>' for dr in dims0)
    return (f'<div class="round-strip"><div class="round-strip-title">Round-by-Round'
            f'<span class="rss-sub">each round, split Total &rarr; Geography &rarr; Time, across every standing</span></div>'
            f'<div class="round-table-wrap"><table class="round-table">'
            f'<thead><tr><th class="rt-round">Round</th><th class="rt-type">Score</th>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></div></div>')

def render_daily_news(dt, evs, round_list=None):
    ec, rh = len(evs), ""
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
    strip_html = render_round_strip(round_list or [])
    body = f'<div class="events-list">{rh}</div>' if rh else ""

    round_card = f"""<div class="daily-card" id="{day_id}"><div class="daily-header daily-header-end"><span class="daily-badge">Round Recap</span></div>{strip_html}</div>"""

    updates_badge = f"{ec} Updates" if ec else "No Updates"
    updates_body = body if body else '<div style="text-align:center; padding:40px; color:#999; font-size: 14px;">No news events for this date.</div>'
    updates_card = f"""<div class="daily-card" id="{day_id}-updates"><div class="daily-header"><span class="daily-date">Daily Updates</span><span class="daily-badge">{updates_badge}</span></div>{updates_body}</div>"""

    return round_card, updates_card

@st.cache_data
def _compute_daily_feed_data(_raw_data: pd.DataFrame, mtime: float):
    """The momentum/streak/record/milestone "news" feed is derived entirely
    from Timeguessr_Stats.csv (via `_raw_data`) — it doesn't depend on any
    widget state — but computing it means ~20 full-history passes (one
    iterrows() scan per generate_* call below, several per score type). Left
    uncached, that ran on *every* rerun of this page, i.e. on every keystroke
    or click anywhere on the page, which is what actually made the Daily page
    feel laggy while filling in a submission. Cached here keyed only on the
    stats file's mtime (the leading-underscore `_raw_data` param is passed
    through uncached/unhashed — see Streamlit's cache_data docs) so it's real
    work exactly once per actual data change, a no-op cache hit otherwise.
    `mtime` is only meaningful now that Score_Update.score_update() skips
    rewriting Timeguessr_Stats.csv when nothing upstream actually changed —
    previously it rewrote (and bumped the mtime of) that file on every single
    rerun regardless, which permanently defeated this kind of caching."""
    df_t = prepare_total_margins_data(_raw_data)
    df_tm = prepare_time_margins_data(_raw_data)
    df_g = prepare_geography_margins_data(_raw_data)
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
    all_evs.extend(generate_milestone_events(_raw_data))
    round_updates = generate_round_updates(_raw_data)
    return df_t, df_tm, df_g, all_evs, round_updates

stats_mtime = os.path.getmtime("./Data/Timeguessr_Stats.csv") if os.path.exists("./Data/Timeguessr_Stats.csv") else 0
raw_data = load_data(mtime=stats_mtime)
# Momentum/streak/record tracking (df_t/df_tm/df_g/all_evs below) needs both
# players' data to mean anything, so it keeps using the both-required `raw_data`.
# Per-day rendering (score boxes, Actuals, bars) needs to work even when only
# one player has submitted, so it uses this unfiltered version instead.
raw_data_all = load_data(mtime=stats_mtime, require_both=False)
if not raw_data_all.empty:
    df_t, df_tm, df_g, all_evs, round_updates = _compute_daily_feed_data(raw_data, stats_mtime)

    with st.sidebar:
        st.markdown("<h2 style='text-align:center;'>Settings</h2>", unsafe_allow_html=True)
        edit_toggle_slot = st.empty()  # filled in below, once the selected date's edit state is known
        st.markdown('<hr style="border:none;border-top:1px solid #d9d7cc;margin:1px 24px 12px 24px;">', unsafe_allow_html=True)
        sf = st.multiselect("Filter Categories:", options=list(FEED_CATEGORIES.keys()), default=list(FEED_CATEGORIES.keys()))

    # Collect requested event types based on sidebar selection
    active_types = set()
    for cat_name in sf:
        active_types.update(FEED_CATEGORIES[cat_name])

    # Filter events and group by date (keys normalized to Timestamp)
    fe = [e for e in all_evs if e.get('event_type') in active_types]
    ev_d = {}
    for e in fe:
        d = pd.Timestamp(e['date'])
        ev_d.setdefault(d, []).append(e)

    # An "edition" exists for every day that actually has round data, plus any
    # day that has matching events. Round strip always shows (it is the recap).
    scored_days = {d for d, rl in round_updates.items() if any(rr["m_round"] is not None for rr in rl)}
    sd = sorted(set(ev_d.keys()) | scored_days, reverse=True)
    sd_set = set(sd)

    # --- HEADER: the Edition Date IS the title now, and stays clickable ---
    st.markdown('<div id="top"></div>', unsafe_allow_html=True)

    with st.container(key="edition_date_stack"):
        if just_entered_daily_page:
            # Fresh arrival on the page (not a same-page rerun) — always
            # default back to today regardless of whatever date was last
            # viewed here.
            st.session_state["edition_date_input"] = datetime.date.today()
        selected_date = st.date_input(
            "Edition Date",
            value=sd[0].date() if sd else datetime.date.today(),
            max_value=datetime.date.today(),
            label_visibility="collapsed",
            key="edition_date_input",
        )
        display_str = pd.Timestamp(selected_date).strftime("%A, %B %d, %Y")
        st.markdown(f'<div class="page-title edition-date-overlay">{display_str}</div>', unsafe_allow_html=True)

    sel_ts = pd.Timestamp(selected_date)
    date_rows = raw_data_all[raw_data_all["Date"] == sel_ts]

    # Comparison bars (Round Scores / Percentile) inherently compare Michael vs
    # Sarah — if only one of them played, there is nothing meaningful to show,
    # so this is filled in below only once both are confirmed present.
    bars_by_cat = {}

    # --- Score Submission (Actuals + Michael / Sarah / Community, merged from
    #     the old Score Submission page) ---
    if selected_date:
        # Calculate Day
        reference_date = datetime.date(2025, 10, 28)
        timeguessr_day = 880 + (selected_date - reference_date).days

        # Exit edit mode after a successful save (must run before the Edit toggle below
        # is instantiated — Streamlit forbids setting a widget's session-state value
        # after the widget with that key has already been created in the same run).
        if st.session_state.pop(f"_exit_edit_page_{selected_date}", False):
            st.session_state[f"edit_page_{selected_date}"] = False
        is_page_edit = st.session_state.get(f"edit_page_{selected_date}", False)

        if "last_viewed_timeguessr_day" not in st.session_state:
            st.session_state["last_viewed_timeguessr_day"] = timeguessr_day
        st.session_state["last_viewed_timeguessr_day"] = timeguessr_day

        row_for_stats = date_rows.iloc[0] if not date_rows.empty else None
        has_community = row_for_stats is not None and pd.notna(row_for_stats.get("Community Average"))
        if has_community and not is_page_edit:
            for r_idx in range(1, 6):
                for k in [f"cs_{r_idx}_{selected_date}", f"ct_{r_idx}_{selected_date}", f"cd_{r_idx}_{selected_date}", f"cu_{r_idx}_{selected_date}"]:
                    if k in st.session_state: del st.session_state[k]
            for k in [f"cavg_{selected_date}", f"cyrs_{selected_date}", f"cloc_{selected_date}"]:
                if k in st.session_state: del st.session_state[k]

        # --- Pre-load Actuals Data ---
        act_path = "./Data/Timeguessr_Actuals_Parsed.csv"
        act_df = pd.DataFrame()
        if os.path.exists(act_path): act_df = pd.read_csv(act_path)

        map_mtime = os.path.getmtime("./Data/Custom_World_Map_New.json") if os.path.exists("./Data/Custom_World_Map_New.json") else 0
        map_subdivs = load_map_subdivisions(map_mtime)

        curr_act = act_df[(act_df['Timeguessr Day'] == timeguessr_day)] if not act_df.empty else pd.DataFrame()
        act_exists = not curr_act.empty

        if act_exists and not is_page_edit:
            for r_idx in range(1, 6):
                for k in [f"ay_{r_idx}_{selected_date}", f"ac_{r_idx}_{selected_date}", f"as_{r_idx}_{selected_date}", f"acs_{r_idx}_{selected_date}", f"aci_{r_idx}_{selected_date}", f"acity_{r_idx}_{selected_date}"]:
                    if k in st.session_state: del st.session_state[k]

        # Each player's CSV is read once here and reused below (both for the
        # m_has/s_has check and inside the p_state loop) — this used to read
        # every player's CSV up to 3x over on a single rerun (twice just for
        # m_has/s_has, since it re-called pd.read_csv inside its own boolean
        # mask expression, plus again per player in the loop below).
        m_path = "./Data/Timeguessr_Michael_Parsed.csv"
        s_path = "./Data/Timeguessr_Sarah_Parsed.csv"
        df_michael_all = pd.read_csv(m_path) if os.path.exists(m_path) else pd.DataFrame()
        df_sarah_all = pd.read_csv(s_path) if os.path.exists(s_path) else pd.DataFrame()
        m_has = not df_michael_all.empty and not df_michael_all[df_michael_all['Timeguessr Day'] == timeguessr_day].empty
        s_has = not df_sarah_all.empty and not df_sarah_all[df_sarah_all['Timeguessr Day'] == timeguessr_day].empty

        act_hidden = selected_date == datetime.date.today() and act_exists and not (m_has and s_has)

        # --- Pre-load Player State Data ---
        p_state = {}
        _player_dfs = {"Michael": df_michael_all, "Sarah": df_sarah_all}
        for p_name in ("Michael", "Sarah"):
            csv_p = f"./Data/Timeguessr_{p_name}_Parsed.csv"
            df_p = _player_dfs[p_name]
            curr_p = df_p[df_p['Timeguessr Day'] == timeguessr_day] if not df_p.empty else pd.DataFrame()

            has_g = not curr_p.empty

            if has_g and not is_page_edit:
                for r_idx in range(1, 6):
                    for k in [f"d_{p_name}_{r_idx}_{selected_date}", f"y_{p_name}_{r_idx}_{selected_date}"]:
                        if k in st.session_state: del st.session_state[k]
                for k in [f"ts_{p_name}_{selected_date}_real", f"pct_{p_name}_{selected_date}_real", f"yrs_{p_name}_{selected_date}_real", f"loc_{p_name}_{selected_date}_real"]:
                    if k in st.session_state: del st.session_state[k]

            def_total = ""
            if has_g:
                ts = curr_p.iloc[0].get(f'{p_name} Total Score')
                def_total = "" if pd.isna(ts) else f"{ts:g}"

            p_state[p_name] = {
                'df': df_p, 'curr': curr_p, 'has_g': has_g,
                'def_total': def_total, 'csv': csv_p,
                'input': {}, 'comp_tot': 0, 'edit': False,
            }

        is_today = selected_date == datetime.date.today()
        both_played = p_state["Michael"]['has_g'] and p_state["Sarah"]['has_g']

        # Round Scores / Percentile comparison bars inherently compare Michael vs
        # Sarah — only meaningful once both have actually played.
        if not date_rows.empty and both_played:
            bars_by_cat = render_score_bars(date_rows)
            pct_by_cat = render_percentile_bars(date_rows)
            for _cat in bars_by_cat:
                bars_by_cat[_cat] += pct_by_cat.get(_cat, "")

        # --- Single shared Edit toggle for the whole page (Actuals + Michael +
        # Sarah + Community), rendered at the top of the sidebar Settings panel
        # as a View/Edit segmented button pair, matching the Comparison page's
        # settings style (Cross/Self, Scores/Win Margins, etc.). ---
        any_submitted = act_exists or p_state["Michael"]['has_g'] or p_state["Sarah"]['has_g'] or has_community
        edit_page = True
        if any_submitted:
            edit_page = st.session_state.get(f"edit_page_{selected_date}", False)
            with edit_toggle_slot.container():
                _ec1, _ec2 = st.columns(2)
                with _ec1:
                    if st.button("View", key=f"edit_btn_view_{selected_date}", use_container_width=True,
                                 type="secondary" if edit_page else "primary"):
                        st.session_state[f"edit_page_{selected_date}"] = False
                        st.rerun()
                with _ec2:
                    if st.button("Edit", key=f"edit_btn_edit_{selected_date}", use_container_width=True,
                                 type="primary" if edit_page else "secondary"):
                        st.session_state[f"edit_page_{selected_date}"] = True
                        st.rerun()
        edit_act = True if not act_exists else edit_page
        p_state["Michael"]['edit'] = edit_page
        p_state["Sarah"]['edit'] = edit_page
        edit_community = edit_page

        # --- ACTUALS (full-width section on top) ---
        # On the current day, if the two haven't both played yet, the actual
        # answers would spoil the round — the consolidated box still shows, but
        # with UN flags and "???" for city / region / year (the same treatment
        # the Michael / Sarah boxes give an unfinished round).
        mask_actuals = act_hidden and not edit_act

        # Once submitted and not editing, the consolidated box below carries its
        # own "Actuals" title, matching the score boxes — this title would be
        # redundant then, so it's only shown while editing/unsubmitted.
        if not (act_exists and not edit_act):
            st.markdown('<div class="section-title" style="color:#db5049;">Actuals</div>', unsafe_allow_html=True)

        # --- ACTUAL ANSWERS ROUNDS ---
        actual_rounds_data = {}
        all_valid_act = True
        save_rows_act = []
        actuals_box_html = None  # submitted & not editing: rendered below the M/S/C boxes instead of here

        if True:  # the Actuals section always renders now (masked when mask_actuals)
            if act_exists and not edit_act:
                # Submitted & not editing: one consolidated strip of 5 round cards
                # (flag, city, subdivision/country, year) instead of 5 separate
                # input-style boxes — a quick-scan recap of the day's locations.
                round_cards = []
                for r in range(1, 6):
                    row = curr_act[curr_act['Timeguessr Round'] == r].iloc[0] if len(curr_act[curr_act['Timeguessr Round'] == r]) > 0 else {}
                    y_val = str(int(row['Year'])) if 'Year' in row and pd.notna(row['Year']) else ""
                    c_def_raw = row.get('Country', '')
                    s_def = row.get('Subdivision', '')
                    c_val = row.get('City', '')

                    valid_y = y_val.isdigit() and len(y_val) == 4 and 1900 <= int(y_val) <= selected_date.year
                    actual_rounds_data[r] = {'year': y_val if valid_y else None, 'year_valid': valid_y}

                    if mask_actuals:
                        flag_html = get_flag_emoji("United Nations")
                        city_disp = sub_country = year_disp = "???"
                    else:
                        flag_html = get_flag_emoji(c_def_raw) if c_def_raw else get_flag_emoji("United Nations")
                        sub_country = c_def_raw or "—"
                        if pd.notna(s_def) and str(s_def).strip(): sub_country = f"{s_def}, {sub_country}"
                        city_disp = c_val or "—"
                        year_disp = y_val or "—"

                    round_cards.append(f'''<div style="flex:1; min-width:140px; background:rgba(255,255,255,0.55); border-radius:8px; padding:10px 12px; text-align:center;">
        <div style="font-weight:800; color:#db5049; font-size:0.7em; letter-spacing:0.5px; margin-bottom:5px;">ROUND {r}</div>
        <div style="font-size:1.5em; line-height:1;">{flag_html}</div>
        <div style="font-weight:700; color:#333; font-size:0.95em; margin-top:5px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{city_disp}</div>
        <div style="color:#777; font-size:0.78em; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{sub_country}</div>
        <div style="color:#db5049; font-weight:700; font-size:0.88em; margin-top:4px;">📅 {year_disp}</div>
    </div>''')

                # Flat pastel background, no border accent / drop shadow — matches
                # the Michael / Sarah / Community boxes above (plain colour-tinted
                # cards, no gradients or shadows there either), and no title:
                # this box sits directly under them so what it is needs no label.
                actuals_box_html = f'''<div style="background:#f5d9d8; border-radius:12px; padding:14px 16px;">
    <div style="display:flex; gap:10px; flex-wrap:wrap;">{"".join(round_cards)}</div>
    </div>'''
            else:
                # The whole editable Actuals grid is one fragment: typing in it
                # only reruns/re-renders these 5 columns, not every Michael /
                # Sarah / Community field (and the momentum boxes) below it.
                # Outputs go through session_state; the shared Submit button
                # (outside every fragment) triggers a full rerun that rebuilds
                # them from scratch.
                _all_countries = list(config.get('countries', {}).keys())

                @st.fragment
                def _actuals_editor():
                    year_data, rows = {}, {}
                    act_cols = st.columns(5)
                    for r in range(1, 6):
                        with act_cols[r - 1]:
                            st.markdown(f'<p style="text-align:center; font-weight:700;">Round {r}</p>', unsafe_allow_html=True)
                            row = curr_act[curr_act['Timeguessr Round'] == r].iloc[0] if act_exists and len(curr_act[curr_act['Timeguessr Round'] == r]) > 0 else {}

                            y_val = str(int(row['Year'])) if 'Year' in row and pd.notna(row['Year']) else ""
                            c_def_raw = row.get('Country', '')
                            s_def = row.get('Subdivision', '')
                            c_val = row.get('City', '')

                            y = st.text_input("Year", value=y_val, key=f"ay_{r}_{selected_date}", disabled=not edit_act)
                            cit = st.text_input("City", value=c_val, key=f"acity_{r}_{selected_date}", disabled=not edit_act)

                            # Build country list from config; float countries matching typed city to top
                            typed_city_for_country = (cit or "").strip().lower()
                            matching_countries = []
                            if typed_city_for_country and not act_df.empty and 'City' in act_df.columns and 'Country' in act_df.columns:
                                hit_countries = act_df[
                                    act_df['City'].str.lower() == typed_city_for_country
                                ]['Country'].dropna().unique().tolist()
                                matching_countries = [c for c in _all_countries if c in hit_countries]

                            other_countries = [c for c in _all_countries if c not in matching_countries]
                            opts = [""] + matching_countries + other_countries
                            matching_country_set = set(matching_countries)

                            c_def = c_def_raw if c_def_raw in opts else opts[0]
                            c_idx = opts.index(c_def) if c_def in opts else 0
                            cou = st.selectbox(
                                "Country", opts, index=c_idx,
                                format_func=lambda c, ms=matching_country_set: ("★ " + c if c in ms else c),
                                key=f"ac_{r}_{selected_date}", disabled=not edit_act
                            )

                            # Build subdivision list from map data; float subs matching typed city to top
                            iso3 = country_to_iso3(cou) if cou else None
                            subs_raw = map_subdivs.get(iso3, []) if iso3 else []

                            typed_city = (cit or "").strip().lower()
                            matching_subs = []
                            if subs_raw and typed_city and not act_df.empty and 'City' in act_df.columns and 'Subdivision' in act_df.columns:
                                hit_subs = act_df[
                                    (act_df['Country'] == cou) &
                                    (act_df['City'].str.lower() == typed_city)
                                ]['Subdivision'].dropna().unique().tolist()
                                matching_subs = [s for s in subs_raw if s in hit_subs]

                            if subs_raw:
                                other_subs = [s for s in subs_raw if s not in matching_subs]
                                subs_ordered = [""] + matching_subs + other_subs
                                matching_set = set(matching_subs)

                                if s_def in subs_ordered: s_idx = subs_ordered.index(s_def)
                                else: s_idx = 0

                                sub = st.selectbox(
                                    "Sub", subs_ordered, index=s_idx,
                                    format_func=lambda s, ms=matching_set: ("★ " + s if s in ms else s),
                                    key=f"as_{r}_{selected_date}", disabled=not edit_act
                                )
                            else:
                                sub = ""

                            valid_y = y.isdigit() and len(y) == 4 and 1900 <= int(y) <= selected_date.year
                            year_data[r] = {'year': y if valid_y else None, 'year_valid': valid_y}
                            rows[r] = {
                                "Timeguessr Day": timeguessr_day, "Timeguessr Round": r,
                                "City": cit, "Subdivision": sub, "Country": cou,
                                "Year": int(y) if valid_y else 0,
                                "_valid": bool(y and cou and cit and valid_y),
                            }
                    st.session_state["_act_year_data"] = year_data
                    st.session_state["_act_rows"] = rows

                _actuals_editor()

                actual_rounds_data = st.session_state.get("_act_year_data", {})
                if edit_act:
                    _rows = [st.session_state["_act_rows"][r] for r in range(1, 6) if r in st.session_state.get("_act_rows", {})]
                    all_valid_act = len(_rows) == 5 and all(rr["_valid"] for rr in _rows)
                    save_rows_act = [{k: v for k, v in rr.items() if k != "_valid"} for rr in _rows]

            # Actuals save logic is invoked from the single shared Submit button below
            # (see submit_actuals()), rather than its own button here.

            st.divider()

        # --- MICHAEL / SARAH / COMMUNITY (3 columns, kept in lock-step via min-height slots
        #     that grow instead of scrolling if content needs more room) ---
        HEADER_SLOT_H = 50   # header (+ optional "hidden" caption) — the Edit toggle is shared, above (below the selected_date)
        ROUND_SLOT_H = 180   # one round's inputs/scores (2 side-by-side rows)
        st.markdown(f"""
        <style>
            div[class*="st-key-hdr_box_"] {{ min-height: {HEADER_SLOT_H}px; }}
            div[class*="st-key-round_box_"] {{ min-height: {ROUND_SLOT_H}px; }}
        </style>
        """, unsafe_allow_html=True)

        # The whole editable Michael / Sarah / Community block is one
        # fragment: editing any score/year/distance field here only reruns
        # and re-renders these three columns — not the Actuals grid, the
        # momentum boxes, or the data pipeline. Cross-fragment outputs go
        # through session_state; the shared Submit button (outside every
        # fragment) does a full rerun that rebuilds them from scratch.
        @st.fragment
        def _msc_editor():
            michael_col, sarah_col, community_col = st.columns([1, 1, 1])

            # Once submitted and not editing, the consolidated score box below already
            # names the player/community right at its top — a section title above it
            # would just be redundant, so skip it in that state. View mode always
            # shows the consolidated box (generate_community_html falls back to
            # "???" placeholders on its own if Community hasn't submitted yet),
            # matching the player boxes — this keeps a submit button available
            # whenever these fields are actually shown as editable.
            community_fields_disabled = not edit_community and not date_rows.empty

            for col, p_name in [(michael_col, "Michael"), (sarah_col, "Sarah")]:
                with col, st.container(key=f"hdr_box_{p_name}_{selected_date}", border=False):
                    st_state = p_state[p_name]
                    # View mode always shows the consolidated box — generate_player_html
                    # falls back to "???" placeholders on its own for whatever this
                    # player hasn't submitted (a few rounds, the whole day, or a day
                    # where only the opponent has played so far), and keeps the round
                    # flags as UN flags until both players have completed the round.
                    show_consolidated_box = not st_state['edit'] and not date_rows.empty
                    if not show_consolidated_box:
                        p_color = "#221e8f" if p_name == "Michael" else "#8a005c"
                        st.markdown(f'<div class="section-title" style="color:{p_color};">{p_name}</div>', unsafe_allow_html=True)

            with community_col, st.container(key=f"hdr_box_community_{selected_date}", border=False):
                if not community_fields_disabled:
                    st.markdown('<div class="section-title" style="color:#6c757d;">Community</div>', unsafe_allow_html=True)

            # --- PLAYER ROUNDS (each column loops its own 5 rounds, one fixed-height slot per round) ---
            community_round_input = {}

            for col, p_name in [(michael_col, "Michael"), (sarah_col, "Sarah")]:
                with col:
                    st_state = p_state[p_name]
                    # Reset per fragment run — this loop re-accumulates comp_tot
                    # and rebuilds input from the current widget values, and a
                    # fragment-only rerun would otherwise stack on the last run.
                    st_state['comp_tot'] = 0
                    st_state['input'] = {}
                    show_consolidated_box = not st_state['edit'] and not date_rows.empty
                    if show_consolidated_box:
                        other = "Sarah" if p_name == "Michael" else "Michael"
                        my_total = row_for_stats.get(f"{p_name} Total Score") if row_for_stats is not None else None
                        other_total = row_for_stats.get(f"{other} Total Score") if row_for_stats is not None else None
                        highlight = pd.notna(my_total) and pd.notna(other_total) and my_total > other_total
                        box_html = generate_player_html(p_name, date_rows, ["Michael", "Sarah"], highlight=highlight)
                        components_html(f'{DAILY_SNAPSHOT_CSS}{box_html}', height=450, scrolling=True)
                        continue
                    for r in range(1, 6):
                      with st.container(key=f"round_box_{p_name}_{r}_{selected_date}", border=True):
                        d_dist, d_year = "", ""

                        if st_state['has_g']:
                            r_row = st_state['curr'][st_state['curr']['Timeguessr Round'] == r]
                            if not r_row.empty:
                                rw = r_row.iloc[0]
                                dist_raw = rw.get(f'{p_name} Geography Distance')
                                if pd.notna(dist_raw):
                                    d_dist = f"{float(dist_raw)/0.3048:.0f} ft"
                                time_raw = rw.get(f'{p_name} Time Guessed')
                                if pd.notna(time_raw): d_year = str(int(time_raw))

                        d_key = f"d_{p_name}_{r}_{selected_date}"
                        y_key = f"y_{p_name}_{r}_{selected_date}"

                        st.markdown(f'<p style="text-align:center; font-weight:700;">Round {r}</p>', unsafe_allow_html=True)

                        # Pre-calculate scores from session state before rendering widgets
                        g_score_disp = None
                        d_meters_calc = 0
                        current_dist_val = st.session_state.get(d_key, d_dist)
                        current_dist_num, current_unit = parse_distance_input(current_dist_val)
                        has_dist_val = current_dist_num is not None
                        dist_unit_missing = has_dist_val and current_unit is None
                        if has_dist_val and current_unit is not None:
                            if current_dist_num >= 0:
                                d_meters_calc = distance_to_meters(current_dist_num, current_unit)
                                g_score_disp = geography_score(d_meters_calc)
                                st_state['comp_tot'] += g_score_disp

                        t_score_disp = None
                        year_int = None
                        y_valid = False
                        act_y = None
                        current_year_val = st.session_state.get(y_key, d_year)
                        has_year_val = bool(current_year_val and str(current_year_val).strip())
                        if has_year_val:
                            if current_year_val.isdigit() and len(current_year_val) == 4:
                                y_val = int(current_year_val)
                                if 1900 <= y_val <= selected_date.year:
                                    y_valid = True
                                    year_int = y_val
                                    if r in actual_rounds_data and actual_rounds_data.get(r, {}).get('year_valid'):
                                        act_y = int(actual_rounds_data[r]['year'])
                                    if act_y:
                                        t_score_disp = calculate_time_score(y_val, act_y)
                                        st_state['comp_tot'] += t_score_disp

                        submitted = st_state['has_g'] and not st_state['edit']
                        p_color = "#221e8f" if p_name == "Michael" else "#8a005c"
                        p_bg = "#dde5eb" if p_name == "Michael" else "#edd3df"

                        if submitted:
                            year_val_in = d_year
                            dist_val = d_dist

                            time_txt = f"{t_score_disp:.0f}" if t_score_disp is not None else ("?" if y_valid else "—")
                            geo_txt = f"{g_score_disp:.0f}" if g_score_disp is not None else "—"

                            st.markdown(f'''<div style="background:{p_bg}; border-radius:10px; padding:10px 14px; border-left:4px solid {p_color}; box-shadow:0 2px 6px rgba(0,0,0,0.1); margin-top:2px;">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                <span style="color:#444; font-size:0.9em;">📅 {d_year or "—"}</span>
                <span style="color:{p_color}; background-color:{p_bg}; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{time_txt}</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px;">
                <span style="color:#444; font-size:0.9em;">🌎 {d_dist or "—"}</span>
                <span style="color:{p_color}; background-color:{p_bg}; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{geo_txt}</span>
            </div>
        </div>''', unsafe_allow_html=True)
                        else:
                            show_time_box = has_year_val and (t_score_disp is not None or y_valid)
                            if show_time_box:
                                yr_col, ts_col = st.columns(2)
                            else:
                                yr_col = ts_col = st.container()
                            with yr_col:
                                year_val_in = st.text_input("Year", value=d_year, key=y_key)
                            if show_time_box:
                                with ts_col:
                                    c_color = "#221e8f" if p_name == "Michael" else "#8a005c"
                                    c_bg = "#dde5eb" if p_name == "Michael" else "#edd3df"
                                    if t_score_disp is not None:
                                        st.markdown(f'<div style="margin-top: 0px;"><label style="margin-bottom: 6px; display: block;"><p style="font-size: 14px; margin: 0; padding: 0;">Score</p></label><div class="score-box" style="background-color:{c_bg}; color:{c_color}; border-left:5px solid {c_color};">📅 {t_score_disp:.0f}</div></div>', unsafe_allow_html=True)
                                    elif y_valid:
                                        st.markdown(f'<div style="margin-top: 0px;"><label style="margin-bottom: 6px; display: block;"><p style="font-size: 14px; margin: 0; padding: 0;">Score</p></label><div class="score-box" style="background-color:#bcb0ff; color:#221e8f; border-left:5px solid #221e8f;" title="Submit actuals to see score">📅 ?</div></div>', unsafe_allow_html=True)

                            show_geo_box = has_dist_val and g_score_disp is not None
                            if show_geo_box:
                                dist_col, gs_col = st.columns(2)
                            else:
                                dist_col = gs_col = st.container()
                            with dist_col:
                                dist_val = st.text_input("Distance", value=d_dist, key=d_key)
                                if dist_unit_missing:
                                    st.caption("⚠️ Include a unit: ft, mi, m, or km")
                            if show_geo_box:
                                with gs_col:
                                    c_color = "#221e8f" if p_name == "Michael" else "#8a005c"
                                    c_bg = "#dde5eb" if p_name == "Michael" else "#edd3df"
                                    st.markdown(f'<div style="margin-top: 0px;"><label style="margin-bottom: 6px; display: block;"><p style="font-size: 14px; margin: 0; padding: 0;">Score</p></label><div class="score-box" style="background-color:{c_bg}; color:{c_color}; border-left:5px solid {c_color};">🌎 {g_score_disp:.0f}</div></div>', unsafe_allow_html=True)

                        st_state['input'][r] = {
                            'dist_raw': dist_val, 'dist_value': current_dist_num, 'unit': current_unit,
                            'dist_m': d_meters_calc,
                            'year': year_val_in, 'year_int': year_int, 'y_valid': y_valid,
                            'g_score': g_score_disp
                        }

            # --- COMMUNITY ROUNDS ---
            with community_col:
              if community_fields_disabled:
                box_html = generate_community_html(date_rows)
                components_html(f'{DAILY_SNAPSHOT_CSS}{box_html}', height=450, scrolling=True)
              else:
                for r in range(1, 6):
                  with st.container(key=f"round_box_community_{r}_{selected_date}", border=True):
                    st.markdown(f'<p style="text-align:center; font-weight:700;">Round {r}</p>', unsafe_allow_html=True)
                    row_r_df = date_rows[date_rows["Timeguessr Round"] == r]
                    row_r = row_r_df.iloc[0] if not row_r_df.empty else None

                    def_c_score = "" if row_r is None or pd.isna(row_r.get("Community Round Score")) else f"{row_r.get('Community Round Score'):g}"
                    def_c_time = "" if row_r is None or pd.isna(row_r.get("Community Time Distance")) else f"{row_r.get('Community Time Distance'):g}"

                    c_unit_key = f"cu_{r}_{selected_date}"
                    last_c_unit = st.session_state.get(c_unit_key, "mi")
                    if last_c_unit not in ["ft", "mi", "m", "km"]:
                        last_c_unit = "mi"
                    def_c_dist = ""
                    if row_r is not None and pd.notna(row_r.get("Community Geography Distance")):
                        cval = float(row_r.get("Community Geography Distance"))
                        if last_c_unit == "km":  def_c_dist = f"{cval/1000:.3f} km"
                        elif last_c_unit == "mi": def_c_dist = f"{cval/1609.344:.3f} mi"
                        elif last_c_unit == "ft": def_c_dist = f"{cval/0.3048:.0f} ft"
                        else:                     def_c_dist = f"{cval:.0f} m"

                    if community_fields_disabled:
                        c_score_in, c_time_in, c_dist_in = def_c_score, def_c_time, def_c_dist

                        # Estimated scores derived from the average years-off/distance, purely for
                        # display — NOT the true community average (that would require averaging
                        # individual scores, not scoring the averaged inputs), so shown in quotes
                        # and never saved anywhere.
                        time_est_txt = "—"
                        if def_c_time:
                            try:
                                time_est = calculate_time_score(float(def_c_time), 0)
                                if time_est is not None:
                                    time_est_txt = f'"{time_est:,.0f}"'
                            except ValueError:
                                pass

                        geo_est_txt = "—"
                        dist_val_parsed, dist_unit_parsed = parse_distance_input(def_c_dist, default_unit="mi")
                        if dist_val_parsed is not None and dist_unit_parsed is not None:
                            geo_est_txt = f'"{geography_score(distance_to_meters(dist_val_parsed, dist_unit_parsed)):,.0f}"'

                        st.markdown(f'''<div style="background:#eef0f2; border-radius:10px; padding:10px 14px; border-left:4px solid #6c757d; box-shadow:0 2px 6px rgba(0,0,0,0.08); margin-top:2px;">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                <span style="color:#444; font-size:0.9em;">🏆 Score</span>
                <span style="color:#495057; background-color:#e9ecef; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{def_c_score or "—"}</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px;">
                <span style="color:#444; font-size:0.9em;">📅 {def_c_time or "—"}</span>
                <span style="color:#495057; background-color:#e9ecef; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{time_est_txt}</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px;">
                <span style="color:#444; font-size:0.9em;">🌎 {def_c_dist or "—"}</span>
                <span style="color:#495057; background-color:#e9ecef; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{geo_est_txt}</span>
            </div>
        </div>''', unsafe_allow_html=True)
                    else:
                        c_score_in = st.text_input("Score", value=def_c_score, key=f"cs_{r}_{selected_date}")
                        ctd1, ctd2 = st.columns(2)
                        c_time_in = ctd1.text_input("Time", value=def_c_time, key=f"ct_{r}_{selected_date}")
                        c_dist_in = ctd2.text_input("Distance", value=def_c_dist, key=f"cd_{r}_{selected_date}")
                        # A bare number (no unit typed) is assumed to be miles —
                        # TimeGuessr's own community-average display is in miles,
                        # so that's what's almost always being copied in here.
                        _, c_dist_unit = parse_distance_input(c_dist_in, default_unit="mi")
                        if c_dist_in.strip() and c_dist_unit is None:
                            st.caption("⚠️ Unrecognized unit — use ft, mi, m, or km (or leave it off for miles)")
                        if c_dist_unit is not None:
                            st.session_state[c_unit_key] = c_dist_unit

                    community_round_input[r] = {'score': c_score_in, 'time': c_time_in, 'dist': c_dist_in}
            st.session_state['_comm_rounds'] = community_round_input

            # --- FOOTER (within each column) ---
            for col, p_name in [(michael_col, "Michael"), (sarah_col, "Sarah")]:
                with col:
                    st_state = p_state[p_name]
                    fields_disabled = st_state['has_g'] and not st_state['edit']
                    # Once the consolidated score box above is shown (view mode), it
                    # already covers everything — the Computed Total / Total Score /
                    # Percentile boxes here would just be redundant (and, for a player
                    # who never played, would otherwise show up as stray editable
                    # inputs), so skip them entirely in that case.
                    show_consolidated_box = not st_state['edit'] and not date_rows.empty
                    hide_footer_boxes = show_consolidated_box
                    if not hide_footer_boxes:
                        st.markdown("---")
                    with st.container():
                        if not hide_footer_boxes:
                            ct1, ct2 = st.columns([1, 1])
                            with ct1: st.markdown(f"**Computed Total**")
                            with ct2:
                                c_color = "#221e8f" if p_name == "Michael" else "#8a005c"
                                c_bg = "#dde5eb" if p_name == "Michael" else "#edd3df"
                                st.markdown(f'<div class="score-box" style="background-color:{c_bg}; color:{c_color}; border-left:5px solid {c_color};">{int(st_state["comp_tot"]):,}</div>', unsafe_allow_html=True)

                        pct_key = f"pct_{p_name}_{selected_date}_real"
                        yrs_key = f"yrs_{p_name}_{selected_date}_real"
                        loc_key = f"loc_{p_name}_{selected_date}_real"
                        ts_key = f"ts_{p_name}_{selected_date}_real"

                        def _stat_default(col, mult=1):
                            if row_for_stats is None: return ""
                            v = row_for_stats.get(col)
                            return "" if pd.isna(v) else f"{v * mult:g}"

                        if hide_footer_boxes:
                            total_input = st_state['def_total']
                        elif fields_disabled:
                            tt1, tt2 = st.columns([1, 1])
                            with tt1: st.markdown(f"**Total Score**")
                            with tt2:
                                ts_display = st_state['def_total'] or "—"
                                st.markdown(f'<div class="score-box" style="background-color:{c_bg}; color:{c_color}; border-left:5px solid {c_color};">{ts_display}</div>', unsafe_allow_html=True)
                            total_input = st_state['def_total']
                        else:
                            total_input = st.text_input("Total Score", value=st_state['def_total'], key=ts_key)

                        if hide_footer_boxes:
                            pct_in = _stat_default(f"{p_name} Percentile", 100)
                            yrs_in = _stat_default(f"{p_name} Years")
                            loc_in = _stat_default(f"{p_name} Location")
                        elif fields_disabled:
                            pct_val = _stat_default(f"{p_name} Percentile", 100) or "—"
                            yrs_val = _stat_default(f"{p_name} Years") or "—"
                            loc_val = _stat_default(f"{p_name} Location") or "—"
                            st.markdown(f'''<div style="background:{c_bg}; border-radius:10px; padding:10px 14px; border-left:4px solid {c_color}; box-shadow:0 2px 6px rgba(0,0,0,0.1); margin-top:2px;">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                <span style="color:#444; font-size:0.9em;">Percentile</span>
                <span style="color:{c_color}; background-color:{c_bg}; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{pct_val}</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px;">
                <span style="color:#444; font-size:0.9em;">Years</span>
                <span style="color:{c_color}; background-color:{c_bg}; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{yrs_val}</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px;">
                <span style="color:#444; font-size:0.9em;">Location</span>
                <span style="color:{c_color}; background-color:{c_bg}; font-weight:700; font-size:0.9em; padding:1px 8px; border-radius:6px; white-space:nowrap;">{loc_val}</span>
            </div>
        </div>''', unsafe_allow_html=True)
                            pct_in = _stat_default(f"{p_name} Percentile", 100)
                            yrs_in = _stat_default(f"{p_name} Years")
                            loc_in = _stat_default(f"{p_name} Location")
                        else:
                            pc1, pc2, pc3 = st.columns(3)
                            pct_in = pc1.text_input("Percentile", value=_stat_default(f"{p_name} Percentile", 100), key=pct_key)
                            yrs_in = pc2.text_input("Years", value=_stat_default(f"{p_name} Years"), key=yrs_key)
                            loc_in = pc3.text_input("Location", value=_stat_default(f"{p_name} Location"), key=loc_key)

                        # Stashed for the single shared Submit button below (each player's own
                        # widget values, looked up by name rather than captured by closure).
                        st_state['total_input'] = total_input
                        st_state['pct_in'] = pct_in
                        st_state['yrs_in'] = yrs_in
                        st_state['loc_in'] = loc_in

            with community_col:
                # Once fully submitted and not editing, the consolidated score box above
                # already shows everything — these boxes would just be redundant.
                if not community_fields_disabled:
                    st.markdown("---")

                def _to_float_c(s):
                    s = (s or "").strip()
                    if not s: return None
                    try: return float(s)
                    except ValueError: return None

                community_comp_tot = sum(
                    v for v in (_to_float_c(community_round_input.get(r, {}).get('score')) for r in range(1, 6))
                    if v is not None
                )

                if not community_fields_disabled:
                    cct1, cct2 = st.columns([1, 1])
                    with cct1: st.markdown(f"**Computed Total**")
                    with cct2:
                        st.markdown(f'<div class="score-box" style="background-color:#e9ecef; color:#495057; border-left:5px solid #6c757d;">{int(community_comp_tot):,}</div>', unsafe_allow_html=True)

                def_c_avg = "" if row_for_stats is None or pd.isna(row_for_stats.get("Community Average")) else f"{row_for_stats.get('Community Average'):g}"
                def_c_yrs = "" if row_for_stats is None or pd.isna(row_for_stats.get("Community Years Average")) else f"{row_for_stats.get('Community Years Average'):g}"
                def_c_loc = "" if row_for_stats is None or pd.isna(row_for_stats.get("Community Location Average")) else f"{row_for_stats.get('Community Location Average'):g}"

                if community_fields_disabled:
                    c_avg_in, c_yrs_in, c_loc_in = def_c_avg, def_c_yrs, def_c_loc
                else:
                    c_avg_in = st.text_input("Average Score", value=def_c_avg, key=f"cavg_{selected_date}")
                    cf1, cf2 = st.columns(2)
                    c_yrs_in = cf1.text_input("Years Average", value=def_c_yrs, key=f"cyrs_{selected_date}")
                    c_loc_in = cf2.text_input("Location Average", value=def_c_loc, key=f"cloc_{selected_date}")

                # Stashed for the single shared Submit button below.
                st.session_state['_comm_stats'] = {'avg': c_avg_in, 'yrs': c_yrs_in, 'loc': c_loc_in}

        _msc_editor()
        community_round_input = st.session_state.get('_comm_rounds', {})
        community_stats_input = st.session_state.get('_comm_stats', {'avg': '', 'yrs': '', 'loc': ''})

        # Submitted & not editing: the Actuals box goes below the Michael / Sarah /
        # Community boxes instead of above them. While editing, it stays in its
        # original spot above (rendered earlier, ordering left untouched).
        if actuals_box_html is not None:
            st.markdown(actuals_box_html, unsafe_allow_html=True)

        # --- Single shared Submit button for the whole page ---
        def _to_float_generic(s):
            s = (s or "").strip()
            if not s: return None
            try: return float(s)
            except ValueError: return None

        def submit_actuals():
            if not all_valid_act:
                st.error("Actuals: Invalid or incomplete round data")
                return False
            try:
                f_df = act_df[act_df['Timeguessr Day'] != timeguessr_day]
                f_df = pd.concat([f_df, pd.DataFrame(save_rows_act)], ignore_index=True)
                f_df.sort_values(['Timeguessr Day', 'Timeguessr Round']).to_csv(act_path, index=False)
                return True
            except Exception as e:
                st.error(f"Actuals: Save failed: {e}")
                return False

        def submit_player(p_name):
            st_state = p_state[p_name]
            total_val = _to_float_generic(st_state['total_input'])
            if total_val is None:
                st.error(f"{p_name}: Missing Total Score"); return False
            ts_val = int(round(total_val))

            if abs(ts_val - st_state['comp_tot']) > 10:
                st.error(f"{p_name}: Computed total ({int(st_state['comp_tot']):,}) differs from Total Score ({ts_val:,}) by more than 10 points.")
                return False

            new_rows = []
            for r in range(1, 6):
                d = st_state['input'][r]
                if not d['dist_raw'] or not d['year']:
                    st.error(f"{p_name}: Round {r} incomplete"); return False
                if not d['y_valid']:
                    st.error(f"{p_name}: Round {r} invalid year"); return False
                if d['dist_value'] is None or d['unit'] is None:
                    st.error(f"{p_name}: Round {r}: Enter a distance with a unit (ft, mi, m, or km)"); return False
                if d['dist_value'] < 0:
                    st.error(f"{p_name}: Round {r} negative distance"); return False

                act_y = actual_rounds_data.get(r, {}).get('year')

                t_dist = np.nan
                t_score = np.nan
                r_score = np.nan

                if act_y:
                    t_dist = abs(d['year_int'] - int(act_y))
                    t_score = calculate_time_score(d['year_int'], int(act_y))

                if pd.notna(t_score) and pd.notna(d['g_score']):
                    r_score = t_score + d['g_score']

                new_rows.append({
                    "Timeguessr Day": int(timeguessr_day),
                    "Timeguessr Round": int(r),
                    f"{p_name} Total Score": ts_val,
                    f"{p_name} Round Score": r_score,
                    f"{p_name} Geography Distance": int(d['dist_m']),
                    f"{p_name} Time Guessed": int(d['year_int']),
                    f"{p_name} Time Distance": t_dist,
                    f"{p_name} Geography Score": d['g_score'],
                    f"{p_name} Geography Score (Min)": d['g_score'],
                    f"{p_name} Geography Score (Max)": d['g_score'],
                    f"{p_name} Time Score": t_score,
                    f"{p_name} Time Score (Min)": t_score,
                    f"{p_name} Time Score (Max)": t_score,
                })

            try:
                df_out = st_state['df'][st_state['df']['Timeguessr Day'] != timeguessr_day]
                df_out = pd.concat([df_out, pd.DataFrame(new_rows)], ignore_index=True)
                df_out.sort_values(['Timeguessr Day', 'Timeguessr Round']).to_csv(st_state['csv'], index=False)

                update_averages_csv_entry(
                    timeguessr_day, p_name,
                    percentile=_to_float_generic(st_state['pct_in']),
                    years=_to_float_generic(st_state['yrs_in']),
                    location=_to_float_generic(st_state['loc_in']),
                )
                return True
            except Exception as e:
                st.error(f"{p_name}: Save failed: {e}")
                return False

        def submit_community():
            rounds_payload = {}
            for r in range(1, 6):
                ci = community_round_input.get(r, {})
                dval, dunit = parse_distance_input(ci.get('dist', ''), default_unit="mi")
                geo_m = distance_to_meters(dval, dunit) if (dval is not None and dunit is not None) else None
                rounds_payload[r] = {
                    'score': _to_float_generic(ci.get('score')),
                    'time': _to_float_generic(ci.get('time')),
                    'geo_m': geo_m,
                }

            avg_val = _to_float_generic(community_stats_input['avg'])
            round_scores = [rounds_payload[r]['score'] for r in range(1, 6)]
            round_sum = sum(s for s in round_scores if s is not None)

            if avg_val is not None and all(s is not None for s in round_scores) and abs(round_sum - avg_val) > 10:
                st.error(f"Community: Sum of round scores ({round_sum:,.0f}) differs from Average ({avg_val:,.0f}) by more than 10 points.")
                return False

            try:
                update_community_averages_csv_entry(
                    timeguessr_day,
                    average=avg_val,
                    years_average=_to_float_generic(community_stats_input['yrs']),
                    location_average=_to_float_generic(community_stats_input['loc']),
                    rounds=rounds_payload,
                )
                return True
            except Exception as e:
                st.error(f"Community: Save failed: {e}")
                return False

        # Eligible to submit only if this player actually went through the
        # editable round-input path: either the global toggle is in Edit mode
        # (always re-enterable there), or — the rare case where nothing exists
        # for this day at all — they were shown input fields by default. A
        # player just viewed as a "???" placeholder box (missing data on a day
        # someone else already completed) has no populated round inputs to
        # submit, and must switch to Edit to fill them in.
        submit_players = [
            p for p in ["Michael", "Sarah"]
            if p_state[p]['edit'] or (date_rows.empty and not p_state[p]['has_g'])
        ]

        if edit_act or submit_players or edit_community:
            st.markdown("---")
            if st.button("Submit All", key=f"sub_all_{selected_date}", use_container_width=True):
                any_success = False
                if edit_act:
                    if submit_actuals():
                        any_success = True
                for p_name in submit_players:
                    if submit_player(p_name):
                        any_success = True
                if edit_community:
                    if submit_community():
                        any_success = True
                if any_success:
                    st.session_state[f"_exit_edit_page_{selected_date}"] = True
                    st.success("Saved!")
                    st.rerun()

    st.markdown('<a href="#top" class="back-to-top">↑</a>', unsafe_allow_html=True)

    # --- MIDDLE: Total / Time / Geo momentum boxes, each with its M/S/C bars ---
    # Averages/streaks/score-runs reflect the state as of the selected date —
    # if that date hasn't been completed (no row for it yet, since df_t/df_tm/df_g
    # only contain days both players have submitted), this naturally falls back
    # to the most recent completed date before it.
    df_t_asof = df_t[df_t["Date"] <= sel_ts]
    df_tm_asof = df_tm[df_tm["Date"] <= sel_ts]
    df_g_asof = df_g[df_g["Date"] <= sel_ts]
    st.markdown(render_forecast_section([get_full_category_forecast(df_t_asof, "Total Score"), get_full_category_forecast(df_tm_asof, "Time Score"), get_full_category_forecast(df_g_asof, "Geography Score")], bars_by_cat), unsafe_allow_html=True)

    # --- BOTTOM: Round-by-round recap, then Updates (separate boxes) for the selected date ---
    if sel_ts in sd_set:
        round_card, updates_card = render_daily_news(sel_ts, ev_d.get(sel_ts, []), round_updates.get(sel_ts, []))
        feed_html = f'<div class="news-container">\n{round_card}\n{updates_card}\n</div>'
        st.markdown(feed_html, unsafe_allow_html=True)
    else:
        st.markdown('<div class="news-container"><div style="text-align:center; padding:50px; color:#666; font-size: 18px;">No news events for this date.</div></div>', unsafe_allow_html=True)

else: st.warning("Please ensure 'Timeguessr_Stats.csv' is in the 'Data' folder.")