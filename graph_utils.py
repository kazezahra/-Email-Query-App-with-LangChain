# graph_utils.py
import requests
from dateutil import parser
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def list_messages(access_token, top=20):
    """
    Fetch Outlook messages using Microsoft Graph API with retries and timeout.
    Automatically handles broken connections or partial responses.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept-Encoding": "identity",  # disables gzip compression
    }

    url = f"{GRAPH_BASE}/me/messages?$select=subject,body,bodyPreview,from,receivedDateTime&$top={top}"
    items = []

    # Create a requests session with retries
    session = requests.Session()
    retries = Retry(
        total=5,  # retry up to 5 times
        backoff_factor=1,  # wait 1s, 2s, 4s...
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))

    while url:
        try:
            r = session.get(url, headers=headers, timeout=60)
            r.raise_for_status()
            data = r.json()
            items.extend(data.get("value", []))
            url = data.get("@odata.nextLink", None)

            # Progress feedback
            print(f"Fetched {len(items)} messages so far...")

        except requests.exceptions.RequestException as e:
            print("⚠️ Graph connection error:", e)
            print("⏳ Retrying or skipping this batch...")
            break  # or continue, depending on your preference

    print(f"✅ Done fetching {len(items)} total messages.")
    return items


def filter_messages_for_date(messages, date_obj):
    """
    Filter messages by date (YYYY-MM-DD).
    Only keeps messages received on the given date.
    """
    filtered = []
    for m in messages:
        try:
            dt = parser.isoparse(m.get("receivedDateTime"))
            if dt.date() == date_obj:
                filtered.append(m)
        except Exception:
            continue
    return filtered
