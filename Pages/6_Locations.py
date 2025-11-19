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
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import country_converter as coco

st.markdown("## Locations")

# --- Load data ---
data = pd.read_csv("./Data/Timeguessr_Stats.csv")

# --- Count occurrences of each country ---
country_counts = data["Country"].value_counts().reset_index()
country_counts.columns = ["Country", "Count"]

# --- Define microstates with coordinates (countries/territories under 4000 km²) ---
microstates = {
    # # Europe
    "Vatican City": {"lon": 12.4534, "lat": 41.9029},
    "Monaco": {"lon": 7.4167, "lat": 43.7384},
    "San Marino": {"lon": 12.4578, "lat": 43.9424},
    "Liechtenstein": {"lon": 9.5215, "lat": 47.1410},
    "Malta": {"lon": 14.5146, "lat": 35.8989},
    "Andorra": {"lon": 1.5218, "lat": 42.5063},
    "Luxembourg": {"lon": 6.133333, "lat": 49.816667},
    
    # # Caribbean
    "Saint Kitts and Nevis": {"lon": -62.7830, "lat": 17.3578},
    "Saint Vincent and the Grenadines": {"lon": -61.2872, "lat": 13.2528},
    "Barbados": {"lon": -59.5432, "lat": 13.1939},
    "Antigua and Barbuda": {"lon": -61.7965, "lat": 17.0608},
    "Grenada": {"lon": -61.6790, "lat": 12.1165},
    "Saint Lucia": {"lon": -60.9789, "lat": 13.9094},
    "Dominica": {"lon": -61.3710, "lat": 15.4150},
    
    # # Pacific
    "Tonga": {"lon": -175.2018, "lat": -21.1790},
    "Kiribati": {"lon": -168.7340, "lat": 1.8709},
    "Palau": {"lon": 134.5825, "lat": 7.5150},
    "Nauru": {"lon": 166.9315, "lat": -0.5228},
    "Tuvalu": {"lon": 179.1942, "lat": -7.1095},
    "Marshall Islands": {"lon": 171.1845, "lat": 7.1315},
    "Micronesia": {"lon": 158.1625, "lat": 6.9248},
    "Samoa": {"lon": -172.1046, "lat": -13.7590},
    
    # # Asia/Middle East/Indian Ocean
    "Singapore": {"lon": 103.8198, "lat": 1.3521},
    "Bahrain": {"lon": 50.5577, "lat": 26.0667},
    "Maldives": {"lon": 73.2207, "lat": 3.2028},
    "Seychelles": {"lon": 55.4920, "lat": -4.6796},
    "Mauritius": {"lon": 57.5522, "lat": -20.3484},
    "Comoros": {"lon": 43.8722, "lat": -11.6455},
    
    # # Africa
    "Sao Tome and Principe": {"lon": 6.6131, "lat": 0.1864},
    "Cape Verde": {"lon": -24.0130, "lat": 16.5388},
    
    # # Territories (British)
    "British Virgin Islands": {"lon": -64.6399, "lat": 18.4207},
    "Anguilla": {"lon": -63.0686, "lat": 18.2206},
    "Bermuda": {"lon": -64.7505, "lat": 32.3078},
    "Cayman Islands": {"lon": -81.2546, "lat": 19.3133},
    "Turks and Caicos Islands": {"lon": -71.7979, "lat": 21.6940},
    "Montserrat": {"lon": -62.1874, "lat": 16.7425},
    "Gibraltar": {"lon": -5.3536, "lat": 36.1408},
    "Saint Helena": {"lon": -5.7089, "lat": -15.9650},
    "Isle of Man": {"lon": -4.5481, "lat": 54.2361},
    "Jersey": {"lon": -2.1358, "lat": 49.2144},
    "Guernsey": {"lon": -2.5857, "lat": 49.4657},
    
    # # Territories (US)
    "American Samoa": {"lon": -170.1322, "lat": -14.2710},
    "Guam": {"lon": 144.7937, "lat": 13.4443},
    "Northern Mariana Islands": {"lon": 145.6739, "lat": 15.0979},
    "US Virgin Islands": {"lon": -64.8963, "lat": 18.3358},
    
    # # Territories (French)
    "Saint Pierre and Miquelon": {"lon": -56.2711, "lat": 46.8852},
    "Wallis and Futuna": {"lon": -176.1761, "lat": -13.7687},
    "Saint Martin": {"lon": -63.0501, "lat": 18.0708},
    "Saint Barthelemy": {"lon": -62.8334, "lat": 17.9000},
    "French Polynesia": {"lon": -149.4068, "lat": -17.6797},
    "Mayotte": {"lon": 45.1662, "lat": -12.8275},
    "Reunion": {"lon": 55.5364, "lat": -21.1151},
    "Martinique": {"lon": -61.0242, "lat": 14.6415},
    "Guadeloupe": {"lon": -61.5510, "lat": 16.2650},
    
    # # Territories (Netherlands)
    "Aruba": {"lon": -69.9683, "lat": 12.5211},
    "Curacao": {"lon": -68.9335, "lat": 12.1696},
    "Sint Maarten": {"lon": -63.0548, "lat": 18.0425},
    "Bonaire": {"lon": -68.2624, "lat": 12.2019},
    "Saba": {"lon": -63.2324, "lat": 17.6353},
    "Sint Eustatius": {"lon": -62.9738, "lat": 17.4890},
    
    # # Territories (Other)
    "Cook Islands": {"lon": -159.7777, "lat": -21.2367},
    "Niue": {"lon": -169.8672, "lat": -19.0544},
    "Tokelau": {"lon": -171.8554, "lat": -9.2002},
    "Cocos Islands": {"lon": 96.828333, "lat": -12.186944},
    "Christmas Island": {"lon": 105.6275, "lat": -10.49},
    "Hong Kong": {"lon": 114.1095, "lat": 22.3964},
    "Macau": {"lon": 113.5439, "lat": 22.1987},
    "Faroe Islands": {"lon": -6.9118, "lat": 61.8926},
    "Trinidad and Tobago": {"lon": -61.2225, "lat": 10.6918},
    "Norfolk Island": {"lon": 167.95, "lat": -29.033333},
    "Easter Island": {"lon": -109.35, "lat": -27.12},
    "Aland": {"lon": 20.366667, "lat": 60.25},
}

# --- Prepare microstate data with colors (only for countries with data) ---
microstate_lons = []
microstate_lats = []
microstate_colors = []
microstate_texts = []

for country, coords in microstates.items():
    if country in country_counts["Country"].values:
        count = country_counts[country_counts["Country"] == country]["Count"].values[0]
        # Calculate color based on count using the same scale
        max_count = country_counts["Count"].max()
        color_ratio = count / max_count
        # Interpolate between light and dark red
        r = int(254 - (254 - 219) * color_ratio)
        g = int(230 - (230 - 80) * color_ratio)
        b = int(230 - (230 - 73) * color_ratio)
        
        microstate_lons.append(coords["lon"])
        microstate_lats.append(coords["lat"])
        microstate_colors.append(f'rgb({r},{g},{b})')
        microstate_texts.append(f"{country}<br>Count: {count}")

# --- Create custom red color scale ---
custom_red_scale = [
    (0.0, "#fee6e6"),
    (1.0, "#db5049")
]

# --- Create choropleth map ---
fig = px.choropleth(
    country_counts,
    locations="Country",
    locationmode="country names",
    color="Count",
    color_continuous_scale=custom_red_scale,
    projection="mercator"
)

# --- Add microstates as markers with fixed pixel size (only if there are any) ---
if microstate_lons:
    fig.add_trace(go.Scattergeo(
        lon=microstate_lons,
        lat=microstate_lats,
        text=microstate_texts,
        mode='markers',
        marker=dict(
            size=6,
            color=microstate_colors,
            line=dict(width=0.5, color='black'),
            sizemode='diameter'  # Fixed pixel size regardless of zoom
        ),
        showlegend=False,
        hoverinfo='text'
    ))

fig.update_layout(
    geo=dict(
        showframe=False,
        showcoastlines=False,
        bgcolor="#d9d7cc",
        lakecolor="#d9d7cc",
        showcountries=True,
        countrycolor="white",
        projection=dict(
            type="natural earth"
        ),
        lonaxis=dict(range=[-180, 180]),
        lataxis=dict(range=[-90, 90]),
    ),
    paper_bgcolor="#eae8dc",
    font=dict(family="Poppins, Arial, sans-serif", color="#000000"),
    width=1600,
    height=1000,
    coloraxis_showscale=False,  # Remove color legend
    showlegend=False,
    margin=dict(t=0, b=0, l=0, r=0)  # Remove all margins
)

st.plotly_chart(fig, use_container_width=True)

# --- Detect which countries Plotly can actually recognize ---
recognized = []
unrecognized = []

for country in country_counts["Country"]:
    iso = coco.convert(names=country, to='ISO3', not_found=None)
    if iso is None:
        unrecognized.append(country)
    else:
        recognized.append(country)

# --- Display missing ones ---
if unrecognized:
    st.markdown("### ⚠️ Unrecognized Countries")
    st.write(", ".join(sorted(unrecognized)))
else:
    st.markdown("✅ All countries recognized successfully!")



# --- Filter to rows where both Michael and Sarah Geography Scores are populated ---
subset = data.dropna(subset=["Michael Geography Score", "Sarah Geography Score"])

# --- Count appearances per country ---
country_counts = subset["Country"].value_counts().reset_index()
country_counts.columns = ["Country", "Appearances"]

# --- Sum Geography Scores per country ---
country_sums = subset.groupby("Country", as_index=False)[["Michael Geography Score", "Sarah Geography Score"]].sum()

# --- Merge counts with sums ---
country_stats = pd.merge(country_counts, country_sums, on="Country", how="left")

# --- Determine which score is higher ---
country_stats["Higher Score"] = country_stats.apply(
    lambda x: "Michael" if x["Michael Geography Score"] > x["Sarah Geography Score"]
    else ("Sarah" if x["Sarah Geography Score"] > x["Michael Geography Score"] else "Equal"),
    axis=1
)

# --- Calculate percent higher ---
def percent_higher(m, s):
    if m == s:
        return 0
    larger = max(m, s)
    smaller = min(m, s)
    return round((larger - smaller) / smaller * 100, 2) if smaller != 0 else None

country_stats["Percent Higher"] = country_stats.apply(
    lambda row: percent_higher(row["Michael Geography Score"], row["Sarah Geography Score"]), axis=1
)

# --- Determine continent automatically ---
cc = coco.CountryConverter()
country_stats["Continent"] = cc.convert(names=country_stats["Country"].tolist(), to="continent")

# --- Define nicer colors ---
continent_colors = {
    "Europe": "#00012e",          # Soft yellow
    "Asia": "#2e2200",            # Orange
    "Americas": "#002e02",         # Blue
    "Africa": "#2e0800",          # Red-orange
    "Oceania": "#2e0026",         # Purple
    "Antarctica": "#404040",      # Gray
    "Unknown": "#000000",
    "United States": "#002e29",             # Darker Blue
    "Other Americas": "#002e02"   # Green
}

def color_by_continent(row):
    return ['background-color: {}'.format(continent_colors.get(row.Continent, "#000000"))]*len(row)

# --- Display table by country ---
st.title("Geography Score Comparison by Country (Colored by Continent)")
st.dataframe(
    country_stats.style.apply(color_by_continent, axis=1).format({
        "Appearances": "{:,.0f}",
        "Michael Geography Score": "{:,.0f}",
        "Sarah Geography Score": "{:,.0f}",
        "Percent Higher": "{:.2f}%"
    })
)

# --- Continent aggregation including United States in Americas ---
continent_incl_us = country_stats.copy()
continent_incl_us["Continent_agg"] = continent_incl_us["Continent"].replace({"America": "Americas"})
continent_stats_incl_us = continent_incl_us.groupby("Continent_agg", as_index=False).agg({
    "Appearances": "sum",
    "Michael Geography Score": "sum",
    "Sarah Geography Score": "sum"
})
# Recalculate percent higher after aggregation
continent_stats_incl_us["Percent Higher"] = continent_stats_incl_us.apply(
    lambda row: percent_higher(row["Michael Geography Score"], row["Sarah Geography Score"]), axis=1
)
continent_stats_incl_us["Higher Score"] = continent_stats_incl_us.apply(
    lambda x: "Michael" if x["Michael Geography Score"] > x["Sarah Geography Score"]
    else ("Sarah" if x["Sarah Geography Score"] > x["Michael Geography Score"] else "Equal"),
    axis=1
)

st.title("Geography Score Comparison by Continent (Including United States in Americas)")
st.dataframe(
    continent_stats_incl_us.style.apply(
        lambda row: ['background-color: {}'.format(continent_colors.get(row.Continent_agg, "#FFFFFF"))]*len(row),
        axis=1
    ).format({
        "Appearances": "{:,.0f}",
        "Michael Geography Score": "{:,.0f}",
        "Sarah Geography Score": "{:,.0f}",
        "Percent Higher": "{:.2f}%"
    })
)

# --- Continent aggregation excluding United States ---
def continent_split_americas(row):
    if row["Country"] == "United States":
        return "United States"
    elif row["Continent"] == "America":
        return "Other Americas"
    else:
        return row["Continent"]

continent_excl_us = country_stats.copy()
continent_excl_us["Continent_agg"] = continent_excl_us.apply(continent_split_americas, axis=1)
continent_stats_excl_us = continent_excl_us.groupby("Continent_agg", as_index=False).agg({
    "Appearances": "sum",
    "Michael Geography Score": "sum",
    "Sarah Geography Score": "sum"
})
# Recalculate percent higher after aggregation
continent_stats_excl_us["Percent Higher"] = continent_stats_excl_us.apply(
    lambda row: percent_higher(row["Michael Geography Score"], row["Sarah Geography Score"]), axis=1
)
continent_stats_excl_us["Higher Score"] = continent_stats_excl_us.apply(
    lambda x: "Michael" if x["Michael Geography Score"] > x["Sarah Geography Score"]
    else ("Sarah" if x["Sarah Geography Score"] > x["Michael Geography Score"] else "Equal"),
    axis=1
)

st.title("Geography Score Comparison by Continent (Excluding United States from Americas)")
st.dataframe(
    continent_stats_excl_us.style.apply(
        lambda row: ['background-color: {}'.format(continent_colors.get(row.Continent_agg, "#FFFFFF"))]*len(row),
        axis=1
    ).format({
        "Appearances": "{:,.0f}",
        "Michael Geography Score": "{:,.0f}",
        "Sarah Geography Score": "{:,.0f}",
        "Percent Higher": "{:.2f}%"
    })
)











# --- Filter to rows where both Michael and Sarah Time Scores are populated ---
subset = data.dropna(subset=["Michael Time Score", "Sarah Time Score"])

# --- Count appearances per country ---
country_counts = subset["Country"].value_counts().reset_index()
country_counts.columns = ["Country", "Appearances"]

# --- Sum Time Scores per country ---
country_sums = subset.groupby("Country", as_index=False)[["Michael Time Score", "Sarah Time Score"]].sum()

# --- Merge counts with sums ---
country_stats = pd.merge(country_counts, country_sums, on="Country", how="left")

# --- Determine which score is higher ---
country_stats["Higher Score"] = country_stats.apply(
    lambda x: "Michael" if x["Michael Time Score"] > x["Sarah Time Score"]
    else ("Sarah" if x["Sarah Time Score"] > x["Michael Time Score"] else "Equal"),
    axis=1
)

# --- Calculate percent higher ---
def percent_higher(m, s):
    if m == s:
        return 0
    larger = max(m, s)
    smaller = min(m, s)
    return round((larger - smaller) / smaller * 100, 2) if smaller != 0 else None

country_stats["Percent Higher"] = country_stats.apply(
    lambda row: percent_higher(row["Michael Time Score"], row["Sarah Time Score"]), axis=1
)

# --- Determine continent automatically ---
cc = coco.CountryConverter()
country_stats["Continent"] = cc.convert(names=country_stats["Country"].tolist(), to="continent")

# --- Define nicer colors ---
continent_colors = {
    "Europe": "#00012e",          # Soft yellow
    "Asia": "#2e2200",            # Orange
    "Americas": "#002e02",         # Blue
    "Africa": "#2e0800",          # Red-orange
    "Oceania": "#2e0026",         # Purple
    "Antarctica": "#404040",      # Gray
    "Unknown": "#000000",
    "United States": "#002e29",             # Darker Blue
    "Other Americas": "#002e02"   # Green
}

def color_by_continent(row):
    return ['background-color: {}'.format(continent_colors.get(row.Continent, "#000000"))]*len(row)

# --- Display table by country ---
st.title("Time Score Comparison by Country (Colored by Continent)")
st.dataframe(
    country_stats.style.apply(color_by_continent, axis=1).format({
        "Appearances": "{:,.0f}",
        "Michael Time Score": "{:,.0f}",
        "Sarah Time Score": "{:,.0f}",
        "Percent Higher": "{:.2f}%"
    })
)

# --- Continent aggregation including United States in Americas ---
continent_incl_us = country_stats.copy()
continent_incl_us["Continent_agg"] = continent_incl_us["Continent"].replace({"America": "Americas"})
continent_stats_incl_us = continent_incl_us.groupby("Continent_agg", as_index=False).agg({
    "Appearances": "sum",
    "Michael Time Score": "sum",
    "Sarah Time Score": "sum"
})
# Recalculate percent higher after aggregation
continent_stats_incl_us["Percent Higher"] = continent_stats_incl_us.apply(
    lambda row: percent_higher(row["Michael Time Score"], row["Sarah Time Score"]), axis=1
)
continent_stats_incl_us["Higher Score"] = continent_stats_incl_us.apply(
    lambda x: "Michael" if x["Michael Time Score"] > x["Sarah Time Score"]
    else ("Sarah" if x["Sarah Time Score"] > x["Michael Time Score"] else "Equal"),
    axis=1
)

st.title("Time Score Comparison by Continent (Including United States in Americas)")
st.dataframe(
    continent_stats_incl_us.style.apply(
        lambda row: ['background-color: {}'.format(continent_colors.get(row.Continent_agg, "#FFFFFF"))]*len(row),
        axis=1
    ).format({
        "Appearances": "{:,.0f}",
        "Michael Time Score": "{:,.0f}",
        "Sarah Time Score": "{:,.0f}",
        "Percent Higher": "{:.2f}%"
    })
)

# --- Continent aggregation excluding United States ---
def continent_split_americas(row):
    if row["Country"] == "United States":
        return "United States"
    elif row["Continent"] == "America":
        return "Other Americas"
    else:
        return row["Continent"]

continent_excl_us = country_stats.copy()
continent_excl_us["Continent_agg"] = continent_excl_us.apply(continent_split_americas, axis=1)
continent_stats_excl_us = continent_excl_us.groupby("Continent_agg", as_index=False).agg({
    "Appearances": "sum",
    "Michael Time Score": "sum",
    "Sarah Time Score": "sum"
})
# Recalculate percent higher after aggregation
continent_stats_excl_us["Percent Higher"] = continent_stats_excl_us.apply(
    lambda row: percent_higher(row["Michael Time Score"], row["Sarah Time Score"]), axis=1
)
continent_stats_excl_us["Higher Score"] = continent_stats_excl_us.apply(
    lambda x: "Michael" if x["Michael Time Score"] > x["Sarah Time Score"]
    else ("Sarah" if x["Sarah Time Score"] > x["Michael Time Score"] else "Equal"),
    axis=1
)

st.title("Time Score Comparison by Continent (Excluding United States from Americas)")
st.dataframe(
    continent_stats_excl_us.style.apply(
        lambda row: ['background-color: {}'.format(continent_colors.get(row.Continent_agg, "#FFFFFF"))]*len(row),
        axis=1
    ).format({
        "Appearances": "{:,.0f}",
        "Michael Time Score": "{:,.0f}",
        "Sarah Time Score": "{:,.0f}",
        "Percent Higher": "{:.2f}%"
    })
)