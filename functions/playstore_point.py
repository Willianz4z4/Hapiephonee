import os
import time
import subprocess
import random
import xml.etree.ElementTree as ET
import re
from datetime import timedelta
from collections import deque

# --- MACHINE LEARNING IMPORTS ---
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

# Novo vocabulário com as palavras de "fuga" para popups
VOCABULARIO = [
    "perfil", "conta", "account", "play points", "pontos do play", "perks", "vantagens", "benefícios", "claim", "reivindicar",
    "resgatar", "next silver prize", "available on", "voltar", "opções",
    "close", "fechar", "sair", "fechar anúncio", "ad", "skip"
]

class DeepQNetwork(nn.Module):
    """🧠 A Estrutura do Cérebro Artificial (3 Camadas Ocultas)"""
    def __init__(self, input_size):
        super(DeepQNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1) # Retorna UMA nota final (Q-Value) para o botão
        )

    def forward(self, x):
        return self.network(x)

class PlayStoreDeepAI:
    def __init__(self):
        self.model_file = "brain_neural.pth"
        self.log_file = "ai_training_deep.log"

        # Hyperparâmetros da Rede Neural
        self.gamma = 0.90
        self.epsilon = 0.80
        self.min_epsilon = 0.15
        self.batch_size = 32

        # Buffer de Memória (Sonho/Replay)
        self.memory = deque(maxlen=2000)
        
        # O Tamanho do Input = (Vocabulario da Tela) + (Vocabulario do Botão Específico)
        self.input_size = len(VOCABULARIO) * 2
        
        self.device = torch.device("cpu") # Usaremos a CPU da sua nuvem
        self.model = DeepQNetwork(self.input_size).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()
        
        self.load_model()
        self.global_start_time = time.time()

    def write_log(self, message):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

    def root_command(self, cmd):
        try:
            result = subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout.strip()
        except: 
            return ""

    def restart_playstore(self):
        self.root_command("am force-stop com.android.vending")
        time.sleep(1.0)
        self.root_command("am start -n com.android.vending/com.google.android.finsky.activities.MainActivity")
        time.sleep(3.0)

    def get_screen_xml(self):
        self.root_command("rm -f /data/local/tmp/dump.xml")
        xml = self.root_command("uiautomator dump /data/local/tmp/dump.xml > /dev/null && cat /data/local/tmp/dump.xml")
        return xml if xml and xml.startswith("<?xml") else None

    # --- EXTRAÇÃO DE DADOS PARA A REDE NEURAL ---
    def text_to_vector(self, text):
        """Converte um texto em uma lista de 0s e 1s para a Rede Neural entender."""
        text = text.lower()
        return [1.0 if palavra in text else 0.0 for palavra in VOCABULARIO]

    def get_state_vector(self, xml_content):
        """Soma todas as palavras da tela para criar o 'Clima' atual (Estado)."""
        screen_vector = np.zeros(len(VOCABULARIO))
        try:
            root = ET.fromstring(xml_content)
            for node in root.iter('node'):
                txt = node.attrib.get('text', '').lower() + " " + node.attrib.get('content-desc', '').lower()
                for i, palavra in enumerate(VOCABULARIO):
                    if palavra in txt: 
                        screen_vector[i] = 1.0
        except: 
            pass
        return screen_vector

    def get_smart_clickables(self, xml_content):
        """Pega os botões e já devolve vetorizados."""
        clickables = {}
        junk_ids = ["ad_label", "promo", "banner", "notification", "play_card"]
        
        # ⚠️ CORREÇÃO: Palavras relacionadas a anúncios agora tornam o botão invisível para ela
        junk_texts = ["mb", "gb", "download", "instalar", "boost", "days ago", "sponsored", "patrocinado", "anúncio", "ad"]

        try:
            root = ET.fromstring(xml_content)
            for node in root.iter('node'):
                if node.attrib.get('clickable') == 'true':
                    text = node.attrib.get('text', '').lower()
                    desc = node.attrib.get('content-desc', '').lower()
                    res_id = node.attrib.get('resource-id', '').lower()
                    bounds = node.attrib.get('bounds', '')

                    if not text and not desc: 
                        continue
                    if len(text) > 70 or any(j in text+desc for j in junk_texts) or any(j in res_id for j in junk_ids): 
                        continue

                    coords = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                    if coords:
                        x = (int(coords.group(1)) + int(coords.group(3))) // 2
                        y = (int(coords.group(2)) + int(coords.group(4))) // 2
                        
                        # DNA Neural: Extrai o vetor de palavras APENAS desse botão
                        btn_vector = self.text_to_vector(text + " " + desc)
                        action_key = f"{x},{y}|{text[:10]}"

                        clickables[action_key] = {
                            "x": x, "y": y,
                            "vector": btn_vector,
                            "raw_text": text + " " + desc
                        }
        except: 
            pass
            
        # INJEÇÃO: Botão Físico "Voltar" (A Cápsula de Fuga)
        btn_voltar_vector = self.text_to_vector("voltar fechar sair")
        clickables["SISTEMA|voltar"] = {
            "x": -1, "y": -1, # Coordenadas falsas, não serão usadas
            "vector": btn_voltar_vector,
            "raw_text": "botao fisico voltar"
        }
            
        return clickables

    # --- FUNÇÕES DE MEMÓRIA DA REDE NEURAL ---
    def load_model(self):
        if os.path.exists(self.model_file):
            try:
                self.model.load_state_dict(torch.load(self.model_file))
                self.model.eval()
            except RuntimeError:
                # Se o tamanho do vocabulário mudar, o carregamento vai falhar.
                print("⚠️ Vocabulário alterado! Criando um novo cérebro neural limpo.")
                pass

    def save_model(self):
        torch.save(self.model.state_dict(), self.model_file)

    def replay_experience(self):
        """O 'Sonho': A IA para e estuda as últimas memórias batendo em lote (Batch) na CPU"""
        if len(self.memory) < self.batch_size: 
            return

        batch = random.sample(self.memory, self.batch_size)
        self.model.train() # Entra em modo de treinamento

        for state_vec, action_vec, reward, next_state_vec, next_actions_vecs, is_terminal in batch:
            # Entrada = Estado (Tela) + Ação (Botão)
            input_tensor = torch.FloatTensor(np.concatenate([state_vec, action_vec])).unsqueeze(0).to(self.device)
            current_q = self.model(input_tensor)

            if is_terminal or not next_actions_vecs:
                target_q = torch.FloatTensor([[reward]]).to(self.device)
            else:
                # Acha o melhor botão da próxima tela para calcular o Q Futuro
                next_qs = []
                for n_a_vec in next_actions_vecs:
                    n_input = torch.FloatTensor(np.concatenate([next_state_vec, n_a_vec])).unsqueeze(0).to(self.device)
                    next_qs.append(self.model(n_input).item())

                target_q = torch.FloatTensor([[reward + self.gamma * max(next_qs)]]).to(self.device)

            # Ajusta os Neurônios (Backpropagation)
            loss = self.criterion(current_q, target_q)
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

    # --- CICLO DE VIDA ---
    def IA_learning(self):
        os.system('clear')
        print("🧠 IA DEEP LEARNING (Rede Neural Ativada). Fritando a CPU!")
        episode = 1

        while True:
            self.restart_playstore()
            start_time = time.time()
            steps = 0

            for step in range(12):
                xml = self.get_screen_xml()
                if not xml: 
                    continue
                
                state_vector = self.get_state_vector(xml)
                clickables = self.get_smart_clickables(xml)

                if not clickables:
                    self.root_command("input swipe 500 1500 500 500")
                    time.sleep(1)
                    continue
                
                # --- 1. A REDE NEURAL AVALIA TODOS OS BOTÕES DA TELA ---
                self.model.eval()
                action_scores = {}
                for key, data in clickables.items():
                    # Junta a tela e o botão num vetor (Tamanho: len(VOCABULARIO)*2)
                    input_tensor = torch.FloatTensor(np.concatenate([state_vector, data["vector"]])).unsqueeze(0)
                    with torch.no_grad():
                        nota_neural = self.model(input_tensor).item()
                        action_scores[key] = nota_neural

                # --- 2. ESCOLHE O CLIQUE ---
                if random.uniform(0, 1) < self.epsilon:
                    chosen_key = random.choice(list(clickables.keys()))
                    nome_botao = chosen_key.split('|')[1] if '|' in chosen_key else chosen_key
                    print(f"🎲 [Explorando] Botão: {nome_botao}")
                else:
                    chosen_key = max(action_scores, key=action_scores.get)
                    nome_botao = chosen_key.split('|')[1] if '|' in chosen_key else chosen_key
                    print(f"🧠 [Neurônios] Botão: {nome_botao} (Nota Prevista: {action_scores[chosen_key]:.1f})")

                action_vector = clickables[chosen_key]["vector"]
                x, y = clickables[chosen_key]["x"], clickables[chosen_key]["y"]

                # Executa o Clique ou o Botão Voltar Físico!
                if "SISTEMA|voltar" == chosen_key:
                    self.root_command("input keyevent 4")
                else:
                    self.root_command(f"input tap {x} {y}")
                time.sleep(1.5)
                steps += 1
                
                # --- 3. VERIFICA AS CONSEQUÊNCIAS ---
                new_xml = self.get_screen_xml()
                is_terminal = False
                reward = -5.0 # Punição natural por demorar

                if "com.android.vending" not in (new_xml or ""):
                    reward = -500.0
                    self.root_command("input keyevent 4")
                    is_terminal = True
                else:
                    txt_clicado = clickables[chosen_key]["raw_text"]
                    if any(t in txt_clicado for t in ["claim", "resgatar", "reivindicar"]):
                        print(f"🎯 ALVO MESTRE ENCONTRADO! GANHOU!")
                        reward = 2000.0 - (steps * 50)
                        is_terminal = True
                        
                    # ⚠️ CORREÇÃO: Fim do farm de pontos! Fuga agora não dá prêmio, dá punição leve
                    elif any(t in txt_clicado for t in ["close", "fechar", "sair", "skip"]): 
                        reward = -1.0 
                        print("🚪 Fuga ativada (mas sem ganhar pontos!)")
                        
                    elif any(t in txt_clicado for t in ["perks", "vantagens"]): 
                        reward = 90.0
                    elif any(t in txt_clicado for t in ["play points"]): 
                        reward = 60.0
                    elif any(t in txt_clicado for t in ["perfil", "conta"]): 
                        reward = 30.0

                new_state_vec = self.get_state_vector(new_xml) if new_xml else np.zeros(len(VOCABULARIO))
                new_clickables = self.get_smart_clickables(new_xml) if new_xml else {}
                new_actions_vecs = [data["vector"] for data in new_clickables.values()]

                # SALVA NA MEMÓRIA DE CURTO PRAZO
                self.memory.append((state_vector, action_vector, reward, new_state_vec, new_actions_vecs, is_terminal))

                # CHAMA A CPU PARA CALCULAR (TREINAR A REDE NEURAL)
                self.replay_experience()

                if is_terminal: 
                    break

            self.save_model()
            if self.epsilon > self.min_epsilon: 
                self.epsilon -= 0.05
            episode += 1

if __name__ == "__main__":
    ai = PlayStoreDeepAI()
    ai.IA_learning()
