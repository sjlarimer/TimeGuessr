import geopandas as gpd
import pandas as pd
import os
import country_converter as coco

# --- Configuration ---
INPUT_FILE = "./Data/World_Administrative_Divisions.geojson"
OUTPUT_FILE = "./Data/Custom_World_Map.geojson"

# List of Countries to KEEP subdivisions for (ISO Alpha-3 Codes)
COUNTRIES_TO_KEEP_SPLIT = [
    'USA', # United States
    'GBR', # United Kingdom
    'FRA', # France
    'NLD', # Netherlands
    'ITA', # Italy
    'CAN', # Canada
    'DEU', # Germany
    'POL', # Poland
    'SWE', # Sweden
    'JPN', # Japan
    'AUS', # Australia
    'CHN', # China
    'CHE', # Switzerland
    'HUN', # Hungary
    'GRC', # Greece
    'DNK', # Denmark
    'NOR', # Norway
    'ESP', # Spain
    'FIN', # Finland
    'IRL', # Ireland
    'RUS', # Russia
    'BRA', # Brazil
    'BEL', # Belgium
    'KOR', # South Korea
    'PRT', # Portugal
    'NZL', # New Zealand
    'IND', # India
    'ZAF', # South Africa
    'MEX', # Mexico
    'PER', # Peru
    'TUR', # Turkey
    'AUT', # Austria
    'VNM', # Vietnam
    'CZE', # Czechia
]

def process_map():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Input file not found at {INPUT_FILE}")
        return

    print(f"READING: {INPUT_FILE}...")
    try:
        gdf = gpd.read_file(INPUT_FILE)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    print(f"✅ Loaded {len(gdf)} rows.")

    if 'ISO3' not in gdf.columns:
        print("PROCESSING: Generating standard ISO3 codes...")
        source_col = 'ISO_CC' if 'ISO_CC' in gdf.columns else 'COUNTRY'
        if source_col not in gdf.columns:
            print(f"❌ Error: Could not find 'ISO_CC' or 'COUNTRY' to generate ISO3 codes.")
            print(f"Columns found: {list(gdf.columns)}")
            return
        names = gdf[source_col].fillna('Unknown').tolist()
        gdf['ISO3'] = coco.convert(names=names, to='ISO3', not_found=None)

    country_col = 'ISO3'
    print("✅ ISO3 column ready.")

    print(f"PROCESSING: Keeping subdivisions for {COUNTRIES_TO_KEEP_SPLIT}...")
    gdf_split = gdf[gdf[country_col].isin(COUNTRIES_TO_KEEP_SPLIT)].copy()
    gdf_dissolve_source = gdf[~gdf[country_col].isin(COUNTRIES_TO_KEEP_SPLIT)].copy()

    print(f"   - Rows to keep split: {len(gdf_split)}")
    print(f"   - Rows to dissolve:   {len(gdf_dissolve_source)}")

    if not gdf_dissolve_source.empty:
        print("DISSOLVING: Merging borders for the rest of the world...")
        gdf_dissolved = gdf_dissolve_source.dissolve(by=country_col, as_index=False)
    else:
        gdf_dissolved = gpd.GeoDataFrame()

    print("COMBINING: merging layers...")
    gdf_final = pd.concat([gdf_split, gdf_dissolved], ignore_index=True)

    print(f"WRITING: Saving to {OUTPUT_FILE}...")
    try:
        gdf_final.to_file(OUTPUT_FILE, driver='GeoJSON')
        print("✅ Done! File saved.")
    except Exception as e:
        print(f"❌ Error writing file: {e}")

if __name__ == "__main__":
    process_map()
