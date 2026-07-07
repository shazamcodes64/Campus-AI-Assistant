#!/bin/bash
# Fix Python PATH for macOS

echo "🔧 Fixing Python PATH..."

# Detect shell
SHELL_NAME=$(basename "$SHELL")
echo "Detected shell: $SHELL_NAME"

# Python bin directory
PYTHON_BIN_DIR="$HOME/Library/Python/3.9/bin"

# Configuration file based on shell
if [ "$SHELL_NAME" = "zsh" ]; then
    CONFIG_FILE="$HOME/.zshrc"
elif [ "$SHELL_NAME" = "bash" ]; then
    CONFIG_FILE="$HOME/.bash_profile"
else
    CONFIG_FILE="$HOME/.profile"
fi

echo "Configuration file: $CONFIG_FILE"

# Check if PATH already contains the directory
if grep -q "$PYTHON_BIN_DIR" "$CONFIG_FILE" 2>/dev/null; then
    echo "✅ Python bin directory already in PATH"
else
    echo "📝 Adding Python bin directory to PATH..."
    echo "" >> "$CONFIG_FILE"
    echo "# Python 3.9 user scripts" >> "$CONFIG_FILE"
    echo "export PATH=\"\$HOME/Library/Python/3.9/bin:\$PATH\"" >> "$CONFIG_FILE"
    echo "✅ Added to $CONFIG_FILE"
fi

# Also add to current session
export PATH="$HOME/Library/Python/3.9/bin:$PATH"

echo ""
echo "✅ PATH fixed!"
echo ""
echo "To apply changes, run one of these:"
echo "  source $CONFIG_FILE"
echo "  # OR restart your terminal"
echo ""
echo "To verify, run:"
echo "  echo \$PATH | grep Python"
