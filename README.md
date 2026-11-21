# Cloud Goal Runner (piloto)

Prototipo de un agente de desarrollo de software coordinado por ChatGPT Chat/Tasks, con estado persistente, código en GitHub y ejecución mediante GitHub Actions. No necesita un ordenador local ni usa una API de modelos.

## Seguridad

- Repositorio **público y experimental**. No guardar tokens, datos personales ni código privado.
- Los cambios del agente se mantienen en ramas `pilot/*` y se revisan mediante PR. No hay auto-merge ni despliegue público.
- Presupuesto adicional autorizado: **0 €**.
- Vercel Sandbox **deshabilitado** hasta demostrar permisos, cuotas y barrera efectiva de gastos.
- Una tarea automática no debe repetir operaciones remotas de resultado incierto.

## Qué contiene

- `goal_runner/state.py`: transiciones verificables de objetivos y eventos idempotentes en memoria.
- `goal_runner/governor.py`: regla conservadora para GitHub Actions y Vercel.
- `tests/`: pruebas unitarias deterministas.
- `.github/workflows/ci.yml`: CI cloud sin secretos.
- `docs/CHATGPT_TASK_PROMPT.md`: protocolo de reentrada.
- `docs/ARCHITECTURE_AND_ROADMAP.md`: fases y pruebas pendientes.

## Pruebas

```sh
python3 -m unittest discover -s tests -v
```

**Alcance:** pasar CI demuestra compilación/pruebas del núcleo, no autonomía de programación ni evaluación visual. No se crea ninguna tarea recurrente por el mero hecho de subir este código.
