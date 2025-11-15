#!/bin/bash
# ClassTop Build Script for Linux and macOS
# Usage: ./build.sh

set -e  # Exit on error

echo "🚀 ClassTop Build Script"
echo "========================"
echo ""

# Get absolute path to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
    PYTHON_PATH="${PROJECT_ROOT}/src-tauri/pyembed/python/bin/python3"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
    PYTHON_PATH="${PROJECT_ROOT}/src-tauri/pyembed/python/bin/python3"
else
    echo "❌ Unsupported platform: $OSTYPE"
    echo "This script only supports Linux and macOS."
    exit 1
fi

echo "📋 Platform: $PLATFORM"
echo ""

# Check if Python embed exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Error: CPython not found at $PYTHON_PATH"
    echo ""
    echo "Please download CPython to src-tauri/pyembed following:"
    echo "https://pytauri.github.io/pytauri/latest/usage/tutorial/build-standalone/"
    echo ""
    exit 1
fi

echo "✅ Found Python at: $PYTHON_PATH"
echo ""

# Set Python path for PyO3
export PYO3_PYTHON="$PYTHON_PATH"
echo "🔧 Set PYO3_PYTHON=$PYO3_PYTHON"

# Set library search path for linking
PYTHON_LIB_DIR="${PROJECT_ROOT}/src-tauri/pyembed/python/lib"

# Add rpath for runtime library loading
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: Add rpath to find libpython in the app bundle
    export RUSTFLAGS="-L ${PYTHON_LIB_DIR} -C link-args=-Wl,-rpath,@executable_path/../Resources/lib"
    echo "🔧 Set RUSTFLAGS=$RUSTFLAGS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux: Add rpath for Linux app bundle
    export RUSTFLAGS="-L ${PYTHON_LIB_DIR} -C link-args=-Wl,-rpath,\$ORIGIN/../lib"
    echo "🔧 Set RUSTFLAGS=$RUSTFLAGS"
fi
echo ""

# Install Python package
echo "📦 Installing Python package..."
uv pip install --exact --python="$PYTHON_PATH" --reinstall-package=classtop ./src-tauri

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python package"
    exit 1
fi

echo "✅ Python package installed"
echo ""

# Build Tauri app
echo "🔨 Building Tauri application..."
npm run -- tauri build --config="src-tauri/tauri.bundle.json" -- --profile bundle-release

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo ""
echo "✅ Build completed successfully!"
echo ""
echo "📁 Build artifacts located at:"
echo "   src-tauri/target/bundle-release/"
echo ""
echo "🔑Add GPG signing of artifacts "
gpg --list-keys >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "🔐 GPG detected, signing artifacts..."
    # Add signing for Linux AppImage
    if [ -f "src-tauri/target/bundle-release/bundle/AppImage" ]; then
        gpg --detach-sign --armor "src-tauri/target/bundle-release/bundle/AppImage"
        echo "✅ Signed: src-tauri/target/bundle-release/bundle/AppImage"
    fi
    # Add signing for macOS DMG files
    for file in src-tauri/target/bundle-release/bundle/dmg/*; do
        gpg --detach-sign --armor "$file"
        echo "✅ Signed: $file"
    done
    echo ""


else
    echo "⚠️  GPG not detected, skipping signing"
    echo ""
fi


# List build artifacts
if [ -d "src-tauri/target/bundle-release" ]; then
    echo "📦 Generated files:"
    ls -lh src-tauri/target/bundle-release/ | tail -n +2
fi

echo ""
echo "🎉 Done!"
