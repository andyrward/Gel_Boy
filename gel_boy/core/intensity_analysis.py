"""Intensity profile generation and analysis."""

from typing import Tuple, Optional, List
import numpy as np


def extract_lane_profile(
    image: np.ndarray,
    x_position: int,
    width: int,
    height: Optional[int] = None,
    method: str = 'mean'
) -> np.ndarray:
    """Extract intensity profile from a lane region.

    Args:
        image: Input gel image as numpy array (grayscale or RGB)
        x_position: X coordinate of lane center
        width: Width of the lane in pixels
        height: Height to extract (full image height if None)
        method: Aggregation method - 'mean' or 'median'

    Returns:
        1D numpy array of intensity values along the lane height

    Examples:
        >>> import numpy as np
        >>> img = np.ones((100, 200), dtype=np.uint8) * 128
        >>> profile = extract_lane_profile(img, 100, 40)
        >>> profile.shape
        (100,)
        >>> float(profile[0])
        128.0
    """
    if image is None or image.size == 0:
        return np.array([])

    # Convert to grayscale if RGB
    if image.ndim == 3:
        gray = np.mean(image, axis=2).astype(np.float32)
    else:
        gray = image.astype(np.float32)

    img_height, img_width = gray.shape
    half_width = width // 2

    # Compute lane boundaries
    x_start = max(0, x_position - half_width)
    x_end = min(img_width, x_position + half_width)

    if x_end <= x_start:
        return np.array([])

    # Determine y range
    y_end = height if height is not None else img_height
    y_end = min(y_end, img_height)

    # Extract lane region and aggregate across width
    region = gray[0:y_end, x_start:x_end]

    if method == 'median':
        profile = np.median(region, axis=1)
    else:
        profile = np.mean(region, axis=1)

    return profile


def smooth_profile(
    profile: np.ndarray,
    window_size: int = 5
) -> np.ndarray:
    """Smooth an intensity profile using moving average.

    Args:
        profile: Input intensity profile as 1D numpy array
        window_size: Size of smoothing window (must be odd and >= 1)

    Returns:
        Smoothed intensity profile

    Examples:
        >>> import numpy as np
        >>> profile = np.array([1.0, 2.0, 10.0, 2.0, 1.0])
        >>> smoothed = smooth_profile(profile, window_size=3)
        >>> smoothed.shape == profile.shape
        True
    """
    if profile is None or len(profile) == 0:
        return profile

    # Clamp window size
    window_size = max(1, window_size)
    if window_size >= len(profile):
        window_size = max(1, len(profile) // 2 * 2 - 1)

    if window_size <= 1:
        return profile.copy()

    kernel = np.ones(window_size) / window_size
    return np.convolve(profile, kernel, mode='same')


def normalize_profile(
    profile: np.ndarray,
    method: str = 'minmax'
) -> np.ndarray:
    """Normalize an intensity profile.

    Args:
        profile: Input intensity profile as 1D numpy array
        method: Normalization method - 'minmax' maps to [0,1],
                'zscore' standardizes to zero mean and unit variance

    Returns:
        Normalized intensity profile

    Examples:
        >>> import numpy as np
        >>> profile = np.array([0.0, 50.0, 100.0])
        >>> norm = normalize_profile(profile, 'minmax')
        >>> float(norm[0]), float(norm[-1])
        (0.0, 1.0)
    """
    if profile is None or len(profile) == 0:
        return profile

    if method == 'zscore':
        std = np.std(profile)
        if std == 0:
            return np.zeros_like(profile, dtype=float)
        return (profile - np.mean(profile)) / std
    else:  # minmax
        min_val = np.min(profile)
        max_val = np.max(profile)
        if max_val == min_val:
            return np.zeros_like(profile, dtype=float)
        return (profile - min_val) / (max_val - min_val)


def calculate_background(
    profile: np.ndarray,
    percentile: float = 10.0
) -> float:
    """Calculate background intensity level using percentile.

    Args:
        profile: Intensity profile as 1D numpy array
        percentile: Percentile to use for background estimation (0-100).
                    Lower values give a more conservative background estimate.

    Returns:
        Estimated background intensity value

    Examples:
        >>> import numpy as np
        >>> profile = np.array([10.0, 10.0, 10.0, 100.0, 10.0])
        >>> bg = calculate_background(profile, percentile=10.0)
        >>> bg <= 10.0
        True
    """
    if profile is None or len(profile) == 0:
        return 0.0

    return float(np.percentile(profile, percentile))


def calculate_profile_statistics(
    image: np.ndarray,
    x_position: int,
    width: int,
    height: Optional[int] = None
) -> dict:
    """Calculate comprehensive statistics for a lane profile.

    Args:
        image: Input gel image as numpy array
        x_position: X coordinate of lane center
        width: Width of the lane in pixels
        height: Height to extract (full image height if None)

    Returns:
        Dictionary with keys:
            - 'mean_profile': np.ndarray of mean intensity values
            - 'median_profile': np.ndarray of median intensity values
            - 'std_profile': np.ndarray of standard deviation values
            - 'background': float background estimate

    Examples:
        >>> import numpy as np
        >>> img = np.ones((50, 100), dtype=np.uint8) * 128
        >>> stats = calculate_profile_statistics(img, 50, 20)
        >>> 'mean_profile' in stats and 'median_profile' in stats
        True
    """
    mean_profile = extract_lane_profile(image, x_position, width, height, method='mean')
    median_profile = extract_lane_profile(image, x_position, width, height, method='median')

    # Compute std across width
    if image is None or image.size == 0:
        std_profile = np.array([])
    else:
        if image.ndim == 3:
            gray = np.mean(image, axis=2).astype(np.float32)
        else:
            gray = image.astype(np.float32)

        img_height, img_width = gray.shape
        half_width = width // 2
        x_start = max(0, x_position - half_width)
        x_end = min(img_width, x_position + half_width)
        y_end = height if height is not None else img_height
        y_end = min(y_end, img_height)

        if x_end > x_start:
            region = gray[0:y_end, x_start:x_end]
            std_profile = np.std(region, axis=1)
        else:
            std_profile = np.array([])

    background = calculate_background(mean_profile) if len(mean_profile) > 0 else 0.0

    return {
        'mean_profile': mean_profile,
        'median_profile': median_profile,
        'std_profile': std_profile,
        'background': background,
    }


def integrate_peak(
    profile: np.ndarray,
    start_idx: int,
    end_idx: int,
    background_points: Optional[List[Tuple[int, float]]] = None
) -> dict:
    """Integrate a peak region with optional linear background subtraction.

    Args:
        profile: Intensity profile array
        start_idx: Start index of integration region
        end_idx: End index of integration region (exclusive)
        background_points: List of (x, y) points for linear fit, or None

    Returns:
        Dictionary with keys:
            - 'raw_area': float, sum of intensities in region
            - 'corrected_area': float, area after background subtraction
            - 'background_slope': float, slope of background line
            - 'background_intercept': float, intercept of background line
            - 'peak_max': float, maximum intensity in region
            - 'peak_position': int, index of maximum intensity

    Examples:
        >>> import numpy as np
        >>> profile = np.array([1.0, 2.0, 5.0, 8.0, 5.0, 2.0, 1.0])
        >>> result = integrate_peak(profile, 1, 6)
        >>> result['raw_area'] > 0
        True
    """
    if profile is None or len(profile) == 0:
        return {
            'raw_area': 0.0, 'corrected_area': 0.0,
            'background_slope': 0.0, 'background_intercept': 0.0,
            'peak_max': 0.0, 'peak_position': 0,
        }

    # Clamp indices
    n = len(profile)
    start_idx = max(0, start_idx)
    end_idx = min(n, end_idx)

    if end_idx <= start_idx:
        return {
            'raw_area': 0.0, 'corrected_area': 0.0,
            'background_slope': 0.0, 'background_intercept': 0.0,
            'peak_max': 0.0, 'peak_position': start_idx,
        }

    region = profile[start_idx:end_idx]
    raw_area = float(np.trapezoid(region))
    peak_max = float(np.max(region))
    peak_position = start_idx + int(np.argmax(region))

    # Compute background
    slope = 0.0
    intercept = 0.0

    if background_points and len(background_points) >= 2:
        _, corrected, slope, intercept = subtract_linear_background(profile, background_points)
        corrected_region = corrected[start_idx:end_idx]
        corrected_area = float(np.trapezoid(np.maximum(corrected_region, 0)))
    else:
        # Use endpoints for simple linear background
        y0 = float(profile[start_idx])
        y1 = float(profile[end_idx - 1])
        x_vals = np.arange(end_idx - start_idx)
        background_line = y0 + (y1 - y0) * x_vals / max(1, end_idx - start_idx - 1)
        corrected_region = region - background_line
        corrected_area = float(np.trapezoid(np.maximum(corrected_region, 0)))
        slope = (y1 - y0) / max(1, end_idx - start_idx - 1)
        intercept = y0

    return {
        'raw_area': raw_area,
        'corrected_area': corrected_area,
        'background_slope': slope,
        'background_intercept': intercept,
        'peak_max': peak_max,
        'peak_position': peak_position,
    }


def subtract_linear_background(
    profile: np.ndarray,
    points: List[Tuple[int, float]]
) -> Tuple[np.ndarray, np.ndarray, float, float]:
    """Fit linear background from selected points and subtract.

    Args:
        profile: Intensity profile as 1D numpy array
        points: List of (x, y) coordinate pairs for linear fit

    Returns:
        Tuple of (background_line, corrected_profile, slope, intercept)

    Examples:
        >>> import numpy as np
        >>> profile = np.array([10.0, 11.0, 12.0, 20.0, 12.0, 11.0, 10.0])
        >>> bg_line, corrected, slope, intercept = subtract_linear_background(
        ...     profile, [(0, 10.0), (6, 10.0)])
        >>> float(corrected[3]) > 0
        True
    """
    if profile is None or len(profile) == 0 or len(points) < 2:
        slope = 0.0
        intercept = 0.0
        background_line = np.zeros_like(profile, dtype=float)
        return background_line, profile.copy().astype(float), slope, intercept

    xs = np.array([p[0] for p in points], dtype=float)
    ys = np.array([p[1] for p in points], dtype=float)

    # Fit linear: y = slope * x + intercept
    coeffs = np.polyfit(xs, ys, 1)
    slope = float(coeffs[0])
    intercept = float(coeffs[1])

    x_all = np.arange(len(profile), dtype=float)
    background_line = slope * x_all + intercept

    corrected = profile.astype(float) - background_line

    return background_line, corrected, slope, intercept
