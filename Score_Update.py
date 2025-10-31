import pandas as pd
import numpy as np

def score_update():
    michael_csv = "Data/Timeguessr_Michael_Parsed.csv"
    sarah_csv   = "Data/Timeguessr_Sarah_Parsed.csv"
    actuals_csv = "Data/Timeguessr_Actuals_Parsed.csv"
    df_michael = pd.read_csv(michael_csv)
    df_sarah   = pd.read_csv(sarah_csv)
    df_actuals = pd.read_csv(actuals_csv)

    df_all = pd.merge(df_michael, df_sarah, on=["Timeguessr Day", "Timeguessr Round"], how="outer")
    df_all = pd.merge(df_all, df_actuals, on=["Timeguessr Day", "Timeguessr Round"], how="left")

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

    df_all.to_csv("Data/Timeguessr_Stats.csv", index=False)