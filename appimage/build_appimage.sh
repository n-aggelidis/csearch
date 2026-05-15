#!/bin/bash
# Stoppt das Skript sofort, falls ein Fehler auftritt
set -e

# Bestimme das AppImage-Skript-Verzeichnis
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

# Wechsle in das Hauptverzeichnis des Projekts (ein Ordner darüber).
# So findet PyInstaller alle Module (wie 'core') absolut zuverlässig!
cd "$SCRIPT_DIR/.."

APP_NAME="CSearch"
APP_DIR="$SCRIPT_DIR/$APP_NAME.AppDir"
ICON_NAME="icon"

export PATH="$HOME/.local/bin:$PATH"

echo "=== 1. Python-Code mit PyInstaller einfrieren ==="
# Alte Reste im Hauptordner rigoros löschen
rm -rf build dist "$APP_NAME.spec" "$APP_DIR"

# Zwingt Python, das aktuelle Verzeichnis als Modul-Quelle zu akzeptieren
export PYTHONPATH="$PWD:$PYTHONPATH"

pyinstaller --noconfirm --clean --windowed --name "$APP_NAME" \
    --paths "$PWD" \
    --collect-all src \
    --add-data "src/ui/window.ui:." \
    --add-data "assets/icon.svg:." \
    src/main.py

echo "=== 2. AppDir-Ordnerstruktur erstellen ==="
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$APP_DIR/usr/lib"

echo "=== 3. Dateien und Abhängigkeiten in das AppDir kopieren ==="
# PyInstaller Code kopieren
cp -r dist/"$APP_NAME"/* "$APP_DIR/usr/bin/"

# Icons kopieren
cp assets/icon.svg "$APP_DIR/usr/share/icons/hicolor/scalable/apps/$ICON_NAME.svg"
cp assets/icon.svg "$APP_DIR/$ICON_NAME.svg"

# Wir iterieren über alle benötigten CLI-Tools
for bin in rga rg rga-preproc pdfgrep pandoc pdftotext; do
    # '|| true' verhindert Skript-Absturz, falls ein Tool fehlt
    bin_path=$(which $bin || true)
    
    if [ -n "$bin_path" ]; then
        cp "$bin_path" "$APP_DIR/usr/bin/"

        # Bibliotheken analysieren
        ldd "$bin_path" | grep "=> /" | awk '{print $3}' | while read -r lib; do
            if [[ ! "$lib" =~ (libc\.so|libm\.so|libpthread\.so|libdl\.so|libstdc\+\+\.so|libgcc_s\.so) ]]; then
                cp -n "$lib" "$APP_DIR/usr/lib/" 2>/dev/null || true
            fi
        done
    fi
done

echo "=== 4. Desktop-Datei (.desktop) erstellen ==="
cat <<EOF > "$APP_DIR/$APP_NAME.desktop"
[Desktop Entry]
Name=CSearch
Exec=$APP_NAME
Icon=$ICON_NAME
Type=Application
Categories=Utility;
Terminal=false
EOF
cp "$APP_DIR/$APP_NAME.desktop" "$APP_DIR/usr/share/applications/"

echo "=== 5. AppRun-Skript erstellen ==="
cat <<EOF > "$APP_DIR/AppRun"
#!/bin/sh
HERE="\$(dirname "\$(readlink -f "\${0}")")"

export PATH="\${HERE}/usr/bin:\$PATH"
export LD_LIBRARY_PATH="\${HERE}/usr/lib:\$LD_LIBRARY_PATH"

export QT_PLUGIN_PATH="${HERE}/usr/bin/PyQt6/Qt6/plugins"
exec "\${HERE}/usr/bin/$APP_NAME" "\$@"
EOF
chmod +x "$APP_DIR/AppRun"

echo "=== 6. Zuviel gepackte System-Bibliotheken entfernen ==="
find "$APP_DIR" -name "libglib-2.0.so*" -delete 2>/dev/null || true
find "$APP_DIR" -name "libgio-2.0.so*" -delete 2>/dev/null || true
find "$APP_DIR" -name "libgobject-2.0.so*" -delete 2>/dev/null || true
find "$APP_DIR" -name "libgmodule-2.0.so*" -delete 2>/dev/null || true
find "$APP_DIR" -name "libgthread-2.0.so*" -delete 2>/dev/null || true
find "$APP_DIR" -name "libstdc++.so*" -delete 2>/dev/null || true
find "$APP_DIR" -name "libgcc_s.so*" -delete 2>/dev/null || true
find "$APP_DIR" -name "libcairo*.so*" -delete 2>/dev/null || true
find "$APP_DIR" -name "libpango*.so*" -delete 2>/dev/null || true
find "$APP_DIR" -name "libharfbuzz*.so*" -delete 2>/dev/null || true
find "$APP_DIR" -name "libfreetype*.so*" -delete 2>/dev/null || true
find "$APP_DIR" -name "libfontconfig*.so*" -delete 2>/dev/null || true

echo "=== 7. AppImage erstellen ==="
cd "$SCRIPT_DIR"

# Prüfen, ob das AppImageTool schon da ist, sonst kurz herunterladen
if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    echo "Lade appimagetool herunter..."
    wget -q https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool-x86_64.AppImage
fi

# Hier passiert die Magie: Das AppImage wird gebaut!
# WICHTIG für NixOS/Docker-Nutzer: Wir extrahieren es erst und nutzen den entpackten Ordner,
# da AppImages in AppImages manchmal Probleme machen (AppImage-Inception).
./appimagetool-x86_64.AppImage --appimage-extract-and-run "$APP_DIR"

echo "=== AUFRÄUMEN ==="
cd "$SCRIPT_DIR/.."
rm -rf build dist "$APP_NAME.spec" "$APP_DIR"

echo "=== FERTIG! ==="
echo "Dein fertiges Programm liegt in: appimage/CSearch-x86_64.AppImage"