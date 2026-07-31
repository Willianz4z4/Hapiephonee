import os
import hashlib
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(BASE_DIR, "security_system", ".hash_cache.json")

def gerar_hashes_oficiais():
    hashes = {}
    
    # Varre toda a pasta do projeto
    for root, dirs, files in os.walk(BASE_DIR):
        # Ignora pastas ocultas (como .git) e caches
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            # Ignora o próprio arquivo de cache e arquivos dinâmicos (logs, txt, pyc e json)
            if file == ".hash_cache.json": continue
            if file.endswith((".pyc", ".pyo", ".log", ".txt", ".json")): continue

            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, BASE_DIR)
            
            sha3 = hashlib.sha3_512()
            try:
                with open(filepath, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha3.update(chunk)
                hashes[rel_path] = sha3.hexdigest()
            except Exception as e:
                print(f"Erro ao ler {rel_path}: {e}")
                
    with open(CACHE_FILE, "w") as f:
        json.dump(hashes, f, indent=4)
        
    print(f"[🔒] Hapiephonee HASH DNA atualizado! {len(hashes)} arquivos assinados.")

if __name__ == "__main__":
    gerar_hashes_oficiais()
