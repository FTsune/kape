from datetime import datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from hashlib import md5
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# Authenticate and return a Google Drive instance using Streamlit Secrets
def authenticate_drive():
    try:
        credentials_dict = st.secrets["gcp_oauth"]  # Use secrets from Streamlit
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_dict, ["https://www.googleapis.com/auth/drive"]
        )
        
        gauth = GoogleAuth()
        gauth.credentials = creds
        drive = GoogleDrive(gauth)

        return drive
    except Exception as e:
        st.error(f"Failed to authenticate Google Drive: {e}")
        return None

# Upload image to Google Drive in structured folders (Disease/Date)
def upload_image(image_path, disease_label, drive, parent_folder_id):
    # Step 1: Get or create disease folder
    file_list = drive.ListFile(
        {"q": f"'{parent_folder_id}' in parents and trashed=false"}
    ).GetList()
    disease_folder_id = None
    for file in file_list:
        if (
            file["title"].lower() == disease_label.lower()
            and file["mimeType"] == "application/vnd.google-apps.folder"
        ):
            disease_folder_id = file["id"]
            break

    if not disease_folder_id:
        folder_metadata = {
            "title": disease_label,
            "parents": [{"id": parent_folder_id}],
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        disease_folder_id = folder["id"]

    # Step 2: Get or create date folder (MM-DD-YY)
    today = datetime.now().strftime("%m-%d-%y")
    date_folders = drive.ListFile(
        {"q": f"'{disease_folder_id}' in parents and trashed=false"}
    ).GetList()
    date_folder_id = None
    for file in date_folders:
        if (
            file["title"] == today
            and file["mimeType"] == "application/vnd.google-apps.folder"
        ):
            date_folder_id = file["id"]
            break

    if not date_folder_id:
        date_metadata = {
            "title": today,
            "parents": [{"id": disease_folder_id}],
            "mimeType": "application/vnd.google-apps.folder",
        }
        date_folder = drive.CreateFile(date_metadata)
        date_folder.Upload()
        date_folder_id = date_folder["id"]

    # Step 3: Upload with duplicate checking
    with open(image_path, "rb") as f:
        file_hash = md5(f.read()).hexdigest()
    filename = f"{disease_label}_{file_hash}.jpg"

    existing_files = drive.ListFile(
        {
            "q": f"'{date_folder_id}' in parents and trashed=false and title = '{filename}'"
        }
    ).GetList()

    if existing_files:
        return f"⚠️ Skipped: Duplicate already exists."

    file = drive.CreateFile({"title": filename, "parents": [{"id": date_folder_id}]})
    file.SetContentFile(image_path)
    file.Upload()

    return f"✅ Uploaded: {filename} to {disease_label}/{today}/"
