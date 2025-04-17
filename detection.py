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
                    image_bytes = source_img.getvalue()
                    current_hash = hashlib.md5(image_bytes).hexdigest()
                    
                    if current_hash != st.session_state.current_image_hash:
                        st.session_state.current_image_hash = current_hash
                        st.session_state.saved_to_database = False
                        st.session_state.saved_to_drive = False
                        st.session_state.detection_run = False
                        st.session_state.last_model_config = {}  # Reset model config on new image

            # Check if model configuration has changed
            config_changed = False
            if st.session_state.detection_run:
                # Compare current config with last used config
                for key, value in current_model_config.items():
                    if key not in st.session_state.last_model_config or st.session_state.last_model_config[key] != value:
                        config_changed = True
                        break

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
                                    
                                    # Display spinner in the placeholder
                                    with col2_placeholder.container():
                                        st.markdown(
                                            f"""
                                            <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 300px;">
                                                <div class="stSpinner">
                                                    <div class="st-spinner-border" role="status">
                                                        <span class="visually-hidden">Loading...</span>
                                                    </div>
                                                </div>
                                                <p style="margin-top: 20px; font-size: 16px; color: {primary_color};">Processing image...</p>
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )
                                    
                                    # Load models based on configuration
                                    model = model_leaf = model_disease = None

                                    if detection_model_choice == "Disease":
                                        if disease_model_mode == "YOLOv11m - Full Leaf":
                                            model = helper.load_model(
                                                Path(settings.DISEASE_MODEL_YOLO11M)
                                            )
                                        else:
                                            model = (
                                                helper.load_model(Path(settings.DISEASE_MODEL_SPOTS)),
                                                helper.load_model(
                                                    Path(settings.DISEASE_MODEL_FULL_LEAF)
                                                ),
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
                                                helper.load_model(
                                                    Path(settings.DISEASE_MODEL_FULL_LEAF)
                                                ),
                                            )
                                        model_leaf = helper.load_model(Path(settings.LEAF_MODEL))
                                        model = None

                                    st.session_state["uploaded_image"] = uploaded_image
                                    
                                    # Auto-generate preview (no saving)
                                    uploaded_image = PIL.Image.open(source_img)
                                    preview_image = generate_preview_image(
                                        uploaded_image,
                                        detection_model_choice,
                                        model if detection_model_choice != "Both Models" else None,
                                        model_leaf
                                        if detection_model_choice == "Both Models"
                                        else None,
                                        model_disease
                                        if detection_model_choice == "Both Models"
                                        else None,
                                        confidence,
                                        overlap_threshold,
                                        cdisease_colors,
                                        cleaf_colors,
                                    )
                                    st.session_state["last_result_image"] = preview_image
                                    
                                    # Process detections with confidence levels
                                    from modules.detection_runner import detect_with_confidence

                                    # Get all detections with confidence
                                    detections_with_confidence = detect_with_confidence(
                                        uploaded_image,
                                        detection_model_choice,
                                        model if detection_model_choice != "Both Models" else None,
                                        model_leaf if detection_model_choice == "Both Models" else None,
                                        model_disease if detection_model_choice == "Both Models" else None,
                                        confidence,
                                        overlap_threshold
                                    )

                                    # Store all unique diseases (don't filter by highest confidence)
                                    unique_diseases = set()
                                    disease_dict = {}
                                    all_detections = []  # Store all detections including duplicates

                                    # Store all instances with their individual confidence levels
                                    all_instances = []
                                    
                                    for disease, conf in detections_with_confidence:
                                        unique_diseases.add(disease)
                                        all_detections.append(disease)  # Keep track of all instances
                                        all_instances.append((disease, conf))  # Store each instance with its confidence
                                        
                                        # For each disease, store the highest confidence score
                                        if disease not in disease_dict or conf > disease_dict[disease]:
                                            disease_dict[disease] = conf

                                    st.session_state["detected_diseases"] = list(unique_diseases)
                                    st.session_state["all_disease_detections"] = all_detections  # Store all instances
                                    st.session_state["disease_confidences"] = disease_dict
                                    st.session_state["all_disease_instances"] = all_instances  # Store all instances with confidence
                                    
                                    # Mark detection as run and save the current model config
                                    st.session_state.detection_run = True
                                    st.session_state.detection_in_progress = False
                                    st.session_state.last_model_config = current_model_config.copy()
                                    
                                    # Display the result image after processing
                                    col2_placeholder.image(
                                        preview_image,
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
            st.markdown(f"""<h3 style='background-color: {primary_color}10; margin-right: 30px; border-radius: 10px 10px 0px 0px; 
                        border: 1px solid {primary_color}; padding: 15px; border-bottom: 1px solid {primary_color};
                        font-weight: 600; font-size: 1.2rem; color: {primary_color}'>
                        Detection Results</h3>""", unsafe_allow_html=True)
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
                
                if tab == "Summary":
                    if source_img is None:
                        st.info("Upload an image to see disease detection summary")
                    else:
                        detected_diseases = st.session_state.get("detected_diseases", [])
                        all_detections = st.session_state.get("all_disease_detections", [])
                        disease_confidences = st.session_state.get("disease_confidences", {})
                        
                        # Display both counts for clarity
                        total_count = len(all_detections)
                        unique_count = len(detected_diseases)
                        
                        if total_count == unique_count:
                            st.markdown(f"### Diseases Detected: {unique_count}")
                        else:
                            st.markdown(f"### Diseases Detected: {total_count} instances ({unique_count} unique types)")
                        
                        if detected_diseases:
                            # Build a counter for each disease
                            from collections import Counter
                            disease_counter = Counter(all_detections)
                            
                            for disease in detected_diseases:
                                confidence = disease_confidences.get(disease, 0)
                                count = disease_counter[disease]
                                if count > 1:
                                    st.markdown(f"- **{disease.title()}** - {count} instances - Highest Confidence: **{confidence:.1f}%**")
                                else:
                                    st.markdown(f"- **{disease.title()}** - Highest Confidence: **{confidence:.1f}%**")
                                
                            # Check if only "healthy" is detected
                            only_healthy = len(detected_diseases) == 1 and detected_diseases[0].lower() == "healthy"
                            
                            # Add buttons for saving data and uploading to drive
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Disable button if already saved or only healthy detected
                                db_button_disabled = st.session_state.saved_to_database or only_healthy
                                
                                if st.button("💾 Save to Database", 
                                           use_container_width=True, 
                                           disabled=db_button_disabled):
                                    try:
                                        gps_data = get_gps_location(source_img)
                                        
                                        with st.spinner("Saving to database..."):
                                            for disease in detected_diseases:
                                                # Skip saving if it's healthy
                                                if disease.lower() != "healthy":
                                                    confidence = disease_confidences.get(disease, 75) # Default to 75 if not found
                                                    save_location_data(source_img, disease, confidence, gps_data)
                                            
                                            st.session_state.saved_to_database = True
                                            st.success("✅ Data saved successfully to database!")
                                    except Exception as e:
                                        st.error(f"Error saving data: {e}")
                                
                                if db_button_disabled and st.session_state.saved_to_database:
                                    st.info("✓ Already saved to database")
                                elif only_healthy:
                                    st.info("ℹ️ Healthy leaves are not saved to database")
                            
                            with col2:
                                # Check if image already exists in Drive
                                image_exists = False
                                if source_img:
                                    try:
                                        image_exists = check_image_exists(drive, PARENT_FOLDER_ID, source_img.name)
                                    except:
                                        # If check fails, assume it doesn't exist
                                        pass
                                
                                # Disable button if already saved or image exists
                                drive_button_disabled = st.session_state.saved_to_drive or image_exists
                                
                                if st.button("☁️ Save to Drive", 
                                           use_container_width=True,
                                           disabled=drive_button_disabled):
                                    try:
                                        uploaded_image = PIL.Image.open(source_img)
                                        
                                        # Double-check if image exists before uploading
                                        if check_image_exists(drive, PARENT_FOLDER_ID, source_img.name):
                                            st.warning("⚠️ This image already exists in Google Drive")
                                        else:
                                            with st.spinner("Uploading to Google Drive..."):
                                                # Use the first detected disease as the label, or "Unknown" if none
                                                label = detected_diseases[0] if detected_diseases else "Unknown"
                                                
                                                _upload_image_once(uploaded_image, label, drive, PARENT_FOLDER_ID)
                                                st.session_state.saved_to_drive = True
                                                st.success("✅ Image uploaded to Google Drive successfully!")
                                    except Exception as e:
                                        st.error(f"Error uploading to Drive: {e}")
                                
                                if drive_button_disabled and st.session_state.saved_to_drive:
                                    st.info("✓ Already saved to Drive")
                                elif drive_button_disabled and image_exists:
                                    st.warning("⚠️ This image already exists in Google Drive")
                        else:
                            st.info("No diseases detected in this image")
                
                elif tab == "Detailed Analysis":
                    if source_img is None:
                        st.info("Upload an image to see detailed analysis")
                    else:
                        # Show image metadata
                        gps_data = get_gps_location(source_img)
                        image_date = get_image_taken_time(source_img)
                        location_name = (
                            get_location_name(
                                gps_data["latitude"], gps_data["longitude"]
                            )
                            if gps_data
                            else "Unavailable"
                        )

                        st.markdown("#### Image Metadata")
                        st.write(f"- **Location**: \`{location_name}\`")
                        if gps_data:
                            st.write(
                                f"- **Latitude**: \`{gps_data.get('latitude', 'N/A')}\`"
                            )
                            st.write(
                                f"- **Longitude**: \`{gps_data.get('longitude', 'N/A')}\`"
                            )
                        else:
                            st.write("- **Latitude**: \`Unavailable\`")
                            st.write("- **Longitude**: \`Unavailable\`")
                        if image_date:
                            st.write(f"- **Date Taken**: \`{image_date}\`")
                        
                        # Show all disease instances with their individual confidence levels
                        st.markdown("#### All Disease Instances")
                        
                        all_instances = st.session_state.get("all_disease_instances", [])
                        if all_instances:
                            # Group instances by disease type for better organization
                            from collections import defaultdict
                            grouped_instances = defaultdict(list)
                            
                            for disease, confidence in all_instances:
                                grouped_instances[disease].append(confidence)
                            
                            # Display each disease type with all its instances
                            for disease, confidences in grouped_instances.items():
                                st.markdown(f"**{disease.title()}** - {len(confidences)} instance(s)")
                                
                                # Display each individual instance with its confidence
                                for i, conf in enumerate(confidences, 1):
                                    st.markdown(f"  - Instance {i}: Confidence **{conf:.1f}%**")
                        else:
                            st.info("No disease instances detected in this image")

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
                    status_text.markdown(f"**Detecting and saving:** \`{file.name}\`")
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
                        save_to_drive=save_to_drive,  # <- still passed in
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