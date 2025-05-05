from PIL import Image
import numpy as np
import cv2

def draw_bounding_boxes(image, boxes, labels, colors, normalize_label=None):
    # Ensure the image is in RGB format
    if isinstance(image, Image.Image):
        image = image.convert("RGB")
        res_image = np.array(image)
    else:
        res_image = np.array(image)
        if len(res_image.shape) == 2:
            res_image = cv2.cvtColor(res_image, cv2.COLOR_GRAY2RGB)
        elif res_image.shape[2] == 1:
            res_image = cv2.cvtColor(res_image, cv2.COLOR_GRAY2RGB)
    
    # Convert to BGR for OpenCV drawing
    res_image = cv2.cvtColor(res_image, cv2.COLOR_RGB2BGR)
    height, width, _ = res_image.shape

    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        label_idx = int(box.cls)
        confidence = float(box.conf)

        raw_label = labels[label_idx]
        display_label = normalize_label(raw_label) if normalize_label else raw_label
        label = f"{display_label}: {confidence:.2f}"
        color = colors[label_idx][::-1]

        font_scale = max(0.6, min(width, height) / 600)
        font_thickness = max(2, min(width, height) // 250)
        box_thickness = max(3, min(width, height) // 200)

        cv2.rectangle(res_image, (x1, y1), (x2, y2), color=color, thickness=box_thickness)
        cv2.putText(res_image, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, font_thickness)

    # Convert back to RGB for Streamlit display
    res_image = cv2.cvtColor(res_image, cv2.COLOR_BGR2RGB)
    return res_image