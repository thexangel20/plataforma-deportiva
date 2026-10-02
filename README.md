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
## 🎯 Funcionalidades

### 📅 Planificador de Entrenamiento
Permite al usuario ingresar su nivel, objetivo y disponibilidad para
obtener una distribución semanal de entrenamiento personalizada.

**Características:**
- Cálculo de horas recomendadas según nivel y objetivo
- Distribución de sesiones y días de descanso
- Advertencias automáticas (poca disponibilidad, sobreentrenamiento, etc.)
- Recomendaciones generales

**Cómo acceder:**
1. Ejecutar `python run.py`
2. Abrir `http://127.0.0.1:5000/planificador`
3. Completar el formulario y presionar "Generar plan"

**Matriz de horas recomendadas:**

| Nivel | Recreativo | Salud | Competitivo |
|-------|:----------:|:-----:|:-----------:|
| Principiante | 3h | 4h | 5h |
| Intermedio | 5h | 6h | 8h |
| Avanzado | 7h | 8h | 12h |
