import streamlit as st
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import os


st.title("Score Submission")

def score_update():
    michael_csv = "Data/Timeguessr_Michael_Parsed.csv"
    sarah_csv   = "Data/Timeguessr_Sarah_Parsed.csv"
    actuals_csv = "Data/Timeguessr_Actuals_Parsed.csv"
    df_michael = pd.read_csv(michael_csv)
    df_sarah   = pd.read_csv(sarah_csv)
    df_actuals = pd.read_csv(actuals_csv)

    df_all = pd.merge(df_michael, df_sarah, on=["Timeguessr Day", "Timeguessr Round"], how="outer")
    df_all = pd.merge(df_all, df_actuals, on=["Timeguessr Day", "Timeguessr Round"], how="left")
    
    # Add calculated total score tracking columns if they don't exist
    for player in ["Michael", "Sarah"]:
        calc_col = f"{player} Calculated Total Score"
        total_col = f"{player} Total Score"
        
        if calc_col not in df_all.columns:
            # Existing rows were manually added, so default to False
            # Only set to True if Total Score is NaN (meaning it's not been set yet)
            df_all[calc_col] = df_all[total_col].isna()

    if "Michael Time Distance" in df_all.columns and "Michael Time Guessed" in df_all.columns:
        mask = df_all["Michael Time Distance"].isna() & df_all["Michael Time Guessed"].notna() & df_all["Year"].notna()
        df_all.loc[mask, "Michael Time Distance"] = abs(df_all.loc[mask, "Year"] - df_all.loc[mask, "Michael Time Guessed"])

    # For Sarah
    if "Sarah Time Distance" in df_all.columns and "Sarah Time Guessed" in df_all.columns:
        mask = df_all["Sarah Time Distance"].isna() & df_all["Sarah Time Guessed"].notna() & df_all["Year"].notna()
        df_all.loc[mask, "Sarah Time Distance"] = abs(df_all.loc[mask, "Year"] - df_all.loc[mask, "Sarah Time Guessed"])

    # --- Add Date column first ---
    start_date = pd.Timestamp("2025-03-20")
    df_all["Date"] = start_date + pd.to_timedelta(df_all["Timeguessr Day"] - df_all["Timeguessr Day"].min(), unit="D")

    # Move Date to first column, keep City, Country, Year early
    cols = ["Date", "Timeguessr Day", "Timeguessr Round", "City", "Subdivision", "Country", "Year"] + [c for c in df_all.columns if c not in ["Date", "Timeguessr Day", "Timeguessr Round", "City", "Subdivision",  "Country", "Year"]]
    df_all = df_all[cols]

    # Sort and reset
    df_all = df_all.sort_values(["Timeguessr Day", "Timeguessr Round"]).reset_index(drop=True)

    # Handle Time scores
    for player in ["Michael", "Sarah"]:
        time_col = f"{player} Time"
        time_score_col = f"{player} Time Score"
        time_dist_col = f"{player} Time Distance"
        
        # Set score to 5000 for "OOO"
        mask = df_all[time_score_col].isna() & (df_all[time_col] == "OOO")
        df_all.loc[mask, time_score_col] = 5000
        
        # Set score to 1000 for "%XX"
        mask = df_all[time_score_col].isna() & (df_all[time_col] == "%XX")
        df_all.loc[mask, time_score_col] = 1000
        
        # Set score to 0 for "XXX"
        mask = df_all[time_score_col].isna() & (df_all[time_col] == "XXX")
        df_all.loc[mask, time_score_col] = 0

        def calc_time_score(yearsOff):
            if pd.isna(yearsOff):
                return None
            yearsOff = float(yearsOff)

            if yearsOff == 0:
                return 5000
            elif yearsOff == 1:
                return 4950
            elif yearsOff == 2:
                return 4800
            elif yearsOff == 3:
                return 4600
            elif yearsOff == 4:
                return 4300
            elif yearsOff == 5:
                return 3900
            elif yearsOff in [6, 7]:
                return 3400
            elif yearsOff in [8, 9, 10]:
                return 2500
            elif 10 < yearsOff < 16:
                return 2000
            elif 15 < yearsOff < 21:
                return 1000
            else:
                return 0
            
        # Apply the conversion
        mask = df_all[time_score_col].isna()  # only fill if not already set by OOO/%XX/XXX
        df_all.loc[mask, time_score_col] = df_all.loc[mask, time_dist_col].apply(calc_time_score)

        # Set Time pattern based on calculated score (only if pattern is empty/NA)
        if time_col in df_all.columns:
            # OOO pattern (5000 pts)
            mask = df_all[time_col].isna() & (df_all[time_score_col] == 5000)
            df_all.loc[mask, time_col] = "OOO"
            
            # OO% pattern (4800-4950 pts)
            mask = df_all[time_col].isna() & df_all[time_score_col].between(4800, 4950)
            df_all.loc[mask, time_col] = "OO%"
            
            # OOX pattern (4300-4600 pts)
            mask = df_all[time_col].isna() & df_all[time_score_col].between(4300, 4600)
            df_all.loc[mask, time_col] = "OOX"
            
            # O%X pattern (3400-3900 pts)
            mask = df_all[time_col].isna() & df_all[time_score_col].between(3400, 3900)
            df_all.loc[mask, time_col] = "O%X"
            
            # OXX pattern (2000-2500 pts)
            mask = df_all[time_col].isna() & df_all[time_score_col].between(2000, 2500)
            df_all.loc[mask, time_col] = "OXX"
            
            # %XX pattern (1000 pts)
            mask = df_all[time_col].isna() & (df_all[time_score_col] == 1000)
            df_all.loc[mask, time_col] = "%XX"
            
            # XXX pattern (0 pts)
            mask = df_all[time_col].isna() & (df_all[time_score_col] == 0)
            df_all.loc[mask, time_col] = "XXX"
        
    # --- Add min/max columns for Time and Geography scores ---
    for player in ["Michael", "Sarah"]:
        # Time Score min/max
        time_score_col = f"{player} Time Score"
        time_col = f"{player} Time"
        time_min_col = f"{player} Time Score (Min)"
        time_max_col = f"{player} Time Score (Max)"
        
        if time_score_col in df_all.columns:
            df_all[time_min_col] = np.nan
            df_all[time_max_col] = np.nan
            
            # If time score exists, use it for both min and max
            mask = df_all[time_score_col].notna()
            df_all.loc[mask, time_min_col] = df_all.loc[mask, time_score_col]
            df_all.loc[mask, time_max_col] = df_all.loc[mask, time_score_col]
            
            # For missing time scores, set min/max based on pattern
            if time_col in df_all.columns:
                # OO% pattern
                mask = df_all[time_score_col].isna() & (df_all[time_col] == "OO%")
                df_all.loc[mask, time_min_col] = 4800
                df_all.loc[mask, time_max_col] = 4950
                
                # OOX pattern
                mask = df_all[time_score_col].isna() & (df_all[time_col] == "OOX")
                df_all.loc[mask, time_min_col] = 4300
                df_all.loc[mask, time_max_col] = 4600
                
                # O%X pattern
                mask = df_all[time_score_col].isna() & (df_all[time_col] == "O%X")
                df_all.loc[mask, time_min_col] = 3400
                df_all.loc[mask, time_max_col] = 3900
                
                # OXX pattern
                mask = df_all[time_score_col].isna() & (df_all[time_col] == "OXX")
                df_all.loc[mask, time_min_col] = 2000
                df_all.loc[mask, time_max_col] = 2500   

    # --- Fill missing Round Scores if both component scores exist ---
    for player in ["Michael", "Sarah"]:
        time_col = f"{player} Time Score"
        geo_col = f"{player} Geography Score"
        round_col = f"{player} Round Score"

        if all(c in df_all.columns for c in [time_col, geo_col, round_col]):
            mask = df_all[round_col].isna() & df_all[time_col].notna() & df_all[geo_col].notna()
            df_all.loc[mask, round_col] = df_all.loc[mask, time_col] + df_all.loc[mask, geo_col]

    # --- Calculate Total Scores for rows marked as calculated ---
    for player in ["Michael", "Sarah"]:
        calc_col = f"{player} Calculated Total Score"
        total_col = f"{player} Total Score"
        time_col = f"{player} Time Score"
        geo_col = f"{player} Geography Score"
        
        if all(c in df_all.columns for c in [calc_col, total_col, time_col, geo_col]):
            # Group by Timeguessr Day to calculate totals
            for day in df_all["Timeguessr Day"].unique():
                day_mask = df_all["Timeguessr Day"] == day
                
                # Check if this day should have calculated total (use first row's value for the day)
                day_rows = df_all[day_mask]
                if len(day_rows) > 0:
                    is_calculated = day_rows[calc_col].iloc[0]
                    
                    if is_calculated:
                        # Sum all time and geo scores for this day
                        time_sum = day_rows[time_col].sum()
                        geo_sum = day_rows[geo_col].sum()
                        total = time_sum + geo_sum
                        
                        # Set total score for all rows of this day
                        df_all.loc[day_mask, total_col] = total

    df_all.to_csv("Data/Timeguessr_Stats.csv", index=False)

# Create two columns - left for inputs, right for score display
input_col, score_col = st.columns([2, 1])

with input_col:
    # Top section - Name, Date, Round Number
    date = st.date_input(
    "Date",
    value=datetime.date.today(),
    max_value=datetime.date.today()
)
    round_number = st.selectbox("Round Number", options=[None, 1, 2, 3, 4, 5], format_func=lambda x: "Select a round" if x is None else str(x))

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
                geo_sum = all_rounds[f"{name} Geography Score"].fillna(0).sum()
                time_sum = all_rounds[f"{name} Time Score"].fillna(0).sum()

                # wrap in score-container which is moved up via CSS
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
                
                # Manual total score override toggle
                manual_override = st.toggle("Manually Replace Total Score", key=f"manual_override_{name}_{date}")
                
                if manual_override:
                    new_total_score = st.number_input(
                        "New Total Score",
                        min_value=0,
                        max_value=50000,
                        value=int(total_score) if pd.notna(total_score) else 0,
                        step=1,
                        key=f"new_total_{name}_{date}"
                    )
                    
                    if st.button("Save Manual Total Score", key=f"save_manual_total_{name}_{date}"):
                        try:
                            stats_df = pd.read_csv("./Data/Timeguessr_Stats.csv")
                            stats_df["Date"] = pd.to_datetime(stats_df["Date"]).dt.date
                            
                            # Update all rows for this date/person combo
                            mask = stats_df["Date"] == date
                            stats_df.loc[mask, total_score_col] = new_total_score
                            stats_df.loc[mask, f"{name} Calculated Total Score"] = False
                            
                            stats_df.to_csv("./Data/Timeguessr_Stats.csv", index=False)
                            st.success(f"Total score manually set to {new_total_score:,}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving manual total score: {e}")

        except FileNotFoundError:
            pass
        except Exception as e:
            st.error(f"Error loading score data: {e}")






# Check if all three fields are filled and valid
if name_valid and date and round_number is not None:
    # Convert date to Timeguessr Day (days since reference point)
    # October 28, 2025 = Day 880
    reference_date = datetime.date(2025, 10, 28)
    timeguessr_day = 880 + (date - reference_date).days
    
    # Load the CSV files to check for existing data
    try:
        # Check actuals file
        try:
            actuals_df = pd.read_csv("./Data/Timeguessr_Actuals_Parsed.csv")
            
            existing_actual = actuals_df[(actuals_df['Timeguessr Day'] == timeguessr_day) & (actuals_df['Timeguessr Round'] == round_number)]
            
            if len(existing_actual) > 0:
                actual_exists = True
                existing_data = existing_actual.iloc[0]
                default_year = str(int(existing_data['Year']))
                default_country = existing_data['Country']
                default_subdivision = existing_data.get('Subdivision', '')
                default_city = existing_data['City']
            else:
                actual_exists = False
                default_year = ""
                default_country = ""
                default_subdivision = ""
                default_city = ""
        except FileNotFoundError:
            actual_exists = False
            default_year = ""
            default_country = ""
            default_subdivision = ""
            default_city = ""
        
        # Check person-specific guess file
        guess_file = f"./Data/Timeguessr_{name}_Parsed.csv"
        try:
            guess_df = pd.read_csv(guess_file)
            
            existing_guess = guess_df[(guess_df['Timeguessr Day'] == timeguessr_day) & (guess_df['Timeguessr Round'] == round_number)]
            
            if len(existing_guess) > 0:
                guess_exists = True
                guess_data = existing_guess.iloc[0]
                
                default_distance = ""
                default_distance_km = False
                default_year_guessed = ""
                
                if pd.notna(guess_data.get(f'{name} Geography Distance')) and guess_data.get( f'{name} Geography Distance') != '':
                    dist_meters = float(guess_data[f'{name} Geography Distance'])
                    if dist_meters >= 1000:
                        default_distance = str(dist_meters / 1000)
                        default_distance_km = True
                    else:
                        default_distance = str(dist_meters)
                        default_distance_km = False
                
                if pd.notna(guess_data.get(f'{name} Time Guessed')) and guess_data.get(f'{name} Time Guessed') != '':
                    default_year_guessed = str(int(guess_data[f'{name} Time Guessed']))
            else:
                guess_exists = False
                default_distance = ""
                default_distance_km = False
                default_year_guessed = ""
        except FileNotFoundError:
            guess_exists = False
            default_distance = ""
            default_distance_km = False
            default_year_guessed = ""
            
    except Exception as e:
        st.error(f"Error loading data: {e}")
        actual_exists = False
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

    actual_year = None
    year_valid = False
    
    # Left column - Actual Answers
    with col1:
        st.subheader("Actual Answers")

        # --- Prevent submitting current round if previous round not yet submitted ---
        # (Skip this check for Round 1)
        must_block = False
        if round_number != 1:
            parsed_path = "./Data/Timeguessr_Actuals_Parsed.csv"
            if os.path.exists(parsed_path):
                try:
                    parsed_df_check = pd.read_csv(parsed_path)
                    parsed_df_check["Timeguessr Round"] = pd.to_numeric(parsed_df_check["Timeguessr Round"], errors="coerce")
                    parsed_df_check["Timeguessr Day"] = pd.to_numeric(parsed_df_check["Timeguessr Day"], errors="coerce")

                    # Compute Timeguessr Day for the selected date
                    reference_date = datetime.date(2025, 10, 24)
                    reference_day_number = 876
                    delta_days = (date - reference_date).days
                    computed_timeguessr_day = reference_day_number + delta_days

                    # Check if previous round is in parsed file
                    prev_round_exists = (
                        (parsed_df_check["Timeguessr Day"] == computed_timeguessr_day) &
                        (parsed_df_check["Timeguessr Round"] == round_number - 1)
                    ).any()

                    if not prev_round_exists:
                        must_block = True
                except Exception:
                    pass
            else:
                must_block = True

        # If previous round missing, show warning and skip rest of actual input section
        if must_block:
            st.warning("⚠️ You Must Submit Previous Round First")
        else:
        
            # If row exists, add edit mode toggle
            if actual_exists:
                edit_mode_actual = st.toggle("Edit Mode", value=False, key=f"edit_mode_actual_{date}_{round_number}")
            else:
                edit_mode_actual = False
            
            actual_year = st.text_input("Year", key=f"actual_year_{date}_{round_number}", value=default_year, disabled=(actual_exists and not edit_mode_actual))
            
            # Validate year
            year_valid = True
            if actual_year and (not actual_exists or edit_mode_actual):
                if not actual_year.isdigit() or len(actual_year) != 4:
                    st.error("Year must be a 4-digit number")
                    year_valid = False
                elif not (1900 <= int(actual_year) <= date.year):
                    st.error(f"Year must be between 1900 and {date.year}")
                    year_valid = False
            elif actual_exists and not edit_mode_actual:
                year_valid = True
            
            actual_country = st.text_input("Country", key=f"actual_country_{date}_{round_number}", value=default_country, disabled=(actual_exists and not edit_mode_actual))
            actual_subdivision = st.text_input("Subdivision", key=f"actual_subdivision_{date}_{round_number}", value=default_subdivision, disabled=(actual_exists and not edit_mode_actual))
            actual_city = st.text_input("City", key=f"actual_city_{date}_{round_number}", value=default_city, disabled=(actual_exists and not edit_mode_actual))
            
            # If in edit mode, show save button
            if actual_exists and edit_mode_actual:
                if st.button("Save Changes", key="save_actual"):
                    if year_valid and actual_year and actual_country and actual_city:
                        try:
                            # Load the Actuals CSV to update
                            actuals_path = "./Data/Timeguessr_Actuals_Parsed.csv"
                            
                            # Convert date to Timeguessr Day
                            reference_date = datetime.date(2025, 10, 28)
                            timeguessr_day = 880 + (date - reference_date).days
                            
                            actuals_df = pd.read_csv(actuals_path)
                            
                            # Find the row to update
                            mask = (actuals_df['Timeguessr Day'] == timeguessr_day) & (actuals_df['Timeguessr Round'] == round_number)
                            
                            # Update existing row
                            actuals_df.loc[mask, 'Year'] = int(actual_year)
                            actuals_df.loc[mask, 'Country'] = actual_country
                            actuals_df.loc[mask, 'Subdivision'] = actual_subdivision
                            actuals_df.loc[mask, 'City'] = actual_city
                            
                            # Sort by Timeguessr Day and then Timeguessr Round
                            actuals_df = actuals_df.sort_values(by=['Timeguessr Day', 'Timeguessr Round'])

                            
                            # Save back to CSV
                            actuals_df.to_csv(actuals_path, index=False)

                            score_update()
                            st.success("Changes saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving changes: {e}")
                    else:
                        st.error("Please fill in all required fields correctly before saving.")

            # -------------------------------
            # Submit Actual Answers (visible ONLY if the row does not already exist)
            # -------------------------------
            # Only show submit UI if this row isn't already present (actual_exists == False)
            if not actual_exists:
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
                    # Show the Submit button (always available when not actual_exists)
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

                                parsed_df = parsed_df.sort_values(by=['Timeguessr Day', 'Timeguessr Round'])
                                
                                parsed_df.to_csv(parsed_path, index=False)
                                score_update()
                                st.success("Actual answers submitted successfully!")

                                # After writing, recompute how many rounds exist for this day and show warning if needed
                                num_rounds = int(parsed_df[pd.to_numeric(parsed_df.get("Timeguessr Day"), errors="coerce") == new_row["Timeguessr Day"]].shape[0])
                                if 0 < num_rounds < 5:
                                    st.warning("WARNING: Not all rounds have actual answers inputted yet")
                                # Optionally, you could st.experimental_rerun() here if you want the UI to refresh
                                st.rerun()
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

            # --- NEW: Check if previous round is submitted ---
        previous_round_missing = False
        if round_number != 1:  # Only check for rounds after the first
            parsed_path = f"./Data/Timeguessr_{name}_Parsed.csv"
            if os.path.exists(parsed_path):
                parsed_df_check = pd.read_csv(parsed_path)
                parsed_df_check["Timeguessr Round"] = pd.to_numeric(parsed_df_check["Timeguessr Round"], errors="coerce")
                parsed_df_check["Timeguessr Day"] = pd.to_numeric(parsed_df_check["Timeguessr Day"], errors="coerce")

                # Compute current Timeguessr Day the same way as before
                reference_date = datetime.date(2025, 10, 24)
                reference_day_number = 876
                delta_days = (date - reference_date).days
                computed_timeguessr_day = reference_day_number + delta_days

                # Check if previous round exists for this day
                has_prev = (
                    (parsed_df_check["Timeguessr Day"] == computed_timeguessr_day)
                    & (parsed_df_check["Timeguessr Round"] == (round_number - 1))
                ).any()

                if not has_prev:
                    previous_round_missing = True
            else:
                previous_round_missing = True  # No file at all means nothing is submitted yet

        
        # If guess exists, add edit mode toggle
        if previous_round_missing:
            st.warning("⚠️ You Must Submit Previous Round First")
        else:
            # (everything below stays the same and just gets indented once)
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
                elif not (1900 <= int(year_guessed) <= date.year):
                    st.error(f"Year must be between 1900 and {date.year}")
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
                            # Load the person-specific guess CSV to update
                            guess_path = f"./Data/Timeguessr_{name}_Parsed.csv"
                            
                            # Convert date to Timeguessr Day
                            reference_date = datetime.date(2025, 10, 28)
                            timeguessr_day = 880 + (date - reference_date).days
                            
                            # Convert distance to meters
                            dist_meters = float(distance_off) * 1000 if distance_unit_toggle else float(distance_off)
                            
                            guess_df = pd.read_csv(guess_path)
                            
                            # Find the row to update
                            mask = (guess_df['Timeguessr Day'] == timeguessr_day) & (guess_df['Timeguessr Round'] == round_number)
                            
                            # Update existing row
                            guess_df.loc[mask, f'{name} Geography Distance'] = int(dist_meters)
                            guess_df.loc[mask, f'{name} Time Guessed'] = int(year_guessed)
                            
                            # Sort by Timeguessr Day and then Timeguessr Round
                            guess_df = guess_df.sort_values(by=['Timeguessr Day', 'Timeguessr Round'])

                            # Save back to CSV
                            guess_df.to_csv(guess_path, index=False)

                            score_update()
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
                                        if 4750 <= x <= 4999:
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
                                            return None  # score outside defined ranges
                                        
                                    geo_score = geography_score(dist_meters)
                                    geo_pattern = geography_pattern(geo_score)

                                    new_row = {
                                        "Timeguessr Day": int(computed_timeguessr_day),
                                        "Timeguessr Round": int(round_number),
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
                                        f"{name} Calculated Total Score": True,  # ADD THIS LINE
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

                                    parsed_df = parsed_df.sort_values(by=['Timeguessr Day', 'Timeguessr Round'])

                                    # Save file
                                    parsed_df.to_csv(parsed_path, index=False)
                                    score_update()
                                    st.success(f"Guesses submitted successfully to {parsed_path}!")
                                    st.rerun()
                            except ValueError:
                                st.error("Distance must be numeric.")
                            except Exception as e:
                                st.error(f"Error submitting guesses: {e}")
                        else:
                            st.error("Please fill out all guess fields correctly before submitting.")
                except Exception as e:
                    st.error(f"Error preparing submit guesses UI: {e}")
