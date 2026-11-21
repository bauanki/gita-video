import os, requests

page = os.environ["FB_PAGE_ID"].strip()
tok = os.environ["FB_PAGE_TOKEN"].strip()
repo = os.environ["GITHUB_REPOSITORY"]
name = os.environ["VIDEO_NAME"]
url = f"https://raw.githubusercontent.com/{repo}/main/videos/{name}.mp4"
caption = open("caption.txt", encoding="utf-8").read()

r = requests.post(f"https://graph.facebook.com/v21.0/{page}/videos",
                  data={"file_url": url, "description": caption,
                        "access_token": tok})
print(r.status_code, r.text[:300])
r.raise_for_status()
