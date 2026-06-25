#!/bin/bash
# Start Reflect locally using Ollama + LLaMA 3
# Run this after: brew install ollama && ollama pull llama3

set -e

# Start Ollama in background if not running
if ! pgrep -x ollama > /dev/null; then
  echo "Starting Ollama..."
  ollama serve &
  sleep 3
fi

# Pull model if not present
if ! ollama list | grep -q "llama3"; then
  echo "Pulling llama3 (4.7GB — one time download)..."
  ollama pull llama3
fi

echo "Starting Reflect server..."
node server.js
