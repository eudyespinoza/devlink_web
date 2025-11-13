# Instrucciones: Cómo enviar emails HTML personalizados desde Gmail

## Método 1: Copiar y pegar HTML directamente (Recomendado)

### Pasos:
1. **Abre el archivo `email-bienvenida.html`** en cualquier navegador web
2. **Selecciona todo el contenido** (Ctrl+A) del email renderizado en el navegador
3. **Copia** (Ctrl+C) el contenido
4. **Ve a Gmail** y crea un nuevo mensaje
5. **Pega** (Ctrl+V) el contenido - Gmail mantendrá el formato HTML
6. **Personaliza los campos** antes de enviar:
   - `[NOMBRE_CLIENTE]` → Nombre real del cliente
   - `[PANEL_URL]` → URL del panel de control
   - `[USUARIO_PANEL]` → Usuario de acceso
   - `[CONTRASEÑA_PANEL]` → Contraseña generada
   - `[DOMINIO_CLIENTE]` → Dominio del cliente
   - `[FECHA_PROXIMA_FACTURA]` → Fecha de próxima facturación

## Método 2: Usando una extensión de Chrome

### Extensiones recomendadas:
- **"HTML Email Template"**
- **"HTML Email Creator"**
- **"Template for Gmail"**

### Pasos:
1. Instala una de las extensiones
2. Carga el archivo `email-bienvenida.html`
3. Personaliza los campos
4. Envía directamente desde la extensión

## Método 3: Crear una plantilla reutilizable en Gmail

### Pasos:
1. **Activa las plantillas** en Gmail:
   - Ve a Configuración (⚙️) → "Ver toda la configuración"
   - Pestaña "Avanzadas" → Activa "Plantillas"
   - Guarda cambios

2. **Crea la plantilla**:
   - Nuevo mensaje
   - Pega el HTML (método 1)
   - Clic en ⋮ (más opciones) → "Plantillas" → "Guardar borrador como plantilla"
   - Ponle nombre: "Bienvenida devLink"

3. **Usar la plantilla**:
   - Nuevo mensaje
   - ⋮ → "Plantillas" → Selecciona "Bienvenida devLink"
   - Personaliza campos específicos del cliente
   - Envía

## Campos a personalizar en cada email:

```
[NOMBRE_CLIENTE] → Ej: "Juan Pérez"
[PANEL_URL] → Ej: "https://cpanel.devlink.com.ar"
[USUARIO_PANEL] → Ej: "juanperez_admin"
[CONTRASEÑA_PANEL] → Ej: "Kx9#mP2$vN8q"
[DOMINIO_CLIENTE] → Ej: "empresajuan.com.ar"
[FECHA_PROXIMA_FACTURA] → Ej: "15 de noviembre de 2024"
```

## Alternativa: Versión texto plano

Si el HTML no funciona correctamente, usa el archivo `email-bienvenida.txt` que tiene el mismo contenido en formato texto plano.

## Tips adicionales:

✅ **Siempre envía un email de prueba** a ti mismo antes de enviarlo al cliente
✅ **Verifica que todos los links funcionen** correctamente
✅ **Revisa que no quede ningún campo [PLACEHOLDER]** sin personalizar
✅ **Guarda una copia** de los datos de acceso del cliente en tu sistema
✅ **Considera crear un checklist** de onboarding para nuevos clientes

## Personalización adicional:

Puedes modificar el archivo HTML para:
- Cambiar colores según tu marca
- Agregar tu logo específico
- Incluir información adicional sobre servicios
- Agregar enlaces a tutorials específicos
- Modificar la estructura de precios según planes diferentes