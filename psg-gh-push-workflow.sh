#!/bin/bash
# Push wrapper tool for FocusFlow / hack Directory
cd /home/siva/Desktop/psg/hack

echo "Ensuring remote is set correctly to https://github.com/suwethadevakiruba3012-wq/Free.git"
git remote set-url origin https://github.com/suwethadevakiruba3012-wq/Free.git 2>/dev/null || git remote add origin https://github.com/suwethadevakiruba3012-wq/Free.git

echo "Status:"
git status
echo "Pushing context! Make sure your password or Personal Access Token (PAT) is provided"
git push -u origin main
