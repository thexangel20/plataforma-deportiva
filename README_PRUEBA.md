# SportsInfo integrado — rama prueba

Implementación de las 21 HU de `HISTORIAS_USUARIO_ACORDADAS.md`, con una interfaz adaptable a celulares, Flask y persistencia intercambiable entre SQLite local y Supabase Postgres/Storage.

## Ejecutar en Windows

Desde la carpeta del proyecto:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe run.py
```

Abre http://127.0.0.1:5000. Para usar otro puerto:

```powershell
.\.venv\Scripts\python.exe -m flask --app run run --host 127.0.0.1 --port 5001
```

Si todavía no existe el entorno virtual, créalo con `python -m venv .venv`. El proyecto se prueba con Python 3.13.

La primera ejecución local crea `instance/sportsinfo.sqlite3` y cinco deportes de ejemplo. Los importes son ilustrativos, no precios verificados de establecimientos. Los datos persisten después de reiniciar. Los deportes eliminados no se vuelven a insertar automáticamente; `manage.py seed` los puede reponer de forma explícita.

## Cuentas y administración

El registro público crea usuarios normales. Cada usuario puede mantener su perfil y sus favoritos. Los administradores se crean desde la terminal, nunca desde el formulario público:

```powershell
.\.venv\Scripts\python.exe manage.py create-admin --email tu-correo@example.com --nombre Administrador
```

El comando solicita la contraseña sin mostrarla. La opción `--generar` crea una contraseña aleatoria y guarda el acceso en `instance/ACCESO_ADMIN_LOCAL.txt`, excluido de Git. Para esta revisión ya se creó `admin@sportsinfo.local`; consulta su contraseña en ese archivo local.

Después de iniciar sesión, abre el menú de tu cuenta y selecciona Administración. Desde allí puedes crear, editar, desactivar, reactivar y eliminar deportes sin referencias, y revisar reportes. Los deportes con favoritos o reportes deben desactivarse en lugar de eliminarse.

Las cuentas de esta implementación pertenecen a la aplicación: Flask verifica contraseñas con hash scrypt y mantiene una sesión firmada. Al cambiar de modo se guardan en Supabase Postgres; no se utilizan todavía cuentas de Supabase Auth ni se confunde una clave API con una sesión de usuario.

## Activar Supabase cuando esté disponible

1. Revisa y ejecuta `sql/sportsinfo_integrado.sql` en el editor SQL del proyecto Supabase. Crea cinco tablas con prefijo `sportsinfo_` y el bucket público `sportsinfo-imagenes`. No modifica las tablas anteriores `deportes`, `deportes_axel` ni `reportes_hu4`.
2. Completa estas variables en `.env`, conservando las demás variables existentes:

```dotenv
DATA_BACKEND=supabase
SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_SECRET_KEY=TU_CLAVE_SECRETA_DEL_SERVIDOR
SPORTSINFO_BUCKET=sportsinfo-imagenes
```

3. Con la aplicación detenida y una copia de `instance/` guardada, copia los registros locales:

```powershell
.\.venv\Scripts\python.exe manage.py migrate-local
.\.venv\Scripts\python.exe manage.py check
```

4. Reinicia Flask y verifica un registro, un favorito, un reporte y una carga de imagen desde el navegador.

La migración conserva identificadores y hashes de contraseñas, copia usuarios antes de sus perfiles/favoritos/reportes y sube las imágenes locales cargadas por administradores. Las imágenes de ejemplo siguen siendo recursos estáticos del proyecto. No sobrescribe registros que ya tengan el mismo identificador en destino. Si se interrumpe, puede reanudarse; ante conflicto de correo informa el error sin sustituir cuentas. Una subida cuyo guardado posterior falle puede dejar una imagen sin referencia; se debe revisar antes de limpiarla.

Para una base remota vacía sin usuarios locales que conservar, `manage.py seed` agrega únicamente los cinco deportes; luego crea el administrador con `manage.py create-admin`.

La clave secreta se utiliza solo desde Flask. Las tablas tienen RLS y acceso directo revocado para `anon` y `authenticated`; el servidor aplica permisos de usuario y administrador antes de operar mediante `service_role`. El bucket de imágenes es público para servir las fotografías del catálogo. No habilites escrituras públicas.

Si existe otro sistema de cuentas del equipo, se necesita una migración/adaptación explícita antes de usarlo. Cambiar la URL y clave no integra automáticamente tablas con estructuras diferentes.

En un despliegue HTTPS configura `COOKIE_SECURE=1` y un `SECRET_KEY` estable. Para la vista local HTTP usa `COOKIE_SECURE=0`. `instance/`, `.env`, contraseñas y claves están excluidos de Git. El servidor de desarrollo se usa únicamente para la revisión local.

## Estructura

- `run.py`: entrada de la aplicación integrada.
- `sportsinfo/__init__.py`: configuración, creación de la aplicación y errores comunes.
- `sportsinfo/routes.py`: catálogo, usuarios, perfil, favoritos, administración y pantallas de herramientas.
- `sportsinfo/store.py`: acceso a SQLite o REST de Supabase, con el mismo contrato.
- `sportsinfo/calculations.py`: presupuesto, desgaste, plan, compras y recomendaciones.
- `sportsinfo/pdf.py`: comparación PDF a partir de una copia firmada de los datos mostrados, válida durante una hora.
- `sportsinfo/templates/` y `sportsinfo/static/`: interfaz integrada, imágenes y búsqueda dinámica.
- `sql/sportsinfo_integrado.sql`: estructura de Supabase.
- `tests/test_integracion_21hu.py`: pruebas integradas de las nuevas HU y permisos.
- `app/`, sus SQL anteriores y sus pruebas: trabajo previo conservado como referencia. No es el punto de entrada de la página integrada.

Las imágenes se tomaron de la rama Angel y se prepararon para el catálogo. Las funciones de comparación/PDF, reportes y edición de Axel, las recomendaciones y perfil de Gabriel, y los cálculos de Daniel se integraron funcionalmente en un modelo común, completando los comportamientos que faltaban. No se hizo una fusión indiscriminada de los archivos `routes.py` de cada rama.

## Decisiones para criterios que estaban abiertos

- Costos orientativos en BOB por mes: bajo hasta 150 inclusive; medio mayor a 150 y hasta 300; alto mayor a 300. Un costo desconocido no equivale a cero.
- Comparación de dos o tres deportes distintos, con duración, costo, equipo, dificultad, beneficios y condiciones.
- Recomendación explicable: objetivo 4 puntos; presupuesto 3; tiempo por sesión 2; experiencia 2. Devuelve hasta tres deportes activos con alguna coincidencia. No usa edad, sexo o medidas para emitir recomendaciones clínicas.
- Perfil: edad 13–100, días 1–7, disponibilidad 15–240 minutos; medidas físicas opcionales.
- Presupuesto: 1–60 meses, gastos únicos o mensuales y aritmética decimal a dos decimales.
- Desgaste: vida total ajustada = vida de referencia × frecuencia de referencia / frecuencia real. Supone desgaste proporcional y uso constante; no determina la seguridad real de un artículo.
- Plan: respeta los días elegidos; máximo 3/4/5 sesiones y 40/60/90 minutos por sesión según nivel, limitado además por el tiempo disponible. Incluye calentamiento, práctica y vuelta a la calma, y deja días de descanso. Es un organizador orientativo, no un programa clínico ni una prescripción individual.
- Compras: considera estado, ahorro y si es equipo de protección. No recomienda automáticamente comprar usado.
- Imágenes: JPEG/PNG/WebP, máximo 5 MB y 16 millones de píxeles; se recodifican a JPEG para retirar contenido adicional y reducir tamaño.
- Todas las operaciones de escritura desde formularios requieren CSRF; el rol se consulta en la base, no se acepta desde datos enviados por el navegador.

## Cobertura de las HU

| HU | Pantalla o flujo |
|---|---|
| 1 | Catálogo `/` |
| 2 | Ficha, orientación inicial |
| 3 | Filtro mensual por costo |
| 4 | Administración, registrar deporte e imagen |
| 5 | Búsqueda dinámica por nombre u objetivo |
| 6 | Ficha, condiciones del lugar |
| 7 | Favoritos asociados a cuenta |
| 8 | Descargar comparación PDF |
| 9 | Reportar datos y gestionar sus estados |
| 10 | Administración, edición de deporte e imagen |
| 11 | Comparación de 2–3 deportes |
| 12 | Recomendaciones explicadas a partir del perfil |
| 13 | Presupuesto con gastos periódicos y únicos |
| 14 | Perfil persistente por usuario |
| 15 | Vida útil del equipamiento |
| 16 | Plan semanal con disponibilidad y descansos |
| 17 | Comparación de compra nueva/usada |
| 18 | Ficha, costos, tiempo y equipamiento |
| 19 | Ficha, alimentación e hidratación |
| 20 | Activación, desactivación y eliminación protegida por referencias |
| 21 | Registro, inicio/cierre de sesión y autorización |

## Verificar

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Se verifican los flujos locales, privacidad entre usuarios, validaciones, PDF, integridad referencial y el contrato REST con respuestas simuladas. La conexión real a Supabase, sus permisos efectivos y el almacenamiento remoto quedan pendientes hasta disponer del proyecto y sus credenciales.
