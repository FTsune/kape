import os
import uuid
import numpy as np
import streamlit as st
from modules.gps_utils import save_location_data
from modules.image_uploader import upload_image
from modules.processing import non_max_suppression
from modules.visualizations import draw_bounding_boxes


def save_prediction_if_valid(
    name,
    score,
    uploaded_image,
    source_img,
    gps_data,
    save_to_drive,
    drive,
    parent_folder_id,
    uploaded_flag,
):
    """Saves to Sheets if label is valid. Uploads to Drive always if confidence >= 50."""
    SKIP_LABELS = {"healthy", "abiotic"}
    saved = False

    # Sheets: skip if low confidence or unwanted label
    if score >= 50 and name.lower() not in SKIP_LABELS:
        save_location_data(source_img, name, score, gps_data)
        saved = True

    # Drive: upload anything with score >= 50
    if score >= 50 and save_to_drive and not uploaded_flag:
        _upload_image_once(uploaded_image, name, drive, parent_folder_id)
        uploaded_flag = True
        saved = True

    return saved, uploaded_flag


def detect_and_save_silently(
    uploaded_image,
    image_file,
    gps_data,
    model_type,
    model,
    model_leaf,
    model_disease,
    confidence,
    overlap_threshold,
    save_to_drive,
    drive,
    parent_folder_id,
    cdisease_colors,
    cleaf_colors,
):
    """Silent detection that only saves valid diseases (no leaf logic)."""

    result_image = np.array(uploaded_image)
    detections = []

    def process_boxes(res, labels):
        boxes = non_max_suppression(res[0].boxes, overlap_threshold)
        current_detections = []
        for box in boxes:
            class_id = int(box.cls[0])
            score = round(float(box.conf[0]) * 100, 1)
            raw_name = labels[class_id]
            name = normalize_label(raw_name)
            current_detections.append((name, score))
        return current_detections

    if model_type in ["Disease", "Both Models"]:
        used_model = model if model_type == "Disease" else model_disease

        if isinstance(used_model, tuple):
            res1 = used_model[0].predict(uploaded_image, conf=confidence)
            detections += process_boxes(res1, res1[0].names)
            res2 = used_model[1].predict(uploaded_image, conf=confidence)
            detections += process_boxes(res2, res2[0].names)
        else:
            res = used_model.predict(uploaded_image, conf=confidence)
            detections += process_boxes(res, res[0].names)

    if detections:
        best_name, best_score = sorted(detections, key=lambda x: x[1], reverse=True)[0]

        if best_score < 50:
            return f"Skipped (low confidence: {best_score}%)", best_score

        saved, _ = save_prediction_if_valid(
            name=best_name,
            score=best_score,
            uploaded_image=uploaded_image,
            source_img=image_file,
            gps_data=gps_data,
            save_to_drive=save_to_drive,
            drive=drive,
            parent_folder_id=parent_folder_id,
            uploaded_flag=False,
        )

        return (
            (best_name, best_score) if saved else (f"Skipped ({best_name})", best_score)
        )

    return "No Detection", 0


def get_highest_confidence_detections(results):
    highest = {}
    for name, score in results:
        if name not in highest or score > highest[name]:
            highest[name] = score
    return highest


def generate_preview_image(
    uploaded_image,
    model_type,
    model,  # In Disease mode, this is the disease tuple
    model_leaf,
    model_disease,  # Used only in Both Models mode
    confidence,
    overlap_threshold,
    cdisease_colors,
    cleaf_colors,
):
    from modules.processing import non_max_suppression
    from modules.visualizations import draw_bounding_boxes
    import numpy as np

    def normalize_label(raw_name):
        """Normalize label names"""
        # Convert underscores to spaces and capitalize
        name = raw_name.lower()
        
        # Special case handling
        if name == "late-stage-rust":
            return "rust"
        
        # Return the name with title case
        return name

    try:
        if model_type == "Disease":
            # Check if 'model' (the disease model input) is a tuple
            if isinstance(model, tuple):
                result_image = np.array(uploaded_image)

                # Process first disease model (use original labels for image drawing)
                result1 = model[0].predict(uploaded_image, conf=confidence)
                boxes1 = non_max_suppression(result1[0].boxes, overlap_threshold)
                labels1 = result1[
                    0
                ].names  # remain as predicted (e.g. "late-stage-rust")
                result_image = draw_bounding_boxes(
                    result_image, boxes1, labels1, cdisease_colors, normalize_label=normalize_label
                )

                # Process second disease model
                result2 = model[1].predict(uploaded_image, conf=confidence)
                boxes2 = non_max_suppression(result2[0].boxes, overlap_threshold)
                labels2 = result2[0].names
                result_image = draw_bounding_boxes(
                    result_image, boxes2, labels2, cdisease_colors, normalize_label=normalize_label
                )

                return result_image
            else:
                # Single disease model
                result = model.predict(uploaded_image, conf=confidence)
                boxes = non_max_suppression(result[0].boxes, overlap_threshold)
                labels = result[0].names
                return draw_bounding_boxes(
                    uploaded_image, boxes, labels, cdisease_colors, normalize_label=normalize_label
                )

        elif model_type == "Leaf":
            # Ensure model is not None
            if model is not None:
                result = model.predict(uploaded_image, conf=confidence)
                boxes = non_max_suppression(result[0].boxes, overlap_threshold)
                labels = result[0].names
                return draw_bounding_boxes(uploaded_image, boxes, labels, cleaf_colors, normalize_label=normalize_label)
            else:
                # Return original image if model is None
                return np.array(uploaded_image)

        elif model_type == "Both Models":
            # Start with a copy of the uploaded image
            result_image = np.array(uploaded_image)

            # Process disease detections using model_disease (passed separately in Both Models mode)
            if isinstance(model_disease, tuple):
                result_disease1 = model_disease[0].predict(
                    uploaded_image, conf=confidence
                )
                boxes_disease1 = non_max_suppression(
                    result_disease1[0].boxes, overlap_threshold
                )
                labels_disease1 = result_disease1[
                    0
                ].names  # original labels used for drawing
                result_image = draw_bounding_boxes(
                    result_image, boxes_disease1, labels_disease1, cdisease_colors, normalize_label=normalize_label
                )

                result_disease2 = model_disease[1].predict(
                    uploaded_image, conf=confidence
                )
                boxes_disease2 = non_max_suppression(
                    result_disease2[0].boxes, overlap_threshold
                )
                labels_disease2 = result_disease2[0].names
                result_image = draw_bounding_boxes(
                    result_image, boxes_disease2, labels_disease2, cdisease_colors, normalize_label=normalize_label
                )
            else:
                result_disease = model_disease.predict(uploaded_image, conf=confidence)
                boxes_disease = non_max_suppression(
                    result_disease[0].boxes, overlap_threshold
                )
                labels_disease = result_disease[0].names
                result_image = draw_bounding_boxes(
                    result_image, boxes_disease, labels_disease, cdisease_colors, normalize_label=normalize_label
                )

            # Process leaf detections (drawn with original label)
            if model_leaf is not None:
                result_leaf = model_leaf.predict(uploaded_image, conf=confidence)
                leaf_boxes = non_max_suppression(result_leaf[0].boxes, overlap_threshold)
                leaf_labels = result_leaf[0].names
                result_image = draw_bounding_boxes(
                    result_image, leaf_boxes, leaf_labels, cleaf_colors, normalize_label=normalize_label
                )

            return result_image
        
        # Default case - return original image
        return np.array(uploaded_image)

    except Exception as e:
        st.warning(f"Auto-preview failed: {e}")
        return uploaded_image

def detect_labels_only(
    uploaded_image,
    model_type,
    model,
    model_leaf,
    model_disease,
    confidence,
    overlap_threshold,
):
    from modules.processing import non_max_suppression
    detections = []

    def process_boxes(res, labels):
        boxes = non_max_suppression(res[0].boxes, overlap_threshold)
        return [normalize_label(labels[int(box.cls[0])]) for box in boxes]

    if model_type == "Disease":
        if isinstance(model, tuple):
            res1 = model[0].predict(uploaded_image, conf=confidence)
            detections += process_boxes(res1, res1[0].names)
            res2 = model[1].predict(uploaded_image, conf=confidence)
            detections += process_boxes(res2, res2[0].names)
        else:
            res = model.predict(uploaded_image, conf=confidence)
            detections += process_boxes(res, res[0].names)

    elif model_type == "Both Models":
        if isinstance(model_disease, tuple):
            res1 = model_disease[0].predict(uploaded_image, conf=confidence)
            detections += process_boxes(res1, res1[0].names)
            res2 = model_disease[1].predict(uploaded_image, conf=confidence)
            detections += process_boxes(res2, res2[0].names)
        else:
            res = model_disease.predict(uploaded_image, conf=confidence)
            detections += process_boxes(res, res[0].names)

    return detections
    
def detect_with_confidence(
    uploaded_image,
    model_type,
    model,
    model_leaf,
    model_disease,
    confidence,
    overlap_threshold,
):
    """Detect diseases with confidence scores"""
    from modules.processing import non_max_suppression
    
    detections = []

    def process_boxes(res, labels):
        boxes = non_max_suppression(res[0].boxes, overlap_threshold)
        current_detections = []
        for box in boxes:
            class_id = int(box.cls[0])
            score = round(float(box.conf[0]) * 100, 1)
            raw_name = labels[class_id]
            name = normalize_label(raw_name)
            current_detections.append((name, score))
        return current_detections

    # Process disease detections
    if model_type in ["Disease", "Both Models"]:
        used_model = model if model_type == "Disease" else model_disease

        if isinstance(used_model, tuple):
            # For tuple models (like Spots + Full Leaf), process both models
            res1 = used_model[0].predict(uploaded_image, conf=confidence)
            detections.extend(process_boxes(res1, res1[0].names))
            
            res2 = used_model[1].predict(uploaded_image, conf=confidence)
            detections.extend(process_boxes(res2, res2[0].names))
        else:
            # For single models
            res = used_model.predict(uploaded_image, conf=confidence)
            detections.extend(process_boxes(res, res[0].names))
    
    # Process leaf detections if using Leaf or Both Models
    if model_type in ["Leaf", "Both Models"]:
        res_leaf = model_leaf.predict(uploaded_image, conf=confidence)
        leaf_detections = process_boxes(res_leaf, res_leaf[0].names)
        detections.extend(leaf_detections)

    # Return all detections without filtering
    return detections

def normalize_label(label: str) -> str:
    # Use this function only for saving text/database entries.
    # If label is "late-stage-rust", return "rust".
    if label.lower() == "late-stage-rust":
        return "rust"
    return label

# Add this function to modules/image_uploader.py
def check_image_exists(drive, folder_id, filename):
    """Check if an image with the same name already exists in the Drive folder"""
    try:
        query = f"name = '{filename}' and '{folder_id}' in parents and trashed = false"
        results = drive.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        return len(files) > 0
    except Exception as e:
        # If there's an error checking, assume it doesn't exist
        return False


def _upload_image_once(uploaded_image, name, drive, parent_folder_id):
    temp_path = f"temp_{uuid.uuid4().hex}.jpg"
    uploaded_image.save(temp_path)
    try:
        with st.spinner("Uploading to Google Drive..."):
            result = upload_image(temp_path, name, drive, parent_folder_id)
            st.toast(result)
    except Exception as e:
        st.error(f"Drive upload failed: {e}")
    os.remove(temp_path)


@st.dialog("Results")
def _run_single_model(
    uploaded_image,
    source_img,
    gps_data,
    model,
    model_type,
    confidence,
    overlap_threshold,
    save_to_drive,
    drive,
    parent_folder_id,
    colors,
):
    # For Disease type with multiple models
    if model_type == "Disease" and isinstance(model, tuple):
        # Create a copy of the uploaded image for drawing (drawing uses original labels)
        result_image = np.array(uploaded_image)
        disease_results = []

        # Run the first disease model
        res1 = model[0].predict(uploaded_image, conf=confidence)
        boxes1 = non_max_suppression(res1[0].boxes, overlap_threshold)
        labels1 = res1[0].names  # original labels for image preview
        result_image = draw_bounding_boxes(result_image, boxes1, labels1, colors)

        # Collect predictions from first model (use normalized label for saving)
        for box in boxes1:
            class_id = int(box.cls[0])
            score = round(float(box.conf[0]) * 100, 1)
            raw_name = labels1[class_id]
            name = normalize_label(raw_name)  # normalized to "rust" if necessary
            disease_results.append((name, score))

        # Run the second disease model
        res2 = model[1].predict(uploaded_image, conf=confidence)
        boxes2 = non_max_suppression(res2[0].boxes, overlap_threshold)
        labels2 = res2[0].names
        result_image = draw_bounding_boxes(result_image, boxes2, labels2, colors)

        # Collect predictions from second model
        for box in boxes2:
            class_id = int(box.cls[0])
            score = round(float(box.conf[0]) * 100, 1)
            raw_name = labels2[class_id]
            name = normalize_label(raw_name)
            disease_results.append((name, score))

        leaf_results = []  # For Disease mode, only disease results are used
    else:
        # Standard single model approach (Leaf or single Disease model)
        res = model.predict(uploaded_image, conf=confidence)
        boxes = non_max_suppression(res[0].boxes, overlap_threshold)
        labels = res[0].names

        result_image = draw_bounding_boxes(uploaded_image, boxes, labels, colors)

        disease_results = []
        leaf_results = []

        # Collect predictions (use normalized labels for saving)
        for box in boxes:
            class_id = int(box.cls[0])
            score = round(float(box.conf[0]) * 100, 1)
            raw_name = labels[class_id]
            name = normalize_label(raw_name)
            if model_type == "Leaf" and name.lower() in [
                "arabica",
                "liberica",
                "robusta",
            ]:
                leaf_results.append((name, score))
            else:
                disease_results.append((name, score))

    # Display the processed image (which still shows original labels)
    with st.container(border=True):
        st.image(result_image, caption="Detected Image", use_column_width=True)

    saved_any_detections = False
    uploaded = False

    # Group by highest confidence per unique label (using normalized labels)
    highest_disease = get_highest_confidence_detections(disease_results)
    highest_leaf = get_highest_confidence_detections(
        [
            item
            for item in leaf_results
            if item[0].lower() not in ["arabica", "liberica", "robusta"]
        ]
    )

    for name, score in highest_disease.items():
        if score > 50:
            did_save, uploaded = save_prediction_if_valid(
                name=name,
                score=score,
                uploaded_image=uploaded_image,
                source_img=source_img,
                gps_data=gps_data,
                save_to_drive=save_to_drive,
                drive=drive,
                parent_folder_id=parent_folder_id,
                uploaded_flag=uploaded,
            )
            if did_save:
                saved_any_detections = True

    for name, score in highest_leaf.items():
        if score > 50:
            with st.spinner(f"Saving {name} to database..."):
                save_location_data(source_img, name, score, gps_data)
            saved_any_detections = True
            if save_to_drive and not uploaded:
                _upload_image_once(uploaded_image, name, drive, parent_folder_id)
                uploaded = True

    if disease_results or leaf_results:
        with st.popover("📋 See advanced results"):
            if disease_results:
                st.markdown("**☣️ Diseases Detected:**")
                for name, score in disease_results:
                    st.markdown(f"- **{name.title()}** — {score}% confidence")

            if leaf_results:
                st.markdown("**🍃 Leaf Types Detected:**")
                for name, score in leaf_results:
                    st.markdown(f"- **{name.title()}** — {score}% confidence")

    if saved_any_detections:
        st.success("✅ Data saved successfully!")

    return {"detection_ran": True, "last_result_image": result_image}


@st.dialog("Results")
def _run_both_models(
    uploaded_image,
    source_img,
    gps_data,
    model_leaf,
    model_disease,
    confidence,
    overlap_threshold,
    save_to_drive,
    drive,
    parent_folder_id,
    cleaf_colors,
    cdisease_colors,
):
    # Start with a copy of the uploaded image (drawing uses original labels)
    result_image = np.array(uploaded_image)
    disease_results = []

    # --- Disease detection ---
    if isinstance(model_disease, tuple):
        # Process first disease model
        res_disease1 = model_disease[0].predict(uploaded_image, conf=confidence)
        boxes_disease1 = non_max_suppression(res_disease1[0].boxes, overlap_threshold)
        labels_disease1 = res_disease1[0].names
        result_image = draw_bounding_boxes(
            result_image, boxes_disease1, labels_disease1, cdisease_colors
        )
        # Collect predictions using normalized labels for saving
        for box in boxes_disease1:
            class_id = int(box.cls[0])
            score = round(float(box.conf[0]) * 100, 1)
            raw_name = labels_disease1[class_id]
            name = normalize_label(raw_name)
            disease_results.append((name, score))

        # Process second disease model
        res_disease2 = model_disease[1].predict(uploaded_image, conf=confidence)
        boxes_disease2 = non_max_suppression(res_disease2[0].boxes, overlap_threshold)
        labels_disease2 = res_disease2[0].names
        result_image = draw_bounding_boxes(
            result_image, boxes_disease2, labels_disease2, cdisease_colors
        )
        # Collect predictions
        for box in boxes_disease2:
            class_id = int(box.cls[0])
            score = round(float(box.conf[0]) * 100, 1)
            raw_name = labels_disease2[class_id]
            name = normalize_label(raw_name)
            disease_results.append((name, score))
    else:
        # Single disease model
        res_disease = model_disease.predict(uploaded_image, conf=confidence)
        disease_boxes = non_max_suppression(res_disease[0].boxes, overlap_threshold)
        disease_labels = res_disease[0].names
        result_image = draw_bounding_boxes(
            result_image, disease_boxes, disease_labels, cdisease_colors
        )
        for box in disease_boxes:
            class_id = int(box.cls[0])
            score = round(float(box.conf[0]) * 100, 1)
            raw_name = disease_labels[class_id]
            name = normalize_label(raw_name)
            disease_results.append((name, score))

    # --- Leaf detection ---
    res_leaf = model_leaf.predict(uploaded_image, conf=confidence)
    leaf_boxes = non_max_suppression(res_leaf[0].boxes, overlap_threshold)
    leaf_labels = res_leaf[0].names
    result_image = draw_bounding_boxes(
        result_image, leaf_boxes, leaf_labels, cleaf_colors
    )
    # Collect leaf predictions (these remain as given)
    leaf_results = []
    for box in leaf_boxes:
        class_id = int(box.cls[0])
        score = round(float(box.conf[0]) * 100, 1)
        name = leaf_labels[class_id]
        leaf_results.append((name, score))

    # Display the final image with all detections
    with st.container(border=True):
        st.image(result_image, caption="Detected Image", use_column_width=True)

    saved_any_detections = False
    uploaded = False

    # Save highest confidence per unique disease label (normalized for DB saving)
    highest_disease = get_highest_confidence_detections(disease_results)
    highest_leaf = get_highest_confidence_detections(
        [
            item
            for item in leaf_results
            if item[0].lower() not in ["arabica", "liberica", "robusta"]
        ]
    )

    for name, score in highest_disease.items():
        if score > 50:
            did_save, uploaded = save_prediction_if_valid(
                name=name,
                score=score,
                uploaded_image=uploaded_image,
                source_img=source_img,
                gps_data=gps_data,
                save_to_drive=save_to_drive,
                drive=drive,
                parent_folder_id=parent_folder_id,
                uploaded_flag=uploaded,
            )
            if did_save:
                saved_any_detections = True

    for name, score in highest_leaf.items():
        if score > 50:
            with st.spinner(f"Saving {name} to database..."):
                save_location_data(source_img, name, score, gps_data)
            saved_any_detections = True
            if save_to_drive and not uploaded:
                _upload_image_once(uploaded_image, name, drive, parent_folder_id)
                uploaded = True

    if disease_results or leaf_results:
        with st.popover("📋 See advanced results"):
            if disease_results:
                st.markdown("**☣️ Diseases Detected:**")
                for name, score in disease_results:
                    st.markdown(f"- **{name.title()}** — {score}% confidence")
                st.markdown("---")
            if leaf_results:
                st.markdown("**🍃 Leaf Types Detected:**")
                for name, score in leaf_results:
                    st.markdown(f"- **{name.title()}** — {score}% confidence")

    if saved_any_detections:
        st.success("✅ Data saved successfully!")

    return {"detection_ran": True, "last_result_image": result_image}


def predict_for_display_only(
    uploaded_image, model, confidence, overlap_threshold, colors
):
    """Run a dry prediction just to show image with bounding boxes."""
    # Handle multiple models for disease preview
    if isinstance(model, tuple):
        result_image = np.array(uploaded_image)

        # Process first model
        res1 = model[0].predict(uploaded_image, conf=confidence)
        boxes1 = non_max_suppression(res1[0].boxes, overlap_threshold)
        labels1 = res1[0].names
        result_image = draw_bounding_boxes(result_image, boxes1, labels1, colors)

        # Process second model
        res2 = model[1].predict(uploaded_image, conf=confidence)
        boxes2 = non_max_suppression(res2[0].boxes, overlap_threshold)
        labels2 = res2[0].names
        result_image = draw_bounding_boxes(result_image, boxes2, labels2, colors)

        return result_image
    else:
        # Standard single model approach
        res = model.predict(uploaded_image, conf=confidence)
        boxes = non_max_suppression(res[0].boxes, overlap_threshold)
        labels = res[0].names
        result_image = draw_bounding_boxes(uploaded_image, boxes, labels, colors)
        return result_image


def handle_detection(
    uploaded_image,
    source_img,
    gps_data,
    model_type,
    model,
    model_leaf,
    model_disease,
    confidence,
    overlap_threshold,
    save_to_drive,
    drive,
    parent_folder_id,
    cdisease_colors,
    cleaf_colors,
):
    if model_type == "Both Models":
        # Run both disease and leaf models
        results = _run_both_models(
            uploaded_image,
            source_img,
            gps_data,
            model_leaf,
            model_disease,
            confidence,
            overlap_threshold,
            save_to_drive,
            drive,
            parent_folder_id,
            cleaf_colors,
            cdisease_colors,
        )
    elif model_type == "Disease":
        # Run just the disease models (loaded as a tuple)
        results = _run_single_model(
            uploaded_image,
            source_img,
            gps_data,
            model,  # This should be the disease model tuple
            model_type,
            confidence,
            overlap_threshold,
            save_to_drive,
            drive,
            parent_folder_id,
            cdisease_colors,
        )
    elif model_type == "Leaf":
        # Run the leaf model only.
        results = _run_single_model(
            uploaded_image,
            source_img,
            gps_data,
            model,
            model_type,
            confidence,
            overlap_threshold,
            save_to_drive,
            drive,
            parent_folder_id,
            cleaf_colors,
        )

    if results:
        st.session_state.update(results)
        # Force immediate display of result in col1 if image placeholder exists
        if (
            "image_placeholder" in st.session_state
            and results.get("last_result_image") is not None
        ):
            st.session_state["image_placeholder"].image(
                results["last_result_image"],
                caption="Detected Image",
                use_column_width=True,
            )
