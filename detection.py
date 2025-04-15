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
from streamlit_extras.stylable_container import stylable_container

from modules.gps_utils import (
    get_gps_location,
    get_image_taken_time,
    get_location_name,
    save_location_data,
)
from modules.processing import non_max_suppression
from modules.visualizations import draw_bounding_boxes
from modules.detection_runner import detect_and_save_silently
from modules.image_uploader import authenticate_drive, upload_image
from modules.detection_runner import generate_preview_image


def main(theme_colors):
    if "dark_theme" not in st.session_state:
        st.session_state.dark_theme = False

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
        ["Default (Spots + Full Leaf)", "YOLOv11m - Full Leaf"],
        index=0,
        key="disease_model_mode",
    )

    detection_model_choice = st.sidebar.selectbox(
        "Select Detection Model", ("Disease", "Leaf", "Both Models"), index=0
    )

    adv_opt = st.sidebar.toggle("Advanced Options")
    confidence = 0.4
    overlap_threshold = 0.3
    if adv_opt:
        confidence = float(st.sidebar.slider("Model Confidence", 25, 100, 40)) / 100
        overlap_threshold = (
            float(st.sidebar.slider("Overlap Threshold", 0, 100, 30)) / 100
        )

    save_to_drive = st.sidebar.checkbox("📤 Save samples to improve the model")

    @st.cache_resource
    def get_drive():
        return authenticate_drive()

    drive = get_drive()
    PARENT_FOLDER_ID = "1OgdV5CRT61ujv1uW1SSgnesnG59bT5ss"

    uploaded_images = st.sidebar.file_uploader(
        "Upload image(s)",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        accept_multiple_files=True,
        key="multi_image_uploader",
    )

    if uploaded_images:
        with stylable_container(
            key="preview_selector_container",
            css_styles=f"""
                background-color: {secondary_background_color};
                padding: 0.5rem 1rem 0.75rem;
                border-radius: 8px;
                margin-bottom: 1rem;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            """,
        ):
            st.markdown(
                f"<p style='margin: 0 0 0.25rem; font-weight: 600; font-size: 1rem; color: {primary_color};'>📷 Select an image to preview</p>",
                unsafe_allow_html=True,
            )

            selected_idx = st.selectbox(
                label="",
                options=range(len(uploaded_images)),
                format_func=lambda i: uploaded_images[i].name,
                key="main_preview_selector",
            )

            source_img = uploaded_images[selected_idx]
    else:
        source_img = None

    with stylable_container(
        key="container_with_border",
        css_styles=f"""
        background-color: {secondary_background_color};
        border-radius: 10px;
        padding: calc(1em - 1px);
        max-width: 694px;
        margin: auto;
        box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        """,
    ):
        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                image_placeholder = st.empty()
                st.session_state["image_placeholder"] = image_placeholder
                default_image_path = str(settings.DEFAULT_DETECT_IMAGE)

                if source_img is None:
                    default_image = PIL.Image.open(default_image_path)
                    image_placeholder.image(
                        default_image,
                        caption="Sample Image: Objects Detected",
                        use_column_width=True,
                    )
                else:
                    uploaded_image = PIL.Image.open(source_img)

                    if (
                        "last_uploaded_filename" not in st.session_state
                        or st.session_state["last_uploaded_filename"] != source_img.name
                    ):
                        st.session_state["last_uploaded_filename"] = source_img.name
                        st.session_state["last_result_image"] = None

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

                    if st.session_state.get("last_result_image") is not None:
                        image_placeholder.image(
                            st.session_state["last_result_image"],
                            caption="Detected Image",
                            use_column_width=True,
                        )
                    else:
                        # 🔁 Auto-generate preview (no saving)
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
                        image_placeholder.image(
                            preview_image,
                            caption="Detected Image",
                            use_column_width=True,
                        )

        with col2:
            with stylable_container(
                key="container_with_border1",
                css_styles=f"""
                background-color: {background_color};
                border-radius: 10px;
                max-width: 694px;
                """,
            ):
                col2_placeholder = st.empty()

                with col2_placeholder.container():
                    if source_img is None:
                        st.markdown(
                            f"<p style='border-radius: 10px 10px 0px 0px; border: 1px solid; border-bottom: 0px; padding: 12px; font-weight: bold; font-size: 1.35rem; color: {primary_color}'>INSTRUCTIONS</p>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"""
                            <p style='border-right: 1px solid {primary_color}; border-left: 1px solid {primary_color}; font-size: 1rem; margin: -30px 0; padding: 12px 12px 25px; color: {text_color}'>
                                Open the sidebar to start configuring.
                                Upload a valid image file (jpeg, jpg, webp, png) and click "Detect Objects".
                                Wait for a few seconds until it's done detecting objects.
                                <br><br>
                                Ensure that the photo clearly shows a coffee leaf. Avoid bluriness and make
                                sure the leaf is the main focus of the image. 
                            </p>
                        """,
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"""
                            <p style='border: 1px solid; border-top: 0px; font-size: 1rem; color: {primary_color}; margin-top: 10px; padding: 10px; border-radius: 0 0 10px 10px'>
                                Our model is currently optimized to detect diseases only in coffee leaves.
                            </p>
                        """,
                            unsafe_allow_html=True,
                        )
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

                        st.markdown(f"- **Location**: `{location_name}`")
                        if gps_data:
                            st.markdown(
                                f"- **Latitude**: `{gps_data.get('latitude', 'N/A')}`"
                            )
                            st.markdown(
                                f"- **Longitude**: `{gps_data.get('longitude', 'N/A')}`"
                            )
                        else:
                            st.markdown("- **Latitude**: `Unavailable`")
                            st.markdown("- **Longitude**: `Unavailable`")
                        if image_date:
                            st.markdown(f"- **Date Taken**: `{image_date}`")

    if source_img:
        uploaded_image = PIL.Image.open(source_img)

        gps_data = get_gps_location(source_img)
        if gps_data:
            with st.expander("Image Location Data", expanded=True):
                st.write(f"Latitude: {gps_data['latitude']:.6f}°")
                st.write(f"Longitude: {gps_data['longitude']:.6f}°")
                if gps_data.get("altitude"):
                    st.write(f"Altitude: {float(gps_data['altitude']):.1f}m")
                st.map({"lat": [gps_data["latitude"]], "lon": [gps_data["longitude"]]})

    # Start detection
    if source_img and st.sidebar.button("Run Detection"):
        try:
            # Load model once

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

            # GPS data
            gps_data = get_gps_location(source_img)

            from modules.detection_runner import handle_detection

            handle_detection(
                PIL.Image.open(source_img),
                source_img,
                gps_data,
                detection_model_choice,
                model,
                model_leaf,
                model_disease,
                confidence,
                overlap_threshold,
                save_to_drive,
                drive,
                PARENT_FOLDER_ID,
                cdisease_colors,
                cleaf_colors,
            )

        except Exception as e:
            st.error(f"Something went wrong during detection: {e}")

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
