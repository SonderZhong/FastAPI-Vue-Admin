#!/bin/bash

# FastAPI-Vue-Admin Docker 部署脚本

set -e

echo "=========================================="
echo "  FastAPI-Vue-Admin Docker 部署"
echo "=========================================="

# 检查 config.yaml 是否存在
if [ ! -f "server/config.yaml" ]; then
    echo "⚠️  警告: server/config.yaml 不存在"
    echo "   首次启动将进入初始化向导"
fi

# 构建并启动
echo ""
echo "🔨 构建镜像..."
docker-compose build

echo ""
echo "🚀 启动服务..."
docker-compose up -d

echo ""
echo "=========================================="
echo "  ✅ 部署完成!"
echo "=========================================="
echo ""
echo "  前端地址: http://localhost"
echo "  后端API:  http://localhost:9090"
echo ""
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo ""
