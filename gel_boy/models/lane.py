"""Lane model for gel electrophoresis analysis."""

from typing import List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np


@dataclass
class IntegrationRegion:
    """Stores the result of a peak integration.

    Attributes:
        start: Start index of integration region
        end: End index of integration region
        raw_area: Raw integrated area (no background correction)
        corrected_area: Background-corrected integrated area, or None
    """
    start: int
    end: int
    raw_area: float
    corrected_area: Optional[float] = None


class Lane:
    """Represents a single lane in a gel electrophoresis image.

    A lane contains multiple bands and has properties like position,
    width, and intensity profile.

    Attributes:
        x_position: X coordinate of lane center (pixels)
        width: Width of the lane (pixels)
        height: Height of the lane (pixels)
        x_start: Left boundary of the lane
        x_end: Right boundary of the lane
        y_start: Top boundary of the lane (for ROI support)
        y_end: Bottom boundary of the lane (for ROI support)
        label: Optional name for the lane
        color: RGB color tuple for visual identification
        bands: List of Band objects in this lane
        intensity_profile: 1D array of mean intensity values (legacy)
        mean_profile: 1D array of mean intensity values along lane height
        median_profile: 1D array of median intensity values along lane height
        integration_regions: List of IntegrationRegion results
        background_points: List of (x, y) pairs for background correction
    """

    def __init__(
        self,
        x_position: int,
        width: int,
        height: int,
        label: str = "",
        color: Tuple[int, int, int] = (0, 120, 215),
        y_start: int = 0,
        y_end: Optional[int] = None,
    ):
        """Initialize a lane.

        Args:
            x_position: X coordinate of the lane center
            width: Width of the lane in pixels
            height: Height of the lane in pixels
            label: Optional name/label for the lane
            color: RGB color tuple for visual identification
            y_start: Top boundary of the lane
            y_end: Bottom boundary (defaults to y_start + height)
        """
        self.x_position = x_position
        self.width = width
        self.height = height
        self.label = label
        self.color = color

        # Boundaries
        self.x_start: int = max(0, x_position - width // 2)
        self.x_end: int = x_position + width // 2
        self.y_start: int = y_start
        self.y_end: int = y_end if y_end is not None else y_start + height

        # Bands
        self.bands: List = []

        # Intensity profiles
        self.intensity_profile: Optional[np.ndarray] = None  # legacy
        self.mean_profile: Optional[np.ndarray] = None
        self.median_profile: Optional[np.ndarray] = None

        # Analysis data
        self.integration_regions: List[IntegrationRegion] = []
        self.background_points: List[Tuple[int, float]] = []

    def add_band(self, band) -> None:
        """Add a band to this lane.

        Args:
            band: Band object to add
        """
        self.bands.append(band)

    def remove_band(self, index: int) -> None:
        """Remove a band from this lane by index.

        Args:
            index: Index of the band to remove

        Raises:
            IndexError: If index is out of range
        """
        if 0 <= index < len(self.bands):
            del self.bands[index]
        else:
            raise IndexError(f"Band index {index} out of range for lane with {len(self.bands)} bands")

    def get_intensity_profile(self) -> Optional[np.ndarray]:
        """Return the stored mean intensity profile for this lane.

        Returns:
            Intensity profile as numpy array, or None if not set
        """
        return self.mean_profile if self.mean_profile is not None else self.intensity_profile

    def set_intensity_profile(self, profile: np.ndarray, profile_type: str = 'mean') -> None:
        """Set the intensity profile for this lane.

        Args:
            profile: Intensity profile as numpy array
            profile_type: Type of profile - 'mean' or 'median'
        """
        if profile_type == 'median':
            self.median_profile = profile
        else:
            self.mean_profile = profile
            self.intensity_profile = profile  # keep legacy attribute in sync

    def __repr__(self) -> str:
        return (
            f"Lane(x_position={self.x_position}, width={self.width}, "
            f"height={self.height}, label={self.label!r})"
        )
