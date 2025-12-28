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

image_file_path = "Images/Sarah4.jpg"

# 1. Get the base64 string
base64_img = get_base64_image(image_file_path)

# 2. Inject the CSS with a 70% lightness overlay
# Try adjusting the second argument (e.g., 0.3 for slightly lighter, 0.9 for very light)
set_lighter_background_image(base64_img, lightness_level=0.7)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import country_converter as coco
import numpy as np
from plotly.colors import sample_colorscale
import datetime
import json
import os
import geopandas as gpd

# --- Styles ---
try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.markdown("""
<style>
    .stRadio [role=radiogroup] {
        align-items: start;
        justify-content: start;
    }
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    div[data-testid="stDataFrame"] {
        width: 100%;
    }
    /* Maximize Chart Area */
    .main .block-container {
        max-width: 98%;
        padding-left: 1rem;
        padding-right: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("## Locations")

# --- Load data ---
try:
    data = pd.read_csv("./Data/Timeguessr_Stats.csv")
except FileNotFoundError:
    st.error("Stats file not found. Please ensure './Data/Timeguessr_Stats.csv' exists.")
    st.stop()

# --- Mappings ---
cc = coco.CountryConverter()

# --- 1. Load Base Map (Enriched) ---
@st.cache_data
def load_base_geodataframe():
    target_file = "./Data/Custom_World_Map_New.json"
    if not os.path.exists(target_file):
        st.error(f"Map file not found at {target_file}")
        return None, set()

    try:
        gdf = gpd.read_file(target_file)
        
        # --- Standardize Columns & ISO Codes ---
        cols = gdf.columns
        
        # 1. Identify source column for ID
        iso_src = next((c for c in ['ISO3', 'iso3', 'ISO_CC', 'iso_cc', 'adm0_a3'] if c in cols), None)
        
        if iso_src:
            # Clean source data first
            gdf[iso_src] = gdf[iso_src].astype(str).str.strip()
            
            # Convert entire column to ISO3
            names = gdf[iso_src].tolist()
            gdf['ISO3'] = cc.convert(names=names, to='ISO3', not_found=None)
                  
        else:
            gdf['ISO3'] = 'UNK'
            
        # Fill missing
        gdf['ISO3'] = gdf['ISO3'].fillna('UNK')

        # 2. Identify source column for Name
        if 'NAME' not in cols:
            name_key = next((c for c in ['name', 'NAME_1', 'Name', 'COUNTRY'] if c in cols), None)
            if name_key:
                gdf['NAME'] = gdf[name_key]
            else:
                gdf['NAME'] = 'Unknown'

        # 3. Enrich with Continent/Region info (for dissolving later)
        # We map based on the ISO3 column we just fixed
        unique_isos = gdf['ISO3'].unique().tolist()
        # Remove UNK to avoid warnings
        clean_isos = [x for x in unique_isos if x != 'UNK']
        
        cont_map = dict(zip(clean_isos, cc.convert(names=clean_isos, to="continent")))
        region_map = dict(zip(clean_isos, cc.convert(names=clean_isos, to="UNregion")))
        
        gdf['Continent'] = gdf['ISO3'].map(cont_map).fillna("Unknown")
        gdf['UN_Region'] = gdf['ISO3'].map(region_map).fillna("Unknown")

        # Initial cleanup
        try:
            gdf['geometry'] = gdf['geometry'].buffer(0)
        except:
            pass 
                
        return gdf, set(gdf['NAME'].unique())

    except Exception as e:
        st.error(f"Error reading map file: {e}")
        return None, set()

base_gdf, valid_map_names = load_base_geodataframe()

# --- 2. Geometry Caching Functions ---

@st.cache_data
def get_background_layer(_gdf):
    """
    Creates a single unified shape for the whole world.
    """
    if _gdf is None: return None
    _gdf['World_Group'] = 1
    bg_gdf = _gdf.dissolve(by='World_Group', as_index=False)
    return json.loads(bg_gdf.to_json())

@st.cache_data(max_entries=10)
def generate_dynamic_map_layer(_gdf, active_iso_tuple, split_us, split_uk, split_germany, split_france, split_canada, split_australia, split_india, split_china, split_poland, view_mode):
    """
    Generates map geometry. 
    Dissolves active countries based on view_mode (Country vs Region vs Continent).
    Prioritizes splitting US/UK/Germany/France/Canada/Australia/India/China/Poland even in Region/Continent modes.
    """
    if _gdf is None: return None
    
    work_gdf = _gdf.copy()
    
    def get_dissolve_key(row):
        iso = row['ISO3']
        name = row['NAME']
        
        if iso in active_iso_tuple:
            # 1. Handle Splits FIRST
            if iso == 'USA' and split_us: 
                return name if view_mode == 'Countries' else iso
            if iso == 'GBR' and split_uk: 
                return name if view_mode == 'Countries' else iso
            if iso == 'DEU' and split_germany:
                return name if view_mode == 'Countries' else iso
            if iso == 'FRA' and split_france:
                return name if view_mode == 'Countries' else iso
            if iso == 'CAN' and split_canada:
                return name if view_mode == 'Countries' else iso
            if iso == 'AUS' and split_australia:
                return name if view_mode == 'Countries' else iso
            if iso == 'IND' and split_india:
                return name if view_mode == 'Countries' else iso
            if iso == 'CHN' and split_china:
                return name if view_mode == 'Countries' else iso
            if iso == 'POL' and split_poland:
                return name if view_mode == 'Countries' else iso
            
            # 2. Determine base identity based on View Mode
            if view_mode == "Continents":
                return row['Continent']
            elif view_mode == "UN Regions":
                return row['UN_Region']
            else: 
                return iso 
        else:
            return "Background"

    work_gdf['Dissolve_Key'] = work_gdf.apply(get_dissolve_key, axis=1)
    
    dissolved_gdf = work_gdf.dissolve(by='Dissolve_Key', as_index=False)
    
    return json.loads(dissolved_gdf.to_json())

# --- 3. Data Calculation ---

def calculate_stats_slice(df, split_us, split_uk, split_germany, split_france, split_canada, split_australia, split_india, split_china, split_poland, max_points):
    """
    Calculates stats at the granular level (ISO/Subdiv).
    Handles tie-breaking for most recent locations.
    """
    df_work = df.copy()
    
    # ISO mapping
    unique_countries = df_work["Country"].unique()
    iso3_map = dict(zip(unique_countries, cc.convert(names=unique_countries, to="ISO3", not_found=None)))
    df_work["ISO3"] = df_work["Country"].map(iso3_map)

    # Add Region Info
    continent_map = dict(zip(unique_countries, cc.convert(names=unique_countries, to="continent")))
    un_region_map = dict(zip(unique_countries, cc.convert(names=unique_countries, to="UNregion")))
    df_work["Continent"] = df_work["Country"].map(continent_map)
    df_work["UN_Region"] = df_work["Country"].map(un_region_map)

    # Palestine Region Fix
    mask_pal = df_work["Country"].astype(str).str.contains("Palestine", case=False)
    if mask_pal.any():
        df_work.loc[mask_pal, "Continent"] = "Asia"
        df_work.loc[mask_pal, "UN_Region"] = "Western Asia"

    # Define Join Key
    def get_join_key(row):
        iso = row['ISO3']
        subdiv = row.get('Subdivision')
        if iso == 'USA' and split_us and pd.notna(subdiv): return subdiv
        if iso == 'GBR' and split_uk and pd.notna(subdiv): return subdiv
        if iso == 'DEU' and split_germany and pd.notna(subdiv): return subdiv
        if iso == 'FRA' and split_france and pd.notna(subdiv): return subdiv
        if iso == 'CAN' and split_canada and pd.notna(subdiv): return subdiv
        if iso == 'AUS' and split_australia and pd.notna(subdiv): return subdiv
        if iso == 'IND' and split_india and pd.notna(subdiv): return subdiv
        if iso == 'CHN' and split_china and pd.notna(subdiv): return subdiv
        if iso == 'POL' and split_poland and pd.notna(subdiv): return subdiv
        return iso

    def get_display_name(row):
        iso = row['ISO3']
        subdiv = row.get('Subdivision')
        country = row['Country']
        
        is_split = False
        if iso == 'USA' and split_us: is_split = True
        elif iso == 'GBR' and split_uk: is_split = True
        elif iso == 'DEU' and split_germany: is_split = True
        elif iso == 'FRA' and split_france: is_split = True
        elif iso == 'CAN' and split_canada: is_split = True
        elif iso == 'AUS' and split_australia: is_split = True
        elif iso == 'IND' and split_india: is_split = True
        elif iso == 'CHN' and split_china: is_split = True
        elif iso == 'POL' and split_poland: is_split = True
        
        # If split is active and subdiv exists, label row "Subdiv, Country"
        if is_split and pd.notna(subdiv):
            return f"{subdiv}, {country}"
            
        return country

    df_work['Join_Key'] = df_work.apply(get_join_key, axis=1)
    df_work['Display_Name'] = df_work.apply(get_display_name, axis=1)
    
    # --- Recent Location Calculation (Handling Ties) ---
    def get_full_loc(row):
        city = str(row['City']).strip() if pd.notna(row.get('City')) else ''
        sub = str(row['Subdivision']).strip() if pd.notna(row.get('Subdivision')) else ''
        ctry = str(row['Country']).strip() if pd.notna(row.get('Country')) else ''
        # Keep components; we will format later
        return f"{city}|{sub}|{ctry}"

    df_work['Loc_Raw'] = df_work.apply(get_full_loc, axis=1)
    
    # 1. Find Max Date per Join_Key
    if 'Date' in df_work.columns:
        max_dates = df_work.groupby('Join_Key')['Date'].max().reset_index().rename(columns={'Date': 'Max_Date'})
        # 2. Merge back to get rows matching Max Date
        df_recent = pd.merge(df_work, max_dates, on='Join_Key')
        df_recent = df_recent[df_recent['Date'] == df_recent['Max_Date']]
        
        # 3. Aggregate unique locations for the max date
        recent_locs = df_recent.groupby('Join_Key')['Loc_Raw'].unique().apply(lambda x: ";".join(x)).reset_index().rename(columns={'Loc_Raw': 'Last_Location_Raw'})
        
        # 4. Get the single max date (for the main agg)
        recent_dates = max_dates.rename(columns={'Max_Date': 'Last_Date'})
    else:
        recent_locs = pd.DataFrame(columns=['Join_Key', 'Last_Location_Raw'])
        recent_dates = pd.DataFrame(columns=['Join_Key', 'Last_Date'])

    # Build aggregation dict
    agg_dict = {
        "Michael Selected": "sum",
        "Sarah Selected": "sum",
        "Country": "count",
    }
    # Add Wins if they exist in df_work
    if "Michael Win" in df_work.columns:
        agg_dict["Michael Win"] = "sum"
    if "Sarah Win" in df_work.columns:
        agg_dict["Sarah Win"] = "sum"

    # Main Aggregate
    grouped = df_work.groupby(['Join_Key', 'ISO3', 'Display_Name', 'Continent', 'UN_Region']).agg(agg_dict).rename(columns={"Country": "Count"}).reset_index()
    
    # Merge Recent Info
    grouped = pd.merge(grouped, recent_dates, on='Join_Key', how='left')
    grouped = pd.merge(grouped, recent_locs, on='Join_Key', how='left')
    
    grouped['Hover_Name'] = grouped['Display_Name']
    
    # Calculations
    grouped["Total Possible"] = grouped["Count"] * max_points
    grouped["Michael Efficiency"] = grouped["Michael Selected"] / grouped["Total Possible"]
    grouped["Sarah Efficiency"] = grouped["Sarah Selected"] / grouped["Total Possible"]
    grouped["Combined Points"] = grouped["Michael Selected"] + grouped["Sarah Selected"]
    grouped["Michael Share Ratio"] = grouped.apply(
        lambda row: row["Michael Selected"] / row["Combined Points"] if row["Combined Points"] > 0 else 0.5, axis=1)
    
    grouped["Michael Avg"] = (grouped["Michael Selected"] / grouped["Count"]).fillna(0).round().astype(int)
    grouped["Sarah Avg"] = (grouped["Sarah Selected"] / grouped["Count"]).fillna(0).round().astype(int)
    
    # Formatting
    grouped["Michael Eff %"] = (grouped["Michael Efficiency"] * 100).map('{:,.1f}%'.format)
    grouped["Sarah Eff %"] = (grouped["Sarah Efficiency"] * 100).map('{:,.1f}%'.format)
    grouped["Michael Share %"] = (grouped["Michael Share Ratio"] * 100).map('{:,.1f}%'.format)
    grouped["Sarah Share %"] = ((1 - grouped["Michael Share Ratio"]) * 100).map('{:,.1f}%'.format)
    
    return grouped

@st.cache_data
def precompute_stats_v12(raw_df, split_us, split_uk, split_germany, split_france, split_canada, split_australia, split_india, split_china, split_poland):
    """
    Calculates stats for ALL 3 Score Modes (Total, Geo, Time).
    Includes Win Counts for Intersection Data.
    """
    results = {}
    args = (split_us, split_uk, split_germany, split_france, split_canada, split_australia, split_india, split_china, split_poland)
    
    modes = ["Total Score", "Geography Score", "Time Score"]
    
    for mode in modes:
        if mode == "Total Score":
            m_cols = ["Michael Geography Score", "Michael Time Score"]
            s_cols = ["Sarah Geography Score", "Sarah Time Score"]
            max_p = 10000
        elif mode == "Geography Score":
            m_cols = ["Michael Geography Score"]
            s_cols = ["Sarah Geography Score"]
            max_p = 5000
        else: # Time
            m_cols = ["Michael Time Score"]
            s_cols = ["Sarah Time Score"]
            max_p = 5000
            
        # 1. Intersection (Both players required)
        df_both = raw_df.dropna(subset=m_cols + s_cols + ["Date"]).copy()
        df_both["Michael Selected"] = df_both[m_cols].sum(axis=1)
        df_both["Sarah Selected"] = df_both[s_cols].sum(axis=1)
        
        # Calculate Wins
        df_both["Michael Win"] = (df_both["Michael Selected"] > df_both["Sarah Selected"]).astype(int)
        df_both["Sarah Win"] = (df_both["Sarah Selected"] > df_both["Michael Selected"]).astype(int)

        results[f"Intersection {mode}"] = calculate_stats_slice(df_both, *args, max_p)
        
        # 2. Michael Only
        df_mich = raw_df.dropna(subset=m_cols + ["Date"]).copy()
        df_mich["Michael Selected"] = df_mich[m_cols].sum(axis=1)
        df_mich["Sarah Selected"] = 0 
        results[f"Michael {mode}"] = calculate_stats_slice(df_mich, *args, max_p)
        
        # 3. Sarah Only
        df_sarah = raw_df.dropna(subset=s_cols + ["Date"]).copy()
        df_sarah["Michael Selected"] = 0
        df_sarah["Sarah Selected"] = df_sarah[s_cols].sum(axis=1)
        results[f"Sarah {mode}"] = calculate_stats_slice(df_sarah, *args, max_p)

    return results

def aggregate_by_view_mode(df, view_mode, split_us, split_uk, split_germany, split_france, split_canada, split_australia, split_india, split_china, split_poland):
    """
    If view_mode is Region/Continent, re-aggregate the stats.
    Includes tie-breaking logic for locations when aggregating.
    """
    if view_mode == "Countries":
        return df

    base_group = "Continent" if view_mode == "Continents" else "UN_Region"
    
    def get_group_key(row):
        iso = row['ISO3']
        if split_us and iso == 'USA': return 'USA'
        if split_uk and iso == 'GBR': return 'GBR'
        if split_germany and iso == 'DEU': return 'DEU'
        if split_france and iso == 'FRA': return 'FRA'
        if split_canada and iso == 'CAN': return 'CAN'
        if split_australia and iso == 'AUS': return 'AUS'
        if split_india and iso == 'IND': return 'IND'
        if split_china and iso == 'CHN': return 'CHN'
        if split_poland and iso == 'POL': return 'POL'
        return row[base_group]

    df_work = df.copy()
    df_work['Agg_Key'] = df_work.apply(get_group_key, axis=1)
    
    # 1. Calculate Aggregated Counts/Scores first
    agg_dict = {
        "Michael Selected": "sum",
        "Sarah Selected": "sum",
        "Count": "sum",
        "Total Possible": "sum",
        "Continent": "first",
        "UN_Region": "first"
    }
    if "Michael Win" in df_work.columns:
        agg_dict["Michael Win"] = "sum"
    if "Sarah Win" in df_work.columns:
        agg_dict["Sarah Win"] = "sum"

    grouped = df_work.groupby('Agg_Key').agg(agg_dict).reset_index()

    # 2. Calculate Aggregated Recent Date/Location with Ties
    if 'Last_Date' in df_work.columns:
        # Find max date per Agg_Key
        max_dates = df_work.groupby('Agg_Key')['Last_Date'].max().reset_index().rename(columns={'Last_Date': 'Group_Max_Date'})
        
        # Filter original rows that match the max date
        df_recent = pd.merge(df_work, max_dates, on='Agg_Key')
        df_recent = df_recent[df_recent['Last_Date'] == df_recent['Group_Max_Date']]
        
        # Collect all raw locations for these rows (unique)
        recent_locs = df_recent.groupby('Agg_Key')['Last_Location_Raw'].apply(
            lambda x: ";".join(set(";".join(x).split(";"))) # Split nested ; then join unique
        ).reset_index().rename(columns={'Last_Location_Raw': 'Last_Location_Raw'})
        
        grouped = pd.merge(grouped, max_dates, on='Agg_Key', how='left')
        grouped = pd.merge(grouped, recent_locs, on='Agg_Key', how='left')
        grouped = grouped.rename(columns={'Group_Max_Date': 'Last_Date'})
    
    grouped['Join_Key'] = grouped['Agg_Key']
    
    name_map = {
        'USA': 'United States', 'GBR': 'United Kingdom', 'DEU': 'Germany', 'FRA': 'France',
        'CAN': 'Canada', 'AUS': 'Australia', 'IND': 'India', 'CHN': 'China', 'POL': 'Poland'
    }
    grouped['Hover_Name'] = grouped['Agg_Key'].replace(name_map)
    
    # Re-calculate Efficiencies
    grouped["Michael Efficiency"] = grouped["Michael Selected"] / grouped["Total Possible"]
    grouped["Sarah Efficiency"] = grouped["Sarah Selected"] / grouped["Total Possible"]
    grouped["Combined Points"] = grouped["Michael Selected"] + grouped["Sarah Selected"]
    grouped["Michael Share Ratio"] = grouped.apply(
        lambda row: row["Michael Selected"] / row["Combined Points"] if row["Combined Points"] > 0 else 0.5, axis=1)
    
    grouped["Michael Avg"] = (grouped["Michael Selected"] / grouped["Count"]).fillna(0).round().astype(int)
    grouped["Sarah Avg"] = (grouped["Sarah Selected"] / grouped["Count"]).fillna(0).round().astype(int)

    grouped["Michael Eff %"] = (grouped["Michael Efficiency"] * 100).map('{:,.1f}%'.format)
    grouped["Sarah Eff %"] = (grouped["Sarah Efficiency"] * 100).map('{:,.1f}%'.format)
    grouped["Michael Share %"] = (grouped["Michael Share Ratio"] * 100).map('{:,.1f}%'.format)
    grouped["Sarah Share %"] = ((1 - grouped["Michael Share Ratio"]) * 100).map('{:,.1f}%'.format)

    return grouped

def add_calculated_colors(df, value_col, colorscale, min_val, max_val):
    if df.empty: return df
    
    mask_active = df['Dissolve_Key'] != "Background"
    if not mask_active.any():
        df['Calculated_Color'] = "#eeeeee"
        return df
        
    vals = pd.to_numeric(df.loc[mask_active, value_col], errors='coerce').fillna(min_val)
    
    denom = max_val - min_val
    if denom == 0:
        norm_vals = pd.Series(0.0, index=vals.index)
    else:
        norm_vals = (vals - min_val) / denom
    norm_vals = norm_vals.clip(0, 1)
    
    sample_points = norm_vals.to_numpy(dtype=float)
    df.loc[mask_active, 'Calculated_Color'] = sample_colorscale(colorscale, sample_points)
    df.loc[~mask_active, 'Calculated_Color'] = "#eeeeee" 
    
    return df

# --- Helper for Microstates ---
microstates = {
    "Vatican City": {"lon": 12.4534, "lat": 41.9029}, "Monaco": {"lon": 7.4167, "lat": 43.7384},
    "San Marino": {"lon": 12.4578, "lat": 43.9424}, "Liechtenstein": {"lon": 9.5215, "lat": 47.1410},
    "Malta": {"lon": 14.5146, "lat": 35.8989}, "Andorra": {"lon": 1.5218, "lat": 42.5063},
    "Luxembourg": {"lon": 6.133333, "lat": 49.816667}, "Saint Kitts and Nevis": {"lon": -62.7830, "lat": 17.3578},
    "Saint Vincent and the Grenadines": {"lon": -61.2872, "lat": 13.2528}, "Barbados": {"lon": -59.5432, "lat": 13.1939},
    "Antigua and Barbuda": {"lon": -61.7965, "lat": 17.0608}, "Grenada": {"lon": -61.6790, "lat": 12.1165},
    "Saint Lucia": {"lon": -60.9789, "lat": 13.9094}, "Dominica": {"lon": -61.3710, "lat": 15.4150},
    "Tonga": {"lon": -175.2018, "lat": -21.1790}, "Kiribati": {"lon": -168.7340, "lat": 1.8709},
    "Palau": {"lon": 134.5825, "lat": 7.5150}, "Nauru": {"lon": 166.9315, "lat": -0.5228},
    "Tuvalu": {"lon": 179.1942, "lat": -7.1095}, "Marshall Islands": {"lon": 171.1845, "lat": 7.1315},
    "Micronesia": {"lon": 158.1625, "lat": 6.9248}, "Samoa": {"lon": -172.1046, "lat": -13.7590},
    "Singapore": {"lon": 103.8198, "lat": 1.3521}, "Bahrain": {"lon": 50.5577, "lat": 26.0667},
    "Maldives": {"lon": 73.2207, "lat": 3.2028}, "Seychelles": {"lon": 55.4920, "lat": -4.6796},
    "Mauritius": {"lon": 57.5522, "lat": -20.3484}, 
    "Comoros": {"lon": 43.3333, "lat": -11.699}, 
    "Sao Tome and Principe": {"lon": 6.6131, "lat": 0.1864}, "Cape Verde": {"lon": -24.0130, "lat": 16.5388},
    "British Virgin Islands": {"lon": -64.6399, "lat": 18.4207}, "Anguilla": {"lon": -63.0686, "lat": 18.2206},
    "Bermuda": {"lon": -64.7505, "lat": 32.3078}, "Cayman Islands": {"lon": -81.2546, "lat": 19.3133},
    "Turks and Caicos Islands": {"lon": -71.7979, "lat": 21.6940}, "Montserrat": {"lon": -62.1874, "lat": 16.7425},
    "Gibraltar": {"lon": -5.3536, "lat": 36.1408}, "Saint Helena": {"lon": -5.7089, "lat": -15.9650},
    "Isle of Man": {"lon": -4.5481, "lat": 54.2361}, "Jersey": {"lon": -2.1358, "lat": 49.2144},
    "Guernsey": {"lon": -2.5857, "lat": 49.4657}, "American Samoa": {"lon": -170.1322, "lat": -14.2710},
    "Guam": {"lon": 144.7937, "lat": 13.4443}, "Northern Mariana Islands": {"lon": 145.6739, "lat": 15.0979},
    "US Virgin Islands": {"lon": -64.8963, "lat": 18.3358}, "Saint Pierre and Miquelon": {"lon": -56.2711, "lat": 46.8852},
    "Wallis and Futuna": {"lon": -176.1761, "lat": -13.7687}, "Saint Martin": {"lon": -63.0501, "lat": 18.0708},
    "Saint Barthelemy": {"lon": -62.8334, "lat": 17.9000}, "French Polynesia": {"lon": -149.4068, "lat": -17.6797},
    "Mayotte": {"lon": 45.1662, "lat": -12.8275}, 
    "Reunion": {"lon": 55.5364, "lat": -21.1151}, "Réunion": {"lon": 55.5364, "lat": -21.1151},
    "Martinique": {"lon": -61.0242, "lat": 14.6415}, "Guadeloupe": {"lon": -61.5510, "lat": 16.2650},
    "Aruba": {"lon": -69.9683, "lat": 12.5211}, "Curacao": {"lon": -68.9335, "lat": 12.1696},
    "Sint Maarten": {"lon": -63.0548, "lat": 18.0425}, "Bonaire": {"lon": -68.2624, "lat": 12.2019},
    "Saba": {"lon": -63.2324, "lat": 17.6353}, "Sint Eustatius": {"lon": -62.9738, "lat": 17.4890},
    "Cook Islands": {"lon": -159.7777, "lat": -21.2367}, "Niue": {"lon": -169.8672, "lat": -19.0544},
    "Tokelau": {"lon": -171.8554, "lat": -9.2002}, "Cocos Islands": {"lon": 96.828333, "lat": -12.186944},
    "Christmas Island": {"lon": 105.6275, "lat": -10.49}, "Hong Kong": {"lon": 114.1095, "lat": 22.3964},
    "Macao": {"lon": 113.5439, "lat": 22.1987}, "Faroe Islands": {"lon": -6.9118, "lat": 61.8926},
    "Trinidad and Tobago": {"lon": -61.2225, "lat": 10.6918}, "Norfolk Island": {"lon": 167.95, "lat": -29.033333},
    "Easter Island": {"lon": -109.35, "lat": -27.12}, "Aland": {"lon": 20.366667, "lat": 60.25},
    "Puerto Rico": {"lon": -66.5901, "lat": 18.2208},
    "New Caledonia": {"lon": 165.6180, "lat": -20.9043},
    "Falkland Islands": {"lon": -59.5236, "lat": -51.7963},
}

def get_microstate_trace(base_df, value_col, colorscale, zmin, zmax, hover_template, custom_data_cols, is_regional=False, line_color_logic=False):
    if "Hover_Name" not in base_df.columns: return None
    
    micro_df = base_df[base_df["Hover_Name"].isin(microstates.keys())].copy()
    if micro_df.empty: return None
    
    micro_df["lat"] = micro_df["Hover_Name"].map(lambda x: microstates.get(x, {}).get("lat"))
    micro_df["lon"] = micro_df["Hover_Name"].map(lambda x: microstates.get(x, {}).get("lon"))
    
    marker_line_color = "black" 
    
    if line_color_logic and value_col in micro_df.columns: 
         micro_df["BorderColor"] = micro_df[value_col].apply(
             lambda ratio: "#221e8f" if ratio > 0.5 else ("#8a005c" if ratio < 0.5 else "#666666")
         )
         marker_line_color = micro_df["BorderColor"]

    return go.Scattergeo(
        lon=micro_df["lon"], lat=micro_df["lat"], mode="markers",
        marker=dict(
            size=8, color=micro_df[value_col], colorscale=colorscale,
            cmin=zmin, cmax=zmax, line=dict(width=1, color=marker_line_color), showscale=False
        ),
        text=micro_df["Hover_Name"], customdata=micro_df[custom_data_cols], hovertemplate=hover_template
    )

# --- GLOBAL HELPER FUNCTIONS ---
def fix_table_name(row):
    if pd.notna(row['Hover_Name']): return row['Hover_Name']
    key = str(row['Join_Key'])
    name_map = {
        'USA': 'United States', 'GBR': 'United Kingdom', 'DEU': 'Germany', 'FRA': 'France',
        'CAN': 'Canada', 'AUS': 'Australia', 'IND': 'India', 'CHN': 'China', 'POL': 'Poland'
    }
    if key in name_map: return name_map[key]
    if len(key) == 3 and key.isupper():
        return cc.convert(names=key, to='name_short', not_found=key)
    return key

def get_final_date(row):
    d1 = row.get('Last_Date', pd.NaT)
    d2 = row.get('Excl_Date', pd.NaT)
    if pd.isna(d1): return d2
    if pd.isna(d2): return d1
    return max(d1, d2)

def get_final_loc(row, view_mode):
    d1 = row.get('Last_Date', pd.NaT)
    d2 = row.get('Excl_Date', pd.NaT)
    l1 = row.get('Last_Location_Raw', '')
    l2 = row.get('Excl_Loc_Raw', '')
    
    use_l1, use_l2 = False, False
    
    if pd.isna(d1): use_l2 = True
    elif pd.isna(d2): use_l1 = True
    elif d1 > d2: use_l1 = True
    elif d2 > d1: use_l2 = True
    else: use_l1 = True; use_l2 = True # TIE
    
    raw_locs = []
    if use_l1 and l1: raw_locs.extend(str(l1).split(";"))
    if use_l2 and l2: raw_locs.extend(str(l2).split(";"))
    
    if not raw_locs: return ""
    
    final_parts = []
    for loc in raw_locs:
        parts = loc.split("|")
        if len(parts) < 3: continue
        city, sub, ctry = parts[0].strip(), parts[1].strip(), parts[2].strip()
        
        key = str(row['Join_Key'])
        is_subdiv_row = False
        is_country_row = False
        
        if view_mode == "Countries":
             # If key is NOT 3-char ISO and not special split country ISO, it's a subdivision
             if len(key) != 3 and key not in ['USA', 'GBR', 'DEU', 'FRA', 'CAN', 'AUS', 'IND', 'CHN', 'POL']: 
                 is_subdiv_row = True
             else:
                 is_country_row = True
        else:
            # In Region view, Countries are rows if split, otherwise Regions
            if len(key) == 3 or key in ['USA', 'GBR', 'DEU', 'FRA', 'CAN', 'AUS', 'IND', 'CHN', 'POL']:
                is_country_row = True
        
        p_out = []
        if city: p_out.append(city)
        
        if is_subdiv_row:
            pass # Subdiv row: just City
        elif is_country_row:
            # Country row: City, Subdiv
            if sub and sub != city: p_out.append(sub)
        else:
            # Region/Continent row: City, Sub, Ctry
            if sub and sub != city: p_out.append(sub)
            if ctry and ctry != city: p_out.append(ctry)
        
        final_parts.append(", ".join(p_out))
    
    return "; ".join(sorted(list(set(final_parts))))

def get_simple_loc_str(row, view_mode):
    # Fallback if no exclusive logic ran (wrapper for same logic)
    # Mock a row with no Excl data so get_final_loc uses just L1
    row_mock = row.copy()
    row_mock['Excl_Date'] = pd.NaT
    row_mock['Excl_Loc_Raw'] = ''
    return get_final_loc(row_mock, view_mode)

def get_top_items_string(series, count_series=None):
    if series.empty: return ""
    if count_series is None:
        counts = series.value_counts()
    else:
        counts = pd.Series(count_series.values, index=series.values)
        counts = counts.groupby(level=0).sum().sort_values(ascending=False)
    if counts.empty: return ""
    top = counts.nlargest(3, keep='all')
    items = [f"{name} ({val})" for name, val in top.items()]
    return ", ".join(items)

# --- 1. Global Controls (Sidebar) ---
view_data = pd.DataFrame()

with st.sidebar:
    st.header("Map Settings")
    
    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"], errors='coerce')
        valid_rows = data.dropna(subset=["Date", "Country"])
        
        if not valid_rows.empty:
            min_date = valid_rows["Date"].min().date()
            max_date = valid_rows["Date"].max().date()
        else:
            min_date = datetime.date.today()
            max_date = datetime.date.today()
            
        selected_dates = st.slider("Select Date Range:", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="MM/DD/YY")
        mask = (data["Date"].dt.date >= selected_dates[0]) & (data["Date"].dt.date <= selected_dates[1])
        filtered_data = data[mask].copy()
    else:
        filtered_data = data.copy()
    
    # Placeholder for slider
    slider_ph = st.empty()
    
    st.divider()
    map_metric = st.radio("Select Metric:", options=["Count", "Comparison", "Michael", "Sarah"], horizontal=False)
    
    if map_metric != "Count":
        st.divider()
        score_mode = st.radio("Select Score Type:", options=["Total Score", "Geography Score", "Time Score"], horizontal=False)
    else:
        score_mode = "Total Score" 

    st.divider()
    view_mode = st.radio("Select View Level:", options=["Countries", "UN Regions", "Continents"], horizontal=False)
    
    split_options = ["United States", "United Kingdom", "Germany", "France", "Canada", "Australia", "India", "China", "Poland"]
    selected_splits = st.multiselect("Split Countries:", options=split_options, default=[])

    split_us = "United States" in selected_splits
    split_uk = "United Kingdom" in selected_splits
    split_germany = "Germany" in selected_splits
    split_france = "France" in selected_splits
    split_canada = "Canada" in selected_splits
    split_australia = "Australia" in selected_splits
    split_india = "India" in selected_splits
    split_china = "China" in selected_splits
    split_poland = "Poland" in selected_splits

    # --- Validation Logic ---
    if split_us:
        us_state_mapping = { "Washington DC": "District of Columbia", "Washington D.C.": "District of Columbia", "D.C.": "District of Columbia", "DC": "District of Columbia" }
        unique_cs = filtered_data['Country'].unique()
        iso_lookup = dict(zip(unique_cs, cc.convert(names=unique_cs, to='ISO3', not_found=None)))
        is_us_mask = filtered_data['Country'].map(iso_lookup) == 'USA'
        if is_us_mask.any(): filtered_data.loc[is_us_mask, 'Subdivision'] = filtered_data.loc[is_us_mask, 'Subdivision'].replace(us_state_mapping)

    if split_germany:
        germany_state_mapping = { "Baden-Wurttemberg": "Baden-Württemberg", "Bavaria": "Bayern", "Hesse": "Hessen", "Lower Saxony": "Niedersachsen", "North Rhine-Westphalia": "Nordrhein-Westfalen", "Rhineland-Palatinate": "Rheinland-Pfalz", "Saxony": "Sachsen", "Saxony-Anhalt": "Sachsen-Anhalt", "Thuringia": "Thüringen" }
        unique_cs = filtered_data['Country'].unique()
        iso_lookup = dict(zip(unique_cs, cc.convert(names=unique_cs, to='ISO3', not_found=None)))
        is_germany_mask = filtered_data['Country'].map(iso_lookup) == 'DEU'
        if is_germany_mask.any(): filtered_data.loc[is_germany_mask, 'Subdivision'] = filtered_data.loc[is_germany_mask, 'Subdivision'].replace(germany_state_mapping)
        germany_rows = filtered_data[is_germany_mask]
        if not germany_rows.empty:
            missing_subdivs = germany_rows[germany_rows['Subdivision'].isna()]
            if not missing_subdivs.empty: st.error("Error: Germany entries missing subdivision"); st.dataframe(missing_subdivs[['Date','Country','Subdivision']]); st.stop()
            if valid_map_names:
                unknown_subdivs = germany_rows[~germany_rows['Subdivision'].isin(valid_map_names)]
                if not unknown_subdivs.empty: st.error(f"Error: Unknown Germany subdivisions: {', '.join(unknown_subdivs['Subdivision'].unique())}"); st.stop()

    if split_france:
        france_region_mapping = { "Auvergne-Rhone-Alpes": "Auvergne-Rhône-Alpes", "Brittany": "Bretagne", "Burgundy-Franche-Comte": "Bourgogne-Franche-Comté", "Centre-Val de Loire": "Centre-Val de Loire", "Corsica": "Corse", "Grand Est": "Grand Est", "Hauts-de-France": "Hauts-de-France", "Ile-de-France": "Île-de-France", "Normandy": "Normandie", "Nouvelle-Aquitaine": "Nouvelle-Aquitaine", "Occitania": "Occitanie", "Pays de la Loire": "Pays de la Loire", "Provence-Alpes-Cote d'Azur": "Provence-Alpes-Côte d'Azur" }
        unique_cs = filtered_data['Country'].unique()
        iso_lookup = dict(zip(unique_cs, cc.convert(names=unique_cs, to='ISO3', not_found=None)))
        is_france_mask = filtered_data['Country'].map(iso_lookup) == 'FRA'
        if is_france_mask.any(): filtered_data.loc[is_france_mask, 'Subdivision'] = filtered_data.loc[is_france_mask, 'Subdivision'].replace(france_region_mapping)
        france_rows = filtered_data[is_france_mask]
        if not france_rows.empty:
            missing_subdivs = france_rows[france_rows['Subdivision'].isna()]
            if not missing_subdivs.empty: st.error("Error: France entries missing subdivision"); st.dataframe(missing_subdivs[['Date','Country','Subdivision']]); st.stop()
            if valid_map_names:
                unknown_subdivs = france_rows[~france_rows['Subdivision'].isin(valid_map_names)]
                if not unknown_subdivs.empty: st.error(f"Error: Unknown France subdivisions: {', '.join(unknown_subdivs['Subdivision'].unique())}"); st.stop()

    if split_canada:
        canada_prov_mapping = { "Québec": "Quebec", "Newfoundland": "Newfoundland and Labrador" }
        unique_cs = filtered_data['Country'].unique()
        iso_lookup = dict(zip(unique_cs, cc.convert(names=unique_cs, to='ISO3', not_found=None)))
        is_canada_mask = filtered_data['Country'].map(iso_lookup) == 'CAN'
        if is_canada_mask.any(): filtered_data.loc[is_canada_mask, 'Subdivision'] = filtered_data.loc[is_canada_mask, 'Subdivision'].replace(canada_prov_mapping)
        canada_rows = filtered_data[is_canada_mask]
        if not canada_rows.empty:
            missing_subdivs = canada_rows[canada_rows['Subdivision'].isna()]
            if not missing_subdivs.empty: st.error("Error: Canada entries missing subdivision"); st.dataframe(missing_subdivs[['Date','Country','Subdivision']]); st.stop()
            if valid_map_names:
                unknown_subdivs = canada_rows[~canada_rows['Subdivision'].isin(valid_map_names)]
                if not unknown_subdivs.empty: st.error(f"Error: Unknown Canada subdivisions: {', '.join(unknown_subdivs['Subdivision'].unique())}"); st.stop()

    if split_australia:
        australia_state_mapping = {}
        unique_cs = filtered_data['Country'].unique()
        iso_lookup = dict(zip(unique_cs, cc.convert(names=unique_cs, to='ISO3', not_found=None)))
        is_aus_mask = filtered_data['Country'].map(iso_lookup) == 'AUS'
        if is_aus_mask.any(): filtered_data.loc[is_aus_mask, 'Subdivision'] = filtered_data.loc[is_aus_mask, 'Subdivision'].replace(australia_state_mapping)
        aus_rows = filtered_data[is_aus_mask]
        if not aus_rows.empty:
            missing_subdivs = aus_rows[aus_rows['Subdivision'].isna()]
            if not missing_subdivs.empty: st.error("Error: Australia entries missing subdivision"); st.dataframe(missing_subdivs[['Date','Country','Subdivision']]); st.stop()
            if valid_map_names:
                unknown_subdivs = aus_rows[~aus_rows['Subdivision'].isin(valid_map_names)]
                if not unknown_subdivs.empty: st.error(f"Error: Unknown Australia subdivisions: {', '.join(unknown_subdivs['Subdivision'].unique())}"); st.stop()
    
    if split_india:
        india_state_mapping = { "Orissa": "Odisha", "Uttaranchal": "Uttarakhand", "Pondicherry": "Puducherry" }
        unique_cs = filtered_data['Country'].unique()
        iso_lookup = dict(zip(unique_cs, cc.convert(names=unique_cs, to='ISO3', not_found=None)))
        is_india_mask = filtered_data['Country'].map(iso_lookup) == 'IND'
        if is_india_mask.any(): filtered_data.loc[is_india_mask, 'Subdivision'] = filtered_data.loc[is_india_mask, 'Subdivision'].replace(india_state_mapping)
        india_rows = filtered_data[is_india_mask]
        if not india_rows.empty:
            missing_subdivs = india_rows[india_rows['Subdivision'].isna()]
            if not missing_subdivs.empty: st.error("Error: India entries missing subdivision"); st.dataframe(missing_subdivs[['Date','Country','Subdivision']]); st.stop()
            if valid_map_names:
                unknown_subdivs = india_rows[~india_rows['Subdivision'].isin(valid_map_names)]
                if not unknown_subdivs.empty: st.error(f"Error: Unknown India subdivisions: {', '.join(unknown_subdivs['Subdivision'].unique())}"); st.stop()

    if split_china:
        china_prov_mapping = { "Beijing": "Beijing Shi", "Shanghai": "Shanghai Shi", "Tianjin": "Tianjin Shi", "Chongqing": "Chongqing Shi", "Inner Mongolia": "Nei Mongol Zizhiqu", "Guangxi": "Guangxi Zhuangzu Zizhiqu", "Tibet": "Xizang Zizhiqu", "Ningxia": "Ningxia Zizhiiqu", "Xinjiang": "Xinjiang Uygur Zizhiqu", "Hong Kong": "Hong Kong", "Macau": "Macao", "Anhui": "Anhui Sheng", "Fujian": "Fujian Sheng", "Gansu": "Gansu Sheng", "Guangdong": "Guangdong Sheng", "Guizhou": "Guizhou Sheng", "Hainan": "Hainan Sheng", "Hebei": "Hebei Sheng", "Heilongjiang": "Heilongjiang Sheng", "Henan": "Henan Sheng", "Hubei": "Hubei Sheng", "Hunan": "Hunan Sheng", "Jiangsu": "Jiangsu Sheng", "Jiangxi": "Jiangxi Sheng", "Jilin": "Jilin Sheng", "Liaoning": "Liaoning Sheng", "Qinghai": "Qinghai Sheng", "Shaanxi": "Shaanxi Sheng", "Shandong": "Shandong Sheng", "Shanxi": "Shanxi Sheng", "Sichuan": "Sichuan Sheng", "Yunnan": "Yunnan Sheng", "Zhejiang": "Zhejiang Sheng", "Taiwan": "Taiwan" }
        unique_cs = filtered_data['Country'].unique()
        iso_lookup = dict(zip(unique_cs, cc.convert(names=unique_cs, to='ISO3', not_found=None)))
        is_china_mask = filtered_data['Country'].map(iso_lookup) == 'CHN'
        if is_china_mask.any(): filtered_data.loc[is_china_mask, 'Subdivision'] = filtered_data.loc[is_china_mask, 'Subdivision'].replace(china_prov_mapping)
        china_rows = filtered_data[is_china_mask]
        if not china_rows.empty:
            missing_subdivs = china_rows[china_rows['Subdivision'].isna()]
            if not missing_subdivs.empty: st.error("Error: China entries missing subdivision"); st.dataframe(missing_subdivs[['Date','Country','Subdivision']]); st.stop()
            if valid_map_names:
                unknown_subdivs = china_rows[~china_rows['Subdivision'].isin(valid_map_names)]
                if not unknown_subdivs.empty: st.error(f"Error: Unknown China subdivisions: {', '.join(unknown_subdivs['Subdivision'].unique())}"); st.stop()

    if split_poland:
        poland_mapping = { "Lower Silesian": "Dolnośląskie", "Kuyavian-Pomeranian": "Kujawsko-pomorskie", "Lublin": "Lubelskie", "Lubusz": "Lubuskie", "Łódź": "Łódzkie", "Lesser Poland": "Małopolskie", "Masovian": "Mazowieckie", "Opole": "Opolskie", "Podlaskie": "Podlaskie", "Pomeranian": "Pomorskie", "Silesian": "Śląskie", "Subcarpathian": "Podkarpackie", "Świętokrzyskie": "Świętokrzyskie", "Warmian-Masurian": "Warmińsko-mazurskie", "Greater Poland": "Wielkopolskie", "West Pomeranian": "Zachodniopomorskie" }
        unique_cs = filtered_data['Country'].unique()
        iso_lookup = dict(zip(unique_cs, cc.convert(names=unique_cs, to='ISO3', not_found=None)))
        is_poland_mask = filtered_data['Country'].map(iso_lookup) == 'POL'
        if is_poland_mask.any(): filtered_data.loc[is_poland_mask, 'Subdivision'] = filtered_data.loc[is_poland_mask, 'Subdivision'].replace(poland_mapping)
        poland_rows = filtered_data[is_poland_mask]
        if not poland_rows.empty:
            missing_subdivs = poland_rows[poland_rows['Subdivision'].isna()]
            if not missing_subdivs.empty: st.error("Error: Poland entries missing subdivision"); st.dataframe(missing_subdivs[['Date','Country','Subdivision']]); st.stop()
            if valid_map_names:
                unknown_subdivs = poland_rows[~poland_rows['Subdivision'].isin(valid_map_names)]
                if not unknown_subdivs.empty: st.error(f"Error: Unknown Poland subdivisions: {', '.join(unknown_subdivs['Subdivision'].unique())}"); st.stop()

    granular_split_us = split_us and (view_mode == "Countries")
    granular_split_uk = split_uk and (view_mode == "Countries")
    granular_split_germany = split_germany and (view_mode == "Countries")
    granular_split_france = split_france and (view_mode == "Countries")
    granular_split_canada = split_canada and (view_mode == "Countries")
    granular_split_australia = split_australia and (view_mode == "Countries")
    granular_split_india = split_india and (view_mode == "Countries")
    granular_split_china = split_china and (view_mode == "Countries")
    granular_split_poland = split_poland and (view_mode == "Countries")

    all_stats = precompute_stats_v12(filtered_data, granular_split_us, granular_split_uk, granular_split_germany, granular_split_france, granular_split_canada, granular_split_australia, granular_split_india, granular_split_china, granular_split_poland)
    
    if map_metric == "Michael":
        granular_key = f"Michael {score_mode}"
    elif map_metric == "Sarah":
        granular_key = f"Sarah {score_mode}"
    else:
        granular_key = f"Intersection {score_mode}"
        
    granular_data = all_stats[granular_key]
    
    view_data = aggregate_by_view_mode(granular_data, view_mode, split_us, split_uk, split_germany, split_france, split_canada, split_australia, split_india, split_china, split_poland)
    
    max_game_count = int(view_data["Count"].max()) if not view_data.empty else 1
    
    min_count_filter = slider_ph.slider("Minimum Games Played:", min_value=1, max_value=max_game_count, value=1)
    
    view_data = view_data[view_data["Count"] >= min_count_filter]

    active_granular = granular_data[granular_data["Count"] >= min_count_filter]
    if view_mode != "Countries" and not view_data.empty:
         valid_keys = view_data['Join_Key'].unique()
         col = "Continent" if view_mode == "Continents" else "UN_Region"
         mask_region = granular_data[col].isin(valid_keys)
         mask_state = granular_data['Join_Key'].isin(valid_keys)
         active_granular = granular_data[mask_region | mask_state]
    
    exclusive_keys = set()
    exclusive_isos = set()
    exclusive_counts_df = pd.DataFrame()
    
    if map_metric == "Count":
        p_mich = ["Michael Geography Score", "Michael Time Score"] 
        p_sarah = ["Sarah Geography Score", "Sarah Time Score"]
        
        df_excl = filtered_data[filtered_data["Date"].notna()].copy()
        
        def get_fmt_loc(row):
            city = str(row['City']).strip() if pd.notna(row.get('City')) else ''
            sub = str(row['Subdivision']).strip() if pd.notna(row.get('Subdivision')) else ''
            ctry = str(row['Country']).strip() if pd.notna(row.get('Country')) else ''
            parts = [p for p in [city, sub, ctry] if p]
            return "|".join(parts)

        df_excl['Formatted_Location'] = df_excl.apply(get_fmt_loc, axis=1)
        df_excl['Excl_City'] = df_excl['City']
        df_excl['Excl_Sub'] = df_excl['Subdivision']
        df_excl['Excl_Ctry'] = df_excl['Country']
        
        has_mich = df_excl[p_mich].notna().any(axis=1)
        has_sarah = df_excl[p_sarah].notna().any(axis=1)
        
        df_excl['Michael_Only'] = (has_mich & ~has_sarah).astype(int)
        df_excl['Sarah_Only'] = (~has_mich & has_sarah).astype(int)
        
        u_cs = df_excl["Country"].unique()
        i_map = dict(zip(u_cs, cc.convert(names=u_cs, to="ISO3", not_found=None)))
        df_excl["ISO3"] = df_excl["Country"].map(i_map)
        
        if view_mode != "Countries":
            c_map = dict(zip(u_cs, cc.convert(names=u_cs, to="continent")))
            u_map = dict(zip(u_cs, cc.convert(names=u_cs, to="UNregion")))
            if "Palestine" in u_cs:
                 c_map["Palestine"] = "Asia"
                 u_map["Palestine"] = "Western Asia"
            df_excl["Continent"] = df_excl["Country"].map(c_map)
            df_excl["UN_Region"] = df_excl["Country"].map(u_map)

        base_g = "Continent" if view_mode == "Continents" else "UN_Region"
        
        def get_agg_key_raw_excl(row):
            iso = row['ISO3']
            subdiv = row.get('Subdivision')
            is_split = False
            if split_us and iso == 'USA': is_split = True
            elif split_uk and iso == 'GBR': is_split = True
            elif split_germany and iso == 'DEU': is_split = True
            elif split_france and iso == 'FRA': is_split = True
            elif split_canada and iso == 'CAN': is_split = True
            elif split_australia and iso == 'AUS': is_split = True
            elif split_india and iso == 'IND': is_split = True
            elif split_china and iso == 'CHN': is_split = True
            elif split_poland and iso == 'POL': is_split = True
            
            if is_split:
                if view_mode == "Countries":
                     if pd.notna(subdiv): return subdiv
                     return iso
                else:
                     return iso
            
            if view_mode == "Countries": return iso
            return row[base_g]

        df_excl['Agg_Key'] = df_excl.apply(get_agg_key_raw_excl, axis=1)
        
        df_really_excl = df_excl[(df_excl['Michael_Only'] == 1) | (df_excl['Sarah_Only'] == 1)].copy()
        df_really_excl = df_really_excl.sort_values("Date", ascending=False)
        
        exclusive_counts_df = df_excl.groupby('Agg_Key').agg({
            'Michael_Only': 'sum',
            'Sarah_Only': 'sum'
        }).reset_index()
        
        excl_dates = df_really_excl.groupby('Agg_Key').agg({
            'Date': 'first',
            'Excl_City': 'first',
            'Excl_Sub': 'first',
            'Excl_Ctry': 'first',
            'Formatted_Location': 'first' # For fallback comparison
        }).reset_index().rename(columns={'Date': 'Excl_Date', 'Formatted_Location': 'Excl_Loc_Raw'})
        
        exclusive_counts_df = pd.merge(exclusive_counts_df, excl_dates, on='Agg_Key', how='left')

        df_has_excl = exclusive_counts_df[(exclusive_counts_df['Michael_Only'] > 0) | (exclusive_counts_df['Sarah_Only'] > 0)]
        exclusive_keys = set(df_has_excl['Agg_Key'].unique())
        isos_needed = df_excl[df_excl['Agg_Key'].isin(exclusive_keys)]['ISO3'].unique()
        exclusive_isos = set(isos_needed)

    base_isos = set(active_granular['ISO3'].unique().tolist())
    final_active_isos = tuple(sorted(base_isos.union(exclusive_isos)))

    map_json = generate_dynamic_map_layer(base_gdf, final_active_isos, split_us, split_uk, split_germany, split_france, split_canada, split_australia, split_india, split_china, split_poland, view_mode)
    bg_geojson = get_background_layer(base_gdf)

    if map_json:
        feats = []
        for f in map_json['features']:
            feats.append(f['properties'])
        
        map_props = pd.DataFrame(feats)
        map_df = pd.merge(map_props, view_data, left_on='Dissolve_Key', right_on='Join_Key', how='left')
        
        if 'Hover_Name' in map_df.columns:
            def fix_hover_name_map(row):
                if pd.notna(row['Hover_Name']): return row['Hover_Name']
                key = str(row['Dissolve_Key'])
                if len(key) == 3 and key.isupper():
                    return cc.convert(names=key, to='name_short', not_found=key)
                return key
            map_df['Hover_Name'] = map_df.apply(fix_hover_name_map, axis=1)
        
        # Initialize Score_String for all modes to prevent KeyError on bubbles
        map_df['Score_String'] = ''
        if not view_data.empty:
            view_data['Score_String'] = ''

        map_df['Count'] = map_df['Count'].fillna(0)
        
        if map_metric == "Count" and not exclusive_counts_df.empty:
            map_df = pd.merge(map_df, exclusive_counts_df, left_on='Dissolve_Key', right_on='Agg_Key', how='left')
            map_df['Michael_Only'] = map_df['Michael_Only'].fillna(0).astype(int)
            map_df['Sarah_Only'] = map_df['Sarah_Only'].fillna(0).astype(int)
            
            def build_excl_str(row):
                s = ""
                if row.get('Michael_Only', 0) > 0: s += f"Michael Only: {row['Michael_Only']}<br>"
                if row.get('Sarah_Only', 0) > 0: s += f"Sarah Only: {row['Sarah_Only']}<br>"
                return s
            
            map_df['Hover_Extra'] = map_df.apply(build_excl_str, axis=1)
            if not view_data.empty:
                view_data = pd.merge(view_data, exclusive_counts_df, left_on='Join_Key', right_on='Agg_Key', how='left')
                view_data['Hover_Extra'] = view_data.apply(build_excl_str, axis=1)
        else:
            map_df['Hover_Extra'] = ''
            if not view_data.empty:
                view_data['Hover_Extra'] = ''
            
    else:
        map_df = pd.DataFrame()

# --- 6. Visualization Logic ---

layout_settings = dict(
    geo=dict(
        showframe=False, 
        bgcolor="white", 
        showland=False, 
        showcountries=False, 
        showcoastlines=False, 
        showocean=False,
        projection=dict(type="robinson"),
        fitbounds=False
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Poppins, Arial, sans-serif", color="#000000"),
    width=1600, height=850, 
    coloraxis_showscale=False, showlegend=False,
    margin=dict(t=0, b=0, l=0, r=0)
)

fig = go.Figure()

if bg_geojson:
    fig.add_trace(go.Choropleth(
        geojson=bg_geojson,
        locations=[1], z=[1], 
        featureidkey="properties.World_Group",
        colorscale=[[0, "#eeeeee"], [1, "#eeeeee"]],
        showscale=False,
        marker_line_color="white", marker_line_width=0.1,
        hoverinfo='skip'
    ))

if map_json and not map_df.empty:
    count_scale = [[0.0, "#fee6e6"], [1.0, "#db5049"]]
    comparison_scale = [[0.0, "#8a005c"], [0.5, "#f2f2f2"], [1.0, "#221e8f"]]
    michael_scale = [[0.0, "#e6e6ff"], [1.0, "#221e8f"]]
    sarah_scale = [[0.0, "#ffe6f2"], [1.0, "#8a005c"]]

    z_col, scale, z_min, z_max = "Count", count_scale, 0, max_game_count
    border_color, border_width = "black", 0.5
    
    hover_base = "<b>%{text}</b><br>"
    custom_cols = []
    hover_fmt = hover_base + "Count: %{z}<extra></extra>"

    if map_metric == "Count":
        df_filled = map_df[map_df["Count"] > 0].copy()
        
        df_filled = add_calculated_colors(df_filled, "Count", count_scale, 0, max_game_count)
        
        def get_filled_border(row):
            if (row.get('Michael_Only', 0) > 0) or (row.get('Sarah_Only', 0) > 0):
                return '#221e8f' # Dark Blue
            return 'black'
        
        filled_borders = df_filled.apply(get_filled_border, axis=1)
        filled_width = 1.0

        custom_cols = ["Hover_Extra"]
        hover_fmt = hover_base + "Count: %{z}<br>%{customdata[0]}<extra></extra>"
        
        fig.add_trace(go.Choropleth(
            geojson=map_json,
            locations=df_filled['Dissolve_Key'],
            z=df_filled['Count'],
            featureidkey="properties.Dissolve_Key",
            colorscale=count_scale,
            zmin=0, zmax=max_game_count,
            marker_line_color=filled_borders,
            marker_line_width=filled_width,
            showscale=False,
            text=df_filled['Hover_Name'],
            customdata=df_filled[custom_cols] if custom_cols else None,
            hovertemplate=hover_fmt
        ))
        
        df_border_only = map_df[map_df['Count'] == 0].copy()
        df_border_only = df_border_only[df_border_only['Dissolve_Key'].isin(exclusive_keys)]
        
        if not df_border_only.empty:
            if 'Hover_Extra' not in df_border_only.columns:
                df_border_only['Hover_Extra'] = ''

            hover_fmt_border = hover_base + "Count: 0<br>%{customdata[0]}<extra></extra>"
            
            fig.add_trace(go.Choropleth(
                geojson=map_json,
                locations=df_border_only['Dissolve_Key'],
                z=[0]*len(df_border_only), 
                featureidkey="properties.Dissolve_Key",
                colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']], 
                marker_line_color='#221e8f', 
                marker_line_width=1.0, 
                showscale=False,
                text=df_border_only['Hover_Name'],
                customdata=df_border_only[custom_cols], 
                hovertemplate=hover_fmt_border
            ))
        
    elif map_metric == "Comparison":
        map_df = add_calculated_colors(map_df, "Michael Share Ratio", comparison_scale, 0.4, 0.6)
        z_col, scale, z_min, z_max = "Michael Share Ratio", comparison_scale, 0.4, 0.6
        border_width = 1.0
        border_color = map_df["Michael Share Ratio"].apply(lambda r: "#221e8f" if r > 0.5 else ("#8a005c" if r < 0.5 else "#666666"))
        custom_cols = ['Michael Avg', 'Sarah Avg', 'Michael Share %', 'Sarah Share %']
        hover_fmt = hover_base + "Michael Avg: %{customdata[0]:,.0f}<br>Sarah Avg: %{customdata[1]:,.0f}<br>Share: %{customdata[2]} vs %{customdata[3]}<extra></extra>"
        
        # Need to re-calculate Efficiencies for hover if they aren't in map_df (they are in view_data, merged to map_df)
        map_df['Michael Eff %'] = (map_df['Michael Efficiency'] * 100).map('{:,.1f}%'.format)
        map_df['Sarah Eff %'] = (map_df['Sarah Efficiency'] * 100).map('{:,.1f}%'.format)
        custom_cols = ['Michael Efficiency', 'Sarah Efficiency', 'Michael Share %', 'Sarah Share %']
        
        fig.add_trace(go.Choropleth(
            geojson=map_json,
            locations=map_df['Dissolve_Key'],
            z=map_df[z_col],
            featureidkey="properties.Dissolve_Key",
            colorscale=scale,
            zmin=z_min, zmax=z_max,
            marker_line_color=border_color,
            marker_line_width=border_width,
            showscale=False,
            text=map_df['Hover_Name'],
            customdata=map_df[custom_cols] if custom_cols else None,
            hovertemplate=hover_fmt
        ))

    elif map_metric == "Michael":
        map_df = add_calculated_colors(map_df, "Michael Efficiency", michael_scale, 0.5, 1.0)
        z_col, scale, z_min, z_max = "Michael Efficiency", michael_scale, 0.5, 1.0
        
        def get_score_str(row, col_prefix):
            sel = row.get(f"{col_prefix} Selected", 0)
            tot = row.get("Total Possible", 0)
            if pd.isna(sel): sel = 0
            if pd.isna(tot): tot = 0
            return f"{sel:,.0f}/{tot:,.0f}"

        map_df['Score_String'] = map_df.apply(lambda r: get_score_str(r, "Michael"), axis=1)
        # Apply to view_data for bubbles
        if 'Score_String' in view_data.columns:
            view_data['Score_String'] = view_data.apply(lambda r: get_score_str(r, "Michael"), axis=1)
        
        custom_cols = ["Michael Eff %", "Score_String"]
        hover_fmt = hover_base + "Percent: %{customdata[0]}<br>Total Score: %{customdata[1]}<extra></extra>"
        
        fig.add_trace(go.Choropleth(
            geojson=map_json,
            locations=map_df['Dissolve_Key'],
            z=map_df[z_col],
            featureidkey="properties.Dissolve_Key",
            colorscale=scale,
            zmin=z_min, zmax=z_max,
            marker_line_color=border_color,
            marker_line_width=border_width,
            showscale=False,
            text=map_df['Hover_Name'],
            customdata=map_df[custom_cols] if custom_cols else None,
            hovertemplate=hover_fmt
        ))

    elif map_metric == "Sarah":
        map_df = add_calculated_colors(map_df, "Sarah Efficiency", sarah_scale, 0.5, 1.0)
        z_col, scale, z_min, z_max = "Sarah Efficiency", sarah_scale, 0.5, 1.0
        
        def get_score_str(row, col_prefix):
            sel = row.get(f"{col_prefix} Selected", 0)
            tot = row.get("Total Possible", 0)
            if pd.isna(sel): sel = 0
            if pd.isna(tot): tot = 0
            return f"{sel:,.0f}/{tot:,.0f}"

        map_df['Score_String'] = map_df.apply(lambda r: get_score_str(r, "Sarah"), axis=1)
        if 'Score_String' in view_data.columns:
            view_data['Score_String'] = view_data.apply(lambda r: get_score_str(r, "Sarah"), axis=1)
        
        custom_cols = ["Sarah Eff %", "Score_String"]
        hover_fmt = hover_base + "Percent: %{customdata[0]}<br>Total Score: %{customdata[1]}<extra></extra>"

        fig.add_trace(go.Choropleth(
            geojson=map_json,
            locations=map_df['Dissolve_Key'],
            z=map_df[z_col],
            featureidkey="properties.Dissolve_Key",
            colorscale=scale,
            zmin=z_min, zmax=z_max,
            marker_line_color=border_color,
            marker_line_width=border_width,
            showscale=False,
            text=map_df['Hover_Name'],
            customdata=map_df[custom_cols] if custom_cols else None,
            hovertemplate=hover_fmt
        ))

    if map_metric == "Count":
        if 'Hover_Extra' not in view_data.columns:
            view_data['Hover_Extra'] = ''
        ms_cols = (custom_cols if custom_cols else []) + [z_col]
        ms_hover = hover_fmt.replace("%{z}", f"%{{customdata[{len(ms_cols)-1}]}}")
        ms_trace = get_microstate_trace(view_data, z_col, scale, z_min, z_max, ms_hover, ms_cols, line_color_logic=(map_metric=="Comparison"))
    else:
        ms_trace = get_microstate_trace(view_data, z_col, scale, z_min, z_max, hover_fmt, custom_cols, line_color_logic=(map_metric=="Comparison"))
    
    if ms_trace: fig.add_trace(ms_trace)

if map_metric == "Comparison":
    st.markdown(f"""<div style="text-align: center;">...legend...</div>""", unsafe_allow_html=True)
elif map_metric == "Michael":
    st.caption(f"Showing Michael's **Efficiency**.")
elif map_metric == "Sarah":
    st.caption(f"Showing Sarah's **Efficiency**.")

fig.update_layout(**layout_settings)
st.plotly_chart(fig, use_container_width=True)

# --- 7. Table ---
st.divider()
st.subheader(f"Statistics by {view_mode}")

if not view_data.empty or (map_metric == "Count" and not exclusive_counts_df.empty):
    if not view_data.empty:
         table_df = view_data.sort_values("Count", ascending=False)
    else:
         table_df = pd.DataFrame()
    
    if map_metric == "Count":
        if view_mode == "Countries":
            raw_work = filtered_data.copy()
            req_cols = ["Michael Geography Score", "Michael Time Score", "Sarah Geography Score", "Sarah Time Score"]
            raw_work = raw_work.dropna(subset=req_cols)
            unique_cs = raw_work["Country"].unique()
            iso_map = dict(zip(unique_cs, cc.convert(names=unique_cs, to="ISO3", not_found=None)))
            raw_work["ISO3"] = raw_work["Country"].map(iso_map)
            
            def local_join_key(row):
                iso = row['ISO3']
                subdiv = row.get('Subdivision')
                is_split = False
                if split_us and iso == 'USA': is_split = True
                elif split_uk and iso == 'GBR': is_split = True
                elif split_germany and iso == 'DEU': is_split = True
                elif split_france and iso == 'FRA': is_split = True
                elif split_canada and iso == 'CAN': is_split = True
                elif split_australia and iso == 'AUS': is_split = True
                elif split_india and iso == 'IND': is_split = True
                elif split_china and iso == 'CHN': is_split = True
                elif split_poland and iso == 'POL': is_split = True
                
                if is_split and pd.notna(subdiv): return subdiv
                return iso
            
            raw_work['Join_Key'] = raw_work.apply(local_join_key, axis=1)
            city_col = "City" if "City" in raw_work.columns else None
            
            if city_col:
                top_cities = raw_work.groupby('Join_Key')[city_col].apply(lambda x: get_top_items_string(x)).reset_index()
                top_cities.columns = ['Join_Key', 'Top 3 Cities']
                table_df = pd.merge(table_df, top_cities, on='Join_Key', how='left')
                display_cols = ["Hover_Name", "Count", "Top 3 Cities"]
            else:
                display_cols = ["Hover_Name", "Count"]

        else:
            base_group = "Continent" if view_mode == "Continents" else "UN_Region"
            def local_agg_key(row):
                iso = row['ISO3']
                if split_us and iso == 'USA': return 'USA'
                if split_uk and iso == 'GBR': return 'GBR'
                if split_germany and iso == 'DEU': return 'DEU'
                if split_france and iso == 'FRA': return 'FRA'
                if split_canada and iso == 'CAN': return 'CAN'
                if split_australia and iso == 'AUS': return 'AUS'
                if split_india and iso == 'IND': return 'IND'
                if split_china and iso == 'CHN': return 'CHN'
                if split_poland and iso == 'POL': return 'POL'
                return row[base_group]
            
            granular_work = granular_data.copy()
            granular_work['Agg_Key'] = granular_work.apply(local_agg_key, axis=1)
            
            top_countries = granular_work.groupby('Agg_Key').apply(
                lambda x: get_top_items_string(x['Display_Name'], x['Count'])
            ).reset_index()
            top_countries.columns = ['Join_Key', 'Top 3 Countries']
            
            table_df = pd.merge(table_df, top_countries, on='Join_Key', how='left')
            display_cols = ["Hover_Name", "Count", "Top 3 Countries"]

        if not exclusive_counts_df.empty:
            excl_merge = exclusive_counts_df.rename(columns={'Agg_Key': 'Join_Key_Excl'})
            if table_df.empty:
                table_df = pd.DataFrame(columns=['Join_Key', 'Hover_Name', 'Count', 'Last_Date', 'Last_Location_Raw'])
                
            merged_table = pd.merge(table_df, excl_merge, left_on='Join_Key', right_on='Join_Key_Excl', how='outer')
            merged_table['Join_Key'] = merged_table['Join_Key'].fillna(merged_table['Join_Key_Excl'])
            
            if 'Count' in merged_table.columns: merged_table['Count'] = merged_table['Count'].fillna(0)
            if 'Last_Date' not in merged_table.columns: merged_table['Last_Date'] = pd.NaT
            if 'Excl_Date' not in merged_table.columns: merged_table['Excl_Date'] = pd.NaT
            if 'Last_Location_Raw' not in merged_table.columns: merged_table['Last_Location_Raw'] = ''
            if 'Excl_Loc_Raw' not in merged_table.columns: merged_table['Excl_Loc_Raw'] = ''
            
            merged_table['Hover_Name'] = merged_table.apply(fix_table_name, axis=1)
            
            merged_table['Most Recent Date'] = merged_table.apply(get_final_date, axis=1)
            merged_table['Most Recent Location'] = merged_table.apply(lambda r: get_final_loc(r, view_mode), axis=1)
            merged_table['Most Recent Date'] = pd.to_datetime(merged_table['Most Recent Date']).dt.strftime('%Y-%m-%d').fillna('')

            table_df = merged_table
            display_cols.extend(["Most Recent Date", "Most Recent Location"])
        else:
            table_df['Most Recent Date'] = pd.to_datetime(table_df['Last_Date']).dt.strftime('%Y-%m-%d').fillna('')
            table_df['Most Recent Location'] = table_df.apply(lambda r: get_simple_loc_str(r, view_mode), axis=1)
            display_cols.extend(["Most Recent Date", "Most Recent Location"])

        final_cols = [c for c in display_cols if c in table_df.columns]
        display_df = table_df[final_cols].copy()
    
    elif map_metric == "Comparison":
        display_df = table_df.copy()
        
        if "Michael Win" in display_df.columns and "Sarah Win" in display_df.columns:
             display_df['Total Wins'] = display_df['Michael Win'] + display_df['Sarah Win']
             display_df['Wins Ratio'] = display_df.apply(
                 lambda x: x['Michael Win'] / x['Total Wins'] if x['Total Wins'] > 0 else 0.5, axis=1
             )
        else:
             display_df['Wins Ratio'] = np.nan
             display_df['Michael Win'] = 0
             display_df['Sarah Win'] = 0

        if "Michael Share Ratio" in display_df.columns:
             display_df['Score Ratio'] = display_df['Michael Share Ratio']
        else:
             display_df['Score Ratio'] = np.nan

        display_df = display_df.rename(columns={
            "Michael Win": "Michael Wins",
            "Sarah Win": "Sarah Wins",
            "Michael Avg": "Michael Average Score",
            "Sarah Avg": "Sarah Average Score"
        })
        
        cols_to_show = ['Hover_Name', 'Count', 'Michael Average Score', 'Sarah Average Score', 'Michael Wins', 'Sarah Wins', 'Score Ratio', 'Wins Ratio']
        cols_to_show = [c for c in cols_to_show if c in display_df.columns]
        display_df = display_df[cols_to_show]

    elif map_metric in ["Michael", "Sarah"]:
        prefix = "Michael" if map_metric == "Michael" else "Sarah"
        
        if score_mode == "Total Score":
            calc_cols = [f"{prefix} Geography Score", f"{prefix} Time Score"]
            filter_cols = calc_cols
            max_points = 10000
        elif score_mode == "Geography Score":
            calc_cols = [f"{prefix} Geography Score"]
            filter_cols = calc_cols
            max_points = 5000
        else:
            calc_cols = [f"{prefix} Time Score"]
            filter_cols = calc_cols
            max_points = 5000
            
        raw_work = filtered_data.dropna(subset=filter_cols + ["Date"]).copy()
        raw_work['Selected_Score'] = raw_work[calc_cols].sum(axis=1)
        
        unique_cs = raw_work["Country"].unique()
        iso_map = dict(zip(unique_cs, cc.convert(names=unique_cs, to="ISO3", not_found=None)))
        raw_work["ISO3"] = raw_work["Country"].map(iso_map)
        
        if view_mode != "Countries":
            cont_map = dict(zip(unique_cs, cc.convert(names=unique_cs, to="continent")))
            un_map = dict(zip(unique_cs, cc.convert(names=unique_cs, to="UNregion")))
            if "Palestine" in unique_cs:
                 cont_map["Palestine"] = "Asia"
                 un_map["Palestine"] = "Western Asia"
            raw_work["Continent"] = raw_work["Country"].map(cont_map)
            raw_work["UN_Region"] = raw_work["Country"].map(un_map)

        base_group = "Continent" if view_mode == "Continents" else "UN_Region"
        
        def local_agg_key_raw(row):
            iso = row['ISO3']
            subdiv = row.get('Subdivision')
            is_split = False
            if split_us and iso == 'USA': is_split = True
            elif split_uk and iso == 'GBR': is_split = True
            elif split_germany and iso == 'DEU': is_split = True
            elif split_france and iso == 'FRA': is_split = True
            elif split_canada and iso == 'CAN': is_split = True
            elif split_australia and iso == 'AUS': is_split = True
            elif split_india and iso == 'IND': is_split = True
            elif split_china and iso == 'CHN': is_split = True
            elif split_poland and iso == 'POL': is_split = True
            
            if is_split:
                if view_mode == "Countries":
                    if pd.notna(subdiv): return subdiv
                    return iso
                else:
                    return iso
            
            if view_mode == "Countries":
                return iso
            return row[base_group]

        raw_work['Agg_Key'] = raw_work.apply(local_agg_key_raw, axis=1)
        
        stats_df = raw_work.groupby('Agg_Key').agg(
            Count=('Selected_Score', 'count'),
            Sum_Score=('Selected_Score', 'sum'),
            Mean=('Selected_Score', 'mean'),
            Median=('Selected_Score', 'median'),
            Max=('Selected_Score', 'max'),
            Min=('Selected_Score', 'min')
        ).reset_index()
        
        stats_df['Total_Possible'] = stats_df['Count'] * max_points
        stats_df['Percentage'] = (stats_df['Sum_Score'] / stats_df['Total_Possible']) * 100
        
        split_name_map = {
            'USA': 'United States', 'GBR': 'United Kingdom', 'DEU': 'Germany', 'FRA': 'France',
            'CAN': 'Canada', 'AUS': 'Australia', 'IND': 'India', 'CHN': 'China', 'POL': 'Poland'
        }
        all_keys = stats_df['Agg_Key'].unique()
        iso_keys = [k for k in all_keys if len(k) == 3 and k.isupper() and k not in split_name_map]
        
        if iso_keys:
            iso_names = cc.convert(names=iso_keys, to='name_short')
            full_iso_map = dict(zip(iso_keys, iso_names))
            full_map = {**split_name_map, **full_iso_map}
        else:
            full_map = split_name_map
            
        stats_df['Hover_Name'] = stats_df['Agg_Key'].replace(full_map)
        display_df = stats_df
        display_df['Percentage'] = display_df['Percentage'].map('{:.1f}%'.format)
        display_df['Mean Score'] = display_df['Mean'].round(0).astype(int)
        display_df['Median Score'] = display_df['Median'].round(0).astype(int)
        display_df['Highest Score'] = display_df['Max'].astype(int)
        display_df['Lowest Score'] = display_df['Min'].astype(int)
        display_df = display_df[['Hover_Name', 'Count', 'Percentage', 'Mean Score', 'Median Score', 'Highest Score', 'Lowest Score']]
    
    any_split = any([split_us, split_uk, split_germany, split_france, split_canada, split_australia, split_india, split_china, split_poland])
    
    if view_mode == "Countries":
        col_name = "Country/Subdivision" if any_split else "Country"
    elif view_mode == "UN Regions":
        col_name = "UN Region/Country" if any_split else "UN Region"
    else: # Continents
        col_name = "Continent/Country" if any_split else "Continent"

    display_df = display_df.rename(columns={"Hover_Name": col_name})

    if map_metric == "Comparison":
        def style_gradient(val):
            if pd.isna(val): return ""
            p = val * 100
            return f"background: linear-gradient(to right, #221e8f {p}%, #8a005c {p}%); color: white;"
        
        st.dataframe(
            display_df.style.map(style_gradient, subset=['Score Ratio', 'Wins Ratio'])
                            .format({'Score Ratio': '{:.1%}', 'Wins Ratio': '{:.1%}'}, na_rep="N/A"),
            use_container_width=True, hide_index=True
        )
    else:
        st.dataframe(display_df, use_container_width=True, hide_index=True)