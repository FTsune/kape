import streamlit as st
from streamlit_extras.stylable_container import stylable_container

def main(): 
    st.header("Coffee Leaf Types")

    cols = st.columns(3)
    with cols[0]:
        with stylable_container(
            key='container_with_border',
            css_styles="""
                {
                    background-color: #141b2a;
                    border: 1px solid #00fecd;
                    border-radius: 10px;
                    padding: 20px;
                }
            """,
        ):           
            st.subheader('Liberica')
            st.write('🍃')
            st.write('Coffea liberica')

    with cols[1]:
        with stylable_container(
            key='container_with_border',
            css_styles="""
                {
                }
            """,
        ):           
            st.subheader('Arabica')
            st.write('🍃')
            st.write('Coffea arabica')

    with cols[2]:
        with stylable_container(
            key='container_with_border',
            css_styles="""
                {
                }
            """,
        ):           
            st.subheader('Robusta')
            st.write('🍃')
            st.write('Coffea canephora')

# Optional: Allow this script to be run directly as well
if __name__ == "__main__":
    main()
