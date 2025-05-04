import streamlit as st
import PIL
from PIL import Image
import hashlib
import json
from pathlib import Path
from components.config import settings, helper
from modules.dialog_utils import show_disease_dialog, show_leaf_dialog, show_both_model_disease_dialog
from modules.detection_runner import generate_preview_image, detect_with_confidence

def check_config_changed(current_model_config):
    """Check if model configuration has changed since last detection."""
    if not st.session_state.detection_run:
        return False
        
    # Compare current config with last used config
    for key, value in current_model_config.items():
        if key not in st.session_state.last_model_config or st.session_state.last_model_config[key] != value:
            return True
    return False

def get_cache_key(source_img, current_model_config):
    """Generate a cache key based on image hash and model configuration."""
    if source_img is None:
        return None
        
    # Generate a hash for the current image and model configuration
    image_bytes = source_img.getvalue()
    image_hash = hashlib.md5(image_bytes).hexdigest()
    
    # Create a combined key for the cache that includes both image and model config
    config_str = json.dumps(current_model_config, sort_keys=True)
    return f"{image_hash}_{hashlib.md5(config_str.encode()).hexdigest()}"

def run_detection(source_img, current_model_config, progress_callback=None):
    """Run detection on an image and return results."""
    if source_img is None:
        return {
            "result_image": None,
            "detected_diseases": [],
            "all_disease_detections": [],
            "disease_confidences": {},
            "all_disease_instances": []
        }
        
    # Extract configuration parameters
    detection_model_choice = current_model_config["detection_model_choice"]
    disease_model_mode = current_model_config["disease_model_mode"]
    confidence = current_model_config["confidence"]
    overlap_threshold = current_model_config["overlap_threshold"]
    
    # Update progress if callback provided
    if progress_callback:
        try:
            progress_callback(10, "Loading models...")
        except:
            pass  # Silently handle any callback errors
    
    # Load models
    model, model_leaf, model_disease = load_models(detection_model_choice, disease_model_mode)
    
    if progress_callback:
        try:
            progress_callback(40, "Preparing image...")
        except:
            pass
    
    # Open the image
    uploaded_image = PIL.Image.open(source_img)
    
    if progress_callback:
        try:
            progress_callback(60, "Running detection...")
        except:
            pass
    
    # Generate preview image with bounding boxes
    preview_image = generate_preview_image(
        uploaded_image,
        detection_model_choice,
        model if detection_model_choice != "Both Models" else None,
        model_leaf if detection_model_choice in ["Leaf", "Both Models"] else None,
        model_disease if detection_model_choice == "Both Models" else None,
        confidence,
        overlap_threshold,
        cdisease_colors={
            0: (255, 255, 0), # Yellow for Abiotic Disorder
            1: (255, 0, 0), # Red for Cercospora
            2: (0, 204, 0), # Green for Healthy
            3: (255, 165, 0), # Orange for Rust
            4: (0, 0, 0), # Black for Sooty Mold
        },
        cleaf_colors={0: (0, 255, 0), 1: (0, 255, 255), 2: (0, 0, 255)}
    )
    
    if progress_callback:
        try:
            progress_callback(80, "Processing results...")
        except:
            pass
    
    # Get all detections with confidence
    detections_with_confidence = detect_with_confidence(
        uploaded_image,
        detection_model_choice,
        model,
        model_leaf,
        model_disease,
        confidence,
        overlap_threshold
    )
    
    # Process detection results
    results = process_detection_results(detections_with_confidence)
    results["result_image"] = preview_image

    # Show dialog if no relevant detections found
    model_choice = current_model_config["detection_model_choice"]
    if model_choice == "Disease" and not results["detected_diseases"]:
        show_disease_dialog()
    elif model_choice == "Leaf" and not results["all_disease_detections"]:
        show_leaf_dialog()
    elif model_choice == "Both Models" and not results["detected_diseases"]:
        show_both_model_disease_dialog()
    
    if progress_callback:
        try:
            progress_callback(100, "Complete!")
        except:
            pass
    
    return results

def load_models(detection_model_choice, disease_model_mode):
    """Load the appropriate models based on configuration."""
    model = model_leaf = model_disease = None

    if detection_model_choice == "Disease":
        if disease_model_mode == "YOLOv11m - Full Leaf":
            model = helper.load_model(
                Path(settings.DISEASE_MODEL_YOLO11M)
            )
        else:
            # Modified to use only spots.pt model instead of a tuple
            model = helper.load_model(Path(settings.DISEASE_MODEL_SPOTS))
        model_leaf = model_disease = None

    elif detection_model_choice == "Leaf":
        # Add this condition to handle Leaf model selection
        model = helper.load_model(Path(settings.LEAF_MODEL))
        model_leaf = model  # Set model_leaf to the same model for consistency
        model_disease = None

    elif detection_model_choice == "Both Models":
        if disease_model_mode == "YOLOv11m - Full Leaf":
            model_disease = helper.load_model(
                Path(settings.DISEASE_MODEL_YOLO11M)
            )
        else:
            # Modified to use only spots.pt model instead of a tuple
            model_disease = helper.load_model(Path(settings.DISEASE_MODEL_SPOTS))
        model_leaf = helper.load_model(Path(settings.LEAF_MODEL))
        model = None
        
    return model, model_leaf, model_disease

def process_detection_results(detections_with_confidence):
    """Process detection results and organize them for display."""
    # Store all unique diseases (don't filter by highest confidence)
    unique_diseases = set()
    disease_dict = {}
    all_detections = []  # Store all detections including duplicates

    # Store all instances with their individual confidence levels
    all_instances = []
    
    # Separate leaf types and diseases
    leaf_types = ["arabica", "liberica", "robusta"]
    
    for disease, conf in detections_with_confidence:
        # Add to all instances regardless of type
        all_instances.append((disease, conf))
        
        # Add to appropriate category
        if disease.lower() in leaf_types:
            # This is a leaf type detection
            unique_diseases.add(disease)
            all_detections.append(disease)
            
            # Store highest confidence for each leaf type
            if disease not in disease_dict or conf > disease_dict[disease]:
                disease_dict[disease] = conf
        else:
            # This is a disease detection
            unique_diseases.add(disease)
            all_detections.append(disease)
            
            # Store highest confidence for each disease
            if disease not in disease_dict or conf > disease_dict[disease]:
                disease_dict[disease] = conf

    return {
        "detected_diseases": list(unique_diseases),
        "all_disease_detections": all_detections,
        "disease_confidences": disease_dict,
        "all_disease_instances": all_instances
    }

def initialize_session_state():
    """Initialize all session state variables."""
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

    # Add a new session state variable to store detection results for each image
    if "image_detection_cache" not in st.session_state:
        st.session_state.image_detection_cache = {}