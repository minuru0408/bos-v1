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
If the variable is omitted or the file is missing, the application simply
skips loading and logging conversation history.

## Gmail OAuth

The application can send and read email once it is authorized with a Google
account. Follow these steps:

1. In the **Google Cloud Console**, create a project and enable the **Gmail API**.
2. Under **Credentials**, create an **OAuth client ID** for a web application and
   download the JSON file containing the client secrets.
3. Set the `GOOGLE_OAUTH_CLIENT_SECRETS` environment variable to the path of this
   JSON file. If the variable is not set, the app looks for `credentials.json` in
   the repository root.
4. (Optional) Set `GMAIL_TOKEN_FILE` to control where the OAuth token is stored.
   It defaults to `gmail_token.json` in the repository root.
5. Run the server and visit `/oauth2login` in your browser to authorize the
   application. Once authorization completes you can use `/api/email/send` to
   dispatch messages on behalf of the authenticated account.
   
Set the `GOOGLE_OAUTH_CLIENT_SECRETS` environment variable to the path of your
Google OAuth client secrets JSON. The application defaults to `credentials.json`
in the repository root if this variable is not provided. The OAuth token is
saved to `gmail_token.json` unless you override the path with
`GMAIL_TOKEN_FILE`.

## Running the app

Install Python dependencies and launch the server locally:

```bash
pip install -r requirements.txt
python3 app.py
```

If you skip the `pip install` step, the server fails to start with errors like
`ModuleNotFoundError: No module named 'openai'`, which means `/oauth2login` will
refuse to connect because nothing is listening on port 5002.

The server listens on port `5002` by default. Hosting services such as Render
often set the `PORT` environment variable to something else (sometimes as high
as `10000`). You can override the port manually when launching the server:

```bash
PORT=5001 python3 app.py
```
