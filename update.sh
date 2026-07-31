#!/bin/bash
cd ~/Hapiephonee

# ==========================================
# 🛑 1ª CAMADA: VERIFICAÇÃO DE FONTE (URL Padrão)
# ==========================================
URL_OFICIAL="https://github.com/Willianz4z4/Hapiephonee"
URL_ATUAL=$(git config --get remote.origin.url)
URL_ATUAL_LIMPA=${URL_ATUAL%.git}

if [ "$URL_ATUAL_LIMPA" != "$URL_OFICIAL" ]; then
    echo "💀 [ALERTA CRÍTICO] Fonte de atualização não reconhecida!"
    echo "❌ O sistema negou a aprovação do download. URL adulterada detectada."
    exit 1
fi
# ==========================================

git fetch origin > /dev/null 2>&1

LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse origin/main)
MUDANCAS_SUJAS=$(git status --porcelain)

# ==========================================
# 🛑 2ª CAMADA: VALIDAÇÃO DE INTEGRIDADE LOCAL
# (DEVE FICAR AQUI, ANTES DO EXIT 0)
# ==========================================
if [ -n "$MUDANCAS_SUJAS" ]; then
    echo "💀 [ALERTA] Edição local detectada! Esmagando alterações e purificando..."
    git reset --hard origin/main > /dev/null 2>&1
    git clean -fdx > /dev/null 2>&1
    python security_system/build_hashes.py
    exit 10
fi

# Se não tem arquivo sujo e as versões são iguais, aí sim ele sai quieto
if [ "$LOCAL" = "$REMOTE" ]; then
    exit 0
fi

# ==========================================
# 🛑 3ª CAMADA: ATUALIZAÇÃO OFICIAL
# ==========================================
echo "[⬇️] Baixando atualizações do servidor oficial e limpando o ambiente..."

git clean -fdx > /dev/null 2>&1
git reset --hard origin/main > /dev/null 2>&1

echo "[⚙️] Reconstruindo matriz de segurança..."
python security_system/build_hashes.py

echo "[✅] Sistema atualizado, purificado e blindado!"

exit 10
