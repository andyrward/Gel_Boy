"""Band model for gel electrophoresis analysis."""

from typing import Optional


class Band:
    """Represents a single band in a gel lane.
    
    A band has position, intensity, and optional molecular weight information.
    """
    
    def __init__(
        self,
        position: float,
        intensity: float,
        width: float,
        lane_index: Optional[int] = None
    ):
        """Initialize a band.
        
        Args:
            position: Position along the lane (pixels from top)
            intensity: Peak intensity value
            width: Band width in pixels
            lane_index: Index of the parent lane
        """
        self.position = position
        self.intensity = intensity
        self.width = width
        self.lane_index = lane_index
        self.molecular_weight: Optional[float] = None
        self.label: Optional[str] = None
        
    def set_molecular_weight(self, mw: float) -> None:
        """Set the molecular weight for this band.
        
        Args:
            mw: Molecular weight in kDa
        """
        pass
        
    def set_label(self, label: str) -> None:
        """Set a label for this band.
        
        Args:
            label: Text label for the band
        """
        pass
        
    def get_relative_intensity(self, total_intensity: float) -> float:
        """Calculate relative intensity as percentage of total.
        
        Args:
            total_intensity: Total intensity of all bands in lane
            
        Returns:
            Relative intensity as percentage (0-100)
        """
        pass
