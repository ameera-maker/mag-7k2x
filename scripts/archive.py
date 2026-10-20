import json, os, random, re, sys, urllib.parse, urllib.request
KEY = os.environ.get("YT_API_KEY")
if not KEY:
    print("No YT_API_KEY secret found.")
    sys.exit(1)
POOL, SKIP_NEWEST, MIN_SECONDS, MAX_PAGES = 60, 15, 180, 10

def api(path, **p):
    p["key"] = KEY
    url = "https://www.googleapis.com/youtube/v3/" + path + "?" + urllib.parse.urlencode(p)
    return json.load(urllib.request.urlopen(url, timeout=30))

def secs(d):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    if not m:
        return 0
    h, mi, s = [int(x or 0) for x in m.groups()]
    return h * 3600 + mi * 60 + s

try:
    old = json.load(open("data/archive.json", encoding="utf-8"))
except Exception:
    old = []
have = {v["channel"] for v in old}
out = list(old)

for ch in json.load(open("channels.json", encoding="utf-8")):
    if not ch["id"] or ch["name"] in have:
        continue
    try:
        items, token = [], None
        for _ in range(MAX_PAGES):
            p = dict(part="snippet,contentDetails", playlistId="UU" + ch["id"][2:], maxResults=50)
            if token:
                p["pageToken"] = token
            r = api("playlistItems", **p)
            items += r.get("items", [])
            token = r.get("nextPageToken")
            if not token:
                break
        items = [i for i in items if i["snippet"]["title"] not in ("Private video", "Deleted video")]
        items = items[SKIP_NEWEST:]
        random.shuffle(items)
        cand = items[:POOL * 2]
        keep = []
        for i in range(0, len(cand), 50):
            chunk = cand[i:i + 50]
            ids = ",".join(c["contentDetails"]["videoId"] for c in chunk)
            d = api("videos", part="contentDetails", id=ids)
            dur = {x["id"]: secs(x["contentDetails"]["duration"]) for x in d.get("items", [])}
            for c in chunk:
                vid = c["contentDetails"]["videoId"]
                if dur.get(vid, 0) >= MIN_SECONDS:
                    keep.append({"id": vid, "title": c["snippet"]["title"], "channel": ch["name"],
                                 "date": c["contentDetails"].get("videoPublishedAt") or c["snippet"]["publishedAt"],
                                 "short": False, "old": True})
        out += keep[:POOL]
        print(ch["name"], len(keep[:POOL]), "old videos")
    except Exception as e:
        print("skip", ch["name"], e)

json.dump(out, open("data/archive.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "total")
