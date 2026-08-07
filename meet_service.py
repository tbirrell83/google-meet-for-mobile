import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI()

class MeetRequest(BaseModel):
    event_id: str
    user_email: str

KEY_FILE_PATH = "service_account.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]

@app.post("/generate-meet")
def generate_meet(request: MeetRequest):
    try:
        creds = service_account.Credentials.from_service_account_file(
            KEY_FILE_PATH, scopes=SCOPES
        )
        delegated_creds = creds.with_subject(request.user_email)
        service = build("calendar", "v3", credentials=delegated_creds)

        # Create a new event with Google Meet attached
        now = datetime.datetime.utcnow().isoformat() + "Z"
        end = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat() + "Z"
        
        event_body = {
            "summary": "Outlook Mobile Generated Meeting",
            "start": {"dateTime": now},
            "end": {"dateTime": end},
            "conferenceData": {
                "createRequest": {
                    "requestId": f"meet-{request.event_id}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            }
        }
        
        event = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1
        ).execute()

        meet_link = event.get("hangoutLink")
        return {"status": "success", "meet_link": meet_link, "event_id": event.get("id")}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))