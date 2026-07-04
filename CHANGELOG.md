# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/);
versionado según [SemVer](https://semver.org/lang/es/).

## [Unreleased]

### Added

- Fase 1 — Core de backup seguro: `scanner.py` (detección de fotos/vídeos),
  `hasher.py` (MD5+SHA256), `backup.py` (copia con manifiesto JSON),
  `verifier.py` (verificación origen vs. destino, estados OK/HASH_MISMATCH/
  MISSING) y `cleaner.py` (borrado del origen solo tras verificación 100% OK,
  con confirmación explícita y log de auditoría). Tests unitarios para los
  cuatro módulos (F-40, F-41, F-42 + tests de cleaner).
- Fase 0 — Infraestructura del proyecto: uv, Ruff, mypy (estricto),
  pre-commit, GitHub Actions CI, estructura `src/` y logging con loguru.
