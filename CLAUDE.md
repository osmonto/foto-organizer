# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                       # install deps (creates .venv)
uv run pre-commit install     # install git hooks (ruff + mypy on commit)

uv run ruff check --fix .     # lint
uv run ruff format .          # format
uv run mypy                   # strict type check (src + tests)
uv run pytest tests/ -v       # full test suite
uv run pytest tests/test_organizer.py -v                    # single file
uv run pytest tests/test_organizer.py::test_name -v         # single test
uv run python -m foto_organizer  # run the desktop app
```

UI tests use `pytest-qt` and run headless via `tests/conftest.py`, which forces
`QT_QPA_PLATFORM=offscreen`. On Linux CI runners this additionally requires system
Qt libs (`libegl1`, `libgl1`, `libxkbcommon0`, `libdbus-1-3`) — see `.github/workflows/ci.yml`.

Pre-commit runs ruff check/format and mypy on every commit; a failing hook blocks the
commit, so fix the issue and re-commit rather than bypassing it.

## Architecture

PySide6 desktop app for organizing photos/videos with **safe backup as the core
invariant**: nothing in the source directory is ever deleted or moved without an
explicit, verified copy existing first. Three layers, one-directional dependency
(`ui` → `core`/`utils`, `core` does not import `ui`):

- `src/foto_organizer/core/` — all file-mutating logic, framework-agnostic, fully
  unit-testable without Qt.
- `src/foto_organizer/ui/` — PySide6 windows/dialogs; each dialog wraps one `core`
  operation and adds the confirmation UX around it.
- `src/foto_organizer/utils/` — EXIF metadata, hashing, app settings persistence
  (`~/.foto_organizer/settings.json`), logging (loguru).

### The core safety pipeline (`core/`)

This is the one thing to understand before touching any core module — the modules
form a pipeline where each step's output gates the next:

1. **`scanner.py`** — `scan_directory()` is read-only; produces `MediaFile` records
   (photo/video detected by extension).
2. **`backup.py`** — `run_backup()` copies (`shutil.copy2`, never moves) source →
   destination, writing `backup_manifest.json` with per-file MD5+SHA256 hashes
   (`ManifestEntry`). Refuses if source == destination.
3. **`verifier.py`** — `verify_backup()` *recomputes* hashes from the manifest's
   recorded paths at verification time (never trusts cached values) and classifies
   each entry `OK` / `HASH_MISMATCH` / `MISSING`. `is_fully_verified()` is all-or-
   nothing: a single non-`OK` entry blocks deletion of the *entire* backup set.
4. **`cleaner.py`** — `delete_verified_sources()` is the only place source files are
   deleted, and only if `is_fully_verified()` is true, the exact confirmation phrase
   `"CONFIRMAR"` was passed, and it writes an `AuditRecord` (with timestamp) to
   `audit_log.jsonl` for every deletion.
5. **`organizer.py`** — date-based organization (copy + rename, never touches
   source) and duplicate detection (`build_duplicate_report`, hash-based grouping).
   `quarantine_duplicates()` is the **one exception** to "core never mutates
   source": it moves non-kept duplicates into `duplicados_a_revisar/` inside the
   source tree (user's explicit choice over direct deletion or requiring a prior
   verified backup). Moving files this way silently invalidates any existing
   `backup_manifest.json` for that source (moved paths become "missing" on next
   verify) — the UI layer is responsible for warning about this (see
   `main_window.py::_find_duplicates`), core does not check for it itself.

### UI layer conventions

- `main_window.py` is the only place that wires `core` functions to menu actions
  and background execution (`ui/workers.py::OperationWorker`, a `QThread` wrapper;
  cancellation is `terminate()` + `wait()`).
- Every scan-triggering action (scan / find duplicates / organize) must go through
  `MainWindow._scan_and_populate_gallery()` rather than calling `scan_directory()`
  directly, or the gallery thumbnails silently fail to refresh (this was a real bug
  — F-32's gallery only updated from one of three call sites).
- Dialogs that gate a destructive action layer confirmation deliberately:
  `VerificationDialog` requires both a reviewed-checkbox and typing `"CONFIRMAR"`
  before `delete_verified_sources` will run.
- `help_dialog.py` (`Ayuda → Guía de uso`) documents each menu action for end users;
  keep it and the README's "Guía de uso" section in sync when adding/changing a
  Herramientas action.

## Workflow notes

- Work proceeds phase-by-phase per `PLAN_DE_TRABAJO.md`; don't jump ahead to a
  later phase without being asked.
- Conventional commits; features land as PRs against `main` (see CI in
  `.github/workflows/ci.yml`: `lint` → `type-check` → `tests` on ubuntu+windows).
- Keep `CHANGELOG.md` (Keep a Changelog format) updated for user-facing changes.
