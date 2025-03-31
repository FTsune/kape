import streamlit as st
import base64
import json
from st_click_detector import click_detector

def image_to_base64(image_path):
    with open(image_path, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
        return f"data:image/jpeg;base64,{encoded}"

def load_disease_data():
    with open('dataset/diseases.json', 'r') as file:
        data = json.load(file)
    return data

def main():
    # Determine if dark theme is active
    is_dark_theme = st.session_state.get('dark_theme', False)

    # Load disease data
    diseases = load_disease_data()

    images = [image_to_base64(d['thumbnail']) for d in diseases]

    # Define theme-specific colors
    if is_dark_theme:
        primary_color = "#00fecd"
        background_gradient = "linear-gradient(#1a3c34, #00fecd, #1a3c34)"
        text_color = "white"
        container_bg = "#111827"
    else:
        primary_color = "#41B3A2"
        background_gradient = "linear-gradient(135deg, #E7FBE6, #B2DFDB)"
        text_color = "black"
        container_bg = "white"

    # HTML content
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
            padding: 10px;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            justify-content: center;
        }}
        .image-container {{
            position: relative;
            border-radius: 20px;
            overflow: hidden;
            width: 100%;
            box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            aspect-ratio: 21 / 5;
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
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-size: 25px;
            font-weight: bold;
            font-family: Arial, sans-serif;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            text-align: center;
            width: 100%;
        }}
        @media (max-width: 768px) {{
            .image-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            .image-title {{
                font-size: 20px;
            }}
        }}
        @media (max-width: 630px) {{
            .image-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        </style>
        <div class="image-wrapper">
        <p class="container-header">DISEASES</p>
        <hr style="margin-top: -10px; border: 1px solid {primary_color};">
            <div class="image-grid">
    """

    # Dynamically generate the images and titles
    for i, disease in enumerate(diseases):
        content += f"""
            <div class="image-container">
                <a href='#' id='{disease["id"]}'>
                    <img class='image-item' src='{images[i]}'>
                    <div class='image-title'>{disease["title"]}</div>
                </a>
            </div>
        """

    content += """
            </div>
        </div>
    """

    clicked = click_detector(content)

    @st.dialog('DISEASE INFO 🦠', width="large")
    def info(disease):
        tab1, tab2 = st.tabs(['Info', 'Solution'])
        
        with tab1:
            cols = st.columns(2)
            with cols[0]:
                with st.container(border=True):
                    st.image(disease['image'], use_column_width=True)
            with cols[1]:
                st.subheader(disease['title'])
                st.markdown(f"<p style='color: gray; margin-top: -15px; font-weight: italic;'><em>{disease['name2']}</em></p>", unsafe_allow_html=True)
                st.markdown(disease['description'])
        
        with tab2:
            st.subheader('Prevention')
            if isinstance(disease.get('solution'), list):
                # Convert the list to a numbered markdown format
                solution_text = "\n".join([f"- {item}" for i, item in enumerate(disease['prevention'])])
                st.markdown(solution_text)
            else:
                st.write(disease.get('solution', 'Use this and that to prevent me. 🐛'))
            st.subheader('Solution')
            if isinstance(disease.get('solution'), list):
                # Convert the list to a numbered markdown format
                solution_text = "\n".join([f"- {item}" for i, item in enumerate(disease['solution'])])
                st.markdown(solution_text)
            else:
                st.write(disease.get('solution', 'Use this and that to solve me. 🐛'))
            

    for disease in diseases:
        if clicked == disease['id']:
            info(disease)

    # Apply overall theme to Streamlit elements
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {container_bg};
            color: {text_color};
        }}
        </style>
    """, unsafe_allow_html=True)
    
if __name__ == '__main__':
    main()
