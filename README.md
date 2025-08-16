# GST Verification API (FastAPI)

Fetches GST taxpayer details using a GSTIN and returns structured JSON. Maintains a per-session captcha flow to comply with the GST portal.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Endpoints](#endpoints)
- [Support](#support)
- [Contribution](#contribution)

## Features

- Maintains in-memory session info to handle dynamic captcha.
- Submit GSTIN + captcha to fetch taxpayer details.
- Returns data as JSON; bubbles up upstream errors when applicable.
- CORS enabled by default for easy integration.

## Installation

1) Clone the repository

```bash
git clone https://github.com/Manav-khadka/gst-verification.git
cd gst-verification
```

2) Create and activate a virtual environment

```bash
python -m venv venv
# Windows (PowerShell/CMD)
venv\Scripts\activate
# Windows bash (e.g., Git Bash) or Linux/macOS
source venv/Scripts/activate || source venv/bin/activate
```

3) Install dependencies

```bash
pip install -r requirements.txt
```

4) Run the API (FastAPI + Uvicorn)

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

- API base: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Note: If you run `python app.py`, it will start on port 8000 by default.

## Usage

High-level flow:

1) Call GET `/api/v1/getCaptcha` to get a fresh captcha (base64 + sessionId).
2) Show captcha to the user; collect GSTIN and the captcha text.
3) Call POST `/api/v1/getGSTDetails` with `sessionId`, `GSTIN`, and `captcha`.
4) Receive GSTIN details as JSON, or an error object if the upstream call failed.

### Quick examples

Fetch captcha

```bash
curl -s http://127.0.0.1:8000/api/v1/getCaptcha
```

Submit GSTIN + captcha

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/getGSTDetails \
  -H "Content-Type: application/json" \
  -d '{
        "sessionId": "<from-getCaptcha>",
        "GSTIN": "01ABCDE0123F0AA",
        "captcha": "<user_entered_text>"
      }'
```

## Endpoints

### Health

- Method: GET
- Path: `/`
- Description: Basic health check
- Response: `{ "status": "ok", "service": "GST Verification API" }`

### Fetch captcha (base64)

- Method: GET
- Path: `/api/v1/getCaptcha`
- Description: Fetches a new captcha and session id. `image` is a data URL you can render directly.
- Response example:

```json
{
  "sessionId": "<uuid>",
  "image": "data:image/png;base64,<captchaBase64>"
}
```

### Fetch captcha (binary image by session)

- Method: GET
- Path: `/api/v1/captcha/{sessionId}`
- Description: Returns the captcha PNG for a session (useful if you prefer an <img src> URL over base64).
- Response: `image/png`

### Get GST details

- Method: POST
- Path: `/api/v1/getGSTDetails`
- Description: Submits GSTIN + captcha to the GST portal and returns parsed JSON. If the upstream service errors, an object like `{ "error": "Upstream error", "status_code": <code>, "body": <payload> }` is returned.
- Request body:

```json
{
  "sessionId": "<from-getCaptcha>",
  "GSTIN": "01ABCDE0123F0AA",
  "captcha": "<user_entered_text>"
}
```

- Typical success response (shape may vary by GST portal):

```json
{
  "gstin": "01ABCDE0123F0AA",
  "lgnm": "ABCDEF GHIJK",
  "tradeNam": "Trade Name",
  "ctb": "Proprietorship",
  "dty": "Regular",
  "nba": ["Retail Business", "Wholesale Business", "Supplier of Services"],
  "pradr": { "adr": "Address" },
  "rgdt": "Registration Date",
  "stj": "Division",
  "sts": "Status"
}
```

## Notes

- Sessions are stored in memory; restarting the server clears them.
- Captcha must be solved by a human. Do not attempt to bypass or automate captcha solving.
- Adjust CORS origins in `app.py` if you need to restrict access.

## Support

For questions or help, please open an issue on the repository.

## Contribution

We welcome contributions to improve this project. Ways to help:

1. Report bugs via GitHub Issues.
2. Propose features/enhancements.
3. Submit pull requests from a feature branch:
   - `git checkout -b feature/<name>`
   - Commit and push
   - Open a PR against `main`

Please ensure changes are linted/tested where applicable and keep docs up to date.
