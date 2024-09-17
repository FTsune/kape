import streamlit as st
from pathlib import Path
import PIL
import cv2
import numpy as np
import pandas as pd
import altair as alt
import time
import settings
import helper
from streamlit_extras.stylable_container import stylable_container

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
        css_styles="""
            {
                background-color: #fafafa;
                border-radius: 10px;
                padding: calc(1em - 1px);
                box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
            }
            """,
    ):
        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                try:
                    if source_img is None:
                        default_image_path = str(settings.DEFAULT_DETECT_IMAGE)
                        default_image = PIL.Image.open(default_image_path)
                        st.image(default_image_path, caption="Sample Image: Objects Detected",
                                use_column_width=True)
                    else:
                        uploaded_image = PIL.Image.open(source_img)
                        st.image(source_img, caption="Uploaded Image",
                                use_column_width=True)
                except Exception as ex:
                    st.error("Error occurred while opening the image.")
                    st.error(ex)

        with col2:
            # def create_circular_progress_chart(metric_name, value):
            #     # Create a DataFrame for the metric
            #     data = pd.DataFrame({
            #         'metric': [metric_name],
            #         'value': [value]  # Metric value in percentage
            #     })

            #     # Create a chart with an arc mark to represent the progress
            #     arc = alt.Chart(data).mark_arc(innerRadius=30, outerRadius=35).encode(
            #         theta=alt.Theta(field='value', type='quantitative', stack=True, scale=alt.Scale(domain=[0, 100])),
            #         color=alt.value('#41B3A2')
            #     )

            #     # Create a chart with an arc mark to represent the background
            #     background = alt.Chart(data).mark_arc(innerRadius=30, outerRadius=35, color='000000').encode(
            #         theta=alt.Theta(field='value', type='quantitative', stack=True, scale=alt.Scale(domain=[0, 100]))
            #     ).transform_calculate(
            #         value='100'
            #     )

            #     # Create the text in the center
            #     text = alt.Chart(data).mark_text(
            #         align='center',
            #         baseline='middle',
            #         size=20,
            #         font='Arial',
            #         color='#00fecd'
            #     ).encode(
            #         text=alt.Text('value:Q')
            #     )

            #     # Combine the background, arc, and text
            #     final_chart = alt.layer(background, arc, text).properties(
            #         width=200,
            #         height=100
            #     )

            #     return final_chart

            # Metrics
            # metrics = [
            #     {'name': 'mAP', 'value': 98},
            #     {'name': 'Precision', 'value': 98},
            #     {'name': 'Recall', 'value': 96}
            # ]

            with stylable_container(
                key="container_with_border1",
                css_styles="""
                    {
                        background-color: white;
                        border-radius: 10px;
                    }
                    """,
            ):
                st.markdown("<p style='padding: 10px; font-weight: bold; font-size: 17px; color: #41B3A2'>Instructions</p>", unsafe_allow_html=True)
                st.markdown("""
                    <p style='margin-top: -25px; padding: 10px'>
                        Open sidebar to start configuring.
                        Upload a valid image file (jpeg, jpg, webp, png) and click "Detect Objects".
                        Wait for a few seconds until it's done detecting objects.
                    </p>
                """, unsafe_allow_html=True)
                st.markdown("""
                    <p style='font-size: 12px; color: #4d8294; background-color: #a6e3f7; margin-top: -12px; padding: 10px; border-radius: 0 0 10px 10px'>
                        Our model is currently optimized to detect diseases only in coffee leaves.
                    </p>
                """, unsafe_allow_html=True)
            
            # Create charts for each metric
            # charts = [create_circular_progress_chart(metric['name'], metric['value']) for metric in metrics]

            # st.markdown("""<p style='font-size: 15px; margin-top: 10px; font-weight: bold; text-align: center;'>
            #             MODEL'S PERFORMANCE METRICS
            #             </p>""",
            #             unsafe_allow_html=True)

            # # Display charts side by side in Streamlit
            # cols = st.columns(3)
            # for col, chart, metric in zip(cols, charts, metrics):
            #     with col:
            #         st.altair_chart(chart, use_container_width=True)
            #         st.markdown(f"<p style='text-align: center; color: #00fecd; margin-top: -40px;'>{metric['name']}</p>", unsafe_allow_html=True)
                     
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

                                end_time = time.time()
                                elapsed_time = end_time - start_time
                                st.success(f"Prediction finished within {elapsed_time:.2f}s!")
                                    
                                with st.popover("Combined Detection Results"):
                                    # Iterate over each box separately
                                    st.write("Disease Detection Results:")
                                    for box in disease_boxes:
                                        st.write(box)

                                    st.write("Leaf Detection Results:")
                                    for box in leaf_boxes:
                                        st.write(box)
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

                                end_time = time.time()
                                elapsed_time = end_time - start_time
                                st.success(f"Prediction finished within {elapsed_time:.2f}s!")

                                try:
                                    with st.popover("Detection Results"):
                                        for box in boxes:
                                            st.write(box.data)
                                except Exception as ex:
                                    st.write("No image is uploaded yet!")
                            
                        single_model()

if __name__ == '__main__':
    main()