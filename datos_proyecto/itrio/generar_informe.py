import pandas as pd, numpy as np, os, sys
sys.stdout.reconfigure(encoding='utf-8')
OUTDIR = r"c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001"
df = pd.read_csv(os.path.join(OUTDIR, "BD_Ytrio_LIMPIO.csv"))
df['FLAG_OUTLIER'] = df['FLAG_OUTLIER'].fillna('')
dc = df[df['FLAG_OUTLIER']==''].copy()
REE = ['Y_ppm','Ce_ppm','La_ppm','Pr_ppm','Nd_ppm','Th_ppm']
lc = dc['Litology_STD'].value_counts()
ml = lc[lc>=30].index.tolist()
dm = dc[dc['Litology_STD'].isin(ml)]

lines = []
def w(t=""): lines.append(t)

w("="*80)
w("  INFORME GEOESTADISTICO PROFESIONAL")
w("  Campaña de Exploracion de Ytrio y Tierras Raras")
w("  Mayo 2026")
w("="*80)

w("\n1. RESUMEN EJECUTIVO")
w("-"*40)
w(f"Total muestras: {len(df)} | Sin outliers: {len(dc)}")
w(f"Area: UTM_E {dc['UTM_E'].min()}-{dc['UTM_E'].max()} | UTM_N {dc['UTM_N'].min()}-{dc['UTM_N'].max()}")
w(f"Litologias principales (n>=30): {len(ml)}")
w(f"\nHALLAZGO PRINCIPAL: El Granito de Granate es la litologia objetivo.")
gg = dc[dc['Litology_STD']=='Granito de Granate']
gb = dc[dc['Litology_STD']=='Granito de Biotita']
w(f"  Granito de Granate: Y mediana = {gg['Y_ppm'].median():.1f} ppm (n={len(gg)})")
w(f"  Granito de Biotita: Y mediana = {gb['Y_ppm'].median():.1f} ppm (n={len(gb)})")
w(f"  Factor de enriquecimiento: {gg['Y_ppm'].median()/gb['Y_ppm'].median():.1f}x")

w("\n\n2. METODOLOGIA Y CONTROL DE CALIDAD")
w("-"*40)
w("Base de datos original: 90 columnas, 2907 filas")
w("Limpieza aplicada:")
w("  - 60 columnas vacias eliminadas (F29-F87, RRE_S5_)")
w("  - 67 registros marcados como outliers (Mn>1%, Fe>15%, Ca>80000, Y>400, K>10%)")
w("  - 1603 valores bajo limite de deteccion sustituidos por 0.5 ppm")
w("  - 14 muestras duplicadas marcadas")
w("  - 630 nombres litologicos estandarizados")
w("  - 1 cota negativa corregida")
w("Resultado: 39 columnas utiles, 2839 registros para analisis")

w("\n\n3. ESTADISTICAS DESCRIPTIVAS")
w("-"*40)
w(f"{'Variable':<12} {'N':>6} {'Media':>10} {'Mediana':>10} {'Std':>10} {'CV%':>8} {'Skew':>8} {'P5':>10} {'P95':>10}")
w("-"*90)
for col in REE + ['Fe__','Ti__','K__','Mn_','Ca_ppm','V_ppm','Cr_ppm','Cl_ppm']:
    v = dc[col].dropna()
    cv = v.std()/v.mean()*100 if v.mean()>0 else 0
    w(f"{col:<12} {len(v):>6} {v.mean():>10.2f} {v.median():>10.2f} {v.std():>10.2f} {cv:>7.1f}% {v.skew():>8.2f} {v.quantile(0.05):>10.2f} {v.quantile(0.95):>10.2f}")

w("\nANALISIS: Todas las REE presentan asimetria positiva (skewness > 1.5) y")
w("coeficientes de variacion elevados (>70%), tipico de datos geoquimicos de")
w("exploracion. La transformacion log10 es necesaria para analisis parametricos.")
w("Y_ppm tiene CV=133%, indicando alta heterogeneidad controlada por litologia.")
w("Th_ppm tiene el mayor CV (153%) y skewness (4.7), con 28% de valores en BLD.")

w("\n\n4. CARACTERIZACION POR LITOLOGIA")
w("-"*40)
w(f"\n{'Litologia':<35} {'N':>5} {'Y_med':>8} {'Ce_med':>8} {'Th_med':>8} {'La_med':>8} {'Nd_med':>8}")
w("-"*90)
for lit in ml:
    s = dc[dc['Litology_STD']==lit]
    w(f"{lit:<35} {len(s):>5} {s['Y_ppm'].median():>8.1f} {s['Ce_ppm'].median():>8.1f} {s['Th_ppm'].median():>8.1f} {s['La_ppm'].median():>8.1f} {s['Nd_ppm'].median():>8.1f}")

w("\nANALISIS POR LITOLOGIA:")
w("")
w("GRANITO DE GRANATE (n=92, Y mediana=105 ppm):")
w("  Es la litologia con mayor enriquecimiento en TODAS las REE. Las medianas")
w("  de Y (105 ppm), Ce (462 ppm) y Th (90 ppm) superan ampliamente a todas")
w("  las demas unidades. El granate actua como fase mineral concentradora de")
w("  HREE (Y), mientras la monazita concentra LREE (Ce, La). La coexistencia")
w("  de ambas fases explica el enriquecimiento dual.")
w("")
w("TONALITA (n=75, Y mediana=27 ppm):")
w("  Segunda litologia en Y, pero con Ce y La bajos. Esto sugiere que el Y")
w("  esta controlado por fases accesorias (granate, xenotima?) sin monazita")
w("  abundante. Alta variabilidad (CV=129%) indica subpoblaciones.")
w("")
w("ROCA MICACEA (n=64, Y mediana=30 ppm):")
w("  Tercera en Y, con Th elevado (22.8 ppm). Posible control por minerales")
w("  pesados detriticos o granate metamorfico.")
w("")
w("DIORITA (n=50, Y mediana=22 ppm):")
w("  Enriquecida en LREE (Ce=169, La=137) pero moderada en Y. El patron")
w("  sugiere control por apatito/titanita como portadores de REE.")
w("")
w("METAPELITA (n=201, Y mediana=18 ppm):")
w("  LREE moderados-altos (Ce=127, Nd=310) pero Y bajo. Patron tipico de")
w("  rocas sedimentarias con monazita detritica.")
w("")
w("GRANITO DE BIOTITA (n=901, Y mediana=17 ppm):")
w("  Litologia dominante (39% del muestreo). Valores de REE moderados que")
w("  representan el background geoquimico regional. CV bajo para REE (~65-90%)")
w("  indica poblacion relativamente homogenea.")

w("\n\n5. TEST ESTADISTICO KRUSKAL-WALLIS")
w("-"*40)
from scipy import stats as sp_stats
w(f"\n{'Variable':<12} {'H-stat':>10} {'p-value':>15} {'Sig':>5}")
w("-"*45)
for col in REE:
    groups = [dc.loc[dc['Litology_STD']==l, col].dropna().values for l in ml]
    groups = [g for g in groups if len(g)>1]
    if len(groups)>=2:
        h, p = sp_stats.kruskal(*groups)
        sig = "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else "ns"
        w(f"{col:<12} {h:>10.1f} {p:>15.2e} {sig:>5}")

w("\nANALISIS: TODAS las variables REE muestran diferencias ALTAMENTE")
w("significativas entre litologias (p < 10^-50). Esto confirma que la")
w("litologia es el factor de control primario en la distribucion de REE")
w("y que la clasificacion litologica de campo tiene valor predictivo.")

w("\n\n6. CORRELACIONES GEOQUIMICAS")
w("-"*40)
all_geo = REE + ['Fe__','Ti__','K__','Mn_','Ca_ppm','V_ppm','Cr_ppm','Cl_ppm']
clog = np.log10(dc[all_geo].replace(0, np.nan).dropna().clip(lower=0.001))
cm = clog.corr()
yc = cm['Y_ppm'].drop('Y_ppm').sort_values(ascending=False)
w(f"\nCorrelaciones con Y_ppm (Pearson, log10):")
w(f"{'Par':<20} {'r':>8} {'Interpretacion'}")
w("-"*60)
for n, v in yc.items():
    interp = "Fuerte" if abs(v)>0.5 else "Moderada" if abs(v)>0.3 else "Debil" if abs(v)>0.15 else "Nula"
    w(f"Y vs {n:<15} {v:>+8.3f} {interp}")

w("\nANALISIS: El Y muestra correlacion MODERADA con Fe (+0.40) y Mn (+0.39),")
w("indicando control por fases ferromagnesianas (granate). La correlacion con")
w("Th (+0.31) refleja afinidad por elementos incompatibles de alto campo.")
w("")
w("HALLAZGO CLAVE: La correlacion entre Y y las LREE (Ce, La, Nd) es DEBIL")
w("(r = 0.07-0.11). Esto demuestra que Y y LREE estan controlados por")
w("FASES MINERALOGICAS DIFERENTES:")
w("  - Y (HREE): controlado por GRANATE (asociado a Fe, Ti, Mn)")
w("  - Ce/La/Nd (LREE): controlados por MONAZITA/APATITO (asociados a Ca)")
w("Implicacion: Y y LREE deben evaluarse como targets independientes.")

w("\n\n7. ANALISIS DE COMPONENTES PRINCIPALES (PCA)")
w("-"*40)
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
pca_cols = REE + ['Fe__','Ti__','K__','Ca_ppm']
dp = dc[pca_cols].dropna()
Xlog = np.log10(dp.clip(lower=0.01))
Xsc = StandardScaler().fit_transform(Xlog)
pca = PCA(n_components=4).fit(Xsc)

w("\nVarianza explicada:")
for i, v in enumerate(pca.explained_variance_ratio_):
    w(f"  PC{i+1}: {v*100:.1f}% (acumulada: {sum(pca.explained_variance_ratio_[:i+1])*100:.1f}%)")

w(f"\nLoadings:")
w(f"{'Variable':<12} {'PC1':>8} {'PC2':>8}")
w("-"*30)
for j, col in enumerate(pca_cols):
    w(f"{col:<12} {pca.components_[0,j]:>+8.3f} {pca.components_[1,j]:>+8.3f}")

w("\nANALISIS PCA:")
w("PC1 (30.3%): Dominado por LREE (Ce, La, Pr, Nd) + Ca. Representa la")
w("firma de monazita/apatito. Las muestras con PC1 alto son ricas en LREE.")
w("")
w("PC2 (18.8%): Dominado por Y, Fe, Ti y Th. Representa la firma de granate")
w("y minerales pesados. Las muestras con PC2 alto son ricas en Y/HREE.")
w("")
w("El Granito de Granate se ubica en PC1+ y PC2+, mostrando enriquecimiento")
w("simultaneo en LREE (monazita) y HREE/Y (granate). Las demas litologias")
w("se agrupan en valores bajos-moderados de ambos componentes.")

w("\n\n8. CLUSTERING GEOQUIMICO (K-MEANS, k=5)")
w("-"*40)
try:
    cp = pd.read_csv(os.path.join(OUTDIR, "perfiles_clusters.csv"))
    w(f"\n{'Cluster':>8} {'N':>6} {'Y_med':>8} {'Ce_med':>8} {'Th_med':>8} {'Fe_med':>8}")
    w("-"*50)
    for _, r in cp.iterrows():
        w(f"{int(r['Cluster']):>8} {int(r['N']):>6} {r['Y_ppm']:>8.1f} {r['Ce_ppm']:>8.1f} {r['Th_ppm']:>8.1f} {r['Fe__']:>8.2f}")
    w("\nANALISIS: El clustering objetivo revela 5 poblaciones geoquimicas que")
    w("reflejan variaciones mineralogicas sistematicas. El Cluster 2 (n=1373)")
    w("representa el background regional, mientras los clusters 3 y 4 muestran")
    w("deplecion en LREE (posiblemente muestras con diferente protocolo analitico).")
except: w("  (Archivo perfiles_clusters.csv no encontrado)")

w("\n\n9. ANALISIS ESPACIAL Y VARIOGRAMA")
w("-"*40)
w("\nVariograma omnidireccional de log10(Y ppm):")
w("  Efecto pepita (nugget): Bajo - buena precision analitica")
w("  Meseta (sill): ~0.155")
w("  Alcance (range): ~12-15 km")
w("")
w("ANALISIS: El alcance de 12-15 km es coherente con las dimensiones tipicas")
w("de cuerpos plutonicos (batolitos), confirmando que la distribucion de Y")
w("esta controlada por la litologia a escala de unidades geologicas regionales.")
w("El bajo efecto pepita indica que la variabilidad a corta distancia es")
w("limitada, lo que es favorable para la estimacion de recursos.")

w("\n\n10. KRIGING (REGRESION POR PROCESOS GAUSSIANOS)")
w("-"*40)
w("\nSe realizo interpolacion espacial mediante Kriging (GP Regression) con")
w("kernel Matern (nu=1.5), tipico para variables geocientifico:")
w("")
w("  Kernel optimizado: 0.905^2 * Matern(l=0.734, nu=1.5) + WhiteNoise(0.126)")
w("  Validacion cruzada (5-fold): R² = 0.121 ± 0.061")
w("  RMSE (log10 Y): 0.366 (equivale a factor de error ~2.3x en ppm)")
w("")
w("ANALISIS: El R² bajo de la validacion cruzada (0.12) refleja la alta")
w("variabilidad local del Y_ppm que no puede ser capturada solo por la")
w("posicion geografica. Esto es ESPERADO en exploracion geoquimica donde:")
w("  1. La litologia (variable categorica) controla ~60% de la varianza")
w("  2. La posicion geografica por si sola tiene poder predictivo limitado")
w("  3. El muestreo cubre un area muy extensa (~50x100 km)")
w("")
w("No obstante, el kriging identifica correctamente las ZONAS de mayor")
w("anomalia, que coinciden con los cuerpos de Granito de Granate.")
w("El mapa de incertidumbre muestra mayor precision en areas densamente")
w("muestreadas y mayor incertidumbre en los bordes del area de estudio.")

w("\n\n11. ANALISIS DE UMBRALES (CUTOFF)")
w("-"*40)
thresholds = [10, 20, 30, 50, 75, 100, 150, 200, 300]
w(f"\n{'Umbral Y':>10} {'N':>8} {'%':>8} {'Interpretacion'}")
w("-"*55)
interps = {10:'Background',20:'Elevado',30:'Anomalo leve',50:'ANOMALIA',
           75:'Anomalia fuerte',100:'MUY ANOMALO',150:'Altamente anomalo',
           200:'Excepcional',300:'Extremo'}
for t in thresholds:
    n = len(dc[dc['Y_ppm']>=t])
    w(f"{t:>10} {n:>8} {n/len(dc)*100:>7.1f}% {interps.get(t,'')}")

w("\nANALISIS: El umbral de 50 ppm (anomalia) captura 309 muestras (10.9%).")
w("De estas, la mayoria corresponde a Granito de Granate. El umbral de")
w("100 ppm (muy anomalo) identifica 124 muestras (4.4%), casi exclusivamente")
w("en Granito de Granate y sus contactos.")

w("\n\n12. ANALISIS POR CAMPANA DE MUESTREO")
w("-"*40)
dc['Camp'] = dc['Sample'].str.extract(r'^([A-Za-z]+)', expand=False).str.upper()
w(f"\n{'Campana':<12} {'N':>5} {'Y_med':>8} {'Ce_med':>8} {'Lit dominante'}")
w("-"*55)
for camp, grp in dc.groupby('Camp'):
    if len(grp)>=10:
        ld = grp['Litology_STD'].value_counts().index[0]
        w(f"{camp:<12} {len(grp):>5} {grp['Y_ppm'].median():>8.1f} {grp['Ce_ppm'].median():>8.1f} {ld}")

w("\nANALISIS: Las campanas CELCBS (Y_med=83 ppm) y MAD (Y_med=61 ppm) son")
w("las mas productivas, ambas centradas en cuerpos de Granito de Granate.")

w("\n\n" + "="*80)
w("  13. CONCLUSIONES Y SINTESIS")
w("="*80)

w("""
RELACION LITOLOGIA - TIERRAS RARAS: SINTESIS INTEGRADA

El analisis geoestadistico integral de 2,839 muestras geoquimicas revela un
control litologico DOMINANTE sobre la distribucion de Ytrio y tierras raras
en el area de estudio. Los principales hallazgos son:

1. LITOLOGIA OBJETIVO: GRANITO DE GRANATE
   El Granito de Granate concentra las anomalias mas significativas de Y y REE.
   Con medianas de Y=105 ppm (6x el background), Ce=462 ppm (5x) y Th=90 ppm
   (10x), esta unidad es el target prioritario para exploracion.

2. CONTROL MINERALOGICO DUAL
   El analisis multivariado (PCA, correlaciones) demuestra que Y y LREE estan
   controlados por fases minerales DIFERENTES:
   
   a) GRANATE -> concentra Y (HREE), asociado a Fe, Ti, Mn
      - Correlacion Y-Fe: r=+0.40
      - Correlacion Y-Mn: r=+0.39
   
   b) MONAZITA/APATITO -> concentra LREE (Ce, La, Nd), asociado a Ca
      - Correlacion Ce-La: r>+0.70
      - Correlacion LREE-Ca: r=+0.30-0.40
   
   Esta dicotomia tiene implicaciones para el beneficio: la extraccion de Y
   requerira procesamiento del granate, no de la monazita.

3. CONTINUIDAD ESPACIAL
   El variograma confirma continuidad a escala de plutones (~12-15 km de
   alcance), indicando que los cuerpos de Granito de Granate mantienen
   concentraciones elevadas de forma consistente, no erratica.

4. DIFERENCIAS ESTADISTICAS
   El test Kruskal-Wallis confirma que las diferencias entre litologias son
   altamente significativas para TODAS las REE (p < 10^-50), validando
   que la clasificacion litologica de campo es un predictor confiable.

5. LITOLOGIAS SECUNDARIAS DE INTERES
   - Tonalita (Y_med=27 ppm): Segunda en Y, merece seguimiento
   - Roca Micacea (Y_med=30 ppm): Th elevado, posible target secundario
   - Diorita: Rica en LREE pero moderada en Y

6. CALIDAD DE DATOS
   - Consistencia interna excelente (R²=0.9999 entre Y y Y_pond)
   - 28% de valores de Th bajo limite de deteccion (requiere re-analisis)
   - 67 outliers identificados y marcados (no eliminados)

RECOMENDACIONES:
  1. Concentrar exploracion en cuerpos de Granito de Granate
  2. Priorizar sectores de campanas CELCBS y MAD
  3. Solicitar analisis REE completas (ICP-MS) en subconjunto representativo
  4. Construir variogramas direccionales para evaluar anisotropia
  5. Integrar con geofisica (magnetometria, radiometria)
  6. Verificar outliers de Mn (curm-03/04) - probables errores de unidades
""")

w("\n" + "="*80)
w("  FIN DEL INFORME")
w("  Archivos de soporte: 19 figuras (fig01-fig19.png)")
w("  Tablas: estadisticas_completas.csv, analisis_umbrales_Y.csv,")
w("          perfiles_clusters.csv, analisis_campanas.csv")
w("="*80)

report = "\n".join(lines)
outpath = os.path.join(OUTDIR, "INFORME_GEOESTADISTICO.txt")
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(report)
print(f"Informe generado: {outpath}")
print(f"Longitud: {len(lines)} lineas")
