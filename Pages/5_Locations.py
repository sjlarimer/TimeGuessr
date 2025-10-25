import streamlit as st
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
import plotly.express as px

st.markdown("## Locations")

# --- Load data ---
data = pd.read_csv("./Data/Timeguessr_Stats_Final.csv")

# --- Count occurrences of each country ---
country_counts = data["Country"].value_counts().reset_index()
country_counts.columns = ["Country", "Count"]

# --- Create custom red color scale (light -> #db5049) ---
custom_red_scale = [
    (0.0, "#fee6e6"),  # very light red for low counts
    (1.0, "#db5049")   # your desired strong red for high counts
]

# --- Create choropleth map ---
fig = px.choropleth(
    country_counts,
    locations="Country",
    locationmode="country names",
    color="Count",
    color_continuous_scale=custom_red_scale,
    title="Number of Appearances per Country",
    projection="mercator"
)

fig.update_layout(
    geo=dict(
        showframe=False,
        showcoastlines=False,
        bgcolor="#d9d7cc",
        lakecolor="#d9d7cc",
        landcolor=None,
        showcountries=True,
        countrycolor="white",
        center=dict(lat=20, lon=0),
        projection=dict(
            type="mercator",
            scale=1.1,    # zooms the map
            # optional: stretch longitude
        ),
        lonaxis=dict(range=[-180, 180]),  # keep full world horizontally
        lataxis=dict(range=[-60, 90]),    # adjust lat range if needed
    ),
    paper_bgcolor="#eae8dc",
    font=dict(family="Poppins, Arial, sans-serif", color="#000000"),
    title_x=0.5,
    width=1600,
    height=1000,
)
# --- Display map ---
st.plotly_chart(fig, use_container_width=True)

# --- Identify unrecognized countries ---
recognized_countries = set(fig.data[0]["locations"])
all_countries = set(country_counts["Country"])
unrecognized = sorted(all_countries - recognized_countries)

# --- Display missing ones, if any ---
if unrecognized:
    st.markdown("### ⚠️ Unrecognized Countries")
    st.write(", ".join(unrecognized))