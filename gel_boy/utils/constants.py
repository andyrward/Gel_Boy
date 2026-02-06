"""Application constants."""

# Application information
APP_NAME = "Gel_Boy"
APP_VERSION = "0.1.0"
APP_AUTHOR = "Gel_Boy Development Team"

# Image processing defaults
DEFAULT_IMAGE_DPI = 300
MAX_IMAGE_SIZE = (10000, 10000)  # Maximum width, height in pixels

# Lane detection defaults
DEFAULT_MIN_LANE_WIDTH = 20
DEFAULT_MAX_LANE_WIDTH = 100
DEFAULT_LANE_SPACING = 10

# Band detection defaults
DEFAULT_BAND_THRESHOLD = 0.1
DEFAULT_MIN_PEAK_DISTANCE = 5

# File formats
SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"]
PROJECT_FILE_EXTENSION = ".gelboy"

# Export formats
EXPORT_FORMATS = {
    "csv": "Comma-Separated Values (*.csv)",
    "xlsx": "Microsoft Excel (*.xlsx)",
    "png": "PNG Image (*.png)",
    "jpeg": "JPEG Image (*.jpg)",
    "tiff": "TIFF Image (*.tif)"
}

# UI defaults
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
DEFAULT_ZOOM_LEVELS = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]

# Color schemes
COLOR_LANE_BORDER = "#00FF00"
COLOR_BAND_MARKER = "#FF0000"
COLOR_BACKGROUND = "#FFFFFF"
