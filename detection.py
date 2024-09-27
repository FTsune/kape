import streamlit as st
from pathlib import Path
import PIL
import cv2
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import numpy as np
import time
import settings
import helper
from streamlit_extras.stylable_container import stylable_container

def run_live_detection(model, leaf_colors, disease_colors):
    st.title("Live Detection")
    video_placeholder = st.empty()
    cap = cv2.VideoCapture(0)

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

def main():
    cleaf_colors = {
        0: (0, 255, 0),
        1: (0, 255, 255),
        2: (0, 0, 255)
    }

    cdisease_colors = {
        0: (255, 165, 0),
        1: (255, 0, 255),
        2: (255, 0, 0),
        3: (128, 0, 128)
    }

    st.sidebar.header("DL MODEL CONFIGURATION")

    with st.sidebar:
        detection_model_choice = st.selectbox(
            "Select Detection Model",
            ("Disease", "Leaf", "Both Models"),
            index=0
        )

        adv_opt = st.toggle("Advanced Options")

        if adv_opt:
            confidence = float(st.sidebar.slider("Select Model Confidence", 
                25, 100, 40)) / 100

            overlap_threshold = float(st.sidebar.slider("Select Overlap Threshold", 0, 100, 30)) / 100

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
        key='live_detection_checkbox'
    )

    if enable_live_detection != st.session_state.enable_live_detection:
        st.session_state.enable_live_detection = enable_live_detection
        st.experimental_rerun()

    if st.session_state.enable_live_detection:
        if detection_model_choice == 'Both Models':
            st.error("Live detection is not supported with 'Both Models' option. Please select either 'Disease' or 'Leaf' model.")
        else:
            run_live_detection(model, cleaf_colors, cdisease_colors)

    st.sidebar.divider()   
    st.sidebar.header("TRY ME")

    source_img = st.sidebar.file_uploader(
        "Choose an image...", type=("jpg", "jpeg", "png", 'bmp', 'webp'))

    def draw_bounding_boxes(image, boxes, labels, colors):
        res_image = np.array(image)
        height, width, _ = res_image.shape

        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            label_idx = int(box.cls)
            confidence = float(box.conf)
            label = f"{labels[label_idx]}: {confidence:.2f}"

            color = colors[label_idx]

            font_scale = max(0.6, min(width, height) / 600)
            font_thickness = max(2, min(width, height) // 250)
            box_thickness = max(3, min(width, height) // 200)

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
        css_styles="""
            {
                background-color: #fafafa;
                border-radius: 10px;
                padding: calc(1em - 1px);
                max-width: 1000px;
                margin: auto;
                box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
            }
            """,
    ):
        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                image_placeholder = st.empty()
                # check_res = st.empty()
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
                except Exception as ex:
                    st.error("Error occurred while opening the image.")
                    st.error(ex)

        with col2:
            with stylable_container(
                key="container_with_border1",
                css_styles="""
                    {
                        background-color: white;
                        border-radius: 10px;
                        min-width: 100px;
                    }
                    """,
            ):
                st.markdown("<p style='padding: 12px; font-weight: bold; font-size: 17px; color: #41B3A2'>Instructions</p>", unsafe_allow_html=True)
                st.markdown("""
                    <p style='font-size: 14px; margin-top: -30px; padding: 12px'>
                        Open the sidebar to start configuring.
                        Upload a valid image file (jpeg, jpg, webp, png) and click "Detect Objects".
                        Wait for a few seconds until it's done detecting objects.
                        <br><br>
                        Ensure that the photo clearly shows a coffee leaf. Avoid bluriness and make
                        sure the leaf is the main focus of the image.
                        <br><br>
                        For best results, upload an image with a resolution of at least 1024 x 728 pixels. 
                    </p>
                """, unsafe_allow_html=True)
                st.markdown("""
                    <p style='font-size: 12px; color: #41B3A2; background-color: #b2dfdb; margin-top: -12px; padding: 10px; border-radius: 0 0 10px 10px'>
                        Our model is currently optimized to detect diseases only in coffee leaves.
                    </p>
                """, unsafe_allow_html=True)
                    
            if source_img is None:
                pass
            else:
                if st.sidebar.button('Detect Objects'):
                    if detection_model_choice == 'Both Models':
                        @st.experimental_dialog("Results")
                        def both_models():
                            with st.spinner("Detecting objects. Please wait..."):
                                time.sleep(0)

                                start_time = time.time()
                            # Use both models for detection
                                if adv_opt:
                                    res_disease = model_disease.predict(uploaded_image, conf=confidence)
                                    res_leaf = model_leaf.predict(uploaded_image, conf=confidence)

                                    # Apply non-max suppression
                                    disease_boxes = non_max_suppression(res_disease[0].boxes, overlap_threshold)
                                    leaf_boxes = non_max_suppression(res_leaf[0].boxes, overlap_threshold)

                                else:
                                    res_disease = model_disease.predict(uploaded_image, conf=.4)
                                    res_leaf = model_leaf.predict(uploaded_image, conf=.4)

                                    # Apply non-max suppression
                                    disease_boxes = non_max_suppression(res_disease[0].boxes, .3)
                                    leaf_boxes = non_max_suppression(res_leaf[0].boxes, .3)

                                # Merge the labels by converting them to dictionaries and concatenating
                                combined_labels = {**res_disease[0].names, **res_leaf[0].names}

                                # Create a combined image with both model detections
                                res_combined = np.array(uploaded_image)

                                # Draw disease boxes
                                res_combined = draw_bounding_boxes(res_combined, disease_boxes, res_disease[0].names, cdisease_colors)

                                # Draw leaf boxes
                                res_combined = draw_bounding_boxes(res_combined, leaf_boxes, res_leaf[0].names, cleaf_colors)
                                    
                                with st.container(border=True):
                                    st.image(res_combined, caption='Combined Detected Image', use_column_width=True)

                                image_placeholder.image(res_combined, caption='Detected Image', use_column_width=True)

                                end_time = time.time()
                                elapsed_time = end_time - start_time
                                st.success(f"Prediction finished within {elapsed_time:.2f}s!")

                                def res():
                                    st.write("Disease Detection Results:")
                                    for box in disease_boxes:
                                        st.write(box)

                                    st.write("Leaf Detection Results:")
                                    for box in leaf_boxes:
                                        st.write(box)    

                                with st.popover("Combined Detection Results"):
                                    res()

                                # with check_res.popover("Combined Detection Results"):
                                #     res()
                                
                        both_models()

                    else:
                        @st.experimental_dialog("Result")
                        def single_model():
                            with st.spinner("Detecting objects. Please wait..."):
                                time.sleep(0)

                                start_time = time.time()
                                # Single model prediction
                                if adv_opt:
                                    res = model.predict(uploaded_image, conf=confidence)
                                    boxes = non_max_suppression(res[0].boxes, overlap_threshold)
                                    
                                else:
                                    res = model.predict(uploaded_image, conf=.4)
                                    boxes = non_max_suppression(res[0].boxes, .3)                                    
                                labels = res[0].names

                                # Choose the appropriate color map based on the model
                                if detection_model_choice == 'Disease':
                                    colors = cdisease_colors
                                else:
                                    colors = cleaf_colors

                                # Draw the bounding boxes
                                res_plotted = draw_bounding_boxes(uploaded_image, boxes, labels, colors)
                                    
                                with st.container(border=True):
                                    st.image(res_plotted, caption='Detected Image', use_column_width=True)

                                image_placeholder.image(res_plotted, caption='Detected Image', use_column_width=True)

                                end_time = time.time()
                                elapsed_time = end_time - start_time
                                st.success(f"Prediction finished within {elapsed_time:.2f}s!")

                                try:
                                    with st.popover("Detection Results"):
                                        for box in boxes:
                                            st.write(box)
                                except Exception as ex:
                                    st.write("No image is uploaded yet!")
                            
                        single_model()

if __name__ == '__main__':
    main()