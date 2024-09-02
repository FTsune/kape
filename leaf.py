import streamlit as st
import streamlit_shadcn_ui as ui

def main(): 
    st.header("Coffee Leaf Types")

    cols = st.columns(3)
    with cols[0]:
        ui.metric_card(title="🍃", content="Liberica", description="Coffea liberica", key="card1")
    with cols[1]:
        ui.metric_card(title="🍃", content="Arabica", description="Coffea arabica", key="card2")
    with cols[2]:
        ui.metric_card(title="🍃", content="Robusta", description="Coffea canephora", key="card3")

# Optional: Allow this script to be run directly as well
if __name__ == "__main__":
    main()
