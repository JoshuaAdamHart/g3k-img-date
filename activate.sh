#!/bin/bash
# Activation script for the img-date project virtual environment

echo "Activating Python virtual environment..."
source venv/bin/activate

echo "Virtual environment activated!"
echo "Python version: $(python --version)"
echo "Installed packages:"
pip list

echo ""
echo "To run the image processor:"
echo "python img_date_processor.py <source_path> <dest_path> <max_dimension> <quality>"
echo ""
echo "To deactivate the environment, run: deactivate"
