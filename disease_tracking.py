import streamlit as st
import pandas as pd
import pydeck as pdk
from modules.database import fetch_all_locations  # Fetch data from Google Sheets

# Define colors for different diseases (RGB format)
DISEASE_COLORS = {
    "rust": [255, 0, 0],  # Red
    "cercospora": [0, 255, 0],  # Green
    "algal-growth": [0, 0, 255],  # Blue
    "sooty-mold": [255, 165, 0],  # Orange
    "late-stage-rust": [128, 0, 128],  # Purple
    "abiotic-disorder": [0, 128, 128],  # Teal
}


def main(theme_colors):
    st.title("🌍 Disease Tracking Map")
    cols = st.columns([0.7,0.3])
    with cols[0]:
        with st.container(border=True):
            # Fetch data from Google Sheets
            locations = fetch_all_locations()

            if not locations or len(locations) == 0:
                st.warning("No disease detection data available.")
                return

            # Convert to DataFrame
            df = pd.DataFrame(locations)

            # Clean column names (remove spaces & convert to lowercase)
            df.columns = [col.strip().lower() for col in df.columns]

            # Ensure required columns exist
            required_columns = ["disease detected", "confidence", "latitude", "longitude"]
            if not all(col in df.columns for col in required_columns):
                st.error("Invalid data format in Google Sheets. Please check column names.")
                st.write("Found columns:", df.columns.tolist())  # Debugging output
                return

            # Convert Latitude & Longitude to float
            df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
            df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

            # Sidebar filters
            st.sidebar.header("Filter Options")
            disease_filter = st.sidebar.selectbox(
                "Select Disease Type", ["All"] + sorted(df["disease detected"].unique())
            )

            if disease_filter != "All":
                df = df[df["disease detected"] == disease_filter]

            # Assign colors to each disease
            df["color"] = df["disease detected"].apply(
                lambda x: DISEASE_COLORS.get(x.lower(), [100, 100, 100])
            )  # Default gray

            # Find the most affected region by clustering locations
            if len(df) > 0:
                # Round latitude and longitude to 1 decimal place (groups locations in ~10 km clusters)
                df["lat_cluster"] = df["latitude"].round(1)
                df["lon_cluster"] = df["longitude"].round(1)

                # Find the most affected region (largest cluster)
                most_affected_region = (
                    df.groupby(["lat_cluster", "lon_cluster"]).size().idxmax()
                )
                center_lat, center_lon = most_affected_region
            else:
                center_lat, center_lon = df["latitude"].mean(), df["longitude"].mean()

            # **Dynamically Adjust Dot Size Based on Zoom**
            def get_dynamic_radius(zoom):
                """Returns the dot size based on zoom level."""
                if zoom > 12:
                    return 300  # Smallest dots when fully zoomed in
                elif zoom > 10:
                    return 600  # Medium-small dots
                elif zoom > 8:
                    return 1200  # Medium dots
                elif zoom > 6:
                    return 1800  # Medium-large dots
                return 2500  # Largest dots when zoomed out

            # Start with a reasonable zoom level
            initial_zoom = 6

            # Pydeck Layer with dynamically adjusting dot sizes
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position=["longitude", "latitude"],
                get_fill_color="color",
                get_radius=get_dynamic_radius(initial_zoom),  # Start with correct size
                pickable=True,
            )

            # Define Pydeck view state
            view_state = pdk.ViewState(
                latitude=center_lat,
                longitude=center_lon,
                zoom=initial_zoom,
                min_zoom=3,
                max_zoom=15,
                pitch=0,
            )

            # Render Pydeck map
            map_deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"text": "{disease detected}"},
            )
            st.pydeck_chart(map_deck)

    # Display legend
    with cols[1]:
        with st.container(border=True):
            st.subheader("📝 Disease Legend")
            for disease, color in DISEASE_COLORS.items():
                st.markdown(
                    f"<div style='display:flex; align-items:center; margin-bottom:5px;'>"
                    f"<div style='background-color:rgb({color[0]},{color[1]},{color[2]}); "
                    f"width:15px; height:15px; border-radius:50%; margin-right:10px;'></div>"
                    f"<span>{disease.title()}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    default_theme = {
        "LIGHT": {
            "primaryColor": "#41B3A2",
            "backgroundColor": "white",
            "secondaryBackgroundColor": "#fafafa",
            "textColor": "black",
        },
        "DARK": {
            "primaryColor": "#00fecd",
            "backgroundColor": "#111827",
            "secondaryBackgroundColor": "#141b2a",
            "textColor": "white",
        },
    }
    main(default_theme)
