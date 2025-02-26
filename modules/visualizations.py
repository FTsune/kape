import streamlit as st
import cv2
import numpy as np
import time


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
        cv2.rectangle(
            res_image, (x1, y1), (x2, y2), color=color, thickness=box_thickness
        )
        cv2.putText(
            res_image,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            font_thickness,
        )

    return res_image


def run_live_detection(model, leaf_colors, disease_colors):
    st.title("Live Detection")
    video_placeholder = st.empty()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("No camera detected. Please check your camera connection.")
        return

    while True:
        if not st.session_state.get("enable_live_detection", False):
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
                cv2.putText(
                    frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2
                )

        video_placeholder.image(frame, channels="BGR", use_column_width=True)

    cap.release()
