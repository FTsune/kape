import streamlit as st
import base64
import json
from st_click_detector import click_detector

def image_to_base64(image_path):
    with open(image_path, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
        return f"data:image/jpeg;base64,{encoded}"

def load_data():
    with open("dataset/leaves.json", "r") as file:
        return json.load(file)

def main():
    data = load_data()

    # Determine if dark theme is active
    is_dark_theme = st.session_state.get('dark_theme', False)

    # Theme-specific settings
    primary_color = "#00fecd" if is_dark_theme else "#41B3A2"
    background_gradient = "linear-gradient(#1a3c34, #00fecd, #1a3c34)" if is_dark_theme else "linear-gradient(135deg, #E7FBE6, #B2DFDB)"
    text_color = "white" if is_dark_theme else "black"
    container_bg = "#111827" if is_dark_theme else "#fcfcfc"

    content = f"""
    <style>
    .container-header {{
                color: {primary_color}; 
                font-size: 35px; 
                font-weight: bold; 
                text-align: center;
                margin-bottom: 10px;
    }}
    .image-wrapper {{
        background: {background_gradient};
        padding: 20px;
        border-radius: 20px;
        max-width: 90%;
        margin: auto;
    }}
    .image-grid {{
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 10px;
    }}
    .image-container {{
        position: relative;
        border-radius: 20px;
        margin: 5px;
        overflow: hidden;
        width: 100%;
        max-width: 300px;
        box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        aspect-ratio: 16 / 9;
    }}
    .image-item {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        filter: brightness(60%);
        transition: transform 0.2s, filter 0.2s;
    }}
    .image-item:hover {{
        transform: scale(1.05);
        filter: brightness(40%);
    }}
    .image-title {{
        position: absolute;
        top: 45%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: white;
        font-size: 30px;
        font-weight: bold;
        font-family: Arial, sans-serif;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        text-align: center;
        width: 100%;
    }}
    .image-subheader {{
        position: absolute;
        top: 45%;
        left: 50%;
        margin-top: 25px;
        transform: translate(-50%, -50%);
        color: white;
        font-size: 15px;
        font-weight: regular;
        font-family: Arial, sans-serif;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        text-align: center;
        width: 100%;       
    }}
    @media (max-width: 500px) {{
        .image-container {{
            max-width: 100%;
        }}
    }}
    </style>
    <div class="image-wrapper">
        <p class="container-header">LEAVES</p>
        <hr style="margin-top: -10px; border: 1px solid {primary_color};">
        <div class="image-grid">
    """

    for leaf in data:
        image_base64 = image_to_base64(leaf["image_path"])
        content += f"""
            <div class="image-container"><a href='#' id='{leaf["id"]}'><img class='image-item' src='{image_base64}'><div class='image-title'>{leaf["name"]}</div><div class='image-subheader'>{leaf["sci_name"]}</div></a></div>
        """

    content += "</div></div>"

    clicked = click_detector(content)

    @st.dialog('LEAF INFO 🍃', width="large")
    def info(name, sci_name, desc, image):
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.image(image, use_column_width=True)
        with cols[1]:
            st.subheader(f':green[{name}]')
            st.markdown(f"<p style='color: gray; margin-top: -15px; font-weight: italic;'><em>{sci_name}</em></p>", unsafe_allow_html=True)
            st.markdown(desc)

    # Display clicked leaf info
    for leaf in data:
        if clicked == leaf["id"]:
            info(leaf["name"], leaf["sci_name"], leaf["description"], leaf["display_image"])

    # Apply theme
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {container_bg};
            color: {text_color};
        }}
        </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()