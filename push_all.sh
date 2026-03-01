#!/bin/bash
# A script to easily commit and push to both GitHub and HuggingFace

if [ -z "$1" ]; then
    echo "Usage: ./push_all.sh \"Commit message\""
    exit 1
fi

COMMIT_MSG=$1

echo "Staging changes..."
git add .

echo "Committing with message: $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

echo "Pushing to HuggingFace (origin)..."
git push origin main

echo "Pushing to GitHub (github)..."
git push github main

echo "All done!"
