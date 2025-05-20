# hector-v1
H.E.C.T.O.R v1 – AI butler web app.

## Networking

The application performs outbound HTTP requests to several APIs. Some
environments set `HTTP_PROXY`/`HTTPS_PROXY` variables that point to an
unreachable proxy, which prevents network access. The app now removes these
variables at startup so it can connect directly.

## Logging to Google Sheets

Set the `GOOGLE_SHEETS_CREDS` environment variable to the path of your
service account JSON credentials file. When configured, all user and assistant
messages are appended to the `HECTOR_Memory_Log` Google Sheet for reference.

## Gmail OAuth

Set the `GOOGLE_OAUTH_CLIENT_SECRETS` environment variable to the path of your
Google OAuth client secrets JSON. The application defaults to `credentials.json`
in the repository root if this variable is not provided.

## Running the app

Install Python dependencies and launch the server locally:

```bash
pip install -r requirements.txt
python3 app.py
```

The server listens on port `5001` by default. Set the `PORT` environment
variable to change the port, for example if `5001` is already in use:

```bash
PORT=5050 python3 app.py
```
