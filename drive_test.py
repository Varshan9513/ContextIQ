import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def connect_drive():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)

def main():
    service = connect_drive()
    print("Google Drive connected successfully!")

    response = service.files().list(
        pageSize=20,
        fields="files(id,name,mimeType,webViewLink)"
    ).execute()

    files = response.get("files", [])

    if not files:
        print("No files found.")

    for file in files:
        print(file["name"], "|", file["mimeType"])

if __name__ == "__main__":
    main()