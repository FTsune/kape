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
    st.info("Disease markers may overlap; zoom in for a clearer view.", icon=":material/info:")

    # Fetch data from Google Sheets
    locations = fetch_all_locations()

    if not locations or len(locations) == 0:
        st.warning("No disease detection data available.")
        return

    df = pd.DataFrame(locations)
    df.columns = [col.strip().lower() for col in df.columns]

    required_columns = ["disease detected", "confidence", "latitude", "longitude"]
    if not all(col in df.columns for col in required_columns):
        st.error("Invalid data format in Google Sheets. Please check column names.")
        st.write("Found columns:", df.columns.tolist())
        return

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    else:
        st.error("Missing 'timestamp' column in the dataset.")
        return

    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month

    month_map = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }

    df["month_name"] = df["month"].map(month_map)

    coord_counts = df.groupby(['latitude', 'longitude']).size().reset_index(name='count')
    for idx, row in coord_counts.iterrows():
        mask = (df['latitude'] == row['latitude']) & (df['longitude'] == row['longitude'])
        if row['count'] > 1:
            jitter_amount = 0.0001
            jitter_lats = np.random.uniform(-jitter_amount, jitter_amount, mask.sum())
            jitter_longs = np.random.uniform(-jitter_amount, jitter_amount, mask.sum())
            df.loc[mask, 'display_lat'] = df.loc[mask, 'latitude'] + jitter_lats
            df.loc[mask, 'display_long'] = df.loc[mask, 'longitude'] + jitter_longs
        else:
            df.loc[mask, 'display_lat'] = df.loc[mask, 'latitude']
            df.loc[mask, 'display_long'] = df.loc[mask, 'longitude']

    col1, col2 = st.columns([0.7, 0.3])

    with col2:
        with st.container(border=True):
            st.subheader("Filter Options")

            disease_filter = st.selectbox(
                "Select Disease Type", ["All"] + sorted(df["disease detected"].unique())
            )

            years = sorted(df['year'].dropna().unique().astype(int))

            filter_col = st.columns(2)

            with filter_col[0]:
                selected_year = st.selectbox("Select Year", ["All"] + [str(year) for year in years])

            # Show month filter only if year is selected
            # selected_month = None
            # with filter_col[1]:
            #     if selected_year != "All":
            #         available_months = df[df['year'] == int(selected_year)]['month'].unique()
            #         available_months = sorted([month for month in available_months if not pd.isna(month)])
            #         month_options = ["All"] + [month_map[m] for m in available_months]
            #         selected_month_name = st.selectbox("Select Month", month_options)
            #         if selected_month_name != "All":
            #             selected_month = [k for k, v in month_map.items() if v == selected_month_name][0]

            filtered_df = df.copy()
            if disease_filter != "All":
                filtered_df = filtered_df[filtered_df["disease detected"] == disease_filter]
            if selected_year != "All":
                filtered_df = filtered_df[filtered_df["year"] == int(selected_year)]
                # if selected_month is not None:
                #     filtered_df = filtered_df[filtered_df["month"] == selected_month]

        with st.container(border=True):
            st.subheader("📝 Disease Legend")
            for disease, color in DISEASE_COLORS.items():
                st.markdown(
                    f"<div style='display:flex; align-items:center; margin-bottom:5px;'>"
                    f"<div style='background-color:{color}; "
                    f"width:7px; height:7px; border-radius:50%; margin-right:10px;'></div>"
                    f"<span>{disease.title()}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    with col1:
        with st.container(border=True):
            if len(filtered_df) > 0:
                filtered_df["color"] = filtered_df["disease detected"].apply(
                    lambda x: DISEASE_COLORS.get(x.lower(), "#646464")
                )

                fig = px.scatter_mapbox(
                    filtered_df,
                    lat="display_lat",
                    lon="display_long",
                    color="disease detected",
                    color_discrete_map=DISEASE_COLORS,
                    hover_name="disease detected",
                    hover_data=["confidence", "latitude", "longitude"],
                    zoom=5,
                    size_max=15,
                    opacity=0.8
                )

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
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available for the selected filter.")

        with st.container(border=True):
            st.subheader("📈 Disease Occurrence Over Time")

            if not filtered_df.empty:
                time_series = (
                    filtered_df.groupby([filtered_df['timestamp'].dt.to_period('M'), 'disease detected'])
                    .size()
                    .reset_index(name='count')
                )
                time_series['timestamp'] = time_series['timestamp'].astype(str)

                fig_line = px.line(
                    time_series,
                    x='timestamp',
                    y='count',
                    color='disease detected',
                    title="Disease Reports",
                    markers=True,
                    color_discrete_map=DISEASE_COLORS
                )
                fig_line.update_layout(xaxis_title="Date", yaxis_title="Occurrence Count")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No data available for time-series visualization.")

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