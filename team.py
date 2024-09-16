import streamlit as st

def main():
    st.markdown("<p style='color: #41B3A2; font-size: 35px; font-weight: bold; text-align: center;'>DEVELOPERS</p>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top: -40px'><hr></p>", unsafe_allow_html=True)
    # Custom CSS to handle responsive columns
    st.markdown(
        """
        <style>
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
        </style>
        """,    
        unsafe_allow_html=True,
    )

    # HTML structure for the grid
    grid_html = '''
    <div class="grid-container">
        <div style="text-align: center;">
            <img src="./app/static/nico.png" style="margin: 5px; padding: 2px; border: 3px solid #41B3A2; border-radius: 100%; max-width: 100%; height: auto; max-height: 150px;">
            <p style='color: #41B3A2; text-align: center; font-weight: bold; max-width: 100%; height: auto;'>NICO</p>
            <p style='color: white; margin-top: -20px; text-align: center; max-width: 100%; height: auto;'>Deep Learning Engineer</p>
        </div>
        <div style="text-align: center;">
            <img src="./app/static/kurt.jpg" style="margin: 5px; padding: 2px; border: 3px solid #41B3A2; border-radius: 100%; max-width: 100%; height: auto; max-height: 150px;">
            <p style='color: #41B3A2; text-align: center; font-weight: bold; max-width: 100%; height: auto;'>KURT</p>
            <p style='color: white; margin-top: -20px; text-align: center; max-width: 100%; height: auto;'>Full Stack Developer</p>
        </div>
        <div style="text-align: center;">
            <img src="./app/static/franco.jpg" style="margin: 5px; padding: 2px; border: 3px solid #41B3A2; border-radius: 100%; max-width: 100%; height: auto; max-height: 150px;">
            <p style='color: #41B3A2; text-align: center; font-weight: bold; max-width: 100%; height: auto;'>FRANCO</p>
            <p style='color: white; margin-top: -20px; text-align: center; max-width: 100%; height: auto;'>Python Developer</p>
        </div>
        <div style="text-align: center;">
            <img src="./app/static/marvin.png" style="margin: 5px; padding: 2px; border: 3px solid #41B3A2; border-radius: 100%; max-width: 100%; height: auto; max-height: 150px;">
            <p style='color: #41B3A2; text-align: center; font-weight: bold; max-width: 100%; height: auto;'>MARVIN</p>
            <p style='color: white; margin-top: -20px; text-align: center; max-width: 100%; height: auto;'>Data Cleaner</p>
        </div>
    </div>
    <style>
        @media (max-width: 600px) {{
            p {{
                font-size: 10px;
            }}
        }}
        @media (min-width: 601px) and (max-width: 1200px) {{
            p {{
                font-size: 13px;
            }}
        }}
        @media (min-width: 1201px) {{
            p {{
                font-size: 15px;
            }}
        }}
    </style>
    '''

    st.markdown(grid_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
