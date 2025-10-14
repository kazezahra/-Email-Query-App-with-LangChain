# auth_utils.py
import msal, json
import os
from dotenv import load_dotenv
load_dotenv()  # <-- ensures .env is read from current directory

# 🔍 Debug check – confirm environment variables are loaded
print("CLIENT_ID:", os.getenv("AZ_CLIENT_ID"))
print("TENANT_ID:", os.getenv("AZ_TENANT_ID"))

CACHE_FILE = "token_cache.json"

def get_access_token(scopes=["Mail.Read", "User.Read"]):
    """
    Automatically retrieves or refreshes an access token.
    Caches token to token_cache.json for future runs.
    """
    CLIENT_ID = os.getenv("AZ_CLIENT_ID")
    TENANT_ID = os.getenv("AZ_TENANT_ID")
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

    # Load token cache if available
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        cache.deserialize(open(CACHE_FILE, "r").read())

    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)

    # Try to get a valid token silently
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
        if result and "access_token" in result:
            print("✅ Using cached access token.")
            return result["access_token"]

    # If silent fails, initiate device code flow
    print("🔑 No valid token found. Initiating device code flow...")
    flow = app.initiate_device_flow(scopes=scopes)
    if "user_code" not in flow:
        raise ValueError("Failed to initiate device flow.")

    print(f"Go to {flow['verification_uri']} and enter code: {flow['user_code']}")
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        print("✅ Got new access token!")
        # Save to cache
        open(CACHE_FILE, "w").write(cache.serialize())
        return result["access_token"]

    raise ValueError("❌ Could not get access token.")
