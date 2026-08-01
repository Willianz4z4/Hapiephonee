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
MUDANCAS_SUJAS=$(git status --porcelain)
if [ -n "$MUDANCAS_SUJAS" ]; then
    exit 0
fi
if [ "$LOCAL" = "$REMOTE" ]; then
    exit 0
fi
BACKUP_DIR="../.hapiephonee_backup"
mkdir -p "$BACKUP_DIR"
find . -name "*.json" -o -name ".webhook_cache" 2>/dev/null | while read -r file; do
    mkdir -p "$BACKUP_DIR/$(dirname "$file")"
    cp -f "$file" "$BACKUP_DIR/$file" 2>/dev/null
done
git clean -fdx > /dev/null 2>&1
git reset --hard origin/main > /dev/null 2>&1
if [ -d "$BACKUP_DIR" ]; then
    cp -r "$BACKUP_DIR"/. . 2>/dev/null
    rm -rf "$BACKUP_DIR"
fi
python security_system/build_hashes.py
exit 10
