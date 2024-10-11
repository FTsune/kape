import streamlit as st
from streamlit_option_menu import option_menu
import leaf
import disease
import detection
import team

# Setting page layout
st.set_page_config(
    page_title="Coffee Leaf Classification and Disease Detection",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Define color schemes
THEME_COLORS = {
    "LIGHT": {
        "primaryColor": "#41B3A2",
        "backgroundColor": "white",
        "secondaryBackgroundColor": "#fafafa",
        "textColor": "black"
    },
    "DARK": {
        "primaryColor": "#00fecd",
        "backgroundColor": "#111827",
        "secondaryBackgroundColor": "#141b2a",
        "textColor": "white"
    }
}

# Initialize session state for theme if not already set
if 'dark_theme' not in st.session_state:
    st.session_state.dark_theme = False

# Function to set theme
def set_theme(is_dark_theme):
    theme = THEME_COLORS["DARK"] if is_dark_theme else THEME_COLORS["LIGHT"]
    for key, value in theme.items():
        st.config.set_option(f"theme.{key}", value)
    return theme

# Set the current theme based on session state
current_theme = set_theme(st.session_state.dark_theme)

# Dynamic styles for option menu
menu_styles = {
    "container": {"padding": "0!important", "background-color": "transparent"},
    "icon": {"color": current_theme["primaryColor"], "font-size": "15px"},
    "nav-link": {
        "font-size": "14px",
        "text-align": "center",
        "text-shadow": "2px 2px 4px rgba(0, 0, 0, 0.2)",
        "margin": "0px",
        "--hover-color": current_theme["secondaryBackgroundColor"],
        "font-family": "'Arial', 'sans-serif'",
        "color": current_theme["textColor"]
    },
    "nav-link-selected": {
        "color": current_theme["primaryColor"],
        "font-weight": "normal",
        "background-color": "transparent",
        "border-radius": "0px"
    }
}

# Navigation menu
tab = option_menu(
    None,
    ["Home", "Leaf", "Disease", 'Team'],
    icons=['house', 'feather', "virus", 'people'],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles=menu_styles
)

# Content rendering based on selected tab
if tab == 'Home':
    detection.main(THEME_COLORS)
elif tab == 'Leaf':
    leaf.main()
elif tab == 'Disease':
    disease.main()
elif tab == 'Team':
    team.main(THEME_COLORS)

# Force a rerun if the theme has changed
if 'previous_theme' not in st.session_state or st.session_state.previous_theme != st.session_state.dark_theme:
    st.session_state.previous_theme = st.session_state.dark_theme
    st.rerun()