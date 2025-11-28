#!/bin/bash
# Force Demo Reset Script
# Triggers an immediate demo reset (hourly reset + Discord notifications)

echo "🔄 Triggering Demo Reset..."

# Call the force-reset API
RESPONSE=$(curl -s -X POST http://localhost:9374/api/demo/force-reset)

# Check response
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✅ Demo reset triggered successfully!"
    echo "   The bot will process the reset within 30 seconds."
    echo ""
    echo "   Actions that will be performed:"
    echo "   - Reset Mech to Level 1, Power 3"
    echo "   - Stop Minecraft and Valheim containers"
    echo "   - Purge all messages from channels"
    echo "   - Post reset notification to all channels"
    echo "   - Restore demo configuration files"
else
    echo "❌ Failed to trigger demo reset"
    echo "   Response: $RESPONSE"
    exit 1
fi
