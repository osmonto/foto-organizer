# 📋 Plan de Trabajo — Organizador de Fotos y Vídeos (Desktop)
> **Stack:** Python 3.12+ · PySide6 · uv · Ruff · mypy · pytest · Git/GitHub

---

## 🛠️ Stack Tecnológico

| Herramienta | Propósito |
|---|---|
| **Python 3.12+** | Lenguaje principal |
| **PySide6** | UI de escritorio (Qt6) |
| **uv** | Gestor de paquetes (moderno, rápido, reemplaza pip/poetry) |
| **Ruff** | Linting + Formatting (reemplaza flake8, black, isort) |
| **mypy** | Type checking estático |
| **pre-commit** | Git hooks automáticos (ejecuta Ruff + mypy antes de cada commit) |
| **pytest + pytest-qt** | Tests unitarios y de UI |
| **Pillow / pillow-heif** | Procesamiento de imágenes (thumbnails, EXIF) |
| **ffmpeg-python** | Procesamiento de vídeos |
| **tqdm** | Barras de progreso en CLI |
| **loguru** | Logging moderno |

---

## 📁 Estructura del Proyecto

```
foto-organizer/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI: lint + type-check + tests
├── src/
│   └── foto_organizer/
│       ├── __init__.py
│       ├── core/
│       │   ├── backup.py       # Lógica de backup seguro
│       │   ├── scanner.py      # Escaneo de directorios
│       │   ├── organizer.py    # Lógica de organización
│       │   ├── verifier.py     # Verificación de integridad
│       │   └── cleaner.py      # Borrado seguro (solo tras verificación)
│       ├── ui/
│       │   ├── main_window.py
│       │   ├── gallery_view.py
│       │   └── settings_dialog.py
│       └── utils/
│           ├── metadata.py     # Lectura EXIF/metadata
│           ├── hasher.py       # MD5/SHA256 para verificación
│           └── logger.py       # Config loguru
├── tests/
│   ├── test_backup.py
│   ├── test_scanner.py
│   ├── test_verifier.py
│   └── test_organizer.py
├── .pre-commit-config.yaml
├── pyproject.toml              # Config uv + Ruff + mypy + pytest
├── CHANGELOG.md
├── README.md
└── PLAN_DE_TRABAJO.md
```

---

## 🚀 Features por Implementar

### FASE 0 — Setup e Infraestructura
**Branch:** `feat/setup-infrastructure`

- [x] **F-00** Inicializar repositorio GitHub con `.gitignore` para Python *(git local; repo remoto pendiente)*
- [x] **F-01** Configurar `uv` como gestor de paquetes (`pyproject.toml`)
- [x] **F-02** Configurar **Ruff** (linting + formatting)
  - Reglas: `E, W, F, I, N, UP, B, SIM, TCH`
  - Line length: 88
- [x] **F-03** Configurar **mypy** en modo estricto (`strict = true`)
- [x] **F-04** Configurar **pre-commit** hooks
  - Hook 1: `ruff check --fix`
  - Hook 2: `ruff format`
  - Hook 3: `mypy`
- [x] **F-05** Configurar **GitHub Actions** CI pipeline
  - Trigger: push + pull_request
  - Jobs: lint → type-check → tests
- [x] **F-06** Crear estructura de directorios del proyecto
- [x] **F-07** Configurar **loguru** para logging centralizado
- [x] **F-08** Escribir `README.md` inicial con instrucciones de setup

---

### FASE 1 — Core: Backup Seguro (CRÍTICO ⚠️)
**Branch:** `feat/safe-backup-system`

> ⚠️ **Regla de oro:** NUNCA se borra el original. El borrado solo ocurre tras verificación explícita.

- [x] **F-10** `scanner.py` — Escanear directorio fuente
  - Detectar fotos: `.jpg`, `.jpeg`, `.png`, `.heic`, `.raw`, `.dng`, `.tiff`
  - Detectar vídeos: `.mp4`, `.mov`, `.avi`, `.mkv`, `.m4v`
  - Retornar lista tipada con metadata básica
- [x] **F-11** `hasher.py` — Calcular hash MD5 + SHA256 de cada archivo
  - Usado para verificar integridad del backup
- [x] **F-12** `backup.py` — Copiar archivos a directorio de backup
  - Copiar con `shutil.copy2` (preserva metadata del filesystem)
  - Crear manifiesto JSON con: ruta original, ruta copia, hash, fecha
  - **Nunca mover, siempre copiar**
- [x] **F-13** `verifier.py` — Verificar integridad del backup
  - Comparar hash origen vs. hash destino archivo por archivo
  - Generar reporte de verificación (`verification_report.json`)
  - Estados posibles: `OK`, `HASH_MISMATCH`, `MISSING`
- [x] **F-14** `cleaner.py` — Borrado seguro del origen
  - **Solo ejecutable si** `verifier.py` retorna 100% OK
  - Requiere confirmación explícita del usuario (doble confirmación)
  - Registra cada borrado en log de auditoría

---

### FASE 2 — Core: Organización de Archivos
**Branch:** `feat/file-organizer`

- [ ] **F-20** `metadata.py` — Extraer metadata EXIF/ID3
  - Fecha de captura (EXIF DateTimeOriginal)
  - GPS coordinates (si existen)
  - Modelo de cámara/dispositivo
  - Duración (vídeos)
- [ ] **F-21** Organización por fecha
  - Estructura: `YYYY/MM-NombreMes/` (ej: `2024/03-Marzo/`)
  - Fallback a fecha de modificación si no hay EXIF
- [ ] **F-22** Detección de duplicados
  - Comparar por hash SHA256
  - Comparar por nombre + tamaño como heurística rápida
  - Generar reporte de duplicados antes de actuar
- [ ] **F-23** Renombrado automático de archivos
  - Formato: `YYYYMMDD_HHMMSS_original_name.ext`
  - Manejo de colisiones (añadir sufijo `_01`, `_02`, etc.)
- [ ] **F-24** Generación de thumbnails
  - Para galería UI: 256x256px
  - Cache local de thumbnails (evitar regeneración)

---

### FASE 3 — Interfaz de Usuario (PySide6)
**Branch:** `feat/ui-main-window`

- [ ] **F-30** Ventana principal (`main_window.py`)
  - Menú: Archivo, Herramientas, Ayuda
  - Barra de estado con progreso
  - Layout: panel izquierdo (árbol carpetas) + panel derecho (galería)
- [ ] **F-31** Selector de directorio fuente y destino
  - Diálogo nativo del OS
  - Validación: directorios no pueden ser el mismo
- [ ] **F-32** Vista de galería (`gallery_view.py`)
  - Grid de thumbnails scrolleable
  - Click → vista previa ampliada
  - Selección múltiple
- [ ] **F-33** Panel de progreso
  - Barra de progreso por operación
  - Log en tiempo real de operaciones
  - Botón cancelar operación
- [ ] **F-34** Diálogo de verificación pre-borrado
  - Muestra reporte de verificación
  - Requiere escribir "CONFIRMAR" para proceder
  - Checkbox "He revisado el reporte completo"
- [ ] **F-35** Vista de duplicados
  - Muestra pares/grupos de duplicados
  - Selección manual de cuál conservar
- [ ] **F-36** Pantalla de configuración (`settings_dialog.py`)
  - Formato de organización de carpetas
  - Extensiones a incluir/excluir
  - Directorio de backup por defecto

---

### FASE 4 — Tests
**Branch:** `feat/tests`

- [x] **F-40** Tests unitarios `test_backup.py`
  - Test: copia correcta de archivos
  - Test: generación correcta del manifiesto JSON
  - Test: backup no modifica original
- [x] **F-41** Tests unitarios `test_verifier.py`
  - Test: verificación OK con archivos íntegros
  - Test: detección de hash mismatch
  - Test: detección de archivo faltante
- [x] **F-42** Tests unitarios `test_scanner.py`
  - Test: detección correcta de formatos
  - Test: manejo de directorios vacíos
  - Test: manejo de archivos sin extensión
- [ ] **F-43** Tests unitarios `test_organizer.py`
  - Test: organización correcta por fecha EXIF
  - Test: fallback a fecha de modificación
  - Test: manejo de colisiones de nombres
- [ ] **F-44** Tests de integración
  - Flujo completo: scan → backup → verify → (no delete)
  - Flujo con duplicados

---

### FASE 5 — Distribución
**Branch:** `feat/packaging`

- [ ] **F-50** Empaquetar con **PyInstaller** o **Nuitka**
  - Binario standalone (sin necesidad de Python instalado)
- [ ] **F-51** Crear instalador macOS (`.dmg`) / Windows (`.exe`)
- [ ] **F-52** GitHub Releases automático via Actions

---

## 📏 Reglas de Git

```
main          ← solo código verificado y testeado
develop       ← integración de features
feat/*        ← una branch por feature
fix/*         ← corrección de bugs
```

**Formato de commits (Conventional Commits):**
```
feat(backup): add SHA256 integrity verification
fix(scanner): handle files without extension
docs(readme): add installation instructions
test(verifier): add hash mismatch detection test
chore(ci): add mypy to GitHub Actions pipeline
```

---

## ⚙️ Comandos de Desarrollo

```bash
# Instalar dependencias
uv sync

# Ejecutar linting + formato
uv run ruff check --fix .
uv run ruff format .

# Type checking
uv run mypy src/

# Tests
uv run pytest tests/ -v

# Ejecutar aplicación
uv run python -m foto_organizer

# Pre-commit (automático en cada commit)
pre-commit run --all-files
```

---

## 🔒 Reglas de Seguridad (irrompibles)

1. **El directorio fuente es de solo lectura** durante scan y backup
2. **El backup siempre precede** a cualquier otra operación
3. **La verificación de integridad es obligatoria** antes de mostrar opción de borrado
4. **El borrado requiere doble confirmación** del usuario
5. **Todo borrado queda registrado** en log de auditoría con timestamp

---

## 📊 Orden de Implementación Sugerido

```
F-00→F-08 (Setup)  →  F-10→F-14 (Backup Core)  →  F-40→F-41 (Tests backup)
     ↓
F-20→F-24 (Organizer)  →  F-42→F-44 (Tests organizer)
     ↓
F-30→F-36 (UI)
     ↓
F-50→F-52 (Distribución)
```

---

*Documento generado: 2026-05-23 | Versión: 1.0*
