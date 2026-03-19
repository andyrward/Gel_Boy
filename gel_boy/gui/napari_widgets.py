"""magicgui widget definitions for Gel_Boy napari integration.

Each function decorated with ``@magicgui`` becomes a dock widget that can be
added to a napari viewer.  The widgets call the existing core analysis
modules unchanged; only the UI wiring is new here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

import numpy as np

if TYPE_CHECKING:
    import napari


# ---------------------------------------------------------------------------
# Lane detection widget
# ---------------------------------------------------------------------------

def make_lane_detection_widget(app: "GelBoyNapariApp"):
    """Create and return the lane-detection magicgui widget.

    Args:
        app: The :class:`GelBoyNapariApp` instance that owns this widget.

    Returns:
        A magicgui widget ready to be docked into the napari viewer.
    """
    from magicgui import magicgui

    @magicgui(
        call_button="Detect Lanes",
        min_lane_width={"label": "Min width (px)", "min": 5, "max": 500},
        max_lane_width={"label": "Max width (px)", "min": 5, "max": 500},
    )
    def detect_lanes_widget(
        min_lane_width: int = 20,
        max_lane_width: int = 100,
    ) -> None:
        """Automatically detect lanes in the loaded gel image."""
        app.detect_lanes(
            min_lane_width=min_lane_width,
            max_lane_width=max_lane_width,
        )

    return detect_lanes_widget


# ---------------------------------------------------------------------------
# Profile calculation widget
# ---------------------------------------------------------------------------

def make_profile_widget(app: "GelBoyNapariApp"):
    """Create and return the intensity-profile magicgui widget.

    Args:
        app: The :class:`GelBoyNapariApp` instance that owns this widget.

    Returns:
        A magicgui widget ready to be docked into the napari viewer.
    """
    from magicgui import magicgui

    @magicgui(
        call_button="Calculate Profiles",
        method={"choices": ["mean", "median"], "label": "Aggregation"},
        smooth_window={"label": "Smooth window", "min": 1, "max": 51},
    )
    def profile_widget(
        method: str = "mean",
        smooth_window: int = 5,
    ) -> None:
        """Extract and display intensity profiles for all defined lanes."""
        app.calculate_profiles(method=method, smooth_window=smooth_window)

    return profile_widget


# ---------------------------------------------------------------------------
# Peak integration widget
# ---------------------------------------------------------------------------

def make_peak_integration_widget(app: "GelBoyNapariApp"):
    """Create and return the peak-integration magicgui widget.

    Args:
        app: The :class:`GelBoyNapariApp` instance that owns this widget.

    Returns:
        A magicgui widget ready to be docked into the napari viewer.
    """
    from magicgui import magicgui

    @magicgui(
        call_button="Integrate Peaks",
        height_threshold={"label": "Min height (0–1)", "min": 0.0, "max": 1.0, "step": 0.01},
        min_distance={"label": "Min distance (px)", "min": 1, "max": 500},
    )
    def peak_integration_widget(
        height_threshold: float = 0.05,
        min_distance: int = 10,
    ) -> None:
        """Detect and integrate peaks in the current intensity profiles."""
        app.integrate_peaks(
            height_threshold=height_threshold,
            min_distance=min_distance,
        )

    return peak_integration_widget


# ---------------------------------------------------------------------------
# Image operations widget
# ---------------------------------------------------------------------------

def make_image_ops_widget(app: "GelBoyNapariApp"):
    """Create and return the image-operations magicgui widget.

    Args:
        app: The :class:`GelBoyNapariApp` instance that owns this widget.

    Returns:
        A magicgui widget ready to be docked into the napari viewer.
    """
    from magicgui import magicgui

    @magicgui(
        call_button="Apply",
        operation={"choices": [
            "Rotate CW 90°",
            "Rotate CCW 90°",
            "Rotate 180°",
            "Flip Horizontal",
            "Flip Vertical",
            "Invert Colors",
            "Reset Image",
        ], "label": "Operation"},
    )
    def image_ops_widget(
        operation: str = "Rotate CW 90°",
    ) -> None:
        """Apply a geometric or tonal operation to the gel image."""
        app.apply_image_operation(operation)

    return image_ops_widget
