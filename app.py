import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_extras.stylable_container import stylable_container
import dataset
import detection
import disease_tracking  # New import
import team

# Setting page layout
st.set_page_config(
    page_title="BrewGuard", page_icon="🍃", layout="wide", initial_sidebar_state="auto"
)

# Define color schemes
THEME_COLORS = {
    "LIGHT": {
        "primaryColor": "#41B3A2",
        "backgroundColor": "#fdfdfe",
        "secondaryBackgroundColor": "#ffffff",
        "textColor": "#000000",
        "logo": "images/logo_light.png",
    },
    "DARK": {
        "primaryColor": "#00fecd",
        "backgroundColor": "#111827",
        "secondaryBackgroundColor": "#141b2a",
        "textColor": "#ffffff",
        "logo": "images/logo_dark.png",
    },
}

# Initialize session state for theme if not already set
if "dark_theme" not in st.session_state:
    st.session_state.dark_theme = False


# Function to get the current theme
def get_theme(is_dark_theme):
    theme = THEME_COLORS["DARK"] if is_dark_theme else THEME_COLORS["LIGHT"]
    for key, value in theme.items():
        st.config.set_option(f"theme.{key}", value)
    return theme


# Set the current theme based on session state
current_theme = get_theme(st.session_state.dark_theme)

# Apply theme using custom CSS
st.markdown(
    f"""
    <style>
        :root {{
            --primary-color: {current_theme["primaryColor"]};
            --background-color: {current_theme["backgroundColor"]};
            --secondary-background-color: {current_theme["secondaryBackgroundColor"]};
            --text-color: {current_theme["textColor"]};
        }}
        .stApp {{
            background-color: var(--background-color);
            color: var(--text-color);
        }}
        .sidebar .sidebar-content {{
            background-color: var(--secondary-background-color);
        }}
    </style>
""",
    unsafe_allow_html=True,
)

# Display the logo using st.image
st.logo(current_theme["logo"], size="large")

# Dynamic styles for option menu
menu_styles = {
    "container": {"padding": "0!important", "background-color": "transparent"},
    "icon": {"color": current_theme["primaryColor"], "font-size": "15px"},
    "nav-link": {
        "font-size": "1rem",
        "text-align": "center",
        "text-shadow": "2px 2px 4px rgba(0, 0, 0, 0.2)",
        "margin": "0px",
        "--hover-color": current_theme["secondaryBackgroundColor"],
        "font-family": "'Arial', 'sans-serif'",
        "color": current_theme["textColor"],
    },
    "nav-link-selected": {
        "color": current_theme["primaryColor"],
        "font-weight": "normal",
        "background-color": "transparent",
        "border-radius": "0px",
    },
}

# Navigation menu wrapped in stylable container
with stylable_container(
    key="menu_container",
    css_styles=f"""
        {{
        background-color: {current_theme["backgroundColor"]};
        margin-top: -40px;
        }}
    """,
):
    tab = option_menu(
        None,
        ["Home", "Dataset", "Map", "Team"],
        icons=["house", "database", "map", "people"],  # Added map icon
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles=menu_styles,
    )

# Content rendering based on selected tab
if tab == "Home":
    detection.main(THEME_COLORS)
elif tab == "Dataset":
    dataset.main()
elif tab == "Map":
    disease_tracking.main(THEME_COLORS)
elif tab == "Team":
    team.main(THEME_COLORS)
