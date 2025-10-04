#!/bin/bash

# Start the Flask API backend on port 8000
BACKEND_PORT=8000 uv run python api_main.py &
BACKEND_PID=$!

# Wait a moment for the backend to start
sleep 3

# Start the Vite frontend on port 5000
cd frontend-react && npm run dev &
FRONTEND_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up trap to catch termination signals
trap cleanup SIGTERM SIGINT

# Wait for both processes
wait
