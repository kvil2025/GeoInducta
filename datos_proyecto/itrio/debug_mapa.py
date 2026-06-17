import json, os

path = r"c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001\mapa_isoconcentraciones_Y.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

print(f"Tamaño: {len(content)/1024:.0f} KB")

# Check for NaN or Infinity in JSON (common JS killer)
script_start = content.find("<script>")
script_end = content.find("</script>")
script = content[script_start:script_end]

# Search for NaN values in the data
import re
nan_count = len(re.findall(r'\bNaN\b', script))
inf_count = len(re.findall(r'\bInfinity\b', script))
print(f"NaN en script: {nan_count}")
print(f"Infinity en script: {inf_count}")

# Check CSS @import position issue
css_start = content.find("<style>")
css_content = content[css_start:css_start+500]
import_pos = css_content.find("@import")
print(f"\n@import position in CSS: {import_pos}")
print("PROBLEMA: @import debe estar al inicio del CSS, no después de otras reglas!")

# Check coordinates of filled features
idx = content.find("const FILLED = ")
end = content.find(";\nconst LINES", idx)
filled_str = content[idx + len("const FILLED = "):end]
try:
    filled = json.loads(filled_str)
    feats = filled["features"]
    print(f"\nFILLED features: {len(feats)}")
    if feats:
        f0 = feats[0]
        coords = f0["geometry"]["coordinates"][0]
        print(f"  Feature 0 coords count: {len(coords)}")
        print(f"  Feature 0 first coord: {coords[0]}")
        print(f"  Feature 0 last coord: {coords[-1]}")
        print(f"  Feature 0 props: {f0['properties']}")
        # Check coord ranges
        all_lats = [c[1] for f in feats for ring in f["geometry"]["coordinates"] for c in ring]
        all_lons = [c[0] for f in feats for ring in f["geometry"]["coordinates"] for c in ring]
        print(f"  Lat range: {min(all_lats):.4f} to {max(all_lats):.4f}")
        print(f"  Lon range: {min(all_lons):.4f} to {max(all_lons):.4f}")
except Exception as e:
    print(f"ERROR: {e}")

# Check SAMPLES
idx2 = content.find("const SAMPLES = ")
end2 = content.find(";\nconst LEVELS", idx2)
samples_str = content[idx2 + len("const SAMPLES = "):end2]
try:
    samples = json.loads(samples_str)
    print(f"\nSAMPLES: {len(samples)}")
    print(f"  First: {samples[0]}")
    lats_s = [s["lat"] for s in samples]
    lons_s = [s["lon"] for s in samples]
    print(f"  Lat range: {min(lats_s):.4f} to {max(lats_s):.4f}")
    print(f"  Lon range: {min(lons_s):.4f} to {max(lons_s):.4f}")
except Exception as e:
    print(f"ERROR: {e}")

# Check CENTER
center_match = re.search(r'const CENTER = \[([^]]+)\]', content)
if center_match:
    print(f"\nCENTER: [{center_match.group(1)}]")
