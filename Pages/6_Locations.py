import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import country_converter as coco
import numpy as np
import json
import os
import geopandas as gpd
from shapely.geometry import shape as shp_shape
import math
from shapely.ops import unary_union
import base64
import io
from PIL import Image

# --- Configuration & Constants ---
st.set_page_config(layout="wide", page_title="Map Stats")

@st.cache_data
def get_base64_image(image_path):
    """Encodes an image to a Base64 string."""
    try:
        img = Image.open(image_path)
        file_format = img.format if img.format is not None else 'PNG'
        buffer = io.BytesIO()
        img.save(buffer, format=file_format)
        return base64.b64encode(buffer.getvalue()).decode()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"An error occurred during image processing: {e}")
        return None

def set_lighter_background_image(base64_string, lightness_level=0.7):
    """Injects CSS to set the background image with a semi-transparent white overlay."""
    if not base64_string:
        return
    rgba_overlay = f"rgba(255, 255, 255, {lightness_level})"
    css = f"""
    <style>
    .stApp {{
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

# Set the background image
base64_img = get_base64_image("Images/Sarah4.jpg")
set_lighter_background_image(base64_img, lightness_level=0.7)

COLORS = {'michael': '#221e8f', 'sarah': '#8a005c', 'neutral': '#696761'}

LANGUAGE_EMOJIS = {
    'English':           '🇬🇧',
    'Spanish':           '🇪🇸',
    'French':            '🇫🇷',
    'Portuguese':        '🇵🇹',
    'Germanic':          '🇩🇪',
    'Other Romance':     '🇮🇹',
    'Slavic (Latin)':    '🇵🇱',
    'Slavic (Cyrillic)': '🇷🇺',
    'Slavic (Mixed)':    '🇧🇦',
    'East Asian Scripts':'🇨🇳',
    'Arabic Script':     '🇸🇦',
    'Brahmic Script':    '🇮🇳',
    'Hebrew Script':     '🇮🇱',
    'Greek Script':      '🇬🇷',
    'Georgian Script':   '🇬🇪',
    'Armenian Script':   '🇦🇲',
    'Turkic':            '🇹🇷',
    'Other European':    '🇫🇮',
    'Asian Latin Script':'🇮🇩',
}

# ISO3 to Primary Language/Script Mapping
ISO_LANGUAGE_MAP = {
    # English
    'USA': 'English', 'GBR': 'English', 'AUS': 'English', 'CAN': 'English', 'NZL': 'English', 
    'IRL': 'English', 'JAM': 'English', 'BHS': 'English', 
    'BRB': 'English', 'GUY': 'English', 'TTO': 'English', 'ATG': 'English', 'DMA': 'English', 
    'GRD': 'English', 'KNA': 'English', 'LCA': 'English', 'VCT': 'English', 'BLZ': 'English',
    'NGA': 'English', 'GHA': 'English', 'SLE': 'English', 'LBR': 'English', 'GMB': 'English', 
    'UGA': 'English', 'ZMB': 'English', 'ZWE': 'English', 'BWA': 'English', 'NAM': 'English',
    
    # Spanish
    'ESP': 'Spanish', 'MEX': 'Spanish', 'COL': 'Spanish', 'ARG': 'Spanish', 'PER': 'Spanish', 
    'VEN': 'Spanish', 'CHL': 'Spanish', 'ECU': 'Spanish', 'GTM': 'Spanish', 'CUB': 'Spanish', 
    'BOL': 'Spanish', 'DOM': 'Spanish', 'HND': 'Spanish', 'PRY': 'Spanish', 'SLV': 'Spanish', 
    'NIC': 'Spanish', 'CRI': 'Spanish', 'PAN': 'Spanish', 'URY': 'Spanish', 'GNQ': 'Spanish',
    'PRI': 'Spanish', # Puerto Rico
    
    # Portuguese
    'BRA': 'Portuguese', 'PRT': 'Portuguese', 'MOZ': 'Portuguese', 'AGO': 'Portuguese', 
    'GNB': 'Portuguese', 'TLS': 'Portuguese', 'CPV': 'Portuguese', 'STP': 'Portuguese',
    
    # French
    'FRA': 'French', 'COD': 'French', 'MAD': 'French', 'CIV': 'French', 
    'BFA': 'French', 'NER': 'French', 'SEN': 'French', 'MLI': 'French', 'RWA': 'French', 
    'GIN': 'French', 'TCD': 'French', 'HTI': 'French', 'MDG': 'French', 
    'BEN': 'French', 'TGO': 'French', 'CAF': 'French', 'COG': 'French', 'GAB': 'French', 
    'DJI': 'French', 'MCO': 'French', 'VUT': 'French', 'SYC': 'French', 'BDI': 'French',
    
    # Other Romance
    'ITA': 'Other Romance', 'SMR': 'Other Romance', 'VAT': 'Other Romance', 
    'AND': 'Other Romance', 'ROU': 'Other Romance', 'MDA': 'Other Romance',

    # Germanic (Excluding English)
    'DEU': 'Germanic', 'AUT': 'Germanic', 'LIE': 'Germanic', # German
    'NLD': 'Germanic', 'SUR': 'Germanic', # Dutch
    'SWE': 'Germanic', 'NOR': 'Germanic', 'DNK': 'Germanic', 'ISL': 'Germanic', # Nordic
    'LUX': 'Germanic',
    
    # Other European (Unique/Isolates/Uralic/Baltic)
    'ALB': 'Other European', # Albanian
    'HUN': 'Other European', # Hungarian
    'MLT': 'Other European', # Maltese
    'FIN': 'Other European', 'EST': 'Other European', # Finnic
    'LVA': 'Other European', 'LTU': 'Other European', # Baltic

    # Turkic
    'TUR': 'Turkic', 'AZE': 'Turkic', 'KAZ': 'Turkic',

    # Slavic (Latin Script)
    'POL': 'Slavic (Latin)', 'CZE': 'Slavic (Latin)', 'SVK': 'Slavic (Latin)',
    'SVN': 'Slavic (Latin)', 'HRV': 'Slavic (Latin)',
    'BIH': 'Slavic (Latin)', 'SRB': 'Slavic (Latin)', 'MNE': 'Slavic (Latin)',
    'MKD': 'Slavic (Latin)', 
    
    # Slavic (Cyrillic Script)
    'RUS': 'Slavic (Cyrillic)', 'BLR': 'Slavic (Cyrillic)', 'UKR': 'Slavic (Cyrillic)', 
    'BGR': 'Slavic (Cyrillic)', 'MKD': 'Slavic (Cyrillic)', 
    
    # East Asian Scripts
    'CHN': 'East Asian Scripts', 'TWN': 'East Asian Scripts', 
    'JPN': 'East Asian Scripts', 'KOR': 'East Asian Scripts', 'PRK': 'East Asian Scripts',

    # Asian Latin Script
    'VNM': 'Asian Latin Script', 'IDN': 'Asian Latin Script', 'PHL': 'Asian Latin Script',
    'MYS': 'Asian Latin Script', 'BRN': 'Asian Latin Script',

    # Brahmic Script (Indic family)
    'IND': 'Brahmic Script', 'BGD': 'Brahmic Script', 'NPL': 'Brahmic Script',
    'LKA': 'Brahmic Script', 'BTN': 'Brahmic Script', 'THA': 'Brahmic Script',
    'LAO': 'Brahmic Script', 'KHM': 'Brahmic Script', 'MMR': 'Brahmic Script',
    
    # Arabic Script
    'EGY': 'Arabic Script', 'DZA': 'Arabic Script', 'SDN': 'Arabic Script', 'IRQ': 'Arabic Script', 
    'MAR': 'Arabic Script', 'SAU': 'Arabic Script', 'YEM': 'Arabic Script', 'SYR': 'Arabic Script', 
    'TUN': 'Arabic Script', 'SOM': 'Arabic Script', 'JOR': 'Arabic Script', 'LBY': 'Arabic Script', 
    'PSE': 'Arabic Script', 'LBN': 'Arabic Script', 'OMN': 'Arabic Script', 'KWT': 'Arabic Script', 
    'MRT': 'Arabic Script', 'QAT': 'Arabic Script', 'BHR': 'Arabic Script', 'ARE': 'Arabic Script',
    'IRN': 'Arabic Script', 'AFG': 'Arabic Script', 'PAK': 'Arabic Script',

    # Greek Script
    'GRC': 'Greek Script', 

    # Hebrew Script
    'ISR': 'Hebrew Script',

    # Georgian Script
    'GEO': 'Georgian Script',

    # Armenian Script
    'ARM': 'Armenian Script',

    # --- Overseas Territories & Dependencies ---
    # UK
    'GIB': 'English', 'BMU': 'English', 'CYM': 'English', 'VGB': 'English', 'TCA': 'English', 'AIA': 'English', 'MSR': 'English', 'FLK': 'English', 'SHN': 'English', 'IOT': 'English', 'SGS': 'English', 'PCN': 'English', 'IMN': 'English', 'JEY': 'English', 'GGY': 'English',
    # USA
    'GUM': 'English', 'VIR': 'English', 'ASM': 'English', 'MNP': 'English',
    # France
    'GLP': 'French', 'MTQ': 'French', 'GUF': 'French', 'REU': 'French', 'MYT': 'French', 'PYF': 'French', 'NCL': 'French', 'MAF': 'French', 'BLM': 'French', 'SPM': 'French', 'WLF': 'French',
    # Netherlands
    'ABW': 'Germanic', 'CUW': 'Germanic', 'SXM': 'Germanic', 'BES': 'Germanic',
    # Denmark
    'GRL': 'Germanic', 'FRO': 'Germanic',
    # Australia
    'CXR': 'English', 'CCK': 'English', 'NFK': 'English',
    # Norway
    'SJM': 'Germanic',
    # China
    'HKG': 'East Asian Scripts', 'MAC': 'East Asian Scripts',
    # New Zealand
    'COK': 'English', 'NIU': 'English', 'TKL': 'English'
}

# --- Universal Territory to Parent Map ---
TERRITORY_PARENT_MAP = {
    # United Kingdom
    'JEY': 'GBR', 'GGY': 'GBR', 'IMN': 'GBR', 'GIB': 'GBR', 'AIA': 'GBR', 'BMU': 'GBR',
    'CYM': 'GBR', 'FLK': 'GBR', 'IOT': 'GBR', 'MSR': 'GBR', 'PCN': 'GBR', 'SGS': 'GBR',
    'SHN': 'GBR', 'TCA': 'GBR', 'VGB': 'GBR',
    # France
    'GLP': 'FRA', 'MTQ': 'FRA', 'GUF': 'FRA', 'REU': 'FRA', 'MYT': 'FRA', 'PYF': 'FRA',
    'NCL': 'FRA', 'MAF': 'FRA', 'BLM': 'FRA', 'SPM': 'FRA', 'WLF': 'FRA',
    # United States
    'PRI': 'USA', 'GUM': 'USA', 'VIR': 'USA', 'ASM': 'USA', 'MNP': 'USA',
    # Netherlands
    'ABW': 'NLD', 'CUW': 'NLD', 'SXM': 'NLD', 'BES': 'NLD',
    # Denmark
    'GRL': 'DNK', 'FRO': 'DNK',
    # Australia
    'CXR': 'AUS', 'CCK': 'AUS', 'NFK': 'AUS',
    # Norway
    'SJM': 'NOR',
    # China
    'HKG': 'CHN', 'MAC': 'CHN',
    # New Zealand
    'COK': 'NZL', 'NIU': 'NZL', 'TKL': 'NZL',
}

# Split Configuration
SPLIT_CONFIG = {
    "AUS": {"name": "Australia", "map": {}},
    "CAN": {"name": "Canada", "map": {"Québec": "Quebec", "Newfoundland": "Newfoundland and Labrador"}},
    "CHN": {"name": "China", "map": {"Beijing": "Beijing Shi", "Shanghai": "Shanghai Shi", "Tianjin": "Tianjin Shi", "Chongqing": "Chongqing Shi", "Inner Mongolia": "Nei Mongol Zizhiqu", "Guangxi": "Guangxi Zhuangzu Zizhiqu", "Tibet": "Xizang Zizhiqu", "Ningxia": "Ningxia Zizhiiqu", "Xinjiang": "Xinjiang Uygur Zizhiqu", "Hong Kong": "Hong Kong", "Macau": "Macao", "Anhui": "Anhui Sheng", "Fujian": "Fujian Sheng", "Gansu": "Gansu Sheng", "Guangdong": "Guangdong Sheng", "Guizhou": "Guizhou Sheng", "Hainan": "Hainan Sheng", "Hebei": "Hebei Sheng", "Heilongjiang": "Heilongjiang Sheng", "Henan": "Henan Sheng", "Hubei": "Hubei Sheng", "Hunan": "Hunan Sheng", "Jiangsu": "Jiangsu Sheng", "Jiangxi": "Jiangxi Sheng", "Jilin": "Jilin Sheng", "Liaoning": "Liaoning Sheng", "Qinghai": "Qinghai Sheng", "Shaanxi": "Shaanxi Sheng", "Shandong": "Shandong Sheng", "Shanxi": "Shanxi Sheng", "Sichuan": "Sichuan Sheng", "Yunnan": "Yunnan Sheng", "Zhejiang": "Zhejiang Sheng"}},
    "FRA": {"name": "France", "map": {"Auvergne-Rhone-Alpes": "Auvergne-Rhône-Alpes", "Brittany": "Bretagne", "Burgundy-Franche-Comte": "Bourgogne-Franche-Comté", "Centre-Val de Loire": "Centre-Val de Loire", "Corsica": "Corse", "Grand Est": "Grand Est", "Hauts-de-France": "Hauts-de-France", "Ile-de-France": "Île-de-France", "Normandy": "Normandie", "Nouvelle-Aquitaine": "Nouvelle-Aquitaine", "Occitania": "Occitanie", "Pays de la Loire": "Pays de la Loire", "Provence-Alpes-Cote d'Azur": "Provence-Alpes-Côte d'Azur"}},
    "DEU": {"name": "Germany", "map": {"Baden-Wurttemberg": "Baden-Württemberg", "Bavaria": "Bayern", "Hesse": "Hessen", "Lower Saxony": "Niedersachsen", "North Rhine-Westphalia": "Nordrhein-Westfalen", "Rhineland-Palatinate": "Rheinland-Pfalz", "Saxony": "Sachsen", "Saxony-Anhalt": "Sachsen-Anhalt", "Thuringia": "Thüringen"}},
    "IND": {"name": "India", "map": {"Orissa": "Odisha", "Uttaranchal": "Uttarakhand", "Pondicherry": "Puducherry"}},
    "ITA": {"name": "Italy", "map": {
        "Apulia": "Puglia", "Lombardy": "Lombardia", "Piedmont": "Piemonte", "Sardinia": "Sardegna", "Sicily": "Sicilia", "Tuscany": "Toscana", "Trentino-South Tyrol": "Trentino-Alto Adige", "Valley of Aosta": "Valle d'Aosta", "Friuli Venezia Giulia": "Friuli-Venezia Giulia"
    }},
    "POL": {"name": "Poland", "map": {"Lower Silesian": "Dolnośląskie", "Kuyavian-Pomeranian": "Kujawsko-pomorskie", "Lublin": "Lubelskie", "Lubelskie": "Lubelskie", "Lubusz": "Lubuskie", "Łódź": "Łódzkie", "Lesser Poland": "Małopolskie", "Masovian": "Mazowieckie", "Opole": "Opolskie", "Podlaskie": "Podlaskie", "Pomeranian": "Pomorskie", "Silesian": "Śląskie", "Subcarpathian": "Podkarpackie", "Świętokrzyskie": "Świętokrzyskie", "Warmian-Masurian": "Warmińsko-mazurskie", "Greater Poland": "Wielkopolskie", "West Pomeranian": "Zachodniopomorskie"}},
    "RUS": {"name": "Russia", "map": {
        "Adygea": "Adygeya, Respublika", "Altai": "Altay, Respublika", "Altai Krai": "Altayskiy kray", "Amur Oblast": "Amurskaya oblast'", "Arkhangelsk Oblast": "Arkhangel'skaya oblast'", "Astrakhan Oblast": "Astrakhanskaya oblast'", "Bashkortostan": "Bashkortostan, Respublika", "Belgorod Oblast": "Belgorodskaya oblast'", "Bryansk Oblast": "Bryanskaya oblast'", "Buryatia": "Buryatiya, Respublika", "Chechnya": "Chechenskaya Respublika", "Chelyabinsk Oblast": "Chelyabinskaya oblast'", "Chukotka Autonomous Okrug": "Chukotskiy avtonomnyy okrug", "Chuvashia": "Chuvashskaya Respublika", "Dagestan": "Dagestan, Respublika", "Ingushetia": "Ingushskaya, Respublika", "Irkutsk Oblast": "Irkutskaya oblast'", "Ivanovo Oblast": "Ivanovskaya oblast'", "Kabardino-Balkaria": "Kabardino-Balkarskaya Respublika", "Kaliningrad Oblast": "Kaliningradskaya oblast'", "Kalmykia": "Kalmykiya, Respublika", "Kaluga Oblast": "Kaluzhskaya oblast'", "Kamchatka Krai": "Kamchatskiy kray", "Karachay-Cherkessia": "Karachayevo-Cherkesskaya Respublika", "Karelia": "Kareliya, Respublika", "Kemerovo Oblast": "Kemerovskaya oblast'", "Khabarovsk Krai": "Khabarovskiy kray", "Khakassia": "Khakasiya, Respublika", "Khanty-Mansi Autonomous Okrug": "Khanty-Mansiyskiy avtonomnyy okrug", "Kirov Oblast": "Kirovskaya oblast'", "Komi": "Komi, Respublika", "Kostroma Oblast": "Kostromskaya oblast'", "Krasnodar Krai": "Krasnodyarskiy kray", "Krasnoyarsk Krai": "Krasnoyarskiy kray", "Kurgan Oblast": "Kurganskaya oblast'", "Kursk Oblast": "Kurskaya oblast'", "Leningrad Oblast": "Leningradskaya oblast'", "Lipetsk Oblast": "Lipetskaya oblast'", "Magadan Oblast": "Magadanskaya oblast'", "Mari El": "Mariy El, Respublika", "Mordovia": "Mordoviya, Respublika", "Moscow": "Moskva", "Moscow Oblast": "Moskovskaya oblast'", "Murmansk Oblast": "Murmanskaya oblast'", "Nenets Autonomous Okrug": "Nenetskiy avtonomnyy okrug", "Nizhny Novgorod Oblast": "Nizhegorodskaya oblast'", "North Ossetia–Alania": "Severnaya Osetiya-Alaniya, Respublika", "Novgorod Oblast": "Novgorodskaya oblast'", "Novosibirsk Oblast": "Novosibirskaya oblast'", "Omsk Oblast": "Omskaya oblast'", "Orenburg Oblast": "Orenburgskaya oblast'", "Oryol Oblast": "Orlovskaya oblast'", "Penza Oblast": "Penzenskaya oblast'", "Perm Krai": "Permskiy kray", "Primorsky Krai": "Primorskiy kray", "Pskov Oblast": "Pskovskaya oblast'", "Rostov Oblast": "Rostovskaya oblast'", "Ryazan Oblast": "Ryazanskaya oblast'", "Saint Petersburg": "Sankt-Peterburg", "Sakha (Yakutia)": "Sakha, Respublika", "Sakhalin Oblast": "Sakhalinskaya oblast'", "Samara Oblast": "Samarskaya oblast'", "Saratov Oblast": "Saratovskaya oblast'", "Smolensk Oblast": "Smolenskaya oblast'", "Stavropol Krai": "Stavropol'skiy kray", "Sverdlovsk Oblast": "Sverdlovskaya oblast'", "Tambov Oblast": "Tambovskaya oblast'", "Tatarstan": "Tatarstan, Respublika", "Tomsk Oblast": "Tomskaya oblast'", "Tula Oblast": "Tul'skaya oblast'", "Tuva": "Tyva, Respublika", "Tver Oblast": "Tverskaya oblast'", "Tyumen Oblast": "Tyumenskaya oblast'", "Udmurtia": "Udmurtskaya Respublika", "Ulyanovsk Oblast": "Ul'yanovskaya oblast'", "Vladimir Oblast": "Vladimirskaya oblast'", "Volgograd Oblast": "Volgogradskaya oblast'", "Vologda Oblast": "Vologodskaya oblast'", "Voronezh Oblast": "Voronezhskaya oblast'", "Yamalo-Nenets Autonomous Okrug": "Yamalo-Nenentskiy avtonomnyy okrug", "Yaroslavl Oblast": "Yaroslavskaya oblast'", "Jewish Autonomous Oblast": "Yeveryskaya avtonomnaya oblast'", "Zabaykalsky Krai": "Zabaykal'skiy kray", "Sevastopol": "Sevastopol"
    }},
    "GBR": {"name": "United Kingdom", "map": {}},
    "USA": {"name": "United States", "map": {"Washington DC": "District of Columbia", "Puerto Rico": "Puerto Rico"}},
    "BEL": {"name": "Belgium", "map": {
        "Brussels": "Bruxelles-Capitale: Région de",
        "Flanders": "Vlaamse Gewest",
        "Wallonia": "wallonne, Région"
    }},
    "CHE": {"name": "Switzerland", "map": {
        "Aargau": "Aargau",
        "Appenzell Ausserrhoden": "Appenzell Ausserrhoden",
        "Appenzell Innerrhoden": "Appenzell Innerrhoden",
        "Basel-Landschaft": "Basel-Landschaft",
        "Basel-Stadt": "Basel-Stadt",
        "Bern": "Bern",
        "Fribourg": "Freiburg",         
        "Geneva": "Genève",          
        "Glarus": "Glarus",
        "Graubünden": "Graubünden",
        "Jura": "Jura",
        "Lucerne": "Luzern",            
        "Neuchâtel": "Neuchâtel",
        "Nidwalden": "Nidwalden",
        "Obwalden": "Obwalden",
        "Schaffhausen": "Schaffhausen",
        "Schwyz": "Schwyz",
        "Solothurn": "Solothurn",
        "St. Gallen": "Sankt Gallen", 
        "Thurgau": "Thurgau",
        "Ticino": "Ticino",
        "Uri": "Uri",
        "Valais": "Valais",          
        "Vaud": "Vaud",
        "Zug": "Zug",
        "Zurich": "Zürich",        
    }},
}

# Microstates
MICROSTATES = {
    "Vatican City": (41.9029, 12.4534), "Holy See": (41.9029, 12.4534), "Monaco": (43.7384, 7.4167), "San Marino": (43.9424, 12.4578), "Liechtenstein": (47.1410, 9.5215),
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

@st.cache_resource
def get_country_converter():
    return coco.CountryConverter()

cc = get_country_converter()

# --- CSS & Styles ---
try:
    with open("styles.css") as f: st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError: pass

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Color+Emoji&display=swap');
    
    .stRadio [role=radiogroup] { align-items: start; justify-content: start; }
    div[data-testid="stMetric"] { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
    .main .block-container { max-width: 98%; padding-left: 1rem; padding-right: 1rem; }
</style>
""", unsafe_allow_html=True)

# --- Data Loading (Cached & Optimized) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("./Data/Timeguessr_Stats.csv")
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        
        # --- SCORE IMPUTATION LOGIC (UPDATED) ---
        def fill_missing_scores(prefix, round_col_name):
            geo_col = f"{prefix} Geography Score"
            time_col = f"{prefix} Time Score"
            geo_min, geo_max = f"{geo_col} (Min)", f"{geo_col} (Max)"
            time_min, time_max = f"{time_col} (Min)", f"{time_col} (Max)"
            
            if not {geo_min, geo_max, time_min, time_max}.issubset(df.columns):
                return

            # 1. Impute Geo
            mask_geo_missing = df[geo_col].isna() & df[geo_min].notna() & df[geo_max].notna()
            if mask_geo_missing.any():
                df.loc[mask_geo_missing, geo_col] = (df.loc[mask_geo_missing, geo_min] + df.loc[mask_geo_missing, geo_max]) / 2

            # 2. Impute Time
            mask_time_missing = df[time_col].isna() & df[time_min].notna() & df[time_max].notna()
            if mask_time_missing.any():
                df.loc[mask_time_missing, time_col] = (df.loc[mask_time_missing, time_min] + df.loc[mask_time_missing, time_max]) / 2
            
            # 3. Recalculate Round Score if missing (Round Score = Geo + Time)
            if round_col_name and round_col_name in df.columns:
                mask_round_missing = df[round_col_name].isna() & df[geo_col].notna() & df[time_col].notna()
                if mask_round_missing.any():
                    df.loc[mask_round_missing, round_col_name] = df.loc[mask_round_missing, geo_col] + df.loc[mask_round_missing, time_col]

        m_col = 'Michael Round Score' if 'Michael Round Score' in df.columns else ('Michael Total Score' if 'Michael Total Score' in df.columns else None)
        s_col = 'Sarah Round Score' if 'Sarah Round Score' in df.columns else ('Sarah Total Score' if 'Sarah Total Score' in df.columns else None)

        fill_missing_scores('Michael', m_col)
        fill_missing_scores('Sarah', s_col)

        # --- TAIWAN DATA FIX ---
        mask_tw_data = (df['Country'] == 'China') & (df['Subdivision'] == 'Taiwan')
        df.loc[mask_tw_data, 'Country'] = 'Taiwan'
        df.loc[mask_tw_data, 'Subdivision'] = np.nan # Clear subdivision as it is now the country

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
        
        # Language Map
        df["Language"] = df["ISO3"].map(ISO_LANGUAGE_MAP).fillna("Other")
        
        # Special Language Logic for Quebec
        df.loc[(df['ISO3'] == 'CAN') & (df['Subdivision'].isin(['Québec', 'Quebec'])), 'Language'] = 'French'
        
        # Special Language Logic for Puerto Rico
        df.loc[(df['ISO3'] == 'USA') & (df['Subdivision'] == 'Puerto Rico'), 'Language'] = 'Spanish'

        # Special Language Logic for Belgium
        df.loc[(df['ISO3'] == 'BEL') & (df['Subdivision'] == 'Flanders'), 'Language'] = 'Germanic'
        df.loc[(df['ISO3'] == 'BEL') & (df['Subdivision'] == 'Wallonia'), 'Language'] = 'French'
        df.loc[(df['ISO3'] == 'BEL') & (df['Subdivision'] == 'Brussels'), 'Language'] = 'French'

        # Special Language Logic for Switzerland
        _che_french   = ['Geneva', 'Vaud', 'Neuchâtel', 'Jura', 'Fribourg', 'Valais']
        _che_italian_romansch  = ['Ticino','Graubünden']
        _che_germanic = [
            'Aargau', 'Appenzell Ausserrhoden', 'Appenzell Innerrhoden',
            'Basel-Landschaft', 'Basel-Stadt', 'Bern', 'Glarus', 
            'Lucerne', 'Nidwalden', 'Obwalden', 'Schaffhausen', 'Schwyz',
            'Solothurn', 'St. Gallen', 'Thurgau', 'Uri', 'Zug', 'Zurich'
        ]
        df.loc[(df['ISO3'] == 'CHE') & (df['Subdivision'].isin(_che_french)),   'Language'] = 'French'
        df.loc[(df['ISO3'] == 'CHE') & (df['Subdivision'].isin(_che_italian_romansch)),  'Language'] = 'Other Romance'
        df.loc[(df['ISO3'] == 'CHE') & (df['Subdivision'].isin(_che_germanic)), 'Language'] = 'Germanic'
        
        # Special Logic for China Subdivisions (Overlapping Languages) -> Set to "Other"
        chn_subdivs_other = ['Hong Kong', 'Macau', 'Macao', 'Tibet', 'Xizang Zizhiqu', 'Xinjiang', 'Xinjiang Uygur Zizhiqu']
        df.loc[(df['ISO3'] == 'CHN') & (df['Subdivision'].isin(chn_subdivs_other)), 'Language'] = 'Other'
        
        return df
    except FileNotFoundError:
        st.error("Stats file not found."); st.stop()

@st.cache_resource
def load_map():
    target_file = "./Data/Custom_World_Map_New.json"
    if not os.path.exists(target_file): return None, set()
    try:
        gdf = gpd.read_file(target_file)
        gdf['geometry'] = gdf['geometry'].buffer(0) # Fix Topology Errors
        
        # --- TAIWAN MAP FIX ---
        mask_tw = gdf['NAME'] == 'Taiwan'
        if 'ISO_SUB' in gdf.columns:
            mask_tw = mask_tw | (gdf['ISO_SUB'] == 'TW')
            
        iso_cols = [c for c in ['ISO3', 'iso3', 'adm0_a3'] if c in gdf.columns]
        if iso_cols:
            for col in iso_cols:
                gdf.loc[mask_tw, col] = 'TWN'
        else:
            gdf.loc[mask_tw, 'ISO3'] = 'TWN'
        
        gdf.loc[mask_tw, 'NAME'] = 'Taiwan'

        # Standardize
        iso_col = next((c for c in ['ISO3', 'iso3', 'adm0_a3'] if c in gdf.columns), None)
        if iso_col:
            gdf['ISO3'] = cc.convert(names=gdf[iso_col].tolist(), to='ISO3', not_found='UNK')
        else: gdf['ISO3'] = 'UNK'
        
        name_col = next((c for c in ['NAME', 'name', 'NAME_1', 'COUNTRY'] if c in gdf.columns), 'NAME')
        gdf['NAME'] = gdf[name_col].astype(str).str.strip()
        
        # Clean up territory suffixes to ensure they match standard subdivision/country names
        suffixes_to_remove = [' (UK)', ' (France)', ' (US)', ' (Netherlands)', ' (Denmark)', ' (Australia)', ' (New Zealand)', ' (China)']
        for suffix in suffixes_to_remove:
            gdf['NAME'] = gdf['NAME'].str.replace(suffix, '', regex=False)
        
        # Enrich Map Data
        clean_isos = [x for x in gdf['ISO3'].unique() if x != 'UNK']
        gdf['Continent'] = gdf['ISO3'].map(dict(zip(clean_isos, cc.convert(names=clean_isos, to="continent")))).fillna("Unknown")
        gdf['UN_Region'] = gdf['ISO3'].map(dict(zip(clean_isos, cc.convert(names=clean_isos, to="UNregion")))).fillna("Unknown")
        gdf['Language'] = gdf['ISO3'].map(ISO_LANGUAGE_MAP).fillna("Other")
        
        # Special Map Logic for Quebec
        gdf.loc[(gdf['ISO3'] == 'CAN') & (gdf['NAME'] == 'Quebec'), 'Language'] = 'French'
        
        # Special Map Logic for Puerto Rico
        gdf.loc[(gdf['ISO3'] == 'USA') & (gdf['NAME'] == 'Puerto Rico'), 'Language'] = 'Spanish'
        
        # Special Map Logic for China Subdivisions -> "Other"
        chn_map_names = ['Hong Kong', 'Macao', 'Xizang Zizhiqu', 'Xinjiang Uygur Zizhiqu']
        gdf.loc[(gdf['ISO3'] == 'CHN') & (gdf['NAME'].isin(chn_map_names)), 'Language'] = 'Other'

        # Special Map Logic for Belgium
        gdf.loc[(gdf['ISO3'] == 'BEL') & (gdf['NAME'] == 'Vlaamse Gewest'), 'Language'] = 'Germanic'
        gdf.loc[(gdf['ISO3'] == 'BEL') & (gdf['NAME'] == 'wallonne, Région'), 'Language'] = 'French'
        gdf.loc[(gdf['ISO3'] == 'BEL') & (gdf['NAME'] == 'Bruxelles-Capitale: Région de'), 'Language'] = 'French'
        
        # Special Map Logic for Switzerland
        _che_map_french   = ['Genève', 'Vaud', 'Neuchâtel', 'Jura', 'Freiburg', 'Valais']
        _che_map_italian_romansch  = ['Ticino','Graubünden']
        _che_map_germanic = [
            'Aargau', 'Appenzell Ausserrhoden', 'Appenzell Innerrhoden',
            'Basel-Landschaft', 'Basel-Stadt', 'Bern', 'Glarus', 
            'Luzern', 'Nidwalden', 'Obwalden', 'Schaffhausen', 'Schwyz',
            'Solothurn', 'Sankt Gallen', 'Thurgau', 'Uri', 'Zug', 'Zürich'
        ]
        gdf.loc[(gdf['ISO3'] == 'CHE') & (gdf['NAME'].isin(_che_map_french)),   'Language'] = 'French'
        gdf.loc[(gdf['ISO3'] == 'CHE') & (gdf['NAME'].isin(_che_map_italian_romansch)),  'Language'] = 'Other Romance'
        gdf.loc[(gdf['ISO3'] == 'CHE') & (gdf['NAME'].isin(_che_map_germanic)), 'Language'] = 'Germanic'

        return gdf, set(gdf['NAME'].unique())
    except Exception as e:
        st.error(f"Map error: {e}"); return None, set()

data = load_data()
base_gdf, valid_map_names = load_map()

# --- Geometry Functions ---

@st.cache_data
def get_background_layer(_gdf):
    """Creates a single unified shape for the whole world."""
    if _gdf is None: return None
    _gdf['World_Group'] = 1
    bg_gdf = _gdf.dissolve(by='World_Group', as_index=False)
    return json.loads(bg_gdf.to_json())

@st.cache_data
def generate_dynamic_map_layer(_gdf, active_iso_tuple, active_splits, active_subdivs_tuple, view_mode):
    """
    Generates map geometry only for active locations.
    Overseas territories automatically merge into their parent country if they 
    lack their own data but the parent country has data.
    """
    if _gdf is None: return None
    
    active_subdivs = {k: set(v) for k, v in active_subdivs_tuple}
    
    # 1. Expand active ISOs to include dependencies if parent is present
    isos_to_fetch = set(active_iso_tuple)
    for dep_iso, parent_iso in TERRITORY_PARENT_MAP.items():
        if parent_iso in isos_to_fetch:
            isos_to_fetch.add(dep_iso)
    
    work_gdf = _gdf[_gdf['ISO3'].isin(isos_to_fetch)].copy()
    if work_gdf.empty: return None

    # 2. Assign effective ISOs and properties to dependencies acting as parents
    def apply_parent_attributes(row):
        iso = row['ISO3']
        # If this is a territory, AND the territory itself has no stats, BUT the parent does:
        if iso in TERRITORY_PARENT_MAP and iso not in active_iso_tuple:
            parent_iso = TERRITORY_PARENT_MAP[iso]
            if parent_iso in active_iso_tuple:
                row['ISO3_Effective'] = parent_iso
                
                # Grab parent's Continent, Region, Language to ensure aggregate views match
                parent_rows = _gdf[_gdf['ISO3'] == parent_iso]
                if not parent_rows.empty:
                    parent_row = parent_rows.iloc[0]
                    row['Continent'] = parent_row['Continent']
                    row['UN_Region'] = parent_row['UN_Region']
                    row['Language'] = parent_row['Language']
                return row
        row['ISO3_Effective'] = iso
        return row
        
    work_gdf = work_gdf.apply(apply_parent_attributes, axis=1)

    # 3. Filter subdivisions for split countries
    def filter_subdivs(row):
        orig_iso = row['ISO3']
        eff_iso = row['ISO3_Effective']
        
        # Keep territories acting as their parent (e.g. Martinique acting as France)
        if orig_iso != eff_iso: return True
        
        # Keep all parts of a split country so they can be re-aggregated correctly
        if eff_iso not in active_splits:
            return True
            
        allowed = active_subdivs.get(eff_iso, set())
        return row['NAME'] in allowed

    if active_splits:
        work_gdf = work_gdf[work_gdf.apply(filter_subdivs, axis=1)]

    if work_gdf.empty: return None

    # 4. Dissolve geometries together based on the view level
    def get_dissolve_key(row):
        iso = row['ISO3_Effective']
        name = row['NAME']
        
        attr_val = None
        if view_mode == "Continents": attr_val = row['Continent']
        elif view_mode == "UN Regions": attr_val = row['UN_Region']
        elif view_mode == "Languages": attr_val = row['Language']
        
        if iso in active_splits:
             if view_mode == "Countries":
                 return name
             else:
                 return f"{iso}___{attr_val}"

        # If not split, just return the aggregate group
        if attr_val: return attr_val
        
        return iso

    work_gdf['Dissolve_Key'] = work_gdf.apply(get_dissolve_key, axis=1)
    return json.loads(work_gdf.dissolve(by='Dissolve_Key', as_index=False).to_json())

# --- Stats Calculation ---

@st.cache_data
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

    # 2. Handle View Mode Aggregation Mapping (Region/Continent/Language)
    if view_mode != "Countries":
        def get_agg_key(row):
            iso = row['ISO3']
            attr_val = None
            if view_mode == "Continents": attr_val = row['Continent']
            elif view_mode == "UN Regions": attr_val = row['UN_Region']
            elif view_mode == "Languages": attr_val = row['Language']

            if iso in active_splits: 
                return f"{iso}___{attr_val}"
            return attr_val
        
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

    # 4. Filter Data based on Metric
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

    # 5. Calculate Scores
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

    # 6. Row-Level Exclusivity
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
        'Row_Sarah_Only': 'sum',
        'Country': 'first',
        'Continent': 'first',
        'UN_Region': 'first',
        'ISO3': 'first',
        'Language': 'first'
    }
    
    grouped = df_work.groupby('Join_Key').agg(agg_cols).rename(columns={
        "Row_Shared": "Shared_Count",
        "Row_Michael_Only": "Michael_Only_Count",
        "Row_Sarah_Only": "Sarah_Only_Count",
        "Country": "Country_Name",
        "Continent": "Continent_Name",
        "UN_Region": "Region_Name",
        "ISO3": "ISO_Code",
        "Language": "Language_Name"
    }).reset_index()

    # 8. Post-Aggregation Calcs
    grouped['Total_Active'] = grouped['Shared_Count'] + grouped['Michael_Only_Count'] + grouped['Sarah_Only_Count']
    
    if metric == "Count":
        grouped['Count'] = grouped['Shared_Count']
    else:
        grouped['Count'] = grouped['Total_Active'] 

    grouped['Total Possible'] = grouped['Total_Active'] * max_p
    grouped['Michael Accuracy'] = grouped['Michael Selected'] / grouped['Total Possible']
    grouped['Sarah Accuracy'] = grouped['Sarah Selected'] / grouped['Total Possible']
    grouped['Combined'] = grouped['Michael Selected'] + grouped['Sarah Selected']
    grouped['Michael Share Ratio'] = grouped.apply(lambda x: x['Michael Selected'] / x['Combined'] if x['Combined'] > 0 else 0.5, axis=1)
    grouped['Sarah Share Ratio'] = 1 - grouped['Michael Share Ratio']

    # Max/Min Scores
    mm = df_work.groupby('Join_Key')[['Michael Selected', 'Sarah Selected']].agg(['max', 'min'])
    mm.columns = [f"{c[0]}_{c[1]}" for c in mm.columns]
    grouped = grouped.merge(mm, on='Join_Key', how='left')

    # 9. Hover Names
    unique_keys = grouped['Join_Key'].unique()
    iso_keys = [k for k in unique_keys if isinstance(k, str) and len(k) == 3 and k.isupper()]
    simple_names = {}
    if iso_keys:
        converted = coco.convert(names=iso_keys, to='name_short', not_found=None)
        if isinstance(converted, str): converted = [converted]
        simple_names = dict(zip(iso_keys, converted))

    def get_label(row):
        key = row['Join_Key']
        iso = row['ISO_Code']

        if view_mode == "Countries" and iso == "VAT": return "Vatican City"
        
        if view_mode != "Countries" and iso in active_splits:
            base_name = SPLIT_CONFIG.get(iso, {}).get('name', simple_names.get(iso, str(iso)))
            suffix = ""
            if view_mode == "UN Regions": suffix = row['Region_Name']
            elif view_mode == "Continents": suffix = row['Continent_Name']
            elif view_mode == "Languages": suffix = row['Language_Name']
            return f"{base_name}, {suffix}"
            
        if view_mode == "Countries" and iso in active_splits:
            if key != iso:
                country_nice = SPLIT_CONFIG.get(iso, {}).get('name', row['Country_Name'])
                return f"{key}, {country_nice}"
        
        if key in SPLIT_CONFIG: return SPLIT_CONFIG[key]['name']
        if key in simple_names: return simple_names[key]
        return str(key)

    grouped['Hover_Name'] = grouped.apply(get_label, axis=1)

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
    
    html += "<thead><tr>"
    for col in df.columns:
        s = header_style if col == "Location" else header_center
        html += f"<th style='{s}'>{col}</th>"
    html += "</tr></thead><tbody>"
    
    for _, row in df.iterrows():
        html += f"<tr style='{row_style}'>"
        for col in df.columns:
            val = row[col]
            style = cell_style if col == "Location" else cell_center
            content = str(val)
            
            if col == "Count" or "Rank" in col or "Highest Score" in col or "Lowest Score" in col:
                content = f"{int(val):,}"
            elif col == "Score Advantage":
                if pd.isna(val):
                    content = "-"
                else:
                    if val > 0:
                        style = style.replace("#696761", COLORS['michael'])
                        content = f"+{val:.1%}"
                    elif val < 0:
                        style = style.replace("#696761", COLORS['sarah'])
                        content = f"+{abs(val):.1%}"
                    else:
                        content = "0.0%"
            elif "Win Rate" in col:
                if pd.isna(val):
                    content = "-"
                else:
                    content = f"{val:.1%}"
                    m_rate = row.get("Michael Win Rate", 0)
                    s_rate = row.get("Sarah Win Rate", 0)
                    
                    if "Michael" in col:
                         style = style.replace("#696761", COLORS['michael'])
                         if m_rate > s_rate: style += " font-weight: bold;"
                    elif "Sarah" in col:
                         style = style.replace("#696761", COLORS['sarah'])
                         if s_rate > m_rate: style += " font-weight: bold;"
                        
            elif "Ratio" in col or "Accuracy" in col:
                if pd.isna(val):
                    content = "-"
                else:
                    content = f"{val:.1%}"
                    if "Michael" in col:
                        style = style.replace("#696761", COLORS['michael'])
                    elif "Sarah" in col:
                        style = style.replace("#696761", COLORS['sarah'])
            
            html += f"<td style='{style}'>{content}</td>"
        html += "</tr>"
    
    html += "</tbody></table>"
    return html

# --- Sidebar ---
tbd_display_list = []

with st.sidebar:
    st.header("Map Settings")

    map_metric = st.radio("Metric:", ["Count", "Comparison", "Michael", "Sarah"])
    score_mode = st.radio("Score Type:", ["Total Score", "Geography Score", "Time Score"]) if map_metric != "Count" else "Total Score"
    view_mode = st.radio("View Level:", ["Countries", "UN Regions", "Continents", "Languages"])
    
    avail_splits = [cfg['name'] for cfg in SPLIT_CONFIG.values()]
    sel_splits = st.multiselect("Split Countries:", avail_splits, default=[])
    
    if "Date" in data.columns:
        min_d = data[data['Country'].notna()]["Date"].min().date()
        max_d = data["Date"].max().date()
        sel_dates = st.slider("Select Date Range:", min_d, max_d, (min_d, max_d), format="MM/DD/YY")
        filtered_data = data[(data["Date"].dt.date >= sel_dates[0]) & (data["Date"].dt.date <= sel_dates[1])].copy()
    else: filtered_data = data.copy()

    active_splits = set()
    for iso, cfg in SPLIT_CONFIG.items():
        if cfg['name'] in sel_splits:
            active_splits.add(iso)
            mask = filtered_data['ISO3'] == iso
            if mask.any() and cfg['map']:
                filtered_data.loc[mask, 'Subdivision'] = filtered_data.loc[mask, 'Subdivision'].replace(cfg['map'])
                if valid_map_names:
                    bad = filtered_data[mask & ~filtered_data['Subdivision'].isin(valid_map_names)]
                    if not bad.empty: 
                        st.error(f"Unknown subdivision in {cfg['name']}: {bad['Subdivision'].unique()}")
                        st.stop()
    
    # Filter TBD Languages for Display
    if view_mode == "Languages":
        tbd_mask = filtered_data['Language'] == "Other"
        if tbd_mask.any():
            tbd_df = filtered_data[tbd_mask]
            for _, r in tbd_df[['Country', 'Subdivision']].drop_duplicates().iterrows():
                name = r['Country']
                if pd.notna(r['Subdivision']) and str(r['Subdivision']).strip():
                    name += f" ({r['Subdivision']})"
                tbd_display_list.append(name)
            
            filtered_data = filtered_data[~tbd_mask]

    active_splits_frozen = frozenset(active_splits)

    # Main Calculation
    stats = calculate_stats(filtered_data, active_splits_frozen, view_mode, map_metric, score_mode)
    
    max_games = int(stats['Total_Active'].max()) if not stats.empty else 0
    min_count = st.slider("Min Games:", 0, max_games, 0)
    
    stats = stats[stats['Total_Active'] >= min_count]
    stats = stats[stats['Total_Active'] > 0]

st.markdown("## Locations")

if tbd_display_list:
    st.info(f"**TBD Languages:** The following locations are excluded from the map/stats because their language is not yet categorized: {', '.join(sorted(list(set(tbd_display_list))))}")

# --- Map Generation ---

if not filtered_data.empty:
    map_data = filtered_data.copy()
    map_data['Join_Key'] = map_data['ISO3'] 
    
    if active_splits:
         if view_mode == "Countries":
            mask_split = map_data['ISO3'].isin(active_splits) & map_data['Subdivision'].notna()
            map_data.loc[mask_split, 'Join_Key'] = map_data.loc[mask_split, 'Subdivision']
    
    if view_mode != "Countries":
        mask_not_split = ~map_data['ISO3'].isin(active_splits)
        
        attr_col = None
        if view_mode == "Continents": attr_col = "Continent"
        elif view_mode == "UN Regions": attr_col = "UN_Region"
        elif view_mode == "Languages": attr_col = "Language"
        
        if attr_col:
            map_data.loc[mask_not_split, 'Join_Key'] = map_data.loc[mask_not_split, attr_col]
            
            if active_splits:
                mask_split = map_data['ISO3'].isin(active_splits)
                if mask_split.any():
                    map_data.loc[mask_split, 'Join_Key'] = map_data.loc[mask_split, 'ISO3'] + "___" + map_data.loc[mask_split, attr_col].astype(str)

    if 'Michael Round Score' in map_data.columns:
        m_played = map_data['Michael Round Score'].notna()
    else:
        m_played = map_data['Michael Geography Score'].notna() 

    if 'Sarah Round Score' in map_data.columns:
        s_played = map_data['Sarah Round Score'].notna()
    else:
        s_played = map_data['Sarah Geography Score'].notna()

    if map_metric == "Michael":
        map_data = map_data[m_played]
    elif map_metric == "Sarah":
        map_data = map_data[s_played]
    elif map_metric == "Comparison":
        map_data = map_data[m_played & s_played]
    elif map_metric == "Count":
        map_data = map_data[m_played | s_played]

active_keys = set(stats['Join_Key'].unique())
active_iso_tuple = tuple(map_data[map_data['Join_Key'].isin(active_keys)]['ISO3'].unique()) if not stats.empty else ()

active_subdivs = {}
if active_splits:
    for iso in active_splits:
        subs = map_data[(map_data['ISO3'] == iso) & map_data['Subdivision'].notna()]['Subdivision'].astype(str).str.strip().unique()
        active_subdivs[iso] = tuple(subs)

active_subdivs_tuple = tuple(active_subdivs.items())

map_geojson = generate_dynamic_map_layer(base_gdf, active_iso_tuple, active_splits_frozen, active_subdivs_tuple, view_mode)
bg_geojson = get_background_layer(base_gdf)

fig = go.Figure()

if bg_geojson:
    fig.add_trace(go.Choropleth(
        geojson=bg_geojson, locations=[1], z=[1], featureidkey="properties.World_Group",
        colorscale=[[0, "#eeeeee"], [1, "#eeeeee"]], showscale=False,
        marker_line_color="white", marker_line_width=0.1, hoverinfo='skip'
    ))

if map_geojson and not stats.empty:
    max_val = stats['Count'].max() if map_metric != "Comparison" else 0.6
    if max_val == 0: max_val = 1
    
    scales = {
        "Count": ([[0, "#fee6e6"], [1, "#db5049"]], 0, max_val),
        "Comparison": ([[0, "#8a005c"], [0.5, "#f2f2f2"], [1, "#221e8f"]], 0.4, 0.6),
        "Michael": ([[0, "#e6e6ff"], [1, "#221e8f"]], 0.5, 1.0),
        "Sarah": ([[0, "#ffe6f2"], [1, "#8a005c"]], 0.5, 1.0)
    }
    scale, zmin, zmax = scales.get(map_metric, scales["Count"])
    z_col = "Michael Share Ratio" if map_metric == "Comparison" else (f"{map_metric} Accuracy" if map_metric in ["Michael", "Sarah"] else "Count")
    
    stats_shared = stats.copy()
    stats_exclusive = pd.DataFrame()
    stats['BorderColor'] = "black"
    stats['BorderWidth'] = 0.5
    
    if map_metric == "Count":
        mask_excl = stats['Count'] == 0
        stats_exclusive = stats[mask_excl].copy()
        stats_shared = stats[~mask_excl].copy()
        stats_exclusive['BorderColor'] = "#221e8f" 
    elif map_metric == "Comparison":
        stats['BorderColor'] = np.where(stats[z_col] > 0.5, "#221e8f", np.where(stats[z_col] < 0.5, "#8a005c", "#666666"))
        stats_shared = stats 
    else:
        stats_shared = stats 

    stats_shared['Score_Str'] = stats_shared.apply(lambda r: f"{int(r['Michael Selected'])}/{int(r['Total Possible'])}" if map_metric=="Michael" else (f"{int(r['Sarah Selected'])}/{int(r['Total Possible'])}" if map_metric=="Sarah" else ""), axis=1)
    if not stats_exclusive.empty: stats_exclusive['Score_Str'] = ""

    hover_base = "<b>%{text}</b><br>"
    if map_metric == "Count":
        hover_t = hover_base + "Count: %{customdata[2]}<br>Michael Only: %{customdata[0]}<br>Sarah Only: %{customdata[1]}<extra></extra>"
        custom_cols = ['Michael_Only_Count', 'Sarah_Only_Count', 'Count']
    elif map_metric == "Comparison": 
        hover_t = hover_base + "Michael Percent: %{customdata[2]:.1%}<br>Sarah Percent: %{customdata[3]:.1%}<br>Michael Points: %{customdata[0]:,.0f}<br>Sarah Points: %{customdata[1]:,.0f}<extra></extra>"
        custom_cols = ['Michael Selected', 'Sarah Selected', 'Michael Share Ratio', 'Sarah Share Ratio']
    else: 
        hover_t = hover_base + "Accuracy: %{z:.1%}<br>Score: %{customdata[0]}<extra></extra>"
        custom_cols = ['Score_Str']

    if not stats_shared.empty:
        fig.add_trace(go.Choropleth(
            geojson=map_geojson, locations=stats_shared['Join_Key'], z=stats_shared[z_col],
            featureidkey="properties.Dissolve_Key", colorscale=scale, zmin=zmin, zmax=zmax,
            marker_line_color=stats_shared['BorderColor'], marker_line_width=stats_shared['BorderWidth'],
            text=stats_shared['Hover_Name'], customdata=stats_shared[custom_cols],
            hovertemplate=hover_t, showscale=False
        ))

    if not stats_exclusive.empty and map_metric == "Count":
        fig.add_trace(go.Choropleth(
            geojson=map_geojson, locations=stats_exclusive['Join_Key'],
            featureidkey="properties.Dissolve_Key", 
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']], 
            marker_line_color=stats_exclusive['BorderColor'], marker_line_width=stats_exclusive['BorderWidth'],
            text=stats_exclusive['Hover_Name'], customdata=stats_exclusive[custom_cols],
            hovertemplate=hover_t, showscale=False,
            z=[1]*len(stats_exclusive)
        ))

    # Fix: Check both Hover_Name (standard) and Join_Key (for split subdivisions with appended parent names)
    ms_mask = stats['Hover_Name'].isin(MICROSTATES) | stats['Join_Key'].isin(MICROSTATES)
    ms_df = stats[ms_mask].copy()
    if not ms_df.empty:
        def get_ms_coord(r):
            if r['Hover_Name'] in MICROSTATES: return MICROSTATES[r['Hover_Name']]
            if r['Join_Key'] in MICROSTATES: return MICROSTATES[r['Join_Key']]
            return None
            
        coords = ms_df.apply(get_ms_coord, axis=1).tolist()
        
        ms_custom = ms_df[custom_cols].copy()
        ms_custom['z_val'] = ms_df[z_col] 
        
        z_idx = len(custom_cols)
        hover_t_ms = hover_t.replace("%{z", f"%{{customdata[{z_idx}]")
        
        fig.add_trace(go.Scattergeo(
            lat=[x[0] for x in coords], lon=[x[1] for x in coords], mode='markers',
            marker=dict(size=8, color=ms_df[z_col], colorscale=scale, cmin=zmin, cmax=zmax, 
                        line=dict(width=1, color=ms_df['BorderColor'])),
            text=ms_df['Hover_Name'], customdata=ms_custom, hovertemplate=hover_t_ms
        ))

    if view_mode == "Languages" and map_geojson and not stats.empty:
        key_to_lang = dict(zip(stats['Join_Key'], stats['Language_Name']))
        MIN_AREA_DEG2 = 0.05 
        BUFFER_DEG = 0.5

        emoji_lats, emoji_lons, emoji_texts = [], [], []
        polys_by_lang = {}

        for feature in map_geojson.get('features', []):
            dissolve_key = feature['properties'].get('Dissolve_Key', '')
            lang = key_to_lang.get(dissolve_key)
            emoji = LANGUAGE_EMOJIS.get(lang) if lang else None
            if not emoji: continue

            geom = shp_shape(feature['geometry'])
            polys = list(geom.geoms) if geom.geom_type == 'MultiPolygon' else ([geom] if geom.geom_type == 'Polygon' else [])

            for poly in polys:
                if poly.area >= MIN_AREA_DEG2:
                    if lang not in polys_by_lang:
                        polys_by_lang[lang] = {'emoji': emoji, 'polygons': []}
                    polys_by_lang[lang]['polygons'].append(poly)

        for lang, data_dict in polys_by_lang.items():
            emoji = data_dict['emoji']
            original_polys = data_dict['polygons']
            
            buffers = [p.buffer(BUFFER_DEG) for p in original_polys]
            merged_buffers = unary_union(buffers)
            clusters = list(merged_buffers.geoms) if merged_buffers.geom_type == 'MultiPolygon' else [merged_buffers]
            
            for cluster in clusters:
                cluster_polys = [p for p in original_polys if p.intersects(cluster)]
                if not cluster_polys: continue
                    
                largest_poly = max(cluster_polys, key=lambda p: p.area)
                pt = largest_poly.representative_point()
                
                emoji_lons.append(pt.x)
                emoji_lats.append(pt.y)
                emoji_texts.append(emoji)

        if emoji_lats:
            fig.add_trace(go.Scattergeo(
                lat=emoji_lats,
                lon=emoji_lons,
                mode='text',
                text=emoji_texts,
                textfont=dict(
                    size=11,
                    color='rgba(0,0,0,0.7)',
                    family='"Noto Color Emoji", "Apple Color Emoji", "Twemoji Mozilla", sans-serif'
                ),
                hoverinfo='skip',
                showlegend=False,
            ))

fig.update_layout(
    geo=dict(showframe=False, showcoastlines=False, projection_type="robinson", 
             bgcolor='rgba(0,0,0,0)', showocean=True, oceancolor="white", showland=True, landcolor="white"),
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
    
    if 'Last_Date' in disp.columns:
        disp['Most Recent Date'] = disp['Last_Date'].dt.strftime('%Y-%m-%d')
    else:
        disp['Most Recent Date'] = ""

    cols = ['Hover_Name', 'Count', 'Most Recent Location', 'Most Recent Date']
    def_sort_col = "Count"
    def_sort_idx = 0 

    if map_metric == "Comparison":
        def get_win_rates(row):
            total = row['Count']
            if total == 0: return 0.0, 0.0
            return row['Michael Win'] / total, row['Sarah Win'] / total

        rates = disp.apply(get_win_rates, axis=1, result_type='expand')
        disp['Michael Win Rate'] = rates[0]
        disp['Sarah Win Rate'] = rates[1]
        
        disp['Score Advantage'] = disp['Michael Accuracy'] - disp['Sarah Accuracy']
        
        v = disp['Total Possible']
        R = disp['Score Advantage'].abs() 
        m_total = disp['Michael Selected'].sum()
        s_total = disp['Sarah Selected'].sum()
        p_total = disp['Total Possible'].sum()
        C = abs(m_total - s_total) / p_total if p_total > 0 else 0
        m = v.mean()
        
        if m > 0:
            bayesian_val = (v * R + m * C) / (v + m)
        else:
            bayesian_val = 0
            
        disp['abs_bayesian'] = bayesian_val
        disp = disp.sort_values('abs_bayesian', ascending=False)
        disp['Discrepancy Rank'] = range(1, len(disp) + 1)
        
        cols = ['Discrepancy Rank', 'Hover_Name', 'Count', 'Score Advantage', 'Michael Win Rate', 'Sarah Win Rate']
        def_sort_col = "Discrepancy Rank"
        def_sort_idx = 1 
        
    elif map_metric in ["Michael", "Sarah"]:
        cols = ['Hover_Name', 'Count']
        prefix = "Michael" if map_metric == "Michael" else "Sarah"
        disp['Score'] = disp.apply(lambda x: f"{int(x[f'{prefix} Selected']):,}/{int(x['Total Possible']):,}", axis=1)
        acc_col = f'{map_metric} Accuracy'
        
        disp['Highest Score'] = disp[f'{prefix} Selected_max']
        disp['Lowest Score'] = disp[f'{prefix} Selected_min']

        v = disp['Total Possible']
        R = disp[acc_col]
        total_sel = disp[f'{prefix} Selected'].sum()
        total_pos = disp['Total Possible'].sum()
        C = total_sel / total_pos if total_pos > 0 else 0
        m = v.mean()
        
        if m > 0:
            disp['bayesian_val'] = (v * R + m * C) / (v + m)
        else:
            disp['bayesian_val'] = 0
            
        disp = disp.sort_values('bayesian_val', ascending=False)
        disp['Rank'] = range(1, len(disp) + 1)
        cols = ['Rank'] + cols + ['Score', 'Highest Score', 'Lowest Score', acc_col]
        
        def_sort_col = "Rank"
        def_sort_idx = 1 
        
    final_df = disp[cols].rename(columns={'Hover_Name': 'Location'})
    
    col_opts = list(final_df.columns)
    try: idx_col = col_opts.index(def_sort_col)
    except: idx_col = 0

    sort_c1, sort_c2 = st.columns([3, 1])
    with sort_c1:
        sort_col = st.selectbox("Sort By", options=col_opts, index=idx_col)
    with sort_c2:
        sort_dir = st.selectbox("Order", options=["Descending", "Ascending"], index=def_sort_idx)
    
    ascending = sort_dir == "Ascending"
    final_df = final_df.sort_values(by=sort_col, ascending=ascending)
    
    st.markdown(create_styled_table(final_df), unsafe_allow_html=True)