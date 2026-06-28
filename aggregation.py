import os
import re
import numpy as np
import pandas as pd

MICHAEL_TXT = "Data/TimeGuessr_Michael.txt"
SARAH_TXT   = "Data/TimeGuessr_Sarah.txt"
ACTUALS_TXT = "Data/TimeGuessr_Actuals.txt"
STATS_CSV   = "Data/Timeguessr_Stats.csv"


def _needs_update():
    if not os.path.exists(STATS_CSV):
        return True
    stats_mtime = os.path.getmtime(STATS_CSV)
    return any(
        os.path.getmtime(p) > stats_mtime
        for p in (MICHAEL_TXT, SARAH_TXT, ACTUALS_TXT)
        if os.path.exists(p)
    )


def parse_user_blocks(lines, user):
    user_data = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith("TimeGuessr"):
            m = re.search(r"TimeGuessr #(\d+)\s+[—-]?\s*([\d,]+)/50,000", line)
            if m:
                day = int(m.group(1))
                total_score = int(m.group(2).replace(",", ""))
                rounds = []
                j = i + 1

                # CASE 1: Emoji keycap rounds (1️⃣ … 5️⃣ …)
                if j < len(lines) and re.search(r"[1-5]️⃣", lines[j]) and "🏆" in lines[j]:
                    rounds_found = 0
                    k = j
                    while k < len(lines) and rounds_found < 5:
                        line_text = lines[k]
                        if re.search(r"[1-5]️⃣", line_text) and "🏆" in line_text:
                            match = re.search(
                                r"🏆(\d+)\s*-\s*📅(\d+)y\s*-\s*🌍([\d.]+\s*\w+)",
                                line_text
                            )
                            if match:
                                rounds.append({
                                    "Round Score": int(match.group(1)),
                                    "Time Distance": int(match.group(2)),
                                    "Geography Distance": match.group(3).strip(),
                                    "Time Guessed": np.nan,
                                    "Time Score": np.nan,
                                    "Geography Score": np.nan,
                                    "Geography": np.nan,
                                    "Time": np.nan,
                                })
                                rounds_found += 1
                        k += 1
                    i = k

                # CASE 2: Detailed format with scores (Year: X. Location: Y)
                elif j < len(lines) and "Year:" in lines[j] and "Location:" in lines[j]:
                    for k in range(j, j + 5):
                        if k >= len(lines):
                            break
                        detailed_match = re.search(
                            r"🌎([🟩🟨⬛️]*)\s*📅([🟩🟨⬛️]*)\s+(?:([^,]+),\s*)?(\d{3,4}),\s*([\d.]+\s*\w+)\.\s*Year:\s*(\d+)\.\s*Location:\s*(\d+)",
                            lines[k]
                        )
                        if detailed_match:
                            time_score = int(detailed_match.group(6))
                            geography_score = int(detailed_match.group(7))
                            rounds.append({
                                "Round Score": time_score + geography_score,
                                "Geography Distance": detailed_match.group(5).strip(),
                                "Time Distance": np.nan,
                                "Time Guessed": int(detailed_match.group(4)),
                                "Time Score": time_score,
                                "Geography Score": geography_score,
                                "Geography": detailed_match.group(1),
                                "Time": detailed_match.group(2),
                            })
                    i += 6

                # CASE 3: Ultra-simplified format (year, distance only — no scores)
                elif j < len(lines) and lines[j].startswith("🌎"):
                    test_line = lines[j]
                    # Modified to check for any word characters (\w+) instead of just k?m
                    if re.search(r"\d{3,4},\s*[\d.]+\s*\w+", test_line) and "Year:" not in test_line:
                        for k in range(j, j + 5):
                            if k >= len(lines):
                                break
                            simple_match = re.search(
                                r"🌎([🟩🟨⬛️]*)\s*📅([🟩🟨⬛️]*)\s+(?:([^,]+),\s*)?(\d{3,4}),\s*([\d.]+)\s*(\w+)",
                                lines[k]
                            )
                            if simple_match:
                                rounds.append({
                                    "Round Score": np.nan,
                                    "Geography Distance": f"{simple_match.group(5)} {simple_match.group(6)}",
                                    "Time Distance": np.nan,
                                    "Time Guessed": int(simple_match.group(4)),
                                    "Time Score": np.nan,
                                    "Geography Score": np.nan,
                                    "Geography": simple_match.group(1),
                                    "Time": simple_match.group(2),
                                })
                            else:
                                print(f"Failed to match line {k}: {lines[k]}")
                        i += 6
                    else:
                        for k in range(i + 1, i + 6):
                            if k < len(lines) and lines[k].startswith("🌎"):
                                r = re.search(r"🌎([🟩🟨⬛️]*)\s+📅([🟩🟨⬛️]*)", lines[k])
                                if r:
                                    rounds.append({
                                        "Round Score": np.nan,
                                        "Geography": r.group(1),
                                        "Geography Distance": np.nan,
                                        "Time": r.group(2),
                                        "Time Distance": np.nan,
                                        "Time Guessed": np.nan,
                                        "Time Score": np.nan,
                                        "Geography Score": np.nan,
                                    })
                        i += 6

                for rnum, rd in enumerate(rounds, start=1):
                    user_data.append({
                        "Timeguessr Day": day,
                        "Timeguessr Round": rnum,
                        "Total Score": total_score,
                        "Round Score": rd.get("Round Score", np.nan),
                        "Geography": rd.get("Geography", np.nan),
                        "Geography Distance": rd.get("Geography Distance", np.nan),
                        "Time": rd.get("Time", np.nan),
                        "Time Distance": rd.get("Time Distance", np.nan),
                        "Time Guessed": rd.get("Time Guessed", np.nan),
                        "Time Score": rd.get("Time Score", np.nan),
                        "Geography Score": rd.get("Geography Score", np.nan),
                    })
            else:
                i += 1
        else:
            i += 1

    df_user = pd.DataFrame(user_data)

    for col in ["Time", "Geography"]:
        df_user[col] = (
            df_user[col]
            .astype(str)
            .str.replace("🟩", "O", regex=False)
            .str.replace("🟨", "%", regex=False)
            .str.replace("⬛", "X", regex=False)
            .apply(lambda x: re.sub(r"[️‍ï¸]", "", x))
            .str.strip()
        )

    def convert_to_meters(value):
        if pd.isna(value):
            return np.nan
        val = str(value).strip().lower()
        
        # Safely extract numeric value using regex (protects against missing spaces like "1.5mi")
        num_match = re.search(r"([\d.,]+)", val)
        if not num_match:
            return np.nan
            
        try:
            num = float(num_match.group(1).replace(",", ""))
        except Exception:
            return np.nan
            
        # Prioritize matching multi-letter units containing 'm' before falling back to isolated 'm'
        if "km" in val:
            return num * 1000
        elif "mi" in val:
            return num * 1609.344
        elif "ft" in val:
            return num * 0.3048
        elif "m" in val:
            return num
            
        return np.nan

    df_user["Geography Distance"] = df_user["Geography Distance"].apply(convert_to_meters)

    mask = df_user["Geography Score"].isna() & (df_user["Geography"] == "OOO")
    df_user.loc[mask, "Geography Score"] = 5000

    mask = df_user["Geography Score"].isna() & df_user["Geography Distance"].notna()
    dist = df_user.loc[mask, "Geography Distance"]
    conditions = [
        (dist <= 50),
        (dist > 50) & (dist <= 1000),
        (dist > 1000) & (dist <= 5000),
        (dist > 5000) & (dist <= 100000),
        (dist > 100000) & (dist <= 1000000),
        (dist > 1000000) & (dist <= 2000000),
        (dist > 2000000) & (dist <= 3000000),
        (dist > 3000000) & (dist <= 6000000),
        (dist > 6000000),
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
        12,
    ]
    df_user.loc[mask, "Geography Score"] = np.select(conditions, scores, default=np.nan)
    df_user["Geography Score"] = df_user["Geography Score"].clip(lower=12)

    if "Geography Score" in df_user.columns:
        df_user["Geography Score (Min)"] = np.nan
        df_user["Geography Score (Max)"] = np.nan
        mask = df_user["Geography Score"].notna()
        df_user.loc[mask, "Geography Score (Min)"] = df_user.loc[mask, "Geography Score"]
        df_user.loc[mask, "Geography Score (Max)"] = df_user.loc[mask, "Geography Score"]

        if "Geography" in df_user.columns:
            for pattern, lo, hi in [
                ("OO%", 4750, 4999),
                ("OOX", 4500, 4749),
                ("O%X", 4250, 4499),
                ("OXX", 3500, 4249),
                ("%XX", 2500, 3499),
                ("XXX", 12,   2499),
            ]:
                mask = df_user["Geography Score"].isna() & (df_user["Geography"] == pattern)
                df_user.loc[mask, "Geography Score (Min)"] = lo
                df_user.loc[mask, "Geography Score (Max)"] = hi

    df_user = df_user.rename(columns={
        "Total Score":              f"{user} Total Score",
        "Round Score":              f"{user} Round Score",
        "Geography":                f"{user} Geography",
        "Geography Distance":       f"{user} Geography Distance",
        "Time":                     f"{user} Time",
        "Time Distance":            f"{user} Time Distance",
        "Time Guessed":             f"{user} Time Guessed",
        "Time Score":               f"{user} Time Score",
        "Geography Score":          f"{user} Geography Score",
        "Geography Score (Min)":    f"{user} Geography Score (Min)",
        "Geography Score (Max)":    f"{user} Geography Score (Max)",
    })
    return df_user


def parse_actuals(lines):
    actuals_data = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("TimeGuessr #"):
            m = re.search(r"TimeGuessr #(\d+)", line)
            if m:
                day = int(m.group(1))
                for round_num in range(1, 6):
                    i += 1
                    if i < len(lines):
                        round_match = re.search(
                            r"^\d+\.\s+(.+?),\s+(.+?),\s+(\d{4})$",
                            lines[i]
                        )
                        if round_match:
                            city = round_match.group(1).strip()
                            country = round_match.group(2).strip()
                            year = int(round_match.group(3))
                            subdivision_match = re.search(r"\((.*?)\)", city)
                            if subdivision_match:
                                subdivision = subdivision_match.group(1).strip()
                                city = re.sub(r"\s*\(.*?\)", "", city).strip()
                            else:
                                subdivision = ""
                            actuals_data.append({
                                "Timeguessr Day": day,
                                "Timeguessr Round": round_num,
                                "City": city,
                                "Subdivision": subdivision,
                                "Country": country,
                                "Year": year,
                            })
        i += 1
    return pd.DataFrame(actuals_data)


def run_aggregation():
    if not _needs_update():
        return

    with open(MICHAEL_TXT, "r", encoding="utf-8") as f:
        michael_lines = [line.strip() for line in f if line.strip()]
    with open(SARAH_TXT, "r", encoding="utf-8") as f:
        sarah_lines = [line.strip() for line in f if line.strip()]
    with open(ACTUALS_TXT, "r", encoding="utf-8") as f:
        actuals_lines = [line.strip() for line in f if line.strip()]

    df_michael = parse_user_blocks(michael_lines, "Michael")
    df_michael.to_csv("Data/Timeguessr_Michael_Parsed.csv", index=False)

    df_sarah = parse_user_blocks(sarah_lines, "Sarah")
    df_sarah.to_csv("Data/Timeguessr_Sarah_Parsed.csv", index=False)

    df_actuals = parse_actuals(actuals_lines)
    df_actuals.to_csv("Data/Timeguessr_Actuals_Parsed.csv", index=False)

    df_all = pd.merge(df_michael, df_sarah, on=["Timeguessr Day", "Timeguessr Round"], how="outer")
    df_all = pd.merge(df_all, df_actuals, on=["Timeguessr Day", "Timeguessr Round"], how="left")

    if "Michael Time Distance" in df_all.columns and "Michael Time Guessed" in df_all.columns:
        mask = df_all["Michael Time Distance"].isna() & df_all["Michael Time Guessed"].notna() & df_all["Year"].notna()
        df_all.loc[mask, "Michael Time Distance"] = abs(df_all.loc[mask, "Year"] - df_all.loc[mask, "Michael Time Guessed"])

    if "Sarah Time Distance" in df_all.columns and "Sarah Time Guessed" in df_all.columns:
        mask = df_all["Sarah Time Distance"].isna() & df_all["Sarah Time Guessed"].notna() & df_all["Year"].notna()
        df_all.loc[mask, "Sarah Time Distance"] = abs(df_all.loc[mask, "Year"] - df_all.loc[mask, "Sarah Time Guessed"])

    start_date = pd.Timestamp("2025-03-20")
    df_all["Date"] = start_date + pd.to_timedelta(df_all["Timeguessr Day"] - df_all["Timeguessr Day"].min(), unit="D")

    cols = (
        ["Date", "Timeguessr Day", "Timeguessr Round", "City", "Subdivision", "Country", "Year"]
        + [c for c in df_all.columns if c not in ["Date", "Timeguessr Day", "Timeguessr Round", "City", "Subdivision", "Country", "Year"]]
    )
    df_all = df_all[cols]
    df_all = df_all.sort_values(["Timeguessr Day", "Timeguessr Round"]).reset_index(drop=True)

    def calc_time_score(years_off):
        if pd.isna(years_off):
            return None
        y = float(years_off)
        if y == 0:   return 5000
        if y == 1:   return 4950
        if y == 2:   return 4800
        if y == 3:   return 4600
        if y == 4:   return 4300
        if y == 5:   return 3900
        if y <= 7:   return 3400
        if y <= 10:  return 2500
        if y < 16:   return 2000
        if y < 21:   return 1000
        return 0

    for player in ["Michael", "Sarah"]:
        time_col       = f"{player} Time"
        time_score_col = f"{player} Time Score"
        time_dist_col  = f"{player} Time Distance"

        mask = df_all[time_score_col].isna() & (df_all[time_col] == "OOO")
        df_all.loc[mask, time_score_col] = 5000
        mask = df_all[time_score_col].isna() & (df_all[time_col] == "%XX")
        df_all.loc[mask, time_score_col] = 1000
        mask = df_all[time_score_col].isna() & (df_all[time_col] == "XXX")
        df_all.loc[mask, time_score_col] = 0

        mask = df_all[time_score_col].isna()
        df_all.loc[mask, time_score_col] = df_all.loc[mask, time_dist_col].apply(calc_time_score)

    for player in ["Michael", "Sarah"]:
        time_score_col = f"{player} Time Score"
        time_col       = f"{player} Time"
        time_min_col   = f"{player} Time Score (Min)"
        time_max_col   = f"{player} Time Score (Max)"

        if time_score_col in df_all.columns:
            df_all[time_min_col] = np.nan
            df_all[time_max_col] = np.nan

            mask = df_all[time_score_col].notna()
            df_all.loc[mask, time_min_col] = df_all.loc[mask, time_score_col]
            df_all.loc[mask, time_max_col] = df_all.loc[mask, time_score_col]

            if time_col in df_all.columns:
                for pattern, lo, hi in [
                    ("OO%", 4800, 4950),
                    ("OOX", 4300, 4600),
                    ("O%X", 3400, 3900),
                    ("OXX", 2000, 2500),
                ]:
                    mask = df_all[time_score_col].isna() & (df_all[time_col] == pattern)
                    df_all.loc[mask, time_min_col] = lo
                    df_all.loc[mask, time_max_col] = hi

    for player in ["Michael", "Sarah"]:
        time_col  = f"{player} Time Score"
        geo_col   = f"{player} Geography Score"
        round_col = f"{player} Round Score"
        if all(c in df_all.columns for c in [time_col, geo_col, round_col]):
            mask = df_all[round_col].isna() & df_all[time_col].notna() & df_all[geo_col].notna()
            df_all.loc[mask, round_col] = df_all.loc[mask, time_col] + df_all.loc[mask, geo_col]

    for player in ["Michael", "Sarah"]:
        for component in ["Time", "Geography"]:
            min_col  = f"{player} {component} Score (Min)"
            max_col  = f"{player} {component} Score (Max)"
            mean_col = f"{player} {component} Score (Mean)"
            if min_col in df_all.columns and max_col in df_all.columns:
                df_all[mean_col] = (df_all[min_col] + df_all[max_col]) / 2

    df_all.to_csv(STATS_CSV, index=False)