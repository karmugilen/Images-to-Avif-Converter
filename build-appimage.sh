#!/bin/bash

# Exit on error
set -e

# 1. Create and activate virtual environment
echo "--- Creating virtual environment ---"
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
echo "--- Installing dependencies ---"
pip install --upgrade pip
pip install -r requirements.txt

# 3. Build the application with cx_Freeze
echo "--- Building application with cx_Freeze ---"
python setup.py build

# 4. Prepare AppDir
echo "--- Preparing AppDir ---"
APPDIR=AppDir
rm -rf $APPDIR
mkdir -p $APPDIR/usr/bin

# 5. Copy built files
echo "--- Copying application files ---"
cp -r build/exe.linux-x86_64-3.13/* $APPDIR/usr/bin/

# 6. Create .desktop file
echo "--- Creating .desktop file ---"
cat > $APPDIR/imageconverter.desktop <<EOL
[Desktop Entry]
Name=Image Converter
Exec=AppRun
Icon=icon
Type=Application
Categories=Graphics;
EOL

# 7. Copy icon
echo "--- Copying icon ---"
cp testImage.png $APPDIR/icon.png

# 8. Create AppRun script
echo "--- Creating AppRun script ---"
cat > $APPDIR/AppRun <<EOL
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
"$HERE/usr/bin/main" "$@"
EOL

# 9. Make AppRun executable
chmod +x $APPDIR/AppRun

# 10. Download and run appimagetool
echo "--- Downloading and running appimagetool ---"
wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -O appimagetool
chmod +x appimagetool
./appimagetool $APPDIR

# 11. Clean up
echo "--- Cleaning up ---"
rm -rf build venv appimagetool

echo "--- AppImage build complete! ---"
