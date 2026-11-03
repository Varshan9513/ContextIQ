
import os
import io

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def connect_drive():
    creds = Credentials.from_authorized_user_file(
        "token.json", SCOPES
    )
    return build("drive", "v3", credentials=creds)

def main():
    service = connect_drive()

    # Find the demo folder
    folders = service.files().list(
        q="name='ContextIQ_Demo' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()

    folder_list = folders.get("files", [])

    if not folder_list:
        print("ContextIQ_Demo folder not found!")
        return

    folder_id = folder_list[0]["id"]
    print("Found ContextIQ_Demo folder!")

    # List files inside the folder
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType)"
    ).execute()

    files = results.get("files", [])
    print("Number of files found:", len(files))

    # Read text files
    for file in files:
        if not file["name"].endswith(".txt"):
            continue

        request = service.files().get_media(fileId=file["id"])
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        content = buffer.getvalue().decode("utf-8", errors="replace")

        print("\n" + "=" * 50)
        print("FILE:", file["name"])
        print("=" * 50)
        print(content)

if __name__ == "__main__":
    main()
