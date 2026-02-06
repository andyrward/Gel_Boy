"""Project and session management model."""

from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path


class Project:
    """Represents a Gel_Boy project/session.
    
    Contains multiple gel images and project-wide settings.
    """
    
    def __init__(self, name: str, path: Optional[Path] = None):
        """Initialize a project.
        
        Args:
            name: Project name
            path: Path to project file
        """
        self.name = name
        self.path = path
        self.gel_images: List = []
        self.created_at = datetime.now()
        self.modified_at = datetime.now()
        self.settings: Dict = {}
        
    def add_gel_image(self, gel_image) -> None:
        """Add a gel image to the project.
        
        Args:
            gel_image: GelImage object to add
        """
        pass
        
    def remove_gel_image(self, index: int) -> None:
        """Remove a gel image from the project.
        
        Args:
            index: Index of the gel image to remove
        """
        pass
        
    def get_gel_image_count(self) -> int:
        """Get the number of gel images in the project.
        
        Returns:
            Number of gel images
        """
        pass
        
    def set_setting(self, key: str, value) -> None:
        """Set a project setting.
        
        Args:
            key: Setting key
            value: Setting value
        """
        pass
        
    def get_setting(self, key: str, default=None):
        """Get a project setting.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        pass
