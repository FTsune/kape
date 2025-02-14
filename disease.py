import streamlit as st
import base64
from st_click_detector import click_detector

def image_to_base64(image_path):
    with open(image_path, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
        return f"data:image/jpeg;base64,{encoded}"

def main():
    # Determine if dark theme is active
    is_dark_theme = st.session_state.get('dark_theme', False)

    image_paths = [
                   "images/diseases/lichens.jpg",
                   "images/diseases/cercospora2.jpg", 
                   "images/diseases/leaf-rust.jpg", 
                   "images/diseases/sooty-mold.jpg"]
    
    images = [image_to_base64(image_path) for image_path in image_paths]

    # Remove leaf miner, red spider mite. Lichens -> Algae growth
    titles = ['Algae Growth', 'Cercospora', 'Leaf Rust', 'Sooty Mold']

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
                <div class="image-container"><a href='#' id='Image 1'><img class='image-item' src='{images[0]}'><div class='image-title'>{titles[0]}</div></a></div>
                <div class="image-container"><a href='#' id='Image 2'><img class='image-item' src='{images[1]}'><div class='image-title'>{titles[1]}</div></a></div>
                <div class="image-container"><a href='#' id='Image 3'><img class='image-item' src='{images[2]}'><div class='image-title'>{titles[2]}</div></a></div>
                <div class="image-container"><a href='#' id='Image 4'><img class='image-item' src='{images[3]}'><div class='image-title'>{titles[3]}</div></a></div>
            </div>
        </div>
    """

    clicked = click_detector(content)

    @st.dialog('DISEASE INFO 🦠', width="large")
    def info(name, name2, desc, image):
        cols = st.columns(2)

        with cols[0]:
            with st.container(border=True):
                st.image(image, use_column_width=True)
        with cols[1]:
            st.subheader(name)
            st.markdown(f"<p style='color: gray; margin-top: -15px; font-weight: italic;'><em>{name2}</em></p>", unsafe_allow_html=True)
            st.markdown(desc)

    if clicked == "Image 1":
        name = titles[0]
        name2 = 'Foliicolous lichens'
        img = 'images/diseases/lichens2.jpg'
        desc = '''
            Foliicolous lichens are those that grow on the leaves of vascular plants. 
            Such lichens are widespread and are especially common in the tropical areas where there 
            are long periods of high humidity. Many foliicolous species are strictly foliicolous 
            but some may also be found on other plant parts (twigs, branches, trunks) 
            or even non-plant substrates such as rocks.
        '''
        info(name, name2, desc, img)

    elif clicked == "Image 2":
        name = titles[1]
        img = 'images/diseases/cercospora.jpg'
        name2 = 'Cercospora coffeicola'
        desc = '''
            This disease, also called Iron Spot, is caused by the fungal pathogen,
            Cercospora coffeicola and tends to present itself on coffee plants grown
            in areas of higher moisture and rainfall and on plants that are stressed.
        '''
        info(name, name2, desc, img)
    
    elif clicked == "Image 3":
        name = titles[2]
        name2 = 'Hemileia vastatrix'
        img = 'images/diseases/leaf-rust.jpg'
        desc = '''
            Hemileia vastatrix is a multicellular basidiomycete fungus of the order 
            Pucciniales that causes coffee leaf rust, 
            a disease affecting the coffee plant. Coffee serves as the obligate host of coffee 
            rust, that is, the rust must have access to and come into physical contact with coffee 
            in order to survive.
        '''
        info(name, name2, desc, img)

    elif clicked == "Image 4":
        name = titles[3]
        name2 = 'Capnodium citri'
        img = 'images/diseases/sooty-mold2.jpg'
        desc = '''
            Sooty mold is a collective term for different Ascomycete fungi, 
            which includes many genera, commonly Cladosporium and Alternaria. 
            It grows on plants and their fruit, but also environmental objects, 
            like fences, garden furniture, stones, and even cars.
        '''
        info(name, name2, desc, img)

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
