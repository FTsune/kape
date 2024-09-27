# External packages
import streamlit as st
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
    initial_sidebar_state="collapsed"
)

# st.markdown(
#     """
#     <style>
#     [data-testid="stHeader"] {
#         display: none;
#     }
#     [data-testid="stToolbar"] {
#         display: none;
#     }
#     .main .block-container {
#         padding-top: 0 !important;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

# st.markdown(
#     """
#     <style>
#     .menu-container {
#         margin-top: 0 !important;
#         padding-top: 20px !important;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

tab = option_menu(None, ["Home", "Leaf", "Disease", 'Team'], 
    icons=['house', 'feather', "virus", 'people'], 
    menu_icon="cast", 
    default_index=0, 
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important",  "background-color": "transparent"},
        "icon": {"color": "#41B3A2", "font-size": "15px"}, 
        "nav-link": {"font-size": "14px", 
                     "text-align": "center", 
                     "margin":"0px", "--hover-color": "#fafafa",
                     "font-family": "'Arial', 'sans-serif'"},
        "nav-link-selected": {"color": "#41B3A2",
                              "font-weight": "normal", 
                              "background-color": "transparent", 
                            #   "border": "2px solid #41B3A2", 
                              "border-radius": "0px"}
    })

if tab == 'Home':
    detection.main()

elif tab == 'Leaf':
    leaf.main()

elif tab == 'Disease':
    disease.main()

elif tab == 'Team':
    team.main()
    