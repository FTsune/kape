import streamlit as st
import json
from streamlit_extras.stylable_container import stylable_container


def load_disease_data():
    with open("components/dataset/diseases.json", "r") as file:
        data = json.load(file)
    return data


def display_disease_card(disease, index, primary_color, card_bg, text_color):
    # Generate a unique key for each card
    card_key = f"disease_card_{index}"
    button_key = f"disease_button_{index}"

    # Create a smaller card with dynamic left border color based on theme
    with stylable_container(
        key=card_key,
        css_styles=f"""
        {{
            border-left: 4px solid {primary_color}; /* Using dynamic primary color */
            border-radius: 6px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            padding: 12px;
            background-color: {card_bg}; /* Using dynamic card background */
            color: {text_color}; /* Using dynamic text color */
            margin: 6px 0;
            height: auto;
            min-height: 50px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        """,
    ):
        # Disease name - bold
        st.markdown(
            f"<h4 style='font-weight: 600; margin-bottom: 2px; font-size: 20px; line-height: 1.2; color: {text_color};'>{disease['title']}</h4>",
            unsafe_allow_html=True,
        )

        # Scientific name - italic and smaller
        st.markdown(
            f"<p style='font-style: italic; color: #71717a; font-size: 16px; margin-top: 6px; margin-bottom: 12px;'>{disease['name2']}</p>",
            unsafe_allow_html=True,
        )

        # Button - aligned to the right
        col1, col2 = st.columns([0.6, 0.3])
        with col2:
            if st.button(
                "View Details",
                key=button_key,
                type="secondary",
                use_container_width=True,
            ):
                info(disease)


@st.dialog("DISEASE INFO 🦠", width="large")
def info(disease):
    tab1, tab2 = st.tabs(["Info", "Solution"])

    with tab1:
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.image(disease["image"], use_container_width=True)
        with cols[1]:
            st.subheader(disease["title"])
            st.markdown(
                f"<p style='color: gray; margin-top: -15px; font-weight: italic;'><em>{disease['name2']}</em></p>",
                unsafe_allow_html=True,
            )
            st.markdown(disease["description"])
            st.markdown("Reference ☕: " + disease["link"])

    with tab2:
        st.subheader("Prevention")
        if isinstance(disease.get("prevention"), list):
            # Convert the list to a numbered markdown format
            prevention_text = "\n".join(
                [f"- {item}" for i, item in enumerate(disease["prevention"])]
            )
            st.markdown(prevention_text)
        else:
            st.write(disease.get("prevention", "Use this and that to prevent me. 🐛"))
        st.divider()
        st.subheader("Solution")
        if isinstance(disease.get("solution"), list):
            # Convert the list to a numbered markdown format
            solution_text = "\n".join(
                [f"- {item}" for i, item in enumerate(disease["solution"])]
            )
            st.markdown(solution_text)
        else:
            st.write(disease.get("solution", "Use this and that to solve me. 🐛"))


def main():
    # Determine if dark theme is active
    is_dark_theme = st.session_state.get("dark_theme", False)

    # Load disease data
    diseases = load_disease_data()

    # Define theme-specific colors
    if is_dark_theme:
        primary_color = "#00fecd"
        container_bg = "#111827"
        text_color = "white"
        card_bg = "#141b2a"
    else:
        primary_color = "#41B3A2"
        container_bg = "#fcfcfc"
        text_color = "black"
        card_bg = "white"

    # Responsive layout handling
    # Get the current viewport width using session state
    if "viewport_width" not in st.session_state:
        st.session_state.viewport_width = 1200  # Default assumption

    # Inject JavaScript to detect viewport width and store it in session state
    st.markdown(
        """
        <script>
            // Function to update the viewport width
            function updateViewportWidth() {
                const width = window.innerWidth;
                // Use Streamlit's setComponentValue when available in the future
                // For now, we'll use this as a placeholder
                console.log("Viewport width:", width);
            }
            
            // Update on load and resize
            window.addEventListener('load', updateViewportWidth);
            window.addEventListener('resize', updateViewportWidth);
        </script>
    """,
        unsafe_allow_html=True,
    )

    # Create a container with custom CSS for the grid
    st.markdown(
        f"""
        <style>
        .disease-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }}
        
        @media (max-width: 768px) {{
            .disease-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .stApp {{
            background-color: {container_bg};
            color: {text_color};
        }}
        
        .intro-text {{
            text-align: center;
            margin: 20px auto;
            max-width: 800px;
            padding: 10px;
        }}
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Header
    st.markdown(
        f"<h1 style='color: {primary_color}; text-align: center; padding-left: 28px;'>DISEASES</h1>",
        unsafe_allow_html=True,
    )
    # Center-aligned introduction text
    st.markdown(
        f"""
        <div style= "margin: auto;" class="intro-text">
            <p style="color: {text_color}; margin: auto;">This dataset provides detailed information on various coffee leaf diseases that affect coffee plants. This resource is essential for researchers and farmers seeking to understand and manage coffee leaf diseases effectively.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Create a container for the grid
    st.markdown('<div class="disease-grid">', unsafe_allow_html=True)

    # Use Streamlit's built-in responsive columns
    # Determine number of columns based on screen size
    screen_width = st.session_state.viewport_width

    # For larger screens, use 2 columns
    if screen_width >= 768:
        cols_per_row = 2
    else:
        cols_per_row = 1

    # Create rows of cards
    num_diseases = len(diseases)
    num_rows = (num_diseases + cols_per_row - 1) // cols_per_row

    # Create the grid using Streamlit columns
    for row in range(num_rows):
        cols = st.columns(cols_per_row)
        for col in range(cols_per_row):
            idx = row * cols_per_row + col
            if idx < num_diseases:
                with cols[col]:
                    display_disease_card(
                        diseases[idx], idx, primary_color, card_bg, text_color
                    )

    # Close the grid container
    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
