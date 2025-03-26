import streamlit as st
from pathlib import Path
import PIL
from PIL import Image
import cv2
import numpy as np
import time
import settings
import helper
import uuid
import json
from datetime import datetime
import os
from streamlit_extras.stylable_container import stylable_container

# Import the updated modules
from modules.gps_utils import get_gps_location, save_location_data
from modules.processing import format_detection_results, non_max_suppression
from modules.visualizations import draw_bounding_boxes, run_live_detection
from modules.image_uploader import authenticate_drive, upload_image  # ✅ NEW


def main(theme_colors):
    # Initialize session state for theme if not already set
    if "dark_theme" not in st.session_state:
        st.session_state.dark_theme = False

    # Sidebar theme selection
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

    # Update session state based on theme selection
    new_theme = theme_option == "Dark"
    if new_theme != st.session_state.dark_theme:
        st.session_state.dark_theme = new_theme
        st.rerun()

    # Apply theme colors
    if st.session_state.dark_theme:
        primary_color = theme_colors["DARK"]["primaryColor"]
        background_color = theme_colors["DARK"]["backgroundColor"]
        secondary_background_color = theme_colors["DARK"]["secondaryBackgroundColor"]
        text_color = theme_colors["DARK"]["textColor"]
    else:
        primary_color = theme_colors["LIGHT"]["primaryColor"]
        background_color = theme_colors["LIGHT"]["backgroundColor"]
        secondary_background_color = theme_colors["LIGHT"]["secondaryBackgroundColor"]
        text_color = theme_colors["LIGHT"]["textColor"]

    # Apply theme to Streamlit
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

    # Define global color mappings for classes
    cleaf_colors = {
        0: (0, 255, 0),  # Green for 'arabica'
        1: (0, 255, 255),  # Aqua for 'liberica'
        2: (0, 0, 255),  # Blue for 'robusta'
    }

    cdisease_colors = {
        0: (0, 128, 128),  # Teal for 'abiotic disorder'
        1: (255, 165, 0),  # Orange for 'algal growth'
        2: (255, 0, 0),  # Red for 'cercospora'
        3: (128, 0, 128),  # Purple for 'late stage rust'
        4: (150, 75, 0),  # Magenta for 'rust'
        5: (255, 255, 0),  # Yellow for 'sooty mold'
    }

    # Sidebar
    st.sidebar.header("MODEL CONFIGURATION")

    detection_model_choice = st.sidebar.selectbox(
        "Select Detection Model",
        ("Disease", "Leaf", "Both Models"),
        index=0,
        placeholder="Choose a model...",
    )

    adv_opt = st.toggle("Advanced Options")
    confidence = 0.4
    overlap_threshold = 0.3
    if adv_opt:
        confidence = (
            float(st.sidebar.slider("Select Model Confidence", 25, 100, 40)) / 100
        )
        overlap_threshold = (
            float(st.sidebar.slider("Select Overlap Threshold", 0, 100, 30)) / 100
        )

    # ✅ GDrive checkbox
    save_to_drive = st.sidebar.checkbox("📤 Save samples to improve the model")

    # ✅ Authenticate Drive only once
    @st.cache_resource
    def get_drive():
        return authenticate_drive()

    drive = get_drive()
    PARENT_FOLDER_ID = (
        "1OgdV5CRT61ujv1uW1SSgnesnG59bT5ss"  # ✅ Your actual GDrive folder
    )

    source_img = st.sidebar.file_uploader(
        "Choose an image...", type=("jpg", "jpeg", "png", "bmp", "webp")
    )

    if source_img:
        uploaded_image = PIL.Image.open(source_img)
        image_placeholder = st.image(
            uploaded_image, caption="Uploaded Image", use_column_width=True
        )

        # Extract GPS metadata
        gps_data = get_gps_location(source_img)

        if gps_data:
            with st.expander("Image Location Data"):
                st.write(f"Latitude: {gps_data['latitude']:.6f}°")
                st.write(f"Longitude: {gps_data['longitude']:.6f}°")
                if gps_data["altitude"]:
                    st.write(f"Altitude: {float(gps_data['altitude']):.1f}m")
                st.map({"lat": [gps_data["latitude"]], "lon": [gps_data["longitude"]]})

        if st.sidebar.button("Detect Objects"):
            st.write("Processing...")

            # Load model based on selection
            try:
                if detection_model_choice == "Disease":
                    model_path = Path(settings.DISEASE_DETECTION_MODEL)
                    model = helper.load_model(model_path)
                    colors = cdisease_colors
                elif detection_model_choice == "Leaf":
                    model_path = Path(settings.LEAF_DETECTION_MODEL)
                    model = helper.load_model(model_path)
                    colors = cleaf_colors
                else:
                    model_disease = helper.load_model(
                        Path(settings.DISEASE_DETECTION_MODEL)
                    )
                    model_leaf = helper.load_model(Path(settings.LEAF_DETECTION_MODEL))
            except Exception as ex:
                st.error(f"Error loading model: {ex}")
                return

            if detection_model_choice == "Both Models":
                res_disease = model_disease.predict(uploaded_image, conf=confidence)
                res_leaf = model_leaf.predict(uploaded_image, conf=confidence)

                disease_boxes = non_max_suppression(
                    res_disease[0].boxes, overlap_threshold
                )
                leaf_boxes = non_max_suppression(res_leaf[0].boxes, overlap_threshold)

                result_image = np.array(uploaded_image)
                result_image = draw_bounding_boxes(
                    result_image, disease_boxes, res_disease[0].names, cdisease_colors
                )
                result_image = draw_bounding_boxes(
                    result_image, leaf_boxes, res_leaf[0].names, cleaf_colors
                )

                boxes = disease_boxes + leaf_boxes
                labels = {**res_disease[0].names, **res_leaf[0].names}

            else:
                res = model.predict(uploaded_image, conf=confidence)
                boxes = non_max_suppression(res[0].boxes, overlap_threshold)
                labels = res[0].names
                result_image = draw_bounding_boxes(
                    uploaded_image, boxes, labels, colors
                )

            image_placeholder.image(
                result_image, caption="Detected Image", use_column_width=True
            )

            saved_any_detections = False
            uploaded = False

            for box in boxes:
                class_id = int(box.cls[0])
                conf_score = round(float(box.conf[0]) * 100, 1)
                disease_name = labels[class_id]

                if conf_score > 50:
                    if disease_name.lower() in ["arabica", "liberica", "robusta"]:
                        continue

                    save_location_data(source_img, disease_name, conf_score, gps_data)
                    saved_any_detections = True

                    # ✅ Upload only once per image
                    if save_to_drive and not uploaded:
                        temp_path = f"temp_{uuid.uuid4().hex}.jpg"
                        uploaded_image.save(temp_path)
                        try:
                            result = upload_image(
                                temp_path, disease_name, drive, PARENT_FOLDER_ID
                            )
                            st.toast(result)
                        except Exception as e:
                            st.error(f"Drive upload failed: {e}")
                        os.remove(temp_path)
                        uploaded = True

            if saved_any_detections:
                st.success("✅ Data saved successfully!")


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
