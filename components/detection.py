import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from components.ui_manager import manage_ui_state

# Import other modules
from modules.detection_utils import initialize_session_state
from modules.batch_processing import process_all_images
from modules.cache_management import (
    clear_cache, 
    get_cache_size, 
    limit_cache_size
)
from modules.image_uploader import authenticate_drive

def main(theme_colors):
    # Initialize session state variables
    initialize_session_state()
    
    # Limit cache size to prevent memory issues
    limit_cache_size(max_entries=50)

    # Add batch upload toggle in sidebar
    st.sidebar.subheader('UPLOAD SETTINGS')
    
    # Initialize batch_mode in session state if not present
    if "batch_mode" not in st.session_state:
        st.session_state.batch_mode = False
    
    # Add toggle for batch mode
    batch_mode = st.sidebar.toggle(
        "Enable Batch Uploading", 
        value=st.session_state.batch_mode,
        help="Toggle to enable uploading multiple images at once"
    )
    
    # Update session state if toggle changed
    if batch_mode != st.session_state.batch_mode:
        st.session_state.batch_mode = batch_mode
        # Reset selected image index when switching modes
        if "selected_image_idx" in st.session_state:
            st.session_state.selected_image_idx = 0
    
    # Remove the file uploader from sidebar since we'll add it to the instructions UI
    # We'll keep the batch mode toggle in the sidebar
    
    st.sidebar.divider()

    # Sidebar theme
    with st.sidebar:
        st.header("THEME")
        theme_option = st.selectbox(
            "Choose theme",
            options=["Light", "Dark"],
            index=1 if st.session_state.dark_theme else 0,
            key="theme_selector",
        )
        warn = st.empty()
        st.divider()

    if theme_option == "Dark" and not st.session_state.dark_theme:
        st.session_state.dark_theme = True
        st.rerun()
    elif theme_option == "Light" and st.session_state.dark_theme:
        st.session_state.dark_theme = False
        st.rerun()

    # Theme colors
    theme = (
        theme_colors["DARK"] if st.session_state.dark_theme else theme_colors["LIGHT"]
    )
    primary_color = theme["primaryColor"]
    background_color = theme["backgroundColor"]
    secondary_background_color = theme["secondaryBackgroundColor"]
    text_color = theme["textColor"]

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {background_color};
            color: {text_color};
        }}
        .stSelectbox, .stSelectbox > div > div > div {{
            background-color: {secondary_background_color};
            color: {text_color};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar model selection
    st.sidebar.header("MODEL CONFIGURATION")

    disease_model_mode = st.sidebar.selectbox(
        "Disease Model Type:",
        ["Ensemble", "YOLO11 - Precised Spots Detection", "YOLO12n - Lightweight Model"],
        index=0,
        key="disease_model_mode",
    )

    detection_model_choice = st.sidebar.selectbox(
        "Select Detection Model", ("Disease", "Leaf", "Both Models"), index=0
    )

    adv_opt = st.sidebar.toggle("Advanced Options")
    confidence = 0.6
    overlap_threshold = 0.3
    if adv_opt:
        confidence = float(st.sidebar.slider("Model Confidence", 25, 100, 60,
                                             help="Set the minimum confidence score for displaying detections. Higher values show only more certain predictions; lower values allow more detections, including less confident ones."
                                             )) / 100
        overlap_threshold = (
            float(st.sidebar.slider("Overlap Threshold", 0, 100, 30, help=
                                    "Adjust the overlap threshold (IoU) to control how much bounding boxes must overlap to be considered the same object. Lower values merge more boxes; higher values require stricter overlap."
                                    )) / 100
        )
        st.sidebar.markdown(
            """
            <div style="border-radius: 8px; background: linear-gradient(to bottom right, #14b8a6, #5eead4); 
                        margin-bottom: 10px; padding: 16px; color: white; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
                <h3 style="text-shadow: 4px 4px 6px rgba(0, 0, 0, 0.5); padding-bottom: 0; color: #d4fcf0; font-weight: bold; margin-bottom: 8px; font-size: 18px;">Pro Tip</h3>
                <p style="color: #d4fcf0; font-size: 14px; opacity: 0.9; margin: 0; text-shadow: 4px 4px 6px rgba(0, 0, 0, 0.5);">
                    Higher confidence values increase precision but may miss some detections. Balance according to your needs.
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )

    # Create current model configuration dictionary
    current_model_config = {
        "disease_model_mode": disease_model_mode,
        "detection_model_choice": detection_model_choice,
        "confidence": confidence,
        "overlap_threshold": overlap_threshold
    }
    
    # Store model config in session state for UI manager
    st.session_state["current_model_config"] = current_model_config

    # Initialize drive for Google Drive integration
    @st.cache_resource
    def get_drive():
        return authenticate_drive()

    drive = get_drive()
    PARENT_FOLDER_ID = "1OgdV5CRT61ujv1uW1SSgnesnG59bT5ss"
    
    # Store drive in session state for UI manager
    st.session_state["drive"] = drive
    st.session_state["PARENT_FOLDER_ID"] = PARENT_FOLDER_ID
    
    # Use the stylable container for our main UI
    with stylable_container(
        key="instructions_container",
        css_styles=f"""
        {{
            background-color: {secondary_background_color};
            border-radius: 10px;
            padding: 0;
            max-width: 1000px;
            margin: auto;
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        }}
        """,
    ):
        # Call our UI manager to handle the UI state
        manage_ui_state(theme_colors)

    # Cache management in sidebar - keep this part as is
    if get_cache_size() > 0:
        st.sidebar.divider()
        st.sidebar.header("CACHE MANAGEMENT")
        st.sidebar.write(f"Cache size: {get_cache_size()} images")
        if st.sidebar.button("🧹 Clear Detection Cache"):
            if clear_cache():
                st.sidebar.success("Cache cleared successfully!")
            else:
                st.sidebar.error("Failed to clear cache.")

if __name__ == "__main__":
    default_theme = {
        "LIGHT": {
            "primaryColor": "#41B3A2",
            "backgroundColor": "white",
            "secondaryBackgroundColor": "#fafafa",
            "textColor": "black",
        },
        "DARK": {
            "primaryColor": "#00fecd",
            "backgroundColor": "#111827",
            "secondaryBackgroundColor": "#141b2a",
            "textColor": "white",
        },
    }
    main(default_theme)
