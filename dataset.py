import streamlit as st
import leaf
import disease

def main():
    # Selectbox for choosing dataset
    cols = st.columns([0.8, 0.2])

    with cols[1]:
        dataset_option = st.selectbox(
            "Choose Dataset:",
            ("Disease Dataset", "Leaf Dataset"),
            index=0,
            label_visibility='hidden'
        )

    # Render based on selection
    if dataset_option == "Leaf Dataset":
        leaf.main()
    else:
        disease.main()

if __name__ == '__main__':
    main()
