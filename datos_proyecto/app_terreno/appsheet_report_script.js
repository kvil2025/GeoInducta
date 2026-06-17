/**
 * Google Apps Script para automatizar la generación y envío del 
 * "Informe Técnico de Terreno Diario" desde Google Sheets (AppSheet).
 * 
 * Instrucciones:
 * 1. Abre tu hoja de Google Sheets.
 * 2. Ve a Extensiones -> Apps Script.
 * 3. Borra el código existente y pega este script.
 * 4. Cambia el correo de destino en la variable 'CORREO_DESTINO'.
 * 5. Guarda y puedes ejecutar 'generarInformeDiario' manualmente o crear un activador diario.
 */

// CONFIGURACIÓN DE DESTINATARIOS
const CORREO_DESTINO = "geologo.responsable@inducta.cl"; // Cambia por tu correo o el del cliente
const NOMBRE_PROYECTO = "Inducta - Exploración Quinhue";

function generarInformeDiario() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Registro_Terreno");
  if (!sheet) {
    Logger.log("La hoja 'Registro_Terreno' no existe.");
    return;
  }
  
  const rawData = sheet.getDataRange().getValues();
  if (rawData.length <= 1) {
    Logger.log("No hay registros en la base de datos.");
    return;
  }
  
  // Encabezados
  const headers = rawData[0];
  
  // Obtener fecha de hoy en formato local (YYYY-MM-DD)
  const hoyStr = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd");
  
  // Filtrar los registros de hoy
  const registrosHoy = [];
  
  for (let i = 1; i < rawData.length; i++) {
    const fila = rawData[i];
    const fechaHoraVal = fila[8]; // Columna 9 (Fecha_Hora)
    
    if (fechaHoraVal) {
      let fechaFilaStr = "";
      if (fechaHoraVal instanceof Date) {
        fechaFilaStr = Utilities.formatDate(fechaHoraVal, Session.getScriptTimeZone(), "yyyy-MM-dd");
      } else {
        fechaFilaStr = String(fechaHoraVal).substring(0, 10);
      }
      
      if (fechaFilaStr === hoyStr) {
        // Crear objeto llave-valor
        const registro = {};
        headers.forEach((header, index) => {
          registro[header] = fila[index];
        });
        registrosHoy.push(registro);
      }
    }
  }
  
  if (registrosHoy.length === 0) {
    Logger.log("No se encontraron registros ingresados en la fecha de hoy: " + hoyStr);
    return;
  }
  
  // Generar HTML del correo
  const htmlBody = construirHtmlReporte(registrosHoy, hoyStr);
  
  // Enviar Correo
  MailApp.sendEmail({
    to: CORREO_DESTINO,
    subject: `Reporte Diario de Terreno (${hoyStr}) - Proyecto ${NOMBRE_PROYECTO}`,
    htmlBody: htmlBody
  });
  
  Logger.log("¡Informe diario enviado con éxito al correo: " + CORREO_DESTINO);
}

/**
 * Función para traducir los números 1-5 a la simbología geológica original en el reporte impreso
 */
function traductoresIntensidad(val) {
  const str = String(val);
  if (str.startsWith("5")) return "++";
  if (str.startsWith("4")) return "+";
  if (str.startsWith("3")) return "±";
  if (str.startsWith("2")) return "-";
  if (str.startsWith("1")) return "--";
  return val;
}

/**
 * Construcción del cuerpo del reporte en HTML
 */
function construirHtmlReporte(registros, fecha) {
  let tablaFilas = "";
  
  registros.forEach(r => {
    // Decodificar valores para el reporte
    const caol = traductoresIntensidad(r["Caolinizacion_Caol"]);
    const oxfe = traductoresIntensidad(r["Oxidos_Fe_OxFe"]);
    const gps = r["Coordenada_GPS"] || "Sin Coordenadas";
    const obs = r["Observaciones"] || "Sin observaciones adicionales.";
    const muest = r["Muestra_ID"] || "—";
    
    tablaFilas += `
      <tr>
        <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold; color: #2c3e50;">${r["Estacion_CP"]}</td>
        <td style="border: 1px solid #ddd; padding: 8px;">${r["Intervalo"]}</td>
        <td style="border: 1px solid #ddd; padding: 8px;">${muest}</td>
        <td style="border: 1px solid #ddd; padding: 8px;">${r["Litologia"]}</td>
        <td style="border: 1px solid #ddd; padding: 8px; font-family: monospace;">${r["Mineralogia_Siglas"]}</td>
        <td style="border: 1px solid #ddd; padding: 8px; text-align: center; font-weight: bold; background-color: #fcfcfc;">${r["Horizonte"]}</td>
        <td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: #d35400; font-weight: bold;">${caol}</td>
        <td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: #c0392b; font-weight: bold;">${oxfe}</td>
        <td style="border: 1px solid #ddd; padding: 8px; font-size: 0.9em; font-style: italic; color: #555;">${obs}</td>
        <td style="border: 1px solid #ddd; padding: 8px; font-size: 0.85em; font-family: monospace;">${gps}</td>
      </tr>
    `;
  });

  return `
    <div style="font-family: Arial, sans-serif; max-width: 900px; margin: auto; border: 1px solid #eee; padding: 20px; box-shadow: 2px 2px 12px rgba(0,0,0,0.05); border-radius: 8px;">
      <div style="background-color: #2c3e50; padding: 15px; border-radius: 6px; text-align: center;">
        <h2 style="color: white; margin: 0; font-size: 1.5em; letter-spacing: 1px;">INFORME DIARIO DE TERRENO</h2>
        <p style="color: #bdc3c7; margin: 5px 0 0 0; font-size: 0.9em;">Proyecto: ${NOMBRE_PROYECTO} | Fecha: ${fecha}</p>
      </div>
      
      <p style="color: #333; margin-top: 20px;">
        Estimado equipo,<br><br>
        A continuación se consolidan las observaciones geológicas y muestras recolectadas durante el día de hoy mediante la aplicación móvil:
      </p>
      
      <table style="width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 0.95em;">
        <thead>
          <tr style="background-color: #f2f2f2; border-bottom: 2px solid #2c3e50;">
            <th style="border: 1px solid #ddd; padding: 10px; text-align: left; color: #2c3e50;">Estación</th>
            <th style="border: 1px solid #ddd; padding: 10px; text-align: left; color: #2c3e50;">Intervalo</th>
            <th style="border: 1px solid #ddd; padding: 10px; text-align: left; color: #2c3e50;">Muestra ID</th>
            <th style="border: 1px solid #ddd; padding: 10px; text-align: left; color: #2c3e50;">Litología</th>
            <th style="border: 1px solid #ddd; padding: 10px; text-align: left; color: #2c3e50;">Mineralogía</th>
            <th style="border: 1px solid #ddd; padding: 10px; text-align: center; color: #2c3e50;">Horizonte</th>
            <th style="border: 1px solid #ddd; padding: 10px; text-align: center; color: #2c3e50;">Caol</th>
            <th style="border: 1px solid #ddd; padding: 10px; text-align: center; color: #2c3e50;">OxFe</th>
            <th style="border: 1px solid #ddd; padding: 10px; text-align: left; color: #2c3e50;">Observaciones de Terreno (Dictadas)</th>
            <th style="border: 1px solid #ddd; padding: 10px; text-align: left; color: #2c3e50;">Ubicación GPS</th>
          </tr>
        </thead>
        <tbody>
          ${tablaFilas}
        </tbody>
      </table>
      
      <div style="margin-top: 25px; font-size: 0.85em; color: #7f8c8d; border-top: 1px solid #eee; padding-top: 10px;">
        *Este informe fue autogenerado mediante la integración de la base de datos Google Sheets y Google Apps Script.
        Responsable de ingreso: Geólogo de Turno (${registros[0]["Geologo"] || "Gro"}).
      </div>
    </div>
  `;
}
