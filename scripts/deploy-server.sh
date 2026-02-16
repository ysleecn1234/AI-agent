#!/bin/bash
# 서버 배포 스크립트 (NCP 서버에서 실행)
# 사용법: bash scripts/deploy-server.sh

set -e
cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

echo "=== 1. Git pull (feature-UI) ==="
git pull origin feature-UI

echo ""
echo "=== 2. 백엔드 재시작 (Docker) ==="
cd "$REPO_ROOT/docker"
docker-compose restart backend
echo "백엔드 재시작 완료. 로그 확인: docker logs agent-backend --tail 20"

echo ""
echo "=== 3. 프론트엔드 빌드 & 재시작 ==="
cd "$REPO_ROOT/frontend"
rm -rf .next
npm run build
if command -v pm2 &> /dev/null; then
    pm2 restart frontend || pm2 start npm --name "frontend" -- start
    echo "프론트엔드 pm2 재시작 완료."
else
    echo "pm2가 없습니다. 수동 실행: cd frontend && npm run build && nohup npm start &"
fi

echo ""
echo "=== 배포 완료 ==="
echo "백엔드: http://223.130.142.76:8000"
echo "프론트: http://223.130.142.76:3000"
