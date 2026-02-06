"""Main application window for Gel_Boy."""

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    """Main application window for Gel_Boy."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle("Gel_Boy - Gel Electrophoresis Analyzer")
        self.setMinimumSize(1200, 800)
        
        self._setup_ui()
        self._create_menus()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        label = QLabel("Gel_Boy - Ready to analyze gel images!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        central_widget.setLayout(layout)
        
    def _create_menus(self) -> None:
        """Create application menus."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        # Edit menu
        edit_menu = self.menuBar().addMenu("&Edit")
        # Analysis menu
        analysis_menu = self.menuBar().addMenu("&Analysis")
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
