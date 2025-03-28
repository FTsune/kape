import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from pathlib import Path
from PIL.ExifTags import TAGS
import piexif
from modules.database import save_detection_to_database  # Import the database function


def get_decimal_coordinates(gps_coords):
    """Convert GPS coordinates from degrees/minutes/seconds to decimal degrees."""
    degrees = float(gps_coords[0])
    minutes = float(gps_coords[1])
    seconds = float(gps_coords[2])

    decimal_degrees = degrees + minutes / 60 + seconds / 3600
    return decimal_degrees


def convert_to_float(value):
    """Convert EXIF GPS data to a float if it's an IFDRational type."""
    try:
        if isinstance(value, tuple):  # Handle rational numbers
            return float(value[0]) / float(value[1])
        elif isinstance(value, int) or isinstance(value, float):
            return float(value)
        else:
            return None  # If it's an unsupported type
    except Exception:
        return None


def clean_gps_data(gps_data):
    """Ensure all GPS data values are JSON serializable."""
    if not gps_data:
        return None

    return {
        "latitude": float(gps_data["latitude"]) if gps_data.get("latitude") else None,
        "longitude": float(gps_data["longitude"])
        if gps_data.get("longitude")
        else None,
        "altitude": convert_to_float(gps_data["altitude"])
        if gps_data.get("altitude")
        else None,
    }


def get_gps_location(image):
    """Extract GPS information from image metadata."""
    try:
        img = Image.open(image)
        exif = img._getexif()
        if not exif:
            return None

        gps_info = {}

        # Find the GPS info tag
        for tag_id in exif:
            tag = TAGS.get(tag_id, tag_id)
            data = exif[tag_id]

            if tag == "GPSInfo":
                for t in data:
                    sub_tag = GPSTAGS.get(t, t)
                    gps_info[sub_tag] = data[t]

        if not gps_info:
            return None

        # Extract coordinates
        try:
            lat_dms = gps_info.get("GPSLatitude")
            lon_dms = gps_info.get("GPSLongitude")
            lat_ref = gps_info.get("GPSLatitudeRef")
            lon_ref = gps_info.get("GPSLongitudeRef")

            if lat_dms and lon_dms and lat_ref and lon_ref:
                lat = get_decimal_coordinates(lat_dms)
                lon = get_decimal_coordinates(lon_dms)

                if lat_ref == "S":
                    lat = -lat
                if lon_ref == "W":
                    lon = -lon

                # Convert altitude safely
                altitude = gps_info.get("GPSAltitude", None)
                if altitude:
                    altitude = convert_to_float(altitude)

                gps_data = {"latitude": lat, "longitude": lon, "altitude": altitude}

                return clean_gps_data(gps_data)

        except Exception as e:
            st.warning(f"Error processing GPS coordinates: {str(e)}")
            return None

    except Exception as e:
        st.warning(f"Error reading image metadata: {str(e)}")
        return None

    return None


# Global flag to avoid spamming the same warning
has_warned_about_date_taken = False


def get_image_taken_time(image_file):
    global has_warned_about_date_taken

    try:
        img = Image.open(image_file)

        # Ensure EXIF data is available
        exif_data_bytes = img.info.get("exif", None)
        if not exif_data_bytes:
            return None  # No EXIF data available

        # Load EXIF data using piexif
        exif_data = piexif.load(exif_data_bytes)

        date_taken = exif_data.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)

        if date_taken:
            return datetime.strptime(
                date_taken.decode("utf-8"), "%Y:%m:%d %H:%M:%S"
            ).date()

    except Exception as e:
        if not has_warned_about_date_taken:
            st.toast(f"⚠️ Error extracting image date taken: {str(e)}", icon="⚠️")
            has_warned_about_date_taken = True

    return None


# Default return if no timestamp is found


def save_location_data(image_file, disease_name, confidence, gps_data):
    """Save disease detection results along with GPS data and only add Date Taken if available."""
    # Extract date taken from the image
    date_taken = get_image_taken_time(image_file)

    # Save to database with or without timestamp
    response = save_detection_to_database(
        disease_name, confidence, gps_data, date_taken
    )
    return response
