# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/);
versionado según [SemVer](https://semver.org/lang/es/).

## [Unreleased]

### Fixed

- La galería (F-32) no se refrescaba si el usuario iba directo a "Buscar
  duplicados" u "Organizar por fecha" sin pasar antes por "Escanear origen":
  esas dos acciones poblaban `_media_files` pero nunca llamaban a
  `gallery.set_media_files`. Ahora las tres rutas de escaneo comparten
  `_scan_and_populate_gallery`.

### Added

- Diálogo de duplicados (F-35): al aceptar, los duplicados no elegidos para
  conservar (`quarantine_duplicates` en `organizer.py`) se mueven a
  `duplicados_a_revisar/` dentro del origen, preservando la ruta relativa
  para evitar colisiones de nombre. Antes el diálogo solo permitía marcar
  cuál conservar, sin ninguna acción real de limpieza conectada.
- Fase 4 — Tests de integración (`test_integration.py`, F-44): flujo completo
  scan → backup → verify (sin borrado del origen) y flujo con detección de
  duplicados combinado con organización por fecha, ejercitando varios
  módulos del core juntos en vez de aislados.
- Fase 3 — Interfaz de usuario (PySide6): `main_window.py` (ventana
  principal con menús Archivo/Herramientas/Ayuda, árbol de carpetas del
  origen, selección de directorios origen/backup con validación de que
  no coincidan, panel de progreso con log en vivo vía sink de loguru y
  cancelación de operaciones en segundo plano), `gallery_view.py` (grid
  de thumbnails con selección múltiple y vista previa ampliada al hacer
  doble click), `verification_dialog.py` (reporte de verificación con
  doble confirmación: checkbox de revisión + frase "CONFIRMAR" antes de
  habilitar el borrado del origen), `duplicates_dialog.py` (grupos de
  duplicados confirmados por hash, con selección manual de cuál
  conservar) y `settings_dialog.py` (formato de carpetas, extensiones
  incluidas/excluidas y directorio de backup por defecto, persistidos en
  `~/.foto_organizer/settings.json`). Tests con `pytest-qt` para los
  cinco componentes de UI.
- Fase 2 — Organización de archivos: `metadata.py` (EXIF: fecha de captura,
  GPS, modelo de cámara; duración de vídeo vía ffprobe con fallback si no
  está disponible), `organizer.py` (organización por fecha `YYYY/MM-Mes`,
  renombrado `YYYYMMDD_HHMMSS_nombre.ext` con manejo de colisiones,
  detección de duplicados por hash SHA256 y por heurística nombre+tamaño,
  reporte de duplicados) y `thumbnails.py` (thumbnails 256x256 con cache en
  disco, solo fotos por ahora). Tests para los tres módulos (F-42/F-43 +
  cobertura adicional de metadata y thumbnails).
- Fase 1 — Core de backup seguro: `scanner.py` (detección de fotos/vídeos),
  `hasher.py` (MD5+SHA256), `backup.py` (copia con manifiesto JSON),
  `verifier.py` (verificación origen vs. destino, estados OK/HASH_MISMATCH/
  MISSING) y `cleaner.py` (borrado del origen solo tras verificación 100% OK,
  con confirmación explícita y log de auditoría). Tests unitarios para los
  cuatro módulos (F-40, F-41, F-42 + tests de cleaner).
- Fase 0 — Infraestructura del proyecto: uv, Ruff, mypy (estricto),
  pre-commit, GitHub Actions CI, estructura `src/` y logging con loguru.
