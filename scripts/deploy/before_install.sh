#!/bin/bash
# before_install.sh - Runs before the application is installed
# Stops the application and cleans up old files

set -e

echo "=== BeforeInstall Phase ==="
echo "Timestamp: $(date)"

APP_DIR="/opt/masterproject"
BACKUP_DIR="/opt/masterproject-backup"
SERVICE_NAME="masterproject"

# Stop the application if it's running
echo "Checking if application is running..."
if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
    echo "Stopping $SERVICE_NAME service..."
    systemctl stop $SERVICE_NAME
    echo "Service stopped."
else
    echo "Service is not running."
fi

# Kill any running uvicorn processes
echo "Checking for running uvicorn processes..."
pkill -f "uvicorn main:app" || true

# Backup current version if exists
if [ -d "$APP_DIR" ]; then
    echo "Backing up current version..."
    rm -rf $BACKUP_DIR
    cp -r $APP_DIR $BACKUP_DIR
    echo "Backup created at $BACKUP_DIR"
fi

# Clean old files
echo "Cleaning old application files..."
rm -rf $APP_DIR/*

echo "=== BeforeInstall Phase Complete ==="
