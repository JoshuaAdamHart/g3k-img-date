# Image Date Processor

A Python tool that processes PNG and JPG images, extracting date information from filenames and converting them to JPEG format with proper timestamps and EXIF data.

## Features

- Searches for PNG and JPG files in a source directory (recursively)
- Extracts dates from filenames in various formats:
  - `YYYY.MM.DD` (e.g., `2023.12.25_photo.jpg`)
  - `YYYY-MM-DD` (e.g., `2023-12-25_photo.jpg`)
  - `YYYY.MM` or `YYYY-MM` (e.g., `2023.12_photo.jpg`)
  - `YYYY` only (e.g., `2023_photo.jpg`)
- Converts images to JPEG format
- **Preserves image orientation** by applying EXIF orientation transformations
- Resizes images proportionally to fit within specified dimensions
- Sets file creation and modification timestamps based on extracted date
- Adds EXIF data with the extracted date information
- Maintains directory structure in destination

## Installation

### Option 1: Using Virtual Environment (Recommended)

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Or use the convenience script:
```bash
./activate.sh
```

### Option 2: Global Installation

1. Install required dependencies globally:
```bash
pip install -r requirements.txt
```

**Note:** Using a virtual environment is recommended to avoid conflicts with other Python projects.

## Usage

```bash
python img_date_processor.py <source_path> <dest_path> <max_dimension> <quality>
```

### Arguments

- `source_path`: Source directory containing images to process
- `dest_path`: Destination directory for processed images
- `max_dimension`: Maximum width or height in pixels (images are scaled proportionally)
- `quality`: JPEG quality from 1-100 (higher = better quality, larger file size)

### Examples

```bash
# Process images with max 1024px dimension and 85% quality
python img_date_processor.py /Users/john/Photos /Users/john/ProcessedPhotos 1024 85

# Process with smaller dimensions and higher quality
python img_date_processor.py ./input ./output 800 90
```

## How It Works

1. **Date Extraction**: The tool scans filenames for date patterns and extracts year, month, and day information
2. **Image Processing**: 
   - Opens each image and converts to RGB format if needed
   - Resizes proportionally if larger than max dimension
   - Converts transparent backgrounds to white for PNG files
3. **EXIF Data**: Adds date information to EXIF metadata fields:
   - `DateTime`
   - `DateTimeOriginal` 
   - `DateTimeDigitized`
4. **File Timestamps**: Sets both creation and modification dates to match the extracted date
5. **Output**: Saves as JPEG with specified quality in the destination directory

## Supported Formats

- **Input**: PNG, JPG, JPEG files
- **Output**: JPEG files only
- **Date Formats**: Flexible date parsing supports various separators and optional month/day

## Notes

- Images smaller than the max dimension are not upscaled
- Directory structure is preserved in the destination
- Files without valid dates in their names are skipped
- On macOS, the tool attempts to set creation time using `SetFile` if available
- Transparent PNG images are converted with white backgrounds

## Dependencies

- `Pillow`: Image processing library
- `piexif`: EXIF data manipulation
