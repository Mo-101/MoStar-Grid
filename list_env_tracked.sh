#!/bin/bash
cd /home/idona/MoStar/_apps/grid
printf '== tracked .env files ==\n'
git ls-files | grep -E '\.env($|\.)' | sort
printf '== .env files in history ==\n'
git log --all --name-only --pretty=format: | grep -E '\.env($|\.)' | sort -u
