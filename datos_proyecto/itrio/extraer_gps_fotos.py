"""
Extraer GPS EXIF de fotos y vincular con muestras del mapa.
NO inventa datos - solo usa coordenadas reales del EXIF.
"""
import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

FOTOS_DIR = r"G:\Mi unidad\GeoSoil_2026-06-05\fotos"
OUTDIR = r"c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001\itrio"

def get_gps(path):
    """Extraer lat/lon de EXIF GPS."""
    try:
        img = Image.open(path)
        exif = img._getexif()
        if not exif:
            return None
        
        gps_info = {}
        for tag_id, val in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'GPSInfo':
                for gps_tag_id, gps_val in val.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag] = gps_val
        
        if not gps_info:
            return None
        
        def dms_to_dd(dms, ref):
            d = float(dms[0])
            m = float(dms[1])
            s = float(dms[2])
            dd = d + m/60 + s/3600
            if ref in ('S', 'W'):
                dd = -dd
            return dd
        
        if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
            lat = dms_to_dd(gps_info['GPSLatitude'], gps_info.get('GPSLatitudeRef', 'N'))
            lon = dms_to_dd(gps_info['GPSLongitude'], gps_info.get('GPSLongitudeRef', 'W'))
            alt = None
            if 'GPSAltitude' in gps_info:
                alt = float(gps_info['GPSAltitude'])
            return {'lat': round(lat, 6), 'lon': round(lon, 6), 'alt': alt}
    except Exception as e:
        return None

def extract_sample_id(filename):
    """Intentar extraer Sample ID del nombre del archivo."""
    # Patron: Quica 147_1140170_foto_1.jpg -> 1140170
    # Patron: Quica 32_245677_foto_1.jpg -> 245677
    m = re.search(r'_(\d{4,})_', filename)
    if m:
        return m.group(1)
    # Patron: numero al principio
    m = re.match(r'(\d{4,})', filename)
    if m:
        return m.group(1)
    return None

# Procesar fotos
fotos = []
no_gps = []
total = 0

for fname in sorted(os.listdir(FOTOS_DIR)):
    if not fname.lower().endswith(('.jpg', '.jpeg', '.heic', '.png')):
        continue
    total += 1
    fpath = os.path.join(FOTOS_DIR, fname)
    gps = get_gps(fpath)
    sid = extract_sample_id(fname)
    
    if gps:
        fotos.append({
            'filename': fname,
            'lat': gps['lat'],
            'lon': gps['lon'],
            'alt': gps.get('alt'),
            'sample_id': sid,
            'size_kb': round(os.path.getsize(fpath) / 1024, 0),
        })
    else:
        no_gps.append(fname)

print("=" * 60)
print("FOTOS CON GPS EXIF")
print("=" * 60)
print("Total archivos: {}".format(total))
print("Con GPS: {}".format(len(fotos)))
print("Sin GPS: {}".format(len(no_gps)))

if no_gps:
    print("\nSin GPS:")
    for f in no_gps:
        print("  - {}".format(f))

print("\nFotos con GPS:")
for f in fotos:
    print("  {} -> lat={}, lon={}, sid={}, {}KB".format(
        f['filename'][:50], f['lat'], f['lon'], f['sample_id'], int(f['size_kb'])))

# Guardar JSON para el visor
out_json = os.path.join(OUTDIR, "fotos_gps.json")
with open(out_json, 'w', encoding='utf-8') as fp:
    json.dump(fotos, fp, ensure_ascii=False, indent=2)
print("\n✅ JSON guardado: {} ({} fotos)".format(out_json, len(fotos)))

# Verificar rango geográfico
if fotos:
    lats = [f['lat'] for f in fotos]
    lons = [f['lon'] for f in fotos]
    print("\nRango GPS fotos:")
    print("  Lat: {} a {}".format(min(lats), max(lats)))
    print("  Lon: {} a {}".format(min(lons), max(lons)))
