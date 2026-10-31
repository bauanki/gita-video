import os, json, requests

tok = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": os.environ["YT_CLIENT_ID"].strip(),
    "client_secret": os.environ["YT_CLIENT_SECRET"].strip(),
    "refresh_token": os.environ["YT_REFRESH_TOKEN"].strip(),
    "grant_type": "refresh_token"}).json()["access_token"]

cap = open("caption.txt", encoding="utf-8").read()
title = (cap.split("\n")[0][:80] + " #Shorts")[:100]
meta = {"snippet": {"title": title, "description": cap + "\n#Shorts", "categoryId": "22"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}

r = requests.post(
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    headers={"Authorization": f"Bearer {tok}",
             "Content-Type": "application/json; charset=UTF-8",
             "X-Upload-Content-Type": "video/mp4"},
    data=json.dumps(meta))
print(r.status_code, r.text[:300])
r.raise_for_status()

up = requests.put(r.headers["Location"], headers={"Content-Type": "video/mp4"},
                  data=open("output.mp4", "rb").read())
print(up.status_code, up.text[:300])
