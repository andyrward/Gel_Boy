"""Coordinate conversion helpers for napari integration.

Utility functions for converting between gel-analysis coordinate formats
(x_position, width, y_start, y_end) and napari Shapes layer rectangle
format ([[y_min, x_min], [y_max, x_max], ...]).

Napari rectangles are represented as an array of four corner points in
(row, col) / (y, x) order:
    [[y_min, x_min],
     [y_min, x_max],
     [y_max, x_max],
     [y_max, x_min]]
"""

from typing import List, Tuple, Optional
import numpy as np

from gel_boy.models.lane import Lane


def lane_to_napari_rect(lane: Lane) -> np.ndarray:
    """Convert a :class:`Lane` to a napari Shapes rectangle.

    Args:
        lane: Lane object with x_start, x_end, y_start, y_end attributes.

    Returns:
        (4, 2) numpy array of corner points in (y, x) order suitable for
        passing to ``napari.Viewer.add_shapes``.
    """
    y_min = float(lane.y_start)
    y_max = float(lane.y_end)
    x_min = float(lane.x_start)
    x_max = float(lane.x_end)
    return np.array([
        [y_min, x_min],
        [y_min, x_max],
        [y_max, x_max],
        [y_max, x_min],
    ], dtype=float)


def napari_rect_to_lane_coords(
    rect: np.ndarray,
) -> Tuple[int, int, int, int]:
    """Extract lane coordinate bounds from a napari rectangle.

    Args:
        rect: (4, 2) array of corner points in (y, x) order as returned
              by the napari Shapes layer.

    Returns:
        Tuple of ``(x_position, width, y_start, y_end)`` where
        ``x_position`` is the lane centre column.
    """
    y_min = int(round(rect[:, 0].min()))
    y_max = int(round(rect[:, 0].max()))
    x_min = int(round(rect[:, 1].min()))
    x_max = int(round(rect[:, 1].max()))
    width = max(1, x_max - x_min)
    x_position = x_min + width // 2
    return x_position, width, y_min, y_max


def lanes_to_napari_rects(lanes: List[Lane]) -> List[np.ndarray]:
    """Convert a list of :class:`Lane` objects to napari rectangle arrays.

    Args:
        lanes: List of Lane objects.

    Returns:
        List of (4, 2) numpy arrays, one per lane.
    """
    return [lane_to_napari_rect(lane) for lane in lanes]


def pil_image_to_numpy(image) -> np.ndarray:
    """Convert a PIL Image to a numpy array suitable for napari.

    Handles 8-bit (L, RGB) and 16-bit (I, I;16) images.  16-bit images are
    returned as uint16; 8-bit images are returned as uint8.

    Args:
        image: PIL.Image.Image instance.

    Returns:
        2-D or 3-D numpy array.
    """
    import numpy as np

    if image.mode in ('I', 'I;16'):
        arr = np.array(image, dtype=np.int32)
        arr = np.clip(arr, 0, 65535).astype(np.uint16)
    elif image.mode == 'L':
        arr = np.array(image, dtype=np.uint8)
    elif image.mode == 'RGB':
        arr = np.array(image, dtype=np.uint8)
    else:
        arr = np.array(image.convert('RGB'), dtype=np.uint8)
    return arr


def lane_colors_for_napari(
    lanes: List[Lane],
    default_alpha: float = 0.3,
) -> Tuple[List, List]:
    """Build edge- and face-colour arrays for a napari Shapes layer.

    Args:
        lanes: List of Lane objects with ``color`` RGB tuples.
        default_alpha: Alpha value for the face (fill) colour.

    Returns:
        Tuple of ``(edge_colors, face_colors)`` where each element is a
        list of RGBA lists normalised to [0, 1].
    """
    edge_colors = []
    face_colors = []
    for lane in lanes:
        r, g, b = [c / 255.0 for c in lane.color]
        edge_colors.append([r, g, b, 1.0])
        face_colors.append([r, g, b, default_alpha])
    return edge_colors, face_colors


def build_lane_properties(lanes: List[Lane]) -> dict:
    """Build a properties dict for a napari Shapes layer from a lane list.

    Args:
        lanes: List of Lane objects.

    Returns:
        Dict with ``"label"`` key containing a list of lane label strings.
    """
    return {"label": [lane.label or f"Lane {i + 1}" for i, lane in enumerate(lanes)]}
