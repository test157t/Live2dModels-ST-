@echo off

echo Welcome to the Gallery Menu!
echo Choose an option:
echo 1. Run with tags
echo 2. Run without tags

set /P choice=Enter your choice (1/2): 

if "%choice%"=="2" (
    python StartGallery.py --notags
) else (
    python StartGallery.py
)
