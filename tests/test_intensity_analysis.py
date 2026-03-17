"""Tests for intensity profile analysis functions."""

import numpy as np
import pytest
from gel_boy.core.intensity_analysis import (
    extract_lane_profile,
    smooth_profile,
    normalize_profile,
    calculate_background,
    calculate_profile_statistics,
    integrate_peak,
    subtract_linear_background,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gaussian_profile(length: int = 100, center: float = 50, sigma: float = 10,
                     amplitude: float = 100, baseline: float = 10) -> np.ndarray:
    """Generate a Gaussian intensity peak."""
    x = np.arange(length, dtype=float)
    return baseline + amplitude * np.exp(-0.5 * ((x - center) / sigma) ** 2)


def make_uniform_image(
    height: int = 100,
    width: int = 200,
    value: int = 128,
) -> np.ndarray:
    """Create a uniform grayscale image."""
    return np.full((height, width), value, dtype=np.uint8)


# ---------------------------------------------------------------------------
# extract_lane_profile
# ---------------------------------------------------------------------------

class TestExtractLaneProfile:

    def test_basic_mean(self):
        """Mean profile from uniform image equals the pixel value."""
        img = make_uniform_image(value=128)
        profile = extract_lane_profile(img, x_position=100, width=40)
        assert profile.shape == (100,)
        assert np.allclose(profile, 128.0)

    def test_basic_median(self):
        """Median profile from uniform image equals the pixel value."""
        img = make_uniform_image(value=200)
        profile = extract_lane_profile(img, x_position=100, width=40, method='median')
        assert profile.shape == (100,)
        assert np.allclose(profile, 200.0)

    def test_height_parameter(self):
        """height parameter limits the extracted profile length."""
        img = make_uniform_image(height=100, value=50)
        profile = extract_lane_profile(img, x_position=100, width=20, height=50)
        assert profile.shape == (50,)

    def test_rgb_image(self):
        """Works with RGB images (converts to grayscale)."""
        gray = make_uniform_image(height=50, width=100, value=150)
        rgb = np.stack([gray, gray, gray], axis=2)
        profile = extract_lane_profile(rgb, x_position=50, width=20)
        assert profile.shape == (50,)
        assert np.allclose(profile, 150.0)

    def test_empty_returns_empty(self):
        """Empty image returns empty array."""
        result = extract_lane_profile(np.array([]), x_position=0, width=10)
        assert len(result) == 0

    def test_lane_at_left_edge(self):
        """Lane center near left edge clamps correctly."""
        img = make_uniform_image(height=50, width=100, value=64)
        profile = extract_lane_profile(img, x_position=5, width=40)
        assert len(profile) > 0

    def test_lane_at_right_edge(self):
        """Lane center near right edge clamps correctly."""
        img = make_uniform_image(height=50, width=100, value=64)
        profile = extract_lane_profile(img, x_position=95, width=40)
        assert len(profile) > 0

    def test_mean_vs_median_different_for_skewed(self):
        """Mean and median differ when a subset of columns has outliers."""
        img = np.ones((50, 100), dtype=np.uint8) * 50
        # Only the leftmost column of the lane region is an outlier
        img[0, 40] = 250
        mean_profile = extract_lane_profile(img, 50, 20, method='mean')
        median_profile = extract_lane_profile(img, 50, 20, method='median')
        # Row 0 mean should differ from median due to the single outlier column
        assert float(mean_profile[0]) != float(median_profile[0])


# ---------------------------------------------------------------------------
# smooth_profile
# ---------------------------------------------------------------------------

class TestSmoothProfile:

    def test_preserves_shape(self):
        """Smoothing preserves profile length."""
        profile = np.random.rand(100)
        smoothed = smooth_profile(profile, window_size=5)
        assert smoothed.shape == profile.shape

    def test_constant_profile_unchanged(self):
        """Smoothing a constant profile returns the same constant in the interior."""
        profile = np.full(100, 42.0)
        smoothed = smooth_profile(profile, window_size=7)
        # Interior values should be exactly 42; edges may differ due to 'same' convolution
        assert np.allclose(smoothed[7:-7], 42.0, atol=1e-6)

    def test_window_size_one_unchanged(self):
        """Window size of 1 returns the original profile."""
        profile = np.array([1.0, 3.0, 2.0, 5.0, 4.0])
        smoothed = smooth_profile(profile, window_size=1)
        assert np.allclose(smoothed, profile)

    def test_reduces_peak_amplitude(self):
        """Smoothing reduces the peak amplitude of a spike."""
        profile = np.zeros(50)
        profile[25] = 100.0
        smoothed = smooth_profile(profile, window_size=5)
        assert smoothed[25] < 100.0

    def test_empty_returns_empty(self):
        """Empty profile returns unchanged."""
        result = smooth_profile(np.array([]), window_size=5)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# normalize_profile
# ---------------------------------------------------------------------------

class TestNormalizeProfile:

    def test_minmax_range(self):
        """minmax normalization maps to [0, 1]."""
        profile = np.array([10.0, 50.0, 100.0, 30.0])
        norm = normalize_profile(profile, method='minmax')
        assert pytest.approx(float(norm.min()), abs=1e-6) == 0.0
        assert pytest.approx(float(norm.max()), abs=1e-6) == 1.0

    def test_zscore_mean_zero(self):
        """zscore normalization gives zero mean."""
        profile = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        norm = normalize_profile(profile, method='zscore')
        assert pytest.approx(float(np.mean(norm)), abs=1e-6) == 0.0

    def test_zscore_std_one(self):
        """zscore normalization gives unit standard deviation."""
        profile = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        norm = normalize_profile(profile, method='zscore')
        assert pytest.approx(float(np.std(norm)), abs=1e-6) == 1.0

    def test_constant_profile_minmax(self):
        """Constant profile minmax returns zeros."""
        profile = np.full(10, 5.0)
        norm = normalize_profile(profile, method='minmax')
        assert np.all(norm == 0.0)

    def test_empty_returns_empty(self):
        """Empty profile returns empty."""
        result = normalize_profile(np.array([]), method='minmax')
        assert len(result) == 0


# ---------------------------------------------------------------------------
# calculate_background
# ---------------------------------------------------------------------------

class TestCalculateBackground:

    def test_all_same_value(self):
        """Background of uniform profile equals the value."""
        profile = np.full(100, 42.0)
        bg = calculate_background(profile, percentile=10.0)
        assert pytest.approx(bg, abs=1.0) == 42.0

    def test_low_percentile_gives_low_value(self):
        """10th percentile is lower than 90th percentile."""
        profile = np.arange(100, dtype=float)
        bg10 = calculate_background(profile, percentile=10.0)
        bg90 = calculate_background(profile, percentile=90.0)
        assert bg10 < bg90

    def test_returns_float(self):
        """Returns a float value."""
        profile = np.array([10.0, 20.0, 30.0])
        result = calculate_background(profile, percentile=10.0)
        assert isinstance(result, float)

    def test_empty_returns_zero(self):
        """Empty profile returns 0.0."""
        result = calculate_background(np.array([]), percentile=10.0)
        assert result == 0.0


# ---------------------------------------------------------------------------
# calculate_profile_statistics
# ---------------------------------------------------------------------------

class TestCalculateProfileStatistics:

    def test_keys_present(self):
        """Result dict contains expected keys."""
        img = make_uniform_image(value=100)
        stats = calculate_profile_statistics(img, x_position=100, width=20)
        assert 'mean_profile' in stats
        assert 'median_profile' in stats
        assert 'std_profile' in stats
        assert 'background' in stats

    def test_uniform_image_mean_equals_median(self):
        """For uniform image, mean profile equals median profile."""
        img = make_uniform_image(value=128)
        stats = calculate_profile_statistics(img, x_position=100, width=40)
        assert np.allclose(stats['mean_profile'], stats['median_profile'])

    def test_std_zero_for_uniform(self):
        """Std profile is zero for a uniform image."""
        img = make_uniform_image(value=50)
        stats = calculate_profile_statistics(img, x_position=100, width=40)
        assert np.allclose(stats['std_profile'], 0.0)

    def test_background_value(self):
        """Background is positive for non-zero image."""
        img = make_uniform_image(value=80)
        stats = calculate_profile_statistics(img, x_position=100, width=40)
        assert stats['background'] > 0


# ---------------------------------------------------------------------------
# integrate_peak
# ---------------------------------------------------------------------------

class TestIntegratePeak:

    def test_basic_integration(self):
        """integrate_peak returns positive area for a peak."""
        profile = gaussian_profile(length=100, center=50, amplitude=100, baseline=0)
        result = integrate_peak(profile, start_idx=30, end_idx=70)
        assert result['raw_area'] > 0

    def test_result_keys(self):
        """Result dict contains all required keys."""
        profile = np.ones(50) * 10.0
        result = integrate_peak(profile, 10, 40)
        for key in ('raw_area', 'corrected_area', 'background_slope',
                    'background_intercept', 'peak_max', 'peak_position'):
            assert key in result, f"Missing key: {key}"

    def test_peak_position_in_range(self):
        """peak_position index is within the integration region."""
        profile = gaussian_profile(length=100, center=50, amplitude=100, baseline=0)
        result = integrate_peak(profile, start_idx=30, end_idx=70)
        assert 30 <= result['peak_position'] < 70

    def test_peak_max_is_maximum(self):
        """peak_max equals the maximum in the region."""
        profile = np.array([1.0, 2.0, 8.0, 5.0, 1.0, 0.0])
        result = integrate_peak(profile, start_idx=0, end_idx=5)
        assert pytest.approx(result['peak_max']) == 8.0

    def test_background_correction_reduces_area(self):
        """Background correction reduces area when background is non-zero."""
        baseline = 10.0
        profile = gaussian_profile(length=100, center=50, amplitude=50, baseline=baseline)
        bg_pts = [(20, baseline), (80, baseline)]
        result_corrected = integrate_peak(profile, 30, 70, background_points=bg_pts)
        result_raw = integrate_peak(profile, 30, 70, background_points=None)
        assert result_corrected['corrected_area'] < result_raw['raw_area']

    def test_empty_region_returns_zeros(self):
        """Empty integration region returns zeroed dict."""
        profile = np.ones(50)
        result = integrate_peak(profile, start_idx=25, end_idx=25)
        assert result['raw_area'] == 0.0

    def test_empty_profile_returns_zeros(self):
        """Empty profile returns zeroed dict."""
        result = integrate_peak(np.array([]), 0, 5)
        assert result['raw_area'] == 0.0

    def test_clamping_out_of_bounds(self):
        """Indices beyond profile length are clamped."""
        profile = np.ones(20) * 5.0
        result = integrate_peak(profile, start_idx=-5, end_idx=100)
        assert result['raw_area'] > 0


# ---------------------------------------------------------------------------
# subtract_linear_background
# ---------------------------------------------------------------------------

class TestSubtractLinearBackground:

    def test_basic_subtraction(self):
        """Subtracting flat background leaves the peak."""
        baseline = 10.0
        profile = gaussian_profile(length=100, center=50, amplitude=50, baseline=baseline)
        pts = [(10, baseline), (90, baseline)]
        bg_line, corrected, slope, intercept = subtract_linear_background(profile, pts)

        # Corrected peak center should be approximately the amplitude
        assert pytest.approx(float(corrected[50]), abs=5.0) == 50.0

    def test_slope_from_tilted_background(self):
        """Slope is non-zero for a tilted background."""
        # Profile with linearly increasing background: y = 0.5*x
        profile = np.arange(100, dtype=float) * 0.5
        pts = [(0, 0.0), (99, 49.5)]
        bg_line, corrected, slope, intercept = subtract_linear_background(profile, pts)
        assert pytest.approx(slope, abs=0.1) == 0.5

    def test_corrected_profile_length(self):
        """Corrected profile has same length as input."""
        profile = np.random.rand(80) * 100
        pts = [(10, 20.0), (70, 25.0)]
        bg_line, corrected, slope, intercept = subtract_linear_background(profile, pts)
        assert len(corrected) == len(profile)

    def test_flat_background_slope_zero(self):
        """Flat background gives slope ≈ 0."""
        profile = np.ones(50) * 100.0
        pts = [(5, 100.0), (45, 100.0)]
        bg_line, corrected, slope, intercept = subtract_linear_background(profile, pts)
        assert pytest.approx(slope, abs=1e-6) == 0.0

    def test_insufficient_points_returns_original(self):
        """Fewer than 2 points returns original profile unchanged."""
        profile = np.array([1.0, 2.0, 3.0])
        bg_line, corrected, slope, intercept = subtract_linear_background(profile, [(1, 2.0)])
        assert np.allclose(corrected, profile)

    def test_returns_four_values(self):
        """Function returns exactly 4 values."""
        profile = np.ones(20)
        result = subtract_linear_background(profile, [(5, 1.0), (15, 1.0)])
        assert len(result) == 4


# ---------------------------------------------------------------------------
# Lane model
# ---------------------------------------------------------------------------

class TestLaneModel:

    def test_lane_init(self):
        """Lane initializes with correct attributes."""
        from gel_boy.models.lane import Lane
        lane = Lane(x_position=100, width=40, height=200)
        assert lane.x_position == 100
        assert lane.width == 40
        assert lane.height == 200
        assert lane.bands == []
        assert lane.label == ""

    def test_add_remove_band(self):
        """add_band and remove_band work correctly."""
        from gel_boy.models.lane import Lane
        lane = Lane(50, 30, 100)
        lane.add_band("band1")
        lane.add_band("band2")
        assert len(lane.bands) == 2
        lane.remove_band(0)
        assert len(lane.bands) == 1
        assert lane.bands[0] == "band2"

    def test_set_get_intensity_profile_mean(self):
        """set_intensity_profile and get_intensity_profile work for mean."""
        from gel_boy.models.lane import Lane
        lane = Lane(50, 30, 100)
        profile = np.array([1.0, 2.0, 3.0])
        lane.set_intensity_profile(profile, profile_type='mean')
        result = lane.get_intensity_profile()
        assert np.allclose(result, profile)

    def test_set_get_intensity_profile_median(self):
        """set_intensity_profile and get_intensity_profile work for median."""
        from gel_boy.models.lane import Lane
        lane = Lane(50, 30, 100)
        profile = np.array([4.0, 5.0, 6.0])
        lane.set_intensity_profile(profile, profile_type='median')
        assert np.allclose(lane.median_profile, profile)

    def test_integration_region_dataclass(self):
        """IntegrationRegion dataclass stores values correctly."""
        from gel_boy.models.lane import IntegrationRegion
        region = IntegrationRegion(start=10, end=50, raw_area=1234.5, corrected_area=1100.0)
        assert region.start == 10
        assert region.end == 50
        assert region.raw_area == 1234.5
        assert region.corrected_area == 1100.0

    def test_lane_boundaries(self):
        """Lane x_start/x_end computed from x_position and width."""
        from gel_boy.models.lane import Lane
        lane = Lane(x_position=100, width=40, height=50)
        assert lane.x_start == 80
        assert lane.x_end == 120

    def test_lane_repr(self):
        """Lane has a meaningful string representation."""
        from gel_boy.models.lane import Lane
        lane = Lane(x_position=50, width=20, height=100, label="Test")
        r = repr(lane)
        assert "Lane" in r
        assert "50" in r
