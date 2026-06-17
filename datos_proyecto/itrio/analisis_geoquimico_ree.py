"""
ANÁLISIS GEOQUÍMICO DE EXPLORACIÓN — TIERRAS RARAS (REE)
Biobío/Ñuble, Chile
Fuentes: BD_Ytrio (2906) + BD_GEOL_2026 (59) + pXRF_2026 (187)

Objetivos:
1. Estadísticas descriptivas por litología
2. Correlaciones Y vs otros elementos (indicadores)
3. Ratios geoquímicos diagnósticos
4. Análisis espacial de anomalías
5. Clasificación de potencial REE por zona
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
from scipy import stats

OUTDIR = r"c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001\itrio"

# Cargar datos integrados
df = pd.read_csv(os.path.join(OUTDIR, "BD_INTEGRADA_2026.csv"))

# Convertir a numérico
num_cols = ['Y_ppm','Y_pond','Ce_ppm','La_ppm','Th_ppm','Nd_ppm','Pr_ppm','Fe__','Ti__',
            'UTM_E','UTM_N','lat','lon','COTA_M']
for c in num_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce')

print("=" * 70)
print("ANÁLISIS GEOQUÍMICO DE EXPLORACIÓN — TIERRAS RARAS")
print("=" * 70)
print(f"\nTotal muestras: {len(df)}")
print(f"Con Y_ppm: {df['Y_ppm'].notna().sum()}")
print(f"Con Y_pond: {df['Y_pond'].notna().sum()}")

# ══════════════════════════════════════════════════════════════════
# 1. ESTADÍSTICAS DESCRIPTIVAS GLOBALES
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("1. ESTADÍSTICAS DESCRIPTIVAS GLOBALES")
print("=" * 70)

for elem in ['Y_ppm','Y_pond','Ce_ppm','La_ppm','Th_ppm','Nd_ppm','Fe__','Ti__']:
    vals = df[elem].dropna()
    if len(vals) > 10:
        p25 = vals.quantile(0.25)
        p75 = vals.quantile(0.75)
        iqr = p75 - p25
        umbral_anom = p75 + 1.5 * iqr  # Tukey fence
        n_anom = (vals > umbral_anom).sum()
        print(f"\n  {elem:10s}: n={len(vals):5d}, media={vals.mean():7.1f}, "
              f"med={vals.median():7.1f}, std={vals.std():7.1f}, "
              f"min={vals.min():7.1f}, P25={p25:.1f}, P75={p75:.1f}, max={vals.max():7.1f}, "
              f"umbral_anom={umbral_anom:.1f}, n_anom={n_anom}")

# ══════════════════════════════════════════════════════════════════
# 2. ESTADÍSTICAS POR LITOLOGÍA (top 10)
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("2. ESTADÍSTICAS Y (ppm) POR LITOLOGÍA (principales)")
print("=" * 70)

lit_stats = []
for lit, grp in df.groupby('Litology_STD'):
    yv = grp['Y_ppm'].dropna()
    if len(yv) >= 5:
        lit_stats.append({
            'Litologia': lit,
            'N': len(yv),
            'Y_media': yv.mean(),
            'Y_mediana': yv.median(),
            'Y_std': yv.std(),
            'Y_max': yv.max(),
            'Y_P95': yv.quantile(0.95),
            'Pct_sobre_50': (yv >= 50).mean() * 100,
            'Pct_sobre_100': (yv >= 100).mean() * 100,
        })

lit_df = pd.DataFrame(lit_stats).sort_values('Y_media', ascending=False)
print(lit_df.to_string(index=False))
lit_df.to_csv(os.path.join(OUTDIR, "geoquimica_litologias.csv"), index=False)

# ══════════════════════════════════════════════════════════════════
# 3. CORRELACIONES — INDICADORES DE ENRIQUECIMIENTO REE
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("3. CORRELACIONES — INDICADORES DE ENRIQUECIMIENTO REE")
print("=" * 70)

pairs = [
    ('Y_ppm', 'Ce_ppm'), ('Y_ppm', 'La_ppm'), ('Y_ppm', 'Th_ppm'),
    ('Y_ppm', 'Nd_ppm'), ('Y_ppm', 'Fe__'), ('Y_ppm', 'Ti__'),
    ('Y_ppm', 'Y_pond'), ('Ce_ppm', 'La_ppm'), ('Ce_ppm', 'Th_ppm'),
    ('La_ppm', 'Nd_ppm'),
]

corr_results = []
for x, y_col in pairs:
    mask = df[x].notna() & df[y_col].notna()
    xv = df.loc[mask, x].values
    yv = df.loc[mask, y_col].values
    if len(xv) > 30:
        r, p = stats.pearsonr(xv, yv)
        rs, ps = stats.spearmanr(xv, yv)
        corr_results.append({
            'Par': f"{x} vs {y_col}",
            'N': len(xv),
            'Pearson_r': round(r, 3),
            'Pearson_p': f"{p:.2e}",
            'Spearman_rs': round(rs, 3),
            'Interpretacion': 'Fuerte' if abs(r) > 0.7 else ('Moderada' if abs(r) > 0.4 else 'Débil')
        })
        print(f"  {x:10s} vs {y_col:10s}: r={r:.3f} (p={p:.2e}), rs={rs:.3f} | {corr_results[-1]['Interpretacion']}")

pd.DataFrame(corr_results).to_csv(os.path.join(OUTDIR, "geoquimica_correlaciones.csv"), index=False)

# ══════════════════════════════════════════════════════════════════
# 4. RATIOS GEOQUÍMICOS DIAGNÓSTICOS
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("4. RATIOS GEOQUÍMICOS DIAGNÓSTICOS")
print("=" * 70)

# Calcular ratios donde hay datos
mask_ree = df['Y_ppm'].notna() & df['Ce_ppm'].notna() & df['La_ppm'].notna()
df_ree = df[mask_ree].copy()

if len(df_ree) > 50:
    df_ree['Ce_Y'] = df_ree['Ce_ppm'] / df_ree['Y_ppm'].replace(0, np.nan)
    df_ree['La_Y'] = df_ree['La_ppm'] / df_ree['Y_ppm'].replace(0, np.nan)
    df_ree['LREE_Y'] = (df_ree['Ce_ppm'] + df_ree['La_ppm']) / df_ree['Y_ppm'].replace(0, np.nan)
    
    if df_ree['Th_ppm'].notna().sum() > 50:
        df_ree['Th_Y'] = df_ree['Th_ppm'] / df_ree['Y_ppm'].replace(0, np.nan)
    
    print(f"\n  Muestras con Ce+La+Y: {len(df_ree)}")
    
    for ratio in ['Ce_Y', 'La_Y', 'LREE_Y']:
        vals = df_ree[ratio].dropna()
        if len(vals) > 10:
            print(f"\n  {ratio:10s}: media={vals.mean():.2f}, med={vals.median():.2f}, "
                  f"std={vals.std():.2f}, P25={vals.quantile(0.25):.2f}, P75={vals.quantile(0.75):.2f}")
    
    # Ratios por litología
    print("\n  Ratios por litología (media Ce/Y):")
    for lit, grp in df_ree.groupby('Litology_STD'):
        r = grp['Ce_Y'].dropna()
        if len(r) >= 5:
            print(f"    {lit:35s}: Ce/Y={r.mean():.2f} (n={len(r)})")

# ══════════════════════════════════════════════════════════════════
# 5. ANÁLISIS ESPACIAL — ZONAS DE POTENCIAL
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("5. ANÁLISIS ESPACIAL — CLASIFICACIÓN DE POTENCIAL REE")
print("=" * 70)

# Dividir en cuadrantes espaciales
df_geo = df[df['Y_ppm'].notna() & df['lat'].notna() & df['lon'].notna()].copy()

lat_med = df_geo['lat'].median()
lon_med = df_geo['lon'].median()

# Grid 3x3
lat_bins = pd.qcut(df_geo['lat'], 3, labels=['Sur','Centro','Norte'])
lon_bins = pd.qcut(df_geo['lon'], 3, labels=['Oeste','Centro_lon','Este'])
df_geo['zona_lat'] = lat_bins
df_geo['zona_lon'] = lon_bins
df_geo['zona'] = df_geo['zona_lat'].astype(str) + '-' + df_geo['zona_lon'].astype(str)

zone_stats = []
for zona, grp in df_geo.groupby('zona'):
    yv = grp['Y_ppm']
    zone_stats.append({
        'Zona': zona,
        'N': len(yv),
        'Y_media': round(yv.mean(), 1),
        'Y_mediana': round(yv.median(), 1),
        'Y_P95': round(yv.quantile(0.95), 1),
        'Pct_anom_50': round((yv >= 50).mean() * 100, 1),
        'Lat_centro': round(grp['lat'].mean(), 4),
        'Lon_centro': round(grp['lon'].mean(), 4),
    })

zone_df = pd.DataFrame(zone_stats).sort_values('Y_media', ascending=False)
print(zone_df.to_string(index=False))
zone_df.to_csv(os.path.join(OUTDIR, "geoquimica_zonas.csv"), index=False)

# ══════════════════════════════════════════════════════════════════
# 6. ANÁLISIS DE ANOMALÍAS — HOTSPOTS
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("6. HOTSPOTS — MUESTRAS ANÓMALAS")
print("=" * 70)

# Umbral de anomalía: P75 + 1.5*IQR
p75_y = df_geo['Y_ppm'].quantile(0.75)
iqr_y = p75_y - df_geo['Y_ppm'].quantile(0.25)
umbral = p75_y + 1.5 * iqr_y

anomalies = df_geo[df_geo['Y_ppm'] >= umbral].copy()
print(f"\n  Umbral anomalía (Tukey): {umbral:.1f} ppm")
print(f"  Muestras anómalas: {len(anomalies)} de {len(df_geo)} ({len(anomalies)/len(df_geo)*100:.1f}%)")

if len(anomalies) > 0:
    print(f"\n  Top 20 por Y_ppm:")
    top20 = anomalies.nlargest(20, 'Y_ppm')[['Sample','Litology_STD','Y_ppm','Ce_ppm','La_ppm','lat','lon','FUENTE']]
    print(top20.to_string(index=False))

# ══════════════════════════════════════════════════════════════════
# 7. KRUSKAL-WALLIS — DIFERENCIA ESTADÍSTICA ENTRE LITOLOGÍAS
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("7. TEST KRUSKAL-WALLIS — DIFERENCIAS ENTRE LITOLOGÍAS")
print("=" * 70)

groups = []
group_names = []
for lit, grp in df.groupby('Litology_STD'):
    yv = grp['Y_ppm'].dropna()
    if len(yv) >= 10:
        groups.append(yv.values)
        group_names.append(lit)

if len(groups) >= 3:
    stat, p = stats.kruskal(*groups)
    print(f"\n  H-statistic = {stat:.2f}, p-value = {p:.2e}")
    print(f"  Conclusión: {'DIFERENCIA SIGNIFICATIVA' if p < 0.05 else 'Sin diferencia significativa'} entre litologías")
    print(f"  Litologías comparadas: {len(groups)}")

# ══════════════════════════════════════════════════════════════════
# 8. COMPARACIÓN Y_ppm vs Y_pond
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("8. COMPARACIÓN Y_ppm vs Y_pond")
print("=" * 70)

mask_yp = df['Y_ppm'].notna() & df['Y_pond'].notna()
df_yp = df[mask_yp].copy()
if len(df_yp) > 50:
    r, p = stats.pearsonr(df_yp['Y_ppm'], df_yp['Y_pond'])
    rmse = np.sqrt(((df_yp['Y_ppm'] - df_yp['Y_pond'])**2).mean())
    bias = (df_yp['Y_pond'] - df_yp['Y_ppm']).mean()
    print(f"  N muestras: {len(df_yp)}")
    print(f"  Correlación Pearson: r={r:.3f} (p={p:.2e})")
    print(f"  RMSE: {rmse:.1f} ppm")
    print(f"  Sesgo (Y_pond - Y_ppm): {bias:+.1f} ppm")
    print(f"  Y_ppm media: {df_yp['Y_ppm'].mean():.1f}, Y_pond media: {df_yp['Y_pond'].mean():.1f}")

# ══════════════════════════════════════════════════════════════════
# 9. RESUMEN EJECUTIVO
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("9. RESUMEN EJECUTIVO — POTENCIAL REE")
print("=" * 70)

best_lits = lit_df.head(5)
print("\n  LITOLOGÍAS CON MAYOR POTENCIAL:")
for _, r in best_lits.iterrows():
    print(f"    • {r['Litologia']:35s} Y_media={r['Y_media']:.1f}, {r['Pct_sobre_50']:.0f}% sobre 50ppm (n={r['N']})")

best_zones = zone_df.head(3)
print("\n  ZONAS CON MAYOR POTENCIAL:")
for _, r in best_zones.iterrows():
    print(f"    • {r['Zona']:20s} Y_media={r['Y_media']:.1f}, {r['Pct_anom_50']:.0f}% anomalías, centro=({r['Lat_centro']},{r['Lon_centro']})")

print("\n✅ Análisis completo guardado en itrio/geoquimica_*.csv")
