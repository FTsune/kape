import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Define the scope for Google Sheets API
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Path to your service account credentials JSON file (Upload it to your project)
CREDENTIALS_FILE = "coffeediseasedb-e3243bda8356.json"

# Google Sheet name
SHEET_NAME = "CoffeeDiseaseData"


def authenticate_google_sheets():
    """Authenticate with Google Sheets API using service account credentials."""
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
    client = gspread.authorize(creds)
    return client


def get_or_create_worksheet():
    """Retrieve the Google Sheet or create it if it doesn't exist."""
    client = authenticate_google_sheets()
    try:
        sheet = client.open(SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        sheet = client.create(SHEET_NAME)
        sheet.share(client.auth.service_account_email, perm_type="user", role="writer")

    # Get first worksheet
    worksheet = sheet.sheet1

    # Set up headers if they don't exist
    if worksheet.row_count == 0:
        worksheet.append_row(
            [
                "Timestamp",
                "Disease Detected",
                "Confidence",
                "Latitude",
                "Longitude",
                "Altitude",
            ]
        )

    return worksheet


def save_detection_to_database(disease_name, confidence, gps_data):
    """Save disease detection results and GPS data to Google Sheets."""
    worksheet = get_or_create_worksheet()

    # Create an entry
    entry = [
        gspread.utils.rowcol_to_a1(
            worksheet.row_count + 1, 1
        ),  # Auto-increment timestamp
        disease_name,
        confidence,
        gps_data.get("latitude", "N/A"),
        gps_data.get("longitude", "N/A"),
        gps_data.get("altitude", "N/A"),
    ]

    # Append data
    worksheet.append_row(entry)

    return "Data saved successfully!"


# 🔹 NEW FUNCTION: Fetch all locations from Google Sheets for disease tracking
def fetch_all_locations():
    """Fetch all disease detection data from Google Sheets."""
    client = authenticate_google_sheets()
    sheet = client.open(SHEET_NAME).sheet1  # First worksheet
    records = sheet.get_all_records()
    return records if records else []
