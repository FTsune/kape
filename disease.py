import streamlit as st
import base64
from st_click_detector import click_detector

def image_to_base64(image_path):
    with open(image_path, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
        return f"data:image/jpeg;base64,{encoded}"

def main():
    st.markdown("<p style='color: white; font-size: 35px; font-weight: bold; text-align: center;'>COFFEE LEAF DISEASES</p>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top: -40px'><hr></p>", unsafe_allow_html=True)
    
    image_paths = ["images/diseases/cercospora2.jpg", 
                   "images/diseases/leaf-miner.jpg", 
                   "images/diseases/leaf-rust.jpg", 
                   "images/diseases/lichens.jpg",
                   "images/diseases/red-spider-mite.jpg",
                   "images/diseases/sooty-mold.jpg"]
    
    images = [image_to_base64(image_path) for image_path in image_paths]

    titles = ['Cercospora', 'Leaf Miner', 'Leaf Rust', 'Lichens', 'Red Spider Mite','Sooty Mold']
    
    content = f"""
        <style>
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
            max-width: 500px;
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
        @media (max-width: 800px) {{
            .image-container {{
                max-width: 100%;
            }}
        }}
        </style>
        <div class="image-grid">
            <div class="image-container"><a href='#' id='Image 1'><img class='image-item' src='{images[0]}'><div class='image-title'>{titles[0]}</div></a></div>
            <div class="image-container"><a href='#' id='Image 2'><img class='image-item' src='{images[1]}'><div class='image-title'>{titles[1]}</div></a></div>
            <div class="image-container"><a href='#' id='Image 3'><img class='image-item' src='{images[2]}'><div class='image-title'>{titles[2]}</div></a></div>
            <div class="image-container"><a href='#' id='Image 4'><img class='image-item' src='{images[3]}'><div class='image-title'>{titles[3]}</div></a></div>
            <div class="image-container"><a href='#' id='Image 5'><img class='image-item' src='{images[4]}'><div class='image-title'>{titles[4]}</div></a></div>
            <div class="image-container"><a href='#' id='Image 6'><img class='image-item' src='{images[5]}'><div class='image-title'>{titles[5]}</div></a></div>
        </div>
    """

    clicked = click_detector(content)

    @st.experimental_dialog('DISEASE INFO')
    def info(name, name2, desc, image):
        with st.container(border=True):
            st.image(image, use_column_width=True)
        st.subheader(name)
        st.markdown(f"<p style='color: gray; margin-top: -15px; font-weight: italic;'><em>{name2}</em></p>", unsafe_allow_html=True)
        st.markdown(desc)

    if clicked == "Image 1":
        name = titles[0]
        img = 'images/diseases/cercospora.jpg'
        name2 = 'Cercospora coffeicola'
        desc = '''
            This disease, also called Iron Spot, is caused by the fungal pathogen,
            Cercospora coffeicola and tends to present itself on coffee plants grown
            in areas of higher moisture and rainfall and on plants that are stressed.
        '''
        info(name, name2, desc, img)

    elif clicked == "Image 2":
        name = titles[1]
        name2 = 'Leucoptera caffeina'
        img = 'images/diseases/leaf-miner.jpg'
        desc = '''
            Leucoptera caffeina is a species of moth. This leaf miner is one of several 
            related pests on Coffea species. It is found in Angola, Zaire, Kenya 
            and Tanzania in Africa. Other coffee leafminers include Leucoptera coffeella.
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
        name2 = 'A coffee disease...'
        img = 'images/diseases/lichens.jpg'
        desc = 'Leaf disease description... :bug:'
        info(name, name2, desc, img)

    elif clicked == "Image 5":
        name = titles[4]
        name2 = 'A coffee disease...'
        img = 'images/diseases/red-spider-mite.jpg'
        desc = 'Leaf disease description... :bug:'
        info(name, name2, desc, img)

    elif clicked == "Image 6":
        name = titles[5]
        name2 = 'Capnodium citri'
        img = 'images/diseases/sooty-mold.jpg'
        desc = '''
            Sooty mold is a collective term for different Ascomycete fungi, 
            which includes many genera, commonly Cladosporium and Alternaria. 
            It grows on plants and their fruit, but also environmental objects, 
            like fences, garden furniture, stones, and even cars.
        '''
        info(name, name2, desc, img)

if __name__ == '__main__':
    main()
