import streamlit as st
import base64
from PIL import Image

def get_base64_image(image_path):
    """
    Encodes an image to a Base64 string, using its detected format (e.g., PNG or JPEG) 
    when saving to the in-memory buffer.

    Args:
        image_path (str): Path to the image file (e.g., "Images/Sarah.jpg").

    Returns:
        str or None: The Base64 encoded string, or None if the file is not found.
    """
    try:
        # Open the image using PIL
        img = Image.open(image_path)
        
        # Determine the saving format. PIL reports 'JPEG' for .jpg/.jpeg files 
        # and 'PNG' for .png files. We use the detected format.
        file_format = img.format if img.format is not None else 'PNG'
        
        buffer = io.BytesIO()
        # Save the image into the buffer using its original format
        img.save(buffer, format=file_format)
        
        # Encode the buffer content to Base64
        return base64.b64encode(buffer.getvalue()).decode()
        
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None
    except Exception as e:
        print(f"An error occurred during image processing: {e}")
        return None

def set_lighter_background_image(base64_string, lightness_level=0.7):
    """
    Injects CSS to set the background image and applies a semi-transparent 
    white overlay using linear-gradient to make the image appear lighter.

    Args:
        base64_string (str): The Base64 encoded image string.
        lightness_level (float): The transparency/lightness of the white overlay (0.0=no overlay, 1.0=pure white).
    """
    if not base64_string:
        st.error("Could not load image for background.")
        return

    # Calculate the alpha value for the RGBA overlay
    # We use lightness_level for the alpha (A) component of RGBA(R, G, B, A)
    # The 'white' color is represented by 255, 255, 255
    rgba_overlay = f"rgba(255, 255, 255, {lightness_level})"

    css = f"""
    <style>
    .stApp {{
        /* Use linear-gradient to layer a semi-transparent white color over the image. */
        background-image: linear-gradient({rgba_overlay}, {rgba_overlay}), 
                          url("data:image/png;base64,{base64_string}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# --- Main Streamlit Script ---
import io

image_file_path = "Images/Sarah2.png"

# 1. Get the base64 string
base64_img = get_base64_image(image_file_path)

# 2. Inject the CSS with a 70% lightness overlay
# Try adjusting the second argument (e.g., 0.3 for slightly lighter, 0.9 for very light)
set_lighter_background_image(base64_img, lightness_level=0.7)

import streamlit as st
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import os
from streamlit.components.v1 import html as components_html
from Score_Update import score_update
import pycountry
import emoji
import json
with open("config.json") as f:
    config = json.load(f)

st.title("Score Submission")

score_update()

# Helper function to validate distance against geography pattern
def validate_distance_pattern(dist_meters, geo_pattern, round_num, is_km):
    patterns = {
        "OOO": (0, 50), "OO%": (50, 37500), "OOX": (37500, 100000),
        "O%X": (100000, 250000), "OXX": (250000, 1000000),
        "%XX": (1000000, 2000000), "XXX": (2000000, float('inf'))
    }
    if geo_pattern not in patterns:
        return (True, "")
    low, high = patterns[geo_pattern]
    if geo_pattern == "OOO":
        if dist_meters <= high:
            return (True, "")
        excess = dist_meters - high
        unit = f"{excess/1000:.3f} km" if is_km else f"{excess} m"
        return (False, f"Round {round_num}: Distance is {unit} too great (🟩🟩🟩 requires ≤ 50 m)")
    elif geo_pattern == "XXX":
        if dist_meters > low:
            return (True, "")
        deficit = low - dist_meters + 1
        unit = f"{deficit/1000:.3f} km" if is_km else f"{deficit} m"
        return (False, f"Round {round_num}: Distance is {unit} too few (⬛⬛⬛ requires > 2000 km)")
    else:
        if low < dist_meters <= high:
            return (True, "")
        elif dist_meters <= low:
            deficit = low - dist_meters + 1
            unit = f"{deficit/1000:.3f} km" if is_km else f"{deficit} m"
            return (False, f"Round {round_num}: Distance is {unit} too few")
        else:
            excess = dist_meters - high
            unit = f"{excess/1000:.3f} km" if is_km else f"{excess} m"
            return (False, f"Round {round_num}: Distance is {unit} too great")

# Create two columns - left for inputs, right for score display
input_col, score_col = st.columns([1.25, 2])

with input_col:
    # Top section - Name and Date only
    date = st.date_input(
        "Date",
        value=datetime.date.today(),
        max_value=datetime.date.today()
    )

    name = st.selectbox("Name", ["", "Michael", "Sarah"], format_func=lambda x: "Select..." if x == "" else x)

    name_valid = name in ["Michael", "Sarah"]

# Display score summary if date is selected
with score_col:
    st.markdown(
        """
        <style>
            .score-container {
                text-align: center;
                background-color: #fff;
                padding: 15px 0 5px 0;
                margin-top: -25px; /* moves section up */
                border-radius: 12px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                width: 100%;
            }
            .score-header {
                font-size: 26px !important;
                font-weight: 800 !important;
                margin-bottom: 6px !important;
                color: #333 !important;
            }
            .score-total {
                font-size: 24px !important;
                color: #db5049 !important;
                font-weight: 800 !important;
                margin-bottom: 8px !important;
            }
            .score-sub {
                font-size: 20px !important;
                color: #555 !important;
                margin-bottom: 6px !important;
            }
            .round-row {
                font-size: 18px !important;
                margin: 8px 0 !important;
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
                gap: 16px !important;
            }
            .bar {
                width: 180px !important;
                height: 14px !important;
                border-radius: 8px !important;
                background-color: #b0afaa !important;
                overflow: hidden !important;
                position: relative !important;
            }
            .bar-fill {
                height: 100% !important;
                background-color: #db5049 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if date:
        try:
            df = pd.read_csv("./Data/Timeguessr_Stats.csv")
            df["Date"] = pd.to_datetime(df["Date"]).dt.date

            date_rows = df[df["Date"] == date]
            if len(date_rows) > 0:
                timeguessr_day = date_rows.iloc[0]["Timeguessr Day"]
                
                # Get scores for both players
                michael_total = date_rows.iloc[0]["Michael Total Score"]
                sarah_total = date_rows.iloc[0]["Sarah Total Score"]
                
                # Determine order (higher score on left)
                michael_score_val = 0 if pd.isna(michael_total) else michael_total
                sarah_score_val = 0 if pd.isna(sarah_total) else sarah_total
                
                if michael_score_val >= sarah_score_val:
                    players = ["Michael", "Sarah"]
                else:
                    players = ["Sarah", "Michael"]

                # Common country name aliases
                COUNTRY_ALIASES = {
                    "Russia": "Russian Federation",
                    "Ivory Coast": "Côte d'Ivoire",
                    "South Korea": "Korea, Republic of",
                    "North Korea": "Korea, Democratic People's Republic of",
                    "Vietnam": "Viet Nam",
                    "Syria": "Syrian Arab Republic",
                    "Laos": "Lao People's Democratic Republic",
                    "Bolivia": "Bolivia, Plurinational State of",
                    "Venezuela": "Venezuela, Bolivarian Republic of",
                    "Iran": "Iran, Islamic Republic of",
                    "Moldova": "Moldova, Republic of",
                    "Tanzania": "Tanzania, United Republic of",
                    "Palestine": "Palestine, State of",
                    "Brunei": "Brunei Darussalam",
                    "Congo": "Congo, Republic of the",
                    "Democratic Republic of the Congo": "Congo, The Democratic Republic of the",
                    "Macau": "Macao",
                    "Taiwan": "Taiwan, Province of China",
                    "Cape Verde": "Cabo Verde",
                    "Vatican City": "Holy See (Vatican City State)",
                    "Turkey": "Türkiye",
                    "Bosnia": "Bosnia and Herzegovina",
                }

                def get_flag_emoji(country_name):
                    """Return an HTML <img> tag with the correct Twemoji flag, or 🇺🇳 fallback."""
                    if not country_name or pd.isna(country_name):
                        return '<img src="https://twemoji.maxcdn.com/v/latest/svg/1f1fa-1f1f3.svg" width="20" style="vertical-align:middle;"/>'

                    name_str = country_name.strip()
                    if name_str in COUNTRY_ALIASES:
                        name_str = COUNTRY_ALIASES[name_str]

                    try:
                        country = pycountry.countries.lookup(name_str)
                        code = country.alpha_2.upper()
                        codepoints = "-".join([f"1f1{format(ord(c) - ord('A') + 0xE6, 'x')}" for c in code])
                        return f'<img src="https://twemoji.maxcdn.com/v/latest/svg/{codepoints}.svg" width="20" style="vertical-align:middle;"/>'
                    except LookupError:
                        return '<img src="https://twemoji.maxcdn.com/v/latest/svg/1f1fa-1f1f3.svg" width="20" style="vertical-align:middle;"/>'

                GEOGRAPHY_RANGES = {
                    "OOO": (5000, 5000),
                    "OO%": (4750, 4999),
                    "OOX": (4500, 4749),
                    "O%X": (4250, 4499),
                    "OXX": (3500, 4249),
                    "%XX": (2500, 3499),
                    "XXX": (0, 2499)
                }

                TIME_RANGES = {
                    "OOO": (5000, 5000),
                    "OO%": (4800, 4950),
                    "OOX": (4300, 4600),
                    "O%X": (3400, 3900),
                    "OXX": (2000, 2500),
                    "%XX": (1000, 1000),
                    "XXX": (0, 0)
                }

                def half_bar_html(score, pattern=None):
                    """Render red-yellow-grey bar for known or uncertain scores."""
                    total = 5000
                    
                    if score is not None and not pd.isna(score):
                        pct = min(max(float(score) / total * 100.0, 0.0), 100.0)
                        return f'<div class="tg-bar-bg"><div class="tg-bar-fill" style="width:{pct:.2f}%; background:#db5049;"></div></div>'
                    
                    elif pattern and pattern in GEOGRAPHY_RANGES:
                        min_val, max_val = GEOGRAPHY_RANGES[pattern]
                        min_pct = min_val / total * 100
                        max_pct = max_val / total * 100
                        
                        return f'''
                        <div class="tg-bar-bg" style="position:relative;">
                            <div style="position:absolute; left:0; width:{min_pct:.2f}%; height:100%; background:#db5049;"></div>
                            <div style="position:absolute; left:{min_pct:.2f}%; width:{max_pct - min_pct:.2f}%; height:100%; background:#d1d647;"></div>
                            <div style="position:absolute; left:{max_pct:.2f}%; width:{100 - max_pct:.2f}%; height:100%; background:#b0afaa;"></div>
                        </div>
                        '''
                    else:
                        return '<div class="tg-bar-bg"><div class="tg-bar-fill" style="width:0%;"></div></div>'

                def generate_player_html(player_name, highlight=False):
                    """Generate HTML for a single player's score summary."""
                    total_score_col = f"{player_name} Total Score"
                    total_score = date_rows.iloc[0][total_score_col]

                    # Calculate sums using midpoints for unknown scores
                    all_rounds = date_rows[date_rows["Timeguessr Round"].between(1, 5)]
                    geo_score_col = f"{player_name} Geography Score"
                    time_score_col = f"{player_name} Time Score"
                    geo_pattern_col = f"{player_name} Geography"
                    time_pattern_col = f"{player_name} Time"
                    
                    geo_sum = 0
                    time_sum = 0
                    
                    for _, round_row in all_rounds.iterrows():
                        # Geography score
                        geo_score = round_row.get(geo_score_col, None)
                        if pd.notna(geo_score):
                            geo_sum += geo_score
                        else:
                            geo_pattern = round_row.get(geo_pattern_col, None)
                            if geo_pattern in GEOGRAPHY_RANGES:
                                min_val, max_val = GEOGRAPHY_RANGES[geo_pattern]
                                geo_sum += (min_val + max_val) / 2
                        
                        # Time score
                        time_score = round_row.get(time_score_col, None)
                        if pd.notna(time_score):
                            time_sum += time_score
                        else:
                            time_pattern = round_row.get(time_pattern_col, None)
                            if time_pattern in TIME_RANGES:
                                min_val, max_val = TIME_RANGES[time_pattern]
                                time_sum += (min_val + max_val) / 2

                    total_text = "???" if pd.isna(total_score) else f"{int(total_score):,}/50,000"

                    # Add highlight styling if this player is selected
                    container_style = ""
                    if highlight:
                        container_style = "border: 3px solid #db5049; box-shadow: 0 0 15px rgba(219,80,73,0.4);"

                    html_parts = []
                    # Set player-specific color
                    player_color = "#221e8f" if player_name == "Michael" else "#8a005c"
                    background_color = "#dde5eb" if player_name == "Michael" else "#edd3df"
                    
                    html_parts.append(f'''
                    <style>
                    .tg-container-{player_name.lower()} {{
                        position: relative;
                        top: 0px;
                        z-index: 9999;
                        font-family: 'Poppins', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
                        padding: 10px 12px;
                        overflow: visible;
                        box-sizing: border-box;
                        width: 100%;  /* CHANGED: Was max-width: 432px */
                        background-color: {background_color};
                        border-radius: 12px;
                        {container_style}
                    }}
                    .tg-header-{player_name.lower()} {{
                        color:{player_color};
                        font-weight:700;
                        font-size:30px;
                        margin:0 0 5px 0;
                        line-height:1.1;
                    }}
                    .tg-total {{
                        color:#222;
                        font-size:24px;
                        font-weight:600;
                        margin:0 0 7px 0;
                        line-height:1.1;
                    }}
                    .tg-sub {{
                        font-size:20px;
                        margin:0 0 7px 0;
                        line-height:1.1;
                        color:#333;
                    }}
                    .tg-rounds-wrapper {{
                        margin-top:7px;
                    }}
                    .tg-round {{
                        margin:7px 0;
                    }}
                    .tg-round-title {{
                        color:#db5049;
                        font-weight:600;
                        font-size:20px;
                        margin:0 0 7px 0;
                        line-height:1.1;
                    }}
                    .tg-row {{
                        display:flex;
                        gap:12px;
                        align-items:center;
                        flex-wrap:nowrap;
                    }}
                    .tg-half {{
                        width: 50%; /* CHANGED: Slightly increased to fill flex space better */
                        flex: 1;    /* ADDED: Ensures they grow evenly */
                    }}
                    .tg-bar-bg {{
                        background:#b0afaa;
                        border-radius:10px;
                        height:10px;
                        overflow:hidden;
                        width: 100%; /* Ensure bars fill their half */
                    }}
                    .tg-bar-fill {{
                        height:10px;
                        border-radius:10px;
                        background:#db5049;
                    }}
                    .tg-score-note {{
                        font-size:20px;
                        margin:0 0 7px 0;
                        white-space: nowrap; /* Prevent text wrapping weirdly */
                    }}
                    .tg-qq {{
                        color:#db5049;
                        font-weight:700;
                        font-size:19px;
                        margin:7px 0;
                    }}
                    .tg-score-note small {{ color:#444; }}
                    </style>

                    <div class="tg-container-{player_name.lower()}">
                    <div class="tg-header-{player_name.lower()}">{player_name}</div>
                    ''')

                    html_parts.append(f'<div class="tg-total">{total_text}</div>')

                    if geo_sum == 0 and time_sum == 0:
                        html_parts.append('<div class="tg-sub">🌎 Geography: <b>???</b>/25,000</div>')
                        html_parts.append('<div class="tg-sub">📅 Time: <b>???</b>/25,000</div>')
                    else:
                        html_parts.append(f'<div class="tg-sub">🌎 Geography: <b>{int(geo_sum):,}</b>/25,000</div>')
                        html_parts.append(f'<div class="tg-sub">📅 Time: <b>{int(time_sum):,}</b>/25,000</div>')

                    html_parts.append('<div class="tg-rounds-wrapper">')

                    geo_score_col_final = f"{player_name} Geography Score"
                    time_score_col_final = f"{player_name} Time Score"
                    geo_pattern_col_final = f"{player_name} Geography"
                    time_pattern_col_final = f"{player_name} Time"

                    for round_num in range(1, 6):
                        round_data = date_rows[date_rows["Timeguessr Round"] == round_num]
                        
                        if len(round_data) > 0:
                            geo_score = round_data.iloc[0].get(geo_score_col_final, None)
                            time_score = round_data.iloc[0].get(time_score_col_final, None)
                            geo_pattern = round_data.iloc[0].get(geo_pattern_col_final, None)
                            time_pattern = round_data.iloc[0].get(time_pattern_col_final, None)
                            country_name = round_data.iloc[0].get("Country", None)
                        else:
                            geo_score = time_score = geo_pattern = time_pattern = country_name = None

                        # --- CHECK IF ALL PLAYERS HAVE SCORES (UN Flag Logic) ---
                        round_fully_revealed = True
                        if len(round_data) > 0:
                            for p in players:
                                p_check_col = f"{p} Geography Score"
                                p_score = round_data.iloc[0].get(p_check_col, None)
                                if pd.isna(p_score):
                                    round_fully_revealed = False
                                    break
                        else:
                            round_fully_revealed = False

                        if round_fully_revealed:
                            flag = get_flag_emoji(country_name)
                        else:
                            flag = get_flag_emoji("United Nations")
                        # -------------------------------------------------------

                        if pd.isna(geo_score):
                            if geo_pattern in GEOGRAPHY_RANGES:
                                min_val, max_val = GEOGRAPHY_RANGES[geo_pattern]
                                geo_text = f"{min_val:,}-{max_val:,}/5,000"
                            else:
                                geo_text = "???/5,000"
                        else:
                            geo_text = f"{int(geo_score):,}/5,000"

                        if pd.isna(time_score):
                            if time_pattern in TIME_RANGES:
                                min_val, max_val = TIME_RANGES[time_pattern]
                                time_text = f"{min_val:,}-{max_val:,}/5,000"
                            else:
                                time_text = "???/5,000"
                        else:
                            time_text = f"{int(time_score):,}/5,000"

                        geo_html = half_bar_html(geo_score, pattern=geo_pattern if pd.isna(geo_score) else None)
                        time_html = half_bar_html(time_score, pattern=time_pattern if pd.isna(time_score) else None)

                        html_parts.append(f'''
                        <div class="tg-round">
                            <div class="tg-row">
                                <div class="tg-half">
                                    <div class="tg-score-note">{flag} <small>{geo_text}</small></div>
                                    {geo_html}
                                </div>
                                <div class="tg-half">
                                    <div class="tg-score-note">📅 <small>{time_text}</small></div>
                                    {time_html}
                                </div>
                            </div>
                        </div>
                        ''')

                    html_parts.append('</div>')
                    html_parts.append('</div>')
                    return "\n".join(html_parts)

                # Generate HTML for both players
                player1_html = generate_player_html(players[0], highlight=(name_valid and name == players[0]))
                player2_html = generate_player_html(players[1], highlight=(name_valid and name == players[1]))

                # Combine both in a side-by-side layout
                combined_html = f'''
                <style>
                .dual-container {{
                    display: flex;
                    gap: 20px;
                    justify-content: center;
                }}
                </style>
                <div class="dual-container">
                    <div style="flex: 1;">
                        {player1_html}
                    </div>
                    <div style="flex: 1;">
                        {player2_html}
                    </div>
                </div>
                '''

                components_html(combined_html, height=520, scrolling=False)

        except FileNotFoundError:
            pass
        except Exception as e:
            st.error(f"Error loading score data: {e}")


# Check if name and date are filled and valid
if name_valid and date:
    # Convert date to Timeguessr Day
    reference_date = datetime.date(2025, 10, 28)
    timeguessr_day = 880 + (date - reference_date).days
    
    st.divider()
    
    # Load existing data for all rounds
    try:
        actuals_df = pd.read_csv("./Data/Timeguessr_Actuals_Parsed.csv")
    except FileNotFoundError:
        actuals_df = pd.DataFrame()
    
    try:
        guess_df = pd.read_csv(f"./Data/Timeguessr_{name}_Parsed.csv")
    except FileNotFoundError:
        guess_df = pd.DataFrame()
    
    # Create two columns
    col1, col2, col3 = st.columns([1.25, 1, 1])
    
    # Left column - Actual Answers (all 5 rounds)
    with col1:
        st.subheader("Actual Answers")
        
        # --- 1. Initialize the dictionary early to prevent NameError ---
        actual_rounds_data = {} 

        # --- 2. Check if Actuals Exist ---
        any_actual_exists = False
        if not actuals_df.empty:
            for round_num in range(1, 6):
                existing = actuals_df[(actuals_df['Timeguessr Day'] == timeguessr_day) & 
                                      (actuals_df['Timeguessr Round'] == round_num)]
                if len(existing) > 0:
                    any_actual_exists = True
                    break
        
        # --- 3. Check if Guesses Exist ---
        any_guess_exists = False
        if not guess_df.empty:
            for round_num in range(1, 6):
                existing = guess_df[(guess_df['Timeguessr Day'] == timeguessr_day) & 
                                   (guess_df['Timeguessr Round'] == round_num)]
                if len(existing) > 0:
                    any_guess_exists = True
                    break

        # --- 4. Session State Logic for Revealing (With Reset on Date Change) ---
        
        # A. Track the last viewed day to detect changes
        if "last_viewed_timeguessr_day" not in st.session_state:
            st.session_state["last_viewed_timeguessr_day"] = timeguessr_day

        reveal_state_key = f"reveal_confirmed_{timeguessr_day}"

        # B. Check if date changed since last run
        if st.session_state["last_viewed_timeguessr_day"] != timeguessr_day:
            # Date changed! Reset the reveal state for the current day to False (Hidden)
            st.session_state[reveal_state_key] = False
            # Update the tracker
            st.session_state["last_viewed_timeguessr_day"] = timeguessr_day

        # C. Initialize key if not present
        if reveal_state_key not in st.session_state:
            st.session_state[reveal_state_key] = False
            
        # --- 5. The Logic Condition ---
        # Hidden if: Actuals exist AND No guesses exist AND Not yet manually revealed
        is_hidden = any_actual_exists and not any_guess_exists and not st.session_state[reveal_state_key]

        if is_hidden:
            st.warning("⚠️ You should not view the actual answers as they have already been filled in.")
            
            # Button to trigger the "popup"
            if st.button("Reveal Actual Answers", key=f"btn_req_reveal_{date}"):
                st.session_state[f"show_confirm_popup_{timeguessr_day}"] = True
            
            # The "Popup" (Confirmation Area)
            if st.session_state.get(f"show_confirm_popup_{timeguessr_day}", False):
                st.info("Are you sure you want to view actual answers?")
                col_yes, col_no = st.columns(2)
                
                with col_yes:
                    if st.button("Yes, View Answers", key=f"btn_yes_reveal_{date}"):
                        st.session_state[reveal_state_key] = True
                        st.session_state[f"show_confirm_popup_{timeguessr_day}"] = False
                        st.rerun()
                
                with col_no:
                    if st.button("No, Keep Hidden", key=f"btn_no_reveal_{date}"):
                        st.session_state[f"show_confirm_popup_{timeguessr_day}"] = False
                        st.rerun()

        else:
            # ============================================================
            # EXISTING FORM RENDER LOGIC
            # ============================================================
            if any_actual_exists:
                edit_mode_actual = st.toggle("Edit Mode", value=False, key=f"edit_mode_actual_{date}")
            else:
                edit_mode_actual = False
            
            for round_num in range(1, 6):
                st.markdown(f"**Round {round_num}**")
                
                # Get existing data for this round
                default_year = ""
                default_country = ""
                default_subdivision = ""
                default_city = ""
                actual_exists = False
                
                if not actuals_df.empty:
                    existing = actuals_df[(actuals_df['Timeguessr Day'] == timeguessr_day) & 
                                          (actuals_df['Timeguessr Round'] == round_num)]
                    if len(existing) > 0:
                        actual_exists = True
                        existing_data = existing.iloc[0]
                        default_year = str(int(existing_data['Year']))
                        default_country = existing_data['Country']
                        default_subdivision = existing_data.get('Subdivision', '')
                        default_city = existing_data['City']
                
                # Create 4 columns for Year, Country, Subdivision, City
                r_cols = st.columns(4)
                
                with r_cols[0]:
                    year = st.text_input("Year", key=f"actual_year_r{round_num}_{date}", 
                                        value=default_year, 
                                        disabled=(actual_exists and not edit_mode_actual),
                                        label_visibility="visible")
                
                with r_cols[1]:
                    country_options = [""] + list(config.get('countries', {}).keys())
                    
                    if default_country and default_country in country_options:
                        default_index = country_options.index(default_country)
                    else:
                        default_index = 0
                    
                    country = st.selectbox("Country", 
                                            options=country_options,
                                            index=default_index,
                                            key=f"actual_country_r{round_num}_{date}",
                                            disabled=(actual_exists and not edit_mode_actual),
                                            label_visibility="visible")
                
                with r_cols[2]:
                    subdivision_display = [""]
                    subdivision_actual = [""]

                    if country and country in config.get('countries', {}):
                        country_data = config['countries'][country]
                        for category, subs in country_data.items():
                            header = f"─ {category.replace('_', ' ').title()} ─"
                            subdivision_display.append(header)
                            subdivision_actual.append(None)
                            subdivision_display.extend(subs)
                            subdivision_actual.extend(subs)

                    display_to_actual = dict(zip(subdivision_display, subdivision_actual))

                    if default_subdivision in subdivision_actual:
                        default_index = subdivision_actual.index(default_subdivision)
                    else:
                        default_index = 0

                    subdivision_display_value = st.selectbox(
                        "Subdivision",
                        options=subdivision_display,
                        index=default_index,
                        key=f"actual_subdivision_r{round_num}_{date}",
                        disabled=(actual_exists and not edit_mode_actual),
                        label_visibility="visible"
                    )

                    subdivision = display_to_actual.get(subdivision_display_value, "")
                    if subdivision is None:
                        subdivision = ""
                
                with r_cols[3]:
                    city = st.text_input("City", key=f"actual_city_r{round_num}_{date}", 
                                        value=default_city,
                                        disabled=(actual_exists and not edit_mode_actual),
                                        label_visibility="visible")
                
                # Validate year
                year_valid = True
                if year and (not actual_exists or edit_mode_actual):
                    if not year.isdigit() or len(year) != 4:
                        st.error(f"Round {round_num}: Year must be a 4-digit number")
                        year_valid = False
                    elif not (1900 <= int(year) <= date.year):
                        st.error(f"Round {round_num}: Year must be between 1900 and {date.year}")
                        year_valid = False
                
                # Populate dictionary
                actual_rounds_data[round_num] = {
                    'year': year,
                    'city': city,
                    'subdivision': subdivision,
                    'country': country,
                    'year_valid': year_valid,
                    'exists': actual_exists
                }
            
            # Save/Submit buttons
            if any_actual_exists and edit_mode_actual:
                if st.button("Save All Changes", key="save_all_actual"):
                    try:
                        actuals_path = "./Data/Timeguessr_Actuals_Parsed.csv"
                        actuals_df = pd.read_csv(actuals_path)
                        
                        all_valid = True
                        for round_num, data in actual_rounds_data.items():
                            if data['exists'] and data['year'] and data['country'] and data['city'] and data['year_valid']:
                                mask = (actuals_df['Timeguessr Day'] == timeguessr_day) & (actuals_df['Timeguessr Round'] == round_num)
                                actuals_df.loc[mask, 'Year'] = int(data['year'])
                                actuals_df.loc[mask, 'Country'] = data['country']
                                actuals_df.loc[mask, 'Subdivision'] = data['subdivision']
                                actuals_df.loc[mask, 'City'] = data['city']
                            elif data['exists']:
                                all_valid = False
                        
                        if all_valid:
                            actuals_df = actuals_df.sort_values(by=['Timeguessr Day', 'Timeguessr Round'])
                            actuals_df.to_csv(actuals_path, index=False)
                            st.success("All changes saved successfully!")
                            st.rerun()
                        else:
                            st.error("Please fill in all required fields correctly for all rounds.")
                    except Exception as e:
                        st.error(f"Error saving changes: {e}")
            
            elif not any_actual_exists:
                if st.button("Submit All Actual Answers", key="submit_all_actual"):
                    try:
                        reference_date = datetime.date(2025, 10, 24)
                        reference_day_number = 876
                        delta_days = (date - reference_date).days
                        computed_timeguessr_day = reference_day_number + delta_days
                        
                        all_valid = True
                        new_rows = []
                        
                        for round_num, data in actual_rounds_data.items():
                            if not data['year'] or not data['country']:
                                st.error(f"Round {round_num}: Year and Country are required fields.")
                                all_valid = False
                                break
                            
                            if not data['year_valid']:
                                st.error(f"Round {round_num}: Please enter a valid year.")
                                all_valid = False
                                break
                            
                            if data['year'] and data['country'] and data['year_valid']:
                                new_rows.append({
                                    "Timeguessr Day": int(computed_timeguessr_day),
                                    "Timeguessr Round": int(round_num),
                                    "City": data['city'],
                                    "Subdivision": data['subdivision'],
                                    "Country": data['country'],
                                    "Year": int(data['year'])
                                })
                            else:
                                all_valid = False
                                break
                        
                        if all_valid and len(new_rows) == 5:
                            parsed_path = "./Data/Timeguessr_Actuals_Parsed.csv"
                            
                            if os.path.exists(parsed_path):
                                parsed_df = pd.read_csv(parsed_path)
                                parsed_df = parsed_df[~(pd.to_numeric(parsed_df.get("Timeguessr Day"), errors="coerce") == computed_timeguessr_day)]
                                parsed_df = pd.concat([parsed_df, pd.DataFrame(new_rows)], ignore_index=True)
                            else:
                                parsed_df = pd.DataFrame(new_rows)
                            
                            parsed_df = parsed_df.sort_values(by=['Timeguessr Day', 'Timeguessr Round'])
                            parsed_df.to_csv(parsed_path, index=False)
                            st.success("All actual answers submitted successfully!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error submitting actual answers: {e}")
    
    # Right column - Guesses (all 5 rounds)
    with col2:
        st.subheader(f"{name}'s Guesses")
        
        # Check if edit mode toggle should appear
        any_guess_exists = False
        if not guess_df.empty:
            for round_num in range(1, 6):
                existing = guess_df[(guess_df['Timeguessr Day'] == timeguessr_day) & 
                                   (guess_df['Timeguessr Round'] == round_num)]
                if len(existing) > 0:
                    any_guess_exists = True
                    break
        
        if any_guess_exists:
            edit_mode_guess = st.toggle("Edit Mode", value=False, key=f"edit_mode_guess_{date}")
        else:
            edit_mode_guess = False
        
        # Store all guess data
        guess_rounds_data = {}
        
        # Build formatted total score text
        default_total_score = ""
        if not guess_df.empty:
            existing = guess_df[guess_df['Timeguessr Day'] == timeguessr_day]
            if len(existing) > 0:
                # Get total score from first row (should be same for all rounds of that day)
                total_score_val = existing.iloc[0].get(f'{name} Total Score')
                if pd.notna(total_score_val) and total_score_val != '':
                    total_score_formatted = f"{int(total_score_val):,}/50,000"
                else:
                    total_score_formatted = "_____/50,000"
                
                # Build the formatted string
                default_total_score = f"TimeGuessr #{timeguessr_day} {total_score_formatted}\n"
                
                # Convert O/X/% to emojis
                def convert_to_emoji(s):
                    if pd.isna(s) or s == "":
                        return "⬛️⬛️⬛️"
                    result = ""
                    for char in s:
                        if char == "O":
                            result += "🟩"
                        elif char == "%":
                            result += "🟨"
                        elif char == "X":
                            result += "⬛️"
                    return result
                
                # Add each round
                for round_num in range(1, 6):
                    round_data = existing[existing['Timeguessr Round'] == round_num]
                    if len(round_data) > 0:
                        geo_string = round_data.iloc[0].get(f'{name} Geography', '')
                        time_string = round_data.iloc[0].get(f'{name} Time', '')
                        geo_display = convert_to_emoji(geo_string)
                        time_display = convert_to_emoji(time_string)
                    else:
                        geo_display = "⬛️⬛️⬛️"
                        time_display = "⬛️⬛️⬛️"
                    
                    default_total_score += f"🌎{geo_display} 📅{time_display}\n"
                
                # Remove trailing newline
                default_total_score = default_total_score.rstrip('\n')
        
        for round_num in range(1, 6):
            st.markdown(f"**Round {round_num}**")
            
            # Get existing data for this round
            default_distance = ""
            default_distance_km = False
            default_year_guessed = ""
            guess_exists = False
            
            if not guess_df.empty:
                existing = guess_df[(guess_df['Timeguessr Day'] == timeguessr_day) & 
                                   (guess_df['Timeguessr Round'] == round_num)]
                if len(existing) > 0:
                    guess_exists = True
                    guess_data = existing.iloc[0]
                    
                    if pd.notna(guess_data.get(f'{name} Geography Distance')) and guess_data.get(f'{name} Geography Distance') != '':
                        dist_meters = float(guess_data[f'{name} Geography Distance'])
                        if dist_meters >= 1000:
                            default_distance = str(dist_meters / 1000)
                            default_distance_km = True
                        else:
                            default_distance = str(dist_meters)
                            default_distance_km = False
                    
                    if pd.notna(guess_data.get(f'{name} Time Guessed')) and guess_data.get(f'{name} Time Guessed') != '':
                        default_year_guessed = str(int(guess_data[f'{name} Time Guessed']))
            
            # Get actual year for this round if available
            actual_year_for_round = None
            if round_num in actual_rounds_data:
                if actual_rounds_data[round_num]['year_valid'] and actual_rounds_data[round_num]['year']:
                    actual_year_for_round = int(actual_rounds_data[round_num]['year'])
            
            # Create 4 columns for Distance, Geo Score, Year, Time Score
            g_cols = st.columns([1, 0.5, 1, 0.5])
            
            # Calculate scores first
            geo_score = None
            time_score = None
            
            with g_cols[0]:
                # Distance input with unit toggle
                if guess_exists and not edit_mode_guess:
                    unit_label = "km" if default_distance_km else "m"
                    distance = st.text_input(f"Distance ({unit_label})", 
                                           key=f"distance_r{round_num}_{date}",
                                           value=default_distance,
                                           disabled=True,
                                           label_visibility="visible")
                    is_km = default_distance_km
                else:
                    # Create sub-columns for toggle and input
                    toggle_col, input_col = st.columns([0.07, 1])
                    with toggle_col:
                        st.markdown("<div style='height: 33px;'></div>", unsafe_allow_html=True)
                        toggle_key = f'distance_unit_r{round_num}_{date}'
                        # Determine current unit based on session state or default
                        current_is_km = st.session_state.get(toggle_key, default_distance_km)
                        toggle_label = "km" if current_is_km else "m"
                        is_km = st.toggle(toggle_label, value=current_is_km, 
                                         key=toggle_key)
                    with input_col:
                        unit_label = "km" if is_km else "m"
                        distance = st.text_input(f"Distance ({unit_label})", 
                                               key=f"distance_r{round_num}_{date}",
                                               value=default_distance,
                                               label_visibility="visible")
                
                # Calculate geography score
                if distance:
                    try:
                        dist_input = float(distance)
                        if dist_input >= 0:
                            dist = dist_input * 1000 if is_km else dist_input
                            
                            conditions = [
                                (dist <= 50),
                                (dist > 50) & (dist <= 1000),
                                (dist > 1000) & (dist <= 5000),
                                (dist > 5000) & (dist <= 100000),
                                (dist > 100000) & (dist <= 1000000),
                                (dist > 1000000) & (dist <= 2000000),
                                (dist > 2000000) & (dist <= 3000000),
                                (dist > 3000000) & (dist <= 6000000),
                                (dist > 6000000)
                            ]
                            
                            scores = [
                                5000,
                                5000 - (dist * 0.02),
                                4980 - (dist * 0.016),
                                4900 - (dist * 0.004),
                                4500 - (dist * 0.001),
                                3500 - (dist * 0.0005),
                                2500 - (dist * 0.0003333),
                                1500 - (dist * 0.0002),
                                12
                            ]
                            
                            for condition, score in zip(conditions, scores):
                                if condition:
                                    geo_score = score
                                    break
                    except:
                        pass
            
            with g_cols[1]:
                st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
                if geo_score is not None:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #dde5eb;
                            color: #221e8f;
                            padding: 4px 8px;
                            border-left: 7px solid #221e8f;
                            border-radius: 4px;
                            font-size: 1rem;
                            line-height: 1.9;
                        ">
                            🌎 {geo_score:.0f}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown("")
            
            with g_cols[2]:
                year_guessed = st.text_input("Year", 
                                            key=f"year_guessed_r{round_num}_{date}",
                                            value=default_year_guessed,
                                            disabled=(guess_exists and not edit_mode_guess),
                                            label_visibility="visible")
                
                # Validate and calculate time score
                year_guessed_valid = False
                if year_guessed:
                    if not year_guessed.isdigit() or len(year_guessed) != 4:
                        st.error("4 digits")
                    elif not (1900 <= int(year_guessed) <= date.year):
                        st.error(f"1900-{date.year}")
                    else:
                        year_guessed_valid = True
                        
                        if actual_year_for_round is not None:
                            years_off = abs(int(year_guessed) - actual_year_for_round)
                            
                            if years_off == 0:
                                time_score = 5000
                            elif years_off == 1:
                                time_score = 4950
                            elif years_off == 2:
                                time_score = 4800
                            elif years_off == 3:
                                time_score = 4600
                            elif years_off == 4:
                                time_score = 4300
                            elif years_off == 5:
                                time_score = 3900
                            elif years_off in [6, 7]:
                                time_score = 3400
                            elif years_off in [8, 9, 10]:
                                time_score = 2500
                            elif 10 < years_off < 16:
                                time_score = 2000
                            elif 15 < years_off < 21:
                                time_score = 1000
                            else:
                                time_score = 0
            
            with g_cols[3]:
                st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
                if time_score is not None:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #dde5eb;
                            color: #221e8f;
                            padding: 4px 8px;
                            border-left: 7px solid #221e8f;
                            border-radius: 4px;
                            font-size: 1rem;
                            line-height: 1.9;
                        ">
                            📅 {time_score:.0f}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                elif year_guessed_valid and actual_year_for_round is None:
                    # Show help text with year ranges
                    guessed = int(year_guessed)
                    def clamp(year):
                        return max(1900, min(year, date.year))
                    
                    help_text = f"""5000: {clamp(guessed)}  
                                    4950: {clamp(guessed-1)}/{clamp(guessed+1)}   
                                    4800: {clamp(guessed-2)}/{clamp(guessed+2)}    
                                    4600: {clamp(guessed-3)}/{clamp(guessed+3)}     
                                    4300: {clamp(guessed-4)}/{clamp(guessed+4)}     
                                    3900: {clamp(guessed-5)}/{clamp(guessed+5)}     
                                    3400: {clamp(guessed-7)}-{clamp(guessed-6)}/{clamp(guessed+6)}-{clamp(guessed+7)}      
                                    2500: {clamp(guessed-10)}-{clamp(guessed-8)}/{clamp(guessed+8)}-{clamp(guessed+10)}    
                                    2000: {clamp(guessed-15)}-{clamp(guessed-11)}/{clamp(guessed+11)}-{clamp(guessed+15)}  
                                    1000: {clamp(guessed-20)}-{clamp(guessed-16)}/{clamp(guessed+16)}-{clamp(guessed+20)}  
                                    0: {clamp(1900)}-{clamp(guessed-21)}/{clamp(guessed+21)}-{clamp(date.year)}"""
                    
                    st.markdown(
                        f"""
                        <div title="{help_text}"
                            style="
                                background-color: #bcb0ff;
                                color: #221e8f;
                                padding: 4px 8px;
                                border-left: 7px solid #221e8f;
                                border-radius: 4px;
                                font-size: 1rem;
                                line-height: 1.9;
                                display: inline-block;
                            ">
                            📅 ?
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown("")
            
            guess_rounds_data[round_num] = {
                'distance': distance,
                'is_km': is_km,
                'year_guessed': year_guessed,
                'year_valid': year_guessed_valid,
                'exists': guess_exists
            }

        # Add Total Score input before rounds
        total_score_input = st.text_area("Total Score", 
                    value=default_total_score, 
                    key=f"total_score_text_{date}",
                    help="Share Your Results from TimeGuessr!",
                    height=180,
                    disabled=(any_guess_exists and not edit_mode_guess))
        
        # Save/Submit buttons for guesses
        if any_guess_exists and edit_mode_guess:
            if st.button("Save All Guess Changes", key="save_all_guess"):
                try:
                    # Validate Total Score format even when editing
                    valid_combos = ['🟩🟩🟩', '🟩🟩🟨', '🟩🟩⬛', '🟩🟩⬛️', '🟩🟨⬛', '🟩🟨⬛️', '🟩⬛⬛', '🟩⬛️⬛️', '🟩⬛⬛️', '🟩⬛️⬛', '🟨⬛⬛', '🟨⬛️⬛️', '🟨⬛⬛️', '🟨⬛️⬛', '⬛⬛⬛', '⬛️⬛️⬛️', '⬛⬛⬛️', '⬛️⬛⬛', '⬛⬛️⬛', '⬛️⬛️⬛', '⬛️⬛⬛️']
                    
                    if not total_score_input or not total_score_input.strip():
                        st.error("Please enter the Total Score from TimeGuessr.")
                    else:
                        lines = total_score_input.strip().split('\n')[:7]
                        
                        if len(lines) < 6:
                            st.error("Total Score format is incorrect. Must have at least 6 lines.")
                        else:
                            
                            # Extract geography patterns from Total Score
                            geo_patterns_edit = []
                            format_valid = True
                            
                            for i, line in enumerate(lines[1:6], 1):
                                if not line.startswith('🌎') or '📅' not in line:
                                    st.error(f"Round {i} format is incorrect in Total Score box")
                                    format_valid = False
                                    break
                                
                                parts = line.split('📅')
                                geo_part = parts[0].replace('🌎', '').strip()
                                time_part = parts[1].strip()
                                
                                if geo_part not in valid_combos:
                                    st.error(f"Round {i} geography emoji combination is invalid: {geo_part}")
                                    format_valid = False
                                    break
                                
                                if time_part not in valid_combos:
                                    st.error(f"Round {i} time emoji combination is invalid: {time_part}")
                                    format_valid = False
                                    break
                                
                                # Convert emojis to O/X/% format
                                def emoji_to_pattern(emoji_str):
                                    return emoji_str.replace('🟩', 'O').replace('🟨', '%').replace('⬛️', 'X').replace('⬛', 'X')
                                
                                geo_patterns_edit.append(emoji_to_pattern(geo_part))
                            
                            if format_valid:
                                guess_path = f"./Data/Timeguessr_{name}_Parsed.csv"
                                guess_df = pd.read_csv(guess_path)
                                
                                all_valid = True
                                for round_num, data in guess_rounds_data.items():
                                    if not data['distance'] or not data['year_guessed']:
                                        st.error(f"Round {round_num}: Distance and Year are required fields.")
                                        all_valid = False
                                        break
                                    
                                    if not data['year_valid']:
                                        st.error(f"Round {round_num}: Please enter a valid year.")
                                        all_valid = False
                                        break
                                    
                                    if data['exists'] and data['distance'] and data['year_valid']:
                                        try:
                                            dist_val = float(data['distance'])
                                            if dist_val < 0:
                                                st.error(f"Round {round_num}: Distance cannot be negative.")
                                                all_valid = False
                                                break
                                            
                                            dist_meters = int(dist_val * 1000) if data['is_km'] else int(dist_val)
                                            
                                            # Get the geography pattern from Total Score input  
                                            geo_pattern_from_input = geo_patterns_edit[round_num - 1]
                                            
                                            # Validate distance matches the geography pattern (no time validation)
                                            validation_result = validate_distance_pattern(dist_meters, geo_pattern_from_input, round_num, data['is_km'])
                                            
                                            if not validation_result[0]:
                                                st.error(validation_result[1])
                                                all_valid = False
                                                break
                                            
                                            mask = (guess_df['Timeguessr Day'] == timeguessr_day) & (guess_df['Timeguessr Round'] == round_num)
                                            guess_df.loc[mask, f'{name} Geography Distance'] = int(dist_meters)
                                            guess_df.loc[mask, f'{name} Time Guessed'] = int(data['year_guessed'])
                                        except ValueError:
                                            st.error(f"Round {round_num}: Invalid distance value.")
                                            all_valid = False
                                            break
                                    elif data['exists']:
                                        all_valid = False
                                
                                if all_valid:
                                    guess_df = guess_df.sort_values(by=['Timeguessr Day', 'Timeguessr Round'])
                                    guess_df.to_csv(guess_path, index=False)
                                    st.success("All guess changes saved successfully!")
                                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving guess changes: {e}")
        
        elif not any_guess_exists:
            if st.button("Submit All Guesses", key="submit_all_guess"):
                # Validate Total Score format
                valid_combos = ['🟩🟩🟩', '🟩🟩🟨', '🟩🟩⬛', '🟩🟩⬛️', '🟩🟨⬛', '🟩🟨⬛️', '🟩⬛⬛', '🟩⬛️⬛️', '🟩⬛⬛️', '🟩⬛️⬛', '🟨⬛⬛', '🟨⬛️⬛️', '🟨⬛⬛️', '🟨⬛️⬛', '⬛⬛⬛', '⬛️⬛️⬛️', '⬛⬛⬛️', '⬛️⬛⬛', '⬛⬛️⬛', '⬛️⬛️⬛', '⬛️⬛⬛️']
                
                if not total_score_input or not total_score_input.strip():
                    st.error("Please enter the Total Score from TimeGuessr.")
                else:
                    lines = total_score_input.strip().split('\n')[:7]  # Only keep first 7 lines
                    
                    if len(lines) < 6:
                        st.error("Total Score format is incorrect. Must have at least 6 lines.")
                    else:
                        # Validate first line format: TimeGuessr #XXX XX,XXX/50,000
                        first_line = lines[0]
                        if not first_line.startswith('TimeGuessr #'):
                            st.error("First line must start with 'TimeGuessr #'")
                        else:
                            # Extract total score from first line
                            try:
                                score_part = first_line.split()[-1]  # Get last part
                                total_score_str = score_part.split('/')[0].replace(',', '')
                                extracted_total_score = int(total_score_str)
                                if not (0 <= extracted_total_score <= 50000):
                                    st.error("Total score must be between 0 and 50,000")
                                    extracted_total_score = None
                            except:
                                st.error("Could not extract total score from first line. Expected format: 'TimeGuessr #XXX XX,XXX/50,000'")
                                extracted_total_score = None
                            
                            if extracted_total_score is not None:
                                # Validate next 5 lines (rounds)
                                geo_patterns = []
                                time_patterns = []
                                format_valid = True
                                
                                for i, line in enumerate(lines[1:6], 1):
                                    # Check format: 🌎XXX 📅XXX
                                    if not line.startswith('🌎'):
                                        st.error(f"Round {i} line must start with 🌎")
                                        format_valid = False
                                        break
                                    
                                    if '📅' not in line:
                                        st.error(f"Round {i} line must contain 📅")
                                        format_valid = False
                                        break
                                    
                                    parts = line.split('📅')
                                    if len(parts) != 2:
                                        st.error(f"Round {i} format is incorrect")
                                        format_valid = False
                                        break
                                    
                                    geo_part = parts[0].replace('🌎', '').strip()
                                    time_part = parts[1].strip()
                                    
                                    if geo_part not in valid_combos:
                                        st.error(f"Round {i} geography emoji combination is invalid: {geo_part}")
                                        format_valid = False
                                        break
                                    
                                    if time_part not in valid_combos:
                                        st.error(f"Round {i} time emoji combination is invalid: {time_part}")
                                        format_valid = False
                                        break
                                    
                                    # Convert emojis to O/X/% format
                                    def emoji_to_pattern(emoji_str):
                                        return emoji_str.replace('🟩', 'O').replace('🟨', '%').replace('⬛️', 'X').replace('⬛', 'X')
                                    
                                    geo_patterns.append(emoji_to_pattern(geo_part))
                                    time_patterns.append(emoji_to_pattern(time_part))
                                
                                if format_valid:
                                    try:
                                        reference_date = datetime.date(2025, 10, 24)
                                        reference_day_number = 876
                                        delta_days = (date - reference_date).days
                                        computed_timeguessr_day = reference_day_number + delta_days
                                        
                                        all_valid = True
                                        new_rows = []
                                        
                                        def geography_score(x):
                                            if x <= 50:
                                                return 5000
                                            elif x <= 1000:
                                                return 5000 - (x * 0.02)
                                            elif x <= 5000:
                                                return 4980 - (x * 0.016)
                                            elif x <= 100000:
                                                return 4900 - (x * 0.004)
                                            elif x <= 1000000:
                                                return 4500 - (x * 0.001)
                                            elif x <= 2000000:
                                                return 3500 - (x * 0.0005)
                                            elif x <= 3000000:
                                                return 2500 - (x * 0.0003333)
                                            elif x <= 6000000:
                                                return 1500 - (x * 0.0002)
                                            else:
                                                return 12
                                        
                                        def geography_pattern(x):
                                            if x == 5000:
                                                return "OOO"
                                            elif 4750 <= x <= 4999:
                                                return "OO%"
                                            elif 4500 <= x < 4750:
                                                return "OOX"
                                            elif 4250 <= x < 4500:
                                                return "O%X"
                                            elif 3500 <= x < 4250:
                                                return "OXX"
                                            elif 2500 <= x < 3500:
                                                return "%XX"
                                            elif 12 <= x < 2500:
                                                return "XXX"
                                            else:
                                                return None
                                        
                                        for round_num, data in guess_rounds_data.items():
                                            # Require distance and year for all rounds
                                            if not data['distance'] or not data['year_guessed']:
                                                st.error(f"Round {round_num}: Distance and Year are required fields.")
                                                all_valid = False
                                                break
                                            
                                            if not data['year_valid']:
                                                st.error(f"Round {round_num}: Please enter a valid year.")
                                                all_valid = False
                                                break
                                            
                                            if data['distance'] and data['year_valid']:
                                                try:
                                                    dist_val = float(data['distance'])
                                                    if dist_val < 0:
                                                        st.error(f"Round {round_num}: Distance cannot be negative.")
                                                        all_valid = False
                                                        break
                                                    
                                                    dist_meters = int(dist_val * 1000) if data['is_km'] else int(dist_val)
                                                    year_val = int(data['year_guessed'])
                                                    
                                                    # Get the geography pattern from Total Score input
                                                    geo_pattern_from_input = geo_patterns[round_num - 1]
                                                    time_pattern_from_input = time_patterns[round_num - 1]
                                                    
                                                    # Validate distance matches the geography pattern (no time validation)
                                                    validation_result = validate_distance_pattern(dist_meters, geo_pattern_from_input, round_num, data['is_km'])
                                                    
                                                    if not validation_result[0]:
                                                        st.error(validation_result[1])
                                                        all_valid = False
                                                        break
                                                    
                                                    geo_score = geography_score(dist_meters)
                                                    
                                                    new_rows.append({
                                                        "Timeguessr Day": int(computed_timeguessr_day),
                                                        "Timeguessr Round": int(round_num),
                                                        f"{name} Total Score": extracted_total_score,
                                                        f"{name} Round Score": np.nan,
                                                        f"{name} Geography": geo_pattern_from_input,
                                                        f"{name} Time": time_pattern_from_input,
                                                        f"{name} Geography Distance": dist_meters,
                                                        f"{name} Time Guessed": year_val,
                                                        f"{name} Time Distance": np.nan,
                                                        f"{name} Geography Score": geo_score,
                                                        f"{name} Geography Score (Min)": geo_score,
                                                        f"{name} Geography Score (Max)": geo_score,
                                                        f"{name} Time Score": np.nan,
                                                        f"{name} Time Score (Min)": np.nan,
                                                        f"{name} Time Score (Max)": np.nan,
                                                    })
                                                except ValueError:
                                                    st.error(f"Round {round_num}: Invalid distance value.")
                                                    all_valid = False
                                                    break
                                            else:
                                                all_valid = False
                                                break
                                        
                                        if all_valid and len(new_rows) == 5:
                                            parsed_path = f"./Data/Timeguessr_{name}_Parsed.csv"
                                            
                                            if os.path.exists(parsed_path):
                                                parsed_df = pd.read_csv(parsed_path)
                                                # Remove any existing entries for this day
                                                parsed_df = parsed_df[~(pd.to_numeric(parsed_df.get("Timeguessr Day"), errors="coerce") == computed_timeguessr_day)]
                                                parsed_df = pd.concat([parsed_df, pd.DataFrame(new_rows)], ignore_index=True)
                                            else:
                                                parsed_df = pd.DataFrame(new_rows)
                                            
                                            parsed_df = parsed_df.sort_values(by=['Timeguessr Day', 'Timeguessr Round'])
                                            parsed_df.to_csv(parsed_path, index=False)
                                            st.success(f"All guesses submitted successfully!")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Error submitting guesses: {e}")