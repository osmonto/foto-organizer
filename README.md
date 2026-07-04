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

## Guía de uso

La misma guía está disponible dentro de la app en `Ayuda -> Guía de uso`.

1. **Seleccionar origen** (`Archivo -> Seleccionar origen...`): carpeta con
   las fotos/vídeos a organizar. Nunca se modifica hasta el paso 5, y solo
   tras verificar el backup.
2. **Seleccionar destino de backup** (`Archivo -> Seleccionar destino de
   backup...`): carpeta distinta al origen donde se copiarán los archivos.
3. **Escanear origen** (`Herramientas -> Escanear origen`): recorre el
   origen y muestra los archivos en la galería con miniaturas.
4. **Ejecutar backup** (`Herramientas -> Ejecutar backup`): copia todo al
   destino y genera `backup_manifest.json` con el hash SHA256 de cada
   archivo. El origen no se toca.
5. **Verificar backup y borrar origen** (`Herramientas -> Verificar backup
   y borrar origen...`): recalcula hashes y compara contra el manifiesto.
   Solo si el 100% verifica correctamente se habilita el borrado, que
   además exige marcar una casilla de revisión y escribir "CONFIRMAR".
   Cada borrado queda en `audit_log.jsonl`.
6. **Buscar duplicados** (`Herramientas -> Buscar duplicados`): agrupa
   archivos con hash idéntico; eliges cuál conservar por grupo y el resto
   se mueve a `duplicados_a_revisar/` dentro del origen (no se borran
   automáticamente). Si ya existía un backup, la app avisa que hay que
   repetirlo porque las rutas cambiaron.
7. **Organizar por fecha** (`Herramientas -> Organizar por fecha...`):
   copia los archivos a una carpeta destino en subcarpetas `AAAA/MM-Mes`
   según la fecha EXIF, renombrando a `AAAAMMDD_HHMMSS_nombre.ext`.
8. **Configuración** (`Herramientas -> Configuración...`): formato de
   carpetas, extensiones incluidas/excluidas y backup por defecto.
9. **Cancelar operación**: botón en el panel de Progreso para detener un
   backup u organización en curso (las operaciones rápidas pueden acabar
   antes de que llegues a cancelarlas).

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
