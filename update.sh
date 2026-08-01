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
    exit 1
fi

git fetch origin > /dev/null 2>&1

LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse origin/main)
MUDANCAS_SUJAS=$(git status --porcelain)

# ==========================================
# 🛑 2ª CAMADA: FLAGRANTE (DELEGA PARA O C-LEVEL)
# ==========================================
if [ -n "$MUDANCAS_SUJAS" ]; then
    echo "👀 [BASH] Adulteração detectada! Repassando flagrante para o Motor C-Level..."
    # O Bash NÃO limpa e NÃO reseta. Ele sai com sucesso (0) para que o bot inicie
    # com o arquivo sujo e o Core aplique o Lockdown e o banimento!
    exit 0
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
