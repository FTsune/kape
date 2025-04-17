import streamlit as st
from pathlib import Path
import PIL
from PIL import Image
import pandas as pd
import numpy as np
import settings
import helper
import uuid
import os
import hashlib
import json
import time
import streamlit_antd_components as sac
from streamlit_extras.stylable_container import stylable_container
from streamlit_option_menu import option_menu

# Import custom modules
from modules.gps_utils import (
    get_gps_location,
    get_image_taken_time,
    get_location_name,
    save_location_data,
)
from modules.processing import non_max_suppression
from modules.visualizations import draw_bounding_boxes
from modules.image_uploader import authenticate_drive, upload_image
from modules.detection_runner import (
    generate_preview_image, 
    detect_labels_only,
    handle_detection,
    save_prediction_if_valid,
    detect_and_save_silently,
    _upload_image_once,
    check_image_exists
)

# Import our new modules
from modules.ui_components import (
    render_instructions,
    create_results_tabs,
    render_results_header
)
from modules.results_display import (
    display_summary_tab,
    display_detailed_analysis_tab
)
from modules.detection_handler import (
    process_image,
    check_model_config_changed,
    get_image_hash
)


def main(theme_colors):
    if "dark_theme" not in st.session_state:
        st.session_state.dark_theme = False

    if "detected_diseases" not in st.session_state:
        st.session_state.detected_diseases = []

    if "disease_confidences" not in st.session_state:
        st.session_state.disease_confidences = {}
        
    if "all_disease_instances" not in st.session_state:
        st.session_state.all_disease_instances = []
        
    if "saved_to_database" not in st.session_state:
        st.session_state.saved_to_database = False
        
    if "saved_to_drive" not in st.session_state:
        st.session_state.saved_to_drive = False
        
    # Track model configuration for redetection
    if "last_model_config" not in st.session_state:
        st.session_state.last_model_config = {}
        
    # Track if detection has been run
    if "detection_run" not in st.session_state:
        st.session_state.detection_run = False
        
    # Track if detection is in progress
    if "detection_in_progress" not in st.session_state:
        st.session_state.detection_in_progress = False

    # File uploader
    st.sidebar.write('Upload Image(s)')
    uploaded_images = st.sidebar.file_uploader(
        "UPLOAD IMAGE(S)",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        accept_multiple_files=True,
        key="multi_image_uploader",
        label_visibility='collapsed'
    )

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

    warn.markdown(
        f"""<div style='background-color: transparent; border: 1px solid {primary_color}; border-radius: 10px;'>
                <p style='font-size: 0.9rem; color: {primary_color}; margin: 0px 0px; padding: 10px;'>
                This feature is still in development and may cause unexpected behavior when used.</p>
            </div>""",
        unsafe_allow_html=True,
    )

    cleaf_colors = {0: (0, 255, 0), 1: (0, 255, 255), 2: (0, 0, 255)}
    cdisease_colors = {
        0: (0, 128, 128),
        1: (255, 165, 0),
        2: (255, 0, 0),
        3: (128, 0, 128),
        4: (150, 75, 0),
        5: (255, 255, 0),
    }

    # Sidebar model selection
    st.sidebar.header("MODEL CONFIGURATION")

    disease_model_mode = st.sidebar.selectbox(
        "Disease Model Type:",
        ["Spots + Full Leaf", "YOLOv11m - Full Leaf"],
        index=1,
        key="disease_model_mode",
    )

    detection_model_choice = st.sidebar.selectbox(
        "Select Detection Model", ("Disease", "Leaf", "Both Models"), index=0
    )

    adv_opt = st.sidebar.toggle("Advanced Options")
    confidence = 0.5
    overlap_threshold = 0.3
    if adv_opt:
        confidence = float(st.sidebar.slider("Model Confidence", 25, 100, 50)) / 100
        overlap_threshold = (
            float(st.sidebar.slider("Overlap Threshold", 0, 100, 30)) / 100
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

    save_to_drive = st.sidebar.checkbox("📤 Save samples to improve the model")

    # Create current model configuration dictionary
    current_model_config = {
        "disease_model_mode": disease_model_mode,
        "detection_model_choice": detection_model_choice,
        "confidence": confidence,
        "overlap_threshold": overlap_threshold
    }

    @st.cache_resource
    def get_drive():
        return authenticate_drive()

    drive = get_drive()
    PARENT_FOLDER_ID = "1OgdV5CRT61ujv1uW1SSgnesnG59bT5ss"
        
    # Render instructions using our new module
    render_instructions(primary_color, background_color, text_color)

    st.divider()

    with stylable_container(
            key="container_with_border",
            css_styles=f"""
                {{=
                    border-radius: 10px;
                    padding: calc(1em - 1px);
                    margin: auto;
                }}
                """,
        ):

        if "multi_image_uploader" not in st.session_state:
            uploaded_images = None
        else:
            uploaded_images = st.session_state["multi_image_uploader"]
        
        # Initialize source_img before pagination
        source_img = None
        selected_idx = 0
        
        if uploaded_images:
            # Get the selected index but don't render pagination yet
            if len(uploaded_images) > 0:
                if "selected_image_idx" not in st.session_state:
                    st.session_state.selected_image_idx = 0
                
                # Ensure index is valid
                if st.session_state.selected_image_idx >= len(uploaded_images):
                    st.session_state.selected_image_idx = 0
                    
                selected_idx = st.session_state.selected_image_idx
                source_img = uploaded_images[selected_idx]
            
            # Reset saved states when changing images
            if "current_image_hash" not in st.session_state:
                st.session_state.current_image_hash = ""
            
            if source_img:
                # Generate a hash of the current image to detect changes
                current_hash = get_image_hash(source_img)
                
                if current_hash != st.session_state.current_image_hash:
                    st.session_state.current_image_hash = current_hash
                    st.session_state.saved_to_database = False
                    st.session_state.saved_to_drive = False
                    st.session_state.detection_run = False
                    st.session_state.last_model_config = {}  # Reset model config on new image

        # Check if model configuration has changed
        config_changed = check_model_config_changed(current_model_config, st.session_state.last_model_config)

        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                image_placeholder = st.empty()
                st.session_state["image_placeholder"] = image_placeholder
                default_image_path = str(settings.DEFAULT_IMAGE)

                if source_img is None:
                    default_image = PIL.Image.open(default_image_path)
                    image_placeholder.image(
                        default_image,
                        caption="Sample Image",
                        use_column_width=True,
                    )
                else:
                    uploaded_image = PIL.Image.open(source_img)

                    if (
                        "last_uploaded_filename" not in st.session_state
                        or st.session_state["last_uploaded_filename"] != source_img.name
                        or not st.session_state.detection_run
                    ):
                        st.session_state["last_uploaded_filename"] = source_img.name
                        if not config_changed:  # Only reset if not just a config change
                            st.session_state["last_result_image"] = None
                            st.session_state["detected_diseases"] = []
                            st.session_state["disease_confidences"] = {}
                            st.session_state["all_disease_instances"] = []
                            st.session_state.saved_to_database = False
                            st.session_state.saved_to_drive = False

                    # Display the original uploaded image in col1
                    image_placeholder.image(
                        uploaded_image,
                        caption="Original Image",
                        use_column_width=True,
                    )

        with col2:
            with stylable_container(
                key="container_with_border_right",
                css_styles=f"""
                {{
                }}
                """,
            ):
                with st.container(border=True):
                    col2_placeholder = st.empty()
                    st.session_state["detection_placeholder"] = col2_placeholder

                if source_img is None:
                    detected_image_path = str(settings.DEFAULT_DETECT_IMAGE)
                    default_image = PIL.Image.open(detected_image_path)
                    col2_placeholder.image(
                        default_image,
                        caption="Sample Image: Objects Detected",
                        use_column_width=True,
                    )
                else:
                    # Show redetect button if config changed and detection was already run
                    if config_changed and st.session_state.detection_run:
                        redetect_col1, redetect_col2, redetect_col3 = st.columns([1, 2, 1])
                        with redetect_col2:
                            if st.button("🔄 Redetect with New Configuration", use_container_width=True):
                                # Reset detection results
                                st.session_state["last_result_image"] = None
                                st.session_state.detection_run = False
                                st.session_state.detection_in_progress = True
                                st.rerun()  # Rerun to apply new detection
                        
                        # Still show the previous detection result
                        if st.session_state.get("last_result_image") is not None:
                            col2_placeholder.image(
                                st.session_state["last_result_image"],
                                caption="Detected Image (Previous Configuration)",
                                use_column_width=True,
                            )
                    else:
                        # Generate and display detection image if not already done
                        if st.session_state.get("last_result_image") is not None and st.session_state.detection_run:
                            col2_placeholder.image(
                                st.session_state["last_result_image"],
                                caption="Detected Image",
                                use_column_width=True,
                            )
                        else:
                            # Show spinner while detection is in progress
                            if not st.session_state.detection_run:
                                # Set detection in progress
                                st.session_state.detection_in_progress = True
                                
                                # Use st.spinner instead of custom markdown
                                with col2_placeholder.container():
                                    with st.spinner("Processing image..."):
                                        # Process the image using our new module
                                        results = process_image(
                                            source_img,
                                            detection_model_choice,
                                            disease_model_mode,
                                            confidence,
                                            overlap_threshold,
                                            cdisease_colors,
                                            cleaf_colors
                                        )
                                        
                                        # Store results in session state
                                        st.session_state["last_result_image"] = results["preview_image"]
                                        st.session_state["detected_diseases"] = results["detected_diseases"]
                                        st.session_state["all_disease_detections"] = results["all_disease_detections"]
                                        st.session_state["disease_confidences"] = results["disease_confidences"]
                                        st.session_state["all_disease_instances"] = results["all_disease_instances"]
                                        
                                        # Mark detection as run and save the current model config
                                        st.session_state.detection_run = True
                                        st.session_state.detection_in_progress = False
                                        st.session_state.last_model_config = current_model_config.copy()
                                
                                # Display the result image after processing
                                col2_placeholder.image(
                                    st.session_state["last_result_image"],
                                    caption="Detected Image",
                                    use_column_width=True,
                                )
        
        # Add pagination AFTER the image columns
        if uploaded_images and len(uploaded_images) > 1:
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)  # Add some spacing
            
            # Create pagination with centered styling
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center; margin-top: 10px;">
                    <div style="width: 80%;">
                """, 
                unsafe_allow_html=True
            )
            
            # Use pagination component
            new_idx = sac.pagination(
                total=len(uploaded_images),
                page_size=1,
                align='center',
                key="pagination_below_images",
                index=selected_idx + 1  # sac.pagination is 1-indexed
            ) - 1  # Convert back to 0-indexed
            
            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Update the selected index if changed
            if new_idx != selected_idx:
                st.session_state.selected_image_idx = new_idx
                st.rerun()  # Rerun to load the new image

    with stylable_container(
            key="detection_res_border",
            css_styles=f"""
                {{
                    padding: calc(1em - 1px);
                    margin: auto;
                }}
                """,
        ):
        # Render results header using our new module
        render_results_header(primary_color)
        
        with stylable_container(
            key='side_border',
            css_styles=f"""
                {{
                    border-left: 1px solid {primary_color};
                    border-right: 1px solid {primary_color};
                    border-bottom: 1px solid {primary_color};
                    border-radius: 0 0 10px 10px;
                    padding: calc(1em - 1px);
                    margin: auto;
                }}
                """,
        ):
            # Create tabs using our new module
            tab = create_results_tabs(primary_color, background_color, secondary_background_color, text_color)
            
            if tab == "Summary":
                # Display summary tab using our new module
                display_summary_tab(source_img, drive, PARENT_FOLDER_ID)
            
            elif tab == "Detailed Analysis":
                # Display detailed analysis tab using our new module
                display_detailed_analysis_tab(source_img)

    if uploaded_images and st.sidebar.button("📦 Save All Uploaded Images"):
        with st.spinner("Running detection and saving..."):
            status_text = st.empty()
            progress = st.progress(0)
            total = len(uploaded_images)

            # Load models once
            disease_model_mode = st.session_state.get(
                "disease_model_mode", "Default (Spots + Full Leaf)"
            )

            if detection_model_choice == "Disease":
                if disease_model_mode == "YOLOv11m - Full Leaf":
                    model = helper.load_model(Path(settings.DISEASE_MODEL_YOLO11M))
                else:
                    model = (
                        helper.load_model(Path(settings.DISEASE_MODEL_SPOTS)),
                        helper.load_model(Path(settings.DISEASE_MODEL_FULL_LEAF)),
                    )
                model_leaf = model_disease = None

            elif detection_model_choice == "Both Models":
                if disease_model_mode == "YOLOv11m - Full Leaf":
                    model_disease = helper.load_model(
                        Path(settings.DISEASE_MODEL_YOLO11M)
                    )
                else:
                    model_disease = (
                        helper.load_model(Path(settings.DISEASE_MODEL_SPOTS)),
                        helper.load_model(Path(settings.DISEASE_MODEL_FULL_LEAF)),
                    )
                model_leaf = helper.load_model(Path(settings.LEAF_MODEL))
                model = None

            for idx, file in enumerate(uploaded_images):
                try:
                    status_text.markdown(f"**Detecting and saving:** `{file.name}`")
                    image = PIL.Image.open(file)
                    gps_data = get_gps_location(file)

                    # Run detection
                    best_label, score = detect_and_save_silently(
                        uploaded_image=image,
                        image_file=file,
                        gps_data=gps_data,
                        model_type=detection_model_choice,
                        model=model,
                        model_leaf=model_leaf,
                        model_disease=model_disease,
                        confidence=confidence,
                        overlap_threshold=overlap_threshold,
                        save_to_drive=save_to_drive,
                        drive=drive,
                        parent_folder_id=PARENT_FOLDER_ID,
                        cdisease_colors=cdisease_colors,
                        cleaf_colors=cleaf_colors,
                    )

                    if best_label != "No Detection":
                        st.success(f"✅ Saved: {file.name} ({best_label}, {score}%)")
                    else:
                        st.info(f"ℹ️ Skipped: {file.name} — No disease detected.")

                except Exception as e:
                    st.error(f"❌ Failed: {file.name}: {e}")

                progress.progress((idx + 1) / total)

            status_text.markdown("✅ **All images processed and saved.**")


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