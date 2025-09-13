#!/bin/bash
set -e

echo "Starting ElevenLabs Bridge API..."

# Export environment variables
export PYTHONUNBUFFERED=1

# Run migrations or setup tasks if needed
# python manage.py migrate

# Start the application
exec uvicorn main_frontend_bridge:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --log-level info