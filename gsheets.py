import pathlib
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pathlib import Path


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SAMPLE_SPREADSHEET_ID = "1Gph7zNLJ3voEk0RVGufDPXczWF5gY_8KcKnh1UHdHWY"
SAMPLE_RANGE_NAME = "Signed In!A:E"


def get_range(sheet_id, r, token_path=Path(__file__).parent.resolve()/Path("token.json"),
              credential_path=Path(__file__).parent.resolve()/Path("credentials.json")):
    creds = None
    if pathlib.Path(token_path).exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credential_path), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    result = (sheet.values().get(spreadsheetId=sheet_id, range=r).execute())
    return result.get("values", [])


if __name__ == "__main__":
    print(get_range(SAMPLE_SPREADSHEET_ID, SAMPLE_RANGE_NAME))
