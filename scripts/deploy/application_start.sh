#!/bin/bash
# application_start.sh - Starts the application
# Starts the service and waits for it to be ready

set -e

echo "=== ApplicationStart Phase ==="
echo "Timestamp: $(date)"

SERVICE_NAME="masterproject"
APP_PORT=8080
MAX_WAIT=60  # Maximum seconds to wait for app to start

# Start the service
echo "Starting $SERVICE_NAME service..."
systemctl start $SERVICE_NAME

# Give the service a moment to initialize
sleep 2

# Check if service started successfully
if ! systemctl is-active --quiet $SERVICE_NAME; then
    echo "ERROR: Service failed to start"
    echo "Service status:"
    systemctl status $SERVICE_NAME --no-pager || true
    echo ""
    echo "Journal logs (last 50 lines):"
    journalctl -u $SERVICE_NAME --no-pager -n 50 || true
    exit 1
fi

# Wait for the application to be ready on the port 
echo "Waiting for application to be ready on port $APP_PORT..."
COUNTER=0
while [ $COUNTER -lt $MAX_WAIT ]; do
    # Use curl to check if the port is responding (curl is pre-installed on AL2023)
    if curl -sf http://localhost:$APP_PORT/health > /dev/null 2>&1; then
        echo "Application is responding on port $APP_PORT"
        echo "Health check successful!"
        break
    fi
    echo "Waiting... ($COUNTER/$MAX_WAIT seconds)"
    sleep 1
    COUNTER=$((COUNTER + 1))
done

if [ $COUNTER -eq $MAX_WAIT ]; then
    echo "ERROR: Application failed to respond within $MAX_WAIT seconds"
    echo ""
    echo "=== Diagnostic Information ==="
    echo "Service status:"
    systemctl status $SERVICE_NAME --no-pager || true
    echo ""
    echo "Journal logs (last 100 lines):"
    journalctl -u $SERVICE_NAME --no-pager -n 100 || true
    echo ""
    echo "Listening ports:"
    ss -tlnp | grep $APP_PORT || echo "Port $APP_PORT not listening"
    echo ""
    echo "Application log (if exists):"
    tail -n 50 /var/log/masterproject/app.log 2>/dev/null || echo "No app log found"
    exit 1
fi

# Verify service is still active
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "Service $SERVICE_NAME is active and running."
else
    echo "ERROR: Service $SERVICE_NAME is not active."
    systemctl status $SERVICE_NAME --no-pager || true
    exit 1
fi

echo "=== ApplicationStart Phase Complete ==="
