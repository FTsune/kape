import streamlit as st
from pathlib import Path
import PIL
from PIL import Image
import hashlib
import settings
import helper
from modules.detection_runner import (
    generate_preview_image,
    detect_with_confidence
)

def process_image(
    source_img, 
    detection_model_choice, 
    disease_model_mode, 
    confidence, 
    overlap_threshold, 
    cdisease_colors, 
    cleaf_colors
):
    """
    Process an image for disease detection and return the results.
    This function handles the entire detection pipeline.
    """
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
    
    # Open the image
    uploaded_image = PIL.Image.open(source_img)
    
    # Generate preview image
    preview_image = generate_preview_image(
        uploaded_image,
        detection_model_choice,
        model if detection_model_choice != "Both Models" else None,
        model_leaf if detection_model_choice == "Both Models" else None,
        model_disease if detection_model_choice == "Both Models" else None,
        confidence,
        overlap_threshold,
        cdisease_colors,
        cleaf_colors,
    )
    
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

    # Process detection results
    unique_diseases = set()
    disease_dict = {}
    all_detections = []  # Store all detections including duplicates
    all_instances = []  # Store all instances with their individual confidence levels
    
    for disease, conf in detections_with_confidence:
        unique_diseases.add(disease)
        all_detections.append(disease)  # Keep track of all instances
        all_instances.append((disease, conf))  # Store each instance with its confidence
        
        # For each disease, store the highest confidence score
        if disease not in disease_dict or conf > disease_dict[disease]:
            disease_dict[disease] = conf
    
    return {
        "preview_image": preview_image,
        "detected_diseases": list(unique_diseases),
        "all_disease_detections": all_detections,
        "disease_confidences": disease_dict,
        "all_disease_instances": all_instances
    }

def check_model_config_changed(current_config, last_config):
    """Check if model configuration has changed"""
    if not last_config:
        return False
        
    for key, value in current_config.items():
        if key not in last_config or last_config[key] != value:
            return True
    return False

def get_image_hash(source_img):
    """Generate a hash of the image to detect changes"""
    image_bytes = source_img.getvalue()
    return hashlib.md5(image_bytes).hexdigest()