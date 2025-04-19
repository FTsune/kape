import streamlit as st
import PIL
import hashlib
import settings
import streamlit_antd_components as sac
from streamlit_extras.stylable_container import stylable_container
from streamlit_option_menu import option_menu
from collections import Counter, defaultdict
import time

# Import modularized components
from modules.detection_utils import (
    initialize_session_state,
    check_config_changed,
    get_cache_key,
    run_detection
)
from modules.batch_processing import process_all_images
from modules.cache_management import (
    clear_cache, 
    get_cache_size, 
    limit_cache_size,
    update_cache_entry,
    preload_adjacent_images
)
from modules.gps_utils import (
    get_gps_location,
    get_image_taken_time,
    get_location_name,
    save_location_data,
)
from modules.image_uploader import authenticate_drive
from modules.detection_runner import check_image_exists, _upload_image_once


def main(theme_colors):
    # Initialize session state variables
    initialize_session_state()
    
    # Limit cache size to prevent memory issues
    limit_cache_size(max_entries=50)

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
                    
                    # Preload adjacent images for faster pagination
                    preload_adjacent_images(uploaded_images, selected_idx, current_model_config, get_cache_key)
                
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
            config_changed = check_config_changed(current_model_config)

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

            # Handle detection in col2
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
                            caption="Sample Image: Detected",
                            use_column_width=True,
                        )
                    else:
                        # Get cache key for this image and configuration
                        cache_key = get_cache_key(source_img, current_model_config)
                        
                        # Check if we have cached results for this image + config combination
                        if cache_key in st.session_state.image_detection_cache:
                            # Use cached results
                            cached_data = st.session_state.image_detection_cache[cache_key]
                            
                            # Display the cached detection image
                            col2_placeholder.image(
                                cached_data["result_image"],
                                caption="Detected Image (Cached)",
                                use_column_width=True,
                            )
                            
                            # Restore all the detection results from cache
                            st.session_state["detected_diseases"] = cached_data["detected_diseases"]
                            st.session_state["all_disease_detections"] = cached_data["all_disease_detections"]
                            st.session_state["disease_confidences"] = cached_data["disease_confidences"]
                            st.session_state["all_disease_instances"] = cached_data["all_disease_instances"]
                            st.session_state["last_result_image"] = cached_data["result_image"]
                            st.session_state.detection_run = True
                            st.session_state.last_model_config = current_model_config.copy()
                            
                        else:
                            # Show redetect button if config changed and detection was already run
                            if config_changed and st.session_state.detection_run:
                                redetect_col1, redetect_col2, redetect_col3 = st.columns([1, 2, 1])
                                with redetect_col2:
                                    if st.button("🔄 Reanalyze objects", use_container_width=True):
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
                                        
                                        # Use Streamlit's native spinner
                                        with col2_placeholder.container():
                                            status_text = st.empty()
                                            status_text.text("Processing image...")
                                            # Create a progress bar that fills up during detection
                                            progress_bar = st.progress(0)
                                        
                                        try:
                                            # Run detection with progress updates
                                            def update_progress(value, message):
                                                try:
                                                    progress_bar.progress(value, message)
                                                    status_text.text(message)
                                                except Exception as e:
                                                    # Silently handle progress bar errors
                                                    pass

                                            results = run_detection(
                                                source_img, 
                                                current_model_config,
                                                update_progress
                                            )

                                            if results and results.get("result_image") is not None:
                                                # Store results in session state
                                                st.session_state["detected_diseases"] = results.get("detected_diseases", [])
                                                st.session_state["all_disease_detections"] = results.get("all_disease_detections", [])
                                                st.session_state["disease_confidences"] = results.get("disease_confidences", {})
                                                st.session_state["all_disease_instances"] = results.get("all_disease_instances", [])
                                                st.session_state["last_result_image"] = results["result_image"]
                                                
                                                # Cache the detection results with optimization
                                                update_cache_entry(cache_key, results)
                                                
                                                # Mark detection as run and save the current model config
                                                st.session_state.detection_run = True
                                                st.session_state.last_model_config = current_model_config.copy()
                                                
                                                # Display the result image
                                                preview_image = results["result_image"]
                                                col2_placeholder.image(
                                                    preview_image,
                                                    caption="Detected Image",
                                                    use_column_width=True,
                                                )
                                            else:
                                                st.error("Detection failed. Please try again.")
                                        except Exception as e:
                                            st.error(f"An error occurred during detection: {str(e)}")
                                        finally:
                                            # Always mark detection as no longer in progress
                                            st.session_state.detection_in_progress = False
            
            # Add pagination AFTER the image columns
            if uploaded_images and len(uploaded_images) > 1:
                with st.container():
                    # Use pagination component with a key that doesn't change with the page
                    # This helps prevent unnecessary reruns
                    new_idx = sac.pagination(
                        total=len(uploaded_images),
                        page_size=1,
                        align='center',
                        key="pagination_below_images",
                        index=selected_idx + 1  # sac.pagination is 1-indexed
                    ) - 1  # Convert back to 0-indexed
                
                # Update the selected index if changed, with debouncing to prevent multiple reruns
                if new_idx != selected_idx:
                    # Store the time of the last pagination change
                    current_time = time.time()
                    last_pagination_time = st.session_state.get("last_pagination_time", 0)
                    
                    # Only update if enough time has passed since the last change (debouncing)
                    if current_time - last_pagination_time > 0.3:  # 300ms debounce
                        st.session_state.selected_image_idx = new_idx
                        st.session_state.last_pagination_time = current_time
                        
                        # Preload the next image before rerunning
                        if new_idx + 1 < len(uploaded_images):
                            next_img = uploaded_images[new_idx + 1]
                            next_cache_key = get_cache_key(next_img, current_model_config)
                            
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

                res_col = st.columns([0.6, 0.4])
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
                        with st.container():
                            st.info("Upload an image to see disease detection summary")
                    else:
                        detected_diseases = st.session_state.get("detected_diseases", [])
                        all_detections = st.session_state.get("all_disease_detections", [])
                        disease_confidences = st.session_state.get("disease_confidences", {})
                        
                        # Display both counts for clarity
                        total_count = len(all_detections)
                        unique_count = len(detected_diseases)
                        
                        with st.container(border=True):
                            if total_count == unique_count:
                                st.markdown(f"""
                                <div style="width: 150px; padding: 20px; background-color: {secondary_background_color}; border-radius: 10px; text-align: center; margin: 20px auto;">
                                    <div style="font-size: 36px; font-weight: 600; color: {primary_color}; margin: 0; padding: 0;">{unique_count}</div>
                                    <div style="font-size: 14px; color: {text_color}80; margin-top: -10px;">Diseases Detected</div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div style="width: 150px; padding: 20px; background-color: {secondary_background_color}; border-radius: 10px; text-align: center; margin: 20px auto;">
                                    <div style="font-size: 36px; font-weight: 600; color: {primary_color}; margin: 0; padding: 0;">{total_count}</div>
                                    <div style="font-size: 14px; color: {text_color}80; margin-top: -10px;">Classes Detected</div>
                                    <div style="font-size: 13.5px; color: {text_color}80; margin-top: -5px;"><span style="color: {primary_color}; font-weight: 600;">{unique_count}</span> Unique Type(s)</div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        if detected_diseases:
                            # Build a counter for each disease
                            disease_counter = Counter(all_detections)
                            
                            for disease in detected_diseases:
                                confidence = disease_confidences.get(disease, 0)
                                count = disease_counter[disease]
                                if count > 1:
                                    st.markdown(f"""
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 10px; margin-right: 30px;">
                                        <div>
                                            <div style="display: flex; align-items: center;">
                                                <span style="margin-right: 10px;">•</span>
                                                <span style="font-weight: 600; font-size: 16px;">{disease.title()}</span>
                                            </div>
                                            <div style="margin:-5px 15px 10px; font-size: 14px;">{count} instances</div>
                                        </div>
                                        <div style="color: {text_color}80; font-size: 16px;">Confidence: <span style="font-weight: 600; color: {primary_color}">{confidence:.1f}%</span></div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown(f"""
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 10px 15px; margin-right: 30px;">
                                        <div style="display: flex; align-items: center;">
                                            <span style="margin-right: 10px;">•</span>
                                            <span style="font-weight: 600; font-size: 16px;">{disease.title()}</span>
                                        </div>
                                        <div style="color: {text_color}80; font-size: 16px;">Confidence: <span style="font-weight: 600; color: {primary_color}">{confidence:.1f}%</span></div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
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
                                    st.info("Healthy leaves are not saved to database", icon=":material/info:")
                            
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
                            with st.container():
                                st.info("No diseases detected in this image")
                
                elif tab == "Detailed Analysis":
                    if source_img is None:
                        with st.container():
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

                        st.markdown("##### Image Metadata")
                        st.write(f"- **Location**: `{location_name}`")
                        if gps_data:
                            st.write(
                                f"- **Latitude**: `{gps_data.get('latitude', 'N/A')}`"
                            )
                            st.write(
                                f"- **Longitude**: `{gps_data.get('longitude', 'N/A')}`"
                            )
                        else:
                            st.write("- **Latitude**: `Unavailable`")
                            st.write("- **Longitude**: `Unavailable`")
                        if image_date:
                            st.write(f"- **Date Taken**: `{image_date}`")
                        
                        # Show all disease instances with their individual confidence levels
                        st.markdown(f"""<div style="margin: 10px 15px 10px 5px; font-size: 20px; font-weight: 600; color: {primary_color}">
                                    All Instances
                                    </div>""", unsafe_allow_html=True)
                        all_instances = st.session_state.get("all_disease_instances", [])
                        if all_instances:
                            # Group instances by disease type for better organization
                            grouped_instances = defaultdict(list)
                            
                            for disease, confidence in all_instances:
                                grouped_instances[disease].append(confidence)
                            
                            # Display each disease type with all its instances
                            for disease, confidences in grouped_instances.items():
                                with st.expander(f"**{disease.title()}** - {len(confidences)} instance(s)"):
                                
                                    # Display each individual instance with its confidence
                                    for i, conf in enumerate(confidences, 1):
                                        st.markdown(f"  - Instance {i}: Confidence **{conf:.1f}%**")
                        else:
                            st.info("No disease instances detected in this image")

    # Cache management in sidebar
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