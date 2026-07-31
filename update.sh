#!/bin/bash
cd ~/Hapiephonee

# ==========================================
# 🛑 1ª CAMADA: VERIFICAÇÃO DE FONTE (URL Padrão)
# ==========================================
URL_OFICIAL="https://github.com/Willianz4z4/Hapiephonee"
URL_ATUAL=$(git config --get remote.origin.url)

# Remove um possível ".git" no final para garantir que a comparação seja perfeita
URL_ATUAL_LIMPA=${URL_ATUAL%.git}

if [ "$URL_ATUAL_LIMPA" != "$URL_OFICIAL" ]; then
    echo "💀 [ALERTA CRÍTICO] Fonte de atualização não reconhecida!"
    echo "❌ O sistema negou a aprovação do download. URL adulterada detectada."
    # Sai com código 1. O import.py só reinicia se for 10, então a tentativa de update morre aqui.
    exit 1
fi
# ==========================================

# Se passou pela porta, olha o que tem de novo no repositório oficial
git fetch origin > /dev/null 2>&1

LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse origin/main)

# Se não tiver atualização, sai quieto (código 0)
if [ "$LOCAL" = "$REMOTE" ]; then
    exit 0
fi

echo "[⬇️] Baixando atualizações do servidor oficial e limpando o ambiente..."

# APAGA TUDO QUE NÃO FOR OFICIAL (Arquivos ou pastas criadas pelo usuário)
git clean -fdx > /dev/null 2>&1

# SOBRESCREVE TUDO (Força os arquivos locais a serem cópias perfeitas da nuvem)
git reset --hard origin/main > /dev/null 2>&1

# ==========================================
# 🛑 2ª CAMADA: VALIDAÇÃO DE INTEGRIDADE LOCAL
# ==========================================
CHECK_LOCAL=$(git rev-parse @)
MUDANCAS_SUJAS=$(git status --porcelain)

# Se tiver qualquer arquivo editado localmente bem na hora do update
if [ "$CHECK_LOCAL" != "$REMOTE" ] || [ -n "$MUDANCAS_SUJAS" ]; then
    echo "💀 [ALERTA] Edição local detectada durante o update! Esmagando alterações..."
    
    # Limpa e reseta tudo de novo com força bruta
    git reset --hard origin/main > /dev/null 2>&1
    git clean -fdx > /dev/null 2>&1
fi
# ==========================================

echo "[⚙️] Reconstruindo matriz de segurança..."
python security_system/build_hashes.py

echo "[✅] Sistema atualizado!"

# Manda o código 10 pro import.py reiniciar o bot com o código aprovado
exit 10
