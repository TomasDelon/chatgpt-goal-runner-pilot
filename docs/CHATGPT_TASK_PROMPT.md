# Protocolo de reentrada para ChatGPT Tasks

**Este archivo es una plantilla, no una tarea ya creada.** Cada ejecución usa los identificadores reales registrados en el checkpoint privado, no nombres inferidos.

1. Leer el estado privado canónico y verificar identificador, revisión y estado.
2. Ante `COMPLETED` o `PAUSED`, no ejecutar trabajo. Pausar solo la tarea programada asociada si procede.
3. Si existe una operación incierta o CI en marcha, inspeccionar su resultado y no reenviar una mutación automáticamente.
4. Ejecutar como máximo un paso verificable por turno y únicamente sobre la rama experimental autorizada.
5. Leer el SHA y las comprobaciones reales. Guardar el estado mediante compare-and-swap (hash de bloque observado).
6. Ante conflicto, permiso faltante, cuota desconocida o dos fallos consecutivos, bloquear y comunicar el motivo.
7. Marcar `COMPLETED` solo con evidencia de criterios de aceptación sobre el mismo commit SHA y detener la tarea.

Restricciones: sin API de modelos, sin Codex, sin Atlas, sin gastos adicionales, sin merges a `main`, sin despliegues de producción ni secretos. No inventar resultados o pruebas visuales.
