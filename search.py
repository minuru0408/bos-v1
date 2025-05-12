import os
from googleapiclient.discovery import build


def intelligent_search(query):
   """Return top search results for the query via Google Custom Search."""
   api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
   cse_id  = os.getenv("GOOGLE_CSE_ID")
   service = build("customsearch", "v1", developerKey=api_key)
   res     = service.cse().list(q=query, cx=cse_id).execute()
   return res.get("items", [])




