from datetime import date
from graph_utils import list_messages, filter_messages_for_date
from dotenv import load_dotenv
import os

load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")



# Fetch up to 50 messages
all_msgs = list_messages(ACCESS_TOKEN, top=50)
print(f"Fetched {len(all_msgs)} total messages")

# Filter by today's date
today = date.today()
filtered = filter_messages_for_date(all_msgs, today)
print(f"Messages received today ({today}): {len(filtered)}")

# Print their subjects
for i, msg in enumerate(filtered[:5], 1):
    print(f"{i}. {msg.get('subject')} — from: {msg.get('from', {}).get('emailAddress', {}).get('address', '')}")
