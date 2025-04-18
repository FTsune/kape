import streamlit as st
from pathlib import Path
import PIL
from modules.gps_utils import get_gps_location
from modules.detection_runner import detect_and_save_silently
from modules.detection_utils import load_models

def process_all_images(uploaded_images, detection_model_choice, disease_model_mode, confidence, overlap_threshold, save_to_drive, drive, PARENT_FOLDER_ID, cdisease_colors, cleaf_colors, settings):
    """Process all uploaded images in batch mode."""
    if not uploaded_images:
        st.warning("No images to process.")
        return
        
    with st.spinner("Running detection and saving..."):
        status_text = st.empty()
        progress = st.progress(0)
        total = len(uploaded_images)

        try:
            # Load models once
            model, model_leaf, model_disease = load_models(detection_model_choice, disease_model_mode)

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
                    st.error(f"❌ Failed: {file.name}: {str(e)}")
                
                try:
                    # Update progress safely
                    progress.progress((idx + 1) / total)
                except:
                    pass

            status_text.markdown("✅ **All images processed and saved.**")
        except Exception as e:
            st.error(f"Error in batch processing: {str(e)}")
