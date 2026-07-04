"""Configuración compartida de pytest: fuerza Qt a modo offscreen para tests de UI."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
