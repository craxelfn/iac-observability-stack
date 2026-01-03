#!/bin/bash
# after_install.sh - Runs after the application files are installed
# Sets permissions and installs dependencies

set -e

echo "=== AfterInstall Phase ==="
echo "Timestamp: $(date)"

APP_DIR="/opt/masterproject"

# Navigate to application directory
cd $APP_DIR

# Set ownership and permissions
echo "Setting file permissions..."
chown -R ec2-user:ec2-user $APP_DIR
chmod -R 755 $APP_DIR

# Make scripts executable
if [ -d "$APP_DIR/scripts" ]; then
    chmod +x $APP_DIR/scripts/*.sh 2>/dev/null || true
fi

# Install Python dependencies
echo "Installing Python dependencies..."
if [ -f "$APP_DIR/requirements.txt" ]; then
    python3.11 -m pip install -r $APP_DIR/requirements.txt --quiet
    echo "Dependencies installed successfully."
else
    echo "No requirements.txt found, skipping dependency installation."
fi

# Create systemd service file
echo "Creating systemd service file..."
cat > /etc/systemd/system/masterproject.service << 'EOF'
[Unit]
Description=MasterProject FastAPI Application
After=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=/opt/masterproject
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/opt/masterproject"
ExecStart=/usr/bin/python3.11 -m uvicorn main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable service to start on boot
echo "Enabling masterproject service..."
systemctl enable masterproject

echo "=== AfterInstall Phase Complete ==="
