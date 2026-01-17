#!/bin/bash
set -euo pipefail

APP_NAME="stock-app"
LOG_DIR="/srv/stock-tracker/logs"
LOG_FILE="$LOG_DIR/deploy.log"
COMPOSE_FILE="docker-compose.yml"

# 确保日志目录存在
mkdir -p "$LOG_DIR"
chmod 700 "$LOG_DIR"

# 日志输出到文件 + 控制台
exec > >(tee -a "$LOG_FILE") 2>&1

# ---todo
eval "$(ssh-agent -s)"
ssh-add /home/deploy/.ssh/github-deploy-key
# 使用指定 SSH key 拉 GitHub 代码
export GIT_SSH_COMMAND='ssh -i /home/deploy/.ssh/github-deploy-key -o StrictHostKeyChecking=no'

echo "===== DEPLOY START $(date) ====="

echo "== [1/6] Git fetch =="
git fetch origin

echo "== [2/6] Save current commit for rollback =="
PREV_COMMIT=$(git rev-parse HEAD)
echo "PREV_COMMIT=$PREV_COMMIT"

echo "== [3/6] Pull latest main =="
git checkout main
git pull origin main

echo "== [4/6] Build Docker images =="
docker compose build --pull

echo "== [5/6] Restart services =="
docker compose up -d

echo "== [6/6] Health check =="
sleep 5
if ! docker ps | grep -q "$APP_NAME"; then
  echo "❌ Container not running, rollback!"
  git reset --hard "$PREV_COMMIT"
  docker compose up -d
  exit 1
fi

echo "== Cleanup old images =="
docker image prune -f

echo "✅ Deploy success"
echo "===== DEPLOY END $(date) ====="