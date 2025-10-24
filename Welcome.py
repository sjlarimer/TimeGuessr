import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout='wide')

st.title("Welcome to Michael & Sarah's TimeGuessr score tracking")

st.markdown("""## Overview""")
st.markdown("Timeguessr is a geography and history based game. The link can be found [here](https://timeguessr.com/)")

col1, col2 = st.columns(2)
with col1:
    st.image("Images/home.png")
with col2:
    st.image("Images/Results.png")

st.markdown("""## Data""")
data = pd.read_csv("./Data/Timeguessr_Stats_Final.csv")
st.dataframe(data)