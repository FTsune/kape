import streamlit as st
import numpy as np
import uuid
import cv2


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
            "detection_id": str(uuid.uuid4()),
        }
        predictions.append(prediction)

    # Create the full result dictionary
    result = {"predictions": predictions}

    # Add GPS data if available
    if gps_data:
        result["location"] = {
            "latitude": round(gps_data["latitude"], 6),
            "longitude": round(gps_data["longitude"], 6),
        }
        if gps_data.get("altitude"):
            result["location"]["altitude"] = round(float(gps_data["altitude"]), 1)

    return result


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
