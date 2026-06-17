import sys; sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd, numpy as np, openpyxl

df_geo = pd.read_excel(r'G:\Mi unidad\BD_GEOL_2026_06_09.xls', engine='xlrd', sheet_name='BD_29May26')
wb = openpyxl.load_workbook(r'c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001\itrio\Datos de muestreo 09.06.xlsx', data_only=True)
ws = wb['2026 06 09']
headers = {}
for col in range(1, ws.max_column+1):
    v = ws.cell(row=1, column=col).value
    if v: headers[col] = str(v).strip()
pxrf_rows = []
for r in range(2, ws.max_row+1):
    row_data = {}
    for ci, h in headers.items():
        row_data[h] = ws.cell(row=r, column=ci).value
    pxrf_rows.append(row_data)
df_pxrf = pd.DataFrame(pxrf_rows)

geo_ids = set(str(int(v)) for v in df_geo['IDSAMPLE'].dropna())
pxrf_base_ids = set(str(v).split('_')[0] for v in df_pxrf['Sample ID'].dropna().astype(str))
matches = geo_ids & pxrf_base_ids

print(f"CRUCE: {len(matches)}/190 con coordenadas")
print()
print("=== 15 primeros matches ===")
for sid in sorted(list(matches))[:15]:
    gr = df_geo[df_geo['IDSAMPLE'] == int(sid)].iloc[0]
    pv = df_pxrf[df_pxrf['Sample ID'].astype(str).str.split('_').str[0] == sid]
    yvals = [float(v) for v in pv['Y'] if v and v != 'ND']
    ya = "{:.1f}".format(np.mean(yvals)) if yvals else "ND"
    cp = gr["CP"]
    horiz = gr.get("HORIZONTE", "")
    roca = gr.get("ROCA CAJA", "")
    yg = gr.get("Y ppm", "")
    print("  {} => CP={}, Horiz={}, Roca={}, Y_geo={}, Y_pxrf_avg={}, n={}".format(
        sid, cp, horiz, roca, yg, ya, len(pv)))

# Contar mediciones con coords
total_med = 0
for sid in matches:
    pv = df_pxrf[df_pxrf['Sample ID'].astype(str).str.split('_').str[0] == sid]
    total_med += len(pv)
print()
print("Total mediciones con coordenadas: {}".format(total_med))
print("Muestras sin coordenadas: Ejrmplo, Prueba_1, Prueba_2, 1140215")
