"""Lane detection algorithms for gel electrophoresis images."""

from typing import List, Tuple, Optional
import numpy as np

# Smoothing window constants for detect_lanes
_MIN_SMOOTHING_WINDOW = 5       # floor for convolution kernel size
_WINDOW_SCALE_FACTOR = 4        # divides min_lane_width to derive kernel size

# Threshold above which a column is considered part of a lane
_LANE_DETECTION_THRESHOLD = 0.3

# Boundary-refinement search-margin constants for refine_lane_boundaries
_MIN_SEARCH_MARGIN = 10         # floor for the pixel search margin around each edge
_MARGIN_SCALE_FACTOR = 3        # divides lane width to derive the search margin


def detect_lanes(
    image: np.ndarray,
    min_lane_width: int = 20,
    max_lane_width: int = 100
) -> List[Tuple[int, int]]:
    """Automatically detect lanes in a gel image using intensity projection.

    Uses vertical projection (sum across rows) to find lane regions.
    Detects peaks in the projection and identifies lane centers and widths.

    Args:
        image: Input gel image as numpy array (grayscale or RGB)
        min_lane_width: Minimum lane width in pixels
        max_lane_width: Maximum lane width in pixels

    Returns:
        List of (x_position, width) tuples for detected lanes

    Examples:
        >>> import numpy as np
        >>> # Create a simple test image with two lanes
        >>> img = np.zeros((100, 200), dtype=np.uint8)
        >>> img[:, 40:80] = 200  # Lane 1
        >>> img[:, 120:160] = 200  # Lane 2
        >>> lanes = detect_lanes(img)
        >>> len(lanes)
        2
    """
    if image is None or image.size == 0:
        return []

    # Convert to grayscale if RGB
    if image.ndim == 3:
        gray = np.mean(image, axis=2).astype(np.float32)
    else:
        gray = image.astype(np.float32)

    # Compute vertical projection (sum across rows)
    projection = np.sum(gray, axis=0)

    # Smooth the projection to reduce noise
    window = max(_MIN_SMOOTHING_WINDOW, min_lane_width // _WINDOW_SCALE_FACTOR)
    smoothed = np.convolve(projection, np.ones(window) / window, mode='same')

    # Normalize projection
    if smoothed.max() > smoothed.min():
        normalized = (smoothed - smoothed.min()) / (smoothed.max() - smoothed.min())
    else:
        return []

    # Find peaks using simple threshold-based approach
    above = normalized > _LANE_DETECTION_THRESHOLD

    # Find contiguous regions above threshold
    lanes = []
    in_region = False
    start = 0

    for i, val in enumerate(above):
        if val and not in_region:
            in_region = True
            start = i
        elif not val and in_region:
            in_region = False
            width = i - start
            if min_lane_width <= width <= max_lane_width:
                x_center = start + width // 2
                lanes.append((x_center, width))

    # Handle case where region extends to edge
    if in_region:
        width = len(above) - start
        if min_lane_width <= width <= max_lane_width:
            x_center = start + width // 2
            lanes.append((x_center, width))

    return lanes


def refine_lane_boundaries(
    image: np.ndarray,
    initial_lanes: List[Tuple[int, int]]
) -> List[Tuple[int, int]]:
    """Refine lane boundaries using gradient analysis.

    Uses the gradient of the intensity projection to find precise lane edges
    and adjusts boundaries to align with actual content edges.

    Args:
        image: Input gel image as numpy array
        initial_lanes: Initial lane positions as list of (x_position, width)

    Returns:
        Refined list of (x_position, width) tuples

    Examples:
        >>> import numpy as np
        >>> img = np.zeros((100, 200), dtype=np.uint8)
        >>> img[:, 40:80] = 200
        >>> refined = refine_lane_boundaries(img, [(60, 40)])
        >>> len(refined)
        1
    """
    if not initial_lanes or image is None or image.size == 0:
        return initial_lanes

    # Convert to grayscale if RGB
    if image.ndim == 3:
        gray = np.mean(image, axis=2).astype(np.float32)
    else:
        gray = image.astype(np.float32)

    image_width = gray.shape[1]
    projection = np.sum(gray, axis=0)

    # Compute gradient of projection
    gradient = np.gradient(projection)

    refined = []
    for x_pos, width in initial_lanes:
        half = width // 2
        search_margin = max(_MIN_SEARCH_MARGIN, width // _MARGIN_SCALE_FACTOR)

        # Search window for left edge (strong positive gradient)
        left_start = max(0, x_pos - half - search_margin)
        left_end = max(0, x_pos - half + search_margin)

        # Search window for right edge (strong negative gradient)
        right_start = min(image_width, x_pos + half - search_margin)
        right_end = min(image_width, x_pos + half + search_margin)

        # Find left edge: position of maximum gradient (rising edge)
        if left_end > left_start:
            left_segment = gradient[left_start:left_end]
            left_edge = left_start + int(np.argmax(left_segment))
        else:
            left_edge = x_pos - half

        # Find right edge: position of minimum gradient (falling edge)
        if right_end > right_start:
            right_segment = gradient[right_start:right_end]
            right_edge = right_start + int(np.argmin(right_segment))
        else:
            right_edge = x_pos + half

        # Ensure valid boundaries
        left_edge = max(0, left_edge)
        right_edge = min(image_width - 1, right_edge)

        if right_edge > left_edge:
            new_width = right_edge - left_edge
            new_center = left_edge + new_width // 2
            refined.append((new_center, new_width))
        else:
            refined.append((x_pos, width))

    return refined


def validate_lanes(
    lanes: List[Tuple[int, int]],
    image_width: int
) -> bool:
    """Validate that lane positions are reasonable.

    Checks that:
    - All lanes are within image bounds
    - No lanes overlap
    - Lane widths are positive

    Args:
        lanes: List of (x_position, width) tuples
        image_width: Width of the gel image in pixels

    Returns:
        True if all lanes are valid, False otherwise

    Examples:
        >>> validate_lanes([(50, 30), (120, 30)], 200)
        True
        >>> validate_lanes([(50, 30), (60, 30)], 200)  # Overlapping
        False
    """
    if not lanes:
        return True

    for x_pos, width in lanes:
        # Width must be positive
        if width <= 0:
            return False

        # Lane must be within image bounds
        left = x_pos - width // 2
        right = x_pos + width // 2
        if left < 0 or right > image_width:
            return False

    # Check for overlapping lanes (sort by x position first)
    sorted_lanes = sorted(lanes, key=lambda l: l[0])
    for i in range(len(sorted_lanes) - 1):
        x1, w1 = sorted_lanes[i]
        x2, w2 = sorted_lanes[i + 1]
        right1 = x1 + w1 // 2
        left2 = x2 - w2 // 2
        if right1 > left2:
            return False

    return True
