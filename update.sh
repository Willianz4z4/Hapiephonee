#!/bin/bash
cd ~/Hapiephonee
URL_OFICIAL="https://github.com/Willianz4z4/Hapiephonee"
URL_ATUAL=$(git config --get remote.origin.url)
URL_ATUAL_LIMPA=${URL_ATUAL%.git}
if [ "$URL_ATUAL_LIMPA" != "$URL_OFICIAL" ]; then
    exit 1
fi
git fetch origin > /dev/null 2>&1
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse origin/main)
DIFF=$(git diff --name-only)
if [ "$LOCAL" = "$REMOTE" ]; then
    if [ -z "$DIFF" ]; then
        python security_system/build_hashes.py > /dev/null 2>&1
        exit 0
    else
        git checkout . > /dev/null 2>&1
        python security_system/build_hashes.py > /dev/null 2>&1
        exit 0
    fi
else
    BACKUP_DIR="../.hapiephonee_backup"
    mkdir -p "$BACKUP_DIR"
    find . \( -name "*.json" -o -name ".webhook_cache" \) ! -name ".hash_cache.json" 2>/dev/null | while read -r file; do
        mkdir -p "$BACKUP_DIR/$(dirname "$file")"
        cp -f "$file" "$BACKUP_DIR/$file" 2>/dev/null
    done
    git clean -fdx > /dev/null 2>&1
    git reset --hard origin/main > /dev/null 2>&1
    if [ -d "$BACKUP_DIR" ]; then
        cp -r "$BACKUP_DIR"/. . 2>/dev/null
        rm -rf "$BACKUP_DIR"
    fi
    python security_system/build_hashes.py > /dev/null 2>&1
    exit 10
fi
