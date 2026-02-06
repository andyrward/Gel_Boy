"""Bottom panel widget for intensity profile visualization."""

from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class IntensityPanel(QWidget):
    """Bottom panel for displaying intensity profiles (placeholder for future)."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the intensity panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setMinimumHeight(150)
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Placeholder label
        self.placeholder_label = QLabel(
            "No lane selected - Intensity profile will appear here"
        )
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet("color: gray; font-style: italic;")
        
        layout.addWidget(self.placeholder_label)
        self.setLayout(layout)
