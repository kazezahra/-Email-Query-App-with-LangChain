# test_raganizer.py — adaptive email fetch version
import json, os, time
from datetime import datetime
from auth_utils import get_access_token
from graph_utils import list_messages
from raganizer import emails_to_documents, make_or_load_chroma

STATS_FILE = "fetch_stats.json"

# --- Load last stats (if any) ---
if os.path.exists(STATS_FILE):
    with open(STATS_FILE, "r") as f:
        stats = json.load(f)
        last_top = stats.get("last_top", 50)
        last_time = stats.get("last_time", 60)
else:
    stats = {}
    last_top, last_time = 50, 60  # default start

# --- Adaptive logic: adjust based on previous runtime ---
if last_time < 45:  # system handled it easily → increase slightly
    top = min(last_top + 25, 200)
elif last_time > 90:  # last run was slow → reduce slightly
    top = max(last_top - 25, 25)
else:
    top = last_top  # keep steady

print(f"⚙️ Adaptive fetch size: {top} emails (based on last runtime ≈ {last_time:.1f}s)\n")

# 1. Ask user for a date
selected_date_str = input("📅 Enter a date (YYYY-MM-DD): ").strip()
try:
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
except ValueError:
    print("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2025-10-13).")
    exit(1)

# 2. Get (or refresh) token automatically
ACCESS_TOKEN = get_access_token()

# 3. Fetch emails
print("📨 Fetching emails from Outlook...")
start_time = time.time()
msgs = list_messages(ACCESS_TOKEN, top=top)
elapsed = time.time() - start_time
print(f"📬 Fetched {len(msgs)} total emails in {elapsed:.2f}s")

# 4. Filter emails for the selected date
filtered_msgs = [
    m for m in msgs if m.get("receivedDateTime", "").startswith(selected_date_str)
]
print(f"📅 Found {len(filtered_msgs)} emails for {selected_date_str}")

if not filtered_msgs:
    print("⚠️ No emails found for this date. Try a different day.")
    exit(0)

# 5. Convert filtered emails to LangChain Documents
docs = emails_to_documents(filtered_msgs)
print(f"📄 Converted {len(docs)} emails to LangChain Documents")

# 6. Create and persist embeddings (offline)
chroma = make_or_load_chroma(docs, persist_dir="chroma_db_test")
print("✅ All done! Chroma database is ready for QA.\n")

# --- Save performance stats for next run ---
with open(STATS_FILE, "w") as f:
    json.dump({"last_top": top, "last_time": elapsed}, f, indent=2)
print(f"💾 Saved performance data for next adaptive run (time: {elapsed:.1f}s, top={top})")
