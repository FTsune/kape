import streamlit as st
import PIL
from PIL import Image
import hashlib
import time
import streamlit_antd_components as sac
from streamlit_option_menu import option_menu
from collections import Counter, defaultdict
from streamlit_extras.stylable_container import stylable_container
import json
import random

# Import necessary functions from your modules
from modules.detection_utils import (
    check_config_changed,
    get_cache_key,
    run_detection
)
from modules.cache_management import (
    update_cache_entry,
    preload_adjacent_images
)
from modules.gps_utils import (
    get_gps_location,
    get_image_taken_time,
    get_location_name,
    save_location_data,
)
from modules.detection_runner import check_image_exists, _upload_image_once

from components.ui.instructions import top_bar, instructions_header, subtitle, step_item, note_banner

# Load disease data from the json file
def load_disease_data():
    try:
        with open('components/dataset/diseases.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading diseases.json: {e}")
        return []

# Fix the get_random_solution function to handle partial matches like "rust" matching "Leaf Rust"
def get_random_solution(disease_name, disease_data):
    """Get a random solution for a given disease from the disease data."""
    # First try exact match
    for disease in disease_data:
        if disease["title"].lower() == disease_name.lower() or disease["name2"].lower() == disease_name.lower():
            if disease.get("solution") and len(disease["solution"]) > 0:
                return random.choice(disease["solution"])
    
    # If no exact match, try partial match
    for disease in disease_data:
        if disease_name.lower() in disease["title"].lower() or disease_name.lower() in disease["name2"].lower():
            if disease.get("solution") and len(disease["solution"]) > 0:
                return random.choice(disease["solution"])
    
    return None

def render_instructions(theme, primary_color, secondary_background_color, text_color, default_image_path, batch_mode=False):
    st.markdown(top_bar(), unsafe_allow_html=True)
    st.markdown(instructions_header(primary_color, text_color), unsafe_allow_html=True)
    st.markdown(subtitle(text_color), unsafe_allow_html=True)

    steps = [
        "Configure the model settings in the sidebar",
        "Upload a valid image file (jpeg, jpg, webp, png)",
        "Avoid bluriness and make sure the leaf is the main focus of the image",
        "The system will detect diseases based on your configuration",
        "Results will display detected diseases and confidence scores"
    ]
    
    for i, step in enumerate(steps, 1):
        st.markdown(step_item(i, step, primary_color, text_color), unsafe_allow_html=True)

    st.markdown(note_banner(primary_color), unsafe_allow_html=True)
    st.warning('Our model is currently optimized to detect diseases only in coffee leaves.', icon=':material/info:')
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    with stylable_container(
        key='uploader_container',
        css_styles=f"""
        {{
            margin: auto;
        }}
        """
    ):
        # File uploader with dynamic accept_multiple_files based on batch_mode
        uploaded_files = st.file_uploader(
            "Upload Image(s)",
            type=["jpg", "jpeg", "png", "bmp", "webp"],
            accept_multiple_files=batch_mode,
            key="instructions_uploader",  # Use a different key than the sidebar uploader
            label_visibility='collapsed'
        )
    
    # Check if file is uploaded
    has_file = uploaded_files is not None
    if isinstance(uploaded_files, list):
        has_file = len(uploaded_files) > 0
        
    return uploaded_files, has_file

def render_results(theme, primary_color, secondary_background_color, text_color, background_color, source_img=None, uploaded_images=None, current_model_config=None, drive=None, PARENT_FOLDER_ID=None):
    """
    Renders the results UI with actual detection logic
    """
    st.markdown(
        """
        <div style="height: 4px; background: linear-gradient(to right, #4dd6c1, #37b8a4, #2aa395); width: 100%; margin-bottom: 20px;"></div>
        """, 
        unsafe_allow_html=True
    )
    
    # Initialize variables
    selected_idx = 0
    batch_mode = st.session_state.get("batch_mode", False)
    
    # Load disease data from json file
    disease_data = load_disease_data()
    
    # Handle both single and multiple file uploads
    if batch_mode and uploaded_images and len(uploaded_images) > 0:
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
    config_changed = check_config_changed(current_model_config)

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
        # Display the images and detection results
        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                image_placeholder = st.empty()
                st.session_state["image_placeholder"] = image_placeholder
                
                if source_img is None:
                    st.info("No image uploaded")
                else:
                    uploaded_image = Image.open(source_img)

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
            with st.container(border=True):
                col2_placeholder = st.empty()
                st.session_state["detection_placeholder"] = col2_placeholder

                if source_img is None:
                    st.info("No image to detect")
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
                            caption="Detected Image",
                            use_column_width=True,
                        )
                        
                        # Restore all the detection results from cache
                        st.session_state["detected_diseases"] = cached_data["detected_diseases"]
                        st.session_state["all_disease_detections"] = cached_data["all_disease_detections"]
                        st.session_state["disease_confidences"] = cached_data["disease_confidences"]
                        st.session_state["all_disease_instances"] = cached_data["all_disease_instances"]
                        st.session_state["last_result_image"] = cached_data["result_image"]
                        st.session_state["processing_time"] = cached_data.get("processing_time", 0)
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
                                        # Record start time
                                        start_time = time.time()
                                        
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
                                        
                                        # Record end time and calculate duration
                                        end_time = time.time()
                                        processing_time = end_time - start_time
                                        st.session_state["processing_time"] = processing_time

                                        if results and results.get("result_image") is not None:
                                            # Store results in session state
                                            st.session_state["detected_diseases"] = results.get("detected_diseases", [])
                                            st.session_state["all_disease_detections"] = results.get("all_disease_detections", [])
                                            st.session_state["disease_confidences"] = results.get("disease_confidences", {})
                                            st.session_state["all_disease_instances"] = results.get("all_disease_instances", [])
                                            st.session_state["last_result_image"] = results["result_image"]
                                            
                                            # Cache the detection results with optimization
                                            results["processing_time"] = st.session_state.get("processing_time", 0)
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
        
        # Add pagination AFTER the image columns - only show if in batch mode and multiple images
        if batch_mode and uploaded_images and len(uploaded_images) > 1:
            with st.container():
                # Use pagination component
                new_idx = sac.pagination(
                    total=len(uploaded_images),
                    page_size=1,
                    align='center',
                    key="pagination_below_images",
                    index=selected_idx + 1  # sac.pagination is 1-indexed
                ) - 1  # Convert back to 0-indexed
            
                # Update the selected index if changed
                if new_idx != selected_idx:
                    st.session_state.selected_image_idx = new_idx
                    
                    # Preload adjacent images to improve pagination performance
                    preload_adjacent_images(
                        uploaded_images, 
                        new_idx, 
                        current_model_config,
                        run_detection
                    )
                    
                    st.rerun()  # Rerun to load the new image

        # Display detection results
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
                        # Create two columns for the stats boxes
                        stat_col1, stat_col2 = st.columns(2)
                                
                        with stat_col1:
                            if total_count == unique_count:
                                st.markdown(f"""
                                <div style="width: 150px; padding: 20px; background-color: {secondary_background_color}; border-radius: 10px; text-align: center; margin: 0 auto;">
                                    <div style="font-size: 36px; font-weight: 600; color: {primary_color}; margin: 0; padding: 0;">{unique_count}</div>
                                    <div style="font-size: 14px; color: {text_color}80; margin-top: -10px;">Class Detected</div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div style="width: 150px; padding: 20px; background-color: {secondary_background_color}; border-radius: 10px; text-align: center; margin: 0 auto;">
                                    <div style="font-size: 36px; font-weight: 600; color: {primary_color}; margin: 0; padding: 0;">{total_count}</div>
                                    <div style="font-size: 14px; color: {text_color}80; margin-top: -10px;">Classes Detected</div>
                                    <div style="font-size: 13.5px; color: {text_color}80; margin-top: -5px;"><span style="color: {primary_color}; font-weight: 600;">{unique_count}</span> Unique Type(s)</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                        with stat_col2:
                            # Get processing time from session state
                            processing_time = st.session_state.get("processing_time", 0)
                            # Format time nicely
                            if processing_time < 1:
                                time_display = f"{processing_time*1000:.0f}ms"
                            else:
                                time_display = f"{processing_time:.2f}s"
                                        
                            st.markdown(f"""
                            <div style="width: 150px; padding: 20px; background-color: {secondary_background_color}; border-radius: 10px; text-align: center; margin: 0 auto;">
                                <div style="font-size: 36px; font-weight: 600; color: {primary_color}; margin: 0; padding: 0;">{time_display}</div>
                                <div style="font-size: 14px; color: {text_color}80; margin-top: -10px;">Processing Time</div>
                            </div>
                            """, unsafe_allow_html=True)
                                
                        st.markdown('<div style="margin: 10px;></div>"', unsafe_allow_html=True)
                            
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
                        
                        # Get all instances from session state
                        all_instances = st.session_state.get("all_disease_instances", [])
                        
                        # Filter for leaf types and disease types
                        leaf_types = ["arabica", "liberica", "robusta"]
                        leaf_instances = [inst for inst in all_instances if inst[0].lower() in leaf_types]
                        disease_instances = [inst for inst in all_instances if inst[0].lower() not in leaf_types]
                        
                        # Check if only leaf types or healthy leaves are detected
                        only_leaf_types = all(disease.lower() in leaf_types for disease in detected_diseases)
                        only_healthy = len(detected_diseases) == 1 and detected_diseases[0].lower() == "healthy"
                        only_healthy_and_leaves = all(disease.lower() == "healthy" or disease.lower() in leaf_types for disease in detected_diseases)
                        
                            # Disable buttons if:
                            # 1. Using Leaf model (only for leaf detection)
                            # 2. Only leaf types detected (no diseases)
                            # For database only:
                        db_buttons_disabled = (
                            current_model_config.get("detection_model_choice", "") == "Leaf" or  # Leaf model only
                            only_leaf_types or       # Only leaf types detected
                            only_healthy or          # Only healthy leaves
                            only_healthy_and_leaves  # Only healthy leaves + leaf types
                        )
                        
                        # For Drive, allow healthy leaves but not leaf types
                        drive_buttons_disabled = (
                            current_model_config.get("detection_model_choice", "") == "Leaf" or  # Leaf model only
                            only_leaf_types         # Only leaf types detected
                        )
                        
                        # Add buttons for saving data and uploading to drive
                        col1, col2 = st.columns(2)
                                
                        with col1:
                            # Disable button if already saved or buttons should be disabled
                            db_button_disabled = st.session_state.saved_to_database or db_buttons_disabled
                            
                            if db_buttons_disabled and not st.session_state.saved_to_database:
                                if current_model_config.get("detection_model_choice", "") == "Leaf":
                                    st.info("Coffee leaf types are not saved to database", icon=":material/info:")
                                elif only_leaf_types:
                                    st.info("Coffee leaf types are not saved to database", icon=":material/info:")
                                elif only_healthy:
                                    st.info("Healthy leaves are not saved to database", icon=":material/info:")
                                elif only_healthy_and_leaves:
                                    st.info("Healthy leaves and leaf types are not saved to database", icon=":material/info:")
                            else:
                                if st.button("💾 Save to Database", 
                                        use_container_width=True, 
                                        disabled=db_button_disabled):
                                    try:
                                        gps_data = get_gps_location(source_img)
                                                
                                        with st.spinner("Saving to database..."):
                                            # Filter out leaf types and healthy leaves when saving
                                            saveable_diseases = [d for d in detected_diseases 
                                                                if d.lower() not in leaf_types and 
                                                                d.lower() != "healthy"]
                                            
                                            # Get confidence scores and filter those >= 60%
                                            high_confidence_diseases = []
                                            for disease in saveable_diseases:
                                                confidence = disease_confidences.get(disease, 0)
                                                if confidence >= 60:
                                                    high_confidence_diseases.append((disease, confidence))
                                            
                                            if not high_confidence_diseases:
                                                st.warning("Confidence score is too low. Try another image.")
                                            else:
                                                for disease, confidence in high_confidence_diseases:
                                                    save_location_data(source_img, disease, confidence, gps_data)
                                                        
                                                st.session_state.saved_to_database = True
                                                st.success("✅ Data saved successfully to database!")
                                    except Exception as e:
                                        st.error(f"Error saving data: {e}")
                                        
                                if db_button_disabled and st.session_state.saved_to_database:
                                    st.info("✓ Already saved to database")
                                
                        with col2:
                            # Check if image already exists in Drive
                            image_exists = False
                            if source_img:
                                try:
                                    image_exists = check_image_exists(drive, PARENT_FOLDER_ID, source_img.name)
                                except:
                                    # If check fails, assume it doesn't exist
                                    pass
                                    
                            # Disable button if already saved, image exists, or buttons should be disabled
                            drive_button_disabled = st.session_state.saved_to_drive or image_exists or drive_buttons_disabled
                                    
                            if drive_buttons_disabled and not st.session_state.saved_to_drive:
                                if current_model_config.get("detection_model_choice", "") == "Leaf":
                                    st.info("Coffee leaf types are not saved to Drive", icon=":material/info:")
                                elif only_leaf_types:
                                    st.info("Coffee leaf types are not saved to Drive", icon=":material/info:")
                            else:
                                if st.button("☁️ Save to Drive", 
                                        use_container_width=True,
                                        disabled=drive_button_disabled):
                                    try:
                                        uploaded_image = PIL.Image.open(source_img)
                                                
                                        # Double-check if image exists before uploading
                                        if check_image_exists(drive, PARENT_FOLDER_ID, source_img.name):
                                            st.warning("⚠️ This image already exists in Google Drive")
                                        else:
                                            # Filter out leaf types when selecting label, but keep "Healthy"
                                            saveable_diseases = [d for d in detected_diseases 
                                                                if d.lower() not in leaf_types]
                                            
                                            if not saveable_diseases:
                                                st.warning("No saveable diseases detected")
                                            else:
                                                # Get all disease instances with their confidence scores
                                                all_instances = st.session_state.get("all_disease_instances", [])
                                                
                                                # Create a dictionary to track highest confidence per disease
                                                highest_confidence = {}
                                                
                                                # Find highest confidence for each unique disease
                                                for disease, confidence in all_instances:
                                                    # Skip leaf types
                                                    if disease.lower() in leaf_types:
                                                        continue
                                                    
                                                    # Update highest confidence for this disease
                                                    if disease not in highest_confidence or confidence > highest_confidence[disease]:
                                                        highest_confidence[disease] = confidence
                                                
                                                # Filter diseases with confidence >= 60%
                                                high_confidence_diseases = {disease: confidence for disease, confidence in highest_confidence.items() if confidence >= 60}
                                                
                                                if not high_confidence_diseases:
                                                    st.warning("Confidence score is too low. Try another image.")
                                                else:
                                                    # Save to each disease folder
                                                    success_count = 0
                                                    for disease, confidence in high_confidence_diseases.items():
                                                        # Create a temporary copy of the image for each upload
                                                        temp_img = uploaded_image.copy()
                                                        _upload_image_once(temp_img, disease, drive, PARENT_FOLDER_ID)
                                                        success_count += 1
                                                    
                                                    st.session_state.saved_to_drive = True
                                                    st.success(f"✅ Image uploaded to {success_count} disease folders in Google Drive!")
                                    except Exception as e:
                                        st.error(f"Error uploading to Drive: {e}")
                                        
                                if drive_button_disabled and st.session_state.saved_to_drive:
                                    st.info("✓ Already saved to Drive")
                                elif drive_button_disabled and image_exists:
                                    st.warning("⚠️ This image already exists in Google Drive")
                    else:
                        with st.container():
                            st.info("No class detected in this image")
                    
            elif tab == "Detailed Analysis":
                if source_img is None:
                    with st.container():
                        st.info("Upload an image to see detailed analysis")
                else:
                    # Show all leaf and disease instances with their individual confidence levels
                    # First, add a dedicated section for leaf types
                    model_type = current_model_config.get("detection_model_choice", "")
                    if model_type in ["Leaf", "Both Models"]:
                        
                        # Get leaf instances from all_disease_instances
                        all_instances = st.session_state.get("all_disease_instances", [])
                        leaf_instances = [inst for inst in all_instances if inst[0].lower() in ["arabica", "liberica", "robusta"]]
                        
                        if leaf_instances:
                            with st.expander('Leaf Types'):
                                for leaf_type, score in leaf_instances:
                                    st.markdown(f"- **{leaf_type.title()}**: {score:.1f}% confidence")
                        else:
                            with st.container():
                                st.info("No leaf type detected in this image")
                    
                    # Add Image Metadata section
                    st.markdown(f"""<div style="margin: 10px 15px 10px 5px; font-size: 20px; font-weight: 600; color: {primary_color}">
                                Image Metadata
                                </div>""", unsafe_allow_html=True)

                    # Get image metadata
                    date_taken = get_image_taken_time(source_img)
                    gps_data = get_gps_location(source_img)
                    location_name = None
                    if gps_data and gps_data.get("latitude") and gps_data.get("longitude"):
                        location_name = get_location_name(gps_data["latitude"], gps_data["longitude"])

                    # Display metadata in a clean format
                    with st.container():
                        if date_taken or location_name:
                            if date_taken:
                                st.markdown(f"📍 **Date Taken**: {date_taken.strftime('%B %d, %Y')}")
                            if location_name:
                                st.markdown(f"📅 **Location**: {location_name}")
                        else:
                            st.info("No metadata available for this image")
                    
                    # Add a Recommendation section for detected diseases
                    st.markdown(f"""<div style="margin: 10px 15px 10px 5px; font-size: 20px; font-weight: 600; color: {primary_color}">
                                Recommendations
                                </div>""", unsafe_allow_html=True)
                    
                    # Get detected diseases and filter out leaf types
                    detected_diseases = st.session_state.get("detected_diseases", [])
                    leaf_types = ["arabica", "liberica", "robusta"]
                    disease_instances = [disease for disease in detected_diseases if disease.lower() not in leaf_types and disease.lower() != "healthy"]
                    
                    if disease_instances:
                        for disease in disease_instances:
                            solution = get_random_solution(disease, disease_data)
                            if solution:
                                with st.container():    
                                    st.markdown(
                                        f"""
                                        <div style="margin-left: 0.95em; margin-bottom: 1.5em;">
                                            <div style="font-weight: 600; font-size: 1em;">• {disease.title()}</div>
                                            <div style="margin-top: 0.5px; margin-bottom: 1em; font-style: italic; font-size: 0.85rem;">Recommendation: {solution}</div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                    else:
                        if any(disease.lower() == "healthy" for disease in detected_diseases):
                            with st.container():
                                st.success("👍 Your coffee leaf appears healthy! No treatment needed.")
                        else:
                            with st.container():
                                st.info("No disease instances requiring recommendations detected in this image")
                                
                    # Then show the disease instances
                    st.markdown(f"""<div style="margin: 10px 15px 10px 5px; font-size: 20px; font-weight: 600; color: {primary_color}">
                                All Class Instances
                                </div>""", unsafe_allow_html=True)
                    all_instances = st.session_state.get("all_disease_instances", [])
                    # Filter out leaf types for the disease section
                    disease_instances = [inst for inst in all_instances if inst[0].lower() not in ["arabica", "liberica", "robusta"]]
                    
                    if disease_instances:
                        # Group instances by disease type for better organization
                        grouped_instances = defaultdict(list)
                                
                        for disease, confidence in disease_instances:
                            grouped_instances[disease].append(confidence)
                                
                        # Display each disease type with all its instances
                        for disease, confidences in grouped_instances.items():
                            with st.expander(f"**{disease.title()}** - {len(confidences)} instance(s)"):
                                    
                                # Display each individual instance with its confidence
                                for i, conf in enumerate(confidences, 1):
                                    st.markdown(f"  - Instance {i}: Confidence **{conf:.1f}%**")
                    else:
                        with st.container():
                            st.info("No class/disease instances detected in this image")

        # Add a button to go back to instructions
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Try another image", use_container_width=True):
                # Clear the uploaded files in session state
                st.session_state["uploaded_files"] = None
                # Don't try to modify the widget key directly
                # Instead, we'll handle this in the manage_ui_state function
                st.rerun()

def manage_ui_state(theme_colors):
    """
    Main function to manage UI state
    """
    # Set up theme variables
    theme = theme_colors["DARK"] if st.session_state.get("dark_theme", True) else theme_colors["LIGHT"]
    primary_color = theme["primaryColor"]
    background_color = theme["backgroundColor"]
    secondary_background_color = theme["secondaryBackgroundColor"]
    text_color = theme["textColor"]
    
    # Get batch mode setting
    batch_mode = st.session_state.get("batch_mode", False)
    
    # Check if batch mode was just toggled
    if "previous_batch_mode" in st.session_state and st.session_state.previous_batch_mode != batch_mode:
        # Reset uploaded files to return to instructions view when batch mode changes
        st.session_state["uploaded_files"] = None
    
    # Store current batch mode for next comparison
    st.session_state["previous_batch_mode"] = batch_mode
    
    # Get current model config
    current_model_config = st.session_state.get("current_model_config", {})
    
    # Default image path
    default_image_path = str(st.session_state.get("DEFAULT_IMAGE", ""))
    
    # Get drive for Google Drive integration
    drive = st.session_state.get("drive")
    PARENT_FOLDER_ID = st.session_state.get("PARENT_FOLDER_ID")
    
    # Get uploaded files from session state
    uploaded_files = st.session_state.get("uploaded_files")
    
    # If no files are in session state, render instructions with file uploader
    if not uploaded_files:
        new_uploaded_files, has_file = render_instructions(
            theme, 
            primary_color, 
            secondary_background_color, 
            text_color, 
            default_image_path,
            batch_mode
        )
        
        # If files were uploaded in the instructions UI, update session state
        if has_file:
            st.session_state["uploaded_files"] = new_uploaded_files
            st.rerun()  # Rerun to show results UI
    else:
        # Initialize source_img before pagination
        source_img = None
        if uploaded_files:
            # Handle both single file and batch mode
            if batch_mode:
                # In batch mode, use the selected index
                selected_idx = st.session_state.get("selected_image_idx", 0)
                if selected_idx < len(uploaded_files):
                    source_img = uploaded_files[selected_idx]
            else:
                # In single mode, just use the file directly
                if not isinstance(uploaded_files, list):
                    source_img = uploaded_files
                elif len(uploaded_files) > 0:
                    source_img = uploaded_files[0]
        
        # Show results if an image is uploaded
        render_results(
            theme, 
            primary_color, 
            secondary_background_color, 
            text_color,
            background_color,
            source_img, 
            uploaded_files, 
            current_model_config,
            drive,
            PARENT_FOLDER_ID
        )