"""Dialog window for the popped-out intensity profile plot."""

from typing import Optional
from PyQt6.QtWidgets import QDialog, QVBoxLayout
from PyQt6.QtCore import Qt


class IntensityPlotDialog(QDialog):
    """Resizable dialog that hosts the IntensityPlotWidget when popped out.

    The dialog does *not* own the widget; it only provides a container.
    Closing the dialog automatically docks the widget back into the main window.
    """

    def __init__(self, plot_widget, parent=None):
        """Initialise the dialog.

        Args:
            plot_widget: The :class:`IntensityPlotWidget` instance to host.
            parent: Parent window (the main window).
        """
        super().__init__(parent)
        self.setWindowTitle("Intensity Profile - Gel_Boy")
        self.setMinimumSize(800, 600)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        self._plot_widget = plot_widget

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(plot_widget)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Window events
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        """Dock the plot back when the user closes the dialog."""
        self._plot_widget.dock_back()
        event.accept()
