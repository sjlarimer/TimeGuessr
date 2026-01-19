import streamlit as st
import streamlit.components.v1 as components
import base64
import time
import io
from PIL import Image
from typing import List, Tuple

# --- Configuration ---
st.set_page_config(page_title="Karaoke Speed Challenge", layout="wide")

# --- Helper Functions for Background ---
def get_base64_image(image_path):
    try:
        img = Image.open(image_path)
        file_format = img.format if img.format is not None else 'PNG'
        buffer = io.BytesIO()
        img.save(buffer, format=file_format)
        return base64.b64encode(buffer.getvalue()).decode()
    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"Error loading background: {e}")
        return None

def set_lighter_background_image(base64_string, lightness_level=0.7):
    if not base64_string: return
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

# --- Custom Styling ---
st.markdown(
    """
    <style>
        .stMarkdown p, label, h1, h2, h3, h4, h5, h6, div {
            font-family: 'Poppins', sans-serif !important;
        }
        h1, h2, h3 { color: #db5049 !important; }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: white !important; }
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown p { color: #696761 !important; }

        /* Karaoke Specific Styles */
        .lyric-container {
            padding: 20px;
            background-color: rgba(255, 255, 255, 0.65);
            border-radius: 15px;
            margin-top: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            min-height: 250px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            border: 1px solid rgba(255, 255, 255, 0.8);
        }
        .lyric-line {
            font-size: 1.3rem;
            color: #666;
            text-align: center;
            transition: all 0.2s ease-in-out;
            margin: 5px 0;
            opacity: 0.5;
        }
        .active-line {
            color: #db5049;
            font-weight: 800;
            font-size: 2.2rem;
            opacity: 1;
            transform: scale(1.05);
            text-shadow: 0 2px 4px rgba(0,0,0,0.15);
            margin: 15px 0;
        }
        .speed-indicator {
            font-size: 0.9rem;
            color: #221e8f;
            font-weight: 600;
            margin-top: 15px;
            padding: 5px 10px;
            background: rgba(255,255,255,0.8);
            border-radius: 20px;
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
st.title("🎤 Karaoke Challenge: Speed Up!")
st.markdown("The song gets **5% faster** after every line. Good luck keeping up!")

# --- Lyrics Data (Original Timestamps) ---
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
    (89, "Cherry lips, crystal skies"),
    (92, "I could show you incredible things"),
    (94, "Stolen kisses, pretty lies"),
    (97, "You're the King, baby, I'm your Queen"),
    (99, "Find out what you want"),
    (102, "Be that girl for a month"),
    (104, "Wait, the worst is yet to come, oh, no"),
    (107, "Screaming, crying, perfect storms"),
    (110, "I can make all the tables turn"),
    (112, "Rose garden filled with thorns"),
    (115, "Keep you second guessing like"),
    (117, "\"Oh, my God, who is she?\""),
    (120, "I get drunk on jealousy"),
    (122, "But you'll come back each time you leave"),
    (125, "'Cause, darling, I'm a nightmare dressed like a daydream"),
    (128, "So it's gonna be forever"),
    (130, "Or it's gonna go down in flames?"),
    (133, "You can tell me when it's over, mm"),
    (135, "If the high was worth the pain"),
    (137, "Got a long list of ex-lovers"),
    (140, "They'll tell you I'm insane"),
    (142, "'Cause you know I love the players"),
    (144, "And you love the game"),
    (146, "'Cause we're young and we're reckless"),
    (149, "We'll take this way too far"),
    (151, "It'll leave you breathless, mm"),
    (153, "Or with a nasty scar"),
    (155, "Got a long list of ex-lovers"),
    (158, "They'll tell you I'm insane"),
    (160, "But I've got a blank space, baby"),
    (162, "And I'll write your name"),
    (164, "Boys only want love if it's torture"),
    (169, "Don't say I didn't, say I didn't warn ya"),
    (174, "Boys only want love if it's torture"),
    (179, "Don't say I didn't, say I didn't warn ya"),
    (184, "So it's gonna be forever"),
    (186, "Or it's gonna go down in flames?"),
    (189, "You can tell me when it's over, mm"),
    (191, "If the high was worth the pain"),
    (193, "Got a long list of ex-lovers"),
    (196, "They'll tell you I'm insane"),
    (198, "'Cause you know I love the players"),
    (200, "And you love the game"),
    (202, "'Cause we're young and we're reckless"),
    (205, "We'll take this way too far"),
    (207, "It'll leave you breathless, mm"),
    (209, "Or with a nasty scar"),
    (211, "Got a long list of ex-lovers"),
    (214, "They'll tell you I'm insane"),
    (216, "But I've got a blank space, baby"),
    (219, "And I'll write your name"),
]

# --- Control & Display ---
audio_container = st.empty()
start_btn = st.button("Start Karaoke 🎤", type="primary")
placeholder = st.empty()

# Hidden div to hold JS injection to prevent layout shifts
js_placeholder = st.empty()

if start_btn:
    # 1. Start Audio (Autoplay)
    audio_container.audio("Images/BlankSpace.mp3", format="audio/mp3", start_time=0, autoplay=True)
    
    current_playback_rate = 1.0
    last_lyric_time = 0.0
    
    # Initial wait for the first line (at normal speed)
    # Note: Streamlit execution overhead might cause a slight initial offset, usually negligible for this demo
    
    # --- Synchronization Loop ---
    for i, (original_time, line) in enumerate(lyrics):
        
        # Calculate the interval in "song time" between this line and the previous anchor
        song_interval = original_time - last_lyric_time
        
        # Calculate how long to wait in "real time" given the CURRENT playback rate
        real_wait_time = song_interval / current_playback_rate
        
        # Wait
        if real_wait_time > 0:
            time.sleep(real_wait_time)
            
        # Update Anchor
        last_lyric_time = original_time

        # --- Display Lyrics ---
        display_html = "<div class='lyric-container'>"
        
        # Previous Line
        if i > 0:
            display_html += f"<div class='lyric-line'>{lyrics[i-1][1]}</div>"
            
        # Current Line (Active)
        display_html += f"<div class='lyric-line active-line'>{line}</div>"
        
        # Next Line
        if i < len(lyrics) - 1:
            display_html += f"<div class='lyric-line'>{lyrics[i+1][1]}</div>"
        
        display_html += f"<div class='speed-indicator'>🚀 Current Speed: {current_playback_rate:.2f}x</div>"
        display_html += "</div>"

        placeholder.markdown(display_html, unsafe_allow_html=True)
        
        # --- Increase Speed ---
        current_playback_rate *= 1.05
        
        # Inject JS to speed up audio element in the parent window
        js_code = f"""
        <script>
            var audio = window.parent.document.querySelector('audio');
            if (audio) {{
                audio.playbackRate = {current_playback_rate};
            }}
        </script>
        """
        # FIX: Use context manager for empty container
        with js_placeholder:
            components.html(js_code, height=0, width=0)

    st.balloons()
    st.success(f"Final Speed: {current_playback_rate:.2f}x! 🏎️")

else:
    # Initial State
    placeholder.markdown(
        """
        <div class='lyric-container'>
            <div class='lyric-line'>Hit 'Start Karaoke' to begin!</div>
            <div class='lyric-line active-line'>Ready for Blank Space?</div>
            <div class='lyric-line'>It gets faster every line...</div>
        </div>
        """, 
        unsafe_allow_html=True
    )