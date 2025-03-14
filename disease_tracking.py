import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from modules.database import fetch_all_locations  # Fetch data from Google Sheets

# Define colors for different diseases (Hex format for Plotly)
DISEASE_COLORS = {
    "rust": "#FF0000",  # Red
    "cercospora": "#00FF00",  # Green
    "algal-growth": "#0000FF",  # Blue
    "sooty-mold": "#FFA500",  # Orange
    "late-stage-rust": "#800080",  # Purple
    "abiotic-disorder": "#008080",  # Teal
}

def main(theme_colors=None):
    st.info("Disease markers may overlap; zoom in for a clearer view.",icon=":material/info:")
    
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

    # Detect and adjust overlapping coordinates
    # Add a small jitter to coordinates that are exactly the same
    # Group by lat/long and create unique display coordinates
    coord_counts = df.groupby(['latitude', 'longitude']).size().reset_index(name='count')
    
    # Add small jitter to coordinates
    for idx, row in coord_counts.iterrows():
        if row['count'] > 1:
            # Find all rows with these coordinates
            mask = (df['latitude'] == row['latitude']) & (df['longitude'] == row['longitude'])
            matching_rows = df[mask]
            
            # Apply jitter to these coordinates
            jitter_amount = 0.0001  # Small amount that's visible on map zoom
            jitter_lats = np.random.uniform(-jitter_amount, jitter_amount, matching_rows.shape[0])
            jitter_longs = np.random.uniform(-jitter_amount, jitter_amount, matching_rows.shape[0])
            
            # Create display coordinates
            df.loc[mask, 'display_lat'] = df.loc[mask, 'latitude'] + jitter_lats
            df.loc[mask, 'display_long'] = df.loc[mask, 'longitude'] + jitter_longs
        else:
            # No overlapping for this coordinate
            mask = (df['latitude'] == row['latitude']) & (df['longitude'] == row['longitude'])
            df.loc[mask, 'display_lat'] = df.loc[mask, 'latitude']
            df.loc[mask, 'display_long'] = df.loc[mask, 'longitude']

    # Create two columns layout
    col1, col2 = st.columns([0.7, 0.3])
    
    with col2:
        # Sidebar filters (now in the right column)
        with st.container(border=True):
            st.subheader("Filter Options")
            disease_filter = st.selectbox(
                "Select Disease Type", ["All"] + sorted(df["disease detected"].unique())
            )
            
            filtered_df = df.copy()
            if disease_filter != "All":
                filtered_df = filtered_df[filtered_df["disease detected"] == disease_filter]

        with st.container(border=True):    
            # Display legend
            st.subheader("📝 Disease Legend")
            for disease, color in DISEASE_COLORS.items():
                st.markdown(
                    f"<div style='display:flex; align-items:center; margin-bottom:5px;'>"
                    f"<div style='background-color:{color}; "
                    f"width:15px; height:15px; border-radius:50%; margin-right:10px;'></div>"
                    f"<span>{disease.title()}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)
    
    with col1:
        # Display the map in the main column
        with st.container(border=True):
            if len(filtered_df) > 0:
                # Assign color based on disease type
                filtered_df["color"] = filtered_df["disease detected"].apply(
                    lambda x: DISEASE_COLORS.get(x.lower(), "#646464")  # Default gray
                )
                
                # Create the Plotly Express scattermapbox using the jittered coordinates
                fig = px.scatter_mapbox(
                    filtered_df, 
                    lat="display_lat",  # Use jittered coordinates 
                    lon="display_long", # Use jittered coordinates
                    color="disease detected",
                    color_discrete_map=DISEASE_COLORS,
                    hover_name="disease detected",
                    hover_data=["confidence", "latitude", "longitude"],  # Show original coordinates in hover
                    zoom=5,
                    size_max=15,
                    opacity=0.8
                )
                
                # Update layout to use open-street-map
                fig.update_layout(
                    mapbox_style="open-street-map",
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    height=600,
                    legend=dict(
                        title="Legend",
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01,
                        bgcolor="rgba(255, 255, 255, 0.8)"
                    )
                )
                
                # Display the map
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available for the selected filter.")

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