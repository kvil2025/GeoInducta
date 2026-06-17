"""
Vincular fotos a muestras por ID en el nombre de archivo.
Las fotos NO tienen GPS EXIF, pero el nombre tiene el IDSAMPLE.
Usamos las coordenadas de BD_GEOL_2026_06_09.xls para geolocalizar.
NO se inventan datos.
"""
import sys, os, json, re, shutil
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

FOTOS_DIR = r"G:\Mi unidad\GeoSoil_2026-06-05\fotos"
OUTDIR = r"c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001\itrio"
COORDS_FILE = r"G:\Mi unidad\BD_GEOL_2026_06_09.xls"
FOTOS_LOCAL = os.path.join(OUTDIR, "fotos")

# Crear carpeta local para servir las fotos
os.makedirs(FOTOS_LOCAL, exist_ok=True)

# Cargar coordenadas
import pyproj
transformer = pyproj.Transformer.from_crs('EPSG:32718', 'EPSG:4326', always_xy=True)

df_coords = pd.read_excel(COORDS_FILE, engine='xlrd', sheet_name='BD_29May26')
coord_lookup = {}
for _, row in df_coords.iterrows():
    sid = row.get('IDSAMPLE')
    if pd.isna(sid):
        continue
    key = str(int(sid))
    xm = row.get('Xm')
    ym = row.get('Ym')
    if pd.isna(xm) or pd.isna(ym) or xm == -999 or ym == -999:
        continue
    lon, lat = transformer.transform(xm, ym)
    cp = str(row.get('CP', '')) if not pd.isna(row.get('CP')) else ''
    coord_lookup[key] = {'lat': round(lat, 6), 'lon': round(lon, 6), 'CP': cp}

# Tambien cargar datos de pXRF para completar IDs cortos
# Los nombres tipo "Quica 169_198_foto_1.jpg" -> 198 podria ser parte de un IDSAMPLE
# Pero tambien "Quica 32_245677_foto_1.jpg" -> 245677 (6 digitos, directo)
# Patron: el ID mas largo en el nombre

def extract_ids(filename):
    """Extraer posibles IDs del nombre."""
    base = os.path.splitext(filename)[0]
    # Buscar todos los numeros
    nums = re.findall(r'\d+', base)
    # Priorizar numeros de 6-7 digitos (IDSAMPLE completo)
    long_ids = [n for n in nums if len(n) >= 6]
    # IDs cortos (3-4 digitos) que podrian ser sufijo de 1140XXX
    short_ids = [n for n in nums if 3 <= len(n) <= 4]
    return long_ids, short_ids

# Procesar fotos
fotos = []
no_match = []
copied = 0

for fname in sorted(os.listdir(FOTOS_DIR)):
    if not fname.lower().endswith(('.jpg', '.jpeg', '.png')):
        continue
    
    long_ids, short_ids = extract_ids(fname)
    
    coords = None
    matched_id = None
    
    # Intentar con IDs largos primero
    for lid in long_ids:
        if lid in coord_lookup:
            coords = coord_lookup[lid]
            matched_id = lid
            break
    
    # Si no, intentar con IDs cortos como sufijo de 1140XXX
    if not coords:
        for sid in short_ids:
            # Probar como 1140 + sid (padding a 3-4 digitos)
            for prefix in ['1140', '114']:
                test_id = prefix + sid.zfill(3)
                if test_id in coord_lookup:
                    coords = coord_lookup[test_id]
                    matched_id = test_id
                    break
                # Sin padding
                test_id2 = prefix + sid
                if test_id2 in coord_lookup:
                    coords = coord_lookup[test_id2]
                    matched_id = test_id2
                    break
            if coords:
                break
    
    if coords:
        # Copiar foto a carpeta local
        src = os.path.join(FOTOS_DIR, fname)
        dst = os.path.join(FOTOS_LOCAL, fname)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            copied += 1
        
        fotos.append({
            'filename': fname,
            'lat': coords['lat'],
            'lon': coords['lon'],
            'sample_id': matched_id,
            'CP': coords['CP'],
            'size_kb': round(os.path.getsize(src) / 1024),
        })
    else:
        no_match.append(fname)

print("=" * 60)
print("VINCULACIÓN FOTOS → MUESTRAS")
print("=" * 60)
print("Total fotos: {}".format(len(fotos) + len(no_match)))
print("Vinculadas: {}".format(len(fotos)))
print("Sin match: {}".format(len(no_match)))
print("Copiadas a itrio/fotos/: {}".format(copied))

if no_match:
    print("\nSin match:")
    for f in no_match:
        ids = re.findall(r'\d+', f)
        print("  {} (nums: {})".format(f, ids))

print("\nVinculadas:")
for f in fotos:
    print("  {} -> IDSAMPLE={}, CP={}, ({},{})".format(
        f['filename'][:45], f['sample_id'], f['CP'], f['lat'], f['lon']))

# Agrupar por sample_id para el visor
fotos_by_sample = {}
for f in fotos:
    sid = f['sample_id']
    if sid not in fotos_by_sample:
        fotos_by_sample[sid] = []
    fotos_by_sample[sid].append(f['filename'])

print("\nResumen por muestra:")
for sid, files in sorted(fotos_by_sample.items()):
    print("  IDSAMPLE {}: {} fotos".format(sid, len(files)))

# Guardar JSON
out_json = os.path.join(OUTDIR, "fotos_gps.json")
with open(out_json, 'w', encoding='utf-8') as fp:
    json.dump(fotos, fp, ensure_ascii=False, indent=2)
print("\n✅ JSON: {} ({} fotos)".format(out_json, len(fotos)))

# Guardar agrupado por sample
out_grouped = os.path.join(OUTDIR, "fotos_por_muestra.json")
with open(out_grouped, 'w', encoding='utf-8') as fp:
    json.dump(fotos_by_sample, fp, ensure_ascii=False, indent=2)
print("✅ Agrupado: {}".format(out_grouped))
