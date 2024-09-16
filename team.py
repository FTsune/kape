import streamlit as st

def main():
    # Custom CSS to handle responsive columns and container styling
    st.markdown(
        """
        <style>
            .container {
                background-color: #fafafa;
                padding: 20px;
                border-radius: 20px;
                max-width: 80%; /* Adjust this value to change the width */
                margin: auto; /* Center the container */
                box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
            }
            .container-header {
                color: #41B3A2; 
                font-size: 35px; 
                font-weight: bold; 
                text-align: center;
                margin-bottom: 10px;
            }
            .grid-container {
                display: grid;
                grid-template-columns: 1fr;
                gap: 10px;
            }
            @media (min-width: 601px) {
                .grid-container {
                    grid-template-columns: 1fr 1fr;
                }
            }
            @media (min-width: 1201px) {
                .grid-container {
                    grid-template-columns: 1fr 1fr 1fr 1fr;
                }
            }
            .grid-item {
                text-align: center;
            }
            .grid-item img {
                margin: 5px;
                padding: 2px;
                border: 3px solid #41B3A2;
                border-radius: 100%;
                max-width: 100%;
                height: auto;
                max-height: 150px;
            }
            .grid-item p {
                color: #41B3A2;
                text-align: center;
                font-weight: bold;
                max-width: 100%;
                height: auto;
            }
            .grid-item .title {
                color: #41B3A2;
                font-weight: bold;
            }
            .grid-item .subtitle {
                font-weight: normal;
                color: black;
                margin-top: -20px;
            }
            @media (max-width: 600px) {
                .grid-item p {
                    font-size: 10px;
                }
            }
            @media (min-width: 601px) and (max-width: 1200px) {
                .grid-item p {
                    font-size: 13px;
                }
            }
            @media (min-width: 1201px) {
                .grid-item p {
                    font-size: 15px;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # HTML structure for the container and grid
    grid_html = '''
    <div class="container">
        <p class="container-header">DEVELOPERS</p>
        <hr style="margin-top: -10px; border: 1px solid #41B3A2;">
        <div class="grid-container">
            <div class="grid-item">
                <img src="./app/static/nico.png">
                <p class="title">NICO</p>
                <p class="subtitle">Deep Learning Engineer</p>
            </div>
            <div class="grid-item">
                <img src="./app/static/kurt.jpg">
                <p class="title">KURT</p>
                <p class="subtitle">Full Stack Developer</p>
            </div>
            <div class="grid-item">
                <img src="./app/static/franco.jpg">
                <p class="title">FRANCO</p>
                <p class="subtitle">Python Developer</p>
            </div>
            <div class="grid-item">
                <img src="./app/static/marvin.png">
                <p class="title">MARVIN</p>
                <p class="subtitle">Data Cleaner</p>
            </div>
    '''

    st.markdown(grid_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()