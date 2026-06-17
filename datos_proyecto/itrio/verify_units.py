#!/usr/bin/env python3
import pandas as pd, numpy as np, sys
from scipy import stats
sys.stdout.reconfigure(encoding='utf-8')

df1 = pd.read_csv(r'c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001\BD_Ytrio_LIMPIO.csv')

# === Mn_ anomalies ===
mn = df1['Mn_'].dropna()
print("=== Mn_ (%) en Pob1 ===")
print(f"N total: {len(mn)}")
print(f"Valores > 1%: {(mn>1).sum()} ({(mn>1).sum()/len(mn)*100:.1f}%)")
print(f"Valores = 0: {(mn==0).sum()} ({(mn==0).sum()/len(mn)*100:.1f}%)")

both = df1[['Mn_', 'Mn']].dropna()
zeros = both[both['Mn_'] == 0]
print(f"Filas con Mn_=0: {len(zeros)}")
if len(zeros) > 0:
    print(f"  Mn(ppm) cuando Mn_=0: min={zeros['Mn'].min()}, max={zeros['Mn'].max()}, med={zeros['Mn'].median()}")

mn_clean = mn[(mn > 0) & (mn < 1)]
print(f"Mn_ sin outliers (0 < x < 1%): n={len(mn_clean)}, mediana={mn_clean.median():.4f}, media={mn_clean.mean():.4f}")

# === V_ppm ===
print("\n=== V_ppm en Pob1 ===")
v = df1['V_ppm'].dropna()
print(f"mediana={v.median():.1f}, P5={v.quantile(0.05):.1f}, P95={v.quantile(0.95):.1f}")
print(f"Si Pob2 V(raw)=0.023% -> 230 ppm -> percentil {stats.percentileofscore(v.values, 230):.1f}% en Pob1")

# === Ca_ppm ===
print("\n=== Ca_ppm en Pob1 ===")
ca = df1['Ca_ppm'].dropna()
print(f"mediana={ca.median():.0f}, P5={ca.quantile(0.05):.0f}, P95={ca.quantile(0.95):.0f}")
print(f"Si Pob2 Ca(raw)=0.24% -> 2434 ppm -> percentil {stats.percentileofscore(ca.values, 2434):.1f}% en Pob1")

# === Verificar TODAS las conversiones con valores corregidos ===
print("\n=== POSICIÓN PERCENTIL CORREGIDA (Pob2 con unidades correctas) ===")
# Valores medianos de Pob2 CORREGIDOS
corrected = {
    'K__ (%)':    (1.31, 'K__'),      # ya OK, ambas en %
    'Ca_ppm':     (0.24 * 10000, 'Ca_ppm'),  # % -> ppm
    'Ti__ (%)':   (0.50, 'Ti__'),      # ya OK, ambas en %
    'V_ppm':      (0.023 * 10000, 'V_ppm'),  # % -> ppm
    'Cr_ppm':     (0.015 * 10000, 'Cr_ppm'), # % -> ppm
    'Mn_ (%)':    (0.058, 'Mn_'),      # ya OK, ambas en %
    'Fe__ (%)':   (3.62, 'Fe__'),      # ya OK, ambas en %
    'Y_ppm':      (29.0, 'Y_ppm'),     # ya OK, ambas en ppm
}

print(f"\n{'Variable':>15s}  {'Pob2 corregido':>15s}  {'Pob1 mediana':>15s}  {'Percentil':>10s}  {'Estado':>10s}")
print("-" * 75)
for name, (val2, col1) in corrected.items():
    v1 = pd.to_numeric(df1[col1], errors='coerce').dropna()
    pct = stats.percentileofscore(v1.values, val2)
    estado = "OK" if 10 < pct < 90 else "EXTREMO" if (pct < 5 or pct > 95) else "MARGINAL"
    print(f"{name:>15s}  {val2:>15.1f}  {v1.median():>15.1f}  {pct:>9.1f}%  {estado:>10s}")
