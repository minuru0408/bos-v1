import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


def _get_sheet():
    """Return authorized gspread worksheet or (None, None) if creds missing."""
    creds_path = os.getenv("GOOGLE_SHEETS_CREDS")
    if not creds_path or not os.path.exists(creds_path):
        # Credentials are optional. If not provided, just return None
        return None, None
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    sheet = client.open("HECTOR_Memory_Log").sheet1
    return sheet, None

def log_message(role, text):
    """Append a timestamped message to Google Sheet if configured."""
    sheet, err = _get_sheet()
    if err or sheet is None:
        # No credentials configured; skip logging
        return None
    sheet.append_row([role, text, datetime.now().isoformat()])
    return None

def load_memory(limit=20):
    """Fetch the last `limit` messages from the sheet as a list of {role,content}."""
    sheet, err = _get_sheet()
    if err or sheet is None:
        # No credentials or sheet available
        return []

    # Get all rows, keep only the last `limit`
    all_rows = sheet.get_all_values()  # each row = [role, text, timestamp]
    recent = all_rows[-limit:]

    messages = []
    for row in recent:
        role, text, _ = row
        messages.append({"role": role, "content": text})
    return messages

