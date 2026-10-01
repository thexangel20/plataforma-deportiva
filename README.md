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

## HU21: Comparar deportes

La aplicación permite seleccionar dos o más deportes desde el catálogo y
compararlos en `/comparar`, mostrando objetivo, costo, duración, equipamiento y
recomendaciones. También permite quitar deportes de la comparación.

La HU22 agrega `/recomendar`, donde el visitante indica costo, objetivo y
tiempo disponible para recibir recomendaciones adaptadas a sus preferencias.

La HU23 agrega `/admin/deportes`, donde el administrador puede activar o
desactivar deportes. La operación actualiza únicamente `activo`; el registro
permanece almacenado y los módulos públicos solo consultan deportes activos.

La HU24 agrega `/admin` y `/admin/resumen`, con totales del catálogo, estados
activo/inactivo y distribución por nivel de costo calculados desde la información actual.

La HU25 agrega una URL pública única por deporte en `/deporte/<id>`, con detalle
completo y botón para compartir o copiar el enlace.

### Ejecución local

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python run.py
```

Sin variables de Supabase se muestran datos locales de demostración. Para usar
PostgreSQL mediante Supabase, ejecuta `pip install -r requirements-supabase.txt`, copia
`.env.example` como `.env`, completa las variables y ejecuta
`supabase/schema.sql` en el SQL Editor de Supabase.

### Pruebas

```bash
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

## Autores

Proyecto académico - Sistemas de Información 2
