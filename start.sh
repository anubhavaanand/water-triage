#!/bin/bash
echo "Starting WaterTriage full stack..."
docker compose up -d --build
echo "Done. Dashboard is at http://localhost:3000"
