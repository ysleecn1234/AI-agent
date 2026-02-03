#!/bin/bash

# IN7 AI Platform Deployment Script
# Usage: ./deploy.sh

echo "====== [IN7 AI Platform] Starting Deployment ======"

# 1. Pull Latest Code
echo "1. Pulling latest changes from git..."
git pull origin main

# 2. Build Docker Images
echo "2. Building Docker images..."
docker-compose build

# 3. Restart Containers (Zero Downtime if Orchestrated, but here simple restart)
echo "3. Restarting services..."
docker-compose up -d

echo "====== Deployment Complete! ======"
echo "Check status with: docker-compose ps"
