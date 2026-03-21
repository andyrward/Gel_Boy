"""Gel_Boy - Gel Electrophoresis Image Analysis Tool."""

import sys


def _run_napari() -> None:
    """Launch the napari-based Gel_Boy application."""
    from gel_boy.gui.napari_main import GelBoyNapariApp

    app = GelBoyNapariApp()
    app.run()


def _run_legacy() -> None:
    """Launch the legacy PyQt6 Gel_Boy application (deprecated)."""
    from PyQt6.QtWidgets import QApplication
    from gel_boy.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Gel_Boy")
    app.setOrganizationName("Gel_Boy")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


def main() -> None:
    """Run the Gel_Boy application.

    Pass ``--legacy`` as a command-line argument to use the deprecated
    PyQt6 QGraphicsView interface instead of the default napari viewer.
    """
    if "--legacy" in sys.argv:
        _run_legacy()
    else:
        _run_napari()


if __name__ == "__main__":
    main()
