#!/bin/bash

# IN7 AI Platform Deployment Script
# Usage: ./deploy.sh

echo "====== [IN7 AI Platform] Starting Deployment ======"

# 1. Pull Latest Code
echo "1. Pulling latest changes from git..."
git pull origin main

# 2. Build Docker Images
# Pointing to docker/docker-compose.yml
echo "2. Building Docker images..."
docker-compose -f docker/docker-compose.yml build

# 3. Restart Containers
echo "3. Restarting services..."
docker-compose -f docker/docker-compose.yml up -d

echo "====== Deployment Complete! ======"
echo "Check status with: docker-compose -f docker/docker-compose.yml ps"
