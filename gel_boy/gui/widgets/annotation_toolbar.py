"""Annotation toolbar for gel images."""

from typing import Optional
from PyQt6.QtWidgets import QToolBar, QWidget
from PyQt6.QtCore import pyqtSignal


class AnnotationToolbar(QToolBar):
    """Toolbar for annotation tools.
    
    Provides tools for adding labels, markers, and annotations to gel images.
    """
    
    tool_selected = pyqtSignal(str)  # Emits name of selected tool
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the annotation toolbar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_tools()
        
    def _setup_tools(self) -> None:
        """Set up annotation tools."""
        pass
        
    def select_tool(self, tool_name: str) -> None:
        """Select an annotation tool.
        
        Args:
            tool_name: Name of the tool to select
        """
        pass
