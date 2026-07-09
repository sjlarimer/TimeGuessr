# TimeGuessr Dashboard

A multi-page Streamlit analytics dashboard for tracking a two-player daily competition in [TimeGuessr](https://timeguessr.com/) — a game where players guess the location and year of historical photographs. The dashboard covers every aspect of performance: raw scores, score breakdowns, head-to-head margins, per-round trends, geography maps, statistical analysis, and historical records.

## Overview

Each TimeGuessr session consists of 5 rounds. Each round awards up to 10,000 points split between:
- **Geography score** (0–5,000): Based on how close the guessed location is to the actual location
- **Time score** (0–5,000): Based on how many years off the guessed year is from the actual year

Maximum daily score: **50,000 points** across 5 rounds.

The dashboard tracks two players — **Michael** and **Sarah** — from their game history stored as raw text exports, and reconstructs full per-round statistics even when exact numeric scores are missing (using emoji pattern inference).

---

## Tech Stack

| Layer | Library |
|---|---|
| Web framework | Streamlit |
| Data processing | Pandas, NumPy |
| Visualization | Plotly, Matplotlib, SciPy |
| Geospatial | GeoJSON (custom world map) |
| Styling | Custom CSS + HTML in Streamlit markdown |

---

## Project Structure

```
TimeGuessr/
├── Welcome.py                  # Landing page (overview, score reference, activity log)
├── aggregation.py              # Raw text parser + score reconstruction
├── Score_Update.py             # Merge + enrich parsed CSVs into final stats file
├── Fix_Actuals.py              # Cleanup script for subdivision names in actuals
├── run.bat                     # Windows launcher
├── styles.css                  # Global Streamlit CSS overrides
├── config.json                 # Country/subdivision hierarchy for submission form
├── Pages/
│   ├── 1_Score_Submission.py   # Daily input form
│   ├── 2_Scores.py             # Time-series score charts + statistics
│   ├── 3_Win_Margins.py        # Head-to-head margin analysis
│   ├── 4_Self_Comparison.py    # Time vs geography scatter + boxplots
│   ├── 6_Locations.py          # Interactive world map heatmap
│   ├── 7_Timeline.py           # Stacked bar timeline by winner
│   ├── 8_Rounds.py             # Per-round performance breakdown
│   ├── 9_Hall_of_Fame.py       # Best scores, streaks, records
│   ├── 10_Hall_of_Shame.py     # Worst scores, losing streaks
│   ├── 11_News.py              # Weekly summaries and milestones
│   ├── 12_Analysis.py          # Statistical tests and correlation tables
│   ├── 13_Fun.py               # Easter eggs and curiosities
│   └── 14_Electoral_College.py # US electoral map based on location guesses
└── Data/
    ├── TimeGuessr_Michael.txt      # Raw game exports (Michael)
    ├── TimeGuessr_Sarah.txt        # Raw game exports (Sarah)
    ├── TimeGuessr_Actuals.txt      # Correct answers per round
    ├── Timeguessr_Michael_Parsed.csv
    ├── Timeguessr_Sarah_Parsed.csv
    ├── Timeguessr_Actuals_Parsed.csv
    ├── Timeguessr_Stats.csv        # Final merged dataset (source of truth)
    └── Custom_World_Map_New.json   # GeoJSON for location heatmap
```

---

## Data Pipeline

### 1. Raw Input

Players paste their TimeGuessr share text into `Data/TimeGuessr_Michael.txt` and `Data/TimeGuessr_Sarah.txt`. The parser handles three export formats (emoji keycaps, detailed with numeric scores, and simplified). Correct answers are stored in `Data/TimeGuessr_Actuals.txt` in the format:

```
1. City (Subdivision), Country, Year
```

### 2. Parsing — `aggregation.py`

`run_aggregation()` reads all three TXT files and extracts per-round data:
- Geography and time emoji patterns (e.g., `OOX` = two greens + a red)
- Distances and guessed years (when present in the export)
- Reconstructed scores using the formulas below

**Geography scoring formula** (piecewise linear by distance):**

| Distance | Score |
|---|---|
| 0–50 m | 5,000 |
| 50 m–1 km | 5,000 − 0.02 × d |
| 1 km–5 km | 4,990 − 0.65 × d |
| 5 km–100 km | 4,665 − 0.49 × d |
| 100 km–250 km | 3,680 − 0.49 × d |
| 250 km–1,000 km | 3,185 − 0.29 × d |
| 1,000 km–3,000 km | 2,897 − 0.0587 × d |
| 3,000 km–6,000 km | 2,310 − 0.0391 × d |
| > 6,000 km | 12 |

**Time scoring formula** (discrete lookup):

| Years off | Score |
|---|---|
| 0 | 5,000 |
| 1 | 4,950 |
| 2 | 4,800 |
| 3 | 4,600 |
| ... | decreasing |
| 20+ | 0 |

When only emoji patterns are available (no numeric distances), scores are estimated as a Min–Max range based on pattern category, with the mean used for charting.

Outputs: `Timeguessr_Michael_Parsed.csv`, `Timeguessr_Sarah_Parsed.csv`, `Timeguessr_Actuals_Parsed.csv`

### 3. Enrichment — `Score_Update.py`

`score_update()` merges the three parsed CSVs on (Day, Round) and produces `Data/Timeguessr_Stats.csv` with columns including:

- **Temporal**: Date, Timeguessr Day, Timeguessr Round (1–5)
- **Location**: City, Subdivision, Country, Year
- **Per-player**: Total score, Round score, Time score/distance/guessed year, Geography score/distance/pattern
- **Derived**: Min/Max/Mean estimated scores for uncertain rounds

This file is the single source of truth for all dashboard pages.

---

## Pages

### Welcome (Landing Page)
- Overview card: total days played, rules summary, link to play TimeGuessr
- Score reference charts: interactive Plotly charts showing the geography score curve (log-scale) and time score step function, both color-coded by emoji accuracy tier
- Recent Activity Log: scrollable table of the last 100 rounds with date, location (city + subdivision + country), year, and per-player scores

### Score Submission (`1_Score_Submission.py`)
Daily input form. Players enter their share text or manual scores; the page validates emoji patterns, calculates estimated scores, and appends to the raw TXT files.

### Scores (`2_Scores.py`)
Time-series charts for total, time, and geography scores. Includes rolling average (configurable window), cumulative average, KDE density estimation, percentile bands, and per-player statistics tables with streak analysis.

### Win Margins (`3_Win_Margins.py`)
Bar/line chart of Michael − Sarah score difference per game. Includes rolling and cumulative average margins, shaded win regions, win count tables, and streak lengths categorized by margin size (Massive, Big, Small, Close, Very Close).

### Self Comparison (`4_Self_Comparison.py`)
Time vs Geography scatter plots for each player, boxplots by score range, and performance trend breakdowns showing how each player's two score components correlate.

### Locations (`6_Locations.py`)
Interactive world map (GeoJSON) with a frequency heatmap of round locations. Filterable by distance accuracy and player.

### Timeline (`7_Timeline.py`)
Stacked bar chart with one bar per day, colored by the day's winner, width proportional to number of rounds played.

### Rounds (`8_Rounds.py`)
Per-round (1–5) performance: average scores, round-by-round trends, and win rates broken down by round position.

### Hall of Fame (`9_Hall_of_Fame.py`)
Records: highest single-round scores, highest daily totals, longest winning streaks, highest rolling averages, best geography and time scores.

### Hall of Shame (`10_Hall_of_Shame.py`)
Inverse of Hall of Fame: worst rounds, worst days, longest losing streaks, lowest averages.

### News (`11_News.py`)
Auto-generated weekly summaries, milestone notifications (e.g., 100th game), and trending statistics.

### Analysis (`12_Analysis.py`)
Statistical tests: t-tests, Mann-Whitney U, correlation coefficients, p-values, and effect sizes comparing the two players across score types and time periods.

### Fun (`13_Fun.py`)
Easter eggs, curiosities, and unusual facts derived from the game data.

### Electoral College (`14_Electoral_College.py`)
US counties colored by which player would hypothetically "win" each region based on their geography guesses near that area.

---

## Running the App

**Requirements**: Python 3.x with the packages below installed.

```bash
streamlit run Welcome.py
```

Or use the included launcher on Windows:

```bash
run.bat
```

On startup, the app checks whether the raw TXT files have been modified since the last run and re-runs aggregation and score update automatically if needed.

**Dependencies** (install via pip):

```
streamlit
pandas
numpy
plotly
matplotlib
scipy
```

---

## Data Formats

### Player share text (TXT)
The parser accepts three formats produced by TimeGuessr's share button. Example (detailed format):

```
TimeGuessr #312 — 42,150/50,000
Round 1: 🟩🟩🟩 | 4,820 pts — 0.3 km | 🟩🟩🟩 | 4,950 pts — 1 year off
...
```

### Actuals (TXT)
```
312
1. Paris (Île-de-France), France, 1963
2. Tokyo, Japan, 1985
...
```

---

## Color Conventions

- **Michael**: Navy (`#221e8f`)
- **Sarah**: Maroon (`#8a005c`)
- **Score tiers**: Purple (OOO) → Blue (OO%) → Green (OOX) → Gold (O%X) → Orange (OXX) → Red (%XX) → Dark Red (XXX)
