import base64
import uuid
from typing import Any, Dict

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

app = FastAPI(title="GST Verification API")

# Enable permissive CORS by default (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for sessions
gstSessions: Dict[str, Dict[str, Any]] = {}


class GSTDetailsRequest(BaseModel):
    sessionId: str
    GSTIN: str
    captcha: str


@app.get("/api/v1/getCaptcha")
def get_captcha():
    try:
        captcha_url = "https://services.gst.gov.in/services/captcha"
        session = requests.Session()
        session_id = str(uuid.uuid4())

        # Initialize session with GST portal
        session.get("https://services.gst.gov.in/services/searchtp")

        # Fetch captcha image
        captcha_response = session.get(captcha_url)
        captcha_response.raise_for_status()
        captcha_bytes = captcha_response.content
        captcha_base64 = base64.b64encode(captcha_bytes).decode("utf-8")

        # For testing/inspection: save the captcha locally
        try:
            image_string = (
                f'<img src="data:image/png;base64,{captcha_base64}" alt="captcha">'
            )
            with open("captcha.html", "w", encoding="utf-8") as f:
                f.write(image_string)
            with open("captcha.png", "wb") as f:
                f.write(captcha_bytes)
        except Exception:
            # Non-fatal: file system might be read-only in some environments
            pass

        gstSessions[session_id] = {"session": session, "captcha": captcha_bytes}

        return {
            "sessionId": session_id,
            "image": "data:image/png;base64," + captcha_base64,
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error in fetching captcha")


@app.post("/api/v1/getGSTDetails")
def get_gst_details(payload: GSTDetailsRequest):
    try:
        user = gstSessions.get(payload.sessionId)
        if not user or not user.get("session"):
            raise HTTPException(status_code=400, detail="Invalid session id")

        session: requests.Session = user["session"]

        gstData = {"gstin": payload.GSTIN, "captcha": payload.captcha}

        response = session.post(
            "https://services.gst.gov.in/services/api/search/taxpayerDetails",
            json=gstData,
        )
        # If remote service returns an error, propagate status when possible
        if not response.ok:
            return {
                "error": "Upstream error",
                "status_code": response.status_code,
                "body": safe_json(response),
            }

        return safe_json(response)
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error in fetching GST Details")


def safe_json(resp: requests.Response):
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


@app.get("/")
def health():
    return {"status": "ok", "service": "GST Verification API"}


@app.get("/api/v1/captcha/{session_id}")
def serve_captcha(session_id: str):
    user = gstSessions.get(session_id)
    if not user or not user.get("captcha"):
        raise HTTPException(status_code=404, detail="Captcha not found")
    return Response(
        content=user["captcha"],
        media_type="image/png",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )

if __name__ == "__main__":
    import uvicorn

    # Default FastAPI/uvicorn port is 8000
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
