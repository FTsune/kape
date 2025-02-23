import streamlit as st
from pathlib import Path
import PIL
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
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


def ensure_logs_directory():
    """Create logs directory if it doesn't exist"""
    log_dir = Path("logs")
    if not log_dir.exists():
        log_dir.mkdir(parents=True)
    return log_dir

def save_location_data(image_name, gps_data):
    """Save GPS location data to a JSON file"""
    log_dir = ensure_logs_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a data entry with timestamp and GPS info
    location_entry = {
        "timestamp": timestamp,
        "image_name": image_name,
        "gps_data": gps_data
    }
    
    # Load existing data if available
    log_file = log_dir / "location_logs.json"
    if log_file.exists():
        with open(log_file, 'r') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []
    
    # Append new data
    existing_data.append(location_entry)
    
    # Save updated data
    with open(log_file, 'w') as f:
        json.dump(existing_data, f, indent=4)
    
    return log_file

def get_decimal_coordinates(gps_coords):
    """Convert GPS coordinates from degrees/minutes/seconds to decimal degrees"""
    degrees = float(gps_coords[0])
    minutes = float(gps_coords[1])
    seconds = float(gps_coords[2])
    
    decimal_degrees = degrees + minutes/60 + seconds/3600
    return decimal_degrees

def get_gps_location(image):
    """Extract GPS information from image metadata"""
    try:
        # Open the image
        if isinstance(image, (str, Path)):
            img = Image.open(image)
        else:
            img = Image.open(image)
            
        # Extract EXIF data
        exif = img._getexif()
        
        if not exif:
            return None
            
        gps_info = {}
        
        # Find the GPS info tag
        for tag_id in exif:
            tag = TAGS.get(tag_id, tag_id)
            data = exif[tag_id]
            
            if tag == "GPSInfo":
                for t in data:
                    sub_tag = GPSTAGS.get(t, t)
                    gps_info[sub_tag] = data[t]
                    
        if not gps_info:
            return None
            
        # Extract coordinates
        try:
            lat_dms = gps_info.get('GPSLatitude')
            lon_dms = gps_info.get('GPSLongitude')
            lat_ref = gps_info.get('GPSLatitudeRef')
            lon_ref = gps_info.get('GPSLongitudeRef')
            
            if lat_dms and lon_dms and lat_ref and lon_ref:
                lat = get_decimal_coordinates(lat_dms)
                lon = get_decimal_coordinates(lon_dms)
                
                if lat_ref == 'S':
                    lat = -lat
                if lon_ref == 'W':
                    lon = -lon
                    
                return {
                    'latitude': lat,
                    'longitude': lon,
                    'altitude': gps_info.get('GPSAltitude', None)
                }
        except Exception as e:
            st.warning(f"Error processing GPS coordinates: {str(e)}")
            return None
            
    except Exception as e:
        st.warning(f"Error reading image metadata: {str(e)}")
        return None
    
    return None


def run_live_detection(model, leaf_colors, disease_colors):
    st.title("Live Detection")
    video_placeholder = st.empty()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        st.error("No camera detected. Please check your camera connection.")
        return

    while True:
        if not st.session_state.get('enable_live_detection', False):
            break

        ret, frame = cap.read()
        if not ret:
            st.error("Failed to capture image from webcam.")
            time.sleep(1)
            continue

        results = model(frame)

        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0]
                cls = int(box.cls[0])

                if cls in leaf_colors:
                    color = leaf_colors[cls]
                else:
                    color = disease_colors[cls - len(leaf_colors)]

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"{model.names[cls]} {conf:.2f}"
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        video_placeholder.image(frame, channels="BGR", use_column_width=True)

    cap.release()

def format_detection_results(boxes, labels, gps_data=None):
    """Format detection results including GPS data if available"""
    predictions = []
    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        width = x2 - x1
        height = y2 - y1
        confidence = float(box.conf[0])
        class_id = int(box.cls[0])
        class_name = labels[class_id]
        
        prediction = {
            "x": x1,
            "y": y1,
            "width": width,
            "height": height,
            "confidence": round(confidence, 3),
            "class": class_name,
            "class_id": class_id,
            "detection_id": str(uuid.uuid4())
        }
        predictions.append(prediction)
    
    # Create the full result dictionary
    result = {
        "predictions": predictions
    }
    
    # Add GPS data if available
    if gps_data:
        result["location"] = {
            "latitude": round(gps_data['latitude'], 6),
            "longitude": round(gps_data['longitude'], 6)
        }
        if gps_data.get('altitude'):
            result["location"]["altitude"] = round(float(gps_data['altitude']), 1)
    
    return result

def main(theme_colors):
    # Initialize session state for theme if not already set
    if 'dark_theme' not in st.session_state:
        st.session_state.dark_theme = False

    # Sidebar theme selection
    with st.sidebar:
        st.header("THEME")
        theme_option = st.selectbox(
            "Choose theme",
            options=["Light", "Dark"],
            index=1 if st.session_state.dark_theme else 0,
            key="theme_selector"
        )

        warn = st.empty()
        st.divider()
        
    # Update session state based on theme selection
    new_theme = (theme_option == "Dark")
    if new_theme != st.session_state.dark_theme:
        st.session_state.dark_theme = new_theme
        st.rerun()

    # Apply theme colors
    if st.session_state.dark_theme:
        primary_color = theme_colors['DARK']['primaryColor']
        background_color = theme_colors['DARK']['backgroundColor']
        secondary_background_color = theme_colors['DARK']['secondaryBackgroundColor']
        text_color = theme_colors['DARK']['textColor']
    else:
        primary_color = theme_colors['LIGHT']['primaryColor']
        background_color = theme_colors['LIGHT']['backgroundColor']
        secondary_background_color = theme_colors['LIGHT']['secondaryBackgroundColor']
        text_color = theme_colors['LIGHT']['textColor']

    # Apply theme to Streamlit
    st.markdown(f"""
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
    """, unsafe_allow_html=True)

    warn.markdown(f"""<div style='background-color: transparent; border: 1px solid {primary_color}; border-radius: 10px;'>
                    <p style='font-size: 0.9rem; color: {primary_color}; margin: 0px 0px; padding: 10px;'>
                    This feature is still in development and may cause unexpected behavior when used.</p>
                    </div>""",
                unsafe_allow_html=True) 

    # Define global color mappings for classes
    cleaf_colors = {
        0: (0, 255, 0),    # Green for 'arabica'
        1: (0, 255, 255),  # Aqua for 'liberica'
        2: (0, 0, 255)     # Blue for 'robusta'
    }

    cdisease_colors = {
        0: (0, 128, 128),  # Teal for 'abiotic disorder'
        1: (255, 165, 0),  # Orange for 'algal growth'
        2: (255, 0, 0),    # Red for 'cercospora'
        3: (128, 0, 128),  # Purple for 'late stage rust'
        4: (150, 75, 0),  # Magenta for 'rust'
        5: (255, 255, 0)    # Purple for 'sooty mold'
    }

    # Sidebar
    st.sidebar.header("MODEL CONFIGURATION")


    # Model Selection
    with st.sidebar:
        detection_model_choice = st.selectbox(
                                    "Select Detection Model",
                                    ("Disease", "Leaf", "Both Models"),
                                    index=0,
                                    placeholder="Choose a model..."
                                )
        adv_opt = st.toggle("Advanced Options")

        if adv_opt:
            confidence = float(st.sidebar.slider("Select Model Confidence", 
                                                25, 100, 40,
                                                help="A higher value means the model will only make predictions when it is more certain, which can reduce false positives but might also increase the number of 'unsure' results.")) / 100

            # New slider for overlap threshold
            overlap_threshold = float(st.sidebar.slider("Select Overlap Threshold", 0, 100, 30,
                                                        help="A higher threshold means the model will require more overlap between detected regions to consider them as distinct, which can help reduce false positives but may also miss some overlapping objects.")) / 100

    # Selecting Detection Model and setting model path
    model = None
    model_path = None
    
    try:
        if detection_model_choice == 'Disease':
            model_path = Path(settings.DISEASE_DETECTION_MODEL)
            model = helper.load_model(model_path)
        elif detection_model_choice == 'Leaf':
            model_path = Path(settings.LEAF_DETECTION_MODEL)
            model = helper.load_model(model_path)
        elif detection_model_choice == 'Both Models':
            model_disease = helper.load_model(Path(settings.DISEASE_DETECTION_MODEL))
            model_leaf = helper.load_model(Path(settings.LEAF_DETECTION_MODEL))
    except Exception as ex:
        st.error(f"Unable to load model. Check the specified path: {model_path}")
        st.error(ex)

    if 'enable_live_detection' not in st.session_state:
        st.session_state.enable_live_detection = False

    enable_live_detection = st.sidebar.checkbox(
        "Enable Live Detection", 
        value=st.session_state.enable_live_detection,
        key='live_detection_checkbox',
        help='Enable live detection to receive real-time analysis and alerts for coffee leaf type and disease.'
    )

    if enable_live_detection != st.session_state.enable_live_detection:
        st.session_state.enable_live_detection = enable_live_detection
        st.rerun()

    if st.session_state.enable_live_detection:
        if detection_model_choice == 'Both Models':
            st.error("Live detection is not supported with 'Both Models' option. Please select either 'Disease' or 'Leaf' model.")
        else:
            run_live_detection(model, cleaf_colors, cdisease_colors)
    else:
        st.sidebar.divider()    
        st.sidebar.header("TRY ME")

        source_img = st.sidebar.file_uploader(
            "Choose an image...", type=("jpg", "jpeg", "png", 'bmp', 'webp'))

        def draw_bounding_boxes(image, boxes, labels, colors):
            """Function to draw bounding boxes with labels and confidence on the image."""
            res_image = np.array(image)
            height, width, _ = res_image.shape  # Get image dimensions

            for box in boxes:
                # Extract information from the box
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                label_idx = int(box.cls)
                confidence = float(box.conf)
                label = f"{labels[label_idx]}: {confidence:.2f}"

                # Determine color based on class
                color = colors[label_idx]

                # Adjust font scale and thickness based on image size
                font_scale = max(0.6, min(width, height) / 600)
                font_thickness = max(2, min(width, height) // 250)
                box_thickness = max(3, min(width, height) // 200)

                # Draw the bounding box
                cv2.rectangle(res_image, (x1, y1), (x2, y2), color=color, thickness=box_thickness)
                cv2.putText(res_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, font_thickness)

            return res_image

        def non_max_suppression(boxes, overlap_threshold):
            """Apply non-max suppression to remove overlapping boxes."""
            if len(boxes) == 0:
                return []

            # Convert boxes to numpy array
            boxes_np = boxes.xyxy.cpu().numpy()
            scores = boxes.conf.cpu().numpy()

            # Compute areas of boxes
            x1 = boxes_np[:, 0]
            y1 = boxes_np[:, 1]
            x2 = boxes_np[:, 2]
            y2 = boxes_np[:, 3]
            areas = (x2 - x1 + 1) * (y2 - y1 + 1)

            # Sort boxes by confidence score
            order = scores.argsort()[::-1]

            keep = []
            while order.size > 0:
                i = order[0]
                keep.append(i)

                # Compute IoU of the picked box with the rest
                xx1 = np.maximum(x1[i], x1[order[1:]])
                yy1 = np.maximum(y1[i], y1[order[1:]])
                xx2 = np.minimum(x2[i], x2[order[1:]])
                yy2 = np.minimum(y2[i], y2[order[1:]])

                w = np.maximum(0.0, xx2 - xx1 + 1)
                h = np.maximum(0.0, yy2 - yy1 + 1)
                inter = w * h
                ovr = inter / (areas[i] + areas[order[1:]] - inter)

                # Keep boxes with IoU less than the threshold
                inds = np.where(ovr <= overlap_threshold)[0]
                order = order[inds + 1]

            return [boxes[i] for i in keep]

        with stylable_container(
            key="container_with_border",
            css_styles=f"""
                {{
                    background-color: {secondary_background_color};
                    border-radius: 10px;
                    padding: calc(1em - 1px);
                    max-width: 694px;
                    margin: auto;
                    box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
                }}
                """,
        ):
            col1, col2 = st.columns(2)

            with col1:
                with st.container(border=True):
                    image_placeholder = st.empty()

                    try:
                        if source_img is None:
                            default_image_path = str(settings.DEFAULT_DETECT_IMAGE)
                            default_image = PIL.Image.open(default_image_path)
                            image_placeholder.image(default_image_path, caption="Sample Image: Objects Detected",
                                    use_column_width=True)
                        else:
                            uploaded_image = PIL.Image.open(source_img)
                            image_placeholder.image(source_img, caption="Uploaded Image",
                                    use_column_width=True)
                            
                            # Add GPS metadata extraction
                            gps_data = get_gps_location(source_img)
                            if gps_data:
                                with st.expander("Image Location Data"):
                                    st.write("GPS Coordinates:")
                                    st.write(f"Latitude: {gps_data['latitude']:.6f}°")
                                    st.write(f"Longitude: {gps_data['longitude']:.6f}°")
                                    if gps_data['altitude']:
                                        st.write(f"Altitude: {float(gps_data['altitude']):.1f}m")
                                    
                                    # Save location data
                                    log_file = save_location_data(source_img.name, gps_data)
                                    st.success(f"Location data saved to {log_file}")
                                    
                                    # Optional: Add a map
                                    st.map({
                                        'lat': [gps_data['latitude']],
                                        'lon': [gps_data['longitude']]
                                    })
                                    
                                    # Add button to view saved locations
                                    if st.button("View All Saved Locations"):
                                        try:
                                            with open(log_file, 'r') as f:
                                                saved_data = json.load(f)
                                                st.json(saved_data)
                                        except FileNotFoundError:
                                            st.warning("No location history found.")
                                        except json.JSONDecodeError:
                                            st.error("Error reading location history.")
                            else:
                                st.info("No GPS data found in the image.")
                                
                    except Exception as ex:
                        st.error("Error occurred while opening the image.")
                        st.error(ex)

            with col2:
                with stylable_container(
                    key="container_with_border1",
                    css_styles=f"""
                        {{
                            background-color: {background_color};
                            border-radius: 10px;
                            max-width: 694px;
                        }}
                        """,
                ):
                    col2_placeholder = st.empty()
                    
                    with col2_placeholder.container():
                        st.markdown(f"<p style='border-radius: 10px 10px 0px 0px; border: 1px solid; border-bottom: 0px; padding: 12px; font-weight: bold; font-size: 1.35rem; color: {primary_color}'>INSTRUCTIONS</p>", unsafe_allow_html=True)
                        st.markdown(f"""
                            <p style='border-right: 1px solid {primary_color}; border-left: 1px solid {primary_color}; font-size: 1rem; margin: -30px 0; padding: 12px 12px 25px; color: {text_color}'>
                                Open the sidebar to start configuring.
                                Upload a valid image file (jpeg, jpg, webp, png) and click "Detect Objects".
                                Wait for a few seconds until it's done detecting objects.
                                <br><br>
                                Ensure that the photo clearly shows a coffee leaf. Avoid bluriness and make
                                sure the leaf is the main focus of the image. 
                                <br><br>
                                If your image contains GPS data, it will be automatically extracted and saved.
                            </p>
                        """, unsafe_allow_html=True)
                        st.markdown(f"""
                            <p style='border: 1px solid; border-top: 0px; font-size: 1rem; color: {primary_color}; margin-top: 10px; padding: 10px; border-radius: 0 0 10px 10px'>
                                Our model is currently optimized to detect diseases only in coffee leaves.
                            </p>
                        """, unsafe_allow_html=True)
                        
                if source_img is None:
                    pass
                else:
                    if st.sidebar.button('Detect Objects'):
                        if detection_model_choice == 'Both Models':
                            @st.dialog("Results")
                            def both_models():
                                with st.spinner("Detecting objects. Please wait..."):
                                    time.sleep(0)

                                    start_time = time.time()
                                    
                                    # Get GPS data first
                                    gps_data = get_gps_location(source_img)
                                    
                                    if adv_opt:
                                        res_disease = model_disease.predict(uploaded_image, conf=confidence)
                                        res_leaf = model_leaf.predict(uploaded_image, conf=confidence)

                                        disease_boxes = non_max_suppression(res_disease[0].boxes, overlap_threshold)
                                        leaf_boxes = non_max_suppression(res_leaf[0].boxes, overlap_threshold)
                                    else:
                                        res_disease = model_disease.predict(uploaded_image, conf=.4)
                                        res_leaf = model_leaf.predict(uploaded_image, conf=.4)

                                        disease_boxes = non_max_suppression(res_disease[0].boxes, .3)
                                        leaf_boxes = non_max_suppression(res_leaf[0].boxes, .3)

                                    combined_labels = {**res_disease[0].names, **res_leaf[0].names}
                                    res_combined = np.array(uploaded_image)
                                    res_combined = draw_bounding_boxes(res_combined, disease_boxes, res_disease[0].names, cdisease_colors)
                                    res_combined = draw_bounding_boxes(res_combined, leaf_boxes, res_leaf[0].names, cleaf_colors)
                                        
                                    with st.container(border=True):
                                        st.image(res_combined, caption='Combined Detected Image', use_column_width=True)

                                    image_placeholder.image(res_combined, caption='Detected Image', use_column_width=True)

                                    end_time = time.time()
                                    elapsed_time = end_time - start_time
                                    st.success(f"Prediction finished within {elapsed_time:.2f}s!")

                                    def res():
                                        st.write("Disease Detection Results:")
                                        disease_results = format_detection_results(disease_boxes, res_disease[0].names, gps_data)
                                        st.json(disease_results)

                                        st.write("Leaf Detection Results:")
                                        leaf_results = format_detection_results(leaf_boxes, res_leaf[0].names, gps_data)
                                        st.json(leaf_results)

                                    with st.popover("Advanced Detection Results"):
                                        res()
                                
                            both_models()
                        else:
                            @st.dialog("Result")
                            def single_model():
                                with st.spinner("Detecting objects. Please wait..."):
                                    time.sleep(0)

                                    start_time = time.time()
                                    
                                    # Get GPS data first
                                    gps_data = get_gps_location(source_img)
                                    
                                    if adv_opt:
                                        res = model.predict(uploaded_image, conf=confidence)
                                        boxes = non_max_suppression(res[0].boxes, overlap_threshold)
                                    else:
                                        res = model.predict(uploaded_image, conf=.4)
                                        boxes = non_max_suppression(res[0].boxes, .3)
                                    
                                    labels = res[0].names

                                    if detection_model_choice == 'Disease':
                                        colors = cdisease_colors
                                    else:
                                        colors = cleaf_colors

                                    res_plotted = draw_bounding_boxes(uploaded_image, boxes, labels, colors)
                                        
                                    with st.container(border=True):
                                        st.image(res_plotted, caption='Detected Image', use_column_width=True)

                                    image_placeholder.image(res_plotted, caption='Detected Image', use_column_width=True)

                                    end_time = time.time()
                                    elapsed_time = end_time - start_time
                                    st.success(f"Prediction finished within {elapsed_time:.2f}s!")

                                    try:
                                        with st.popover("Advanced Detection Results"):
                                            results = format_detection_results(boxes, labels, gps_data)
                                            st.json(results)
                                    except Exception as ex:
                                        st.write("No image is uploaded yet!")
                                
                            single_model()
if __name__ == '__main__':
    # This will be called when running detection.py directly
    # You can set default colors here for testing
    default_theme = {
        "LIGHT": {
            "primaryColor": "#41B3A2",
            "backgroundColor": "white",
            "secondaryBackgroundColor": "#fafafa",
            "textColor": "black"
        },
        "DARK": {
            "primaryColor": "#00fecd",
            "backgroundColor": "#111827",
            "secondaryBackgroundColor": "#141b2a",
            "textColor": "white"
        }
    }
    main(default_theme)