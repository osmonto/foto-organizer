"""Guía de uso dentro de la aplicación (menú Ayuda)."""

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

HELP_TEXT = """
# Guía de uso

## 1. Seleccionar origen
`Archivo -> Seleccionar origen...` Elige la carpeta con las fotos y vídeos
que quieres organizar. Esta carpeta nunca se modifica hasta que tú decidas
borrar el origen (paso 4), y solo tras verificar el backup.

## 2. Seleccionar destino de backup
`Archivo -> Seleccionar destino de backup...` Elige dónde se copiarán los
archivos. Debe ser una carpeta distinta al origen.

## 3. Escanear origen
`Herramientas -> Escanear origen` Recorre el origen y muestra los archivos
encontrados en la galería central, con miniaturas.

## 4. Ejecutar backup
`Herramientas -> Ejecutar backup` Copia todos los archivos del origen al
destino de backup y genera un manifiesto (`backup_manifest.json`) con el
hash SHA256 de cada archivo. **El origen nunca se toca en este paso.**

## 5. Verificar backup y borrar origen
`Herramientas -> Verificar backup y borrar origen...` Recalcula los hashes
del backup y los compara contra el manifiesto. Solo si el 100% de los
archivos verifica correctamente se habilita el borrado del origen, y aun
así se pide marcar una casilla de revisión y escribir la frase
"CONFIRMAR". Cada borrado queda registrado en un log de auditoría
(`audit_log.jsonl`) junto al backup.

## 6. Buscar duplicados
`Herramientas -> Buscar duplicados` Agrupa archivos con contenido idéntico
(mismo hash). Para cada grupo eliges cuál conservar; el resto se mueve a
`duplicados_a_revisar/` dentro del origen (no se borran automáticamente).

**Importante:** si ya ejecutaste un backup antes de mover duplicados a
cuarentena, vuelve a ejecutar el backup después, porque las rutas de esos
archivos cambiaron y el manifiesto anterior quedó desactualizado.

## 7. Organizar por fecha
`Herramientas -> Organizar por fecha...` Copia los archivos a una carpeta
destino organizados en subcarpetas `AAAA/MM-Mes` según la fecha de
captura (EXIF), renombrando con el patrón
`AAAAMMDD_HHMMSS_nombre.ext`.

## 8. Configuración
`Herramientas -> Configuración...` Ajusta el formato de carpetas,
extensiones incluidas/excluidas y el directorio de backup por defecto.

## 9. Cancelar una operación
El botón "Cancelar operación" del panel de Progreso (parte inferior de la
ventana) detiene un backup u organización en curso. Las operaciones
rápidas pueden terminar antes de que llegues a cancelarlas.

## Reglas de seguridad

- El origen es de solo lectura durante escaneo y backup.
- El backup siempre precede a cualquier borrado.
- La verificación de integridad es obligatoria antes de ofrecer el borrado.
- El borrado requiere doble confirmación explícita.
- Todo borrado queda en un log de auditoría con fecha y hora.
"""


class HelpDialog(QDialog):
    """Diálogo modal de solo lectura con la guía de uso de la aplicación."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Guía de uso")
        self.resize(560, 600)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setMarkdown(HELP_TEXT)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(browser)
        layout.addWidget(buttons)
