import pandas as pd
import numpy as np
import json
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

OUTDIR = r"c:\Users\geolo\OneDrive\Documentos\INDUCTA\ANTI\001"
df = pd.read_csv(os.path.join(OUTDIR, "BD_Ytrio_LIMPIO.csv"))
df['FLAG_OUTLIER'] = df['FLAG_OUTLIER'].fillna('')
df['Litology_STD'] = df['Litology_STD'].fillna('SIN_ASIGNAR')
df['FLAG_DUPLICADO'] = df['FLAG_DUPLICADO'].fillna('')

# Preparar datos para el visor
cols = ['Sample','UTM_E','UTM_N','COTA_M','Y_ppm','Y_pond',
        'Ce_ppm','La_ppm','Th_ppm','Nd_ppm','Fe__','Litology_STD',
        'FLAG_OUTLIER','FLAG_DUPLICADO']
data = df[cols].dropna(subset=['UTM_E','UTM_N','Y_ppm']).copy()
data = data.fillna('')

# Convertir a lista de dicts para JSON
records = data.to_dict(orient='records')
json_data = json.dumps(records, ensure_ascii=False)

# Literales para litologias unicas y sus colores
lits = sorted(data['Litology_STD'].unique().tolist())

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Visor Geoquimico — Y (ppm) | Campaña Ytrio y REE</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',sans-serif; background:#0f1117; color:#e0e0e0; display:flex; flex-direction:column; height:100vh; overflow:hidden; }}

  /* HEADER */
  #header {{ background:linear-gradient(135deg,#1a1f2e,#0d1b2a); padding:10px 20px; display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #2a3a4a; flex-shrink:0; }}
  #header h1 {{ font-size:18px; font-weight:700; color:#4fc3f7; letter-spacing:1px; }}
  #header .subtitle {{ font-size:12px; color:#78909c; margin-top:2px; }}
  #stats-bar {{ display:flex; gap:20px; }}
  .stat-pill {{ background:#1e2a3a; border:1px solid #2a3a4a; border-radius:20px; padding:4px 14px; font-size:12px; }}
  .stat-pill span {{ color:#4fc3f7; font-weight:700; }}

  /* LAYOUT */
  #main {{ display:flex; flex:1; overflow:hidden; }}

  /* PANEL IZQUIERDO */
  #sidebar {{ width:300px; background:#141920; border-right:1px solid #2a3a4a; display:flex; flex-direction:column; flex-shrink:0; overflow:hidden; }}
  #sidebar h3 {{ padding:12px 16px; font-size:13px; color:#90a4ae; text-transform:uppercase; letter-spacing:1px; border-bottom:1px solid #2a3a4a; }}

  /* CONTROLES */
  #controls {{ padding:12px; border-bottom:1px solid #2a3a4a; }}
  .ctrl-group {{ margin-bottom:12px; }}
  .ctrl-group label {{ font-size:11px; color:#78909c; display:block; margin-bottom:4px; text-transform:uppercase; letter-spacing:0.5px; }}
  input[type=range] {{ width:100%; accent-color:#4fc3f7; }}
  .range-vals {{ display:flex; justify-content:space-between; font-size:11px; color:#546e7a; margin-top:2px; }}
  select {{ width:100%; background:#1e2a3a; border:1px solid #2a3a4a; color:#e0e0e0; padding:6px 8px; border-radius:6px; font-size:12px; }}
  .btn {{ width:100%; padding:8px; background:linear-gradient(135deg,#0077b6,#0096c7); border:none; color:white; border-radius:6px; cursor:pointer; font-size:12px; font-weight:600; margin-top:4px; }}
  .btn:hover {{ background:linear-gradient(135deg,#0096c7,#00b4d8); }}
  .btn.secondary {{ background:#1e2a3a; border:1px solid #2a3a4a; color:#90a4ae; }}
  .btn.secondary:hover {{ background:#2a3a4a; color:#e0e0e0; }}

  /* LEYENDA */
  #legend {{ padding:12px; border-bottom:1px solid #2a3a4a; }}
  #legend-bar {{ height:16px; border-radius:4px; margin:8px 0; background:linear-gradient(to right, #313695,#4575b4,#74add1,#abd9e9,#ffffbf,#fee090,#fdae61,#f46d43,#d73027,#a50026); }}
  .legend-labels {{ display:flex; justify-content:space-between; font-size:10px; color:#78909c; }}

  /* INFO MUESTRA */
  #sample-info {{ padding:12px; flex:1; overflow-y:auto; }}
  #sample-info h4 {{ font-size:13px; color:#4fc3f7; margin-bottom:10px; }}
  .info-row {{ display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid #1e2a3a; font-size:12px; }}
  .info-row .label {{ color:#78909c; }}
  .info-row .value {{ color:#e0e0e0; font-weight:600; }}
  .info-row .value.high {{ color:#ff5722; }}
  .info-row .value.med {{ color:#ffa726; }}
  .info-row .value.low {{ color:#66bb6a; }}
  #no-selection {{ color:#546e7a; font-size:12px; text-align:center; padding:20px; }}

  /* MAPA */
  #map-area {{ flex:1; position:relative; overflow:hidden; background:#0a0e14; }}
  #canvas {{ width:100%; height:100%; cursor:crosshair; }}

  /* TOOLTIP */
  #tooltip {{ position:absolute; background:rgba(10,15,25,0.95); border:1px solid #2a3a4a; border-radius:8px; padding:10px 14px; font-size:12px; pointer-events:none; display:none; max-width:220px; z-index:100; box-shadow:0 4px 20px rgba(0,0,0,0.5); }}
  #tooltip .tt-title {{ font-weight:700; color:#4fc3f7; font-size:13px; margin-bottom:6px; }}
  #tooltip .tt-row {{ display:flex; justify-content:space-between; gap:12px; margin:2px 0; }}
  #tooltip .tt-val {{ font-weight:700; }}

  /* MINIHISTOGRAMA */
  #mini-hist {{ padding:12px; border-top:1px solid #2a3a4a; }}
  #mini-hist h4 {{ font-size:11px; color:#78909c; text-transform:uppercase; margin-bottom:6px; }}

  /* ESCALA ZOOM */
  #zoom-controls {{ position:absolute; bottom:20px; right:20px; display:flex; flex-direction:column; gap:4px; z-index:50; }}
  .zoom-btn {{ width:36px; height:36px; background:#1e2a3a; border:1px solid #2a3a4a; color:#e0e0e0; font-size:20px; cursor:pointer; border-radius:6px; display:flex; align-items:center; justify-content:center; line-height:1; }}
  .zoom-btn:hover {{ background:#2a3a4a; }}

  /* BARRA INFERIOR */
  #statusbar {{ background:#0d1117; border-top:1px solid #2a3a4a; padding:5px 16px; font-size:11px; color:#546e7a; display:flex; gap:20px; flex-shrink:0; }}
  #statusbar span b {{ color:#78909c; }}

  /* FILTROS LITOLOGIA */
  #lit-filter {{ padding:12px; border-bottom:1px solid #2a3a4a; max-height:160px; overflow-y:auto; }}
  #lit-filter h4 {{ font-size:11px; color:#78909c; text-transform:uppercase; margin-bottom:6px; }}
  .lit-item {{ display:flex; align-items:center; gap:6px; margin-bottom:3px; font-size:11px; cursor:pointer; }}
  .lit-item input {{ accent-color:#4fc3f7; cursor:pointer; }}
  .lit-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; }}
</style>
</head>
<body>

<div id="header">
  <div>
    <h1>🗺 VISOR GEOQUIMICO — Y (ppm)</h1>
    <div class="subtitle">Campaña de Exploración de Ytrio y Tierras Raras | BD_Ytrio_LIMPIO.csv</div>
  </div>
  <div id="stats-bar">
    <div class="stat-pill">Muestras: <span id="stat-n">0</span></div>
    <div class="stat-pill">Y media: <span id="stat-mean">0</span> ppm</div>
    <div class="stat-pill">Y mediana: <span id="stat-med">0</span> ppm</div>
    <div class="stat-pill">Y máx: <span id="stat-max">0</span> ppm</div>
  </div>
</div>

<div id="main">
  <!-- SIDEBAR -->
  <div id="sidebar">
    <h3>⚙ Controles</h3>
    <div id="controls">
      <div class="ctrl-group">
        <label>Escala de Color</label>
        <select id="colormap-sel" onchange="redraw()">
          <option value="spectral">Spectral (científico)</option>
          <option value="hot">Hot (anomalías)</option>
          <option value="viridis">Viridis</option>
          <option value="plasma">Plasma</option>
        </select>
      </div>
      <div class="ctrl-group">
        <label>Tamaño de punto</label>
        <input type="range" id="pt-size" min="2" max="16" value="5" oninput="redraw()">
        <div class="range-vals"><span>2</span><span>16</span></div>
      </div>
      <div class="ctrl-group">
        <label>Umbral mínimo Y (ppm)</label>
        <input type="range" id="y-min" min="0" max="300" value="0" oninput="updateYFilter()">
        <div class="range-vals"><span>0</span><span id="y-min-val">0</span><span>300</span></div>
      </div>
      <div class="ctrl-group">
        <label>Umbral máximo Y (ppm)</label>
        <input type="range" id="y-max" min="0" max="620" value="620" oninput="updateYFilter()">
        <div class="range-vals"><span>0</span><span id="y-max-val">620</span><span>620</span></div>
      </div>
      <div class="ctrl-group">
        <label>Mostrar solo anomalías</label>
        <select id="anomaly-filter" onchange="redraw()">
          <option value="all">Todas las muestras</option>
          <option value="50">Y ≥ 50 ppm</option>
          <option value="100">Y ≥ 100 ppm</option>
          <option value="200">Y ≥ 200 ppm</option>
        </select>
      </div>
      <button class="btn" onclick="resetView()">🔄 Restablecer Vista</button>
      <button class="btn secondary" onclick="toggleGrid()"># Cuadrícula</button>
    </div>

    <!-- LEYENDA -->
    <div id="legend">
      <label style="font-size:11px;color:#78909c;">ESCALA Y (ppm)</label>
      <div id="legend-bar"></div>
      <div class="legend-labels">
        <span>0</span><span>50</span><span>100</span><span>200</span><span>400+</span>
      </div>
    </div>

    <!-- FILTRO LITOLOGIA -->
    <div id="lit-filter">
      <h4>Litologías</h4>
      <label class="lit-item">
        <input type="checkbox" id="chk-all" checked onchange="toggleAllLit(this)"> Todas
      </label>
      <div id="lit-checkboxes"></div>
    </div>

    <!-- INFO MUESTRA -->
    <div id="sample-info">
      <div id="no-selection">👆 Haz clic en una muestra para ver sus datos</div>
      <div id="sample-detail" style="display:none"></div>
    </div>
  </div>

  <!-- MAPA -->
  <div id="map-area">
    <canvas id="canvas"></canvas>
    <div id="tooltip">
      <div class="tt-title" id="tt-sample"></div>
      <div class="tt-row"><span>Y</span><span class="tt-val" id="tt-y" style="color:#ff7043"></span></div>
      <div class="tt-row"><span>Ce</span><span class="tt-val" id="tt-ce"></span></div>
      <div class="tt-row"><span>Th</span><span class="tt-val" id="tt-th"></span></div>
      <div class="tt-row"><span>Fe%</span><span class="tt-val" id="tt-fe"></span></div>
      <div class="tt-row"><span>Litología</span><span class="tt-val" id="tt-lit" style="font-size:11px"></span></div>
      <div style="font-size:10px;color:#546e7a;margin-top:4px">Clic para detalles completos</div>
    </div>
    <div id="zoom-controls">
      <button class="zoom-btn" onclick="zoom(1.25)">+</button>
      <button class="zoom-btn" onclick="zoom(0.8)">−</button>
      <button class="zoom-btn" title="Encuadrar" onclick="resetView()" style="font-size:13px">⊠</button>
    </div>
  </div>
</div>

<div id="statusbar">
  <span><b>UTM E:</b> <span id="sb-e">—</span></span>
  <span><b>UTM N:</b> <span id="sb-n">—</span></span>
  <span><b>Muestras visibles:</b> <span id="sb-vis">—</span></span>
  <span><b>Zoom:</b> <span id="sb-zoom">1.0x</span></span>
</div>

<script>
const RAW = {json_data};

// ── Paletas ──────────────────────────────────────────────────
const PALETTES = {{
  spectral: ['#313695','#4575b4','#74add1','#abd9e9','#ffffbf','#fee090','#fdae61','#f46d43','#d73027','#a50026'],
  hot:      ['#000000','#200000','#500000','#900000','#c80000','#ff2000','#ff6000','#ff9000','#ffc000','#ffff00'],
  viridis:  ['#440154','#482878','#3e4989','#31688e','#26828e','#1f9e89','#35b779','#6ece58','#b5de2b','#fde725'],
  plasma:   ['#0d0887','#46039f','#7201a8','#9c179e','#bd3786','#d8576b','#ed7953','#fb9f3a','#fdcf18','#f0f921'],
}};

function getColor(val, min, max, palette) {{
  const t = Math.max(0, Math.min(1, (val - min) / (max - min)));
  const n = palette.length - 1;
  const i = Math.floor(t * n);
  const f = t * n - i;
  if (i >= n) return palette[n];
  return lerpColor(palette[i], palette[i+1], f);
}}

function lerpColor(a, b, t) {{
  const ah = parseInt(a.slice(1),16), bh = parseInt(b.slice(1),16);
  const ar=(ah>>16)&0xff, ag=(ah>>8)&0xff, ab=ah&0xff;
  const br=(bh>>16)&0xff, bg=(bh>>8)&0xff, bb=bh&0xff;
  const r=Math.round(ar+(br-ar)*t), g=Math.round(ag+(bg-ag)*t), bl2=Math.round(ab+(bb-ab)*t);
  return `rgb(${{r}},${{g}},${{bl2}})`;
}}

// ── Estado ────────────────────────────────────────────────────
let transform = {{ x:0, y:0, scale:1 }};
let dragging = false, dragStart = null, dragTf = null;
let showGrid = true;
let selectedSample = null;
let visibleLits = new Set();

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');

// ── Litologias ────────────────────────────────────────────────
const litColors = {{}};
const litList = [...new Set(RAW.map(r => r.Litology_STD))].sort();
const litHues = litList.map((_,i) => Math.round(i * 360 / litList.length));
litList.forEach((l,i) => {{
  const h = litHues[i];
  litColors[l] = `hsl(${{h}},70%,60%)`;
  visibleLits.add(l);
}});

// Construir checkboxes
const litBox = document.getElementById('lit-checkboxes');
litList.forEach(l => {{
  const div = document.createElement('div');
  div.className = 'lit-item';
  div.innerHTML = `<input type="checkbox" class="lit-chk" value="${{l}}" checked>
    <div class="lit-dot" style="background:${{litColors[l]}}"></div>
    <span title="${{l}}">${{l.length>28?l.slice(0,26)+'…':l}}</span>`;
  div.querySelector('input').addEventListener('change', e => {{
    if(e.target.checked) visibleLits.add(l); else visibleLits.delete(l);
    document.getElementById('chk-all').indeterminate = true;
    redraw();
  }});
  litBox.appendChild(div);
}});

function toggleAllLit(chk) {{
  document.querySelectorAll('.lit-chk').forEach(c => c.checked = chk.checked);
  if(chk.checked) litList.forEach(l => visibleLits.add(l));
  else visibleLits.clear();
  redraw();
}}

// ── Datos filtrados ───────────────────────────────────────────
let yMin = 0, yMax = 620;
function getFiltered() {{
  const af = parseFloat(document.getElementById('anomaly-filter').value) || 0;
  return RAW.filter(r =>
    r.Y_ppm >= yMin && r.Y_ppm <= yMax &&
    r.Y_ppm >= af &&
    visibleLits.has(r.Litology_STD)
  );
}}

// ── Rangos globales ──────────────────────────────────────────
const allE = RAW.map(r=>r.UTM_E), allN = RAW.map(r=>r.UTM_N);
const extE = [Math.min(...allE), Math.max(...allE)];
const extN = [Math.min(...allN), Math.max(...allN)];
const allY = RAW.map(r=>r.Y_ppm).filter(v=>v>0);
const colorMin = 0, colorMax = Math.percentile ? Math.percentile(allY,98) : 300;
const CMAX = 300;

// ── Coordenadas ──────────────────────────────────────────────
function toScreen(e, n) {{
  const cx = canvas.width/2, cy = canvas.height/2;
  const mx = extE[0] + (extE[1]-extE[0])/2;
  const my = extN[0] + (extN[1]-extN[0])/2;
  const scaleBase = Math.min(canvas.width/(extE[1]-extE[0]), canvas.height/(extN[1]-extN[0])) * 0.88;
  const sc = scaleBase * transform.scale;
  return [
    cx + (e - mx)*sc + transform.x,
    cy - (n - my)*sc + transform.y
  ];
}}

function toWorld(px, py) {{
  const cx = canvas.width/2, cy = canvas.height/2;
  const mx = extE[0] + (extE[1]-extE[0])/2;
  const my = extN[0] + (extN[1]-extN[0])/2;
  const scaleBase = Math.min(canvas.width/(extE[1]-extE[0]), canvas.height/(extN[1]-extN[0])) * 0.88;
  const sc = scaleBase * transform.scale;
  return [
    mx + (px - cx - transform.x)/sc,
    my - (py - cy - transform.y)/sc
  ];
}}

// ── Resize ───────────────────────────────────────────────────
function resize() {{
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width || window.innerWidth - 300;
  canvas.height = rect.height || window.innerHeight - 60;
  redraw();
}}
window.addEventListener('resize', resize);
setTimeout(resize, 50);
setTimeout(resize, 200);
setTimeout(resize, 600);

// ── Dibujar ──────────────────────────────────────────────────
function redraw() {{
  if(!canvas.width) return;
  ctx.clearRect(0,0,canvas.width,canvas.height);

  // Fondo
  ctx.fillStyle = '#0a0e14';
  ctx.fillRect(0,0,canvas.width,canvas.height);

  // Grid
  if(showGrid) drawGrid();

  const data = getFiltered();
  const ptSize = parseInt(document.getElementById('pt-size').value);
  const pal = PALETTES[document.getElementById('colormap-sel').value];

  // Borde de muestras seleccionadas primero
  data.forEach(r => {{
    const [x,y] = toScreen(r.UTM_E, r.UTM_N);
    const col = getColor(r.Y_ppm, colorMin, CMAX, pal);
    ctx.beginPath();
    ctx.arc(x, y, ptSize, 0, Math.PI*2);
    ctx.fillStyle = col;
    ctx.globalAlpha = 0.85;
    ctx.fill();
    if(r.Y_ppm >= 100) {{
      ctx.strokeStyle = 'rgba(255,255,255,0.6)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }}
  }});

  // Resaltar seleccionada
  if(selectedSample) {{
    const [x,y] = toScreen(selectedSample.UTM_E, selectedSample.UTM_N);
    ctx.globalAlpha = 1;
    ctx.beginPath();
    ctx.arc(x,y,ptSize+5,0,Math.PI*2);
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(x,y,ptSize+2,0,Math.PI*2);
    ctx.strokeStyle = '#4fc3f7';
    ctx.lineWidth = 2;
    ctx.stroke();
  }}

  ctx.globalAlpha = 1;

  // Stats
  document.getElementById('stat-n').textContent = data.length.toLocaleString();
  const yVals = data.map(r=>r.Y_ppm);
  if(yVals.length > 0) {{
    document.getElementById('stat-mean').textContent = (yVals.reduce((a,b)=>a+b,0)/yVals.length).toFixed(1);
    const sorted = [...yVals].sort((a,b)=>a-b);
    document.getElementById('stat-med').textContent = sorted[Math.floor(sorted.length/2)].toFixed(1);
    document.getElementById('stat-max').textContent = Math.max(...yVals).toFixed(1);
  }}
  document.getElementById('sb-vis').textContent = data.length.toLocaleString();
  document.getElementById('sb-zoom').textContent = transform.scale.toFixed(2)+'x';
}}

function drawGrid() {{
  ctx.strokeStyle = 'rgba(255,255,255,0.04)';
  ctx.lineWidth = 1;
  ctx.setLineDash([4,4]);
  // Lineas verticales
  for(let e=Math.ceil(extE[0]/1000)*1000; e<=extE[1]; e+=5000) {{
    const [x,] = toScreen(e, extN[0]);
    ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,canvas.height); ctx.stroke();
    ctx.fillStyle='rgba(255,255,255,0.2)'; ctx.font='10px monospace';
    ctx.fillText(e.toLocaleString(), x+2, 12);
  }}
  // Lineas horizontales
  for(let n=Math.ceil(extN[0]/1000)*1000; n<=extN[1]; n+=5000) {{
    const [,y] = toScreen(extE[0], n);
    ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(canvas.width,y); ctx.stroke();
    ctx.fillStyle='rgba(255,255,255,0.2)'; ctx.font='10px monospace';
    ctx.fillText(n.toLocaleString(), 2, y-2);
  }}
  ctx.setLineDash([]);
}}

// ── Interacciones ─────────────────────────────────────────────
canvas.addEventListener('mousedown', e => {{
  dragging = true;
  dragStart = [e.clientX - canvas.getBoundingClientRect().left, e.clientY - canvas.getBoundingClientRect().top];
  dragTf = {{...transform}};
}});

canvas.addEventListener('mousemove', e => {{
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  const [we, wn] = toWorld(mx, my);
  document.getElementById('sb-e').textContent = Math.round(we).toLocaleString();
  document.getElementById('sb-n').textContent = Math.round(wn).toLocaleString();

  if(dragging) {{
    transform.x = dragTf.x + (mx - dragStart[0]);
    transform.y = dragTf.y + (my - dragStart[1]);
    redraw(); return;
  }}

  // Hover tooltip
  const data = getFiltered();
  const ptSize = parseInt(document.getElementById('pt-size').value);
  let nearest = null, nearDist = (ptSize+8)**2;
  data.forEach(r => {{
    const [sx,sy] = toScreen(r.UTM_E, r.UTM_N);
    const d2 = (sx-mx)**2 + (sy-my)**2;
    if(d2 < nearDist) {{ nearDist=d2; nearest=r; }}
  }});

  if(nearest) {{
    tooltip.style.display = 'block';
    tooltip.style.left = (mx+14)+'px';
    tooltip.style.top = (my-10)+'px';
    document.getElementById('tt-sample').textContent = nearest.Sample;
    document.getElementById('tt-y').textContent = nearest.Y_ppm.toFixed(2)+' ppm';
    document.getElementById('tt-y').style.color = nearest.Y_ppm>100?'#ff5722':nearest.Y_ppm>50?'#ffa726':'#66bb6a';
    document.getElementById('tt-ce').textContent = nearest.Ce_ppm!==''?nearest.Ce_ppm.toFixed(1)+' ppm':'—';
    document.getElementById('tt-th').textContent = nearest.Th_ppm!==''?nearest.Th_ppm.toFixed(1)+' ppm':'—';
    document.getElementById('tt-fe').textContent = nearest.Fe__!==''?nearest.Fe__.toFixed(2)+'%':'—';
    document.getElementById('tt-lit').textContent = nearest.Litology_STD;
    canvas.style.cursor = 'pointer';
  }} else {{
    tooltip.style.display = 'none';
    canvas.style.cursor = dragging?'grabbing':'crosshair';
  }}
}});

canvas.addEventListener('mouseup', e => {{
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  const moved = Math.abs(mx-dragStart[0]) + Math.abs(my-dragStart[1]);
  dragging = false;

  if(moved < 4) {{
    // Click = seleccionar
    const data = getFiltered();
    const ptSize = parseInt(document.getElementById('pt-size').value);
    let nearest = null, nearDist = (ptSize+10)**2;
    data.forEach(r => {{
      const [sx,sy] = toScreen(r.UTM_E, r.UTM_N);
      const d2 = (sx-mx)**2 + (sy-my)**2;
      if(d2 < nearDist) {{ nearDist=d2; nearest=r; }}
    }});
    if(nearest) showDetail(nearest);
  }}
}});

canvas.addEventListener('wheel', e => {{
  e.preventDefault();
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  const factor = e.deltaY < 0 ? 1.15 : 0.87;
  const [we, wn] = toWorld(mx, my);
  transform.scale *= factor;
  transform.scale = Math.max(0.2, Math.min(50, transform.scale));
  const [nx, ny] = toScreen(we, wn);
  transform.x += mx - nx;
  transform.y += my - ny;
  redraw();
}}, {{passive:false}});

// ── Detalle muestra ───────────────────────────────────────────
function showDetail(r) {{
  selectedSample = r;
  document.getElementById('no-selection').style.display='none';
  const det = document.getElementById('sample-detail');
  det.style.display='block';
  const yClass = r.Y_ppm>100?'high':r.Y_ppm>50?'med':'low';
  det.innerHTML = `
    <h4>📍 ${{r.Sample}}</h4>
    <div class="info-row"><span class="label">Litología</span><span class="value" style="font-size:11px;color:${{litColors[r.Litology_STD]}}">${{r.Litology_STD}}</span></div>
    <div class="info-row"><span class="label">UTM E</span><span class="value">${{r.UTM_E.toLocaleString()}}</span></div>
    <div class="info-row"><span class="label">UTM N</span><span class="value">${{r.UTM_N.toLocaleString()}}</span></div>
    <div class="info-row"><span class="label">Cota (m)</span><span class="value">${{r.COTA_M||'—'}}</span></div>
    <div style="margin:8px 0 4px;font-size:11px;color:#546e7a;text-transform:uppercase">— Tierras Raras —</div>
    <div class="info-row"><span class="label">Y (ppm)</span><span class="value ${{yClass}}">${{r.Y_ppm.toFixed(2)}}</span></div>
    <div class="info-row"><span class="label">Y ponderado</span><span class="value">${{r.Y_pond!==''?r.Y_pond.toFixed(3):'—'}}</span></div>
    <div class="info-row"><span class="label">Ce (ppm)</span><span class="value">${{r.Ce_ppm!==''?r.Ce_ppm.toFixed(2):'—'}}</span></div>
    <div class="info-row"><span class="label">La (ppm)</span><span class="value">${{r.La_ppm!==''?r.La_ppm.toFixed(2):'—'}}</span></div>
    <div class="info-row"><span class="label">Th (ppm)</span><span class="value">${{r.Th_ppm!==''?r.Th_ppm.toFixed(2):'—'}}</span></div>
    <div class="info-row"><span class="label">Nd (ppm)</span><span class="value">${{r.Nd_ppm!==''?r.Nd_ppm.toFixed(2):'—'}}</span></div>
    <div style="margin:8px 0 4px;font-size:11px;color:#546e7a;text-transform:uppercase">— Elementos Mayores —</div>
    <div class="info-row"><span class="label">Fe (%)</span><span class="value">${{r.Fe__!==''?r.Fe__.toFixed(4):'—'}}</span></div>
    <div class="info-row"><span class="label">Ti (%)</span><span class="value">${{r.Ti__!==''?r.Ti__.toFixed(4):'—'}}</span></div>
    ${{r.FLAG_OUTLIER?`<div style="margin-top:8px;padding:6px;background:#2a1a0a;border:1px solid #5d4037;border-radius:4px;font-size:11px;color:#ffa726">⚠ ${{r.FLAG_OUTLIER}}</div>`:''}}
    ${{r.FLAG_DUPLICADO?`<div style="margin-top:4px;padding:6px;background:#1a1a2a;border:1px solid #3949ab;border-radius:4px;font-size:11px;color:#7986cb">🔁 ${{r.FLAG_DUPLICADO}}</div>`:''}}
  `;
  redraw();
}}

// ── Controles ─────────────────────────────────────────────────
function updateYFilter() {{
  yMin = parseFloat(document.getElementById('y-min').value);
  yMax = parseFloat(document.getElementById('y-max').value);
  document.getElementById('y-min-val').textContent = yMin;
  document.getElementById('y-max-val').textContent = yMax;
  redraw();
}}

function resetView() {{
  transform = {{x:0,y:0,scale:1}};
  redraw();
}}

function zoom(f) {{
  transform.scale = Math.max(0.2, Math.min(50, transform.scale*f));
  redraw();
}}

function toggleGrid() {{
  showGrid = !showGrid;
  redraw();
}}

// Actualizar leyenda segun paleta
document.getElementById('colormap-sel').addEventListener('change', () => {{
  const pal = PALETTES[document.getElementById('colormap-sel').value];
  document.getElementById('legend-bar').style.background =
    `linear-gradient(to right, ${{pal.join(',')}})`;
  redraw();
}});
</script>
</body>
</html>"""

outpath = os.path.join(OUTDIR, "visor_Y_ppm.html")
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Visor generado: {outpath}")
print(f"Tamaño: {os.path.getsize(outpath)/1024:.0f} KB")
