#!/bin/bash
set -e

REPO="Ashixi/consensia_cli"
COMMAND_NAME="consensia"
INSTALL_DIR="/usr/local/bin"

echo "⏳ Detecting your operating system..."

OS="$(uname -s)"

case "$OS" in
    Linux)
        BINARY_NAME="consensia"
        ;;
    Darwin)
        BINARY_NAME="consensia"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        BINARY_NAME="consensia.exe"
        COMMAND_NAME="consensia.exe"
        # Змінюємо шлях на локальний для користувача, щоб не вимагати прав Адміна
        INSTALL_DIR="$HOME/bin" 
        mkdir -p "$INSTALL_DIR"
        ;;
    *)
        echo "❌ OS ($OS) not supported."
        exit 1
        ;;
esac

echo "✅ OS detected: $OS"
echo "🔍 Searching for $BINARY_NAME in latest release..."

# This improved logic looks specifically for the file name match in the assets
DOWNLOAD_URL=$(curl -s https://api.github.com/repos/$REPO/releases/latest | \
    grep "browser_download_url" | \
    grep "/$BINARY_NAME\"" | \
    cut -d '"' -f 4 | head -n 1)

if [ -z "$DOWNLOAD_URL" ] || [ "$DOWNLOAD_URL" == "null" ]; then
    echo "❌ Could not find $BINARY_NAME in GitHub releases."
    echo "Check manually: https://github.com/$REPO/releases"
    exit 1
fi

echo "⬇️ Downloading: $DOWNLOAD_URL"
TMP_FILE="/tmp/$COMMAND_NAME"
curl -sL "$DOWNLOAD_URL" -o "$TMP_FILE"
chmod +x "$TMP_FILE"

echo "📦 Installing to $INSTALL_DIR..."
if [[ "$OS" == "MINGW"* || "$OS" == "MSYS"* ]]; then
    mv -f "$TMP_FILE" "$INSTALL_DIR/$COMMAND_NAME"
else
    sudo mv -f "$TMP_FILE" "$INSTALL_DIR/$COMMAND_NAME"
fi

echo "--------------------------------------------------"
echo "🎉 Successfully installed!"

# --- ПЕРЕВІРКА PATH ---
# Додаємо двокрапки по краях, щоб уникнути хибних спрацювань (наприклад, коли шукаємо /bin, а знаходить /usr/bin)
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "⚠️  WARNING: The installation directory ($INSTALL_DIR) is not in your PATH."
    echo "    This means your terminal won't find the '$COMMAND_NAME' command automatically."
    echo ""
    echo "    👉 TO FIX THIS, add the directory to your PATH manually:"
    
    if [[ "$OS" == "MINGW"* || "$OS" == "MSYS"* ]]; then
        echo "    Run this command or add it to your ~/.bashrc or ~/.bash_profile:"
        echo "    export PATH=\"\$HOME/bin:\$PATH\""
    else
        echo "    For bash users, add this to your ~/.bashrc:"
        echo "    export PATH=\"$INSTALL_DIR:\$PATH\""
        echo "    For zsh users (macOS default), add this to your ~/.zshrc:"
        echo "    export PATH=\"$INSTALL_DIR:\$PATH\""
    fi
    echo ""
    echo "    After adding it, restart your terminal or run: source ~/.bashrc (or ~/.zshrc)"
    echo "--------------------------------------------------"
else
    echo "🚀 Run: $COMMAND_NAME --help"
    echo "--------------------------------------------------"
fi