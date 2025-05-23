import os
from googleapiclient.discovery import build

def intelligent_search(query, num_results=5):
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cse_id  = os.getenv("GOOGLE_CSE_ID")

    if not api_key:
        raise RuntimeError("Missing GOOGLE_SEARCH_API_KEY")
    if not cse_id:
        raise RuntimeError("Missing GOOGLE_CSE_ID")

    service = build("customsearch", "v1", developerKey=api_key)
    res     = service.cse().list(q=query, cx=cse_id, num=num_results).execute()
    return res.get("items", [])
