import os
import re
import numpy as np
import pandas as pd

try:
    pd.set_option("future.infer_string", False)
except Exception:
    pass

def _parse_distance_to_meters(value):
    if value is None:
        return np.nan
    if isinstance(value, float) and value != value:
        return np.nan
    if not isinstance(value, str):
        return np.nan
    v = value.strip().lower()
    m = re.search(r"([\d.,]+)", v)
    if not m:
        return np.nan
    try:
        num = float(m.group(1).replace(",", ""))
    except Exception:
        return np.nan
    if "km" in v:
        return num * 1000
    if "mi" in v:
        return num * 1609.344
    if "ft" in v:
        return num * 0.3048
    if "m" in v:
        return num
    return np.nan


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

    _STRIP_CHARS = ('️', '‍', 'ï', '¸', '⃣')

    for _rd in user_data:
        for _field in ("Geography", "Time"):
            _v = _rd.get(_field)
            if _v is None or (isinstance(_v, float) and _v != _v):
                _rd[_field] = ''
            else:
                _s = str(_v).replace("🟩", "O").replace("🟨", "%").replace("⬛", "X")
                for _ch in _STRIP_CHARS:
                    _s = _s.replace(_ch, '')
                _rd[_field] = _s.strip()

        _rd["Geography Distance"] = _parse_distance_to_meters(_rd.get("Geography Distance"))

    _cols = [
        "Timeguessr Day", "Timeguessr Round", "Total Score", "Round Score",
        "Geography", "Geography Distance", "Time", "Time Distance",
        "Time Guessed", "Time Score", "Geography Score",
    ]
    _float_cols = {"Round Score", "Geography Distance", "Time Distance",
                   "Time Guessed", "Time Score", "Geography Score"}
    _int_cols   = {"Timeguessr Day", "Timeguessr Round", "Total Score"}
    _str_cols   = {"Geography", "Time"}
    _col_data   = {c: [_rd.get(c, np.nan) for _rd in user_data] for c in _cols}
    df_user = pd.DataFrame({
        c: (np.array(_col_data[c], dtype=object) if c in _str_cols else
            np.array(_col_data[c], dtype=np.float64) if c in _float_cols else
            np.array(_col_data[c], dtype=np.int64))
        for c in _cols
    })

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
    if not actuals_data:
        return pd.DataFrame(columns=["Timeguessr Day", "Timeguessr Round", "City", "Subdivision", "Country", "Year"])
    return pd.DataFrame({
        "Timeguessr Day":   np.array([r["Timeguessr Day"]   for r in actuals_data], dtype=np.int64),
        "Timeguessr Round": np.array([r["Timeguessr Round"] for r in actuals_data], dtype=np.int64),
        "City":             np.array([r["City"]             for r in actuals_data], dtype=object),
        "Subdivision":      np.array([r["Subdivision"]      for r in actuals_data], dtype=object),
        "Country":          np.array([r["Country"]          for r in actuals_data], dtype=object),
        "Year":             np.array([r["Year"]             for r in actuals_data], dtype=np.int64),
    })


_DAILY_COLS = [
    "Timeguessr Day",
    "Community Average", "Community Years Average", "Community Location Average",
    "Michael Percentile", "Michael Years", "Michael Location",
    "Sarah Percentile", "Sarah Years", "Sarah Location",
]
_ROUND_COLS = [
    "Timeguessr Day", "Timeguessr Round",
    "Community Round Score", "Community Time Distance", "Community Geography Distance",
]


def parse_averages(lines):
    daily_rows = []
    round_rows = []
    i = 0
    n = len(lines)

    while i < n:
        header = re.match(r"^TimeGuessr #(\d+)$", lines[i])
        if not header:
            i += 1
            continue
        day = int(header.group(1))
        i += 1

        block = []
        while i < n and not re.match(r"^TimeGuessr #(\d+)$", lines[i]):
            block.append(lines[i])
            i += 1

        daily = {c: np.nan for c in _DAILY_COLS}
        daily["Timeguessr Day"] = day
        rounds = {r: {c: np.nan for c in _ROUND_COLS} for r in range(1, 6)}
        for r in range(1, 6):
            rounds[r]["Timeguessr Day"] = day
            rounds[r]["Timeguessr Round"] = r

        for bline in block:
            m = re.match(r"^Average\s*-\s*([\d,.]+)", bline)
            if m: daily["Community Average"] = float(m.group(1).replace(",", "")); continue
            m = re.match(r"^Years Average\s*-\s*([\d,.]+)", bline)
            if m: daily["Community Years Average"] = float(m.group(1).replace(",", "")); continue
            m = re.match(r"^Location Average\s*-\s*([\d,.]+)", bline)
            if m: daily["Community Location Average"] = float(m.group(1).replace(",", "")); continue
            m = re.match(r"^Michael Percentile\s*-\s*([\d.]+)", bline)
            if m: daily["Michael Percentile"] = float(m.group(1)) / 100; continue
            m = re.match(r"^Michael Years\s*-\s*([\d,.]+)", bline)
            if m: daily["Michael Years"] = float(m.group(1).replace(",", "")); continue
            m = re.match(r"^Michael Location\s*-\s*([\d,.]+)", bline)
            if m: daily["Michael Location"] = float(m.group(1).replace(",", "")); continue
            m = re.match(r"^Sarah Percentile\s*-\s*([\d.]+)", bline)
            if m: daily["Sarah Percentile"] = float(m.group(1)) / 100; continue
            m = re.match(r"^Sarah Years\s*-\s*([\d,.]+)", bline)
            if m: daily["Sarah Years"] = float(m.group(1).replace(",", "")); continue
            m = re.match(r"^Sarah Location\s*-\s*([\d,.]+)", bline)
            if m: daily["Sarah Location"] = float(m.group(1).replace(",", "")); continue

            m = re.match(r"^([1-5])\s+Time\s*-\s*([\d.]+)", bline)
            if m: rounds[int(m.group(1))]["Community Time Distance"] = float(m.group(2)); continue
            m = re.match(r"^([1-5])\s+Geo\s*-\s*(.+)$", bline)
            if m: rounds[int(m.group(1))]["Community Geography Distance"] = _parse_distance_to_meters(m.group(2)); continue
            m = re.match(r"^([1-5])\s*-\s*([\d,]+)$", bline)
            if m: rounds[int(m.group(1))]["Community Round Score"] = float(m.group(2).replace(",", "")); continue

        daily_rows.append(daily)
        round_rows.extend(rounds[r] for r in range(1, 6))

    df_daily = pd.DataFrame(daily_rows, columns=_DAILY_COLS) if daily_rows else pd.DataFrame(columns=_DAILY_COLS)
    df_rounds = pd.DataFrame(round_rows, columns=_ROUND_COLS) if round_rows else pd.DataFrame(columns=_ROUND_COLS)
    if not df_daily.empty:
        df_daily["Timeguessr Day"] = df_daily["Timeguessr Day"].astype(np.int64)
    if not df_rounds.empty:
        df_rounds["Timeguessr Day"] = df_rounds["Timeguessr Day"].astype(np.int64)
        df_rounds["Timeguessr Round"] = df_rounds["Timeguessr Round"].astype(np.int64)
    return df_daily, df_rounds


# ──────────────────────────────────────────────────────────────────────────────
# CSV-native averages persistence (current data-collection path). Writes
# straight to Data/Timeguessr_Averages_Parsed.csv, one row per Timeguessr Day +
# Round. The old TimeGuessr_*.txt files and their txt-parsing/writing helpers
# have been retired — this CSV (plus the Michael/Sarah/Actuals Parsed CSVs) is
# now the sole source of truth.
# ──────────────────────────────────────────────────────────────────────────────
AVERAGES_PARSED_CSV = "Data/Timeguessr_Averages_Parsed.csv"

_AVERAGES_CSV_COLS = (
    ["Timeguessr Day", "Timeguessr Round"]
    + [c for c in _ROUND_COLS if c not in ("Timeguessr Day", "Timeguessr Round")]
    + [c for c in _DAILY_COLS if c != "Timeguessr Day"]
)


def _load_averages_csv():
    if os.path.exists(AVERAGES_PARSED_CSV):
        df = pd.read_csv(AVERAGES_PARSED_CSV)
        for c in _AVERAGES_CSV_COLS:
            if c not in df.columns:
                df[c] = np.nan
        return df[_AVERAGES_CSV_COLS]
    return pd.DataFrame(columns=_AVERAGES_CSV_COLS)


def _save_averages_csv(df):
    df = df.sort_values(["Timeguessr Day", "Timeguessr Round"]).reset_index(drop=True)
    df.to_csv(AVERAGES_PARSED_CSV, index=False)


def _ensure_averages_day_rows(df, day):
    """Return (df, mask) where df has all 5 round rows for `day` (adding any
    that are missing) and mask selects exactly those 5 rows."""
    mask = df["Timeguessr Day"] == day
    existing_rounds = set(df.loc[mask, "Timeguessr Round"])
    missing = [r for r in range(1, 6) if r not in existing_rounds]
    if missing:
        new_rows = pd.DataFrame([
            {**{c: np.nan for c in _AVERAGES_CSV_COLS}, "Timeguessr Day": day, "Timeguessr Round": r}
            for r in missing
        ])
        df = pd.concat([df, new_rows], ignore_index=True)
        mask = df["Timeguessr Day"] == day
    return df, mask


def update_averages_csv_entry(day, player, percentile=None, years=None, location=None):
    """Upserts `{player} Percentile/Years/Location` for every round row of
    `day` in Timeguessr_Averages_Parsed.csv. `percentile` is on a 0-100 scale
    (matching the UI), stored as a 0-1 fraction to match the existing column
    convention."""
    if percentile is None and years is None and location is None:
        return
    df = _load_averages_csv()
    df, mask = _ensure_averages_day_rows(df, day)
    if percentile is not None:
        df.loc[mask, f"{player} Percentile"] = percentile / 100.0
    if years is not None:
        df.loc[mask, f"{player} Years"] = years
    if location is not None:
        df.loc[mask, f"{player} Location"] = location
    _save_averages_csv(df)


def update_community_averages_csv_entry(day, average=None, years_average=None, location_average=None, rounds=None):
    """Upserts the community averages/round data for `day`. `rounds` is
    a dict of {round_num: {'score': float|None, 'time': float|None,
    'geo_m': float|None}} — geo_m is the geography distance in meters (the
    unit Timeguessr_Averages_Parsed.csv's Community Geography Distance column
    already uses)."""
    if average is None and years_average is None and location_average is None and not rounds:
        return
    df = _load_averages_csv()
    df, mask = _ensure_averages_day_rows(df, day)
    if average is not None:
        df.loc[mask, "Community Average"] = average
    if years_average is not None:
        df.loc[mask, "Community Years Average"] = years_average
    if location_average is not None:
        df.loc[mask, "Community Location Average"] = location_average
    for r, vals in (rounds or {}).items():
        rmask = mask & (df["Timeguessr Round"] == r)
        if not rmask.any():
            continue
        if vals.get("score") is not None:
            df.loc[rmask, "Community Round Score"] = vals["score"]
        if vals.get("time") is not None:
            df.loc[rmask, "Community Time Distance"] = vals["time"]
        if vals.get("geo_m") is not None:
            df.loc[rmask, "Community Geography Distance"] = vals["geo_m"]
    _save_averages_csv(df)
