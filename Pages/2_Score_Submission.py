import streamlit as st
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import os


st.title("Score Submission")

# Create two columns - left for inputs, right for score display
input_col, score_col = st.columns([2, 1])

with input_col:
    # Top section - Name, Date, Round Number
    name = st.text_input("Name")

    # Validate name
    name_valid = False
    if name:
        if name not in ["Michael", "Sarah"]:
            st.error("Name must be either 'Michael' or 'Sarah'")
        else:
            name_valid = True

    date = st.date_input(
    "Date",
    value=datetime.date.today(),
    max_value=datetime.date.today()
)
    round_number = st.selectbox("Round Number", options=[None, 1, 2, 3, 4, 5], format_func=lambda x: "Select a round" if x is None else str(x))

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
            top: -44px;              /* <-- moves the whole block upward; increase magnitude to move higher */
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
        .round-highlight {
            background-color: #ffcccc;
            padding: 3px 6px;
            border-radius: 5px;
        }
        hr { margin: 6px 0 !important; }
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

                # --- check for full 5 rounds ---
                all_rounds = date_rows[date_rows["Timeguessr Round"].between(1, 5)]
                if len(all_rounds) == 5:
                    geo_sum = all_rounds[f"{name} Geography Score"].sum()
                    time_sum = all_rounds[f"{name} Time Score"].sum()
                else:
                    geo_sum = time_sum = None

                # wrap in score-container which is moved up via CSS
                st.markdown("<div class='score-container'>", unsafe_allow_html=True)
                st.markdown(f"<div class='score-header'>TimeGuessr #{int(timeguessr_day)}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='score-total'>{int(total_score):,}/50,000</div>", unsafe_allow_html=True)

                # subtotals only if all 5 rounds present
                if geo_sum is not None and time_sum is not None:
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

                    is_selected = round_number == round_num
                    if geo_display == "MISSING" or time_display == "MISSING":
                        display_text = "<b style='color:red;'>MISSING</b>"
                    else:
                        display_text = f"🌎{geo_display} &nbsp;&nbsp;📅{time_display}"

                    if is_selected:
                        st.markdown(f"<div class='round-row round-highlight'>{display_text}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='round-row'>{display_text}</div>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

        except FileNotFoundError:
            pass
        except Exception as e:
            st.error(f"Error loading score data: {e}")






# Check if all three fields are filled and valid
if name_valid and date and round_number is not None:
    # Load the CSV file to check for existing data
    try:
        df = pd.read_csv("./Data/Timeguessr_Stats.csv")
        # Convert date column to datetime for comparison
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        
        # Check if this date and round already exists
        existing_row = df[(df['Date'] == date) & (df['Timeguessr Round'] == round_number)]
        
        if len(existing_row) > 0:
            # Pre-populate with existing data
            existing_data = existing_row.iloc[0]
            row_exists = True
            default_year = str(int(existing_data['Year']))
            default_country = existing_data['Country']
            default_subdivision = existing_data.get('Subdivision', '')
            default_city = existing_data['City']
            
            # Get name-specific columns
            geo_col = f"{name} Geography Distance"
            time_col = f"{name} Time Guessed"
            
            # Check if guess data exists for this person
            guess_exists = False
            default_distance = ""
            default_distance_km = False
            default_year_guessed = ""
            
            if pd.notna(existing_data.get(geo_col)) and existing_data.get(geo_col) != '':
                guess_exists = True
                dist_meters = float(existing_data[geo_col])
                if dist_meters >= 1000:
                    default_distance = str(dist_meters / 1000)
                    default_distance_km = True
                else:
                    default_distance = str(dist_meters)
                    default_distance_km = False
            
            if pd.notna(existing_data.get(time_col)) and existing_data.get(time_col) != '':
                guess_exists = True
                default_year_guessed = str(int(existing_data[time_col]))
        else:
            row_exists = False
            guess_exists = False
            default_year = ""
            default_country = ""
            default_subdivision = ""
            default_city = ""
            default_distance = ""
            default_distance_km = False
            default_year_guessed = ""
    except FileNotFoundError:
        row_exists = False
        guess_exists = False
        default_year = ""
        default_country = ""
        default_subdivision = ""
        default_city = ""
        default_distance = ""
        default_distance_km = False
        default_year_guessed = ""
    except Exception as e:
        st.error(f"Error loading data: {e}")
        row_exists = False
        guess_exists = False
        default_year = ""
        default_country = ""
        default_subdivision = ""
        default_city = ""
        default_distance = ""
        default_distance_km = False
        default_year_guessed = ""
    
    st.divider()
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    # Left column - Actual Answers
    with col1:
        st.subheader("Actual Answers")
        
        # If row exists, add edit mode toggle
        if row_exists:
            edit_mode_actual = st.toggle("Edit Mode", value=False, key=f"edit_mode_actual_{date}_{round_number}")
        else:
            edit_mode_actual = False
        
        actual_year = st.text_input("Year", key=f"actual_year_{date}_{round_number}", value=default_year, disabled=(row_exists and not edit_mode_actual))
        
        # Validate year
        year_valid = True
        if actual_year and (not row_exists or edit_mode_actual):
            if not actual_year.isdigit() or len(actual_year) != 4:
                st.error("Year must be a 4-digit number")
                year_valid = False
            elif not (1900 <= int(actual_year) <= 2100):
                st.error("Year must be between 1900 and 2100")
                year_valid = False
        elif row_exists and not edit_mode_actual:
            year_valid = True
        
        actual_country = st.text_input("Country", key=f"actual_country_{date}_{round_number}", value=default_country, disabled=(row_exists and not edit_mode_actual))
        actual_subdivision = st.text_input("Subdivision", key=f"actual_subdivision_{date}_{round_number}", value=default_subdivision, disabled=(row_exists and not edit_mode_actual))
        actual_city = st.text_input("City", key=f"actual_city_{date}_{round_number}", value=default_city, disabled=(row_exists and not edit_mode_actual))
        
        # If in edit mode, show save button
        if row_exists and edit_mode_actual:
            if st.button("Save Changes", key="save_actual"):
                if year_valid and actual_year and actual_country and actual_city:
                    try:
                        # Load the CSV again to ensure we have the latest data
                        df = pd.read_csv("./Data/Timeguessr_Stats.csv")
                        df['Date'] = pd.to_datetime(df['Date']).dt.date
                        
                        # Find the row to update
                        mask = (df['Date'] == date) & (df['Timeguessr Round'] == round_number)
                        
                        # Update the values
                        df.loc[mask, 'Year'] = int(actual_year)
                        df.loc[mask, 'Country'] = actual_country
                        df.loc[mask, 'Subdivision'] = actual_subdivision
                        df.loc[mask, 'City'] = actual_city
                        
                        # Save back to CSV
                        df['Date'] = pd.to_datetime(df['Date'])
                        df.to_csv("./Data/Timeguessr_Stats.csv", index=False)
                        
                        st.success("Changes saved successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving changes: {e}")
                else:
                    st.error("Please fill in all required fields correctly before saving.")

        # -------------------------------
        # Submit Actual Answers (visible ONLY if the row does not already exist)
        # -------------------------------
        # Only show submit UI if this row isn't already present (row_exists == False)
        if not row_exists:
            try:
                # Compute Timeguessr Day for the selected date (used for the warning & final write)
                # Reference: 876 corresponds to 2025-10-24
                reference_date = datetime.date(2025, 10, 24)
                reference_day_number = 876
                delta_days = (date - reference_date).days
                computed_timeguessr_day = reference_day_number + delta_days

                # Check parsed CSV to see how many rounds already exist for that Timeguessr Day
                parsed_path = "./Data/Timeguessr_Actuals_Parsed.csv"
                existing_rounds_for_day = 0
                if os.path.exists(parsed_path):
                    try:
                        parsed_df_check = pd.read_csv(parsed_path)
                        # Ensure Timeguessr Day column is numeric if possible
                        if "Timeguessr Day" in parsed_df_check.columns:
                            parsed_df_check["Timeguessr Day"] = pd.to_numeric(parsed_df_check["Timeguessr Day"], errors="coerce")
                            existing_rounds_for_day = int(parsed_df_check[parsed_df_check["Timeguessr Day"] == computed_timeguessr_day].shape[0])
                    except Exception:
                        existing_rounds_for_day = 0

                # If between 1 and 4 rounds already exist for that day, show the warning under the button
                # We'll display the warning below the button per your spec, but compute it now so we can show it immediately.
                submit_col_placeholder = st.empty()
                # Show the Submit button (always available when not row_exists)
                if submit_col_placeholder.button("Submit Actual Answers", key=f"submit_actual_{date}_{round_number}"):
                    # Validate required fields before writing
                    if actual_year and actual_country and actual_city and year_valid:
                        try:
                            # Build the row to append
                            new_row = {
                                "Timeguessr Day": int(computed_timeguessr_day),
                                "Timeguessr Round": int(round_number),
                                "City": actual_city,
                                "Subdivision": actual_subdivision,
                                "Country": actual_country,
                                "Year": int(actual_year)
                            }

                            # Read existing parsed file or create a new DataFrame
                            if os.path.exists(parsed_path):
                                parsed_df = pd.read_csv(parsed_path)
                                # Remove any existing entry for same day & round (avoid duplicates)
                                parsed_df = parsed_df[~((pd.to_numeric(parsed_df.get("Timeguessr Day"), errors="coerce") == new_row["Timeguessr Day"]) &
                                                        (pd.to_numeric(parsed_df.get("Timeguessr Round"), errors="coerce") == new_row["Timeguessr Round"]))]
                                parsed_df = pd.concat([parsed_df, pd.DataFrame([new_row])], ignore_index=True)
                            else:
                                parsed_df = pd.DataFrame([new_row])

                            # Ensure column order (optional)
                            cols_order = ["Timeguessr Round", "City", "Subdivision", "Country", "Year", "Timeguessr Day"]
                            # Reorder if possible, otherwise just save
                            try:
                                parsed_df = parsed_df[[c for c in cols_order if c in parsed_df.columns] + [c for c in parsed_df.columns if c not in cols_order]]
                            except Exception:
                                pass

                            parsed_df.to_csv(parsed_path, index=False)
                            st.success("Actual answers submitted successfully!")

                            # After writing, recompute how many rounds exist for this day and show warning if needed
                            num_rounds = int(parsed_df[pd.to_numeric(parsed_df.get("Timeguessr Day"), errors="coerce") == new_row["Timeguessr Day"]].shape[0])
                            if 0 < num_rounds < 5:
                                st.warning("WARNING: Not all rounds have actual answers inputted yet")
                            # Optionally, you could st.experimental_rerun() here if you want the UI to refresh
                        except Exception as e:
                            st.error(f"Error submitting actual answers: {e}")
                    else:
                        st.error("Please fill out all actual answer fields correctly before submitting.")
                # Show warning under the button when parsed file already has between 1 and 4 rounds
                if 0 < existing_rounds_for_day < 5:
                    st.warning("WARNING: Not all rounds have actual answers inputted yet")
            except Exception as e:
                # Defensive: show an error if something unexpected happens while preparing submit UI
                st.error(f"Error preparing submit UI: {e}")

    
    # Right column - Guessed Information
    with col2:
        st.subheader(f"{name}'s Guesses")
        
        # If guess exists, add edit mode toggle
        if guess_exists:
            edit_mode_guess = st.toggle("Edit Mode", value=False, key=f"edit_mode_guess_{date}_{round_number}")
        else:
            edit_mode_guess = False
        
        st.write("Distance Off")
        
        # Set up distance unit toggle with default value
        if guess_exists and not edit_mode_guess:
            distance_unit_toggle = st.toggle("kilometers" if default_distance_km else "meters", 
                                            value=default_distance_km, 
                                            key=f'distance_unit_toggle_{date}_{round_number}',
                                            disabled=True)
        else:
            distance_unit_toggle = st.toggle("kilometers" if st.session_state.get(f'distance_unit_toggle_{date}_{round_number}', default_distance_km) else "meters", 
                                            value=st.session_state.get(f'distance_unit_toggle_{date}_{round_number}', default_distance_km), 
                                            key=f'distance_unit_toggle_{date}_{round_number}')
        
        distance_off = st.text_input("", key=f"distance_off_{date}_{round_number}", 
                                     value=default_distance, 
                                     label_visibility="collapsed",
                                     disabled=(guess_exists and not edit_mode_guess))
        
        # Validate and calculate geography score
        if distance_off:
            try:
                dist_input = float(distance_off)
                if dist_input < 0:
                    st.error("Distance must be a positive number")
                else:
                    # Convert to meters if in kilometers
                    dist = dist_input * 1000 if distance_unit_toggle else dist_input
                    
                    # Calculate score based on conditions
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
                    
                    # Find which condition is true and get corresponding score
                    geo_score = 0
                    for condition, score in zip(conditions, scores):
                        if condition:
                            geo_score = score
                            break
                    
                    st.success(f"Geography Score: {geo_score:.2f}")
            except ValueError:
                st.error("Distance must be a numeric value")
        
        year_guessed = st.text_input("Year Guessed", key=f"year_guessed_{date}_{round_number}",
                                     value=default_year_guessed,
                                     disabled=(guess_exists and not edit_mode_guess))
        
        # Validate year guessed
        year_guessed_valid = False
        if year_guessed:
            if not year_guessed.isdigit() or len(year_guessed) != 4:
                st.error("Year must be a 4-digit number")
            elif not (1900 <= int(year_guessed) <= 2100):
                st.error("Year must be between 1900 and 2100")
            else:
                year_guessed_valid = True
                
                # Calculate time score if actual year is provided
                if actual_year and year_valid:
                    years_off = abs(int(year_guessed) - int(actual_year))
                    
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
                    
                    st.success(f"Time Score: {time_score}")
                
                # Show year ranges if actual year is not provided
                elif not actual_year or not year_valid:
                    guessed = int(year_guessed)
                    st.info("**Point Ranges:**")
                    st.write(f"5000 pts - {guessed}")
                    st.write(f"4950 pts - {guessed-1} & {guessed+1}")
                    st.write(f"4800 pts - {guessed-2} & {guessed+2}")
                    st.write(f"4600 pts - {guessed-3} & {guessed+3}")
                    st.write(f"4300 pts - {guessed-4} & {guessed+4}")
                    st.write(f"3900 pts - {guessed-5} & {guessed+5}")
                    st.write(f"3400 pts - {guessed-7}-{guessed-6} & {guessed+6}-{guessed+7}")
                    st.write(f"2500 pts - {guessed-10}-{guessed-8} & {guessed+8}-{guessed+10}")
                    st.write(f"2000 pts - {guessed-15}-{guessed-11} & {guessed+11}-{guessed+15}")
                    st.write(f"1000 pts - {guessed-20}-{guessed-16} & {guessed+16}-{guessed+20}")
                    st.write(f"0 pts - All other years")
        
        # If in edit mode for guesses, show save button
        if guess_exists and edit_mode_guess:
            if st.button("Save Changes", key="save_guess"):
                if distance_off and year_guessed_valid:
                    try:
                        # Load the CSV again to ensure we have the latest data
                        df = pd.read_csv("./Data/Timeguessr_Stats.csv")
                        df['Date'] = pd.to_datetime(df['Date']).dt.date
                        
                        # Find the row to update
                        mask = (df['Date'] == date) & (df['Timeguessr Round'] == round_number)
                        
                        # Convert distance to meters
                        dist_meters = float(distance_off) * 1000 if distance_unit_toggle else float(distance_off)
                        
                        # Update the values
                        geo_col = f"{name} Geography Distance"
                        time_col = f"{name} Time Guessed"
                        df.loc[mask, geo_col] = dist_meters
                        df.loc[mask, time_col] = int(year_guessed)
                        
                        # Save back to CSV
                        df['Date'] = pd.to_datetime(df['Date'])
                        df.to_csv("./Data/Timeguessr_Stats.csv", index=False)
                        
                        st.success("Guess changes saved successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving guess changes: {e}")
                else:
                    st.error("Please fill in all fields correctly before saving.")

                # -------------------------------
        # Submit Guesses (visible ONLY if no default guesses exist)
        # -------------------------------
        if not guess_exists:
            try:
                # Compute Timeguessr Day same way as in actual answers
                reference_date = datetime.date(2025, 10, 24)
                reference_day_number = 876
                delta_days = (date - reference_date).days
                computed_timeguessr_day = reference_day_number + delta_days

                parsed_path = f"./Data/Timeguessr_{name}_Parsed.csv"

                # Show submit button
                if st.button("Submit Guesses", key=f"submit_guesses_{date}_{round_number}"):
                    # Validate inputs
                    if distance_off and year_guessed_valid:
                        try:
                            dist_val = float(distance_off)
                            if dist_val < 0:
                                st.error("Distance must be positive.")
                            else:
                                # Convert km → meters if needed
                                dist_meters = int(dist_val * 1000) if distance_unit_toggle else int(dist_val)
                                year_val = int(year_guessed)

                                new_row = {
                                    "Timeguessr Day": int(computed_timeguessr_day),
                                    "Timeguessr Round": int(round_number),
                                    f"{name} Geography Distance": dist_meters,
                                    f"{name} Time Guessed": year_val
                                }

                                # Append or create CSV
                                if os.path.exists(parsed_path):
                                    parsed_df = pd.read_csv(parsed_path)
                                    # Remove any duplicates for same day & round
                                    parsed_df = parsed_df[
                                        ~((pd.to_numeric(parsed_df.get("Timeguessr Day"), errors="coerce") == new_row["Timeguessr Day"]) &
                                          (pd.to_numeric(parsed_df.get("Timeguessr Round"), errors="coerce") == new_row["Timeguessr Round"]))]
                                    parsed_df = pd.concat([parsed_df, pd.DataFrame([new_row])], ignore_index=True)
                                else:
                                    parsed_df = pd.DataFrame([new_row])

                                # Column order
                                cols_order = ["Timeguessr Day", "Timeguessr Round", 
                                              f"{name} Geography Distance", f"{name} Time Guessed"]
                                try:
                                    parsed_df = parsed_df[[c for c in cols_order if c in parsed_df.columns] + 
                                                          [c for c in parsed_df.columns if c not in cols_order]]
                                except Exception:
                                    pass

                                # Save file
                                parsed_df.to_csv(parsed_path, index=False)
                                st.success(f"Guesses submitted successfully to {parsed_path}!")
                        except ValueError:
                            st.error("Distance must be numeric.")
                        except Exception as e:
                            st.error(f"Error submitting guesses: {e}")
                    else:
                        st.error("Please fill out all guess fields correctly before submitting.")
            except Exception as e:
                st.error(f"Error preparing submit guesses UI: {e}")
