import streamlit as st
import base64
from PIL import Image

def get_base64_image(image_path):
    """Encodes an image to a Base64 string."""
    try:
        # Save the PIL image to a buffer before encoding
        img = Image.open(image_path)
        # Convert to PNG buffer (good for transparency)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    except FileNotFoundError:
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

image_file_path = "Images/Sarah.jpg"

# 1. Get the base64 string
base64_img = get_base64_image(image_file_path)

# 2. Inject the CSS with a 70% lightness overlay
# Try adjusting the second argument (e.g., 0.3 for slightly lighter, 0.9 for very light)
set_lighter_background_image(base64_img, lightness_level=0.7)

import streamlit as st
import time
from typing import List, Tuple

# --- App Title ---
st.title("🎤 Streamlit Karaoke Demo (Simplified Auto-Sync)")
st.markdown("---")

# --- 2. Timed lyric lines (Adjusted Timings) ---
lyrics: List[Tuple[int, str]] = [
    # ... (Your original lyrics list)
    (9, "Nice to meet you, where you been?"),
    (12, "I could show you incredible things"),
    (14, "Magic, madness, heaven, sin"),
    (17, "Saw you there and I thought"),
    (19, "Oh, my God, look at that face"),
    (21, "You look like my next mistake"),
    (24, "Love's a game, wanna play?"),
    (29, "New money, suit and tie"),
    (32, "I can read you like a magazine"),
    (34, "Ain't it funny? Rumors fly"),
    (37, "And I know you heard about me"),
    (39, "So, hey, let's be friends"),
    (41, "I'm dying to see how this one ends"),
    (44, "Grab your passport and my hand"),
    (46, "I can make the bad guys good for a weekend"),

    # Chorus
    (48, "So it's gonna be forever"),
    (50, "Or it's gonna go down in flames?"),
    (50, "You can tell me when it's over, mm"),
    (52, "If the high was worth the pain"),
    (54, "Got a long list of ex-lovers"),
    (56, "They'll tell you I'm insane"),
    (58, "'Cause you know I love the players"),
    (60, "And you love the game"),
    (62, "'Cause we're young and we're reckless"),
    (64, "We'll take this way too far"),
    (66, "It'll leave you breathless, mm"),
    (68, "Or with a nasty scar"),
    (70, "Got a long list of ex-lovers"),
    (72, "They'll tell you I'm insane"),
    (74, "But I've got a blank space, baby"),
    (76, "And I'll write your name"),
    
    # ... (Rest of the lyrics)
    (192, "And I'll write your name"),
]

# --- 3. CSS for highlighted lyric display ---
st.markdown(
    """
    <style>
    .lyric-line {
        font-size: 1.3rem;
        font-family: 'Poppins', sans-serif;
        color: #666;
        text-align: center;
        transition: all 0.3s ease-in-out;
    }
    .active-line {
        color: #db5049;
        font-weight: 700;
        font-size: 1.6rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 4. Audio Player (Must be manually started by user) ---

st.audio("./Images/BlankSpace.mp3", start_time=0) 

placeholder = st.empty()

# Record the start time of the Python script execution (when the page loaded)
start_time = time.time()

# --- Synchronization Logic ---
# The script will run through all the lyrics sequentially based on the timer,
# assuming the user hits play on the audio player around the same time
# the app starts running.

for i, (t, line) in enumerate(lyrics):
    
    # Calculate time to wait until next line
    next_line_time = lyrics[i + 1][0] if i + 1 < len(lyrics) else None

    # Wait for the correct moment (t) based on the absolute start time
    current_time_offset = time.time() - start_time
    time_to_wait = t - current_time_offset
    
    if time_to_wait > 0:
        # Wait for the specific duration to reach the next lyric time (t)
        time.sleep(time_to_wait)
    
    # Display Logic
    display = ""
    display_lines = lyrics[max(0, i-1) : i+2]
    
    for start_t, txt in display_lines:
        active = (start_t == t)
        display += f"<div class='lyric-line {'active-line' if active else ''}'>{txt}</div>"

    # Update the lyrics display
    placeholder.markdown(display, unsafe_allow_html=True)

    # Wait for the duration of the current line
    if next_line_time:
        expected_end_time = start_time + next_line_time
        time_to_wait_for_line_duration = expected_end_time - time.time()
        
        if time_to_wait_for_line_duration > 0:
            time.sleep(time_to_wait_for_line_duration)
    else:
        time.sleep(5)
        
# Karaoke finished
placeholder.empty()
st.success("Karaoke finished! Thanks for singing! 🎤")