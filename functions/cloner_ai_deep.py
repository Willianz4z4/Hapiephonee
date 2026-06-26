import os
import time
import subprocess
import random
import xml.etree.ElementTree as ET
import re
from collections import deque

# --- MACHINE LEARNING IMPORTS ---
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

# 🧠 Vocabulário base estrutural (focado nas ações e caminhos, independente do app)
VOCABULARIO = [
    "cloner", "clone", "app cloner", "load settings", "settings", "configurações", "config",
    "import", "importar", "data", "dados", "download", "storage", "emulated", "diretório",
    "directory", "file", "arquivo", "voltar", "cancelar", "cancel", "ok", "confirm", "aceitar"
]

class DeepQNetwork(nn.Module):
    """🧠 O Cérebro Artificial Resiliente (3 Camadas Ocultas)"""
    def __init__(self, input_size):
        super(DeepQNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1) # Retorna a nota de utilidade (Q-Value) da ação
        )

    def forward(self, x):
        return self.network(x)

class ClonerStressAI:
    def __init__(self):
        self.model_file = "brain_cloner_general.pth"
        self.log_file = "ai_cloner_stress.log"

        # Hiperparâmetros de Aprendizado
        self.gamma = 0.95
        self.epsilon = 0.80  # Começa explorando bastante
        self.min_epsilon = 0.15
        self.batch_size = 32
        self.memory = deque(maxlen=4000)

        # Tamanho do Input Fixo = (Vocabulário Estrutural + 2 Slots de Match Dinâmico) * 2
        self.vector_length = len(VOCABULARIO) + 2
        self.input_size = self.vector_length * 2

        self.device = torch.device("cpu")
        self.model = DeepQNetwork(self.input_size).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()

        self.load_model()

    def root_command(self, cmd):
        try:
            result = subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout.strip()
        except:
            return ""

    def get_installed_user_apps(self):
        """Pega dinamicamente todos os aplicativos de usuário instalados no celular"""
        saida = self.root_command("pm list packages -3")
        packages = []
        for line in saida.split("\n"):
            if "package:" in line:
                pkg = line.replace("package:", "").strip()
                # Extrai uma palavra-chave simples do pacote (ex: com.termux -> termux)
                parts = pkg.split(".")
                clean_name = parts[-1] if len(parts) > 1 else pkg
                if clean_name.lower() not in ["vending", "cloner"]: # evita os apps de sistema básicos
                    packages.append((pkg, clean_name))
        
        # Fallback de segurança caso o comando falhe ou não tenha apps cadastrados
        return packages if packages else [("com.termux", "termux"), ("com.roblox.client", "roblox")]

    def get_screen_xml(self):
        self.root_command("rm -f /data/local/tmp/cloner_dump.xml")
        xml = self.root_command("uiautomator dump /data/local/tmp/cloner_dump.xml > /dev/null && cat /data/local/tmp/cloner_dump.xml")
        return xml if xml and xml.startswith("<?xml") else None

    def text_to_vector(self, text, target_name):
        """Transforma o texto em vetor usando o vocabulário fixo + os slots de match dinâmico"""
        text = text.lower()
        target_name = target_name.lower()
        
        # 1. Monta a parte estrutural do vocabulário
        vector = [1.0 if palavra in text else 0.0 for palavra in VOCABULARIO]
        
        # 2. Injeta o Slot Dinâmico 1: É o app alvo do episódio atual?
        vector.append(1.0 if target_name in text else 0.0)
        
        # 3. Injeta o Slot Dinâmico 2: É o arquivo de settings/data do alvo?
        vector.append(1.0 if (target_name in text and "settings" in text) or (f"{target_name}.settings" in text) else 0.0)
        
        return vector

    def get_state_vector(self, xml_content, target_name):
        """Soma o estado geral de leitura da tela inteira baseado no alvo atual"""
        screen_vector = np.zeros(self.vector_length)
        try:
            root = ET.fromstring(xml_content)
            for node in root.iter('node'):
                txt = node.attrib.get('text', '').lower() + " " + node.attrib.get('content-desc', '').lower()
                btn_vec = self.text_to_vector(txt, target_name)
                for i in range(self.vector_length):
                    if btn_vec[i] == 1.0:
                        screen_vector[i] = 1.0
        except:
            pass
        return screen_vector

    def get_clickables_and_scrolls(self, xml_content, target_name):
        """Mapeia o ambiente gerando as ações vetorizadas dinamicamente para o alvo da rodada"""
        actions = {}
        try:
            root = ET.fromstring(xml_content)
            for node in root.iter('node'):
                if node.attrib.get('clickable') == 'true' or node.attrib.get('resource-id') == 'android:id/text1':
                    text = node.attrib.get('text', '').lower()
                    desc = node.attrib.get('content-desc', '').lower()
                    bounds = node.attrib.get('bounds', '')

                    if not text and not desc:
                        continue

                    coords = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                    if coords:
                        x = (int(coords.group(1)) + int(coords.group(3))) // 2
                        y = (int(coords.group(2)) + int(coords.group(4))) // 2

                        btn_vector = self.text_to_vector(text + " " + desc, target_name)
                        action_key = f"CLICK|{x},{y}|{text[:15]}"
                        actions[action_key] = {"type": "click", "x": x, "y": y, "vector": btn_vector, "raw_text": text + " " + desc}
        except:
            pass

        # 📜 Ação virtual de SCROLL (A IA escolhe dar scroll quando julgar necessário)
        scroll_vector = self.text_to_vector("scroll rolar deslizar", target_name)
        actions["SISTEMA|scroll_down"] = {"type": "scroll", "vector": scroll_vector, "raw_text": "ação de rolar para baixo"}
        
        # 🔙 Botão físico Voltar
        back_vector = self.text_to_vector("voltar retornar", target_name)
        actions["SISTEMA|back"] = {"type": "back", "vector": back_vector, "raw_text": "botão voltar"}

        return actions

    def load_model(self):
        if os.path.exists(self.model_file):
            try:
                self.model.load_state_dict(torch.load(self.model_file))
                self.model.eval()
                print("🧠 Cérebro geral carregado com sucesso. Pronto para o estresse!")
            except:
                print("⚠️ Criando um novo cérebro neural geral.")

    def save_model(self):
        torch.save(self.model.state_dict(), self.model_file)

    def replay_experience(self):
        if len(self.memory) < self.batch_size:
            return
        batch = random.sample(self.memory, self.batch_size)
        self.model.train()

        for state_vec, action_vec, reward, next_state_vec, next_actions_vecs, is_terminal in batch:
            input_tensor = torch.FloatTensor(np.concatenate([state_vec, action_vec])).unsqueeze(0).to(self.device)
            current_q = self.model(input_tensor)

            if is_terminal or not next_actions_vecs:
                target_q = torch.FloatTensor([[reward]]).to(self.device)
            else:
                next_qs = []
                for n_a_vec in next_actions_vecs:
                    n_input = torch.FloatTensor(np.concatenate([next_state_vec, n_a_vec])).unsqueeze(0).to(self.device)
                    next_qs.append(self.model(n_input).item())
                target_q = torch.FloatTensor([[reward + self.gamma * max(next_qs)]]).to(self.device)

            loss = self.criterion(current_q, target_q)
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

    def live_stress_training(self):
        os.system('clear')
        print("🔥 APRENDIZADO SOB ESTRESSE ATIVADO! Varrendo os APKs do celular...")
        
        episode = 1
        lista_apks = self.get_installed_user_apps()

        while True:
            # 🎲 Escolhe um APP alvo completamente aleatório para este episódio!
            target_pkg, target_name = random.choice(lista_apks)
            
            print(f"\n╔══════════════════════════════════════════════════════════════╗")
            f"  EPISÓDIO #{episode} | ALVO DA VEZ: {target_name.upper()} ({target_pkg})"
            print(f"╚══════════════════════════════════════════════════════════════╝")
            
            # Aqui você pode dar um force-stop/start no app cloner para resetar o estado da tela
            time.sleep(1)
            steps = 0

            while steps < 25: # Limite de 25 ações por alvo
                xml = self.get_screen_xml()
                if not xml:
                    time.sleep(1)
                    continue

                state_vector = self.get_state_vector(xml, target_name)
                actions = self.get_clickables_and_scrolls(xml, target_name)

                # Avaliação da Rede Neural
                self.model.eval()
                action_scores = {}
                for key, data in actions.items():
                    input_tensor = torch.FloatTensor(np.concatenate([state_vector, data["vector"]])).unsqueeze(0)
                    with torch.no_grad():
                        action_scores[key] = self.model(input_tensor).item()

                # Epsilon-Greedy (Explorar vs Explorar)
                if random.uniform(0, 1) < self.epsilon:
                    chosen_key = random.choice(list(actions.keys()))
                    print(f"🎲 [Explorando] Movimento: {chosen_key.split('|')[-1]}")
                else:
                    chosen_key = max(action_scores, key=action_scores.get)
                    print(f"🧠 [Neurônios] Movimento: {chosen_key.split('|')[-1]} (Nota Q: {action_scores[chosen_key]:.2f})")

                action_data = actions[chosen_key]
                
                # Execução Física no Celular
                if action_data["type"] == "click":
                    self.root_command(f"input tap {action_data['x']} {action_data['y']}")
                elif action_data["type"] == "scroll":
                    self.root_command("input swipe 500 1500 500 600 300")
                elif action_data["type"] == "back":
                    self.root_command("input keyevent 4")

                time.sleep(1.5)
                steps += 1

                # --- 🎯 SISTEMA DE RECOMPENSAS GENERALIZADO ---
                new_xml = self.get_screen_xml()
                reward = -2.0  # Punição por tempo
                is_terminal = False
                txt_clicado = action_data["raw_text"]

                # Verificação dinâmica de Vitória Mestre usando as variáveis do alvo da rodada
                if f"{target_name}.settings" in txt_clicado or (target_name in txt_clicado and "settings" in txt_clicado):
                    print(f"🎉 ACERTOU EM CHEIO! Dados do {target_name.upper()} injetados com sucesso!")
                    reward = 4000.0 - (steps * 50)
                    is_terminal = True
                
                # Recompensas de trilha condizentes com o alvo dinâmico
                elif target_name in txt_clicado:
                    reward = 600.0  # Encontrou o aplicativo mutável na lista
                    print(f"  └─> [Recompensa] Achou o pacote do {target_name.upper()}")
                elif "load settings" in txt_clicado or "importar" in txt_clicado:
                    reward = 400.0  
                elif "download" in txt_clicado:
                    reward = 250.0  

                if not new_xml:
                    reward = -150.0
                    is_terminal = True

                new_state_vec = self.get_state_vector(new_xml, target_name) if new_xml else np.zeros(self.vector_length)
                new_actions = self.get_clickables_and_scrolls(new_xml, target_name) if new_xml else {}
                new_actions_vecs = [d["vector"] for d in new_actions.values()]

                # Gravação da memória e Replay (Treino em Lote)
                self.memory.append((state_vector, action_data["vector"], reward, new_state_vec, new_actions_vecs, is_terminal))
                self.replay_experience()

                if is_terminal:
                    break

            self.save_model()
            
            # Decaimento do Epsilon para ir consolidando o aprendizado real
            if self.epsilon > self.min_epsilon:
                self.epsilon -= 0.02
                
            episode += 1

if __name__ == "__main__":
    ai = ClonerStressAI()
    ai.live_stress_training()
