# Enhanced Image Adjustment Features

This document describes the new ImageJ-style brightness/contrast controls with histogram display and precise rotation capabilities added to Gel_Boy.

## Features

### 1. Histogram Display with Intensity Adjustment

The new `BrightnessContrastWidget` provides a comprehensive image adjustment interface similar to ImageJ:

#### Histogram View
- **Live histogram display** showing the intensity distribution of the current image
- Works with both grayscale and RGB images
- Automatically updates when a new image is loaded
- Cached for performance (doesn't recalculate on every slider movement)

#### Intensity Window Controls
- **Minimum slider** (0-255): Sets the lower bound of the intensity display range
- **Maximum slider** (0-255): Sets the upper bound of the intensity display range
- Visual feedback on histogram:
  - Red dashed line indicates minimum value
  - Blue dashed line indicates maximum value
  - Green shaded region shows the active intensity range

#### Brightness & Contrast Controls
- **Brightness slider** (0-200%): Shifts the entire intensity range
- **Contrast slider** (0-200%): Stretches/compresses the intensity range
- Both sliders work in combination with intensity windowing

#### Action Buttons
- **Auto**: Automatically adjusts min/max based on histogram (1st and 99th percentile)
- **Reset**: Resets all controls to default values (min=0, max=255, brightness=100%, contrast=100%)

### 2. Precise Image Rotation

A new rotation dialog allows precise angle input beyond 90° increments:

#### Rotation Dialog Features
- **Decimal degree input**: Enter any angle from -360° to +360° with 0.1° precision
- **Quick angle buttons**: Fast selection of common angles (45°, 90°, 180°, 270°)
- **Expand canvas option**: Choose whether to expand the canvas to fit the entire rotated image
- **Fill color selection**: Choose black or white background for areas outside the original image
- **Clear instructions**: Visual feedback about rotation direction (positive = counter-clockwise)

#### Access
- **Menu**: Image → Rotate by Angle...
- **Keyboard shortcut**: Ctrl+Shift+T

### 3. Performance Optimizations

#### LUT-Based Processing
All brightness/contrast/min/max adjustments use lookup tables (LUTs) for efficient processing:
- Single-pass application of all adjustments
- Fast numpy-based operations
- Smooth slider interaction without lag
- Responsive even with large images

#### Histogram Caching
- Histogram is calculated only when image loads or changes
- Not recalculated during slider movements
- Efficient memory usage

## Usage Examples

### Adjusting Image Brightness and Contrast

1. **Load an image** using File → Open Image
2. The histogram will automatically display in the side panel
3. Adjust sliders to modify the image:
   - Move **Min/Max** sliders to change the intensity window
   - Move **Brightness** slider to make the image lighter/darker
   - Move **Contrast** slider to increase/decrease contrast
4. Watch the histogram update with visual markers showing your adjustments
5. Use **Auto** button for automatic optimal settings
6. Use **Reset** button to return to original settings

### Rotating an Image by Precise Angle

1. **Load an image** using File → Open Image
2. Go to Image → Rotate by Angle... (or press Ctrl+Shift+T)
3. Enter the desired angle (e.g., 37.5°)
   - Positive angles rotate counter-clockwise
   - Negative angles rotate clockwise
4. Choose whether to expand canvas (checked = no cropping)
5. Select fill color for background areas
6. Click OK to apply the rotation

### Auto-Adjusting Contrast

1. Load an image with poor contrast
2. Click the **Auto** button in the Brightness & Contrast section
3. The min/max values will be automatically adjusted to the 1st and 99th percentile
4. Fine-tune if needed using the sliders

## Technical Details

### LUT Implementation

The system uses a lookup table approach for efficient image processing:

```python
# Pseudocode
lut = create_identity_lut()  # 0-255 array
lut = apply_windowing(lut, min, max)  # Map [min,max] to [0,255]
lut = apply_contrast(lut, contrast_factor)  # Stretch around midpoint
lut = apply_brightness(lut, brightness_factor)  # Scale values
adjusted_image = lut[original_image]  # Single array lookup
```

This approach is much faster than applying multiple PIL ImageEnhance operations sequentially.

### Histogram Calculation

For grayscale images:
- Direct histogram of pixel intensities (0-255)

For RGB images:
- Combined histogram of all three channels
- Shows overall intensity distribution

### Rotation Quality

The precise rotation function uses:
- PIL's `Image.rotate()` with BICUBIC resampling for high quality
- Optional canvas expansion to prevent cropping
- Configurable fill color for background areas

## API Reference

### Core Functions

#### `apply_intensity_window(image, min_val, max_val)`
Apply intensity windowing to remap pixel values.

**Parameters:**
- `image`: PIL Image
- `min_val`: Minimum intensity (0-255)
- `max_val`: Maximum intensity (0-255)

**Returns:** Windowed PIL Image

#### `apply_lut_adjustments(image, min_val, max_val, brightness, contrast)`
Apply combined LUT-based adjustments.

**Parameters:**
- `image`: PIL Image
- `min_val`: Minimum intensity (0-255)
- `max_val`: Maximum intensity (0-255)
- `brightness`: Brightness factor (1.0 = original)
- `contrast`: Contrast factor (1.0 = original)

**Returns:** Adjusted PIL Image

#### `rotate_image_precise(image, angle, expand=True, fillcolor=None)`
Rotate image by precise decimal angle.

**Parameters:**
- `image`: PIL Image
- `angle`: Rotation angle in degrees (positive = counter-clockwise)
- `expand`: If True, expand canvas to fit rotated image
- `fillcolor`: Fill color for background (default: black for RGB, 0 for grayscale)

**Returns:** Rotated PIL Image

#### `calculate_histogram(image)`
Calculate histogram for image.

**Parameters:**
- `image`: PIL Image

**Returns:** Tuple of (bins, values) where bins are 0-255 and values are counts

### Widget Classes

#### `BrightnessContrastWidget`

**Signals:**
- `min_changed(int)`: Emitted when minimum slider changes
- `max_changed(int)`: Emitted when maximum slider changes
- `brightness_changed(float)`: Emitted when brightness slider changes
- `contrast_changed(float)`: Emitted when contrast slider changes
- `auto_clicked()`: Emitted when Auto button clicked
- `reset_clicked()`: Emitted when Reset button clicked

**Methods:**
- `update_histogram(image)`: Update histogram from image
- `reset_values()`: Reset all sliders to defaults
- `set_enabled(enabled)`: Enable/disable all controls
- `get_values()`: Get current (min, max, brightness, contrast) values

#### `RotateDialog`

**Static Methods:**
- `get_rotation_parameters(parent)`: Show dialog and return (angle, expand, fillcolor) or None

## Testing

### Unit Tests
Run the test suite:
```bash
python3 -m pytest tests/test_enhanced_image_processing.py -v
```

### UI Component Tests
Test UI components interactively (requires display):
```bash
python3 test_ui_components.py
```

## Performance Considerations

- **Histogram calculation**: O(n) where n = number of pixels, performed once per image load
- **LUT application**: O(n) with numpy vectorization, very fast
- **Slider responsiveness**: Target < 100ms update time achieved through:
  - Single LUT application instead of multiple operations
  - Efficient numpy array operations
  - No histogram recalculation during adjustments

## Known Limitations

- Histogram shows combined channels for RGB images (not separate R/G/B histograms)
- Auto-adjustment uses 1st and 99th percentile (not customizable)
- Rotation quality depends on PIL's implementation

## Future Enhancements

Possible future improvements:
- Separate RGB channel histograms
- Customizable auto-adjustment percentiles
- Histogram equalization option
- Gamma correction slider
- Save/load adjustment presets
