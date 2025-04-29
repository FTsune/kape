import streamlit as st

@st.dialog("No Classes Detected")
def show_disease_dialog():
    st.warning("Make sure to read the instructions carefully.", icon=':material/warning:')
    st.markdown("**Another Tips:**")
    st.markdown("- **Coffee Leaf**: Make sure the image contains a **coffee** leaf")
    st.markdown("- **Adjust Confidence Threshold**: Try lowering the threshold in Advanced Options")
    st.markdown("- **Ensure Proper Lighting**: Make sure the leaf is well-lit in the image")
    st.markdown("- **Center the Subject**: Position the leaf in the center of the frame")
    st.markdown("- **Change Disease Model**: If issue still persists, try changing the disease model")

@st.dialog("No Leaf Types Detected")
def show_leaf_dialog():
    st.warning("No leaf types were found. Make sure the image contains a clear leaf.", icon=':material/warning:')
    st.markdown("**Helpful Tips:**")
    st.markdown("- **Use Clear Images**: Avoid blurry or cluttered backgrounds")
    st.markdown("- **Center the Leaf**: Ensure the leaf fills the frame")

@st.dialog("No Classes Detected")
def show_both_model_disease_dialog():
    st.warning("No diseases were detected, even though a leaf was present.", icon=':material/warning:')
    st.markdown("**Helpful Tips:**")
    st.markdown("- **Coffee Leaf**: Make sure the image contains a **coffee** leaf.")
    st.markdown("- **Adjust Confidence Threshold**: Try lowering the threshold in Advanced Options")
    st.markdown("- **Ensure Proper Lighting**: Make sure the leaf is well-lit in the image")
    st.markdown("- **Center the Subject**: Position the leaf in the center of the frame")