/**
 * ============================================================
 *  SCRIPT COMPLETO - PROYECTO INDUCTA · EXPLORACIÓN QUINHUE
 *  Google Apps Script para Automatización de Informes Diarios
 * ============================================================
 *  INSTRUCCIONES:
 *  1. Abre tu Google Sheets → Extensiones → Apps Script
 *  2. Borra todo el código existente y pega este script
 *  3. Guarda (Ctrl+S) y ejecuta la función "setup()" UNA SOLA VEZ
 *  4. ¡Listo! El informe se enviará automáticamente cada día a las 18:00 hrs
 * ============================================================
 */

// ─── CONFIGURACIÓN GLOBAL ────────────────────────────────────
const CONFIG = {
  CORREO_DESTINO:   'geologo@inducta.cl',       // ← Cambia por tu correo
  CORREO_CC:        '',                          // ← Opcional: copia a otro correo
  NOMBRE_PROYECTO:  'Inducta - Exploración Quinhue',
  NOMBRE_HOJA:      'Registro_Terreno',
  CARPETA_INFORMES: 'Informes_Diarios_Inducta',
  ZONA_HORARIA:     'America/Santiago',
  HORA_ENVIO:       18                           // Hora de envío automático (18:00)
};

// ─── COLUMNAS (deben coincidir con el Excel) ─────────────────
const COL = {
  ESTACION:    0,   // Estacion_CP
  MUESTRA:     1,   // Muestra_ID
  INTERVALO:   2,   // Intervalo
  SECTOR:      3,   // Sector
  LITOLOGIA:   4,   // Litologia
  MINERALOGIA: 5,   // Mineralogia_Siglas
  HORIZONTE:   6,   // Horizonte
  CAOL:        7,   // Caolinizacion_Caol
  OXFE:        8,   // Oxidos_Fe_OxFe
  ESTRUCTURAS: 9,   // Estructuras
  FECHA:       10,  // Fecha
  HORA:        11,  // Hora
  GPS:         12,  // Coordenada_GPS
  UTM_E:       13,  // UTM_Este
  UTM_N:       14,  // UTM_Norte
  ELEV:        15,  // Elevacion_m
  FOTO:        16,  // Foto_URL
  OBS:         17,  // Observaciones
  GEOLOGO:     18,  // Geologo
  SYNC:        19   // Estado_Sync
};


// ════════════════════════════════════════════════════════════════
//  1. MENÚ PERSONALIZADO
// ════════════════════════════════════════════════════════════════
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('⛏️ Inducta Geología')
    .addItem('📋 Generar Informe del Día', 'generarInformeDiario')
    .addItem('🔍 Informe por Estación', 'generarInformePorEstacion')
    .addSeparator()
    .addItem('📊 Ver Resumen del Día', 'verResumenDia')
    .addItem('✅ Marcar Todo como Sincronizado', 'marcarSincronizado')
    .addItem('🧹 Limpiar Registros Duplicados', 'limpiarDuplicados')
    .addSeparator()
    .addItem('⚙️ Configuración Inicial (ejecutar 1 vez)', 'setup')
    .addToUi();
}


// ════════════════════════════════════════════════════════════════
//  2. CONFIGURACIÓN INICIAL (ejecutar solo una vez)
// ════════════════════════════════════════════════════════════════
function setup() {
  // Crear carpeta de informes en Google Drive si no existe
  const folders = DriveApp.getFoldersByName(CONFIG.CARPETA_INFORMES);
  if (!folders.hasNext()) {
    DriveApp.createFolder(CONFIG.CARPETA_INFORMES);
    Logger.log('Carpeta creada: ' + CONFIG.CARPETA_INFORMES);
  }

  // Crear activador diario automático si no existe
  const triggers = ScriptApp.getProjectTriggers();
  const yaExiste = triggers.some(t => t.getHandlerFunction() === 'generarInformeDiario');
  if (!yaExiste) {
    ScriptApp.newTrigger('generarInformeDiario')
      .timeBased()
      .atHour(CONFIG.HORA_ENVIO)
      .everyDays(1)
      .create();
    Logger.log('Activador diario creado para las ' + CONFIG.HORA_ENVIO + ':00 hrs');
  }

  SpreadsheetApp.getUi().alert(
    '✅ Configuración completada',
    'La aplicación está lista.\n\n' +
    '• Carpeta de informes: "' + CONFIG.CARPETA_INFORMES + '" creada en Google Drive\n' +
    '• Informe diario automático configurado para las ' + CONFIG.HORA_ENVIO + ':00 hrs\n' +
    '• Correo de destino: ' + CONFIG.CORREO_DESTINO + '\n\n' +
    'Puedes usar el menú "⛏️ Inducta Geología" para generar informes manualmente.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}


// ════════════════════════════════════════════════════════════════
//  3. INFORME DIARIO PRINCIPAL
// ════════════════════════════════════════════════════════════════
function generarInformeDiario() {
  const ss     = SpreadsheetApp.getActiveSpreadsheet();
  const sheet  = ss.getSheetByName(CONFIG.NOMBRE_HOJA);

  if (!sheet) {
    SpreadsheetApp.getUi().alert('Error: No se encontró la hoja "' + CONFIG.NOMBRE_HOJA + '".');
    return;
  }

  const data = sheet.getDataRange().getValues();
  if (data.length <= 1) {
    SpreadsheetApp.getUi().alert('No hay registros en la base de datos.');
    return;
  }

  const hoy = Utilities.formatDate(new Date(), CONFIG.ZONA_HORARIA, 'yyyy-MM-dd');
  const registrosHoy = [];

  for (let i = 1; i < data.length; i++) {
    const fila = data[i];
    const fechaVal = fila[COL.FECHA];
    let fechaStr = '';

    if (fechaVal instanceof Date) {
      fechaStr = Utilities.formatDate(fechaVal, CONFIG.ZONA_HORARIA, 'yyyy-MM-dd');
    } else {
      fechaStr = String(fechaVal || '').substring(0, 10);
    }

    if (fechaStr === hoy) {
      registrosHoy.push({
        estacion:    fila[COL.ESTACION]    || '—',
        muestra:     fila[COL.MUESTRA]     || '—',
        intervalo:   fila[COL.INTERVALO]   || '—',
        sector:      fila[COL.SECTOR]      || '—',
        litologia:   fila[COL.LITOLOGIA]   || '—',
        mineralogia: fila[COL.MINERALOGIA] || '—',
        horizonte:   fila[COL.HORIZONTE]   || '—',
        caol:        traductorIntensidad(fila[COL.CAOL]),
        oxfe:        traductorIntensidad(fila[COL.OXFE]),
        estructuras: fila[COL.ESTRUCTURAS] || '—',
        hora:        fila[COL.HORA]        || '—',
        gps:         fila[COL.GPS]         || 'Sin coordenadas',
        observaciones: fila[COL.OBS]       || '',
        geologo:     fila[COL.GEOLOGO]     || 'Gro'
      });
    }
  }

  if (registrosHoy.length === 0) {
    SpreadsheetApp.getUi().alert('No se encontraron registros con fecha de hoy (' + hoy + ').');
    return;
  }

  // Generar HTML y enviar
  const htmlBody = construirHtmlReporte(registrosHoy, hoy);
  const asunto   = 'Reporte Diario de Terreno (' + hoy + ') — ' + CONFIG.NOMBRE_PROYECTO;

  const mailOptions = { htmlBody: htmlBody };
  if (CONFIG.CORREO_CC) mailOptions.cc = CONFIG.CORREO_CC;
  MailApp.sendEmail(CONFIG.CORREO_DESTINO, asunto, '', mailOptions);

  // Guardar PDF en Drive
  try {
    guardarPdfEnDrive(ss, hoy);
  } catch(e) {
    Logger.log('Advertencia: No se pudo guardar PDF. ' + e.message);
  }

  // Marcar registros como sincronizados
  for (let i = 1; i < data.length; i++) {
    const fila = data[i];
    const fechaVal = fila[COL.FECHA];
    let fechaStr = '';
    if (fechaVal instanceof Date) {
      fechaStr = Utilities.formatDate(fechaVal, CONFIG.ZONA_HORARIA, 'yyyy-MM-dd');
    } else {
      fechaStr = String(fechaVal || '').substring(0, 10);
    }
    if (fechaStr === hoy) {
      sheet.getRange(i + 1, COL.SYNC + 1).setValue('Sincronizado');
    }
  }

  SpreadsheetApp.getActiveSpreadsheet().toast(
    '✅ Informe enviado a ' + CONFIG.CORREO_DESTINO + ' (' + registrosHoy.length + ' registros)',
    '⛏️ Inducta Geología', 5
  );
}


// ════════════════════════════════════════════════════════════════
//  4. TRADUCTOR DE INTENSIDAD (numérico → símbolo geológico)
// ════════════════════════════════════════════════════════════════
function traductorIntensidad(val) {
  const s = String(val || '').trim();
  if (s.startsWith('5')) return '++';
  if (s.startsWith('4')) return '+';
  if (s.startsWith('3')) return '±';
  if (s.startsWith('2')) return '-';
  if (s.startsWith('1')) return '--';
  return s || '—';
}


// ════════════════════════════════════════════════════════════════
//  5. CONSTRUCTOR DEL HTML DEL REPORTE
// ════════════════════════════════════════════════════════════════
function construirHtmlReporte(registros, fecha) {
  const geologo  = registros[0].geologo;
  const nMuestras = registros.filter(r => r.muestra !== '—').length;
  const nEstaciones = new Set(registros.map(r => r.estacion)).size;
  const nEstructuras = registros.filter(r => r.estructuras && r.estructuras !== 'Sin estructura singular' && r.estructuras !== '—').length;

  // Color según intensidad
  function colorIntensidad(simb) {
    const map = {
      '++': '#c0392b', '+': '#e67e22', '±': '#f39c12', '-': '#95a5a6', '--': '#bdc3c7'
    };
    return map[simb] || '#2c3e50';
  }

  let filas = '';
  registros.forEach(r => {
    const colorCaol = colorIntensidad(r.caol);
    const colorOxFe = colorIntensidad(r.oxfe);

    filas += `
      <tr style="border-bottom: 1px solid #ecf0f1;">
        <td style="padding:10px 12px; font-weight:700; color:#1a2f4a; white-space:nowrap;">${r.estacion}</td>
        <td style="padding:10px 12px; white-space:nowrap;">${r.intervalo}</td>
        <td style="padding:10px 12px; font-family:monospace; font-size:12px;">${r.muestra}</td>
        <td style="padding:10px 12px;">${r.litologia}</td>
        <td style="padding:10px 12px; font-family:monospace; font-size:12px;">${r.mineralogia}</td>
        <td style="padding:10px 12px; text-align:center; font-weight:600;">${r.horizonte}</td>
        <td style="padding:10px 12px; text-align:center;">
          <span style="background:${colorCaol}22; color:${colorCaol}; font-weight:800; font-size:14px; padding:3px 8px; border-radius:6px;">${r.caol}</span>
        </td>
        <td style="padding:10px 12px; text-align:center;">
          <span style="background:${colorOxFe}22; color:${colorOxFe}; font-weight:800; font-size:14px; padding:3px 8px; border-radius:6px;">${r.oxfe}</span>
        </td>
        <td style="padding:10px 12px; font-size:11px; color:#7f8c8d; font-style:italic;">${r.estructuras !== '—' && r.estructuras !== 'Sin estructura singular' ? '<strong style="color:#1a2f4a;">⚡ ' + r.estructuras + '</strong>' : r.estructuras}</td>
        <td style="padding:10px 12px; font-size:11px; color:#555; max-width:200px;">${r.observaciones || '<span style="color:#bdc3c7">Sin observaciones</span>'}</td>
        <td style="padding:10px 12px; font-size:10px; font-family:monospace; color:#95a5a6; white-space:nowrap;">${r.gps}</td>
      </tr>
    `;
  });

  return `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body { font-family: Arial, sans-serif; margin: 0; background: #f5f7fa; color: #2c3e50; }
  .container { max-width: 960px; margin: 0 auto; background: white; }
  table { border-collapse: collapse; }
</style>
</head>
<body>
<div class="container">

  <!-- HEADER -->
  <div style="background: linear-gradient(135deg,#1a2f4a,#2c4a6e); padding:30px; text-align:center;">
    <div style="font-size:11px; letter-spacing:2px; color:rgba(255,255,255,0.6); text-transform:uppercase; margin-bottom:6px;">INFORME TÉCNICO DIARIO DE TERRENO</div>
    <h1 style="color:white; margin:0; font-size:22px; font-weight:700;">${CONFIG.NOMBRE_PROYECTO}</h1>
    <p style="color:rgba(255,255,255,0.65); margin:8px 0 0; font-size:13px;">Fecha: ${fecha} · Geólogo: ${geologo}</p>
  </div>

  <!-- RESUMEN ESTADÍSTICO -->
  <div style="display:flex; gap:0; border-bottom:2px solid #ecf0f1;">
    <div style="flex:1; text-align:center; padding:20px; border-right:1px solid #ecf0f1;">
      <div style="font-size:28px; font-weight:800; color:#1a2f4a;">${nMuestras}</div>
      <div style="font-size:11px; color:#7f8c8d; text-transform:uppercase; letter-spacing:1px;">Muestras registradas</div>
    </div>
    <div style="flex:1; text-align:center; padding:20px; border-right:1px solid #ecf0f1;">
      <div style="font-size:28px; font-weight:800; color:#2980b9;">${nEstaciones}</div>
      <div style="font-size:11px; color:#7f8c8d; text-transform:uppercase; letter-spacing:1px;">Estaciones visitadas</div>
    </div>
    <div style="flex:1; text-align:center; padding:20px;">
      <div style="font-size:28px; font-weight:800; color:#e67e22;">${nEstructuras}</div>
      <div style="font-size:11px; color:#7f8c8d; text-transform:uppercase; letter-spacing:1px;">Con estructuras singulares</div>
    </div>
  </div>

  <!-- TABLA PRINCIPAL -->
  <div style="overflow-x:auto; padding:0;">
    <table style="width:100%; font-size:12px;">
      <thead>
        <tr style="background:#1a2f4a; color:white;">
          <th style="padding:12px; text-align:left; font-size:10px; letter-spacing:0.5px; text-transform:uppercase;">Estación</th>
          <th style="padding:12px; text-align:left; font-size:10px; text-transform:uppercase;">Intervalo</th>
          <th style="padding:12px; text-align:left; font-size:10px; text-transform:uppercase;">Muestra ID</th>
          <th style="padding:12px; text-align:left; font-size:10px; text-transform:uppercase;">Litología</th>
          <th style="padding:12px; text-align:left; font-size:10px; text-transform:uppercase;">Mineralogía</th>
          <th style="padding:12px; text-align:center; font-size:10px; text-transform:uppercase;">Hz.</th>
          <th style="padding:12px; text-align:center; font-size:10px; text-transform:uppercase;">Caol</th>
          <th style="padding:12px; text-align:center; font-size:10px; text-transform:uppercase;">OxFe</th>
          <th style="padding:12px; text-align:left; font-size:10px; text-transform:uppercase;">Estructuras</th>
          <th style="padding:12px; text-align:left; font-size:10px; text-transform:uppercase;">Observaciones (Voz/Campo)</th>
          <th style="padding:12px; text-align:left; font-size:10px; text-transform:uppercase;">GPS</th>
        </tr>
      </thead>
      <tbody>
        ${filas}
      </tbody>
    </table>
  </div>

  <!-- LEYENDA -->
  <div style="padding:16px 20px; background:#f8f9fa; border-top:1px solid #ecf0f1; font-size:10px; color:#95a5a6; display:flex; gap:20px; flex-wrap:wrap;">
    <span><strong>Escala Caol / OxFe:</strong></span>
    <span style="color:#c0392b; font-weight:700;">++ (5) Muy fuerte</span>
    <span style="color:#e67e22; font-weight:700;">+ (4) Fuerte</span>
    <span style="color:#f39c12; font-weight:700;">± (3) Moderado</span>
    <span style="color:#95a5a6; font-weight:700;">- (2) Débil</span>
    <span style="color:#bdc3c7; font-weight:700;">-- (1) Nulo</span>
  </div>

  <!-- FOOTER -->
  <div style="padding:16px 20px; text-align:right; border-top:1px solid #ecf0f1; font-size:10px; color:#bdc3c7;">
    ⚡ Generado automáticamente el ${fecha} a las ${new Date().toLocaleTimeString('es-CL')} hrs ·
    Sistema de captura móvil AppSheet + Google Sheets + Apps Script ·
    Proyecto ${CONFIG.NOMBRE_PROYECTO}
  </div>

</div>
</body>
</html>`;
}


// ════════════════════════════════════════════════════════════════
//  6. GUARDAR PDF EN GOOGLE DRIVE
// ════════════════════════════════════════════════════════════════
function guardarPdfEnDrive(ss, fecha) {
  const folders = DriveApp.getFoldersByName(CONFIG.CARPETA_INFORMES);
  const folder  = folders.hasNext() ? folders.next() : DriveApp.createFolder(CONFIG.CARPETA_INFORMES);
  const url     = 'https://docs.google.com/spreadsheets/d/' + ss.getId() + '/export?format=pdf&size=A3&landscape=true&fitw=true&gridlines=false';
  const res     = UrlFetchApp.fetch(url, { headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() } });
  const blob    = res.getBlob().setName('Informe_Terreno_' + fecha + '.pdf');
  folder.createFile(blob);
  Logger.log('PDF guardado en carpeta: ' + CONFIG.CARPETA_INFORMES);
}


// ════════════════════════════════════════════════════════════════
//  7. INFORME POR ESTACIÓN ESPECÍFICA
// ════════════════════════════════════════════════════════════════
function generarInformePorEstacion() {
  const ui       = SpreadsheetApp.getUi();
  const response = ui.prompt('🔍 Informe por Estación', 'Ingresa el ID de la estación (ej: Qui-CA-112):', ui.ButtonSet.OK_CANCEL);
  if (response.getSelectedButton() !== ui.Button.OK) return;

  const estacionBuscar = response.getResponseText().trim().toUpperCase();
  const sheet  = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.NOMBRE_HOJA);
  const data   = sheet.getDataRange().getValues();
  const filas  = [];

  for (let i = 1; i < data.length; i++) {
    if (String(data[i][COL.ESTACION]).toUpperCase() === estacionBuscar) {
      filas.push(data[i]);
    }
  }

  if (filas.length === 0) {
    ui.alert('No se encontraron registros para la estación: ' + estacionBuscar);
    return;
  }

  const registros = filas.map(fila => ({
    estacion:    fila[COL.ESTACION]    || '—',
    muestra:     fila[COL.MUESTRA]     || '—',
    intervalo:   fila[COL.INTERVALO]   || '—',
    sector:      fila[COL.SECTOR]      || '—',
    litologia:   fila[COL.LITOLOGIA]   || '—',
    mineralogia: fila[COL.MINERALOGIA] || '—',
    horizonte:   fila[COL.HORIZONTE]   || '—',
    caol:        traductorIntensidad(fila[COL.CAOL]),
    oxfe:        traductorIntensidad(fila[COL.OXFE]),
    estructuras: fila[COL.ESTRUCTURAS] || '—',
    hora:        fila[COL.HORA]        || '—',
    gps:         fila[COL.GPS]         || 'Sin coordenadas',
    observaciones: fila[COL.OBS]       || '',
    geologo:     fila[COL.GEOLOGO]     || 'Gro'
  }));

  const fecha = Utilities.formatDate(new Date(), CONFIG.ZONA_HORARIA, 'yyyy-MM-dd');
  const html  = HtmlService.createHtmlOutput(construirHtmlReporte(registros, fecha))
    .setWidth(900).setHeight(600);
  ui.showModalDialog(html, '📋 Informe Estación: ' + estacionBuscar);
}


// ════════════════════════════════════════════════════════════════
//  8. VER RESUMEN DEL DÍA (modal interactivo)
// ════════════════════════════════════════════════════════════════
function verResumenDia() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.NOMBRE_HOJA);
  const data  = sheet.getDataRange().getValues();
  const hoy   = Utilities.formatDate(new Date(), CONFIG.ZONA_HORARIA, 'yyyy-MM-dd');

  const registros = [];
  for (let i = 1; i < data.length; i++) {
    const fv  = data[i][COL.FECHA];
    let fs    = '';
    if (fv instanceof Date) fs = Utilities.formatDate(fv, CONFIG.ZONA_HORARIA, 'yyyy-MM-dd');
    else fs = String(fv || '').substring(0, 10);
    if (fs === hoy) registros.push(data[i]);
  }

  if (registros.length === 0) {
    SpreadsheetApp.getUi().alert('No hay registros para hoy (' + hoy + ').');
    return;
  }

  // Estadísticas
  const estaciones  = new Set(registros.map(r => r[COL.ESTACION]));
  const litologias  = {};
  const caolCounts  = {};
  const oxfeCounts  = {};

  registros.forEach(r => {
    const lit  = r[COL.LITOLOGIA] || 'Desconocida';
    const caol = traductorIntensidad(r[COL.CAOL]);
    const oxfe = traductorIntensidad(r[COL.OXFE]);
    litologias[lit]  = (litologias[lit]  || 0) + 1;
    caolCounts[caol] = (caolCounts[caol] || 0) + 1;
    oxfeCounts[oxfe] = (oxfeCounts[oxfe] || 0) + 1;
  });

  let litRows  = Object.entries(litologias).map(([k,v])  => `<tr><td>${k}</td><td><b>${v}</b></td></tr>`).join('');
  let caolRows = Object.entries(caolCounts).map(([k,v])  => `<tr><td><b>${k}</b></td><td>${v}</td></tr>`).join('');
  let oxfeRows = Object.entries(oxfeCounts).map(([k,v])  => `<tr><td><b>${k}</b></td><td>${v}</td></tr>`).join('');

  const html = HtmlService.createHtmlOutput(`
    <style>
      body { font-family: Arial, sans-serif; margin: 0; color: #2c3e50; }
      h2 { background: #1a2f4a; color: white; margin: 0; padding: 14px 20px; font-size: 15px; }
      .grid { display: flex; gap: 16px; padding: 16px; }
      .card { flex: 1; background: #f8f9fa; border-radius: 10px; padding: 14px; }
      .card h4 { margin: 0 0 10px; font-size: 11px; text-transform: uppercase; color: #7f8c8d; letter-spacing: 1px; }
      .big { font-size: 36px; font-weight: 800; color: #1a2f4a; text-align: center; padding: 10px; }
      table { width: 100%; border-collapse: collapse; font-size: 12px; }
      td { padding: 6px 4px; border-bottom: 1px solid #ecf0f1; }
    </style>
    <h2>📊 Resumen del Día — ${hoy}</h2>
    <div class="grid">
      <div class="card"><div class="big">${registros.length}</div><h4>Total Muestras</h4></div>
      <div class="card"><div class="big">${estaciones.size}</div><h4>Estaciones Visitadas</h4></div>
    </div>
    <div class="grid">
      <div class="card">
        <h4>Por Litología</h4>
        <table>${litRows}</table>
      </div>
      <div class="card">
        <h4>Intensidad Caol</h4>
        <table>${caolRows}</table>
      </div>
      <div class="card">
        <h4>Intensidad OxFe</h4>
        <table>${oxfeRows}</table>
      </div>
    </div>
  `).setWidth(700).setHeight(400);

  SpreadsheetApp.getUi().showModalDialog(html, '📊 Resumen del Día');
}


// ════════════════════════════════════════════════════════════════
//  9. MARCAR TODO COMO SINCRONIZADO
// ════════════════════════════════════════════════════════════════
function marcarSincronizado() {
  const sheet  = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.NOMBRE_HOJA);
  const data   = sheet.getDataRange().getValues();
  const hoy    = Utilities.formatDate(new Date(), CONFIG.ZONA_HORARIA, 'yyyy-MM-dd');
  let marcados = 0;

  for (let i = 1; i < data.length; i++) {
    const fv  = data[i][COL.FECHA];
    let fs    = '';
    if (fv instanceof Date) fs = Utilities.formatDate(fv, CONFIG.ZONA_HORARIA, 'yyyy-MM-dd');
    else fs = String(fv || '').substring(0, 10);

    if (fs === hoy && data[i][COL.SYNC] !== 'Sincronizado') {
      sheet.getRange(i + 1, COL.SYNC + 1).setValue('Sincronizado');
      marcados++;
    }
  }

  SpreadsheetApp.getActiveSpreadsheet().toast(`✅ ${marcados} registros marcados como sincronizados`, '⛏️ Inducta', 4);
}


// ════════════════════════════════════════════════════════════════
//  10. LIMPIAR DUPLICADOS
// ════════════════════════════════════════════════════════════════
function limpiarDuplicados() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.NOMBRE_HOJA);
  const data  = sheet.getDataRange().getValues();
  const headers = data[0];
  const vistas  = new Map();
  const rowsToDelete = [];

  for (let i = data.length - 1; i >= 1; i--) {
    const key = [data[i][COL.ESTACION], data[i][COL.MUESTRA], data[i][COL.INTERVALO]].join('|');
    if (vistas.has(key)) {
      rowsToDelete.push(i + 1);
    } else {
      vistas.set(key, true);
    }
  }

  if (rowsToDelete.length === 0) {
    SpreadsheetApp.getUi().alert('✅ No se encontraron duplicados.');
    return;
  }

  // Borrar de abajo hacia arriba para no desplazar índices
  rowsToDelete.sort((a, b) => b - a).forEach(r => sheet.deleteRow(r));
  SpreadsheetApp.getActiveSpreadsheet().toast(`🧹 ${rowsToDelete.length} duplicados eliminados`, '⛏️ Inducta', 4);
}
