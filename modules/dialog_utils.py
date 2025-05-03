import streamlit as st

@st.dialog("No Classes Detected")
def show_disease_dialog():
    st.markdown("**Another Tips:**")
    st.markdown("- **Coffee Leaf**: Make sure the image contains a **coffee** leaf")
    st.markdown("- **Adjust Confidence Threshold**: Try lowering the threshold in Advanced Options")
    st.markdown("- **Ensure Proper Lighting**: Make sure the leaf is well-lit in the image")
    st.markdown("- **Center the Subject**: Position the leaf in the center of the frame")
    st.markdown("- **Change Disease Model**: If issue still persists, try changing the disease model")
    st.warning("Make sure to read the instructions carefully.", icon=':material/warning:')

@st.dialog("No Leaf Types Detected")
def show_leaf_dialog():
    st.markdown("**Helpful Tips:**")
    st.markdown("- **Coffee Leaf**: Make sure the image contains a **coffee** leaf")
    st.markdown("- **Adjust Confidence Threshold**: Try lowering the threshold in Advanced Options")
    st.markdown("- **Use Clear Images**: Avoid blurry or low quality images")
    st.markdown("- **Center the Leaf**: Ensure the leaf fills the frame")
    st.warning("No leaf types were found. Make sure the image contains a clear leaf.", icon=':material/warning:')

@st.dialog("No Classes Detected")
def show_both_model_disease_dialog():
    st.markdown("**Helpful Tips:**")
    st.markdown("- **Coffee Leaf**: Make sure the image contains a **coffee** leaf.")
    st.markdown("- **Adjust Confidence Threshold**: Try lowering the threshold in Advanced Options")
    st.markdown("- **Ensure Proper Lighting**: Make sure the leaf is well-lit in the image")
    st.markdown("- **Center the Subject**: Position the leaf in the center of the frame")
    st.warning("Make sure to read the instrucions carefully.", icon=':material/warning:')