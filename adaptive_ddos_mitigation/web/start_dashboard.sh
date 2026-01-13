#!/bin/bash

# Quick Start Script for Web Dashboard
# Adaptive DDoS Mitigation System

echo "========================================="
echo "  DDoS Mitigation System - Web Dashboard"
echo "========================================="
echo ""

# Check if we're in the correct directory
if [ ! -f "app.py" ]; then
    echo "Error: Please run this script from the web/ directory"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements_web.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo ""
echo "Dependencies installed successfully!"
echo ""
echo "Starting web server..."
echo ""
echo "Dashboard will be available at:"
echo "  → http://localhost:5000"
echo "  → http://127.0.0.1:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python app.py
