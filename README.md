# 📸 foto-organizer

Aplicación de escritorio (PySide6) para organizar fotos y vídeos con **backup seguro**:
nunca se borra un original sin antes copiar, verificar la integridad (SHA256) y
pedir doble confirmación al usuario.

> Plan completo de features y fases: [PLAN_DE_TRABAJO.md](PLAN_DE_TRABAJO.md)

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes)

## Setup

```bash
# Clonar e instalar dependencias (crea .venv automáticamente)
uv sync

# Instalar los git hooks (Ruff + mypy antes de cada commit)
uv run pre-commit install
```

## Comandos de desarrollo

```bash
uv run ruff check --fix .   # linting
uv run ruff format .        # formateo
uv run mypy                 # type checking (estricto)
uv run pytest tests/ -v     # tests
uv run python -m foto_organizer  # ejecutar la aplicación
```

## Estructura

```
src/foto_organizer/
├── core/    # backup, escaneo, organización, verificación, borrado seguro
├── ui/      # ventanas y vistas PySide6
└── utils/   # metadata EXIF, hashing, logging
tests/       # pytest + pytest-qt
```

## Reglas de seguridad (irrompibles)

1. El directorio fuente es de **solo lectura** durante scan y backup.
2. El backup **siempre precede** a cualquier otra operación.
3. La verificación de integridad es **obligatoria** antes de ofrecer el borrado.
4. El borrado requiere **doble confirmación** del usuario.
5. Todo borrado queda registrado en un **log de auditoría** con timestamp.
