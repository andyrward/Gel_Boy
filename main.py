"""Gel_Boy - Gel Electrophoresis Image Analysis Tool."""

import sys
from PyQt6.QtWidgets import QApplication
from gel_boy.gui.main_window import MainWindow


def main():
    """Run the Gel_Boy application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Gel_Boy")
    app.setOrganizationName("Gel_Boy")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
