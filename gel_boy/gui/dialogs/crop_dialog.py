"""Confirmation dialog for the image crop operation."""

from typing import Optional, Tuple
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDialogButtonBox
)
from PyQt6.QtCore import Qt


class CropDialog(QDialog):
    """Modal confirmation dialog shown before applying a crop.

    Displays the size of the selected crop region and asks the user
    to confirm or cancel the operation.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        parent: Optional[QDialog] = None,
    ):
        """Initialise the dialog.

        Args:
            x: Left edge of the crop rectangle in image pixels.
            y: Top edge of the crop rectangle in image pixels.
            width: Width of the crop rectangle in image pixels.
            height: Height of the crop rectangle in image pixels.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Crop Image")
        self.setModal(True)

        self._x = x
        self._y = y
        self._width = width
        self._height = height

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the dialog layout."""
        layout = QVBoxLayout()
        layout.setSpacing(12)

        title_label = QLabel("<b>Crop to selection?</b>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        info_label = QLabel(
            f"Selected region: <b>{self._width} × {self._height}</b> pixels\n"
            f"Top-left corner: ({self._x}, {self._y})"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        note_label = QLabel(
            "<i>Note: existing lanes will be cleared after cropping.</i>"
        )
        note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(note_label)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Static helper
    # ------------------------------------------------------------------

    @staticmethod
    def confirm_crop(
        x: int,
        y: int,
        width: int,
        height: int,
        parent=None,
    ) -> bool:
        """Show the dialog and return True if the user clicked OK.

        Args:
            x: Left edge of the crop rectangle in image pixels.
            y: Top edge of the crop rectangle in image pixels.
            width: Width of the crop rectangle in image pixels.
            height: Height of the crop rectangle in image pixels.
            parent: Parent widget.

        Returns:
            ``True`` if the crop was confirmed, ``False`` otherwise.
        """
        dialog = CropDialog(x, y, width, height, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted
