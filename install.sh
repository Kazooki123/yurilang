#!/bin/bash
# YuriLang installer for Linux/Mac/Termux
# "She found her way in. Now so can you." 🌼

set -e

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║         Y U R I L A N G              ║"
echo "  ║   Yuring Complete since 2026  🪷     ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# detect if we need sudo
if [ "$(id -u)" -eq 0 ] || \
   [ -w "/usr/local/bin" ] || \
   [[ "$PREFIX" == *"termux"* ]]; then
    python3 install.py "$@"
else
    echo "  [info] No write access to /usr/local/bin"
    echo "  [info] Installing to ~/.local/bin instead..."
    python3 install.py --user "$@"
fi
