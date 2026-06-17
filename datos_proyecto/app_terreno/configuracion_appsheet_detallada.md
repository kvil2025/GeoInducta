# 🛠️ Configuración Técnica Avanzada de AppSheet

Este documento detalla configuraciones técnicas y fórmulas avanzadas para optimizar la aplicación móvil de terreno para el proyecto **Inducta / Quinhue**.

---

## 1. Organización del Formulario Wizard (Pestañas Paso a Paso)

Para lograr que el formulario móvil sea limpio y no requiera scroll vertical interminable, lo organizamos en **5 pantallas sucesivas** (Wizard). 

### Cómo configurar los Page Breaks en AppSheet:
1. En tu Google Sheets, agrega una fila ficticia o utiliza la estructura de columnas para insertar separadores. En AppSheet, la forma estándar de crear saltos de página es agregando columnas virtuales de tipo **`Show`** con la categoría **`Page_Header`**:
2. Ve a **`Data`** → **`Columns`** → tabla **`Registro_Terreno`**.
3. Haz clic en **`Add Virtual Column`** para crear los siguientes separadores (configura el tipo de columna como `Show`, el `Show category` como `Page_Header` y escribe el nombre de la página en la fórmula `Content` con comillas simples):

*   **Página 1: Identificación**
    *   *Virtual Column name*: `Pagina_Identificacion`
    *   *Type*: `Show`
    *   *Category*: `Page_Header`
    *   *Content*: `"1. Identificación de Estación"`
    *   *Columnas incluidas*: `Estacion_CP`, `Muestra_ID`, `Intervalo`, `Sector`

*   **Página 2: Litología y Mineralogía**
    *   *Virtual Column name*: `Pagina_Litologia`
    *   *Type*: `Show`
    *   *Category*: `Page_Header`
    *   *Content*: `"2. Litología y Mineralogía"`
    *   *Columnas incluidas*: `Litologia`, `Mineralogia_Siglas`, `Horizonte`

*   **Página 3: Alteraciones**
    *   *Virtual Column name*: `Pagina_Alteraciones`
    *   *Type*: `Show`
    *   *Category*: `Page_Header`
    *   *Content*: `"3. Intensidad de Alteraciones"`
    *   *Columnas incluidas*: `Caolinizacion_Caol`, `Oxidos_Fe_OxFe`, `Estructuras`

*   **Página 4: Coordenadas y Foto**
    *   *Virtual Column name*: `Pagina_Coordenadas`
    *   *Type*: `Show`
    *   *Category*: `Page_Header`
    *   *Content*: `"4. Geolocalización y Registro Visual"`
    *   *Columnas incluidas*: `Coordenada_GPS`, `UTM_Este`, `UTM_Norte`, `Elevacion_m`, `Foto_URL`

*   **Página 5: Observaciones y Cierre**
    *   *Virtual Column name*: `Pagina_Cierre`
    *   *Type*: `Show`
    *   *Category*: `Page_Header`
    *   *Content*: `"5. Notas de Campo"`
    *   *Columnas incluidas*: `Observaciones`, `Geologo`, `Fecha`, `Hora`

Una vez creadas, ordénalas en la vista de formulario en **`App -> Views -> Registro_Terreno_Form`** en la propiedad **`Column Order`**.

---

## 2. Autogeneración de Código de Estación (`Estacion_CP`)

Para evitar errores tipográficos en terreno y hacer que la aplicación asigne automáticamente el siguiente ID secuencial de estación (ej. `Qui-CA-107`, `Qui-CA-108`), puedes utilizar fórmulas en la propiedad **`Initial Value`** de la columna `Estacion_CP`.

### Opción A: Si usas una columna numérica oculta de autoincremento (`Station_Num`):
Si en tu Excel tienes una columna de apoyo que extrae el número correlativo, usa la siguiente fórmula en el `Initial Value` de `Estacion_CP`:
```excel
CONCATENATE("Qui-CA-", TEXT(MAX(Registro_Terreno[Station_Num]) + 1, "000"))
```

### Opción B: Fórmulas directas de AppSheet basadas en el conteo total:
Si deseas calcular el código dinámicamente según la cantidad de registros en la tabla:
```excel
CONCATENATE("Qui-CA-", TEXT(COUNT(SELECT(Registro_Terreno[Estacion_CP], TRUE)) + 107, "000"))
```
*(Reemplaza el `107` con el número inicial del correlativo de tu campaña actual).*

---

## 3. Vista de Mapa (Geolocalización en Tiempo Real)

Para visualizar las estaciones mapeadas directamente en tu celular sobre imágenes satelitales o mapas de Google:

1. Ve a **`App`** → **`Views`** → Haz clic en **`New View`**.
2. Configura los siguientes parámetros:
   - **View name**: `Mapa de Estaciones`
   - **For this data**: `Registro_Terreno`
   - **View type**: `Map`
   - **Map column**: `Coordenada_GPS`
   - **Title column**: `Estacion_CP`
   - **Sub-title column**: `Litologia`
   - **Display -> Icon**: Busca `map` y selecciona un ícono de pin o mapa.
3. Haz clic en **`Save`**. Ahora verás un nuevo botón en el menú inferior de la app que te mostrará los puntos capturados en el mapa.

---

## 4. Personalización Visual (Icono y Pantalla de Carga)

Para darle una identidad visual profesional al proyecto Inducta/Quinhue:

1. Ve a **`Settings`** → **`Theme & Brand`**.
2. **Primary color**: Selecciona un color verde oscuro o azul corporativo (ej. `#1B4F72` para azul minero o `#1E8449` para verde geológico).
3. **App logo**:
   - Puedes seleccionar uno de la biblioteca de AppSheet (como el ícono de la montaña o de archivo).
   - O seleccionar **`Custom`** e ingresar un enlace URL directo al logotipo oficial de **Inducta**.
4. **Launch image** (Pantalla de carga): Elige una imagen de fondo o logo que se despliega al abrir la aplicación en el teléfono.
5. **Style**: Elige el modo **Dark** (Oscuro) para mejorar la visualización en terreno bajo luz solar intensa y ahorrar batería del dispositivo.

---

## 5. Reglas de Validación de Datos (`Valid_If`)

Para prevenir el ingreso de datos erróneos por parte del personal de terreno, puedes usar reglas **`Valid_If`** en columnas críticas:

*   **Rango de Muestra ID**: Para asegurar que el código de muestra ingresado esté en el rango asignado a la campaña (ej. entre `1140000` y `1150000`):
    - Selecciona la columna `Muestra_ID` → ve a la sección **`Auto Compute / Validation`** → **`Valid_If`**:
      ```excel
      AND(
        NUMBER([Muestra_ID]) >= 1140000,
        NUMBER([Muestra_ID]) <= 1150000
      )
      ```
    - *Error Message*: `"El ID de muestra debe pertenecer al lote asignado (1140000 - 1150000)"`.

*   **Evitar coordenadas en el origen (0,0)**: Para evitar que el geólogo guarde un registro si el GPS no ha tomado señal satelital aún:
    - Selecciona `Coordenada_GPS` → **`Valid_If`**:
      ```excel
      LAT([Coordenada_GPS]) <> 0
      ```
    - *Error Message*: `"Señal GPS insuficiente. Espere unos segundos e intente de nuevo."`

---

## 6. Notificación por Correo de Nuevos Registros

Si deseas que cada vez que un geólogo sincronice un registro crítico (por ejemplo, una muestra con alteración fuerte `5 (++)` o con presencia de brecha) se envíe una alerta automática inmediata:

1. En el editor de AppSheet, ve a la pestaña lateral **`Automation`** → **`Bots`** → **`Create a new bot`**.
2. **Event Trigger**: Configura el evento para que se active cuando se agregue una nueva fila (`ADDS_ONLY`) en la tabla `Registro_Terreno`.
3. **Run this step**: Selecciona **`Send an email`**.
4. **Email Config**:
   - **To**: `geologo@inducta.cl` (o el supervisor de campaña).
   - **Email Subject**: `"[Estacion_CP] - Registro de Campo Crítico Detectado"`
   - **Email Body**:
     ```html
     Alerta de Terreno:<br><br>
     Se ha ingresado la estación <b><<[Estacion_CP]>></b> en el sector <b><<[Sector]>></b>.<br>
     <b>Litología:</b> <<[Litologia]>> (Horizonte <<[Horizonte]>>)<br>
     <b>Caolinización:</b> <<[Caolinizacion_Caol]>> | <b>Óxidos de Fe:</b> <<[Oxidos_Fe_OxFe]>> <br>
     <b>Observaciones:</b> <<[Observaciones]>>
     ```
5. Presiona **`Save`**. ¡El bot enviará alertas instantáneas sin necesidad de ejecutar scripts adicionales!
