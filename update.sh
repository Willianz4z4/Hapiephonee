#!/bin/bash
echo "[⬇️] Baixando atualizações do Hapiephonee..."
cd ~/Hapiephonee

# Puxa o código com força do repositório oficial
git fetch origin
git reset --hard origin/main

# Reconstrói as assinaturas de segurança baseadas no código virgem que acabou de chegar
echo "[⚙️] Reconstruindo matriz de segurança..."
python security_system/build_hashes.py

echo "[✅] Sistema atualizado e blindado!"
