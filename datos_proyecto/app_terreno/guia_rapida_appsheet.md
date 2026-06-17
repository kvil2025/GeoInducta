# 🪨 Guía Rápida: Tu App de Terreno en 15 Minutos

Este documento te guiará paso a paso para configurar tu app de captura geológica de terreno para el proyecto **Inducta / Quinhue** en Chile.

---

## ¿Qué tendrás al final?

Una aplicación móvil nativa en tu celular (Android/iOS) que:
- Te guía paso a paso por cada dato de la estación (formulario tipo Wizard).
- Captura las coordenadas GPS de forma automática.
- Tiene botones táctiles gigantes con la escala de intensidad geológica `1(--)` → `5(++)`.
- Permite dictar observaciones por voz usando el micrófono del celular.
- Funciona sin señal de internet/celular y se sincroniza sola al volver a la red.
- Genera y envía por correo un informe técnico diario profesional automáticamente a las 18:00 hrs.

---

## Paso 1: Sube el Excel a Google Drive (2 min)

1. Abre [drive.google.com](https://drive.google.com) con tu cuenta de Google.
2. Haz clic en **`+ Nuevo`** → **`Subir archivo`**.
3. Selecciona el archivo **`Base_Datos_AppSheet_FINAL.xlsx`** de tu carpeta.
4. Cuando se suba, haz **doble clic** sobre él en Drive para abrir la vista previa.
5. Haz clic en el menú superior: **`Archivo`** → **`Guardar como Hoja de cálculo de Google`**.
6. Esto creará una copia en formato nativo de Sheets (con el ícono verde). Cierra el archivo .xlsx original para evitar confusiones.

---

## Paso 2: Crea la App en AppSheet (1 min)

1. Dentro de tu nueva Hoja de cálculo de Google, ve al menú superior:
   **`Extensiones`** → **`AppSheet`** → **`Crear una aplicación`**.
2. Inicia sesión con tu misma cuenta de Google.
3. En unos segundos, se cargará el editor de AppSheet con un prototipo de tu app ya funcionando.

---

## Paso 3: Configura las columnas como botones (5 min)

Ve a la barra lateral izquierda del editor de AppSheet: **`Data`** → **`Columns`** → expande la tabla **`Registro_Terreno`**.

Configura los tipos de datos e inputs de las siguientes columnas:

| Columna | Type | Input Mode / Configuración | Required | Initial Value |
|---|---|---|---|---|
| `Estacion_CP` | `Text` | ID único de estación | ✅ | — |
| `Muestra_ID` | `Text` | ID de muestra física | ✅ | — |
| `Intervalo` | `Text` | ej. (0-1) m | ✅ | — |
| `Sector` | `Enum` | Valores: `Este`, `Oeste`. Input Mode: `Buttons` | ✅ | — |
| `Litologia` | `Enum` | Valores: `Granito`, `Pegmatita`, `Granito con stockwork`, `Brecha`, `Otro`. Input Mode: `Buttons` | ✅ | — |
| `Mineralogia_Siglas` | `EnumList` | Valores: `Qz`, `bt`, `Msc`, `Kfs`, `Pl`, `Qz+bt`, `Qz+Msc`, `Qz+bt+Msc`. Input Mode: `Buttons` | — | — |
| `Horizonte` | `Enum` | Valores: `UP`, `LP`, `US`, `LS`, `LP-US`, `US/LP`, `N/A`. Input Mode: `Buttons` | ✅ | — |
| `Caolinizacion_Caol` | `Enum` | Valores: `5 (++)`, `4 (+)`, `3 (±)`, `2 (-)`, `1 (--)`. Input Mode: `Buttons` | ✅ | — |
| `Oxidos_Fe_OxFe` | `Enum` | Valores: `5 (++)`, `4 (+)`, `3 (±)`, `2 (-)`, `1 (--)`. Input Mode: `Buttons` | ✅ | — |
| `Estructuras` | `Enum` | Valores: `Stockwork Qz+Msc`, `Pegmatita intruida`, `Cuerpo Pegmatitico`, `Sin estructura singular`, `Otra`. Input Mode: `Buttons` | — | — |
| `Fecha` | `Date` | Captura automática de fecha | ✅ | `TODAY()` |
| `Hora` | `Time` | Captura automática de hora | — | `NOW()` |
| `Coordenada_GPS` | `LatLong` | Captura automática de posición celular | — | `HERE()` |
| `UTM_Este` | `Decimal` | Ingreso manual de coordenada X si se requiere | — | — |
| `UTM_Norte` | `Decimal` | Ingreso manual de coordenada Y si se requiere | — | — |
| `Elevacion_m` | `Decimal` | Altura | — | — |
| `Foto_URL` | `Image` | Activa la cámara del celular | — | — |
| `Observaciones` | `LongText` | Campo largo. Soporta dictado por voz del teclado | — | — |
| `Geologo` | `Text` | Siglas del geólogo (ej. "Gro") | — | `"Gro"` |
| `Estado_Sync` | `Text` | Control de sincronización interna | — | `"Pendiente"` |

> 💡 **Tip**: Para que `Coordenada_GPS` obtenga la ubicación automáticamente en terreno, asegúrate de colocar `HERE()` en la casilla **Initial Value** de esa columna.

---

## Paso 4: Activa el Wizard (Formulario Paso a Paso) (1 min)

1. En el editor de AppSheet, ve a la pestaña **`App`** (o `UX` según la versión) → **`Views`**.
2. Selecciona la vista **`Registro_Terreno_Form`**.
3. En la configuración a la derecha, busca el campo **`Form page navigation`** y cámbialo de *Standard* a **`Wizard`**.
4. Para agrupar los datos en pestañas sucesivas, introduce elementos de tipo **Page Header** (se configuran en `Data -> Columns` agregando filas de tipo `Show` con categoría `Page_Header` si quieres una separación estricta, o simplemente usando la organización del Wizard en AppSheet).

---

## Paso 5: Activa el soporte Offline (1 min)

1. Ve a **`Settings`** → **`Offline & Sync`**.
2. Marca las siguientes opciones:
   - ✅ **The app can start when offline** (permite abrir la app sin internet).
   - ✅ **Store content for offline use** (guarda los datos localmente).
   - ✅ **Automatic updates** (sube los cambios al servidor apenas detecte señal en segundo plano).
3. Presiona **`Save`** en la esquina superior derecha.

---

## Paso 6: Instala el script de informes automáticos (3 min)

1. Abre tu hoja de Google Sheets en el navegador.
2. Ve al menú superior: **`Extensiones`** → **`Apps Script`**.
3. Elimina cualquier línea de código existente en el archivo `Código.gs`.
4. Abre tu archivo local **`appsheet_completo.js`**, copia todo su contenido y pégalo en el editor de Apps Script.
5. Modifica la variable `CORREO_DESTINO` en la línea 15 con tu dirección de correo electrónico real.
6. Presiona el ícono de **`Guardar`** (diskette).
7. En el selector de funciones (arriba), selecciona la función **`setup`** y haz clic en **`Ejecutar`** (▶️).
8. Acepta los permisos de seguridad de Google.
9. Listo, esto creará automáticamente la carpeta en tu Google Drive y programará el envío diario automático.

---

## Paso 7: Instala la app en tu teléfono (2 min)

1. En el editor de AppSheet, haz clic en el botón **`Share`** en la parte superior derecha.
2. Escribe tu correo electrónico o el de tus geólogos y envíales la invitación.
3. Abre el correo desde tu teléfono móvil y presiona el botón **`Install App`**.
4. Sigue los pasos en pantalla para descargar la aplicación base **AppSheet** de tu tienda de aplicaciones (Google Play / App Store) y abrir tu app de terreno.

---

## ¿Cómo usar la app en terreno?
1. Abre la app en tu celular y presiona el botón **`+`** (Nueva Estación).
2. **Pestaña 1**: Ingresa el ID de la estación, muestra e intervalo.
3. **Pestaña 2**: Selecciona la litología, mineralogía y horizonte con botones directos.
4. **Pestaña 3**: Toca la intensidad de la caolinización y óxidos de hierro (escala 1 a 5).
5. **Pestaña 4**: Confirma el GPS capturado por el sensor y toma una foto de la estación.
6. **Pestaña 5**: Toca el micrófono del teclado de tu celular y dicta las observaciones de campo detalladas.
7. Haz clic en **`Save`** para guardar. La app almacena todo offline y lo sube cuando vuelvas a tener señal. A las 18:00 hrs recibirás el informe en tu correo.
