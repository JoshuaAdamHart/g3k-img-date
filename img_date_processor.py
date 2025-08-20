#!/usr/bin/env python3
"""
Image Date Processor

Processes PNG and JPG files, extracting dates from filenames and converting them to JPEG
with proper timestamps and EXIF data.
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import piexif
from PIL import Image, ExifTags


def parse_date_from_filename(filename: str) -> Optional[datetime]:
    """
    Extract date from filename in YYYY.MM.DD or YYYY-MM-DD format.
    Month and day are optional.
    
    Args:
        filename: The filename to parse
        
    Returns:
        datetime object if date found, None otherwise
    """
    # Remove file extension for parsing
    name_without_ext = Path(filename).stem
    
    # Try full date pattern first (most specific)
    full_date_pattern = r'(\d{4})[.-](\d{1,2})[.-](\d{1,2})'
    match = re.search(full_date_pattern, name_without_ext)
    if match:
        year, month, day = map(int, match.groups())
        if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
            try:
                return datetime(year, month, day)
            except ValueError:
                # Invalid date (e.g., Feb 30), return None
                return None
        else:
            # Invalid month or day, return None instead of falling back
            return None
    
    # Try year-month pattern (only if no full date pattern was found)
    year_month_pattern = r'(\d{4})[.-](\d{1,2})(?![.-]\d)'  # Negative lookahead to avoid matching full dates
    match = re.search(year_month_pattern, name_without_ext)
    if match:
        year, month = map(int, match.groups())
        if 1900 <= year <= 2100 and 1 <= month <= 12:
            try:
                return datetime(year, month, 1)
            except ValueError:
                return None
        else:
            return None
    
    # Try year-only pattern (only if no year-month pattern was found)
    year_pattern = r'(\d{4})(?![.-]\d)'  # Negative lookahead to avoid matching year-month or full dates
    match = re.search(year_pattern, name_without_ext)
    if match:
        year = int(match.group(1))
        if 1900 <= year <= 2100:
            try:
                return datetime(year, 1, 1)
            except ValueError:
                return None
    
    return None


def resize_image(image: Image.Image, max_dimension: int) -> Image.Image:
    """
    Resize image proportionally to fit within max_dimension while maintaining aspect ratio.
    
    Args:
        image: PIL Image object
        max_dimension: Maximum width or height in pixels
        
    Returns:
        Resized PIL Image object
    """
    width, height = image.size
    
    # Don't upscale if image is already smaller
    if width <= max_dimension and height <= max_dimension:
        return image
    
    # Calculate new dimensions maintaining aspect ratio
    if width > height:
        new_width = max_dimension
        new_height = int((height * max_dimension) / width)
    else:
        new_height = max_dimension
        new_width = int((width * max_dimension) / height)
    
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def create_exif_with_date(date_taken: datetime) -> bytes:
    """
    Create EXIF data with the specified date.
    
    Args:
        date_taken: datetime object for the photo date
        
    Returns:
        EXIF data as bytes
    """
    # Format date for EXIF (YYYY:MM:DD HH:MM:SS)
    date_str = date_taken.strftime("%Y:%m:%d %H:%M:%S")
    
    # Create EXIF dictionary
    exif_dict = {
        "0th": {
            piexif.ImageIFD.DateTime: date_str,
            piexif.ImageIFD.Software: "img-date-processor",
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: date_str,
            piexif.ExifIFD.DateTimeDigitized: date_str,
        }
    }
    
    return piexif.dump(exif_dict)


def set_file_timestamps(file_path: Path, date_time: datetime):
    """
    Set the creation and modification timestamps of a file.
    
    Args:
        file_path: Path to the file
        date_time: datetime to set as timestamps
    """
    timestamp = date_time.timestamp()
    
    # Set modification and access times
    os.utime(file_path, (timestamp, timestamp))
    
    # On macOS, also try to set creation time
    if sys.platform == "darwin":
        try:
            import subprocess
            date_str = date_time.strftime("%m/%d/%Y %H:%M:%S")
            subprocess.run([
                "SetFile", "-d", date_str, "-m", date_str, str(file_path)
            ], check=False, capture_output=True)
        except (FileNotFoundError, subprocess.SubprocessError):
            # SetFile not available, skip creation time setting
            pass


def apply_exif_orientation(image: Image.Image) -> Image.Image:
    """
    Apply EXIF orientation transformation to rotate image correctly.
    
    Args:
        image: PIL Image object
        
    Returns:
        Rotated PIL Image object
    """
    try:
        # Get EXIF data
        exif = image.getexif()
        
        # Get orientation tag (274 is the EXIF tag for Orientation)
        orientation = exif.get(274, 1)
        
        # Apply rotation based on orientation value
        if orientation == 2:
            # Horizontal flip
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        elif orientation == 3:
            # 180 degree rotation
            image = image.rotate(180, expand=True)
        elif orientation == 4:
            # Vertical flip
            image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        elif orientation == 5:
            # Horizontal flip + 90 degree rotation
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            image = image.rotate(90, expand=True)
        elif orientation == 6:
            # 90 degree rotation
            image = image.rotate(270, expand=True)
        elif orientation == 7:
            # Horizontal flip + 270 degree rotation
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            image = image.rotate(270, expand=True)
        elif orientation == 8:
            # 270 degree rotation
            image = image.rotate(90, expand=True)
        # orientation == 1 or any other value: no transformation needed
        
    except (AttributeError, KeyError, TypeError):
        # No EXIF data or orientation tag, return image as-is
        pass
    
    return image


def process_image(source_path: Path, dest_path: Path, max_dimension: int, quality: int) -> bool:
    """
    Process a single image file.
    
    Args:
        source_path: Path to source image
        dest_path: Path to destination image
        max_dimension: Maximum dimension for resizing
        quality: JPEG quality (1-100)
        
    Returns:
        True if processed successfully, False otherwise
    """
    try:
        # Parse date from filename
        date_from_filename = parse_date_from_filename(source_path.name)
        if not date_from_filename:
            print(f"No valid date found in filename: {source_path.name}")
            return False
        
        # Open and process image
        with Image.open(source_path) as img:
            # Apply EXIF orientation transformation first
            img = apply_exif_orientation(img)
            
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize image if needed
            img = resize_image(img, max_dimension)
            
            # Create destination directory if it doesn't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create EXIF data with date
            exif_bytes = create_exif_with_date(date_from_filename)
            
            # Save as JPEG with EXIF data
            img.save(dest_path, 'JPEG', quality=quality, exif=exif_bytes)
        
        # Set file timestamps
        set_file_timestamps(dest_path, date_from_filename)
        
        print(f"Processed: {source_path.name} -> {dest_path.name} (date: {date_from_filename.strftime('%Y-%m-%d')})")
        return True
        
    except Exception as e:
        print(f"Error processing {source_path.name}: {e}")
        return False


def main():
    """Main function to handle command line arguments and process images."""
    parser = argparse.ArgumentParser(
        description="Process images with date information in filenames",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /source/photos /dest/photos 1024 85
  %(prog)s ./input ./output 800 90

Supported filename date formats:
  - YYYY.MM.DD (e.g., 2023.12.25_photo.jpg)
  - YYYY-MM-DD (e.g., 2023-12-25_photo.jpg)
  - YYYY.MM or YYYY-MM (e.g., 2023.12_photo.jpg)
  - YYYY (e.g., 2023_photo.jpg)
        """
    )
    
    parser.add_argument('source_path', type=str, help='Source directory path')
    parser.add_argument('dest_path', type=str, help='Destination directory path')
    parser.add_argument('max_dimension', type=int, help='Maximum width/height in pixels')
    parser.add_argument('quality', type=int, choices=range(1, 101), metavar='1-100',
                       help='JPEG quality (1-100)')
    
    args = parser.parse_args()
    
    # Convert to Path objects
    source_dir = Path(args.source_path)
    dest_dir = Path(args.dest_path)
    
    # Validate source directory
    if not source_dir.exists():
        print(f"Error: Source directory does not exist: {source_dir}")
        sys.exit(1)
    
    if not source_dir.is_dir():
        print(f"Error: Source path is not a directory: {source_dir}")
        sys.exit(1)
    
    # Find all PNG and JPG files
    image_extensions = {'.png', '.jpg', '.jpeg'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(source_dir.rglob(f'*{ext}'))
        image_files.extend(source_dir.rglob(f'*{ext.upper()}'))
    
    if not image_files:
        print(f"No PNG or JPG files found in: {source_dir}")
        sys.exit(0)
    
    print(f"Found {len(image_files)} image files")
    
    # Process each image
    processed_count = 0
    for source_file in image_files:
        # Calculate relative path from source directory
        relative_path = source_file.relative_to(source_dir)
        
        # Create destination path with .jpg extension
        dest_file = dest_dir / relative_path.with_suffix('.jpg')
        
        if process_image(source_file, dest_file, args.max_dimension, args.quality):
            processed_count += 1
    
    print(f"\nProcessed {processed_count} out of {len(image_files)} images")


if __name__ == '__main__':
    main()
