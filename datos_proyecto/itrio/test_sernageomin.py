import urllib.request, json, ssl, sys
sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    # Macrostrat - geologia global con cobertura Chile
    "https://macrostrat.org/api/v2/geologic_units/map?lat=-36.74&lng=-72.93&format=geojson",
    # USGS geology  
    "https://mrdata.usgs.gov/services/sgmc2?service=WMS&request=GetCapabilities",
    # OneGeology portal
    "https://onegeology-europe.brgm.fr/geolology_unece_wms?service=WMS&version=1.3.0&request=GetCapabilities",
    # Macrostrat tiles
    "https://tiles.macrostrat.org/carto/0/0/0.png",
    # Macrostrat burwell  
    "https://macrostrat.org/api/v2/maps?lat=-36.74&lng=-72.93",
]

for u in urls:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=10, context=ctx)
        content = r.read(3000).decode("utf-8", errors="replace")
        ct = r.headers.get("Content-Type","")
        print(f"OK [{r.status}] {ct}: {u}")
        if "json" in ct:
            try:
                d = json.loads(content + r.read().decode("utf-8","replace"))
                print(f"  Keys: {list(d.keys())[:10]}")
                if "success" in d:
                    print(f"  success={d['success']}")
                if "data" in d and isinstance(d["data"], list):
                    print(f"  {len(d['data'])} items")
                    if d["data"]:
                        print(f"  First: {json.dumps(d['data'][0], ensure_ascii=False)[:300]}")
            except:
                print(f"  Raw: {content[:300]}")
        elif "png" in ct or "image" in ct:
            print(f"  Image tile OK, size={len(content)} bytes")
        else:
            print(f"  Content: {content[:300]}")
    except Exception as e:
        print(f"FAIL: {u}")
        print(f"  -> {type(e).__name__}: {str(e)[:150]}")
    print()
