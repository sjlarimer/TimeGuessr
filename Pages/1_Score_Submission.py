import streamlit as st
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import os
from Score_Update import score_update

st.title("Score Submission")

score_update()

# Create two columns - left for inputs, right for score display
input_col, score_col = st.columns([2, 1])

with input_col:
    # Top section - Name and Date only
    date = st.date_input(
        "Date",
        value=datetime.date.today(),
        max_value=datetime.date.today()
    )

    name = st.text_input("Name")

    # Validate name
    name_valid = False
    if name:
        if name not in ["Michael", "Sarah"]:
            st.error("Name must be either 'Michael' or 'Sarah'")
        else:
            name_valid = True

# Display score summary if name and date are selected
with score_col:
    st.markdown("""
        <style>
        /* make internal spacing very tight */
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
            gap: 0.08rem !important;
        }

        /* force the score container to move up (actual movement) */
        .score-container {
            position: relative;
            top: -44px;
            margin-bottom: 0 !important;
        }

        .score-header {
            font-size: 1.4rem;
            font-weight: 600;
            margin: 0 0 5px 0;
            line-height: 1;
        }
        .score-total {
            font-size: 1.4rem;
            font-weight: 700;
            color: #db5049;
            margin: 0 0 5px 0;
            line-height: 1;
        }
        .score-sub {
            font-size: 1.2rem;
            margin: 0 0 1px 0;
            line-height: 1;
        }
        .round-row {
            font-size: 1.0rem;
            margin: 0 0 2px 0;
            line-height: 1.08;
        }
        hr { margin: 6px 0 !important; }
        
        /* Red labels for input fields and toggles */
        label[data-testid="stWidgetLabel"] p {
            color: #db5049 !important;
        }
        
        /* Red text for toggle labels - more specific selectors */
        label[data-testid="stWidgetLabel"] span {
            color: #db5049 !important;
        }
        
        /* Target toggle text specifically */
        div[data-testid="stToggle"] label span {
            color: #db5049 !important;
        }
        
        div[data-testid="stToggle"] label p {
            color: #db5049 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    if name_valid and date:
        try:
            df = pd.read_csv("./Data/Timeguessr_Stats.csv")
            df["Date"] = pd.to_datetime(df["Date"]).dt.date

            date_rows = df[df["Date"] == date]
            if len(date_rows) > 0:
                timeguessr_day = date_rows.iloc[0]["Timeguessr Day"]
                total_score_col = f"{name} Total Score"
                total_score = date_rows.iloc[0][total_score_col]

                # check for full 5 rounds
                all_rounds = date_rows[date_rows["Timeguessr Round"].between(1, 5)]
                geo_sum = all_rounds[f"{name} Geography Score"].fillna(0).sum()
                time_sum = all_rounds[f"{name} Time Score"].fillna(0).sum()

                st.markdown("<div class='score-container'>", unsafe_allow_html=True)
                st.markdown(f"<div class='score-header'>TimeGuessr #{int(timeguessr_day)}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='score-total'>{int(total_score):,}/50,000</div>", unsafe_allow_html=True)

                # subtotals
                st.markdown(f"<div class='score-sub'>🌎 Geography: <b>{int(geo_sum):,}</b>/25,000</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='score-sub'>📅 Time: <b>{int(time_sum):,}</b>/25,000</div>", unsafe_allow_html=True)

                st.markdown("<hr>", unsafe_allow_html=True)

                geo_col = f"{name} Geography"
                time_col = f"{name} Time"

                for round_num in range(1, 6):
                    round_data = date_rows[date_rows["Timeguessr Round"] == round_num]

                    def convert_to_emoji(s):
                        if pd.isna(s) or s == "":
                            return "MISSING"
                        result = ""
                        for char in s:
                            if char == "O":
                                result += "🟩"
                            elif char == "%":
                                result += "🟨"
                            elif char == "X":
                                result += "⬛"
                        return result

                    if len(round_data) > 0:
                        geo_string = round_data.iloc[0][geo_col]
                        time_string = round_data.iloc[0][time_col]
                        geo_display = convert_to_emoji(geo_string)
                        time_display = convert_to_emoji(time_string)
                    else:
                        geo_display = time_display = "MISSING"

                    if geo_display == "MISSING" or time_display == "MISSING":
                        display_text = "<b style='color:red;'>MISSING</b>"
                    else:
                        display_text = f"🌎{geo_display} &nbsp;&nbsp;📅{time_display}"

                    st.markdown(f"<div class='round-row'>{display_text}</div>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

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
    col1, col2 = st.columns(2)
    
    # Left column - Actual Answers (all 5 rounds)
    with col1:
        st.subheader("Actual Answers")
        
        # Check if edit mode toggle should appear (if any round has data)
        any_actual_exists = False
        if not actuals_df.empty:
            for round_num in range(1, 6):
                existing = actuals_df[(actuals_df['Timeguessr Day'] == timeguessr_day) & 
                                     (actuals_df['Timeguessr Round'] == round_num)]
                if len(existing) > 0:
                    any_actual_exists = True
                    break
        
        if any_actual_exists:
            edit_mode_actual = st.toggle("Edit Mode", value=False, key=f"edit_mode_actual_{date}")
        else:
            edit_mode_actual = False
        
        # Store all actual data for validation
        actual_rounds_data = {}
        
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
            
            # Create 4 columns for Year, City, Subdivision, Country
            r_cols = st.columns(4)
            
            with r_cols[0]:
                year = st.text_input("Year", key=f"actual_year_r{round_num}_{date}", 
                                    value=default_year, 
                                    disabled=(actual_exists and not edit_mode_actual),
                                    label_visibility="visible")
            
            with r_cols[1]:
                city = st.text_input("City", key=f"actual_city_r{round_num}_{date}", 
                                    value=default_city,
                                    disabled=(actual_exists and not edit_mode_actual),
                                    label_visibility="visible")
            
            with r_cols[2]:
                subdivision = st.text_input("Subdivision", key=f"actual_subdivision_r{round_num}_{date}", 
                                           value=default_subdivision,
                                           disabled=(actual_exists and not edit_mode_actual),
                                           label_visibility="visible")
            
            with r_cols[3]:
                country = st.text_input("Country", key=f"actual_country_r{round_num}_{date}", 
                                       value=default_country,
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
            
            actual_rounds_data[round_num] = {
                'year': year,
                'city': city,
                'subdivision': subdivision,
                'country': country,
                'year_valid': year_valid,
                'exists': actual_exists
            }
        
        # Save/Submit buttons for actual answers
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
                        if data['year'] and data['country'] and data['city'] and data['year_valid']:
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
                            # Remove any existing entries for this day
                            parsed_df = parsed_df[~(pd.to_numeric(parsed_df.get("Timeguessr Day"), errors="coerce") == computed_timeguessr_day)]
                            parsed_df = pd.concat([parsed_df, pd.DataFrame(new_rows)], ignore_index=True)
                        else:
                            parsed_df = pd.DataFrame(new_rows)
                        
                        parsed_df = parsed_df.sort_values(by=['Timeguessr Day', 'Timeguessr Round'])
                        parsed_df.to_csv(parsed_path, index=False)
                        st.success("All actual answers submitted successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill out all fields correctly for all 5 rounds before submitting.")
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
        
        # Add Total Score input before rounds
        st.text_area("Total Score", 
                    value="", 
                    key=f"total_score_text_{date}",
                    help="Share Your Results from TimeGuessr!",
                    height=180)
        
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
            g_cols = st.columns([1.2, 0.6, 0.8, 0.6])
            
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
                    st.info(f"🌎 {geo_score:.0f}")
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
                    st.info(f"📅 {time_score}")
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
                    
                    st.markdown(f'<div title="{help_text}" style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 0.25rem; padding: 0.75rem 1.25rem; color: #0c5460;">📅 ?</div>', unsafe_allow_html=True)
                else:
                    st.markdown("")
            
            guess_rounds_data[round_num] = {
                'distance': distance,
                'is_km': is_km,
                'year_guessed': year_guessed,
                'year_valid': year_guessed_valid,
                'exists': guess_exists
            }
        
        # Save/Submit buttons for guesses
        if any_guess_exists and edit_mode_guess:
            if st.button("Save All Guess Changes", key="save_all_guess"):
                try:
                    guess_path = f"./Data/Timeguessr_{name}_Parsed.csv"
                    guess_df = pd.read_csv(guess_path)
                    
                    all_valid = True
                    for round_num, data in guess_rounds_data.items():
                        if data['exists'] and data['distance'] and data['year_valid']:
                            dist_meters = float(data['distance']) * 1000 if data['is_km'] else float(data['distance'])
                            
                            mask = (guess_df['Timeguessr Day'] == timeguessr_day) & (guess_df['Timeguessr Round'] == round_num)
                            guess_df.loc[mask, f'{name} Geography Distance'] = int(dist_meters)
                            guess_df.loc[mask, f'{name} Time Guessed'] = int(data['year_guessed'])
                        elif data['exists']:
                            all_valid = False
                    
                    if all_valid:
                        guess_df = guess_df.sort_values(by=['Timeguessr Day', 'Timeguessr Round'])
                        guess_df.to_csv(guess_path, index=False)
                        st.success("All guess changes saved successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill in all fields correctly for all rounds.")
                except Exception as e:
                    st.error(f"Error saving guess changes: {e}")
        
        elif not any_guess_exists:
            if st.button("Submit All Guesses", key="submit_all_guess"):
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
                        if data['distance'] and data['year_valid']:
                            try:
                                dist_val = float(data['distance'])
                                if dist_val < 0:
                                    all_valid = False
                                    break
                                
                                dist_meters = int(dist_val * 1000) if data['is_km'] else int(dist_val)
                                year_val = int(data['year_guessed'])
                                
                                geo_score = geography_score(dist_meters)
                                geo_pattern = geography_pattern(geo_score)
                                
                                new_rows.append({
                                    "Timeguessr Day": int(computed_timeguessr_day),
                                    "Timeguessr Round": int(round_num),
                                    f"{name} Total Score": np.nan,
                                    f"{name} Round Score": np.nan,
                                    f"{name} Geography": geo_pattern,
                                    f"{name} Time": '',
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
                    st.error(f"Error preparing submit guesses UI: {e}")