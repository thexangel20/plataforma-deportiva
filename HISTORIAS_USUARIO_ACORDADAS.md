# SportsInfo — Historias de usuario acordadas

Fecha: 2 de octubre de 2026.

Esta es la nueva numeración de 21 HU acordada en la conversación. Cada historia tiene un único responsable. No representa el estado de implementación del código ni cambia automáticamente las referencias históricas de las ramas. Dificultad: 1–10. Importancia: 1–20. Las puntuaciones son estimaciones.

## HU1 — Consultar el catálogo
Responsable: Angel. Dificultad: 3/10. Importancia: 20/20.

Como visitante, quiero ver los deportes disponibles para elegir cuál consultar.

Criterios de aceptación:
- Muestra nombre e imagen de los deportes activos.
- Cada tarjeta permite abrir su ficha.
- Presenta un mensaje cuando no hay deportes disponibles.

## HU2 — Orientación para principiantes
Responsable: Angel. Dificultad: 3/10. Importancia: 13/20.

Como principiante, quiero conocer cómo empezar a practicar un deporte para prepararme adecuadamente.

Criterios de aceptación:
- Muestra primeros pasos y precauciones específicas para comenzar.
- Identifica cuando esa información todavía no está disponible.
- Se limita a orientación inicial; alimentación, costos y condiciones del lugar pertenecen a otras HU.

## HU3 — Filtrar deportes por costo
Responsable: Angel. Dificultad: 5/10. Importancia: 16/20.

Como usuario, quiero filtrar deportes por nivel de costo para encontrar opciones acordes a mi presupuesto.

Criterios de aceptación:
- Permite elegir costo bajo, medio o alto según rangos definidos por el equipo.
- Muestra únicamente coincidencias y permite limpiar el filtro.
- Avisa cuando no hay resultados e identifica los deportes sin costo registrado.

## HU4 — Registrar un deporte
Responsable: Angel. Dificultad: 8/10. Importancia: 20/20.

Como administrador, quiero registrar un deporte nuevo para incorporarlo al catálogo.

Criterios de aceptación:
- Solo un administrador puede registrar deportes.
- Valida campos obligatorios, valores y formato/tamaño de imagen.
- Guarda el registro y su imagen, confirma el resultado y permite encontrar el nuevo deporte en el catálogo.
- Un fallo no se presenta como registro exitoso.

## HU5 — Buscar deportes
Responsable: Angel. Dificultad: 5/10. Importancia: 17/20.

Como usuario, quiero buscar deportes por nombre u objetivo para encontrar opciones de mi interés.

Criterios de aceptación:
- Busca por nombre u objetivo sin distinguir mayúsculas.
- Actualiza los resultados sin recargar toda la página y puede combinarse con HU3.
- Permite limpiar la búsqueda y avisa cuando no hay coincidencias.

## HU6 — Consultar condiciones de práctica
Responsable: Axel. Dificultad: 3/10. Importancia: 14/20.

Como usuario, quiero conocer las condiciones de práctica para saber si puedo realizar un deporte en mi entorno.

Criterios de aceptación:
- Muestra las condiciones registradas del lugar: espacio, ambiente interior/exterior y requisitos de instalaciones.
- Indica los datos faltantes.
- No repite el equipamiento personal de HU18 ni los consejos iniciales de HU2.

## HU7 — Gestionar favoritos
Responsable: Axel. Dificultad: 6/10. Importancia: 14/20.

Como usuario con cuenta, quiero agregar y quitar deportes favoritos para consultarlos posteriormente.

Criterios de aceptación:
- Requiere iniciar sesión y permite agregar, consultar y quitar favoritos.
- Evita duplicados y conserva la selección entre sesiones.
- Restringe cada lista a su propietario e identifica deportes que dejaron de estar disponibles.

## HU8 — Descargar comparación en PDF
Responsable: Axel. Dificultad: 6/10. Importancia: 12/20.

Como usuario, quiero descargar en PDF una comparación ya realizada para conservarla o compartirla.

Criterios de aceptación:
- Desde una comparación válida de HU11, permite descargar un PDF legible.
- Incluye los mismos deportes, atributos, valores y unidades que se mostraron.
- No permite descargar una comparación vacía o inválida.

## HU9 — Reportar información incorrecta
Responsable: Axel. Dificultad: 6/10. Importancia: 15/20.

Como usuario, quiero reportar un dato incorrecto para que un administrador pueda revisarlo.

Criterios de aceptación:
- Permite seleccionar el deporte, describir el problema y recibir confirmación.
- Rechaza reportes vacíos.
- Solo un administrador puede consultarlos y cambiar su estado a pendiente, resuelto o descartado.
- El reporte no modifica automáticamente el deporte; la corrección corresponde a HU10.

## HU10 — Actualizar un deporte
Responsable: Axel. Dificultad: 8/10. Importancia: 19/20.

Como administrador, quiero editar un deporte existente para mantener vigente su información.

Criterios de aceptación:
- Solo un administrador puede editar un registro existente.
- Valida los cambios y permite reemplazar su imagen.
- Los cambios guardados aparecen en la ficha.
- Si falla el guardado, conserva los datos anteriores e informa el error.

## HU11 — Comparar deportes
Responsable: Gabriel. Dificultad: 6/10. Importancia: 18/20.

Como usuario, quiero comparar dos o más deportes para evaluar sus diferencias antes de elegir.

Criterios de aceptación:
- Permite seleccionar al menos dos deportes distintos dentro del límite definido por el equipo.
- Presenta los mismos atributos para todos: costos, duración, equipamiento, dificultad y beneficios disponibles.
- Muestra unidades y períodos; distingue los datos faltantes de los valores cero.

## HU12 — Recibir recomendaciones personalizadas
Responsable: Gabriel. Dificultad: 8/10. Importancia: 17/20.

Como usuario con perfil, quiero recibir recomendaciones de deportes según mis características, objetivos y disponibilidad.

Criterios de aceptación:
- Utiliza los datos del perfil de HU14 y solicita completar los campos necesarios cuando falten.
- Presenta deportes recomendados y explica los motivos según reglas definidas.
- Actualizar el perfil permite obtener resultados acordes a los nuevos datos.

## HU13 — Calcular el presupuesto de práctica
Responsable: Gabriel. Dificultad: 8/10. Importancia: 18/20.

Como usuario, quiero calcular cuánto gastaré al practicar un deporte durante un período para organizar mi presupuesto.

Criterios de aceptación:
- Permite elegir un período e ingresar gastos por categoría, incluidos inscripción, cuotas, instalaciones, equipo, ropa, transporte, alimentación y otros gastos.
- Distingue gastos únicos y periódicos para no contarlos dos veces.
- Valida importes no negativos y utiliza una moneda común.
- Muestra el desglose y un total que coincide con sus componentes.

## HU14 — Gestionar el perfil deportivo
Responsable: Gabriel. Dificultad: 6/10. Importancia: 18/20.

Como usuario con cuenta, quiero guardar y actualizar mis características y preferencias deportivas para personalizar mi experiencia.

Criterios de aceptación:
- Requiere una cuenta y permite guardar y editar características deportivas, experiencia, objetivos, presupuesto y disponibilidad.
- Valida los campos y rangos definidos.
- Conserva los datos entre sesiones y permite acceder únicamente al perfil propio.

## HU15 — Estimar el desgaste del equipamiento
Responsable: Daniel. Dificultad: 8/10. Importancia: 12/20.

Como deportista, quiero estimar la vida útil restante de mi equipamiento según su uso para planificar su reemplazo.

Criterios de aceptación:
- Permite seleccionar o describir un implemento e ingresar antigüedad, frecuencia de uso y vida útil de referencia.
- Rechaza valores inválidos.
- Muestra una estimación de vida restante y reemplazo, indicando sus suposiciones.
- Identifica cuando la vida estimada ya se agotó; no vuelve a calcular el presupuesto general de HU13.

## HU16 — Generar un plan de entrenamiento
Responsable: Daniel. Dificultad: 9/10. Importancia: 15/20.

Como deportista, quiero obtener un plan según mi nivel, objetivo y disponibilidad para organizar mis sesiones.

Criterios de aceptación:
- Solicita deporte, nivel, objetivo, días y tiempo disponible; valida los datos.
- Genera sesiones con duración y descansos sin superar la disponibilidad.
- Explica cuando no puede generar un plan con los parámetros ingresados.

## HU17 — Comparar equipamiento nuevo y usado
Responsable: Daniel. Dificultad: 6/10. Importancia: 13/20.

Como deportista, quiero comparar opciones nuevas y usadas de un mismo implemento para decidir cuál comprar.

Criterios de aceptación:
- Compara alternativas del mismo tipo de implemento.
- Solicita y valida precios y estado del usado.
- Muestra la diferencia monetaria, el ahorro cuando corresponda y recomendaciones justificadas.
- No presenta automáticamente lo usado como la mejor opción.

## HU18 — Consultar las características del deporte
Responsable: Jhonatan. Dificultad: 3/10. Importancia: 20/20.

Como usuario, quiero conocer los costos orientativos, duración y equipamiento de un deporte para entender sus requisitos.

Criterios de aceptación:
- Muestra costos orientativos con moneda y período, duración/frecuencia habitual y equipamiento personal necesario.
- Identifica información faltante.
- Presenta datos informativos; el cálculo del presupuesto personal corresponde a HU13.

## HU19 — Consultar alimentación deportiva
Responsable: Jhonatan. Dificultad: 3/10. Importancia: 14/20.

Como usuario, quiero consultar recomendaciones alimenticias relacionadas con un deporte para complementar mi preparación.

Criterios de aceptación:
- Muestra recomendaciones generales de alimentación e hidratación relacionadas con el deporte seleccionado.
- Identifica cuando no hay contenido disponible.
- No calcula calorías ni genera dietas personalizadas.

## HU20 — Gestionar la disponibilidad de deportes
Responsable: Jhonatan. Dificultad: 7/10. Importancia: 18/20.

Como administrador, quiero desactivar, reactivar o eliminar deportes para mantener vigente el catálogo.

Criterios de aceptación:
- Solo un administrador puede desactivar, reactivar o solicitar eliminar deportes.
- Los inactivos dejan de aparecer como opciones disponibles en catálogo, búsqueda y recomendaciones.
- La eliminación exige confirmación y se bloquea cuando existen referencias que deban conservarse, ofreciendo desactivación.

## HU21 — Registrarse y gestionar la sesión
Responsable: Jhonatan. Dificultad: 8/10. Importancia: 20/20.

Como visitante, quiero crear una cuenta e iniciar y cerrar sesión para acceder a mis funciones personales.

Criterios de aceptación:
- Permite registrarse con datos válidos y evita cuentas duplicadas.
- Permite iniciar y cerrar sesión; rechaza credenciales incorrectas.
- Un registro público obtiene rol de usuario y no puede asignarse permisos administrativos.
- Las operaciones protegidas verifican la sesión y el rol en el servidor.

## Dependencias y trazabilidad

- HU7 y HU14 requieren cuentas de HU21; HU12 utiliza HU14; HU8 utiliza HU11.
- HU1 muestra el catálogo, HU3 lo filtra y HU5 realiza búsquedas.
- HU4 crea registros, HU10 los edita y HU20 administra disponibilidad/eliminación.
- Las antiguas HU1 de Angel y HU21 de Jhonatan se consolidaron en la nueva HU1, responsable Angel.
- Las antiguas HU13 de Gabriel y HU17 de Daniel se consolidaron en la nueva HU13, responsable Gabriel.
- La antigua HU19 de Daniel sigue eliminada. La nueva HU19 es alimentación informativa de Jhonatan.
- La antigua HU14 no se recibió; la nueva HU14 es el perfil deportivo que antes tenía el número 15.
- La antigua HU25 se conserva como trabajo técnico transversal de almacenamiento de datos e imágenes, responsable Jhonatan, sin una HU funcional duplicada.
- Rangos de costo, límite máximo de deportes comparables, reglas de recomendación y parámetros de los cálculos deben concretarse durante el diseño; no se inventan valores en este documento.

## Reparto

Angel: 5 HU. Axel: 5 HU. Gabriel: 4 HU. Daniel: 3 HU. Jhonatan: 4 HU.
