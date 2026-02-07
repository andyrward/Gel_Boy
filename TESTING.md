# Testing the Enhanced Features

This guide explains how to test the new histogram and rotation features in Gel_Boy.

## Quick Start

### 1. Install Dependencies

```bash
# Using pip
python3 -m pip install -e .

# Or using uv (if available)
uv sync
```

### 2. Run the Application

```bash
python3 main.py
```

### 3. Test the Features

#### Testing Histogram and Brightness/Contrast

1. **Open an image**: File → Open Image (or Ctrl+O)
2. **View the histogram**: The histogram will appear automatically in the right side panel
3. **Adjust intensity window**:
   - Move the **Minimum** slider to set the lower cutoff
   - Move the **Maximum** slider to set the upper cutoff
   - Watch the red and blue lines move on the histogram
   - The green shaded area shows the active range
4. **Adjust brightness and contrast**:
   - Move the **Brightness** slider (0-200%)
   - Move the **Contrast** slider (0-200%)
   - Changes apply immediately using fast LUT processing
5. **Auto-adjust**: Click the **Auto** button to automatically set optimal min/max
6. **Reset**: Click the **Reset** button to return to defaults

#### Testing Precise Rotation

1. **Open an image**: File → Open Image
2. **Open rotation dialog**: Image → Rotate by Angle... (or Ctrl+Shift+T)
3. **Set rotation angle**:
   - Enter a decimal value (e.g., 37.5°, -12.3°)
   - Or use quick buttons (45°, 90°, 180°, 270°)
4. **Choose options**:
   - Check "Expand canvas" to see the entire rotated image (unchecked will crop)
   - Select fill color (Black or White) for background areas
5. **Apply**: Click OK

## Running Unit Tests

```bash
# Run all tests
python3 -m pytest tests/test_enhanced_image_processing.py -v

# Run specific test class
python3 -m pytest tests/test_enhanced_image_processing.py::TestRotateImagePrecise -v

# Run with coverage
python3 -m pytest tests/test_enhanced_image_processing.py --cov=gel_boy.core.image_processing
```

## Testing UI Components Standalone

For testing the UI components without the full application:

```bash
python3 test_ui_components.py
```

This will open a test window where you can:
- Load test grayscale and RGB images
- See the histogram update
- Test all sliders and buttons
- Test the rotation dialog
- See signal output in the console

## Sample Test Images

### Creating Test Images

If you don't have gel images, you can create test images using Python:

```python
from PIL import Image
import numpy as np

# Create a gradient image (good for testing histogram)
gradient = np.linspace(0, 255, 512*512, dtype=np.uint8).reshape(512, 512)
Image.fromarray(gradient, mode='L').save('test_gradient.png')

# Create a low-contrast image (good for testing auto-adjust)
low_contrast = np.random.randint(100, 150, (512, 512), dtype=np.uint8)
Image.fromarray(low_contrast, mode='L').save('test_low_contrast.png')

# Create a high-contrast image
high_contrast = np.where(
    np.random.rand(512, 512) > 0.5,
    255,
    0
).astype(np.uint8)
Image.fromarray(high_contrast, mode='L').save('test_high_contrast.png')
```

## Performance Testing

To test performance with large images:

```python
from PIL import Image
import numpy as np
import time

# Create a large test image
large_image = np.random.randint(0, 256, (4000, 4000), dtype=np.uint8)
img = Image.fromarray(large_image, mode='L')

# Time the histogram calculation
from gel_boy.core.image_processing import calculate_histogram
start = time.time()
bins, values = calculate_histogram(img)
print(f"Histogram calculation: {(time.time() - start)*1000:.1f}ms")

# Time the LUT adjustment
from gel_boy.core.image_processing import apply_lut_adjustments
start = time.time()
adjusted = apply_lut_adjustments(img, 50, 200, 1.2, 1.3)
print(f"LUT adjustment: {(time.time() - start)*1000:.1f}ms")
```

Expected results on modern hardware:
- Histogram calculation: < 50ms for 4000x4000 image
- LUT adjustment: < 100ms for 4000x4000 image

## Troubleshooting

### "No module named matplotlib"
Install matplotlib:
```bash
python3 -m pip install matplotlib
```

### "libEGL.so.1: cannot open shared object file"
This is expected in headless environments. The application requires a display.

For headless testing, use:
```bash
xvfb-run python3 main.py
```

### Histogram not updating
- Make sure an image is loaded
- Try clicking Reset button
- Check console for error messages

### Slow slider response
- Ensure you're using the LUT-based implementation (should be automatic)
- Check if image is extremely large (> 10000x10000 pixels)
- Monitor CPU usage

## Verifying the Implementation

### Checklist

- [ ] Histogram displays when image is loaded
- [ ] Min slider shows red dashed line on histogram
- [ ] Max slider shows blue dashed line on histogram
- [ ] Green shaded area shows active range
- [ ] Auto button sets reasonable min/max values
- [ ] Reset button returns all sliders to defaults
- [ ] Brightness slider affects image brightness
- [ ] Contrast slider affects image contrast
- [ ] Sliders feel responsive (no lag)
- [ ] Rotation dialog opens with Ctrl+Shift+T
- [ ] Can enter decimal angles (e.g., 45.5°)
- [ ] Quick angle buttons work
- [ ] Expand canvas checkbox works
- [ ] Fill color selection works
- [ ] Rotation applies correctly

## Screenshot Examples

When testing on a machine with a display, take screenshots showing:
1. Histogram with an image loaded
2. Min/Max markers on histogram
3. Auto-adjustment result
4. Rotation dialog
5. Image rotated by precise angle (e.g., 37.5°)

Save screenshots in `docs/screenshots/` directory.

## Next Steps

After verifying the implementation:
1. Test with real gel electrophoresis images
2. Verify histogram accurately represents image data
3. Check that auto-adjustment works well for typical gel images
4. Test rotation with various angles
5. Report any issues or suggestions for improvement
