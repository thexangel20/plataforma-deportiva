# Rama prueba: aplicación integrada

La entrada `run.py` inicia la versión con las 21 HU. Consulta [README_PRUEBA.md](README_PRUEBA.md) para ejecutarla, acceder como administrador, probarla y conectar Supabase. La definición acordada está en [HISTORIAS_USUARIO_ACORDADAS.md](HISTORIAS_USUARIO_ACORDADAS.md).

El contenido siguiente documenta la implementación anterior de Axel, conservada en `app/`.

---

# Plataforma Deportiva

Plataforma web para consultar información sobre diferentes deportes.

## Tecnologías

- HTML5
- CSS3
- Python
- Supabase
- PostgreSQL

## Descripción

El sistema permitirá consultar información relacionada con diferentes deportes,
incluyendo costos, duración, equipamiento, alimentación y recomendaciones.

## Autores

Proyecto académico - Sistemas de Información 2

## Desarrollo local de Axel: HU4 y HU5

La aplicación incluye reportes de información (HU4) y edición administrativa de
los deportes existentes (HU5), sin JavaScript. La tabla `deportes_axel` es una
estructura provisional autorizada para integrar después con el equipo.

### Puesta en marcha en PowerShell

1. Usar Python 3.13.3. El entorno local `.venv` fue actualizado a esa versión.

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. En un proyecto de prueba de Supabase, ejecutar el contenido de
   `sql/estructura_axel.sql` desde SQL Editor. Crea las tablas `deportes_axel` y
   `reportes_hu4`, sus permisos y el bucket público `imagenes-deportes-axel`.
   Inserta los cuatro nombres originales de deportes; sus costos y otros datos
   quedan pendientes, sin inventar información. No modifica deportes ya
   existentes con esos identificadores. Si ya existe una tabla con otro esquema,
   revisar sus columnas antes: `create table if not exists` no migra columnas.

3. Completar el archivo local `.env` junto a `run.py`:

```dotenv
SECRET_KEY=conservar_el_valor_local_generado
SUPABASE_URL=https://TU_PROYECTO.supabase.co
SUPABASE_SECRET_KEY=TU_CLAVE_PRIVADA_DE_SERVIDOR
SUPABASE_BUCKET=imagenes-deportes-axel
ADMIN_USUARIO=axel
ADMIN_PASSWORD_HASH=
```

La clave de Supabase debe ser `secret` o `service_role`. No usar `anon` o
`publishable`. `.env` está excluido por Git y las claves nunca se envían al HTML.
En otra copia del repositorio, copiar `.env.example` como `.env` y generar una
clave propia con `python -c "import secrets; print(secrets.token_hex(32))"`.

4. Configurar el administrador con el asistente local. Pide la contraseña sin
   mostrarla y guarda únicamente su hash; no es necesario pegar la contraseña
   en el código ni compartirla por chat.

```powershell
.\.venv\Scripts\python.exe configurar_admin.py
.\.venv\Scripts\python.exe run.py
```

5. Abrir `http://127.0.0.1:5000`. El enlace Administración permite acceder a
   Reportes y Editar deportes. Reiniciar Flask después de cambiar `.env`.

### Comprobación manual con Supabase

- Enviar un reporte desde una tarjeta y verificar que aparezca como pendiente.
- Entrar como administrador, filtrar reportes y marcar uno como revisado.
- Editar un deporte, cambiar costos y recomendaciones, y guardar.
- Confirmar que los cambios aparecen en la portada y el detalle público.
- Reemplazar una imagen JPEG, PNG o WebP de hasta 5 MB y comprobar que se muestra.
- Cerrar sesión y comprobar que no se puede editar ni revisar reportes.

### Pruebas locales

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Las pruebas usan respuestas simuladas: no envían información a Supabase.
Sin configuración de Supabase se puede navegar por los cuatro deportes
iniciales; las operaciones de guardado muestran un error de configuración y no
simulan persistencia. La validación real de SQL, Storage y permisos queda
pendiente de ejecutar el script y configurar las credenciales.

### Integración posterior

- `app/servicios.py`: acceso de servidor a la API REST y Storage.
- `app/seguridad.py`: sesión administrativa y protección CSRF.
- `app/reportes.py`: HU4, listado de 50 reportes por página y revisión.
- `app/deportes.py`: HU5, validación, edición e imágenes.
- `sql/estructura_axel.sql`: propuesta de estructura independiente.

Los reportes conservan el identificador de texto del deporte para mantener
compatibilidad con la propuesta anterior. Al integrar la tabla del equipo hay
que migrar esos identificadores y definir su relación. La autenticación local
se reemplazará por la compartida del equipo cuando exista.

El costo incluye moneda y período para no confundir un costo mensual con uno
por sesión. Los campos desconocidos se muestran como información pendiente.
Las imágenes se comprueban por su contenido y se convierten a JPEG antes de
subirse. Las imágenes anteriores se conservan en Storage para evitar borrar
archivos que todavía puedan estar referenciados. Una carga fallida se limpia
solo si se puede comprobar que la nueva imagen no quedó asociada al deporte.

Una rama de Git no aísla Supabase: utilizar un proyecto de prueba propio.
No se realizaron commits ni push como parte de estos cambios.

## HU1: condiciones y espacios de práctica

El detalle público muestra si el deporte se practica en interiores, exteriores
o ambos; si requiere instalaciones especiales; y si requiere compañeros.
El administrador carga estos tres datos desde Editar deporte. Los datos
desconocidos se muestran como Información pendiente, no como una respuesta No.
El campo de condiciones existente sirve para describir instalaciones y otros
requisitos con más detalle.

Para una base nueva, ejecutar `sql/estructura_axel.sql`. Si la tabla ya fue
creada con la versión anterior, ejecutar además `sql/hu1_condiciones.sql` antes
de guardar nuevas ediciones. Este script agrega columnas sin borrar registros.
No se cargaron condiciones deportivas inventadas.

## HU2: demostración de favoritos para el equipo

Por solicitud de Axel se incluye una demostración temporal mientras se prepara
la base de datos. Desde el catálogo o el detalle se pueden agregar favoritos,
abrir `/favoritos`, consultar sus características y quitarlos. No permite
duplicados y admite hasta 20 deportes. Todas las acciones usan POST y CSRF.

La selección se almacena en la sesión firmada de este navegador, sin crear
usuarios ni escribir favoritos en Supabase. Se puede perder al borrar cookies,
terminar la sesión o iniciar/cerrar la sesión administrativa. Los navegadores
que restauran sesiones pueden conservarla al reiniciarse. La interfaz identifica
expresamente esta funcionalidad como demostración y guardado temporal.

La HU2 definitiva sigue pendiente de cuentas y base de datos: deberá guardar la
relación entre usuario y deporte, impedir duplicados y restringir la consulta
y eliminación al propietario. `app/favoritos.py` concentra el flujo provisional
para sustituirlo cuando se acuerden los identificadores del equipo.

## HU3: comparación básica y descarga PDF

Abrir `/comparar` desde la navegación. Seleccionar dos o tres deportes y pulsar
Comparar seleccionados. El resultado muestra costos con moneda y período,
equipamiento, tiempos, alimentación, recomendaciones y condiciones. Descargar
comparación en PDF genera un documento con resumen y detalle de cada deporte.

La descarga conserva los datos que se mostraron al comparar, aunque un deporte
se edite después. El formulario transporta una copia firmada por el servidor,
válida por 30 minutos y protegida con CSRF. No guarda la comparación en una cookie
ni necesita cuentas. Al vencer, volver a comparar para obtener datos actuales.

Sin Supabase se puede comprobar la selección y descargar un PDF con los cuatro
nombres iniciales. Los demás datos aparecen como pendientes. No se presentan
estos documentos como información deportiva verificada.

La comparación básica es provisional, autorizada para poder utilizar la HU3.
Cuando llegue la comparación del equipo, reutilizar `preparar_resumen` de
`app/comparacion.py` y `generar_pdf` de `app/pdf_comparacion.py` con sus datos.
ReportLab se instala desde `requirements.txt`; no se requiere JavaScript.

Las pruebas incluyen las HU1, HU3, HU4 y HU5. Se verificaron PDFs con dos y tres
deportes y se revisaron visualmente ejemplos de texto corto y largo. Las
pruebas de conexión siguen usando respuestas simuladas de Supabase.
