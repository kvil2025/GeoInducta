# ============================================================
# Limpieza BD_Ytrio.csv — Pasos 1 a 7
# Genera: BD_Ytrio_LIMPIO.csv (tabla nueva)
# ============================================================
import pandas as pd
import numpy as np
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

INPUT  = r"C:\Users\geolo\Downloads\BD_Ytrio.csv"
OUTDIR = r"c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001"
OUTPUT = os.path.join(OUTDIR, "BD_Ytrio_LIMPIO.csv")
LOG    = os.path.join(OUTDIR, "log_limpieza.txt")

log_lines = []
def log(msg):
    log_lines.append(msg)
    print(msg)

# Cargar
df = pd.read_csv(INPUT)
log(f"=== CARGA ===")
log(f"Filas: {len(df)}  |  Columnas: {len(df.columns)}")

# ============================================================
# PASO 1: Eliminar columnas vacías (F29-F87) y RRE_S5_
# ============================================================
log(f"\n--- PASO 1: Eliminar columnas vacías ---")
cols_drop = [f"F{i}" for i in range(29, 88)] + ["RRE_S5_"]
cols_drop = [c for c in cols_drop if c in df.columns]
df.drop(columns=cols_drop, inplace=True)
log(f"  Eliminadas: {len(cols_drop)} columnas")
log(f"  Columnas restantes: {len(df.columns)}")

# ============================================================
# PASO 2: Marcar outliers extremos
# ============================================================
log(f"\n--- PASO 2: Marcar outliers extremos ---")

def flag_outliers(row):
    flags = []
    # Mn_ > 1%
    if pd.notna(row.get("Mn_")) and row["Mn_"] > 1.0:
        flags.append(f"Mn_ALTO({row['Mn_']}%)")
    # Fe__ > 15%
    if pd.notna(row.get("Fe__")) and row["Fe__"] > 15.0:
        flags.append(f"Fe_ALTO({row['Fe__']}%)")
    # Ca_ppm > 80000
    if pd.notna(row.get("Ca_ppm")) and row["Ca_ppm"] > 80000:
        flags.append(f"Ca_ALTO({row['Ca_ppm']}ppm)")
    # Y_ppm > 400
    if pd.notna(row.get("Y_ppm")) and row["Y_ppm"] > 400:
        flags.append(f"Y_ALTO({row['Y_ppm']}ppm)")
    # K__ > 10%
    if pd.notna(row.get("K__")) and row["K__"] > 10.0:
        flags.append(f"K_ALTO({row['K__']}%)")
    return "; ".join(flags)

df["FLAG_OUTLIER"] = df.apply(flag_outliers, axis=1)
n_flagged = (df["FLAG_OUTLIER"] != "").sum()
log(f"  Registros con outliers: {n_flagged}")
for _, r in df[df["FLAG_OUTLIER"] != ""].iterrows():
    log(f"    -> {r['Sample']}: {r['FLAG_OUTLIER']}")

# ============================================================
# PASO 3: Tratar valores BLD (=1) en REE
# ============================================================
log(f"\n--- PASO 3: Tratar valores BLD (=1 → 0.5) ---")
ree_cols = ["Th_ppm", "La_ppm", "Pr_ppm", "Ce_ppm", "Nd_ppm", "Y_ppm"]

for col in ree_cols:
    cens_col = f"{col}_cens"
    mask = df[col] == 1.0
    n_bld = mask.sum()
    df[cens_col] = mask.astype(int)
    df.loc[mask, col] = 0.5
    log(f"  {col}: {n_bld} valores BLD → 0.5  (flag en {cens_col})")

# ============================================================
# PASO 4: Marcar muestras duplicadas
# ============================================================
log(f"\n--- PASO 4: Marcar muestras duplicadas ---")
dup_mask = df.duplicated(subset=["Sample"], keep=False)
df["FLAG_DUPLICADO"] = ""

dup_samples = df.loc[dup_mask, "Sample"].unique()
for s in dup_samples:
    idxs = df.index[df["Sample"] == s].tolist()
    for rank, idx in enumerate(idxs, 1):
        df.at[idx, "FLAG_DUPLICADO"] = f"DUP_{rank}/{len(idxs)}"
    log(f"  {s}: {len(idxs)} registros")
log(f"  Total muestras duplicadas: {len(dup_samples)}")

# ============================================================
# PASO 5: Estandarizar nomenclatura litológica
# ============================================================
log(f"\n--- PASO 5: Estandarizar litología ---")

lit_map = {
    'Granito de bt':                       'Granito de Biotita',
    'Granito BT':                          'Granito de Biotita',
    'Granio de biotita':                   'Granito de Biotita',
    'Granito Biotita -Migmatita':          'Granito de Biotita',
    'Granito de Biotita Máfico':           'Granito de Biotita Mafico',
    'Granito de biotita mafico':           'Granito de Biotita Mafico',
    'Granito de biotita siliceo':          'Granito de Biotita Siliceo',
    'Granito de biotita oxidado':          'Granito de Biotita Oxidado',
    'Granito de biotita fino':             'Granito de Biotita Fino',
    'Granito de biotita fino foliado':     'Granito de Biotita Fino',
    'Granito de biotita grueso':           'Granito de Biotita Grueso',
    'Granito de Biotita porfidico':        'Granito de Biotita Porfidico',
    'Granito de Biotita >QZ':             'Granito de Biotita Rico en Qz',
    'Granito de Biotita?':                 'Granito de Biotita',
    'Granito de biotita ?':                'Granito de Biotita',
    'Granito de bt?':                      'Granito de Biotita',
    'Granito de biotita o tonalita?':      'Granito de Biotita',
    'Granito de Biotita y Anfibol':        'Granito de Biotita y Anfibol',
    'Granito de Biotita de Granate':       'Granito de Biotita con Granate',
    'Granito de Granate?':                 'Granito de Granate',
    'Granito de granate':                  'Granito de Granate',
    'Metapelitas':                         'Metapelita',
    'Metapelitas?':                        'Metapelita',
    'Metapelita?':                         'Metapelita',
    'Metapelita recristalizada':           'Metapelita Recristalizada',
    'Metapelita/Roca cornea':              'Metapelita/Hornfels',
    'Cen?/Metapelita':                     'Metapelita',
    'Tonalita Bt':                         'Tonalita de Biotita',
    'Tonalita de Bt':                      'Tonalita de Biotita',
    'Tonalita de biotita fina':            'Tonalita de Biotita Fina',
    'Tonalita de biotita?o GG':            'Tonalita de Biotita',
    'Tonalita?':                           'Tonalita',
    'Tonalita oxn':                        'Tonalita',
    'Tonalita de biotita y anfibol':       'Tonalita de Anfibol y Biotita',
    'Tonalita de Biotita (VTT)':           'Tonalita de Biotita',
    'Esquisto de Biotita?':                'Esquisto de Biotita',
    'Esquisto de Biotita (+Grt)':          'Esquisto de Biotita con Granate',
    'Roca Micacea?':                       'Roca Micacea',
    'Roca micacea?/suelo':                 'Roca Micacea',
    'hornfels':                            'Hornfels',
    'Diorita?':                            'Diorita',
    'Diorita Cuarcifera?':                 'Diorita Cuarcifera',
    'Diorita finas cuarcifera de biotita': 'Diorita Cuarcifera de Biotita',
    'Diorita porfídica':                   'Diorita Porfidica',
    'Diorita con cúmulos de granate':      'Diorita con Granate',
    'Diorita con granate':                 'Diorita con Granate',
    'Diorita fina':                        'Diorita Fina',
    'MDiorita':                            'Microdiorita',
    'Microdioria':                         'Microdiorita',
    'Granodiorita?':                       'Granodiorita',
    'Migmatita?':                          'Migmatita',
    'Migmatita (Leucosoma)':               'Migmatita Leucosoma',
    'Migmatita (Melanosoma)':              'Migmatita Melanosoma',
    'Lutita?':                             'Lutita',
    'Lutitas':                             'Lutita',
    'Areniscas':                           'Arenisca',
    'Areniscas?':                          'Arenisca',
    'Areniscas purpuras?':                 'Arenisca',
    'Arenisca media':                      'Arenisca',
    'Milonita?':                           'Milonita',
    'Granito fino':                        'Granito Fino',
    'Micro Granito':                       'Microgranito',
    'Microgranito de biotita':             'Microgranito de Biotita',
    'Microgranito de biotita/aplita':      'Microgranito de Biotita',
    'Aplita?':                             'Aplita',
    'Granito rosado':                      'Granito Rosado',
    'Halo Tonalítico':                     'Halo Tonalitico',
    'Halo Tonalítico?':                    'Halo Tonalitico',
    'Halo tonalítico o GG?':              'Halo Tonalitico',
    'Porfido dacítico':                    'Porfido Dacitico',
    'Porfido Dacitico':                    'Porfido Dacitico',
    'Dique andesita':                      'Dique Andesita',
    'Dique Andesitico':                    'Dique Andesita',
    'Dique dacitico':                      'Dique Dacitico',
    'Dique dacítico':                      'Dique Dacitico',
    'Dique microdiorita?':                 'Dique Microdiorita',
    'Dique tonalitico?':                   'Dique Tonalitico',
    'Dique tonalitico':                    'Dique Tonalitico',
    'Dique Tonalita Leucocrática':         'Dique Tonalitico',
    'Dique granitico':                     'Dique Granitico',
    'Dique granítico':                     'Dique Granitico',
    'Dique Granitico argilizado':          'Dique Granitico',
    'Dique aplítico':                      'Dique Aplitico',
    'Dique Aplita':                        'Dique Aplitico',
    'Dique Aplita afanitica':              'Dique Aplitico',
    'Dique Aplitico?':                     'Dique Aplitico',
    'Dique Diorita con orbiculos':         'Dique Diorita',
    'Dique Diorita fina':                  'Dique Diorita',
    'Dique arcilloso fino(oxidado)':       'Dique Arcilloso',
    'Dique diabasa?':                      'Dique Diabasa',
    'Dique Granodioritico?':               'Dique Granodioritico',
    'Dique pegmatitico':                   'Dique Pegmatitico',
    'Dique Pegm':                          'Dique Pegmatitico',
    'Dique indeterminado':                 'Dique Indeterminado',
    'Zona de falla':                       'Zona de Falla',
    'Falla':                               'Zona de Falla',
    'Roca de Falla':                       'Zona de Falla',
    'Xenolito de tonalita?':               'Xenolito Tonalitico',
    'Xenolito microdioritico':             'Xenolito Microdioritico',
    'Xenolito Dioritico':                  'Xenolito Dioritico',
    'Xenolito de GB':                      'Xenolito de Granito',
    'Xenolito':                            'Xenolito',
    'Enclave Máfico':                      'Enclave Mafico',
    'Enclave Tonalitico':                  'Enclave Tonalitico',
    'Enclave Dioritico':                   'Enclave Dioritico',
    'Sedimento fino (GBt)':                'Sedimento Fino',
    'Sedimento grueso (GBt)':              'Sedimento Grueso',
    'Sedimento magnetita':                 'Sedimento Magnetita',
    'Arena de río':                        'Arena',
    'Suelo orgánico':                      'Suelo',
    'Roca Sedimentarias':                  'Roca Sedimentaria',
    'Vetilla':                             'Vetilla',
    'Vetillas':                            'Vetilla',
    'Vetilla de oxidos negros':            'Vetilla de Oxidos',
    'Vetilla Oxidos':                      'Vetilla de Oxidos',
    'Vetilla Caol-Lim':                    'Vetilla Caolinita-Limonita',
    'Vetilla Qz Plg':                      'Vetilla Cuarzo-Plagioclasa',
    'Vetilla Qz Feldespsato':             'Vetilla Cuarzo-Feldespato',
    'Oxidos Negros':                       'Oxidos Negros',
    'VTT Limonitas-Micas':                 'VTT Limonitas-Micas',
    'VTT Pegmatitica':                     'VTT Pegmatitica',
    'veta de kaolin':                      'Veta de Caolin',
    'MIGMATITA(Franja Go>Jr>Grt)':         'Migmatita con Granate',
    'Granito Gráfico':                     'Granito Grafico',
    'Cúmulo anfiboles':                    'Cumulo de Anfiboles',
}

df["Litology"] = df["Litology"].fillna("").str.strip()
df["Litology_STD"] = df["Litology"].replace(lit_map)
df.loc[df["Litology_STD"].str.strip() == "", "Litology_STD"] = "SIN_ASIGNAR"

n_changed = (df["Litology"] != df["Litology_STD"]).sum()
n_sin = (df["Litology_STD"] == "SIN_ASIGNAR").sum()
n_unique = df["Litology_STD"].nunique()
log(f"  Litologías cambiadas: {n_changed}")
log(f"  Sin asignar: {n_sin}")
log(f"  Litologías únicas finales: {n_unique}")

# ============================================================
# PASO 6: Corregir coordenada anómala (COTA < 0)
# ============================================================
log(f"\n--- PASO 6: Corregir COTA anómala ---")
mask_cota = df["COTA_M"] < 0
n_cota = mask_cota.sum()
for _, r in df[mask_cota].iterrows():
    log(f"  {r['Sample']}: COTA_M={r['COTA_M']} → NaN")
    # Agregar al flag
    old_flag = df.at[r.name, "FLAG_OUTLIER"]
    sep = "; " if old_flag else ""
    df.at[r.name, "FLAG_OUTLIER"] = f"{old_flag}{sep}COTA_NEGATIVA({r['COTA_M']})"
df.loc[mask_cota, "COTA_M"] = np.nan
log(f"  Corregidas: {n_cota}")

# ============================================================
# PASO 7: Evaluar TLC_REO_P3
# ============================================================
log(f"\n--- PASO 7: Evaluar TLC_REO_P3 ---")
tlc_valid = df["TLC_REO_P3"].notna() & (df["TLC_REO_P3"].astype(str).str.strip() != "")
n_tlc = tlc_valid.sum()
log(f"  Registros con dato: {n_tlc} ({n_tlc/len(df)*100:.1f}%)")
log(f"  Columna mantenida — cobertura parcial documentada")

# ============================================================
# EXPORTAR
# ============================================================
log(f"\n--- EXPORTAR ---")
df.to_csv(OUTPUT, index=False)
log(f"  Archivo: {OUTPUT}")
log(f"  Filas: {len(df)}")
log(f"  Columnas: {len(df.columns)}")

# Resumen columnas finales
log(f"\n=== COLUMNAS FINALES ({len(df.columns)}) ===")
for i, c in enumerate(df.columns, 1):
    log(f"  {i:2d}. {c}  ({df[c].dtype})")

# Resumen general
log(f"\n{'='*50}")
log(f"  RESUMEN DE LIMPIEZA")
log(f"{'='*50}")
log(f"  Columnas: 90 → {len(df.columns)}")
log(f"  Eliminadas: {len(cols_drop)} columnas vacías")
log(f"  Outliers marcados: {n_flagged} registros")
log(f"  BLD sustituidos: Th={df['Th_ppm_cens'].sum()}, La={df['La_ppm_cens'].sum()}, "
    f"Pr={df['Pr_ppm_cens'].sum()}, Ce={df['Ce_ppm_cens'].sum()}, "
    f"Nd={df['Nd_ppm_cens'].sum()}, Y={df['Y_ppm_cens'].sum()}")
log(f"  Duplicados: {len(dup_samples)} muestras")
log(f"  Litologías estandarizadas: {n_changed}")
log(f"  Cotas corregidas: {n_cota}")
log(f"{'='*50}")

# Guardar log
with open(LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))

print(f"\n✅ LIMPIEZA COMPLETADA → {OUTPUT}")
