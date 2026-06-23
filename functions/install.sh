#!/bin/bash
echo "⚙️ Iniciando a Instalação Automática do Bot Deep Learning..."

echo "📦 Atualizando o sistema..."
pkg update -y && pkg upgrade -y

echo "🐍 Verificando Python..."
pkg install python -y
python -m pip install --upgrade pip

echo "🧠 Baixando e instalando a Rede Neural (PyTorch e Numpy)..."
echo "⏳ Isso pode demorar um pouco dependendo da internet..."
pip install -r requirements.txt

echo "✅ Instalação Concluída! O Cérebro Neural está pronto para rodar."
