# msal_device_test.py
import os
import msal
import requests
from pprint import pprint

# --- CONFIG: set these to your app values ---
CLIENT_ID = "1f5fd89b-83a6-41cd-bb5c-794a8ff56bf9"
TENANT_ID = "75df096c-8b72-48e4-9b91-cbf79d87ee3a"

# Scopes we will request. (Mail.Read needed for reading mail)
SCOPES = ["User.Read", "Mail.Read"]

# Authority (tenant-specific)
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

def device_flow_login():
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

    # Start device code flow
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise ValueError("Failed to create device flow. Response:\n{}".format(flow))

    print("=== DEVICE CODE LOGIN ===")
    print("1. Open this URL in your browser:\n   ", flow["verification_uri"])
    print("2. Enter this code when prompted:\n   ", flow["user_code"])
    print("3. Sign in with the user account that has the mailbox you want to read.")
    print("\nWaiting for you to complete authentication in the browser...\n")

    # This will block until authentication completed or timed out
    result = app.acquire_token_by_device_flow(flow)  # blocks
    return result

def call_graph_list_messages(access_token):
    url = "https://graph.microsoft.com/v1.0/me/messages?$select=subject,receivedDateTime,from&$top=10"
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    res = device_flow_login()
    print("\n=== LOGIN RESULT ===")
    pprint(res)

    if "access_token" in res:
        print("\nAccess token acquired! (printing only first 100 chars)\n")
        print(res["access_token"][:100] + "...\n")

        # optional: call Graph to list messages
        try:
            msgs = call_graph_list_messages(res["access_token"])
            print("Sample mail items (up to 10):")
            for i, m in enumerate(msgs.get("value", []), 1):
                subj = m.get("subject", "<no subject>")
                frm = m.get("from", {}).get("emailAddress", {}).get("address", "")
                rcv = m.get("receivedDateTime", "")
                print(f"{i}. {subj}  —  from: {frm}  at: {rcv}")
        except Exception as e:
            print("Graph API call failed:", e)
    else:
        print("No access token found in result. See full result above for error details.")
