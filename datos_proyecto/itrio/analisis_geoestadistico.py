# ============================================================
# Analisis Geoestadistico Profesional - BD_Ytrio_LIMPIO.csv
# REE + Litologias
# ============================================================
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import warnings, os, sys

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

OUTDIR = r"c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001"
df = pd.read_csv(os.path.join(OUTDIR, "BD_Ytrio_LIMPIO.csv"))

# Definir variables REE y geoquimicas
REE = ['Y_ppm','Ce_ppm','La_ppm','Pr_ppm','Nd_ppm','Th_ppm']
MAJORS = ['Fe__','Ti__','K__','Mn_','Ca_ppm','V_ppm','Cr_ppm','Cl_ppm']
ALL_GEO = REE + MAJORS

# Filtrar solo registros sin flag de outlier extremo para analisis
df['FLAG_OUTLIER'] = df['FLAG_OUTLIER'].fillna('')
df_clean = df[df['FLAG_OUTLIER'] == ''].copy()
print(f"Registros totales: {len(df)} | Sin outliers: {len(df_clean)}")

# Litologias principales (>30 muestras)
lit_counts = df_clean['Litology_STD'].value_counts()
main_lits = lit_counts[lit_counts >= 30].index.tolist()
df_main = df_clean[df_clean['Litology_STD'].isin(main_lits)].copy()
print(f"Litologias principales (n>=30): {len(main_lits)}")
for l in main_lits:
    print(f"  {l}: {lit_counts[l]}")

# Colores para litologias
palette = sns.color_palette("husl", len(main_lits))
lit_colors = dict(zip(main_lits, palette))

# ============================================================
# FIG 1: Estadisticas descriptivas REE por litologia
# ============================================================
print("\n=== ESTADISTICAS REE POR LITOLOGIA ===")
stats_table = []
for lit in main_lits:
    sub = df_clean[df_clean['Litology_STD'] == lit]
    row = {'Litologia': lit, 'N': len(sub)}
    for col in REE:
        vals = sub[col].dropna()
        row[f'{col}_mean'] = round(vals.mean(), 2)
        row[f'{col}_med'] = round(vals.median(), 2)
        row[f'{col}_std'] = round(vals.std(), 2)
        row[f'{col}_cv'] = round(vals.std()/vals.mean()*100, 1) if vals.mean() > 0 else 0
    stats_table.append(row)

stats_df = pd.DataFrame(stats_table)
stats_df.to_csv(os.path.join(OUTDIR, "estadisticas_REE_litologia.csv"), index=False)
print("Guardado: estadisticas_REE_litologia.csv")

# Imprimir tabla resumida
for _, r in stats_df.iterrows():
    print(f"\n  {r['Litologia']} (n={int(r['N'])})")
    for col in REE:
        print(f"    {col}: media={r[f'{col}_mean']:.1f}  med={r[f'{col}_med']:.1f}  CV={r[f'{col}_cv']:.0f}%")

# ============================================================
# FIG 2: Boxplots REE por litologia
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(20, 12))
fig.suptitle('Distribucion de REE por Litologia Principal', fontsize=16, fontweight='bold')

for idx, col in enumerate(REE):
    ax = axes[idx // 3, idx % 3]
    data_plot = df_main[['Litology_STD', col]].dropna()
    # Ordenar por mediana
    order = data_plot.groupby('Litology_STD')[col].median().sort_values(ascending=False).index
    sns.boxplot(data=data_plot, x='Litology_STD', y=col, order=order,
                palette='viridis', ax=ax, fliersize=2)
    ax.set_title(col, fontsize=13, fontweight='bold')
    ax.set_xlabel('')
    ax.tick_params(axis='x', rotation=45, labelsize=7)
    ax.set_ylabel('ppm')

plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig01_boxplots_REE.png"), dpi=150, bbox_inches='tight')
plt.close()
print("\nGuardado: fig01_boxplots_REE.png")

# ============================================================
# FIG 3: Histogramas + Log-transform de Y_ppm
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Distribucion de REE - Histogramas (log10)', fontsize=16, fontweight='bold')

for idx, col in enumerate(REE):
    ax = axes[idx // 3, idx % 3]
    vals = df_clean[col].dropna()
    vals_log = np.log10(vals[vals > 0])
    ax.hist(vals_log, bins=50, color='steelblue', edgecolor='white', alpha=0.8)
    ax.axvline(np.log10(vals.median()), color='red', ls='--', lw=2, label=f'Med={vals.median():.1f}')
    ax.axvline(np.log10(vals.mean()), color='orange', ls='-', lw=2, label=f'Mean={vals.mean():.1f}')
    ax.set_title(f'{col} (log10)', fontsize=12, fontweight='bold')
    ax.set_xlabel('log10(ppm)')
    ax.legend(fontsize=8)
    # Test normalidad log
    if len(vals_log) > 8:
        _, p_shap = stats.shapiro(vals_log.sample(min(5000, len(vals_log)), random_state=42))
        ax.text(0.02, 0.95, f'Shapiro p={p_shap:.4f}', transform=ax.transAxes, fontsize=8, va='top')

plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig02_histogramas_REE.png"), dpi=150, bbox_inches='tight')
plt.close()
print("Guardado: fig02_histogramas_REE.png")

# ============================================================
# FIG 4: Matriz de correlacion
# ============================================================
fig, ax = plt.subplots(figsize=(14, 11))
corr_data = df_clean[ALL_GEO].dropna()
corr_log = np.log10(corr_data.replace(0, np.nan).dropna())
corr_matrix = corr_log.corr(method='pearson')

mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
            mask=mask, square=True, ax=ax, vmin=-1, vmax=1,
            annot_kws={'size': 9}, linewidths=0.5)
ax.set_title('Matriz de Correlacion (Pearson, log10)', fontsize=15, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig03_correlacion.png"), dpi=150, bbox_inches='tight')
plt.close()
print("Guardado: fig03_correlacion.png")

# Imprimir correlaciones clave con Y
print("\n=== CORRELACIONES CON Y_ppm (log) ===")
y_corr = corr_matrix['Y_ppm'].drop('Y_ppm').sort_values(ascending=False)
for name, val in y_corr.items():
    sig = "***" if abs(val) > 0.5 else "**" if abs(val) > 0.3 else "*" if abs(val) > 0.15 else ""
    print(f"  Y vs {name}: r={val:.3f} {sig}")

# ============================================================
# FIG 5: Scatter Y vs otros REE
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(18, 11))
fig.suptitle('Y_ppm vs Otros Elementos (por Litologia)', fontsize=16, fontweight='bold')

scatter_vs = ['Ce_ppm', 'La_ppm', 'Nd_ppm', 'Th_ppm', 'Fe__', 'Ti__']
for idx, col in enumerate(scatter_vs):
    ax = axes[idx // 3, idx % 3]
    for lit in main_lits:
        sub = df_main[df_main['Litology_STD'] == lit]
        ax.scatter(sub[col], sub['Y_ppm'], s=8, alpha=0.5, label=lit, color=lit_colors[lit])
    ax.set_xlabel(col)
    ax.set_ylabel('Y_ppm')
    ax.set_title(f'Y vs {col}', fontweight='bold')
    # Regression line general
    valid = df_clean[[col, 'Y_ppm']].dropna()
    if len(valid) > 2:
        slope, intercept, r, p, se = stats.linregress(valid[col], valid['Y_ppm'])
        ax.text(0.02, 0.95, f'r={r:.3f}  p={p:.2e}', transform=ax.transAxes, fontsize=9, va='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

axes[0, 0].legend(fontsize=6, loc='lower right', ncol=2)
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig04_scatter_Y.png"), dpi=150, bbox_inches='tight')
plt.close()
print("Guardado: fig04_scatter_Y.png")

# ============================================================
# FIG 6: Diagrama Spider REE normalizado a Condrita
# ============================================================
# Valores condrita C1 (McDonough & Sun 1995)
chondrite = {'La_ppm': 0.237, 'Ce_ppm': 0.613, 'Pr_ppm': 0.0928,
             'Nd_ppm': 0.457, 'Y_ppm': 1.57, 'Th_ppm': 0.0292}
ree_order = ['La_ppm', 'Ce_ppm', 'Pr_ppm', 'Nd_ppm', 'Y_ppm', 'Th_ppm']
ree_labels = ['La', 'Ce', 'Pr', 'Nd', 'Y', 'Th']

fig, ax = plt.subplots(figsize=(12, 7))
for lit in main_lits:
    sub = df_clean[df_clean['Litology_STD'] == lit]
    medians = [sub[col].median() / chondrite[col] for col in ree_order]
    ax.plot(ree_labels, medians, 'o-', label=f'{lit} (n={len(sub)})',
            color=lit_colors[lit], linewidth=2, markersize=5)

ax.set_yscale('log')
ax.set_ylabel('Muestra / Condrita C1', fontsize=12)
ax.set_xlabel('Elemento', fontsize=12)
ax.set_title('Diagrama Spider REE Normalizado a Condrita C1\n(Medianas por Litologia)',
             fontsize=14, fontweight='bold')
ax.legend(fontsize=7, loc='best', ncol=2)
ax.grid(True, which='both', alpha=0.3)
ax.set_ylim(bottom=1)
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig05_spider_REE.png"), dpi=150, bbox_inches='tight')
plt.close()
print("Guardado: fig05_spider_REE.png")

# ============================================================
# FIG 7: PCA - Analisis de Componentes Principales
# ============================================================
print("\n=== ANALISIS DE COMPONENTES PRINCIPALES (PCA) ===")
pca_cols = REE + ['Fe__', 'Ti__', 'K__', 'Ca_ppm']
df_pca = df_clean[pca_cols + ['Litology_STD']].dropna()
df_pca = df_pca[df_pca['Litology_STD'].isin(main_lits)]
X = df_pca[pca_cols].values
X_log = np.log10(np.where(X > 0, X, 0.01))

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_log)

pca = PCA(n_components=4)
pcs = pca.fit_transform(X_scaled)

print(f"  Varianza explicada:")
for i, v in enumerate(pca.explained_variance_ratio_):
    print(f"    PC{i+1}: {v*100:.1f}%")
print(f"  Acumulada PC1+PC2: {sum(pca.explained_variance_ratio_[:2])*100:.1f}%")

# Loadings
print(f"\n  Loadings PC1 y PC2:")
for j, col in enumerate(pca_cols):
    print(f"    {col:10s}  PC1={pca.components_[0,j]:+.3f}  PC2={pca.components_[1,j]:+.3f}")

fig, axes = plt.subplots(1, 2, figsize=(18, 7))

# Biplot scores
ax = axes[0]
for lit in main_lits:
    mask = df_pca['Litology_STD'] == lit
    ax.scatter(pcs[mask, 0], pcs[mask, 1], s=10, alpha=0.5, label=lit, color=lit_colors[lit])
ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)', fontsize=12)
ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)', fontsize=12)
ax.set_title('PCA - Scores por Litologia', fontsize=14, fontweight='bold')
ax.legend(fontsize=7, ncol=2)
ax.axhline(0, color='gray', ls='-', lw=0.5)
ax.axvline(0, color='gray', ls='-', lw=0.5)
ax.grid(alpha=0.2)

# Biplot loadings
ax = axes[1]
for j, col in enumerate(pca_cols):
    ax.arrow(0, 0, pca.components_[0, j]*3, pca.components_[1, j]*3,
             head_width=0.08, head_length=0.05, fc='red', ec='red', alpha=0.8)
    ax.text(pca.components_[0, j]*3.3, pca.components_[1, j]*3.3,
            col.replace('_ppm','').replace('__','%'), fontsize=10, fontweight='bold', color='darkred')
ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')
ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')
ax.set_title('PCA - Loadings (Variables)', fontsize=14, fontweight='bold')
ax.axhline(0, color='gray', ls='-', lw=0.5)
ax.axvline(0, color='gray', ls='-', lw=0.5)
ax.grid(alpha=0.2)
ax.set_xlim(-4, 4)
ax.set_ylim(-4, 4)

plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig06_PCA.png"), dpi=150, bbox_inches='tight')
plt.close()
print("Guardado: fig06_PCA.png")

# ============================================================
# FIG 8: Kruskal-Wallis test por litologia
# ============================================================
print("\n=== TEST KRUSKAL-WALLIS (REE por Litologia) ===")
kw_results = []
for col in REE:
    groups = [df_clean.loc[df_clean['Litology_STD'] == lit, col].dropna().values for lit in main_lits]
    groups = [g for g in groups if len(g) > 1]
    if len(groups) >= 2:
        h_stat, p_val = stats.kruskal(*groups)
        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
        print(f"  {col}: H={h_stat:.1f}  p={p_val:.2e}  {sig}")
        kw_results.append({'Variable': col, 'H_stat': round(h_stat, 2), 'p_value': p_val, 'Significancia': sig})

kw_df = pd.DataFrame(kw_results)
kw_df.to_csv(os.path.join(OUTDIR, "test_kruskal_wallis.csv"), index=False)

# ============================================================
# FIG 9: Mapa de muestras coloreado por Y_ppm
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(18, 8))

ax = axes[0]
sc = ax.scatter(df_clean['UTM_E'], df_clean['UTM_N'], c=np.log10(df_clean['Y_ppm'].clip(lower=0.1)),
                s=5, cmap='hot_r', alpha=0.7)
plt.colorbar(sc, ax=ax, label='log10(Y ppm)', shrink=0.8)
ax.set_xlabel('UTM E')
ax.set_ylabel('UTM N')
ax.set_title('Mapa Geoquimico - Y (ppm)', fontsize=14, fontweight='bold')
ax.set_aspect('equal')

ax = axes[1]
for lit in main_lits:
    sub = df_main[df_main['Litology_STD'] == lit]
    ax.scatter(sub['UTM_E'], sub['UTM_N'], s=5, alpha=0.5, label=lit, color=lit_colors[lit])
ax.set_xlabel('UTM E')
ax.set_ylabel('UTM N')
ax.set_title('Mapa por Litologia', fontsize=14, fontweight='bold')
ax.legend(fontsize=6, loc='best', ncol=2, markerscale=3)
ax.set_aspect('equal')

plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig07_mapa_Y_litologia.png"), dpi=150, bbox_inches='tight')
plt.close()
print("Guardado: fig07_mapa_Y_litologia.png")

# ============================================================
# FIG 10: Violin plots Y_ppm por litologia
# ============================================================
fig, ax = plt.subplots(figsize=(16, 7))
order = df_main.groupby('Litology_STD')['Y_ppm'].median().sort_values(ascending=False).index
sns.violinplot(data=df_main, x='Litology_STD', y='Y_ppm', order=order,
               palette='viridis', ax=ax, inner='quartile', cut=0)
ax.set_title('Distribucion de Y (ppm) por Litologia - Violin Plot', fontsize=14, fontweight='bold')
ax.set_xlabel('')
ax.tick_params(axis='x', rotation=45, labelsize=8)
ax.set_ylabel('Y (ppm)')
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig08_violin_Y.png"), dpi=150, bbox_inches='tight')
plt.close()
print("Guardado: fig08_violin_Y.png")

# ============================================================
# FIG 11: Ratios REE diagnosticos
# ============================================================
print("\n=== RATIOS REE DIAGNOSTICOS ===")
df_clean['La_Ce'] = df_clean['La_ppm'] / df_clean['Ce_ppm'].replace(0, np.nan)
df_clean['Ce_Y'] = df_clean['Ce_ppm'] / df_clean['Y_ppm'].replace(0, np.nan)
df_clean['Nd_Y'] = df_clean['Nd_ppm'] / df_clean['Y_ppm'].replace(0, np.nan)
df_clean['LREE_Y'] = (df_clean['La_ppm'] + df_clean['Ce_ppm'] + df_clean['Nd_ppm']) / df_clean['Y_ppm'].replace(0, np.nan)

ratios = ['La_Ce', 'Ce_Y', 'Nd_Y', 'LREE_Y']
fig, axes = plt.subplots(2, 2, figsize=(16, 11))
fig.suptitle('Ratios REE Diagnosticos por Litologia', fontsize=15, fontweight='bold')

for idx, ratio in enumerate(ratios):
    ax = axes[idx // 2, idx % 2]
    data_r = df_clean[df_clean['Litology_STD'].isin(main_lits)][['Litology_STD', ratio]].dropna()
    order = data_r.groupby('Litology_STD')[ratio].median().sort_values(ascending=False).index
    sns.boxplot(data=data_r, x='Litology_STD', y=ratio, order=order,
                palette='Set2', ax=ax, fliersize=2)
    ax.set_title(ratio.replace('_', '/'), fontsize=12, fontweight='bold')
    ax.set_xlabel('')
    ax.tick_params(axis='x', rotation=45, labelsize=7)

plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig09_ratios_REE.png"), dpi=150, bbox_inches='tight')
plt.close()
print("Guardado: fig09_ratios_REE.png")

for ratio in ratios:
    vals = df_clean[ratio].dropna()
    print(f"  {ratio}: media={vals.mean():.2f}  med={vals.median():.2f}  std={vals.std():.2f}")

# ============================================================
# RESUMEN FINAL
# ============================================================
print("\n" + "="*60)
print("  ANALISIS GEOESTADISTICO COMPLETADO")
print("="*60)
print(f"\nArchivos generados en: {OUTDIR}")
print("  - estadisticas_REE_litologia.csv")
print("  - test_kruskal_wallis.csv")
print("  - fig01_boxplots_REE.png")
print("  - fig02_histogramas_REE.png")
print("  - fig03_correlacion.png")
print("  - fig04_scatter_Y.png")
print("  - fig05_spider_REE.png")
print("  - fig06_PCA.png")
print("  - fig07_mapa_Y_litologia.png")
print("  - fig08_violin_Y.png")
print("  - fig09_ratios_REE.png")
