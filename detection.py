import streamlit as st
import streamlit_shadcn_ui as ui
from pathlib import Path
import PIL
import cv2
import numpy as np

import settings
import helper

def main():
    # Define global color mappings for classes
    cleaf_colors = {
        0: (0, 255, 0),    # Green for 'arabica'
        1: (0, 255, 255),  # Yellow for 'liberica'
        2: (0, 0, 255)     # Blue for 'robusta'
    }

    cdisease_colors = {
        0: (255, 165, 0),  # Orange for 'brown_eye_spot'
        1: (255, 0, 255),  # Magenta for 'leaf_miner'
        2: (255, 0, 0),    # Red for 'leaf_rust'
        3: (128, 0, 128)   # Purple for 'red_spider_mite'
    }

    # Logo
    st.logo('images/icon.png')
    
    # Main page heading
    st.markdown("<h1 style='font-size: 35px;'>COFFEE LEAF CLASSIFICATION AND DISEASE DETECTION</h1>", unsafe_allow_html=True)


    # Sidebar
    st.sidebar.header("DL MODEL CONFIGURATION")


    # Model Selection
    with st.sidebar:
        #st.markdown("<p style='font-size: 14px;'>Select Detection Model</p>", unsafe_allow_html=True)
        detection_model_choice = st.selectbox(
                                    "Select Detection Model",
                                    ("Disease", "Leaf", "Both Models"),
                                    index=0,
                                    placeholder="Choose a model..."
                                )

    confidence = float(st.sidebar.slider("Select Model Confidence", 25, 100, 40)) / 100

    # New slider for overlap threshold
    overlap_threshold = float(st.sidebar.slider("Select Overlap Threshold", 0, 100, 30)) / 100

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

    with st.container(border=True):
        col1, col2 = st.columns(2)

        with col1:
            try:
                if source_img is None:
                    default_image_path = str(settings.DEFAULT_IMAGE)
                    default_image = PIL.Image.open(default_image_path)
                    st.image(default_image_path, caption="Default Image",
                            use_column_width=True)
                else:
                    uploaded_image = PIL.Image.open(source_img)
                    st.image(source_img, caption="Uploaded Image",
                            use_column_width=True)
            except Exception as ex:
                st.error("Error occurred while opening the image.")
                st.error(ex)

        with col2:
            if source_img is None:
                default_detected_image_path = str(settings.DEFAULT_DETECT_IMAGE)
                default_detected_image = PIL.Image.open(default_detected_image_path)
                st.image(default_detected_image_path, caption='Detected Image',
                        use_column_width=True)
            else:
                if st.sidebar.button('Detect Objects'):
                    if detection_model_choice == 'Both Models':
                        # Use both models for detection
                        res_disease = model_disease.predict(uploaded_image, conf=confidence)
                        res_leaf = model_leaf.predict(uploaded_image, conf=confidence)

                        # Apply non-max suppression
                        disease_boxes = non_max_suppression(res_disease[0].boxes, overlap_threshold)
                        leaf_boxes = non_max_suppression(res_leaf[0].boxes, overlap_threshold)

                        # Merge the labels by converting them to dictionaries and concatenating
                        combined_labels = {**res_disease[0].names, **res_leaf[0].names}

                        # Create a combined image with both model detections
                        res_combined = np.array(uploaded_image)

                        # Draw disease boxes
                        res_combined = draw_bounding_boxes(res_combined, disease_boxes, res_disease[0].names, cdisease_colors)

                        # Draw leaf boxes
                        res_combined = draw_bounding_boxes(res_combined, leaf_boxes, res_leaf[0].names, cleaf_colors)

                        st.image(res_combined, caption='Combined Detected Image', use_column_width=True)

                        with st.popover("Combined Detection Results"):
                            # Iterate over each box separately
                            st.write("Disease Detection Results:")
                            for box in disease_boxes:
                                st.write(box)

                            st.write("Leaf Detection Results:")
                            for box in leaf_boxes:
                                st.write(box)

                    else:
                        # Single model prediction
                        res = model.predict(uploaded_image, conf=confidence)
                        boxes = non_max_suppression(res[0].boxes, overlap_threshold)
                        labels = res[0].names

                        # Choose the appropriate color map based on the model
                        if detection_model_choice == 'Disease':
                            colors = cdisease_colors
                        else:
                            colors = cleaf_colors

                        # Draw the bounding boxes
                        res_plotted = draw_bounding_boxes(uploaded_image, boxes, labels, colors)
                        
                        st.image(res_plotted, caption='Detected Image', use_column_width=True)
                        try:
                            with st.popover("Detection Results"):
                                for box in boxes:
                                    st.write(box.data)
                        except Exception as ex:
                            st.write("No image is uploaded yet!")


if __name__ == '__main__':
    main()