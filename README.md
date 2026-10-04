# SGR — Prototipo (Etapa 3)

Prototipo del Sistema de Gestión de Resultados (SGR) para Delegaciones Municipales — Ilustre Municipalidad de La Serena. Cubre el Sprint 2 "Operación principal" del backlog: registro de actividades, evidencias, validación y agenda colectiva de compromisos.

## Stack

- Python 3.12 + Django 6.1
- SQLite (desarrollo local)
- Entorno gestionado con `uv`

## Cómo correr el proyecto

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Apps

- `operacion` — modelos y vistas del Sprint 2 (Actividad, Evidencia, Validación, Compromiso)
