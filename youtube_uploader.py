import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubeUploader:
    def __init__(self, client_secret_file="client_secret.json"):
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        self.client_secret_file = client_secret_file
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.credentials = None

    def authenticate(self):
        """Handles OAuth2 flow."""
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.credentials = pickle.load(token)

        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                if not os.path.exists(self.client_secret_file):
                    raise FileNotFoundError(f"Missing '{self.client_secret_file}'")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file, self.SCOPES)
                self.credentials = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(self.credentials, token)

        return build(self.api_service_name, self.api_version, credentials=self.credentials)

    def upload_video(self, file_path, title, description, category_id="22", privacy="private"):
        youtube = self.authenticate()

        body = {
            'snippet': {
                'title': title[:100],
                'description': description,
                'tags': ['podcast', 'audio'],
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': False
            }
        }

        print(f"🚀 Uploading to YouTube: {title}...")
        
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Progress: {int(status.progress() * 100)}%")

        return f"https://youtu.be/{response['id']}"

if __name__ == "__main__":
    # Run this locally to generate token.pickle
    uploader = YouTubeUploader()
    uploader.authenticate()
    print("✅ Token generated!")
