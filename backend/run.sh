#!/bin/bash
# 后端启动脚本 — 使用项目自带 venv Python
cd "$(dirname "$0")/.."
PYTHONPATH=. ./backend/venv/bin/python -m backend.src.app
