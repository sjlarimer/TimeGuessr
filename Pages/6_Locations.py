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

# --- Styles ---
try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.markdown("""
<style>
    .stRadio [role=radiogroup] {
        align-items: center;
        justify-content: center;
    }
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    div[data-testid="stDataFrame"] {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("## Locations")

# --- 1. Global Controls ---
col1, col2, col3 = st.columns(3)

with col1:
    map_metric = st.radio(
        "Select Metric:",
        options=["Count", "Comparison", "Michael", "Sarah"],
        horizontal=True,
        label_visibility="collapsed",
        key="map_metric_selector"
    )

with col2:
    # Container for view controls
    c2_1, c2_2 = st.columns([2, 1])
    with c2_1:
        view_mode = st.radio(
            "Select View Level:",
            options=["Countries", "Continents", "UN Regions"],
            horizontal=True,
            label_visibility="collapsed",
            key="view_mode_selector"
        )
    with c2_2:
        split_us = st.toggle("Split US", value=False)

with col3:
    score_mode = st.radio(
        "Select Score Type:",
        options=["Total Score", "Geography Score", "Time Score"],
        horizontal=True,
        label_visibility="collapsed",
        key="score_mode_selector"
    )

# --- Load data ---
try:
    data = pd.read_csv("./Data/Timeguessr_Stats.csv")
except FileNotFoundError:
    st.error("Stats file not found. Please ensure './Data/Timeguessr_Stats.csv' exists.")
    st.stop()

# --- Mappings ---
cc = coco.CountryConverter()

# US State Mapping (Name -> Code)
us_state_abbrev = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
    'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
    'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
    'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
    'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
    'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
    'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
    'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
    'District of Columbia': 'DC', 'Washington DC': 'DC', 'Washington, D.C.': 'DC', 'DC': 'DC', 'D.C.': 'DC'
}

# --- 2. Dynamic Data Prep ---

if score_mode == "Total Score":
    req_cols = ["Michael Geography Score", "Michael Time Score", "Sarah Geography Score", "Sarah Time Score"]
    data = data.dropna(subset=req_cols).copy()
    data["Michael Selected"] = data["Michael Geography Score"] + data["Michael Time Score"]
    data["Sarah Selected"] = data["Sarah Geography Score"] + data["Sarah Time Score"]
    max_points_per_game = 10000
elif score_mode == "Geography Score":
    req_cols = ["Michael Geography Score", "Sarah Geography Score"]
    data = data.dropna(subset=req_cols).copy()
    data["Michael Selected"] = data["Michael Geography Score"]
    data["Sarah Selected"] = data["Sarah Geography Score"]
    max_points_per_game = 5000
else:
    req_cols = ["Michael Time Score", "Sarah Time Score"]
    data = data.dropna(subset=req_cols).copy()
    data["Michael Selected"] = data["Michael Time Score"]
    data["Sarah Selected"] = data["Sarah Time Score"]
    max_points_per_game = 5000

# Metadata Conversion
unique_countries = data["Country"].unique()
iso3_map = dict(zip(unique_countries, cc.convert(names=unique_countries, to="ISO3", not_found=None)))
continent_map = dict(zip(unique_countries, cc.convert(names=unique_countries, to="continent")))
un_region_map = dict(zip(unique_countries, cc.convert(names=unique_countries, to="UNregion")))

data["ISO3"] = data["Country"].map(iso3_map)
data["Continent"] = data["Country"].map(continent_map)
data["UN_Region"] = data["Country"].map(un_region_map)

# --- 3. Aggregation Function ---
def get_aggregated_data(df, view_mode, split_us_flag):
    """
    Aggregates data. 
    - Handles US Splitting (Only in 'Countries' mode).
    - Handles Full Continent Coloring (In 'Continents'/'UN Regions' mode).
    """
    df_working = df.copy()
    df_working["Location_Mode"] = "ISO-3" # Default
    
    subdiv_col = "Subdivision"
    
    # --- Regional Split Logic ---
    if split_us_flag and view_mode in ["Continents", "UN Regions"]:
        target_col = "Continent" if view_mode == "Continents" else "UN_Region"
        df_working.loc[df_working["ISO3"] == "USA", target_col] = "United States"

    # --- Country Split Logic ---
    if view_mode == "Countries" and subdiv_col in df_working.columns and split_us_flag:
        is_us = df_working["ISO3"] == "USA"
        df_working.loc[is_us, "Mapped_Code"] = df_working.loc[is_us, subdiv_col].map(us_state_abbrev)
        
        mask_us_valid = is_us & df_working["Mapped_Code"].notna()
        df_working.loc[mask_us_valid, "Location_Mode"] = "USA-states"
        df_working.loc[mask_us_valid, "Country"] = df_working.loc[mask_us_valid, subdiv_col]
        df_working.loc[mask_us_valid, "ISO3"] = df_working.loc[mask_us_valid, "Mapped_Code"]

    # --- Grouping ---
    if view_mode == "Countries":
        group_col = "Country"
        grouped = df_working.groupby(["Country", "ISO3", "Location_Mode"]).agg({
            "Michael Selected": "sum",
            "Sarah Selected": "sum",
            "Country": "count"
        }).rename(columns={"Country": "Count"}).reset_index()
        
        grouped["Hover_Name"] = grouped["Country"]
        
    else:
        # --- Regional Aggregation (Fill Holes) ---
        group_key = "Continent" if view_mode == "Continents" else "UN_Region"
        group_col = group_key
        
        # 1. Aggregate Stats by Region
        grouped_agg = df_working.groupby(group_key).agg({
            "Michael Selected": "sum",
            "Sarah Selected": "sum",
            "Country": "count"
        }).rename(columns={"Country": "Count"}).reset_index()
        
        # 2. Build a Full Reference of ALL Countries to fill holes
        try:
            full_ref = cc.data[['ISO3', 'continent', 'UNregion', 'name_short']].copy()
            full_ref = full_ref[full_ref['ISO3'].notna()].drop_duplicates(subset=['ISO3'])
        except:
            full_ref = df_working[["Country", "ISO3", "Continent", "UN_Region"]].drop_duplicates()

        # Map the reference columns to our group key
        ref_key = 'continent' if view_mode == "Continents" else 'UNregion'
        
        # Apply US Split to Reference as well
        if split_us_flag:
            full_ref.loc[full_ref["ISO3"] == "USA", ref_key] = "United States"
        
        # Merge stats into the full reference based on the region name
        grouped = pd.merge(full_ref, grouped_agg, left_on=ref_key, right_on=group_key, how="right")
        
        grouped["Hover_Name"] = grouped[group_key]
        grouped["Location_Mode"] = "ISO-3"
        grouped = grouped.rename(columns={'name_short': 'Country'})

    # --- Calculations ---
    grouped["Total Possible"] = grouped["Count"] * max_points_per_game
    grouped["Michael Efficiency"] = grouped["Michael Selected"] / grouped["Total Possible"]
    grouped["Sarah Efficiency"] = grouped["Sarah Selected"] / grouped["Total Possible"]
    
    grouped["Combined Points"] = grouped["Michael Selected"] + grouped["Sarah Selected"]
    grouped["Michael Share Ratio"] = grouped.apply(
        lambda row: row["Michael Selected"] / row["Combined Points"] if row["Combined Points"] > 0 else 0.5, 
        axis=1
    )
    
    # Formatting
    grouped["Michael Eff %"] = (grouped["Michael Efficiency"] * 100).map('{:,.1f}%'.format)
    grouped["Sarah Eff %"] = (grouped["Sarah Efficiency"] * 100).map('{:,.1f}%'.format)
    grouped["Michael Share %"] = (grouped["Michael Share Ratio"] * 100).map('{:,.1f}%'.format)
    grouped["Sarah Share %"] = ((1 - grouped["Michael Share Ratio"]) * 100).map('{:,.1f}%'.format)
    
    return grouped, group_col

# --- 4. Get Data ---
map_data, locality_col = get_aggregated_data(data, view_mode, split_us)

# DEBUG: Check for unmapped US subdivisions
if split_us and view_mode == "Countries":
    us_subset = data[data["ISO3"] == "USA"]
    if "Subdivision" in us_subset.columns:
        unmapped_mask = ~us_subset["Subdivision"].isin(us_state_abbrev.keys())
        unmapped_vals = us_subset.loc[unmapped_mask, "Subdivision"]
        if not unmapped_vals.empty:
            with st.expander("⚠️ Unmapped US Subdivisions Found", expanded=True):
                st.write(unmapped_vals.value_counts())

# Split data for plotting logic
world_data = map_data[map_data["Location_Mode"] == "ISO-3"].copy()
if split_us and view_mode == "Countries":
    world_data = world_data[world_data["ISO3"] != "USA"]

us_data = map_data[map_data["Location_Mode"] == "USA-states"].copy()

# --- 5. Layout Settings & Helpers ---
is_regional = view_mode in ["Continents", "UN Regions"]

layout_settings = dict(
    geo=dict(
        showframe=False, 
        bgcolor="#d9d7cc",
        lakecolor="#d9d7cc",
        showland=True, 
        landcolor="white",
        projection=dict(type="robinson"),
        scope="world",
        # Regional Settings
        # Hide internal country borders to make continents look like solid blobs
        showcountries=not is_regional, 
        countrycolor="white",
        # Explicitly show coastlines in black so outer edges are visible against ocean
        showcoastlines=True, 
        coastlinecolor="black", 
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Poppins, Arial, sans-serif", color="#000000"),
    width=1600, height=1200, coloraxis_showscale=False, showlegend=False,
    margin=dict(t=0, b=0, l=0, r=0)
)

# Helper to calculate fill color to use as border color (Color Dissolve)
def add_calculated_colors(df, value_col, colorscale, min_val, max_val):
    if df.empty: return df
    
    # 1. Force numeric and handle NaNs/Infs
    # coerce errors to NaN, then fill with min_val (or 0) to avoid crashing sample_colorscale
    vals = pd.to_numeric(df[value_col], errors='coerce').fillna(min_val)
    
    # 2. Normalize
    denom = max_val - min_val
    if denom == 0:
        # Default to 0.0 (start of colorscale) if range is flat
        norm_vals = pd.Series(0.0, index=vals.index)
    else:
        norm_vals = (vals - min_val) / denom
    
    # 3. Clip to [0, 1] to prevent values > 1.0 (which cause the TypeError)
    norm_vals = norm_vals.clip(0, 1)
    
    # 4. Get colors
    # Ensure numpy array of floats
    sample_points = norm_vals.to_numpy(dtype=float)
    
    df['Calculated_Color'] = sample_colorscale(colorscale, sample_points)
    return df

# Helper for Microstates
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
    "Mauritius": {"lon": 57.5522, "lat": -20.3484}, "Comoros": {"lon": 43.8722, "lat": -11.6455},
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
    "Mayotte": {"lon": 45.1662, "lat": -12.8275}, "Reunion": {"lon": 55.5364, "lat": -21.1151},
    "Martinique": {"lon": -61.0242, "lat": 14.6415}, "Guadeloupe": {"lon": -61.5510, "lat": 16.2650},
    "Aruba": {"lon": -69.9683, "lat": 12.5211}, "Curacao": {"lon": -68.9335, "lat": 12.1696},
    "Sint Maarten": {"lon": -63.0548, "lat": 18.0425}, "Bonaire": {"lon": -68.2624, "lat": 12.2019},
    "Saba": {"lon": -63.2324, "lat": 17.6353}, "Sint Eustatius": {"lon": -62.9738, "lat": 17.4890},
    "Cook Islands": {"lon": -159.7777, "lat": -21.2367}, "Niue": {"lon": -169.8672, "lat": -19.0544},
    "Tokelau": {"lon": -171.8554, "lat": -9.2002}, "Cocos Islands": {"lon": 96.828333, "lat": -12.186944},
    "Christmas Island": {"lon": 105.6275, "lat": -10.49}, "Hong Kong": {"lon": 114.1095, "lat": 22.3964},
    "Macau": {"lon": 113.5439, "lat": 22.1987}, "Faroe Islands": {"lon": -6.9118, "lat": 61.8926},
    "Trinidad and Tobago": {"lon": -61.2225, "lat": 10.6918}, "Norfolk Island": {"lon": 167.95, "lat": -29.033333},
    "Easter Island": {"lon": -109.35, "lat": -27.12}, "Aland": {"lon": 20.366667, "lat": 60.25},
}

def get_microstate_trace(base_df, value_col, colorscale, zmin, zmax, hover_template, custom_data_cols, line_color_logic=False):
    micro_df = base_df[base_df["Country"].isin(microstates.keys())].copy()
    if micro_df.empty: return None
    micro_df["lat"] = micro_df["Country"].map(lambda x: microstates.get(x, {}).get("lat"))
    micro_df["lon"] = micro_df["Country"].map(lambda x: microstates.get(x, {}).get("lon"))
    
    marker_line_color = "black" 
    if line_color_logic: 
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

def add_us_subdivision_trace(fig, df_sub, color_col, colorscale, zmin, zmax, hover_template, custom_data_cols, marker_line_logic=None):
    if df_sub.empty: return
    trace_kwargs = dict(
        z=df_sub[color_col],
        colorscale=colorscale,
        zmin=zmin, zmax=zmax,
        text=df_sub['Hover_Name'],
        customdata=df_sub[custom_data_cols],
        hovertemplate=hover_template,
        showscale=False,
        locations=df_sub['ISO3'], 
        locationmode='USA-states'
    )
    if marker_line_logic:
        trace_kwargs['marker_line_color'] = df_sub[marker_line_logic]
        trace_kwargs['marker_line_width'] = 1.5
    else:
        trace_kwargs['marker_line_color'] = 'black'
        trace_kwargs['marker_line_width'] = 0.5 

    fig.add_trace(go.Choropleth(**trace_kwargs))


# --- 6. Visualization Logic ---

if map_metric == "Count":
    count_scale = [[0.0, "#fee6e6"], [1.0, "#db5049"]]
    max_count = map_data["Count"].max() if not map_data.empty else 1
    
    # Calculate colors for regional "Dissolve" effect
    if is_regional:
        world_data = add_calculated_colors(world_data, "Count", count_scale, 0, max_count)
        border_color = world_data['Calculated_Color']
        border_width = 1.0 
    else:
        border_color = "black"
        border_width = 0.5

    fig = px.choropleth(
        world_data, locations="ISO3", locationmode="ISO-3", color="Count",
        color_continuous_scale=count_scale, range_color=[0, max_count],
        hover_name="Hover_Name", hover_data={"ISO3": False, "Count": True, "Michael Selected": False, "Sarah Selected": False}
    )
    fig.update_traces(marker_line_color=border_color, marker_line_width=border_width)
    
    add_us_subdivision_trace(
        fig, us_data, "Count", count_scale, 0, max_count, 
        "<b>%{text}</b><br>Count: %{z}<extra></extra>", ["Count"]
    )
    ms_trace = get_microstate_trace(
        world_data, "Count", count_scale, 0, max_count, 
        "<b>%{text}</b><br>Count: %{customdata[0]}<extra></extra>", ["Count"]
    )
    if ms_trace: fig.add_trace(ms_trace)

    fig.update_layout(**layout_settings)
    st.plotly_chart(fig, use_container_width=True)

elif map_metric == "Comparison":
    comparison_scale = [[0.0, "#8a005c"], [0.5, "#f2f2f2"], [1.0, "#221e8f"]]

    def get_border_color(ratio):
        if ratio > 0.5: return "#221e8f"
        elif ratio < 0.5: return "#8a005c"
        else: return "#666666"

    # For Comparison, we dissolve borders if regional
    if is_regional:
        world_data = add_calculated_colors(world_data, "Michael Share Ratio", comparison_scale, 0.4, 0.6)
        world_data["BorderColor"] = world_data["Calculated_Color"]
        border_width = 1.0
    else:
        world_data["BorderColor"] = world_data["Michael Share Ratio"].apply(get_border_color)
        border_width = 1.5

    if not us_data.empty: 
        us_data["BorderColor"] = us_data["Michael Share Ratio"].apply(get_border_color)

    hover_template = (
        "<b>%{text}</b><br>" + f"Michael ({score_mode}): %{{customdata[0]:,.0f}}<br>" +
        f"Sarah ({score_mode}): %{{customdata[1]:,.0f}}<br>" + "Share: %{customdata[2]} vs %{customdata[3]}<extra></extra>"
    )
    custom_cols = ['Michael Selected', 'Sarah Selected', 'Michael Share %', 'Sarah Share %']

    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        locations=world_data['ISO3'], z=world_data['Michael Share Ratio'], locationmode='ISO-3',
        colorscale=comparison_scale, zmin=0.4, zmax=0.6,
        marker_line_color=world_data['BorderColor'], 
        marker_line_width=border_width,
        text=world_data['Hover_Name'], customdata=world_data[custom_cols], hovertemplate=hover_template, showscale=False
    ))
    
    add_us_subdivision_trace(
        fig, us_data, "Michael Share Ratio", comparison_scale, 0.4, 0.6,
        hover_template, custom_cols, marker_line_logic="BorderColor"
    )
    ms_trace = get_microstate_trace(
        world_data, "Michael Share Ratio", comparison_scale, 0.4, 0.6,
        hover_template, custom_cols, line_color_logic=True
    )
    if ms_trace: fig.add_trace(ms_trace)
    
    fig.update_layout(**layout_settings)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""
        <div style="text-align: center; font-weight: bold; margin-top: -10px;">
            <div style="display: flex; justify-content: center; align-items: center; gap: 20px; margin-bottom: 10px;">
                <span style="color: #ff94bd;">← Sarah Dominant</span>
                <span style="background: linear-gradient(90deg, #ff94bd, #bcb0ff); width: 200px; height: 10px; display: inline-block; border-radius: 5px;"></span>
                <span style="color: #bcb0ff;">Michael Dominant →</span>
            </div>
            <div style="font-size: 0.8em; color: #555;">*Comparing {score_mode}</div>
        </div>
        """, unsafe_allow_html=True)

elif map_metric == "Michael":
    michael_scale = [[0.0, "#e6e6ff"], [1.0, "#221e8f"]]
    
    if is_regional:
        world_data = add_calculated_colors(world_data, "Michael Efficiency", michael_scale, 0.5, 1.0)
        border_color = world_data['Calculated_Color']
        border_width = 1.0
    else:
        border_color = "black"
        border_width = 0.5

    hover_template = "<b>%{text}</b><br>Michael Eff %: %{customdata[0]}<br>Score: %{customdata[1]}<br>Count: %{customdata[2]}<extra></extra>"
    custom_cols = ["Michael Eff %", "Michael Selected", "Count"]

    fig = px.choropleth(
        world_data, locations="ISO3", locationmode="ISO-3", color="Michael Efficiency",
        color_continuous_scale=michael_scale, range_color=[0.5, 1],
        hover_name="Hover_Name", hover_data={"ISO3": False, "Michael Efficiency": False, "Michael Eff %": True, "Michael Selected": True, "Count": True}
    )
    fig.update_traces(marker_line_color=border_color, marker_line_width=border_width)
    
    add_us_subdivision_trace(
        fig, us_data, "Michael Efficiency", michael_scale, 0.5, 1.0,
        hover_template, custom_cols
    )
    ms_trace = get_microstate_trace(
        world_data, "Michael Efficiency", michael_scale, 0.5, 1.0,
        hover_template, custom_cols
    )
    if ms_trace: fig.add_trace(ms_trace)
    
    fig.update_layout(**layout_settings)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Showing Michael's **Efficiency**. Scale: 50%-100%.")

elif map_metric == "Sarah":
    sarah_scale = [[0.0, "#ffe6f2"], [1.0, "#8a005c"]]
    
    if is_regional:
        world_data = add_calculated_colors(world_data, "Sarah Efficiency", sarah_scale, 0.5, 1.0)
        border_color = world_data['Calculated_Color']
        border_width = 1.0
    else:
        border_color = "black"
        border_width = 0.5

    hover_template = "<b>%{text}</b><br>Sarah Eff %: %{customdata[0]}<br>Score: %{customdata[1]}<br>Count: %{customdata[2]}<extra></extra>"
    custom_cols = ["Sarah Eff %", "Sarah Selected", "Count"]

    fig = px.choropleth(
        world_data, locations="ISO3", locationmode="ISO-3", color="Sarah Efficiency",
        color_continuous_scale=sarah_scale, range_color=[0.5, 1],
        hover_name="Hover_Name", hover_data={"ISO3": False, "Sarah Efficiency": False, "Sarah Eff %": True, "Sarah Selected": True, "Count": True}
    )
    fig.update_traces(marker_line_color=border_color, marker_line_width=border_width)
    
    add_us_subdivision_trace(
        fig, us_data, "Sarah Efficiency", sarah_scale, 0.5, 1.0,
        hover_template, custom_cols
    )
    ms_trace = get_microstate_trace(
        world_data, "Sarah Efficiency", sarah_scale, 0.5, 1.0,
        hover_template, custom_cols
    )
    if ms_trace: fig.add_trace(ms_trace)
    
    fig.update_layout(**layout_settings)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Showing Sarah's **Efficiency**. Scale: 50%-100%.")


# --- 7. Single Summary Table ---
st.divider()
st.subheader(f"Statistics by {view_mode}")

table_cols = [locality_col, "Count", "Michael Selected", "Sarah Selected", "Total Possible"]
table_df = map_data[table_cols].drop_duplicates()
# Filter out "not found" values
table_df = table_df[table_df[locality_col] != "not found"]

table_df["Michael Efficiency"] = (table_df["Michael Selected"] / table_df["Total Possible"]) * 100
table_df["Sarah Efficiency"] = (table_df["Sarah Selected"] / table_df["Total Possible"]) * 100
table_df["% Better"] = table_df["Michael Efficiency"] - table_df["Sarah Efficiency"]
table_df = table_df.sort_values("Count", ascending=False)

display_df = table_df[[locality_col, "Count", "% Better", "Michael Efficiency", "Sarah Efficiency"]].copy()
display_df.columns = ["Locality", "Count", "% Better", "Michael % Gathered", "Sarah % Gathered"]

column_config = {
    "Locality": st.column_config.TextColumn("Location", width="medium"),
    "Count": st.column_config.NumberColumn("Games", format="%d"),
    "% Better": st.column_config.NumberColumn("% Better", format="%.1f%%"),
    "Michael % Gathered": st.column_config.ProgressColumn("Michael Efficiency", format="%.1f%%", min_value=0, max_value=100),
    "Sarah % Gathered": st.column_config.ProgressColumn("Sarah Efficiency", format="%.1f%%", min_value=0, max_value=100),
}

height = (len(display_df) + 1) * 35 + 3
st.dataframe(display_df, column_config=column_config, use_container_width=True, hide_index=True, height=height)