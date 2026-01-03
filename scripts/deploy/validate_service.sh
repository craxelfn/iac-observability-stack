#!/bin/bash
# validate_service.sh - Validates the deployed application
# Performs health checks to ensure the application is working correctly

set -e

echo "=== ValidateService Phase ==="
echo "Timestamp: $(date)"

APP_HOST="localhost"
APP_PORT=8080
HEALTH_ENDPOINT="http://${APP_HOST}:${APP_PORT}/health"
MAX_RETRIES=5
RETRY_DELAY=3

# Function to perform health check
perform_health_check() {
    local response
    local http_code
    
    echo "Performing health check on $HEALTH_ENDPOINT..."
    
    # Get response and HTTP code
    response=$(curl -s -w "\n%{http_code}" "$HEALTH_ENDPOINT" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    echo "HTTP Status Code: $http_code"
    echo "Response Body: $body"
    
    if [ "$http_code" = "200" ]; then
        # Verify response contains expected fields
        if echo "$body" | grep -q '"status".*:.*"healthy"'; then
            echo "Health check passed: Application is healthy"
            return 0
        else
            echo "Health check failed: Unexpected response format"
            return 1
        fi
    else
        echo "Health check failed: HTTP status $http_code"
        return 1
    fi
}

# Retry health check with backoff
echo "Starting health check validation..."
ATTEMPT=1
while [ $ATTEMPT -le $MAX_RETRIES ]; do
    echo ""
    echo "Attempt $ATTEMPT of $MAX_RETRIES..."
    
    if perform_health_check; then
        echo ""
        echo "=== Validation Successful ==="
        echo "Application is deployed and healthy."
        
        # Log additional endpoint tests
        echo ""
        echo "Testing additional endpoints..."
        
        # Test root endpoint
        echo "Testing / endpoint..."
        curl -s "http://${APP_HOST}:${APP_PORT}/" | head -c 200
        echo ""
        
        # Test items endpoint
        echo "Testing /items endpoint..."
        curl -s "http://${APP_HOST}:${APP_PORT}/items?count=2" | head -c 300
        echo ""
        
        echo ""
        echo "=== ValidateService Phase Complete ==="
        exit 0
    fi
    
    if [ $ATTEMPT -lt $MAX_RETRIES ]; then
        echo "Retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
done

# All retries failed
echo ""
echo "=== Validation Failed ==="
echo "Health check failed after $MAX_RETRIES attempts."
echo ""
echo "Diagnostic Information:"
echo "----------------------"

# Show service status
echo "Service Status:"
systemctl status masterproject --no-pager 2>/dev/null || echo "Service not found"

# Show recent logs
echo ""
echo "Recent Application Logs:"
journalctl -u masterproject --no-pager -n 30 2>/dev/null || echo "No logs available"

# Show listening ports
echo ""
echo "Listening Ports:"
ss -tlnp | grep $APP_PORT || echo "Port $APP_PORT not listening"

# Exit with error to trigger rollback
exit 1
