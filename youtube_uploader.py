from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

def upload_video(file_path, title, description, tags):
    with open("token.pickle", "rb") as token:
        credentials = pickle.load(token)

    youtube = build("youtube", "v3", credentials=credentials)

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
        media_body=MediaFileUpload(file_path)
    )

    response = request.execute()
    return response["id"]
