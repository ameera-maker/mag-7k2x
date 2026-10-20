import json, os, sys, time, urllib.request, urllib.error, xml.etree.ElementTree as ET
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
PER_CHANNEL = 8

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None
opener = urllib.request.build_opener(NoRedirect)

def is_short(vid):
    try:
        r = opener.open(urllib.request.Request(f"https://www.youtube.com/shorts/{vid}", method="HEAD"), timeout=15)
        return r.status == 200
    except Exception:
        return False

def feed(url):
    err = None
    for i in range(3):
        try:
            return ET.fromstring(urllib.request.urlopen(url, timeout=20).read()).findall("a:entry", NS)
        except Exception as e:
            err = e
            time.sleep(3 * (i + 1))
    raise err

try:
    prev = json.load(open("data/videos.json", encoding="utf-8"))
except Exception:
    prev = []

out, failed = [], set()
for ch in json.load(open("channels.json", encoding="utf-8")):
    if not ch["id"]:
        continue
    try:
        entries = feed(f"https://www.youtube.com/feeds/videos.xml?channel_id={ch['id']}")
    except Exception as e:
        print("skip", ch["name"], e)
        failed.add(ch["name"])
        continue
    for e in entries[:PER_CHANNEL]:
        vid = e.find("yt:videoId", NS).text
        out.append({"id": vid, "title": e.find("a:title", NS).text, "channel": ch["name"],
                    "date": e.find("a:published", NS).text, "short": is_short(vid)})

if os.path.exists("playlists.json"):
    for pl in json.load(open("playlists.json", encoding="utf-8")):
        if not pl["id"]:
            continue
        try:
            entries = feed(f"https://www.youtube.com/feeds/videos.xml?playlist_id={pl['id']}")
        except Exception as e:
            print("skip playlist", pl["name"], e)
            failed.add(pl["name"])
            continue
        print(pl["name"], len(entries), "videos in feed")
        for e in entries:
            out.append({"id": e.find("yt:videoId", NS).text, "title": e.find("a:title", NS).text,
                        "channel": pl["name"], "date": e.find("a:published", NS).text,
                        "short": False, "pl": True})

out += [v for v in prev if v.get("channel") in failed]
if not out:
    print("Nothing fetched. Keeping the old file.")
    sys.exit(0)
out.sort(key=lambda v: v["date"], reverse=True)
json.dump(out, open("data/videos.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "videos;", len(failed), "feeds failed")
