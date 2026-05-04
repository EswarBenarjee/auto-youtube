from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import pickle
import os

# 🔐 Scope for uploading
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# ==============================
# AUTH
# ==============================
def get_authenticated_service():
    creds = None

    # Load existing token
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If no valid creds
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing token...")
            creds.refresh(Request())
        else:
            print("🔐 Opening browser for login...")
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)

# ==============================
# UPLOAD
# ==============================
def upload_video(file_path, title, description, tags):
    youtube = get_authenticated_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(file_path, resumable=True)
    )

    response = None

    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"⬆️ Upload {int(status.progress() * 100)}%")

    print("✅ Upload complete")
    return response["id"]
