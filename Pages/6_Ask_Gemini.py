import streamlit as st
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import requests
import json

st.title("Ask Gemini!")

# --- Ask user for API Key ---
api_key = st.text_input("Enter your Gemini API Key:", type="password")
if not api_key:
    st.warning("Please enter your Gemini API key to use the app.")
    st.stop()  # Stop execution until API key is provided

# List of all columns required for filtering and transformation
required_cols = [
    'City', 'Country', 'Year',
    'Michael Time Distance', 'Michael Geography Distance', 'Michael Time Guessed',
    'Sarah Time Distance', 'Sarah Geography Distance', 'Sarah Time Guessed'
]

data = pd.read_csv("./Data/Timeguessr_Stats.csv")

# 1. Subset to include rows where all required columns are populated, and then select those columns
data_subset = data.dropna(subset=required_cols)
data_subset = data_subset[required_cols].copy()

# 2. Store raw 'Distance' values in temporary columns
data_subset['Michael Time Distance Raw'] = data_subset['Michael Time Distance'].astype(str)
data_subset['Sarah Time Distance Raw'] = data_subset['Sarah Time Distance'].astype(str)
data_subset['Michael Geography Distance Raw'] = data_subset['Michael Geography Distance'].astype(str)
data_subset['Sarah Geography Distance Raw'] = data_subset['Sarah Geography Distance'].astype(str)

# --- 3. APPLY NEW FORMAT TO TIME DISTANCE COLUMNS ---
# Format: ____ Guessed {Time Guessed}, which was {Time Distance} Years off from the actual year

# Michael Time Distance
data_subset['Michael Time Distance'] = (
    'Michael Guessed ' +
    data_subset['Michael Time Guessed'].astype(str) +
    ', which was ' +
    data_subset['Michael Time Distance Raw'] +
    ' Years off from the actual year'
)

# Sarah Time Distance
data_subset['Sarah Time Distance'] = (
    'Sarah Guessed ' +
    data_subset['Sarah Time Guessed'].astype(str) +
    ', which was ' +
    data_subset['Sarah Time Distance Raw'] +
    ' Years off from the actual year'
)

# --- 4. APPLY ORIGINAL FORMAT TO GEOGRAPHY DISTANCE COLUMNS ---
# Format: ____ Guessed _____ meters off
data_subset['Michael Geography Distance'] = (
    'Michael Guessed ' + data_subset['Michael Geography Distance Raw'] + ' meters off'
)
data_subset['Sarah Geography Distance'] = (
    'Sarah Guessed ' + data_subset['Sarah Geography Distance Raw'] + ' meters off'
)

# 5. Drop temporary raw columns and the original 'Time Guessed' columns (as they are now incorporated into Time Distance)
data_subset = data_subset.drop(columns=[
    'Michael Time Distance Raw',
    'Sarah Time Distance Raw',
    'Michael Geography Distance Raw',
    'Sarah Geography Distance Raw',
    'Michael Time Guessed',
    'Sarah Time Guessed'
])

# 6. Convert the resulting DataFrame to JSON
json_output = data_subset.to_json(orient='records', indent=4)

# Print the JSON output
print(json_output)

# Initialize a variable in session state
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# Text input
input_text = st.text_input("Enter your question:")

# Submit button
if st.button("Submit"):
    st.session_state.user_input = input_text

# --- Gemini API call ---
def query_gemini(prompt: str, api_key: str):
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite-preview-06-17:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = {
        "prompt": {"text": prompt},
        "temperature": 0.2,
        "candidate_count": 1
    }
    response = requests.post(api_url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        result_json = response.json()
        return result_json['candidates'][0]['content'][0]['text']
    else:
        return f"Error {response.status_code}: {response.text}"

# --- Generate prompt and show output ---
if st.session_state.user_input:
    prompt_text = f"""
You are an AI data analyst specialized in competitive gaming statistics, geography, and history.

**Your Task:**
The JSON below contains data regarding the guess accuracy of players Michael and Sarah. The data includes the actual location/year of the answer, and the guesses/distances for two players, Michael and Sarah.

**Specific Deliverables:**
{st.session_state.user_input}

**THE DATASET (JSON FORMAT):**
```json
{json_output}
"""
st.markdown("### Generated Answer")
with st.spinner("Querying Gemini 2.5 Flash-Lite..."):
    gemini_response = query_gemini(prompt_text, api_key)
st.markdown("### Gemini Response")
st.text(gemini_response)