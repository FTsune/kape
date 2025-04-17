import streamlit as st
from collections import Counter, defaultdict
from modules.gps_utils import (
    get_gps_location,
    get_image_taken_time,
    get_location_name,
    save_location_data,
)
from modules.detection_runner import check_image_exists
from modules.detection_runner import _upload_image_once

def display_summary_tab(source_img, drive, PARENT_FOLDER_ID):
    """Display the summary tab with disease detection results"""
    if source_img is None:
        st.info("Upload an image to see disease detection summary")
        return
        
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
                    import PIL
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

def display_detailed_analysis_tab(source_img):
    """Display the detailed analysis tab with metadata and confidence scores"""
    if source_img is None:
        st.info("Upload an image to see detailed analysis")
        return
        
    st.markdown("### Detailed Analysis")
    
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
    st.markdown("#### All Disease Instances")
    
    all_instances = st.session_state.get("all_disease_instances", [])
    if all_instances:
        # Group instances by disease type for better organization
        grouped_instances = defaultdict(list)
        
        for disease, confidence in all_instances:
            grouped_instances[disease].append(confidence)
        
        # Display each disease type with all its instances
        for disease, confidences in grouped_instances.items():
            st.markdown(f"**{disease.title()}** - {len(confidences)} instance(s)")
            
            # Display each individual instance with its confidence
            for i, conf in enumerate(confidences, 1):
                st.markdown(f"  - Instance {i}: Confidence **{conf:.1f}%**")
            
            st.markdown("---")
    else:
        st.info("No disease instances detected in this image")