import os
import pandas as pd
import numpy as np
from aggregation import AVERAGES_PARSED_CSV

# --- Old / New scoring systems -------------------------------------------
# The game's scoring formulas changed on 2026-10-19. The base score columns
# hold whatever the game actually awarded (old system before that date, new
# system on/after it). The "(Old)" / "(New)" columns re-score every round
# under each system so the two can be compared across the whole history.
def old_geo_score(dist_m):
    d = float(dist_m)
    if d <= 50: s = 5000
    elif d <= 1000: s = 5000 - d * 0.02
    elif d <= 5000: s = 4980 - d * 0.016
    elif d <= 100000: s = 4900 - d * 0.004
    elif d <= 1000000: s = 4500 - d * 0.001
    elif d <= 2000000: s = 3500 - d * 0.0005
    elif d <= 3000000: s = 2500 - d * 0.0003333
    elif d <= 6000000: s = 1500 - d * 0.0002
    else: s = 12
    return round(max(s, 12))

def new_geo_score(dist_m):
    d = max(float(dist_m) / 1000 - 0.05, 0)
    return round(5000 * np.exp(-(d / 6000) ** 0.62 - (d / 3000) ** 1.5))

def old_time_score(years_off):
    y = int(abs(float(years_off)))
    if y == 0: return 5000
    elif y == 1: return 4950
    elif y == 2: return 4800
    elif y == 3: return 4600
    elif y == 4: return 4300
    elif y == 5: return 3900
    elif y in (6, 7): return 3400
    elif y in (8, 9, 10): return 2500
    elif 10 < y < 16: return 2000
    elif 15 < y < 21: return 1000
    else: return 0

def new_time_score(years_off):
    return round(5000 / (1 + (abs(float(years_off)) / 12) ** 2))

PLAYER_STEMS = ["Geography Score", "Geography Score (Min)", "Geography Score (Max)",
                "Time Score", "Time Score (Min)", "Time Score (Max)", "Round Score", "Total Score"]
COMMUNITY_STEMS = ["Geography Score", "Time Score"]
SYSTEMS = ["Old", "New"]
KEY_COLS = ["Timeguessr Day", "Timeguessr Round"]

def player_system_columns(player):
    return [f"{player} {stem} ({sys})" for sys in SYSTEMS for stem in PLAYER_STEMS]

def community_system_columns():
    return [f"Community {stem} ({sys})" for sys in SYSTEMS for stem in COMMUNITY_STEMS]

def _set_keeping_existing(df, col, values):
    """Assign freshly computed values, but never blank a value that is already
    stored (so previously recorded days survive if a later run can't recompute
    them)."""
    if col in df.columns:
        values = values.combine_first(df[col])
    df[col] = values

def add_community_system_columns(df_avg):
    """Estimated community Geography/Time scores under each system, derived
    from the community's average distance / average years off (the same
    estimate the Daily page shows). The recorded Community Round Score itself
    cannot be converted between systems."""
    for label, (geo_fn, time_fn) in {"Old": (old_geo_score, old_time_score), "New": (new_geo_score, new_time_score)}.items():
        if "Community Geography Distance" in df_avg.columns:
            geo = pd.Series(np.nan, index=df_avg.index)
            m = df_avg["Community Geography Distance"].notna()
            geo[m] = df_avg.loc[m, "Community Geography Distance"].map(geo_fn)
            _set_keeping_existing(df_avg, f"Community Geography Score ({label})", geo)
        if "Community Time Distance" in df_avg.columns:
            tim = pd.Series(np.nan, index=df_avg.index)
            m = df_avg["Community Time Distance"].notna()
            tim[m] = df_avg.loc[m, "Community Time Distance"].map(time_fn)
            _set_keeping_existing(df_avg, f"Community Time Score ({label})", tim)
    return df_avg

def persist_columns(path, source_df, cols):
    """Write `cols` from source_df back into the CSV at `path`, matched on
    Timeguessr Day + Round. Existing rows/columns are untouched apart from
    these columns, and a stored value is kept when no fresh value exists, so
    adding new days never overwrites old ones. Skips the write if nothing
    changed (avoids bumping the file's mtime)."""
    if not os.path.exists(path):
        return
    cols = [c for c in cols if c in source_df.columns]
    cur = pd.read_csv(path)
    if not cols or not all(k in cur.columns for k in KEY_COLS):
        return
    fresh = source_df[KEY_COLS + cols].drop_duplicates(KEY_COLS).set_index(KEY_COLS)
    out = cur.copy().set_index(KEY_COLS)
    for c in cols:
        new = fresh[c].reindex(out.index)
        out[c] = new.combine_first(out[c]) if c in out.columns else new
    out = out.reset_index()
    if not out.equals(cur):
        out.to_csv(path, index=False)

def add_system_score_columns(df_all):
    """Add "<Player> {Geography,Time,Round,Total} Score ... (Old)/(New)"
    columns. A player's row is populated only when both their years off
    (Time Distance, or actual year vs. year guessed) and geography distance
    are known (squares-only rows can't be re-scored under a different system). Total is filled only
    for days where all five rounds were populated."""
    systems = {"Old": (old_geo_score, old_time_score), "New": (new_geo_score, new_time_score)}
    for player in ["Michael", "Sarah"]:
        geo_dist_col = f"{player} Geography Distance"
        if geo_dist_col not in df_all.columns or f"{player} Time Distance" not in df_all.columns:
            continue
        # Years off: straight from the stored Time Distance, or derived from
        # the actual year and the year guessed when that's missing.
        years_off = df_all[f"{player} Time Distance"].abs()
        if f"{player} Time Guessed" in df_all.columns:
            years_off = years_off.fillna((df_all["Year"] - df_all[f"{player} Time Guessed"]).abs())
        known = years_off.notna() & df_all[geo_dist_col].notna()
        for label, (geo_fn, time_fn) in systems.items():
            geo = pd.Series(np.nan, index=df_all.index)
            tim = pd.Series(np.nan, index=df_all.index)
            geo[known] = df_all.loc[known, f"{player} Geography Distance"].map(geo_fn)
            tim[known] = years_off[known].map(time_fn)
            rnd = geo + tim
            total = rnd.groupby(df_all["Timeguessr Day"]).transform(
                lambda s: s.sum() if (len(s) == 5 and s.notna().all()) else np.nan)
            for stem, vals in (("Geography Score", geo), ("Geography Score (Min)", geo), ("Geography Score (Max)", geo),
                               ("Time Score", tim), ("Time Score (Min)", tim), ("Time Score (Max)", tim),
                               ("Round Score", rnd), ("Total Score", total)):
                _set_keeping_existing(df_all, f"{player} {stem} ({label})", vals)
    return df_all

def score_update():
    michael_csv = "Data/Timeguessr_Michael_Parsed.csv"
    sarah_csv   = "Data/Timeguessr_Sarah_Parsed.csv"
    actuals_csv = "Data/Timeguessr_Actuals_Parsed.csv"
    stats_csv   = "Data/Timeguessr_Stats.csv"

    # Both Home.py and the Daily page call score_update() unconditionally on
    # every single script rerun (i.e. on every widget interaction, not just
    # when a submission actually changes something) — so skip the rebuild
    # entirely when Timeguessr_Stats.csv is already at least as new as every
    # source CSV. Besides the wasted merge/write work itself, rewriting the
    # file on every rerun bumps its mtime every time, which permanently
    # defeats the @st.cache_data cache keyed on that mtime in Pages/1_Daily.py
    # and forces its whole historical events pipeline to recompute from
    # scratch on every keystroke — that cascading cost, not this function's
    # own runtime, is what actually makes the Daily page feel laggy.
    source_csvs = [michael_csv, sarah_csv, actuals_csv, AVERAGES_PARSED_CSV, __file__]
    if os.path.exists(stats_csv):
        source_mtimes = [os.path.getmtime(p) for p in source_csvs if os.path.exists(p)]
        if source_mtimes and os.path.getmtime(stats_csv) >= max(source_mtimes):
            # Also rebuild if Stats lacks the Old/New columns (e.g. a data
            # update from a machine without them overwrote the file).
            have = set(pd.read_csv(stats_csv, nrows=0).columns)
            needed = set(community_system_columns() + player_system_columns("Michael") + player_system_columns("Sarah"))
            if needed <= have:
                return

    df_michael = pd.read_csv(michael_csv)
    df_sarah   = pd.read_csv(sarah_csv)
    df_actuals = pd.read_csv(actuals_csv)

    df_all = pd.merge(df_michael, df_sarah, on=["Timeguessr Day", "Timeguessr Round"], how="outer")
    df_all = pd.merge(df_all, df_actuals, on=["Timeguessr Day", "Timeguessr Round"], how="left")

    # Community/percentile averages now live directly in this CSV (kept current
    # by update_averages_csv_entry / update_community_averages_csv_entry) —
    # already shaped one row per Timeguessr Day + Round, so a single merge
    # covers both the daily-level and round-level average fields.
    if os.path.exists(AVERAGES_PARSED_CSV):
        df_avg = pd.read_csv(AVERAGES_PARSED_CSV)
    else:
        df_avg = pd.DataFrame(columns=["Timeguessr Day", "Timeguessr Round"])
    df_avg = add_community_system_columns(df_avg)
    df_all = pd.merge(df_all, df_avg, on=["Timeguessr Day", "Timeguessr Round"], how="left")

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

    df_all = add_system_score_columns(df_all)

    # Persist the Old/New columns into every source datasheet. Stats is
    # written last so its mtime stays newer than all of them (otherwise the
    # skip check at the top would rebuild on every run).
    persist_columns(michael_csv, df_all, player_system_columns("Michael"))
    persist_columns(sarah_csv, df_all, player_system_columns("Sarah"))
    persist_columns(AVERAGES_PARSED_CSV, df_all, community_system_columns())

    df_all.to_csv("Data/Timeguessr_Stats.csv", index=False)