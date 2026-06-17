import sys; sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

df = pd.read_csv(r'c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001\itrio\BD_INTEGRADA_2026.csv')

print('=== RESUMEN GENERAL ===')
print(df.groupby('FUENTE').size().to_string())

print('\n=== LITOLOGIAS por FUENTE ===')
ct = df.groupby(['FUENTE','Litology_STD']).size().reset_index(name='N')
for fuente in ct['FUENTE'].unique():
    sub = ct[ct['FUENTE']==fuente].sort_values('N', ascending=False)
    print('\n  {}:'.format(fuente))
    for _, r in sub.iterrows():
        print('    {:30s} {:5d}'.format(str(r['Litology_STD']), r['N']))

print('\n=== Y_pond por FUENTE ===')
for fuente in df['FUENTE'].unique():
    sub = df[df['FUENTE']==fuente]
    yw = pd.to_numeric(sub['Y_pond'], errors='coerce')
    n_valid = int(yw.notna().sum())
    if n_valid > 0:
        print('  {:15s}: {:4d} con Ypond, media={:.1f}, max={:.1f}'.format(fuente, n_valid, yw.mean(), yw.max()))
    else:
        print('  {:15s}: SIN datos de Ypond'.format(fuente))

print('\n=== pXRF: 10 primeras filas ===')
pxrf = df[df['FUENTE']=='pXRF_2026'][['Sample','CP','Litology_STD','HORIZONTE','Y_ppm','Y_pond','Ce_ppm','La_ppm']].head(10)
print(pxrf.to_string(index=False))
