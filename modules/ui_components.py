import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_extras.stylable_container import stylable_container

def render_instructions(primary_color, background_color, text_color):
    """Render the instructions panel"""
    with stylable_container(
        key="instructions_container",
        css_styles=f"""
        {{
            background-color: {background_color};
            border-radius: 10px;
            padding: 0;
            max-width: 1000px;
            margin: auto;
            box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        }}
        """,
    ):
        # Teal gradient at the top
        st.markdown(
            """
            <div style="height: 4px; background: linear-gradient(to right, #4dd6c1, #37b8a4, #2aa395); width: 100%;"></div>
            """, 
            unsafe_allow_html=True
        )
        
        # Instructions header with checkmark icon
        st.markdown(
            f"""
            <div style="padding: 0 24px 0 24px; display: flex; align-items: center;">
                <div style="background-color: {primary_color}33; border: 2px solid {primary_color}; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
                    <svg xmlns="http://www.w3.org/2000/svg" color="{primary_color}" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                </div>
                <h2 style="margin: 0; font-family: 'Inter', sans-serif; font-size: 1.4rem; color: {text_color};">Instructions</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Instructions subtitle
        st.markdown(
            f"""
            <div style="padding: 0 24px 15px 65px; margin-top: -15px;">
                <p style="font-family: 'Inter', sans-serif; color: {text_color}; font-size: 0.95rem; line-height: 1.25rem; opacity: 0.5; margin: 0;">Follow these steps to detect coffee leaf diseases</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Steps
        steps = [
            "Configure the model settings in the sidebar",
            "Upload a valid image file (jpeg, jpg, webp, png)",
            "Avoid bluriness and make sure the leaf is the main focus of the image",
            "The system will detect diseases based on your configuration",
            "Results will display detected diseases and confidence scores"
        ]
        
        for i, step in enumerate(steps, 1):
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; padding: 12px 20px 5px 50px;">
                    <div style="background-color: {primary_color}; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px; flex-shrink: 0;">
                        <span style="font-weight: 600; font-size: 15px; color: white">{i}</span>
                    </div>
                    <p style="letter-spacing: 0.4px; font-family: 'Inter', sans-serif; font-size: 0.95rem; line-height: 1.25rem; margin: 0; color: {text_color};">{step}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Note banner
        st.markdown(
            f"""
            <div style="border-radius: 4px; margin: 20px 24px 0; padding: 12px 16px 0; display: flex; align-items: flex-start;">
                <p style="font-family: 'Inter', sans-serif; margin: 0; color: {primary_color};"></p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.warning('Our model is currently optimized to detect diseases only in coffee leaves.', icon=':material/info:')

def create_results_tabs(primary_color, background_color, secondary_background_color, text_color):
    """Create the results tabs for Summary and Detailed Analysis"""
    menu_styles = {
        "container": {"padding": "6px", "background-color": f'{primary_color}10'},
        "icon": {"color": primary_color, "font-size": "15px"},
        "nav-link": {
            "font-size": "1rem",
            "text-align": "center",
            "margin": "0px",
            "--hover-color": secondary_background_color,
            "font-family": "'Arial', 'sans-serif'",
            "color": text_color,
        },
        "nav-link-selected": {
            "color": primary_color,
            "font-weight": "normal",
            "background-color": background_color,
            "box-shadow": "0 2px 2px rgba(0, 0, 0, 0.15)",
            "border-radius": "5px",
        },
    }   

    res_col = st.columns(2)
    with res_col[0]:
        tab = option_menu(
            None,
            ["Summary", "Detailed Analysis"],
            icons=["journal", "bar-chart"],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles=menu_styles,
        )
    
    return tab

def render_results_header(primary_color):
    """Render the results header"""
    st.markdown(f"""<h3 style='background-color: {primary_color}10; margin-right: 30px; border-radius: 10px 10px 0px 0px; 
                border: 1px solid {primary_color}; padding: 15px; border-bottom: 1px solid {primary_color};
                font-weight: 600; font-size: 1.2rem; color: {primary_color}'>
                Detection Results</h3>""", unsafe_allow_html=True)