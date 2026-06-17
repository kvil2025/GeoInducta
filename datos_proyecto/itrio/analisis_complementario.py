# ============================================================
# Analisis Complementario Profundo - BD_Ytrio
# ============================================================
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import warnings, os, sys

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

OUTDIR = r"c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001"
df = pd.read_csv(os.path.join(OUTDIR, "BD_Ytrio_LIMPIO.csv"))
df['FLAG_OUTLIER'] = df['FLAG_OUTLIER'].fillna('')
df_clean = df[df['FLAG_OUTLIER'] == ''].copy()

REE = ['Y_ppm','Ce_ppm','La_ppm','Pr_ppm','Nd_ppm','Th_ppm']
MAJORS = ['Fe__','Ti__','K__','Mn_','Ca_ppm']
lit_counts = df_clean['Litology_STD'].value_counts()
main_lits = lit_counts[lit_counts >= 30].index.tolist()
df_main = df_clean[df_clean['Litology_STD'].isin(main_lits)].copy()

palette = sns.color_palette("husl", len(main_lits))
lit_colors = dict(zip(main_lits, palette))

# ============================================================
# 1. Estadisticas descriptivas COMPLETAS
# ============================================================
print("=== 1. ESTADISTICAS DESCRIPTIVAS COMPLETAS ===")
all_cols = REE + MAJORS + ['V_ppm','Cr_ppm','Cl_ppm']
full_stats = []
for col in all_cols:
    v = df_clean[col].dropna()
    vlog = np.log10(v[v > 0])
    row = {
        'Variable': col, 'N': len(v), 'Min': round(v.min(),3), 'Max': round(v.max(),3),
        'Media': round(v.mean(),3), 'Mediana': round(v.median(),3),
        'Std': round(v.std(),3), 'CV%': round(v.std()/v.mean()*100,1) if v.mean()>0 else 0,
        'Skewness': round(v.skew(),3), 'Kurtosis': round(v.kurtosis(),3),
        'P5': round(v.quantile(0.05),3), 'P25': round(v.quantile(0.25),3),
        'P75': round(v.quantile(0.75),3), 'P95': round(v.quantile(0.95),3),
        'Log_Media': round(vlog.mean(),3) if len(vlog)>0 else None,
        'Log_Std': round(vlog.std(),3) if len(vlog)>0 else None,
    }
    full_stats.append(row)
    print(f"  {col}: media={row['Media']}, med={row['Mediana']}, CV={row['CV%']}%, skew={row['Skewness']}")

pd.DataFrame(full_stats).to_csv(os.path.join(OUTDIR, "estadisticas_completas.csv"), index=False)

# ============================================================
# 2. Q-Q Plots (log-normalidad)
# ============================================================
print("\n=== 2. Q-Q PLOTS ===")
fig, axes = plt.subplots(2, 3, figsize=(18, 11))
fig.suptitle('Q-Q Plots (Log-Normalidad) — Tierras Raras', fontsize=16, fontweight='bold')
for idx, col in enumerate(REE):
    ax = axes[idx//3, idx%3]
    v = df_clean[col].dropna()
    vlog = np.log10(v[v > 0])
    stats.probplot(vlog, dist="norm", plot=ax)
    ax.set_title(f'{col} (log10)', fontsize=12, fontweight='bold')
    _, p_sw = stats.shapiro(vlog.sample(min(2000, len(vlog)), random_state=42))
    _, p_ks = stats.kstest(vlog, 'norm', args=(vlog.mean(), vlog.std()))
    ax.text(0.05, 0.85, f'Shapiro p={p_sw:.4f}\nK-S p={p_ks:.4f}', transform=ax.transAxes,
            fontsize=9, bbox=dict(boxstyle='round', facecolor='lightyellow'))
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig10_QQ_plots.png"), dpi=150, bbox_inches='tight')
plt.close()
print("  Guardado: fig10_QQ_plots.png")

# ============================================================
# 3. Curvas de frecuencia acumulada (CDF) de Y
# ============================================================
print("\n=== 3. CDF Y_ppm POR LITOLOGIA ===")
fig, ax = plt.subplots(figsize=(12, 7))
for lit in main_lits[:10]:
    v = df_clean.loc[df_clean['Litology_STD']==lit, 'Y_ppm'].dropna().sort_values()
    cdf = np.arange(1, len(v)+1) / len(v) * 100
    ax.plot(v, cdf, label=f'{lit} (n={len(v)})', linewidth=1.8, color=lit_colors[lit])

ax.set_xlabel('Y (ppm)', fontsize=12)
ax.set_ylabel('Frecuencia Acumulada (%)', fontsize=12)
ax.set_title('Curvas de Probabilidad Acumulada — Y (ppm) por Litología', fontsize=14, fontweight='bold')
ax.set_xscale('log')
ax.legend(fontsize=7, loc='lower right')
ax.grid(True, alpha=0.3)
ax.axhline(50, color='gray', ls=':', lw=1)
ax.axhline(90, color='gray', ls=':', lw=1)
for thresh in [20, 50, 100]:
    ax.axvline(thresh, color='red', ls='--', lw=0.8, alpha=0.5)
    ax.text(thresh, 2, f'{thresh}', fontsize=8, color='red', ha='center')
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig11_CDF_Y.png"), dpi=150, bbox_inches='tight')
plt.close()
print("  Guardado: fig11_CDF_Y.png")

# ============================================================
# 4. Analisis de umbrales (cutoff) Y_ppm
# ============================================================
print("\n=== 4. ANALISIS DE UMBRALES Y_ppm ===")
thresholds = [10, 20, 30, 50, 75, 100, 150, 200, 300]
thresh_data = []
for t in thresholds:
    above = df_clean[df_clean['Y_ppm'] >= t]
    row = {'Umbral_Y_ppm': t, 'N_muestras': len(above),
           'Pct_total': round(len(above)/len(df_clean)*100,1)}
    for lit in main_lits[:8]:
        n_lit = len(above[above['Litology_STD']==lit])
        row[lit] = n_lit
    thresh_data.append(row)
    print(f"  Y >= {t} ppm: {len(above)} muestras ({row['Pct_total']}%)")

pd.DataFrame(thresh_data).to_csv(os.path.join(OUTDIR, "analisis_umbrales_Y.csv"), index=False)

# ============================================================
# 5. K-Means Clustering geoquimico
# ============================================================
print("\n=== 5. CLUSTERING K-MEANS ===")
clust_cols = REE + ['Fe__','Ti__','K__','Ca_ppm']
df_clust = df_clean[clust_cols + ['Litology_STD','UTM_E','UTM_N','Sample']].dropna().copy()
X = df_clust[clust_cols].values
X_log = np.log10(np.where(X > 0, X, 0.01))
scaler = StandardScaler()
X_sc = scaler.fit_transform(X_log)

# Elbow
inertias = []
K_range = range(2, 10)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_sc)
    inertias.append(km.inertia_)

# Usar k=5
km5 = KMeans(n_clusters=5, random_state=42, n_init=10)
df_clust['Cluster'] = km5.fit_predict(X_sc)

# PCA para visualizar
pca = PCA(n_components=2)
pcs = pca.fit_transform(X_sc)

fig, axes = plt.subplots(1, 3, figsize=(21, 6))

ax = axes[0]
ax.plot(list(K_range), inertias, 'bo-', linewidth=2)
ax.axvline(5, color='red', ls='--', label='k=5')
ax.set_xlabel('Número de Clusters (k)')
ax.set_ylabel('Inercia')
ax.set_title('Método del Codo', fontsize=13, fontweight='bold')
ax.legend()
ax.grid(alpha=0.3)

ax = axes[1]
for c in range(5):
    mask = df_clust['Cluster'] == c
    ax.scatter(pcs[mask, 0], pcs[mask, 1], s=8, alpha=0.5, label=f'Cluster {c+1}')
ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')
ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')
ax.set_title('Clusters en Espacio PCA', fontsize=13, fontweight='bold')
ax.legend(fontsize=8)
ax.grid(alpha=0.2)

ax = axes[2]
for c in range(5):
    sub = df_clust[df_clust['Cluster'] == c]
    ax.scatter(sub['UTM_E'], sub['UTM_N'], s=5, alpha=0.4, label=f'Cluster {c+1} (n={len(sub)})')
ax.set_xlabel('UTM E')
ax.set_ylabel('UTM N')
ax.set_title('Clusters en Espacio Geográfico', fontsize=13, fontweight='bold')
ax.legend(fontsize=7, markerscale=3)
ax.set_aspect('equal')
ax.grid(alpha=0.2)

plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig12_clustering.png"), dpi=150, bbox_inches='tight')
plt.close()
print("  Guardado: fig12_clustering.png")

# Perfil de cada cluster
print("\n  Perfiles de clusters (medianas):")
cluster_profiles = []
for c in range(5):
    sub = df_clust[df_clust['Cluster'] == c]
    profile = {'Cluster': c+1, 'N': len(sub)}
    for col in clust_cols:
        profile[col] = round(sub[col].median(), 2)
    # Litologia dominante
    lit_dom = sub['Litology_STD'].value_counts().head(3)
    profile['Litologias_top'] = "; ".join([f"{l}({n})" for l, n in lit_dom.items()])
    cluster_profiles.append(profile)
    print(f"  Cluster {c+1} (n={len(sub)}): Y_med={profile['Y_ppm']}, Ce_med={profile['Ce_ppm']}, "
          f"Th_med={profile['Th_ppm']}, Fe_med={profile['Fe__']}")
    print(f"    Lits: {profile['Litologias_top']}")

pd.DataFrame(cluster_profiles).to_csv(os.path.join(OUTDIR, "perfiles_clusters.csv"), index=False)

# ============================================================
# 6. Variograma omnidireccional de Y_ppm
# ============================================================
print("\n=== 6. VARIOGRAMA EXPERIMENTAL Y_ppm ===")
coords = df_clean[['UTM_E','UTM_N','Y_ppm']].dropna()
# Submuestrear para velocidad
if len(coords) > 1500:
    coords = coords.sample(1500, random_state=42)

y_vals = np.log10(coords['Y_ppm'].values.clip(min=0.1))
xy = coords[['UTM_E','UTM_N']].values

# Calcular variograma experimental
dists = pdist(xy)
dist_matrix = squareform(dists)
n = len(y_vals)

max_dist = np.percentile(dists, 50)
n_lags = 20
lag_width = max_dist / n_lags

lags, gammas, counts = [], [], []
for lag_i in range(n_lags):
    d_min = lag_i * lag_width
    d_max = (lag_i + 1) * lag_width
    pairs = []
    for i in range(n):
        for j in range(i+1, n):
            if d_min <= dist_matrix[i, j] < d_max:
                pairs.append((y_vals[i] - y_vals[j])**2)
            if len(pairs) > 5000:
                break
        if len(pairs) > 5000:
            break
    if len(pairs) > 10:
        lags.append((d_min + d_max) / 2)
        gammas.append(np.mean(pairs) / 2)
        counts.append(len(pairs))

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(np.array(lags)/1000, gammas, 'ko-', markersize=6, linewidth=1.5)
for i, c in enumerate(counts):
    ax.annotate(str(c), (lags[i]/1000, gammas[i]), fontsize=7, color='blue',
                textcoords="offset points", xytext=(0, 8), ha='center')
ax.set_xlabel('Distancia (km)', fontsize=12)
ax.set_ylabel('γ(h) — Semivarianza', fontsize=12)
ax.set_title('Variograma Experimental Omnidireccional — log10(Y ppm)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
sill = np.var(y_vals)
ax.axhline(sill, color='red', ls='--', lw=1.5, label=f'Varianza total = {sill:.3f}')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig13_variograma.png"), dpi=150, bbox_inches='tight')
plt.close()
print(f"  Guardado: fig13_variograma.png")
print(f"  Varianza total (sill): {sill:.4f}")
print(f"  Lag width: {lag_width:.0f} m")

# ============================================================
# 7. Heatmap Y por sector geografico
# ============================================================
print("\n=== 7. HEATMAP GEOGRAFICO Y_ppm ===")
fig, axes = plt.subplots(1, 3, figsize=(21, 7))

for idx, (col, title, cmap) in enumerate([
    ('Y_ppm', 'Y (ppm)', 'hot_r'),
    ('Ce_ppm', 'Ce (ppm)', 'YlOrRd'),
    ('Th_ppm', 'Th (ppm)', 'PuRd')
]):
    ax = axes[idx]
    vals = df_clean[col].clip(lower=0.1)
    sc = ax.scatter(df_clean['UTM_E'], df_clean['UTM_N'],
                    c=np.log10(vals), s=4, cmap=cmap, alpha=0.7)
    plt.colorbar(sc, ax=ax, label=f'log10({col})', shrink=0.8)
    ax.set_xlabel('UTM E')
    ax.set_ylabel('UTM N')
    ax.set_title(f'Mapa Geoquímico — {title}', fontsize=13, fontweight='bold')
    ax.set_aspect('equal')

plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig14_mapas_REE.png"), dpi=150, bbox_inches='tight')
plt.close()
print("  Guardado: fig14_mapas_REE.png")

# ============================================================
# 8. Pair plot REE
# ============================================================
print("\n=== 8. PAIR PLOT REE ===")
df_pair = df_main[REE + ['Litology_STD']].dropna()
df_pair_log = df_pair.copy()
for c in REE:
    df_pair_log[c] = np.log10(df_pair_log[c].clip(lower=0.1))

# Solo top 6 litologias para legibilidad
top6 = lit_counts.head(6).index.tolist()
df_pp = df_pair_log[df_pair_log['Litology_STD'].isin(top6)]

g = sns.pairplot(df_pp, hue='Litology_STD', vars=REE,
                 plot_kws={'s': 5, 'alpha': 0.3}, diag_kws={'alpha': 0.5},
                 height=2.2, palette='husl')
g.figure.suptitle('Pair Plot REE (log10) — Top 6 Litologías', y=1.01, fontsize=15, fontweight='bold')
g.savefig(os.path.join(OUTDIR, "fig15_pairplot_REE.png"), dpi=120, bbox_inches='tight')
plt.close()
print("  Guardado: fig15_pairplot_REE.png")

# ============================================================
# 9. Analisis por campana (prefijo de muestra)
# ============================================================
print("\n=== 9. ANALISIS POR CAMPAÑA ===")
df_clean['Campana'] = df_clean['Sample'].str.extract(r'^([A-Za-z]+)', expand=False).str.upper()
camp_stats = []
for camp, grp in df_clean.groupby('Campana'):
    if len(grp) >= 10:
        camp_stats.append({
            'Campana': camp, 'N': len(grp),
            'Y_med': round(grp['Y_ppm'].median(), 1),
            'Y_mean': round(grp['Y_ppm'].mean(), 1),
            'Ce_med': round(grp['Ce_ppm'].median(), 1),
            'Th_med': round(grp['Th_ppm'].median(), 1),
            'Lit_dom': grp['Litology_STD'].value_counts().index[0],
            'UTM_E_mean': int(grp['UTM_E'].mean()),
            'UTM_N_mean': int(grp['UTM_N'].mean()),
        })

camp_df = pd.DataFrame(camp_stats).sort_values('Y_med', ascending=False)
camp_df.to_csv(os.path.join(OUTDIR, "analisis_campanas.csv"), index=False)
print("  Top 10 campañas por Y_ppm mediana:")
for _, r in camp_df.head(10).iterrows():
    print(f"    {r['Campana']} (n={r['N']}): Y_med={r['Y_med']}, Ce_med={r['Ce_med']}, Lit={r['Lit_dom']}")

# ============================================================
# 10. Scatter Y vs Y_pond con R2
# ============================================================
print("\n=== 10. Y_ppm vs Y_pond ===")
fig, ax = plt.subplots(figsize=(8, 8))
ax.scatter(df_clean['Y_ppm'], df_clean['Y_pond'], s=3, alpha=0.3, color='steelblue')
slope, intercept, r, p, se = stats.linregress(df_clean['Y_ppm'].dropna(), df_clean['Y_pond'].dropna())
x_line = np.linspace(0, df_clean['Y_ppm'].max(), 100)
ax.plot(x_line, slope*x_line + intercept, 'r-', lw=2, label=f'y={slope:.3f}x+{intercept:.3f}\nR²={r**2:.4f}')
ax.set_xlabel('Y (ppm)', fontsize=12)
ax.set_ylabel('Y ponderado', fontsize=12)
ax.set_title('Y_ppm vs Y_pond — Verificación de Consistencia', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig16_Y_vs_Ypond.png"), dpi=150, bbox_inches='tight')
plt.close()
print(f"  R² = {r**2:.4f}, slope = {slope:.4f}")
print("  Guardado: fig16_Y_vs_Ypond.png")

print("\n" + "="*60)
print("  ANALISIS COMPLEMENTARIO COMPLETADO")
print("="*60)
