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

# Wait for the application to be ready
echo "Waiting for application to be ready on port $APP_PORT..."
COUNTER=0
while [ $COUNTER -lt $MAX_WAIT ]; do
    if nc -z localhost $APP_PORT 2>/dev/null; then
        echo "Application is listening on port $APP_PORT"
        break
    fi
    echo "Waiting... ($COUNTER/$MAX_WAIT seconds)"
    sleep 1
    COUNTER=$((COUNTER + 1))
done

if [ $COUNTER -eq $MAX_WAIT ]; then
    echo "ERROR: Application failed to start within $MAX_WAIT seconds"
    echo "Service status:"
    systemctl status $SERVICE_NAME --no-pager || true
    echo "Journal logs:"
    journalctl -u $SERVICE_NAME --no-pager -n 50 || true
    exit 1
fi

# Verify service is active
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "Service $SERVICE_NAME is active and running."
else
    echo "ERROR: Service $SERVICE_NAME is not active."
    systemctl status $SERVICE_NAME --no-pager || true
    exit 1
fi

echo "=== ApplicationStart Phase Complete ==="
