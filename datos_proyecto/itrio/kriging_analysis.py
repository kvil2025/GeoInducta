# ============================================================
# Kriging de Y_ppm — Gaussian Process Regression
# ============================================================
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel
from sklearn.preprocessing import StandardScaler
from scipy.interpolate import griddata
import warnings, os, sys

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

OUTDIR = r"c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001"
df = pd.read_csv(os.path.join(OUTDIR, "BD_Ytrio_LIMPIO.csv"))
df['FLAG_OUTLIER'] = df['FLAG_OUTLIER'].fillna('')
df_clean = df[df['FLAG_OUTLIER'] == ''].copy()

print("=== KRIGING DE Y_ppm ===")

# Preparar datos
coords = df_clean[['UTM_E','UTM_N','Y_ppm','Litology_STD']].dropna().copy()
coords['Y_log'] = np.log10(coords['Y_ppm'].clip(lower=0.1))

# Normalizar coordenadas para GP
scaler_xy = StandardScaler()
XY = scaler_xy.fit_transform(coords[['UTM_E','UTM_N']].values)
Z = coords['Y_log'].values

# Submuestrear para GP (max ~800 puntos para velocidad)
np.random.seed(42)
if len(XY) > 800:
    idx_sub = np.random.choice(len(XY), 800, replace=False)
    XY_train = XY[idx_sub]
    Z_train = Z[idx_sub]
else:
    XY_train = XY
    Z_train = Z

print(f"  Puntos de entrenamiento: {len(XY_train)}")
print(f"  Rango Y_log: {Z_train.min():.3f} a {Z_train.max():.3f}")

# Kernel Matern (nu=1.5 tipico para geociencias)
kernel = ConstantKernel(1.0) * Matern(length_scale=1.0, nu=1.5) + WhiteKernel(noise_level=0.05)

gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5, random_state=42)
print("  Entrenando GP/Kriging...")
gp.fit(XY_train, Z_train)

print(f"  Kernel optimizado: {gp.kernel_}")
print(f"  Log-marginal-likelihood: {gp.log_marginal_likelihood_value_:.3f}")

# Crear grilla de prediccion
e_min, e_max = coords['UTM_E'].min(), coords['UTM_E'].max()
n_min, n_max = coords['UTM_N'].min(), coords['UTM_N'].max()
margin = 1000
nx, ny = 150, 200

E_grid = np.linspace(e_min - margin, e_max + margin, nx)
N_grid = np.linspace(n_min - margin, n_max + margin, ny)
EE, NN = np.meshgrid(E_grid, N_grid)
grid_points = np.column_stack([EE.ravel(), NN.ravel()])
grid_scaled = scaler_xy.transform(grid_points)

print(f"  Prediciendo en grilla {nx}x{ny} ({nx*ny} puntos)...")
Z_pred, Z_std = gp.predict(grid_scaled, return_std=True)

Z_pred_grid = Z_pred.reshape(ny, nx)
Z_std_grid = Z_std.reshape(ny, nx)

# Convertir de log a ppm
Y_pred_ppm = 10**Z_pred_grid
Y_std_ppm = Z_std_grid  # mantener en log

# ============================================================
# FIGURA: Mapa Kriging Y_ppm
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(24, 8))

# --- Panel 1: Kriging estimacion ---
ax = axes[0]
levels_ppm = [5, 10, 15, 20, 30, 50, 75, 100, 150, 200, 300, 500]
norm = mcolors.LogNorm(vmin=5, vmax=500)
im = ax.pcolormesh(EE, NN, Y_pred_ppm, cmap='hot_r', norm=norm, shading='auto')
cs = ax.contour(EE, NN, Y_pred_ppm, levels=levels_ppm, colors='black', linewidths=0.5, alpha=0.5)
ax.clabel(cs, inline=True, fontsize=7, fmt='%.0f')
ax.scatter(coords['UTM_E'], coords['UTM_N'], c='white', s=1, alpha=0.15)
cb = plt.colorbar(im, ax=ax, shrink=0.8, label='Y estimado (ppm)')
ax.set_xlabel('UTM E', fontsize=11)
ax.set_ylabel('UTM N', fontsize=11)
ax.set_title('Kriging — Y (ppm) Estimado', fontsize=14, fontweight='bold')
ax.set_aspect('equal')

# --- Panel 2: Incertidumbre (std) ---
ax = axes[1]
im2 = ax.pcolormesh(EE, NN, Z_std_grid, cmap='YlOrRd', shading='auto')
ax.scatter(coords['UTM_E'], coords['UTM_N'], c='blue', s=1, alpha=0.1)
plt.colorbar(im2, ax=ax, shrink=0.8, label='Desviacion estandar (log10 Y)')
ax.set_xlabel('UTM E', fontsize=11)
ax.set_ylabel('UTM N', fontsize=11)
ax.set_title('Kriging — Incertidumbre de Estimacion', fontsize=14, fontweight='bold')
ax.set_aspect('equal')

# --- Panel 3: Anomalias Y > 50 ppm ---
ax = axes[2]
anomaly_mask = Y_pred_ppm >= 50
anomaly_grid = np.where(anomaly_mask, Y_pred_ppm, np.nan)
ax.pcolormesh(EE, NN, np.where(Y_pred_ppm < 50, Y_pred_ppm, np.nan),
              cmap='Greys', norm=norm, shading='auto', alpha=0.3)
im3 = ax.pcolormesh(EE, NN, anomaly_grid, cmap='hot_r', norm=norm, shading='auto')
ax.contour(EE, NN, Y_pred_ppm, levels=[50, 100, 200], colors=['yellow','orange','red'],
           linewidths=[2, 2.5, 3])

# Muestras reales > 50 ppm
high_y = coords[coords['Y_ppm'] >= 50]
ax.scatter(high_y['UTM_E'], high_y['UTM_N'], c='lime', s=12, edgecolors='black',
           linewidth=0.5, zorder=5, label=f'Muestras Y≥50 (n={len(high_y)})')
plt.colorbar(im3, ax=ax, shrink=0.8, label='Y estimado (ppm)')
ax.set_xlabel('UTM E', fontsize=11)
ax.set_ylabel('UTM N', fontsize=11)
ax.set_title('Zonas Anomalas — Y ≥ 50 ppm', fontsize=14, fontweight='bold')
ax.legend(fontsize=9, loc='lower left')
ax.set_aspect('equal')

plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig17_kriging_Y.png"), dpi=150, bbox_inches='tight')
plt.close()
print("  Guardado: fig17_kriging_Y.png")

# ============================================================
# Kriging Ce_ppm y Th_ppm
# ============================================================
for elem, vmin_v, vmax_v in [('Ce_ppm', 10, 800), ('Th_ppm', 1, 200)]:
    print(f"\n  Kriging {elem}...")
    z_col = np.log10(coords[elem].clip(lower=0.1).values) if elem in coords.columns else None
    if z_col is None:
        coords_e = df_clean[['UTM_E','UTM_N',elem]].dropna()
        z_col = np.log10(coords_e[elem].clip(lower=0.1).values)
        xy_e = scaler_xy.transform(coords_e[['UTM_E','UTM_N']].values)
    else:
        xy_e = XY

    if len(xy_e) > 800:
        idx_s = np.random.choice(len(xy_e), 800, replace=False)
        xy_t, z_t = xy_e[idx_s], z_col[idx_s]
    else:
        xy_t, z_t = xy_e, z_col

    gp_e = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=3, random_state=42)
    gp_e.fit(xy_t, z_t)
    z_p, _ = gp_e.predict(grid_scaled, return_std=True)
    z_ppm = 10**z_p.reshape(ny, nx)

    fig, ax = plt.subplots(figsize=(10, 8))
    norm_e = mcolors.LogNorm(vmin=vmin_v, vmax=vmax_v)
    im = ax.pcolormesh(EE, NN, z_ppm, cmap='YlOrRd', norm=norm_e, shading='auto')
    ax.scatter(coords['UTM_E'], coords['UTM_N'], c='white', s=1, alpha=0.1)
    plt.colorbar(im, ax=ax, label=f'{elem} estimado (ppm)', shrink=0.8)
    ax.set_xlabel('UTM E')
    ax.set_ylabel('UTM N')
    ax.set_title(f'Kriging — {elem} Estimado', fontsize=14, fontweight='bold')
    ax.set_aspect('equal')
    plt.tight_layout()
    fname = f"fig18_kriging_{elem.replace('_ppm','')}.png"
    plt.savefig(os.path.join(OUTDIR, fname), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Guardado: {fname}")

# ============================================================
# Cross-validation del kriging Y
# ============================================================
print("\n=== CROSS-VALIDATION KRIGING Y ===")
from sklearn.model_selection import cross_val_score
scores = cross_val_score(
    GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=2, random_state=42),
    XY_train, Z_train, cv=5, scoring='r2'
)
print(f"  R² (5-fold CV): {scores.mean():.3f} ± {scores.std():.3f}")
print(f"  R² por fold: {[f'{s:.3f}' for s in scores]}")

# RMSE
from sklearn.model_selection import cross_val_predict
Z_cv_pred = cross_val_predict(
    GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=2, random_state=42),
    XY_train, Z_train, cv=5
)
rmse_log = np.sqrt(np.mean((Z_train - Z_cv_pred)**2))
print(f"  RMSE (log10 Y): {rmse_log:.4f}")
print(f"  Esto equivale a un factor de error de ~{10**rmse_log:.2f}x en ppm")

# Scatter real vs predicho
fig, ax = plt.subplots(figsize=(8, 8))
ax.scatter(10**Z_train, 10**Z_cv_pred, s=8, alpha=0.4, color='steelblue')
lims = [1, 700]
ax.plot(lims, lims, 'r--', lw=2, label='1:1')
ax.set_xlabel('Y real (ppm)', fontsize=12)
ax.set_ylabel('Y predicho CV (ppm)', fontsize=12)
ax.set_title('Validación Cruzada Kriging — Y (ppm)', fontsize=14, fontweight='bold')
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlim(lims)
ax.set_ylim(lims)
r2_text = f'R² = {scores.mean():.3f}\nRMSE(log) = {rmse_log:.4f}'
ax.text(0.05, 0.92, r2_text, transform=ax.transAxes, fontsize=12,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8), va='top')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3, which='both')
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "fig19_kriging_CV.png"), dpi=150, bbox_inches='tight')
plt.close()
print("  Guardado: fig19_kriging_CV.png")

print("\n=== KRIGING COMPLETADO ===")
