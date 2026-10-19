import json, urllib.request, urllib.error, xml.etree.ElementTree as ET
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
PER_CHANNEL = 8

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None
opener = urllib.request.build_opener(NoRedirect)

def is_short(vid):
    # /shorts/ID answers 200 for Shorts and redirects for normal videos.
    # On any doubt we treat it as a normal video.
    try:
        r = opener.open(urllib.request.Request(f"https://www.youtube.com/shorts/{vid}", method="HEAD"), timeout=15)
        return r.status == 200
    except Exception:
        return False

out = []
for ch in json.load(open("channels.json", encoding="utf-8")):
    if not ch["id"]:
        continue
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ch['id']}"
        root = ET.fromstring(urllib.request.urlopen(url, timeout=20).read())
    except Exception as e:
        print("skip", ch["name"], e)
        continue
    n = 0
    for e in root.findall("a:entry", NS):
        vid = e.find("yt:videoId", NS).text
        out.append({"id": vid, "title": e.find("a:title", NS).text, "channel": ch["name"],
                    "date": e.find("a:published", NS).text, "short": is_short(vid)})
        n += 1
        if n >= PER_CHANNEL:
            break
out.sort(key=lambda v: v["date"], reverse=True)
json.dump(out, open("data/videos.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "videos")
