import streamlit as st
import base64
from st_clickable_images import clickable_images
from PIL import Image
import io

def preprocess_image(image_path, size=(250, 250)):
    image = Image.open(image_path)
    image = image.resize((size[0], size[1]), Image.LANCZOS)
    return image

def image_to_base64(image):
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{encoded}"

def main():
    st.markdown("<p style='color: white; font-size: 35px; font-weight: bold; text-align: center;'>COFFEE LEAF DISEASES</p>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top: -40px'><hr></p>", unsafe_allow_html=True)
    
    image_paths = ["images/diseases/cercospora.jpg", 
                   "images/diseases/leaf-miner.jpg", 
                   "images/diseases/leaf-rust.jpg", 
                   "images/diseases/lichens.jpg", 
                   "images/diseases/sooty-mold.jpg"]
    
    images = [image_to_base64(preprocess_image(image_path)) for image_path in image_paths]

    clicked = clickable_images(
            images,
            titles=['Cercospora', 'Leaf Miner', 'Leaf Rust', 'Lichens', 'Sooty Mold'],
            div_style={"display": "flex", "justify-content": "center", "flex-wrap": "wrap"},
            img_style={"border-radius": "10px", "padding": "2px","margin": "5px", "height": "250px", "width": "250px"},
        )

    @st.experimental_dialog('DISEASE INFO')
    def info(name, name2, desc, image):
        with st.container(border=True):
            st.image(image, use_column_width=True)
        st.subheader(name)
        st.markdown(f"<p style='color: gray; margin-top: -15px; font-weight: italic;'><em>{name2}</em></p>", unsafe_allow_html=True)
        st.markdown(desc)

    if clicked == 0:
        name = 'Cercospora'
        img = 'images/diseases/cercospora.jpg'
        name2 = 'Cercospora coffeicola'
        desc = '''
            This disease, also called Iron Spot, is caused by the fungal pathogen,
            Cercospora coffeicola and tends to present itself on coffee plants grown
            in areas of higher moisture and rainfall and on plants that are stressed.
        '''
        info(name, name2, desc, img)

    elif clicked == 1:
        name = 'Leaf Miner'
        name2 = 'Leucoptera caffeina'
        img = 'images/diseases/leaf-miner.jpg'
        desc = '''
            Leucoptera caffeina is a species of moth. This leaf miner is one of several 
            related pests on Coffea species. It is found in Angola, Zaire, Kenya 
            and Tanzania in Africa. Other coffee leafminers include Leucoptera coffeella.
        '''
        info(name, name2, desc, img)
    
    elif clicked == 2:
        name = 'Leaf Rust'
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

    elif clicked == 3:
        name = 'Lichens'
        name2 = 'A coffee disease...'
        img = 'images/diseases/lichens.jpg'
        desc = 'Leaf disease description... :bug:'
        info(name, name2, desc, img)

    elif clicked == 4:
        name = 'Sooty Mold'
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
