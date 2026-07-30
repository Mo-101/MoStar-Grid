#!/bin/bash
set -e
cd /home/idona/MoStar/_apps/grid

# Remove from index if still tracked (ignore if already gone)
git rm --cached --ignore-unmatch \
  backend/.env \
  frontend/.env \
  frontend/.env.local \
  __attic__/.env.local

# Add explicit .gitignore rules
git add .gitignore

echo "=== git diff --cached --stat ==="
git diff --cached --stat

echo "=== git diff --cached -- .gitignore ==="
git diff --cached -- .gitignore
