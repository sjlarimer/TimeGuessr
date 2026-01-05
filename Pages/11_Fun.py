import streamlit as st
import pandas as pd
import numpy as np
import base64
import time
import io
from PIL import Image
from typing import List, Tuple
from pathlib import Path

# --- Configuration ---
st.set_page_config(page_title="Karaoke", layout="wide")

# --- Helper Functions for Background ---
def get_base64_image(image_path):
    """
    Encodes an image to a Base64 string.
    """
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
    """
    Injects CSS to set the background image with a white overlay.
    """
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

# --- Load Global CSS ---
try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# --- Custom Styling (Global + Karaoke Specific) ---
st.markdown(
    """
    <style>
        /* Global Font & Colors (Matching other pages) */
        .stMarkdown p, label, h1, h2, h3, h4, h5, h6, div {
            font-family: 'Poppins', sans-serif !important;
        }
        h1, h2, h3 {
            color: #db5049 !important;
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3 {
            color: white !important;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown p {
            color: #696761 !important;
        }

        /* Karaoke Specific Styles */
        .lyric-container {
            padding: 20px;
            background-color: rgba(255, 255, 255, 0.6);
            border-radius: 15px;
            margin-top: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            min-height: 200px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        .lyric-line {
            font-size: 1.3rem;
            color: #666;
            text-align: center;
            transition: all 0.3s ease-in-out;
            margin: 5px 0;
            opacity: 0.6;
        }
        .active-line {
            color: #db5049;
            font-weight: 800;
            font-size: 1.8rem;
            opacity: 1;
            transform: scale(1.05);
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Background Setup ---
image_file_path = "Images/Sarah5.jpg"
base64_img = get_base64_image(image_file_path)
if base64_img:
    set_lighter_background_image(base64_img, lightness_level=0.85)

# --- App Content ---
st.title("🎤 Karaoke Mode")

# --- Lyrics Data ---
lyrics: List[Tuple[int, str]] = [
    (9, "Nice to meet you, where you been?"),
    (11, "I could show you incredible things"),
    (14, "Magic, madness, heaven, sin"),
    (16, "Saw you there and I thought"),
    (19, "Oh, my God, look at that face"),
    (21, "You look like my next mistake"),
    (24, "Love's a game, wanna play?"),
    (29, "New money, suit and tie"),
    (31, "I can read you like a magazine"),
    (34, "Ain't it funny? Rumors fly"),
    (36, "And I know you heard about me"),
    (39, "So, hey, let's be friends"),
    (41, "I'm dying to see how this one ends"),
    (44, "Grab your passport and my hand"),
    (46, "I can make the bad guys good for a weekend"),
    (48, "So it's gonna be forever"),
    (51, "Or it's gonna go down in flames?"),
    (53, "You can tell me when it's over, mm"),
    (56, "If the high was worth the pain"),
    (58, "Got a long list of ex-lovers"),
    (61, "They'll tell you I'm insane"),
    (63, "'Cause you know I love the players"),
    (66, "And you love the game"),
    (68, "'Cause we're young and we're reckless"),
    (71, "We'll take this way too far"),
    (73, "It'll leave you breathless, mm"),
    (76, "Or with a nasty scar"),
    (78, "Got a long list of ex-lovers"),
    (81, "They'll tell you I'm insane"),
    (83, "But I've got a blank space, baby"),
    (86, "And I'll write your name"),
    (192, "And I'll write your name"),
]

# --- Control & Display ---
audio_placeholder = st.empty()
start_btn = st.button("Start Karaoke 🎤", type="primary")
placeholder = st.empty()

if start_btn:
    # 1. Start Audio (Autoplay)
    audio_placeholder.audio("Images/BlankSpace.mp3", format="audio/mp3", start_time=0, autoplay=True)
    
    # 2. Record the start time of the execution
    start_time = time.time()

    # --- Synchronization Loop ---
    for i, (t, line) in enumerate(lyrics):
        
        # Calculate time to wait until this specific line should appear
        current_time_offset = time.time() - start_time
        time_to_wait = t - current_time_offset
        
        if time_to_wait > 0:
            time.sleep(time_to_wait)
        
        # Determine surrounding lines for context
        # Show previous line, current line, next line
        display_html = "<div class='lyric-container'>"
        
        # Previous Line
        if i > 0:
            display_html += f"<div class='lyric-line'>{lyrics[i-1][1]}</div>"
            
        # Current Line (Active)
        display_html += f"<div class='lyric-line active-line'>{line}</div>"
        
        # Next Line
        if i < len(lyrics) - 1:
            display_html += f"<div class='lyric-line'>{lyrics[i+1][1]}</div>"
            
        display_html += "</div>"

        # Update the lyrics display
        placeholder.markdown(display_html, unsafe_allow_html=True)

        # Logic to hold the current line until the next one starts
        # This prevents the loop from racing if the 'time_to_wait' above was 0
        if i < len(lyrics) - 1:
            next_line_start = lyrics[i+1][0]
            # Calculate how long to keep this slide visible
            # We want to wait until the NEXT line's timestamp
            playhead = time.time() - start_time
            duration = next_line_start - playhead
            if duration > 0:
                 time.sleep(duration)
        else:
            time.sleep(5) # End of song buffer
            
    st.balloons()
    st.success("Karaoke finished! 🎤")
else:
    # Initial State
    # Note: We show a dormant audio player here just so the UI element is visible 
    # if the user wants to play manually without lyrics, but the button is the main interaction.
    # We leave the audio_placeholder empty until button press to force auto-play state.
    
    placeholder.markdown(
        """
        <div class='lyric-container'>
            <div class='lyric-line'>Hit 'Start Karaoke' to begin!</div>
            <div class='lyric-line active-line'>Ready for Blank Space?</div>
            <div class='lyric-line'>...</div>
        </div>
        """, 
        unsafe_allow_html=True
    )