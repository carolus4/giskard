#!/bin/bash

# Build script for Giskard Desktop with DMG creation
# This script builds the app and creates a DMG using sandbox-safe mode

echo "Building Giskard Desktop..."

# Build the app bundle first
npm run tauri build -- --bundles app

if [ $? -eq 0 ]; then
    echo "App bundle created successfully!"
    
    # Create DMG manually with sandbox-safe option
    echo "Creating DMG..."
    cd src-tauri/target/release/bundle/dmg
    
    # Remove existing DMG if it exists
    rm -f Giskard_0.1.0_aarch64.dmg
    
    ./bundle_dmg.sh --sandbox-safe \
        --volname "Giskard" \
        --volicon icon.icns \
        Giskard_0.1.0_aarch64.dmg \
        ../macos/
    
    if [ $? -eq 0 ]; then
        echo "DMG created successfully!"
        echo "DMG location: $(pwd)/Giskard_0.1.0_aarch64.dmg"
    else
        echo "Failed to create DMG"
        exit 1
    fi
else
    echo "Failed to build app bundle"
    exit 1
fi
