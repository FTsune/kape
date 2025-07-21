import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from geopy.geocoders import Nominatim
import piexif
from modules.database import save_detection_to_database
import io


def get_decimal_coordinates(gps_coords):
    """Convert GPS coordinates from degrees/minutes/seconds to decimal degrees."""
    try:
        degrees = float(gps_coords[0])
        minutes = float(gps_coords[1])
        seconds = float(gps_coords[2])
        decimal_degrees = degrees + minutes / 60 + seconds / 3600
        return decimal_degrees
    except (ValueError, TypeError, IndexError) as e:
        st.warning(f"Error converting GPS coordinates: {e}")
        return None


def convert_to_float(value):
    """Convert EXIF GPS data to a float if it's an IFDRational type."""
    try:
        if isinstance(value, tuple) and len(value) >= 2:  # Handle rational numbers
            if value[1] != 0:  # Avoid division by zero
                return float(value[0]) / float(value[1])
            else:
                return float(value[0])
        elif isinstance(value, (int, float)):
            return float(value)
        else:
            return None
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def clean_gps_data(gps_data):
    """Ensure all GPS data values are JSON serializable."""
    if not gps_data or not isinstance(gps_data, dict):
        return None

    try:
        return {
            "latitude": float(gps_data["latitude"])
            if gps_data.get("latitude") is not None
            else None,
            "longitude": float(gps_data["longitude"])
            if gps_data.get("longitude") is not None
            else None,
            "altitude": convert_to_float(gps_data.get("altitude"))
            if gps_data.get("altitude") is not None
            else None,
        }
    except (ValueError, TypeError, KeyError):
        return None


def get_gps_location(image_file):
    """Extract GPS information from image metadata with robust error handling."""
    try:
        # Handle both file objects and file paths
        if hasattr(image_file, "read"):
            # It's a file-like object, read it into bytes
            image_bytes = image_file.read()
            image_file.seek(0)  # Reset file pointer for later use
            img = Image.open(io.BytesIO(image_bytes))
        else:
            img = Image.open(image_file)

        # Try to get EXIF data safely
        try:
            exif = img._getexif()
        except AttributeError:
            # Fallback method if _getexif() is not available
            exif = img.getexif()
            if not exif:
                return None

        if not exif:
            return None

        gps_info = {}

        # Find the GPS info tag
        for tag_id in exif:
            try:
                tag = TAGS.get(tag_id, tag_id)
                data = exif[tag_id]

                if tag == "GPSInfo":
                    for t in data:
                        sub_tag = GPSTAGS.get(t, t)
                        gps_info[sub_tag] = data[t]
            except (KeyError, TypeError):
                continue

        if not gps_info:
            return None

        # Extract coordinates with validation
        try:
            lat_dms = gps_info.get("GPSLatitude")
            lon_dms = gps_info.get("GPSLongitude")
            lat_ref = gps_info.get("GPSLatitudeRef")
            lon_ref = gps_info.get("GPSLongitudeRef")

            if all([lat_dms, lon_dms, lat_ref, lon_ref]):
                lat = get_decimal_coordinates(lat_dms)
                lon = get_decimal_coordinates(lon_dms)

                if lat is None or lon is None:
                    return None

                if lat_ref == "S":
                    lat = -lat
                if lon_ref == "W":
                    lon = -lon

                # Validate coordinate ranges
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    st.warning("GPS coordinates are out of valid range")
                    return None

                # Convert altitude safely
                altitude = gps_info.get("GPSAltitude")
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
    """Extract image taken time with robust error handling."""
    global has_warned_about_date_taken

    try:
        # Handle both file objects and file paths
        if hasattr(image_file, "read"):
            image_bytes = image_file.read()
            image_file.seek(0)  # Reset file pointer
            img = Image.open(io.BytesIO(image_bytes))
        else:
            img = Image.open(image_file)

        # Try multiple methods to get EXIF data
        exif_data_bytes = None

        # Method 1: Try getting from info
        if hasattr(img, "info") and "exif" in img.info:
            exif_data_bytes = img.info["exif"]

        # Method 2: Try getexif() method
        if not exif_data_bytes:
            try:
                exif_dict = img.getexif()
                if exif_dict:
                    # Try to find DateTime tags
                    for tag_id, value in exif_dict.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        if tag_name == "DateTimeOriginal":
                            if isinstance(value, str):
                                return datetime.strptime(
                                    value, "%Y:%m:%d %H:%M:%S"
                                ).date()
            except Exception:
                pass

        if not exif_data_bytes:
            return None

        # Load EXIF data using piexif with error handling
        try:
            exif_data = piexif.load(exif_data_bytes)
            date_taken = exif_data.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)

            if date_taken:
                # Handle both bytes and string types
                if isinstance(date_taken, bytes):
                    date_string = date_taken.decode("utf-8")
                else:
                    date_string = str(date_taken)

                return datetime.strptime(date_string, "%Y:%m:%d %H:%M:%S").date()

        except piexif.InvalidImageDataError:
            # If piexif fails, try alternative method
            pass
        except Exception as e:
            if not has_warned_about_date_taken:
                st.warning(f"Error parsing EXIF date: {str(e)}")

    except Exception as e:
        if not has_warned_about_date_taken:
            st.warning(f"Error extracting image date taken: {str(e)}")
            has_warned_about_date_taken = True

    return None


def get_location_name(latitude, longitude):
    """Return a human-readable location name from GPS coordinates with timeout and error handling."""
    try:
        # Validate inputs
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            return "Invalid coordinates"

        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return "Coordinates out of range"

        geolocator = Nominatim(
            user_agent="brewguard",
            timeout=10,  # Add timeout to prevent hanging
        )
        location = geolocator.reverse((latitude, longitude), language="en")
        return location.address if location else "Unknown location"

    except Exception as e:
        return f"Unable to retrieve location: {str(e)}"


def save_location_data(image_file, disease_name, confidence, gps_data):
    """Save disease detection results along with GPS data and only add Date Taken if available."""
    try:
        # Extract date taken from the image
        date_taken = get_image_taken_time(image_file)

        # Save to database with or without timestamp
        response = save_detection_to_database(
            disease_name, confidence, gps_data, date_taken
        )
        return response

    except Exception as e:
        st.error(f"Error saving location data: {str(e)}")
        return None
