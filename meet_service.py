import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI()

class MeetRequest(BaseModel):
    event_id: str
    user_email: str

def get_calendar_service(user_email: str):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    # Check if running in the cloud using an environment variable
    service_account_env = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    
    if service_account_env:
        # Load credentials directly from Render/Cloud environment variable
        service_account_info = json.loads(service_account_env)
        creds = service_account.Credentials.from_service_account_info(
            service_account_info, 
            scopes=SCOPES
        )
    else:
        # Fallback to local service_account.json for local testing
        creds = service_account.Credentials.from_service_account_file(
            'service_account.json', 
            scopes=SCOPES
        )
    
    # Delegate access to act on behalf of the user
    delegated_creds = creds.with_subject(user_email)
    return build('calendar', 'v3', credentials=delegated_creds)

@app.post("/generate-meet")
def generate_meet(request: MeetRequest):
    try:
        service = get_calendar_service(request.user_email)
        
        # Create a temporary event in Google Calendar with Google Meet attached
        event_body = {
            'summary': 'Outlook Sync - Google Meet Link',
            'start': {'dateTime': '2026-08-07T10:00:00Z'},
            'end': {'dateTime': '2026-08-07T10:30:00Z'},
            'conferenceData': {
                'createRequest': {
                    'requestId': f"req-{request.event_id}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
        }
        
        event = service.events().insert(
            calendarId='primary',
            body=event_body,
            conferenceDataVersion=1
        ).execute()
        
        meet_link = event.get('hangoutLink')
        
        if not meet_link:
            raise HTTPException(status_code=500, detail="Failed to generate Google Meet link.")
            
        return {
            "status": "success",
            "meet_link": meet_link,
            "event_id": event.get('id')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))