# Decisiones y gates del Cloud Goal Runner

**Alcance:** ChatGPT Chat/Tasks como razonamiento. GitHub ofrece código, PR, CI y logs; ChatGPT Space sirve como checkpoint privado, con CAS por hash. Vercel es opcional, inicialmente bloqueado.

## Estado y corrección

`DRAFT → PLANNING → EXECUTING → AWAITING_CI → VERIFYING → COMPLETED`, con alternativas `BLOCKED` y `PAUSED`. Cada mutación remota debe tener una postcondición observable. El modelo no interpreta el hecho de recibir un receipt como evidencia de que la aplicación funciona.

El módulo Python implementa **solo la lógica pura**. Aún no proporciona almacenamiento CAS real, bloqueo distribuido, gestión de trabajos ni recursos reales.

## Presupuesto

GitHub Actions en un repositorio público, con runner estándar y límites internos. Máximo 5 minutos de ejecución del workflow del prototipo. Vercel bloqueado hasta verificar un control de gastos y cuotas fiables, incluso si existe una conexión OAuth.

## Pruebas progresivas

1. Ejecutar tests Python en GitHub Actions desde una rama aislada.
2. Abrir un PR en borrador y verificar SHA, checks y logs sin tocar `main`.
3. Primera tarea autónoma: leer el estado canónico y registrar el resultado de CI.
4. Segunda tarea autónoma: continuar desde otro turno, corregir un fallo deliberado y volver a verificar.
5. Añadir Playwright, Chromium, capturas de móvil/escritorio y logs de consola.
6. Probar que ChatGPT recibe los píxeles reales; un nombre de archivo/ZIP no basta para afirmar inspección visual.
7. Solo después integrar Vercel Sandbox con cuotas y freno duro de gasto verificables.
8. Simular pérdidas de respuesta, conflictos CAS y expiración de permisos.

No fusionar PR automáticamente ni dejar una tarea recurrente sin objetivo acotado.
