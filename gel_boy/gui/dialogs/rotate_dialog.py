"""Dialog for precise image rotation."""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QPushButton, QCheckBox, QComboBox, QGroupBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt


class RotateDialog(QDialog):
    """Dialog for rotating image by precise angle.
    
    Allows user to specify rotation angle with decimal precision,
    choose whether to expand canvas, and select background fill color.
    """
    
    def __init__(self, parent: Optional[QDialog] = None):
        """Initialize the rotation dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Rotate Image")
        self.setModal(True)
        self.setMinimumWidth(350)
        
        self._angle = 0.0
        self._expand = True
        self._fillcolor = "black"
        
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Angle input group
        angle_group = QGroupBox("Rotation Angle")
        angle_layout = QVBoxLayout()
        
        angle_container = QHBoxLayout()
        angle_label = QLabel("Angle:")
        angle_container.addWidget(angle_label)
        
        self.angle_spinbox = QDoubleSpinBox()
        self.angle_spinbox.setMinimum(-360.0)
        self.angle_spinbox.setMaximum(360.0)
        self.angle_spinbox.setValue(0.0)
        self.angle_spinbox.setDecimals(1)
        self.angle_spinbox.setSingleStep(1.0)
        self.angle_spinbox.setSuffix("°")
        self.angle_spinbox.setToolTip("Rotation angle in degrees (positive = counter-clockwise)")
        angle_container.addWidget(self.angle_spinbox)
        
        angle_layout.addLayout(angle_container)
        
        # Quick angle buttons
        quick_buttons_label = QLabel("Quick angles:")
        angle_layout.addWidget(quick_buttons_label)
        
        quick_buttons = QHBoxLayout()
        
        btn_45 = QPushButton("45°")
        btn_45.clicked.connect(lambda: self.angle_spinbox.setValue(45.0))
        quick_buttons.addWidget(btn_45)
        
        btn_90 = QPushButton("90°")
        btn_90.clicked.connect(lambda: self.angle_spinbox.setValue(90.0))
        quick_buttons.addWidget(btn_90)
        
        btn_180 = QPushButton("180°")
        btn_180.clicked.connect(lambda: self.angle_spinbox.setValue(180.0))
        quick_buttons.addWidget(btn_180)
        
        btn_270 = QPushButton("270°")
        btn_270.clicked.connect(lambda: self.angle_spinbox.setValue(270.0))
        quick_buttons.addWidget(btn_270)
        
        angle_layout.addLayout(quick_buttons)
        
        angle_group.setLayout(angle_layout)
        layout.addWidget(angle_group)
        
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        # Expand canvas checkbox
        self.expand_checkbox = QCheckBox("Expand canvas to fit rotated image")
        self.expand_checkbox.setChecked(True)
        self.expand_checkbox.setToolTip(
            "If checked, canvas will be expanded to show entire rotated image.\n"
            "If unchecked, rotated image will be cropped to original dimensions."
        )
        options_layout.addWidget(self.expand_checkbox)
        
        # Background color selection
        color_container = QHBoxLayout()
        color_label = QLabel("Fill color:")
        color_container.addWidget(color_label)
        
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Black", "White"])
        self.color_combo.setToolTip("Color for areas outside original image")
        color_container.addWidget(self.color_combo)
        color_container.addStretch()
        
        options_layout.addLayout(color_container)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Info label
        info_label = QLabel(
            "<i>Note: Positive angles rotate counter-clockwise,<br>"
            "negative angles rotate clockwise.</i>"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def get_angle(self) -> float:
        """Get the selected rotation angle.
        
        Returns:
            Rotation angle in degrees
        """
        return self.angle_spinbox.value()
        
    def get_expand(self) -> bool:
        """Get whether to expand canvas.
        
        Returns:
            True if canvas should be expanded, False otherwise
        """
        return self.expand_checkbox.isChecked()
        
    def get_fillcolor(self) -> str:
        """Get the selected fill color.
        
        Returns:
            Fill color name ("black" or "white")
        """
        color_text = self.color_combo.currentText().lower()
        return color_text
        
    @staticmethod
    def get_rotation_parameters(parent=None) -> Optional[tuple]:
        """Static method to get rotation parameters.
        
        Args:
            parent: Parent widget
            
        Returns:
            Tuple of (angle, expand, fillcolor) if accepted, None if canceled
        """
        dialog = RotateDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return (
                dialog.get_angle(),
                dialog.get_expand(),
                dialog.get_fillcolor()
            )
        return None
