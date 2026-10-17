#!/usr/bin/env bash
# Cloudflare Pages 构建脚本
# Build command: bash build.sh
# Build output directory: curiohood-site
set -e

echo "==> 安装 Markdown 解析库"
python3 -m pip install --quiet markdown 2>/dev/null \
  || python3 -m pip install --quiet --break-system-packages markdown 2>/dev/null \
  || echo "（已存在或无法安装，继续尝试构建）"

echo "==> 从 Markdown 生成页面"
python3 curiohood-src/newpost.py rebuild

echo "==> 构建完成"
