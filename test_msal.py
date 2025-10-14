import msal

CLIENT_ID = "1f5fd89b-83a6-41cd-bb5c-794a8ff56bf9"
TENANT_ID = "75df096c-8b72-48e4-9b91-cbf79d87ee3a"
SCOPES = ["User.Read"]

app = msal.PublicClientApplication(CLIENT_ID, authority=f"https://login.microsoftonline.com/{TENANT_ID}")
flow = app.initiate_device_flow(scopes=SCOPES)
print(flow)
