import os
import base64
import re
import pandas as pd

DIR = r"c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001"

def img_to_base64(img_name):
    img_path = os.path.join(DIR, img_name)
    if not os.path.exists(img_path): return ""
    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f'<img src="data:image/png;base64,{encoded}" alt="{img_name}">'

def csv_to_html(csv_name):
    csv_path = os.path.join(DIR, csv_name)
    if not os.path.exists(csv_path): return ""
    df = pd.read_csv(csv_path)
    return df.to_html(classes="data-table", index=False, border=0)

print("Leyendo reporte...")
with open(os.path.join(DIR, "INFORME_GEOESTADISTICO.txt"), "r", encoding="utf-8") as f:
    text = f.read()

# Define sections mapping to images/tables
sections_content = {
    "3. ESTADISTICAS DESCRIPTIVAS": f"<div class='figs'>{img_to_base64('fig02_histogramas_REE.png')}</div>",
    "4. CARACTERIZACION POR LITOLOGIA": f"<div class='figs'>{img_to_base64('fig01_boxplots_REE.png')}{img_to_base64('fig08_violin_Y.png')}</div>",
    "6. CORRELACIONES GEOQUIMICAS": f"<div class='figs'>{img_to_base64('fig03_correlacion.png')}{img_to_base64('fig04_scatter_Y.png')}{img_to_base64('fig05_spider_REE.png')}{img_to_base64('fig09_ratios_REE.png')}{img_to_base64('fig15_pairplot_REE.png')}</div>",
    "7. ANALISIS DE COMPONENTES PRINCIPALES": f"<div class='figs'>{img_to_base64('fig06_PCA.png')}</div>",
    "8. CLUSTERING GEOQUIMICO": f"<div class='figs'>{img_to_base64('fig12_clustering.png')}</div>",
    "9. ANALISIS ESPACIAL Y VARIOGRAMA": f"<div class='figs'>{img_to_base64('fig13_variograma.png')}</div>",
    "10. KRIGING": f"<div class='figs'>{img_to_base64('fig17_kriging_Y.png')}{img_to_base64('fig18_kriging_Ce.png')}{img_to_base64('fig18_kriging_Th.png')}{img_to_base64('fig19_kriging_CV.png')}</div>",
    "11. ANALISIS DE UMBRALES": f"<div class='figs'>{img_to_base64('fig10_QQ_plots.png')}{img_to_base64('fig11_CDF_Y.png')}</div>",
    "12. ANALISIS POR CAMPANA": f"<div class='figs'>{img_to_base64('fig07_mapa_Y_litologia.png')}</div>"
}

html = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Informe Geoestadístico Ytrio</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono&display=swap');
body { background-color: #0f1117; color: #e2e8f0; font-family: 'Inter', sans-serif; line-height: 1.6; margin: 0; padding: 0; display: flex;}
nav { width: 300px; background-color: #1a1d27; padding: 20px; position: fixed; height: 100vh; overflow-y: auto; border-right: 1px solid #334155; box-sizing: border-box;}
nav h2 { color: #4ade80; margin-bottom: 20px;}
nav a { display: block; color: #94a3b8; text-decoration: none; padding: 10px 0; font-size: 14px; border-bottom: 1px solid #1e293b; transition: all 0.3s;}
nav a:hover { color: #f0a500; padding-left: 10px; }
main { margin-left: 300px; padding: 40px; width: calc(100% - 300px); max-width: 1200px; box-sizing: border-box;}
h1 { color: #f0a500; font-size: 2.5rem; text-align: center; border-bottom: 2px solid #334155; padding-bottom: 20px;}
h2 { color: #4ade80; margin-top: 40px; border-bottom: 1px solid #334155; padding-bottom: 10px;}
pre { background-color: #1a1d27; padding: 20px; border-radius: 8px; overflow-x: auto; color: #cbd5e1; font-family: 'JetBrains Mono', monospace; border: 1px solid #334155; white-space: pre-wrap;}
img { max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5); border: 1px solid #334155;}
.data-table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;}
.data-table th { background-color: #f0a500; color: #0f1117; padding: 12px; text-align: left; font-weight: 600;}
.data-table td { padding: 10px; border-bottom: 1px solid #334155; }
.data-table tr:hover { background-color: #1e293b; }
.section { margin-bottom: 60px; }
.figs { display: flex; flex-direction: column; gap: 40px; margin-top: 30px;}
.card { background-color: #1a1d27; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #4ade80;}
</style>
</head>
<body>
<nav>
<h2>Índice</h2>
"""

# Very simple parsing
sections = re.split(r'\n(?=\d+\.\s)', text)
header_text = sections.pop(0) if sections and sections[0].startswith('=') else "INFORME GEOESTADISTICO PROFESIONAL"

nav_html = ""
main_html = f"<main><h1>INFORME GEOESTADISTICO PROFESIONAL<br><span style='font-size:1.2rem;color:#94a3b8;'>Campaña de Exploración de Ytrio y Tierras Raras</span></h1>\n"

for i, sec in enumerate(sections):
    lines = sec.strip().split('\n')
    title = lines[0].strip()
    id_title = f"sec_{i}"
    nav_html += f"<a href='#{id_title}'>{title}</a>\n"
    
    content = chr(10).join(lines[1:]).strip()
    # Format the content a bit better if it contains "HALLAZGO CLAVE" or "ANALISIS:"
    content = content.replace("HALLAZGO PRINCIPAL:", "<span style='color:#f0a500;font-weight:bold;'>HALLAZGO PRINCIPAL:</span>")
    content = content.replace("HALLAZGO CLAVE:", "<span style='color:#f0a500;font-weight:bold;'>HALLAZGO CLAVE:</span>")
    content = content.replace("ANALISIS:", "<span style='color:#4ade80;font-weight:bold;'>ANALISIS:</span>")
    
    main_html += f"<div class='section' id='{id_title}'><h2>{title}</h2>\n<pre>{content}</pre>\n"
    
    # Check if we have figures for this section
    for k, v in sections_content.items():
        if k in title:
            main_html += v
            break
            
    main_html += "</div>\n"

html += nav_html + "</nav>\n" + main_html + "</main></body></html>"

out_path = os.path.join(DIR, "INFORME_GEOESTADISTICO.html")
print("Guardando HTML...")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Informe HTML generado con éxito en: {out_path}")
