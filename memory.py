import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def log_message(role, text):
    """Append a timestamped message (role + text) to Google Sheet."""
    creds_path = os.getenv("GOOGLE_SHEETS_CREDS")
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    sheet = client.open("BOS_Memory_Log").sheet1
    sheet.append_row([role, text, datetime.now().isoformat()])
def load_memory(limit=20):
    """Fetch the last `limit` messages from the sheet as a list of {role,content}."""
    creds_path = os.getenv("GOOGLE_SHEETS_CREDS")
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    sheet = client.open("BOS_Memory_Log").sheet1

    # Get all rows, keep only the last `limit`
    all_rows = sheet.get_all_values()  # each row = [role, text, timestamp]
    recent = all_rows[-limit:]

    messages = []
    for row in recent:
        role, text, _ = row
        messages.append({"role": role, "content": text})
    return messages

