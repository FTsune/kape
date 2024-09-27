import streamlit as st
import base64
from st_click_detector import click_detector

def image_to_base64(image_path):
    with open(image_path, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
        return f"data:image/jpeg;base64,{encoded}"
    
def main():
    image_paths = ["images/leaves/arabica2.jpg",
                   "images/leaves/liberica2.jpg",
                   "images/leaves/robusta.jpg"]
    
    images = [image_to_base64(image_path) for image_path in image_paths]

    titles = ['Arabica', 'Liberica', 'Robusta']
    sci_names = ['Coffea arabica', 'Coffea liberica', 'Coffea canephora']

    content = f"""
    <style>
    .container-header {{
                color: #41B3A2; 
                font-size: 35px; 
                font-weight: bold; 
                text-align: center;
                margin-bottom: 10px;
    }}
    .image-wrapper {{
        background: linear-gradient(135deg, #E7FBE6, #B2DFDB);
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
        <hr style="margin-top: -10px; border: 1px solid #41B3A2;">
        <div class="image-grid">
            <div class="image-container"><a href='#' id='Image 1'><img class='image-item' src='{images[0]}'><div class='image-title'>{titles[0]}</div><div class='image-subheader'>{sci_names[0]}</div></a></div>
            <div class="image-container"><a href='#' id='Image 2'><img class='image-item' src='{images[1]}'><div class='image-title'>{titles[1]}</div><div class='image-subheader'>{sci_names[1]}</div></a></div>
            <div class="image-container"><a href='#' id='Image 3'><img class='image-item' src='{images[2]}'><div class='image-title'>{titles[2]}</div><div class='image-subheader'>{sci_names[2]}</div></a></div>
        </div>
    </div>
    """


    clicked = click_detector(content)

    @st.experimental_dialog('LEAF INFO 🍃', width="large")
    def info(name, name2, desc, image):
        cols = st.columns(2)

        with cols[0]:
            with st.container(border=True):
                st.image(image, use_column_width=True)
        with cols[1]:
            st.subheader(f':green[{name}]')
            st.markdown(f"<p style='color: gray; margin-top: -15px; font-weight: italic;'><em>{name2}</em></p>", unsafe_allow_html=True)
            st.markdown(desc)

    if clicked == "Image 1":
        name = titles[0]
        img = 'images/leaves/arabica.jpg'
        name2 = sci_names[0]
        desc = f'''
            Coffea arabica, also known as the Arabica coffee, is a species of flowering 
            plant in the coffee and madder family Rubiaceae. It is believed to be the first 
            species of coffee to have been cultivated and is the dominant cultivar, 
            representing about 60% of global production.
        '''
        info(name, name2, desc, img)

    elif clicked == "Image 2":
        name = titles[1]
        name2 = sci_names[1]
        img = 'images/leaves/liberica.jpg'
        desc = '''
            Coffea liberica, commonly known as the Liberian coffee, is a species 
            of flowering plant in the family Rubiaceae from which coffee is produced. 
            It is native to western and central Africa, and has become naturalised in areas 
            including Colombia, Venezuela, the Philippines, Borneo and Java.
        '''
        info(name, name2, desc, img)
    
    elif clicked == "Image 3":
        name = titles[2]
        name2 = sci_names[2]
        img = 'images/leaves/robusta2.png'
        desc = '''
            Coffea canephora is a species of coffee plant that has its origins in central 
            and western sub-Saharan Africa. It is a species of flowering plant in the family Rubiaceae. 
            Though widely known as Coffea robusta, the plant is scientifically identified as 
            Coffea canephora, which has two main varieties, robusta and nganda.
        '''
        info(name, name2, desc, img)


if __name__ == "__main__":
    main()
