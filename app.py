# External packages
import streamlit as st
import streamlit_shadcn_ui as ui
from streamlit_option_menu import option_menu

# Additional Page
import leaf
import disease
import detection

# Setting page layout
st.set_page_config(
    page_title="Coffee Leaf Classification and Disease Detection",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="expanded"
)

tab = option_menu(None, ["DETECT", "LEAF", "DISEASE", 'TEAM'], 
    icons=['search', 'mouse', "virus", 'people'], 
    menu_icon="cast", 
    default_index=0, 
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "white"},
        "icon": {"color": "green", "font-size": "15px"}, 
        "nav-link": {"font-size": "15px", 
                     "text-align": "center", 
                     "margin":"0px", "--hover-color": "#F7F9F2",
                     "font-family": "'Arial', 'sans-serif'"},
        "nav-link-selected": {"color": "green", "background-color": "white"},
    })

if tab == 'DETECT':
    detection.main()

elif tab == 'LEAF':
    leaf.main()

elif tab == 'DISEASE':
    disease.main()

    