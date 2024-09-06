# External packages
import streamlit as st
import streamlit_shadcn_ui as ui
from streamlit_option_menu import option_menu

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
    initial_sidebar_state="expanded"
)

tab = option_menu(None, ["HOME", "LEAF", "DISEASE", 'TEAM'], 
    icons=['house', 'mouse', "virus", 'people'], 
    menu_icon="cast", 
    default_index=0, 
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#111827"},
        "icon": {"color": "#00fecd", "font-size": "15px"}, 
        "nav-link": {"font-size": "14px", 
                     "text-align": "center", 
                     "margin":"0px", "--hover-color": "#1f2937",
                     "font-family": "'Arial', 'sans-serif'"},
        "nav-link-selected": {"color": "#00fecd",
                              "font-weight": "normal", 
                              "background-color": "#111827", 
                              "border": "2px solid #00fecd", 
                              "border-radius": "25px"}
    })

if tab == 'HOME':
    detection.main()

elif tab == 'LEAF':
    leaf.main()

elif tab == 'DISEASE':
    disease.main()

elif tab == 'TEAM':
    team.main()
    