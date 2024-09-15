# External packages
import streamlit as st
import streamlit_shadcn_ui as ui
from streamlit_option_menu import option_menu
import hydralit_components as hc

# Additional Page
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

# menu_data = [
#     {'icon': 'bi bi-house', 'label': "Home"},
#     {'icon': "bi bi-mouse", 'label': "Leaf"},
#     {'icon': "bi bi-radioactive", 'label': "Disease"},
#     {'icon': "bi bi-people", 'label': "Team"},
# ]

# # Define the theme customization
# over_theme = {
#     'txc_inactive': 'white',  # Inactive text color
#     'menu_background': '000000',  # Background color for the navbar
#     'txc_active': '#00fecd',  # Active text color
#     'menu_border': 'white',
# }

# # Create the navbar
# menu_id = hc.nav_bar(
#     menu_definition=menu_data,
#     override_theme=over_theme,
#     hide_streamlit_markers=True,  # will show the st hamburger as well as the navbar now!
#     sticky_nav=True,  # at the top or not
#     sticky_mode='not-jumpy',  # jumpy or not-jumpy, but sticky or pinned
# )

st.markdown(
    """
    <style>
    [data-testid="stHeader"] {
        display: none;
    }
    [data-testid="stToolbar"] {
        display: none;
    }
    .main .block-container {
        padding-top: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Adjust the container styling to move the option menu to the top
st.markdown(
    """
    <style>
    .menu-container {
        margin-top: 0 !important;
        padding-top: 20px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


tab = option_menu(None, ["HOME", "LEAF", "DISEASE", 'TEAM'], 
    icons=['house', 'mouse', "virus", 'people'], 
    menu_icon="cast", 
    default_index=0, 
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important",  "background-color": "#111827"},
        "icon": {"color": "#00fecd", "font-size": "15px"}, 
        "nav-link": {"font-size": "14px", 
                     "text-align": "center", 
                     "margin":"0px", "--hover-color": "#1f2937",
                     "font-family": "'Arial', 'sans-serif'"},
        "nav-link-selected": {"color": "#00fecd",
                              "font-weight": "normal", 
                              "background-color": "#111827", 
                              "border": "2px solid #00fecd", 
                              "border-radius": "0px"}
    })

if tab == 'HOME':
    detection.main()

elif tab == 'LEAF':
    leaf.main()

elif tab == 'DISEASE':
    disease.main()

elif tab == 'TEAM':
    team.main()
    