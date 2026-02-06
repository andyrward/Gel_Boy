"""Molecular weight ladder calibration dialog."""

from typing import Optional, List
from PyQt6.QtWidgets import QDialog, QWidget


class CalibrationDialog(QDialog):
    """Dialog for calibrating molecular weight ladder.
    
    Allows users to define molecular weight standards and calibrate
    the gel image for accurate band size estimation.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the calibration dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("MW Ladder Calibration")
        self.standards: List = []
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Set up the dialog user interface."""
        pass
        
    def add_standard(self, position: float, molecular_weight: float) -> None:
        """Add a molecular weight standard.
        
        Args:
            position: Position in the gel (pixels or mm)
            molecular_weight: Molecular weight in kDa
        """
        pass
        
    def calculate_calibration(self) -> None:
        """Calculate calibration curve from standards."""
        pass
