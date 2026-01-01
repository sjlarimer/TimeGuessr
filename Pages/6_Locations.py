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
import plotly.graph_objects as go
import country_converter as coco
import numpy as np
from plotly.colors import sample_colorscale
import json
import os
import geopandas as gpd

# --- Configuration & Constants ---
st.set_page_config(layout="wide")

COLORS = {'michael': '#221e8f', 'sarah': '#8a005c', 'neutral': '#696761'}

# Split Configuration
SPLIT_CONFIG = {
    "USA": {"name": "United States", "map": {"Washington DC": "District of Columbia", "Washington D.C.": "District of Columbia", "D.C.": "District of Columbia", "DC": "District of Columbia"}},
    "GBR": {"name": "United Kingdom", "map": {}},
    "DEU": {"name": "Germany", "map": {"Baden-Wurttemberg": "Baden-Württemberg", "Bavaria": "Bayern", "Hesse": "Hessen", "Lower Saxony": "Niedersachsen", "North Rhine-Westphalia": "Nordrhein-Westfalen", "Rhineland-Palatinate": "Rheinland-Pfalz", "Saxony": "Sachsen", "Saxony-Anhalt": "Sachsen-Anhalt", "Thuringia": "Thüringen"}},
    "FRA": {"name": "France", "map": {"Auvergne-Rhone-Alpes": "Auvergne-Rhône-Alpes", "Brittany": "Bretagne", "Burgundy-Franche-Comte": "Bourgogne-Franche-Comté", "Centre-Val de Loire": "Centre-Val de Loire", "Corsica": "Corse", "Grand Est": "Grand Est", "Hauts-de-France": "Hauts-de-France", "Ile-de-France": "Île-de-France", "Normandy": "Normandie", "Nouvelle-Aquitaine": "Nouvelle-Aquitaine", "Occitania": "Occitanie", "Pays de la Loire": "Pays de la Loire", "Provence-Alpes-Cote d'Azur": "Provence-Alpes-Côte d'Azur"}},
    "CAN": {"name": "Canada", "map": {"Québec": "Quebec", "Newfoundland": "Newfoundland and Labrador"}},
    "AUS": {"name": "Australia", "map": {}},
    "IND": {"name": "India", "map": {"Orissa": "Odisha", "Uttaranchal": "Uttarakhand", "Pondicherry": "Puducherry"}},
    "CHN": {"name": "China", "map": {"Beijing": "Beijing Shi", "Shanghai": "Shanghai Shi", "Tianjin": "Tianjin Shi", "Chongqing": "Chongqing Shi", "Inner Mongolia": "Nei Mongol Zizhiqu", "Guangxi": "Guangxi Zhuangzu Zizhiqu", "Tibet": "Xizang Zizhiqu", "Ningxia": "Ningxia Zizhiiqu", "Xinjiang": "Xinjiang Uygur Zizhiqu", "Hong Kong": "Hong Kong", "Macau": "Macao", "Anhui": "Anhui Sheng", "Fujian": "Fujian Sheng", "Gansu": "Gansu Sheng", "Guangdong": "Guangdong Sheng", "Guizhou": "Guizhou Sheng", "Hainan": "Hainan Sheng", "Hebei": "Hebei Sheng", "Heilongjiang": "Heilongjiang Sheng", "Henan": "Henan Sheng", "Hubei": "Hubei Sheng", "Hunan": "Hunan Sheng", "Jiangsu": "Jiangsu Sheng", "Jiangxi": "Jiangxi Sheng", "Jilin": "Jilin Sheng", "Liaoning": "Liaoning Sheng", "Qinghai": "Qinghai Sheng", "Shaanxi": "Shaanxi Sheng", "Shandong": "Shandong Sheng", "Shanxi": "Shanxi Sheng", "Sichuan": "Sichuan Sheng", "Yunnan": "Yunnan Sheng", "Zhejiang": "Zhejiang Sheng", "Taiwan": "Taiwan"}},
    "POL": {"name": "Poland", "map": {"Lower Silesian": "Dolnośląskie", "Kuyavian-Pomeranian": "Kujawsko-pomorskie", "Lublin": "Lubelskie", "Lubelskie": "Lubelskie", "Lubusz": "Lubuskie", "Łódź": "Łódzkie", "Lesser Poland": "Małopolskie", "Masovian": "Mazowieckie", "Opole": "Opolskie", "Podlaskie": "Podlaskie", "Pomeranian": "Pomorskie", "Silesian": "Śląskie", "Subcarpathian": "Podkarpackie", "Świętokrzyskie": "Świętokrzyskie", "Warmian-Masurian": "Warmińsko-mazurskie", "Greater Poland": "Wielkopolskie", "West Pomeranian": "Zachodniopomorskie"}},
    "RUS": {"name": "Russia", "map": {
        "Adygea": "Adygeya, Respublika", "Altai": "Altay, Respublika", "Altai Krai": "Altayskiy kray", "Amur Oblast": "Amurskaya oblast'", "Arkhangelsk Oblast": "Arkhangel'skaya oblast'", "Astrakhan Oblast": "Astrakhanskaya oblast'", "Bashkortostan": "Bashkortostan, Respublika", "Belgorod Oblast": "Belgorodskaya oblast'", "Bryansk Oblast": "Bryanskaya oblast'", "Buryatia": "Buryatiya, Respublika", "Chechnya": "Chechenskaya Respublika", "Chelyabinsk Oblast": "Chelyabinskaya oblast'", "Chukotka Autonomous Okrug": "Chukotskiy avtonomnyy okrug", "Chuvashia": "Chuvashskaya Respublika", "Dagestan": "Dagestan, Respublika", "Ingushetia": "Ingushskaya, Respublika", "Irkutsk Oblast": "Irkutskaya oblast'", "Ivanovo Oblast": "Ivanovskaya oblast'", "Kabardino-Balkaria": "Kabardino-Balkarskaya Respublika", "Kaliningrad Oblast": "Kaliningradskaya oblast'", "Kalmykia": "Kalmykiya, Respublika", "Kaluga Oblast": "Kaluzhskaya oblast'", "Kamchatka Krai": "Kamchatskiy kray", "Karachay-Cherkessia": "Karachayevo-Cherkesskaya Respublika", "Karelia": "Kareliya, Respublika", "Kemerovo Oblast": "Kemerovskaya oblast'", "Khabarovsk Krai": "Khabarovskiy kray", "Khakassia": "Khakasiya, Respublika", "Khanty-Mansi Autonomous Okrug": "Khanty-Mansiyskiy avtonomnyy okrug", "Kirov Oblast": "Kirovskaya oblast'", "Komi": "Komi, Respublika", "Kostroma Oblast": "Kostromskaya oblast'", "Krasnodar Krai": "Krasnodyarskiy kray", "Krasnoyarsk Krai": "Krasnoyarskiy kray", "Kurgan Oblast": "Kurganskaya oblast'", "Kursk Oblast": "Kurskaya oblast'", "Leningrad Oblast": "Leningradskaya oblast'", "Lipetsk Oblast": "Lipetskaya oblast'", "Magadan Oblast": "Magadanskaya oblast'", "Mari El": "Mariy El, Respublika", "Mordovia": "Mordoviya, Respublika", "Moscow": "Moskva", "Moscow Oblast": "Moskovskaya oblast'", "Murmansk Oblast": "Murmanskaya oblast'", "Nenets Autonomous Okrug": "Nenetskiy avtonomnyy okrug", "Nizhny Novgorod Oblast": "Nizhegorodskaya oblast'", "North Ossetia–Alania": "Severnaya Osetiya-Alaniya, Respublika", "Novgorod Oblast": "Novgorodskaya oblast'", "Novosibirsk Oblast": "Novosibirskaya oblast'", "Omsk Oblast": "Omskaya oblast'", "Orenburg Oblast": "Orenburgskaya oblast'", "Oryol Oblast": "Orlovskaya oblast'", "Penza Oblast": "Penzenskaya oblast'", "Perm Krai": "Permskiy kray", "Primorsky Krai": "Primorskiy kray", "Pskov Oblast": "Pskovskaya oblast'", "Rostov Oblast": "Rostovskaya oblast'", "Ryazan Oblast": "Ryazanskaya oblast'", "Saint Petersburg": "Sankt-Peterburg", "Sakha (Yakutia)": "Sakha, Respublika", "Sakhalin Oblast": "Sakhalinskaya oblast'", "Samara Oblast": "Samarskaya oblast'", "Saratov Oblast": "Saratovskaya oblast'", "Smolensk Oblast": "Smolenskaya oblast'", "Stavropol Krai": "Stavropol'skiy kray", "Sverdlovsk Oblast": "Sverdlovskaya oblast'", "Tambov Oblast": "Tambovskaya oblast'", "Tatarstan": "Tatarstan, Respublika", "Tomsk Oblast": "Tomskaya oblast'", "Tula Oblast": "Tul'skaya oblast'", "Tuva": "Tyva, Respublika", "Tver Oblast": "Tverskaya oblast'", "Tyumen Oblast": "Tyumenskaya oblast'", "Udmurtia": "Udmurtskaya Respublika", "Ulyanovsk Oblast": "Ul'yanovskaya oblast'", "Vladimir Oblast": "Vladimirskaya oblast'", "Volgograd Oblast": "Volgogradskaya oblast'", "Vologda Oblast": "Vologodskaya oblast'", "Voronezh Oblast": "Voronezhskaya oblast'", "Yamalo-Nenets Autonomous Okrug": "Yamalo-Nenentskiy avtonomnyy okrug", "Yaroslavl Oblast": "Yaroslavskaya oblast'", "Jewish Autonomous Oblast": "Yeveryskaya avtonomnaya oblast'", "Zabaykalsky Krai": "Zabaykal'skiy kray", "Sevastopol": "Sevastopol"
    }}
}

# Microstates
MICROSTATES = {
    "Vatican City": (41.9029, 12.4534), "Monaco": (43.7384, 7.4167), "San Marino": (43.9424, 12.4578), "Liechtenstein": (47.1410, 9.5215),
    "Malta": (35.8989, 14.5146), "Andorra": (42.5063, 1.5218), "Luxembourg": (49.816667, 6.133333), "Singapore": (1.3521, 103.8198),
    "Bahrain": (26.0667, 50.5577), "Maldives": (3.2028, 73.2207), "Seychelles": (-4.6796, 55.4920), "Mauritius": (-20.3484, 57.5522),
    "Barbados": (13.1939, -59.5432), "Grenada": (12.1165, -61.6790), "Saint Lucia": (13.9094, -60.9789), "Dominica": (15.4150, -61.3710),
    "Saint Kitts and Nevis": (17.3578, -62.7830), "Saint Vincent and the Grenadines": (13.2528, -61.2872), "Antigua and Barbuda": (17.0608, -61.7965),
    "Tonga": (-21.1790, -175.2018), "Kiribati": (1.8709, -168.7340), "Palau": (7.5150, 134.5825), "Nauru": (-0.5228, 166.9315),
    "Tuvalu": (-7.1095, 179.1942), "Marshall Islands": (7.1315, 171.1845), "Micronesia": (6.9248, 158.1625), "Samoa": (-13.7590, -172.1046),
    "Comoros": (-11.699, 43.3333), "Sao Tome and Principe": (0.1864, 6.6131), "Cape Verde": (16.5388, -24.0130),
    "British Virgin Islands": (18.4207, -64.6399), "Anguilla": (18.2206, -63.0686), "Bermuda": (32.3078, -64.7505),
    "Cayman Islands": (19.3133, -81.2546), "Turks and Caicos Islands": (21.6940, -71.7979), "Montserrat": (16.7425, -62.1874),
    "Gibraltar": (36.1408, -5.3536), "Saint Helena": (-15.9650, -5.7089), "Isle of Man": (54.2361, -4.5481),
    "Jersey": (49.2144, -2.1358), "Guernsey": (49.4657, -2.5857), "American Samoa": (-14.2710, -170.1322),
    "Guam": (13.4443, 144.7937), "Northern Mariana Islands": (15.0979, 145.6739), "US Virgin Islands": (18.3358, -64.8963),
    "Saint Pierre and Miquelon": (46.8852, -56.2711), "Wallis and Futuna": (-13.7687, -176.1761), "Saint Martin": (18.0708, -63.0501),
    "Saint Barthelemy": (17.9000, -62.8334), "French Polynesia": (-17.6797, -149.4068), "Mayotte": (-12.8275, 45.1662),
    "Reunion": (-21.1151, 55.5364), "Réunion": (-21.1151, 55.5364), "Martinique": (14.6415, -61.0242), "Guadeloupe": (16.2650, -61.5510),
    "Aruba": (12.5211, -69.9683), "Curacao": (12.1696, -68.9335), "Sint Maarten": (18.0425, -63.0548), "Bonaire": (12.2019, -68.2624),
    "Saba": (17.6353, -63.2324), "Sint Eustatius": (17.4890, -62.9738), "Cook Islands": (-21.2367, -159.7777),
    "Niue": (-19.0544, -169.8672), "Tokelau": (-9.2002, -171.8554), "Cocos Islands": (-12.186944, 96.828333),
    "Christmas Island": (-10.49, 105.6275), "Hong Kong": (22.3964, 114.1095), "Macao": (22.1987, 113.5439),
    "Faroe Islands": (61.8926, -6.9118), "Trinidad and Tobago": (10.6918, -61.2225), "Norfolk Island": (-29.033333, 167.95),
    "Easter Island": (-27.12, -109.35), "Aland": (60.25, 20.366667), "Puerto Rico": (18.2208, -66.5901),
    "New Caledonia": (-20.9043, 165.6180), "Falkland Islands": (-51.7963, -59.5236)
}

cc = coco.CountryConverter()

# --- CSS & Styles ---
try:
    with open("styles.css") as f: st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError: pass

st.markdown("""
<style>
    .stRadio [role=radiogroup] { align-items: start; justify-content: start; }
    div[data-testid="stMetric"] { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
    .main .block-container { max-width: 98%; padding-left: 1rem; padding-right: 1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("## Locations")

# --- Data Loading (Cached & Optimized) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("./Data/Timeguessr_Stats.csv")
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        # Pre-calculate ISO, Continent, Region ONCE
        unique_c = df["Country"].dropna().unique()
        iso_map = dict(zip(unique_c, cc.convert(names=unique_c, to='ISO3', not_found=None)))
        cont_map = dict(zip(unique_c, cc.convert(names=unique_c, to="continent")))
        reg_map = dict(zip(unique_c, cc.convert(names=unique_c, to="UNregion")))
        
        # Palestine fix
        for k in unique_c:
            if "Palestine" in str(k): cont_map[k], reg_map[k] = "Asia", "Western Asia"

        df["ISO3"] = df["Country"].map(iso_map)
        df["Continent"] = df["Country"].map(cont_map)
        df["UN_Region"] = df["Country"].map(reg_map)
        return df
    except FileNotFoundError:
        st.error("Stats file not found."); st.stop()

@st.cache_data
def load_map():
    target_file = "./Data/Custom_World_Map_New.json"
    if not os.path.exists(target_file): return None, set()
    try:
        gdf = gpd.read_file(target_file)
        gdf['geometry'] = gdf['geometry'].buffer(0) # Fix Topology Errors
        
        # Standardize
        iso_col = next((c for c in ['ISO3', 'iso3', 'adm0_a3'] if c in gdf.columns), None)
        if iso_col:
            gdf['ISO3'] = cc.convert(names=gdf[iso_col].tolist(), to='ISO3', not_found='UNK')
        else: gdf['ISO3'] = 'UNK'
        
        name_col = next((c for c in ['NAME', 'name', 'NAME_1', 'COUNTRY'] if c in gdf.columns), 'NAME')
        gdf['NAME'] = gdf[name_col].astype(str).str.strip()
        
        # Enrich Map Data
        clean_isos = [x for x in gdf['ISO3'].unique() if x != 'UNK']
        gdf['Continent'] = gdf['ISO3'].map(dict(zip(clean_isos, cc.convert(names=clean_isos, to="continent")))).fillna("Unknown")
        gdf['UN_Region'] = gdf['ISO3'].map(dict(zip(clean_isos, cc.convert(names=clean_isos, to="UNregion")))).fillna("Unknown")
        
        return gdf, set(gdf['NAME'].unique())
    except Exception as e:
        st.error(f"Map error: {e}"); return None, set()

data = load_data()
base_gdf, valid_map_names = load_map()

# --- Geometry Functions ---

@st.cache_data
def get_background_layer(_gdf):
    """Restored: Creates a single unified shape for the whole world."""
    if _gdf is None: return None
    _gdf['World_Group'] = 1
    bg_gdf = _gdf.dissolve(by='World_Group', as_index=False)
    return json.loads(bg_gdf.to_json())

@st.cache_data
def generate_dynamic_map_layer(_gdf, active_iso_tuple, active_splits, active_subdivs, view_mode):
    """
    Generates map geometry only for active locations.
    Only colors in parts of split countries for which there are subdivisions.
    """
    if _gdf is None: return None
    
    work_gdf = _gdf[_gdf['ISO3'].isin(active_iso_tuple)].copy()
    
    if work_gdf.empty: return None

    # Filter subdivisions for split countries
    # We want to keep:
    # 1. Rows where ISO is NOT in active_splits (normal countries)
    # 2. Rows where ISO IS in active_splits AND NAME is in the active_subdivs set for that ISO
    
    def filter_subdivs(row):
        iso = row['ISO3']
        if iso not in active_splits:
            return True
        # It is a split country, check name
        allowed = active_subdivs.get(iso, set())
        return row['NAME'] in allowed

    # Apply the filter logic
    if active_splits:
        work_gdf = work_gdf[work_gdf.apply(filter_subdivs, axis=1)]

    if work_gdf.empty: return None

    def get_dissolve_key(row):
        iso = row['ISO3']
        name = row['NAME']
        
        # Check if this specific ISO is being split
        if iso in active_splits:
             return name if view_mode == "Countries" else iso

        # Base Identity
        if view_mode == "Continents":
            return row['Continent']
        elif view_mode == "UN Regions":
            return row['UN_Region']
        else: 
            return iso

    work_gdf['Dissolve_Key'] = work_gdf.apply(get_dissolve_key, axis=1)
    return json.loads(work_gdf.dissolve(by='Dissolve_Key', as_index=False).to_json())

# --- Stats Calculation ---

def calculate_stats(df, active_splits, view_mode, metric, score_mode):
    df_work = df.copy()
    
    # 1. Determine Join Key
    def get_key(row):
        iso = row['ISO3']
        sub = row.get('Subdivision')
        if iso in active_splits and pd.notna(sub):
            return sub
        return iso
        
    df_work['Join_Key'] = df_work.apply(get_key, axis=1)

    # 2. Handle View Mode Aggregation Mapping (Region/Continent)
    if view_mode != "Countries":
        def get_agg_key(row):
            iso = row['ISO3']
            if iso in active_splits: return iso # Split countries stay as countries in region view
            
            if view_mode == "Continents": return row['Continent']
            if view_mode == "UN Regions": return row['UN_Region']
            return iso
        
        df_work['Join_Key'] = df_work.apply(get_agg_key, axis=1)

    # 3. Check Participation using Round Score Columns
    if 'Michael Round Score' in df_work.columns:
        m_played = df_work['Michael Round Score'].notna()
    else:
        m_played = df_work['Michael Geography Score'].notna() 

    if 'Sarah Round Score' in df_work.columns:
        s_played = df_work['Sarah Round Score'].notna()
    else:
        s_played = df_work['Sarah Geography Score'].notna()

    # 4. Filter Data based on Metric (Pre-aggregation)
    if metric == "Comparison":
        df_work = df_work[m_played & s_played]
        m_played = m_played[df_work.index]
        s_played = s_played[df_work.index]
    elif metric == "Michael": 
        df_work = df_work[m_played]
        m_played = m_played[df_work.index]
        s_played = s_played[df_work.index]
    elif metric == "Sarah": 
        df_work = df_work[s_played]
        m_played = m_played[df_work.index]
        s_played = s_played[df_work.index]

    # 5. Calculate Scores (Create Columns)
    max_p = 10000 if score_mode == "Total Score" else 5000
    
    df_work['Michael Selected'] = 0
    df_work['Sarah Selected'] = 0
    df_work['Michael Win'] = 0
    df_work['Sarah Win'] = 0

    if score_mode == "Total Score":
        df_work['Michael Selected'] = df_work["Michael Geography Score"].fillna(0) + df_work["Michael Time Score"].fillna(0)
        df_work['Sarah Selected'] = df_work["Sarah Geography Score"].fillna(0) + df_work["Sarah Time Score"].fillna(0)
    elif score_mode == "Geography Score":
        df_work['Michael Selected'] = df_work["Michael Geography Score"].fillna(0)
        df_work['Sarah Selected'] = df_work["Sarah Geography Score"].fillna(0)
    else: # Time
        df_work['Michael Selected'] = df_work["Michael Time Score"].fillna(0)
        df_work['Sarah Selected'] = df_work["Sarah Time Score"].fillna(0)

    # Zero out scores if they didn't "play"
    df_work.loc[~m_played, 'Michael Selected'] = 0
    df_work.loc[~s_played, 'Sarah Selected'] = 0

    # Win Logic
    df_work['Michael Win'] = ((df_work['Michael Selected'] > df_work['Sarah Selected']) & m_played & s_played).astype(int)
    df_work['Sarah Win'] = ((df_work['Sarah Selected'] > df_work['Michael Selected']) & m_played & s_played).astype(int)

    # 6. Row-Level Exclusivity Calculation
    df_work['Row_Michael_Only'] = (m_played & ~s_played).astype(int)
    df_work['Row_Sarah_Only'] = (s_played & ~m_played).astype(int)
    df_work['Row_Shared'] = (m_played & s_played).astype(int)

    # 7. Aggregate
    agg_cols = {
        'Row_Shared': 'sum', 
        'Michael Selected': 'sum', 
        'Sarah Selected': 'sum',
        'Michael Win': 'sum',
        'Sarah Win': 'sum',
        'Row_Michael_Only': 'sum',
        'Row_Sarah_Only': 'sum'
    }
    
    grouped = df_work.groupby('Join_Key').agg(agg_cols).rename(columns={
        "Row_Shared": "Shared_Count",
        "Row_Michael_Only": "Michael_Only_Count",
        "Row_Sarah_Only": "Sarah_Only_Count"
    }).reset_index()

    # 8. Post-Aggregation Calcs
    
    # Calculate Total Active Games (valid games)
    grouped['Total_Active'] = grouped['Shared_Count'] + grouped['Michael_Only_Count'] + grouped['Sarah_Only_Count']
    
    # IMPORTANT: "Count" metric uses Shared_Count only, per user request.
    if metric == "Count":
        grouped['Count'] = grouped['Shared_Count']
    else:
        grouped['Count'] = grouped['Total_Active'] 

    grouped['Total Possible'] = grouped['Total_Active'] * max_p
    grouped['Michael Efficiency'] = grouped['Michael Selected'] / grouped['Total Possible']
    grouped['Sarah Efficiency'] = grouped['Sarah Selected'] / grouped['Total Possible']
    grouped['Combined'] = grouped['Michael Selected'] + grouped['Sarah Selected']
    grouped['Michael Share Ratio'] = grouped.apply(lambda x: x['Michael Selected'] / x['Combined'] if x['Combined'] > 0 else 0.5, axis=1)

    # 9. Hover Names
    grouped['Hover_Name'] = grouped['Join_Key'].apply(lambda x: SPLIT_CONFIG.get(x, {}).get('name', str(x)))
    mask_iso = (grouped['Join_Key'].str.len() == 3) & (grouped['Join_Key'].str.isupper())
    if mask_iso.any():
        iso_to_name = dict(zip(grouped.loc[mask_iso, 'Join_Key'], cc.convert(names=grouped.loc[mask_iso, 'Join_Key'], to='name_short')))
        grouped.loc[mask_iso, 'Hover_Name'] = grouped.loc[mask_iso, 'Join_Key'].map(iso_to_name)

    # 10. Recent Location Logic
    if 'Date' in df_work.columns:
        latest = df_work.sort_values('Date', ascending=False).drop_duplicates('Join_Key')
        grouped = grouped.merge(latest[['Join_Key', 'Date', 'City', 'Subdivision', 'Country']], on='Join_Key', how='left')
        grouped['Last_Date'] = grouped['Date']
        
        def fmt_loc(r):
            parts = [str(x).strip() for x in [r['City'], r['Subdivision'], r['Country']] if pd.notna(x) and str(x).strip()]
            return ", ".join(dict.fromkeys(parts)) 
        grouped['Most Recent Location'] = grouped.apply(fmt_loc, axis=1)
    
    return grouped

def create_styled_table(df):
    header_style = "background-color: #d9d7cc; border-bottom: 2px solid #8f8d85; padding: 10px; text-align: left; color: #696761; font-weight: 600;"
    header_center = "background-color: #d9d7cc; border-bottom: 2px solid #8f8d85; padding: 10px; text-align: center; color: #696761; font-weight: 600;"
    
    row_style = "border-bottom: 1px solid #d9d7cc;"
    cell_style = "padding: 8px; color: #696761;"
    cell_center = "padding: 8px; text-align: center; color: #696761;"
    
    html = '<table style="width:100%; border-collapse: collapse; font-family: Poppins, Arial, sans-serif; font-size: 13px;">'
    
    # Header
    html += "<thead><tr>"
    for col in df.columns:
        s = header_style if col == "Location" else header_center
        html += f"<th style='{s}'>{col}</th>"
    html += "</tr></thead><tbody>"
    
    # Rows
    for _, row in df.iterrows():
        html += f"<tr style='{row_style}'>"
        for col in df.columns:
            val = row[col]
            style = cell_style if col == "Location" else cell_center
            content = str(val)
            
            # Custom Formatting
            if col == "Count":
                content = f"{int(val):,}"
            elif "Ratio" in col or "Efficiency" in col:
                if pd.isna(val):
                    content = "-"
                else:
                    content = f"{val:.1%}"
                    # Color logic
                    if "Michael" in col:
                        style = style.replace("#696761", COLORS['michael'])
                    elif "Sarah" in col:
                        style = style.replace("#696761", COLORS['sarah'])
                    elif "Win Ratio" in col:
                        if val > 0.5:
                            style = style.replace("#696761", COLORS['michael']) + " font-weight: bold;"
                        elif val < 0.5:
                            style = style.replace("#696761", COLORS['sarah']) + " font-weight: bold;"
            
            html += f"<td style='{style}'>{content}</td>"
        html += "</tr>"
    
    html += "</tbody></table>"
    return html

# --- Sidebar ---
with st.sidebar:
    st.header("Map Settings")
    if "Date" in data.columns:
        min_d, max_d = data["Date"].min().date(), data["Date"].max().date()
        sel_dates = st.slider("Select Date Range:", min_d, max_d, (min_d, max_d), format="MM/DD/YY")
        filtered_data = data[(data["Date"].dt.date >= sel_dates[0]) & (data["Date"].dt.date <= sel_dates[1])].copy()
    else: filtered_data = data.copy()

    map_metric = st.radio("Metric:", ["Count", "Comparison", "Michael", "Sarah"])
    score_mode = st.radio("Score Type:", ["Total Score", "Geography Score", "Time Score"]) if map_metric != "Count" else "Total Score"
    view_mode = st.radio("View Level:", ["Countries", "UN Regions", "Continents"])
    
    # Split Logic
    avail_splits = [cfg['name'] for cfg in SPLIT_CONFIG.values()]
    sel_splits = st.multiselect("Split Countries:", avail_splits, default=[])
    
    active_splits = set()
    for iso, cfg in SPLIT_CONFIG.items():
        if cfg['name'] in sel_splits:
            active_splits.add(iso)
            # Apply Cleanups
            mask = filtered_data['ISO3'] == iso
            if mask.any() and cfg['map']:
                filtered_data.loc[mask, 'Subdivision'] = filtered_data.loc[mask, 'Subdivision'].replace(cfg['map'])
                if valid_map_names:
                    bad = filtered_data[mask & ~filtered_data['Subdivision'].isin(valid_map_names)]
                    if not bad.empty: st.error(f"Unknown subdivision in {cfg['name']}: {bad['Subdivision'].unique()}")

    # Main Calculation
    stats = calculate_stats(filtered_data, active_splits, view_mode, map_metric, score_mode)
    
    # Filter based on Total_Active (Active Games), allowing "Count" (Shared) to be 0 for exclusive rows.
    # Set min slider value to 0.
    max_games = int(stats['Total_Active'].max()) if not stats.empty else 0
    min_count = st.slider("Min Games:", 0, max_games, 0)
    
    stats = stats[stats['Total_Active'] >= min_count]
    
    # HARD CONSTRAINT: Remove completely empty rows (0 count, 0 michael only, 0 sarah only)
    stats = stats[stats['Total_Active'] > 0]

# --- Map Generation ---

if not filtered_data.empty:
    filtered_data['Join_Key'] = filtered_data['ISO3'] 
    
    if active_splits:
         if view_mode == "Countries":
            mask_split = filtered_data['ISO3'].isin(active_splits) & filtered_data['Subdivision'].notna()
            filtered_data.loc[mask_split, 'Join_Key'] = filtered_data.loc[mask_split, 'Subdivision']
    
    if view_mode != "Countries":
        mask_not_split = ~filtered_data['ISO3'].isin(active_splits)
        if view_mode == "Continents":
            filtered_data.loc[mask_not_split, 'Join_Key'] = filtered_data.loc[mask_not_split, 'Continent']
        elif view_mode == "UN Regions":
            filtered_data.loc[mask_not_split, 'Join_Key'] = filtered_data.loc[mask_not_split, 'UN_Region']

active_keys = set(stats['Join_Key'].unique())
active_iso_tuple = tuple(filtered_data[filtered_data['Join_Key'].isin(active_keys)]['ISO3'].unique()) if not stats.empty else ()

# Calculate Active Subdivs for Split Countries
active_subdivs = {}
if active_splits:
    for iso in active_splits:
        # Get unique subdivisions present in data for this ISO
        subs = filtered_data[(filtered_data['ISO3'] == iso) & filtered_data['Subdivision'].notna()]['Subdivision'].astype(str).str.strip().unique()
        active_subdivs[iso] = set(subs)

map_geojson = generate_dynamic_map_layer(base_gdf, active_iso_tuple, active_splits, active_subdivs, view_mode)
bg_geojson = get_background_layer(base_gdf)

fig = go.Figure()

if bg_geojson:
    fig.add_trace(go.Choropleth(
        geojson=bg_geojson, locations=[1], z=[1], featureidkey="properties.World_Group",
        colorscale=[[0, "#eeeeee"], [1, "#eeeeee"]], showscale=False,
        marker_line_color="white", marker_line_width=0.1, hoverinfo='skip'
    ))

if map_geojson and not stats.empty:
    # Scales
    max_val = stats['Count'].max() if map_metric != "Comparison" else 0.6
    if max_val == 0: max_val = 1
    
    scales = {
        "Count": ([[0, "#fee6e6"], [1, "#db5049"]], 0, max_val),
        "Comparison": ([[0, "#8a005c"], [0.5, "#f2f2f2"], [1, "#221e8f"]], 0.4, 0.6),
        "Michael": ([[0, "#e6e6ff"], [1, "#221e8f"]], 0.5, 1.0),
        "Sarah": ([[0, "#ffe6f2"], [1, "#8a005c"]], 0.5, 1.0)
    }
    scale, zmin, zmax = scales.get(map_metric, scales["Count"])
    z_col = "Michael Share Ratio" if map_metric == "Comparison" else (f"{map_metric} Efficiency" if map_metric in ["Michael", "Sarah"] else "Count")
    
    # Split for COUNT metric: Shared vs Pure Exclusive
    stats_shared = stats.copy()
    stats_exclusive = pd.DataFrame()
    
    stats['BorderColor'] = "black"
    stats['BorderWidth'] = 0.5
    
    if map_metric == "Count":
        # Pure Exclusive: Count is 0 (because we updated Count to be Shared_Count)
        mask_excl = stats['Count'] == 0
        stats_exclusive = stats[mask_excl].copy()
        
        # Shared: Count > 0
        stats_shared = stats[~mask_excl].copy()
        
        stats_exclusive['BorderColor'] = "#221e8f" # Blue border for exclusive
        
    elif map_metric == "Comparison":
        stats['BorderColor'] = np.where(stats[z_col] > 0.5, "#221e8f", np.where(stats[z_col] < 0.5, "#8a005c", "#666666"))
        stats_shared = stats 
    else:
        stats_shared = stats 

    # Hover
    stats_shared['Score_Str'] = stats_shared.apply(lambda r: f"{int(r['Michael Selected'])}/{int(r['Total Possible'])}" if map_metric=="Michael" else (f"{int(r['Sarah Selected'])}/{int(r['Total Possible'])}" if map_metric=="Sarah" else ""), axis=1)
    if not stats_exclusive.empty: stats_exclusive['Score_Str'] = ""

    hover_base = "<b>%{text}</b><br>"
    if map_metric == "Count":
        hover_t = hover_base + "Count: %{customdata[2]}<br>Michael Only: %{customdata[0]}<br>Sarah Only: %{customdata[1]}"
        custom_cols = ['Michael_Only_Count', 'Sarah_Only_Count', 'Count']
    elif map_metric == "Comparison": 
        hover_t = hover_base + "Share: %{customdata[0]:.1%}"
        custom_cols = [z_col]
    else: 
        hover_t = hover_base + "Eff: %{z:.1%}<br>Score: %{customdata[0]}"
        custom_cols = ['Score_Str']

    # Trace 1: Shared (Colored)
    if not stats_shared.empty:
        fig.add_trace(go.Choropleth(
            geojson=map_geojson, locations=stats_shared['Join_Key'], z=stats_shared[z_col],
            featureidkey="properties.Dissolve_Key", colorscale=scale, zmin=zmin, zmax=zmax,
            marker_line_color=stats_shared['BorderColor'], marker_line_width=stats_shared['BorderWidth'],
            text=stats_shared['Hover_Name'], customdata=stats_shared[custom_cols],
            hovertemplate=hover_t, showscale=False
        ))

    # Trace 2: Pure Exclusive (Transparent Fill)
    if not stats_exclusive.empty and map_metric == "Count":
        fig.add_trace(go.Choropleth(
            geojson=map_geojson, locations=stats_exclusive['Join_Key'],
            featureidkey="properties.Dissolve_Key", 
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']], 
            marker_line_color=stats_exclusive['BorderColor'], marker_line_width=stats_exclusive['BorderWidth'],
            text=stats_exclusive['Hover_Name'], customdata=stats_exclusive[custom_cols],
            hovertemplate=hover_t, showscale=False,
            z=[1]*len(stats_exclusive) # Dummy z for plotting
        ))

    # Microstates
    ms_df = stats[stats['Hover_Name'].isin(MICROSTATES)].copy()
    if not ms_df.empty:
        coords = ms_df['Hover_Name'].map(MICROSTATES)
        ms_custom = ms_df[custom_cols]
        fig.add_trace(go.Scattergeo(
            lat=[x[0] for x in coords], lon=[x[1] for x in coords], mode='markers',
            marker=dict(size=8, color=ms_df[z_col], colorscale=scale, cmin=zmin, cmax=zmax, 
                        line=dict(width=1, color=ms_df['BorderColor'])),
            text=ms_df['Hover_Name'], customdata=ms_custom, hovertemplate=hover_t
        ))

fig.update_layout(
    geo=dict(showframe=False, showcoastlines=False, projection_type="robinson", 
             bgcolor='rgba(0,0,0,0)', showocean=True, oceancolor="white", showlakes=True, lakecolor="white"),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(t=0, b=0, l=0, r=0), 
    height=850
)
st.plotly_chart(fig, use_container_width=True)

# --- Table ---
st.divider()
st.subheader(f"Statistics by {view_mode}")

if not stats.empty:
    disp = stats.sort_values("Count", ascending=False).copy()
    cols = ['Hover_Name', 'Count', 'Most Recent Location']
    if map_metric == "Comparison":
        if 'Michael Win' in disp.columns and 'Sarah Win' in disp.columns:
            disp['Total Wins'] = disp['Michael Win'] + disp['Sarah Win']
            disp['Win Ratio'] = disp.apply(lambda x: x['Michael Win'] / x['Total Wins'] if x['Total Wins'] > 0 else 0.5, axis=1)
        else: disp['Win Ratio'] = 0.5     
        cols += ['Michael Share Ratio', 'Win Ratio']
    elif map_metric in ["Michael", "Sarah"]:
        cols += [f'{map_metric} Efficiency']
        
    final_df = disp[cols].rename(columns={'Hover_Name': 'Location'})
    
    # Sorting Controls
    sort_c1, sort_c2 = st.columns([3, 1])
    with sort_c1:
        sort_col = st.selectbox("Sort By", options=final_df.columns, index=1 if "Count" in final_df.columns else 0)
    with sort_c2:
        # Using a selectbox for order to match visual height of sort_by box better than radio
        sort_dir = st.selectbox("Order", options=["Descending", "Ascending"], index=0)
    
    ascending = sort_dir == "Ascending"
    final_df = final_df.sort_values(by=sort_col, ascending=ascending)
    
    st.markdown(create_styled_table(final_df), unsafe_allow_html=True)