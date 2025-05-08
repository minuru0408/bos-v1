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
