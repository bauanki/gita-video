import os, time, requests

IG_ID = os.environ["IG_ID"]
TOKEN = os.environ["FB_TOKEN"]
repo = os.environ["GITHUB_REPOSITORY"]
name = os.environ["VIDEO_NAME"]
url = f"https://raw.githubusercontent.com/{repo}/main/videos/{name}.mp4"
caption = open("caption.txt", encoding="utf-8").read()
G = "https://graph.facebook.com/v21.0"

time.sleep(30)
r = requests.post(f"{G}/{IG_ID}/media", data={
    "media_type": "REELS", "video_url": url,
    "caption": caption, "access_token": TOKEN}).json()
print(r)
cid = r["id"]

for _ in range(30):
    s = requests.get(f"{G}/{cid}", params={"fields": "status_code",
                     "access_token": TOKEN}).json()
    print(s)
    if s.get("status_code") == "FINISHED":
        break
    if s.get("status_code") == "ERROR":
        raise SystemExit("Instagram processing error")
    time.sleep(10)

p = requests.post(f"{G}/{IG_ID}/media_publish",
                  data={"creation_id": cid, "access_token": TOKEN}).json()
print(p)
