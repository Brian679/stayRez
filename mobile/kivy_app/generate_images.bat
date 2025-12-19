@echo off
echo Installing required libraries...
python -m pip install Pillow requests --quiet

echo.
echo Downloading realistic stock images...
python generate_images.py

echo.
echo Done! Press any key to exit.
pause >nul
