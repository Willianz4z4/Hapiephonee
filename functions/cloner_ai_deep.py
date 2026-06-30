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

# 🧠 Vocabulário base em INGLÊS (Foco total no alvo)
VOCABULARIO = [
    "cloner", "clone", "app cloner", "load settings", "settings", "import",
    "data", "download", "storage", "emulated", "directory",
    "file", "back", "cancel", "ok", "confirm", "accept", "options"
]

class DeepQNetwork(nn.Module):
    def __init__(self, input_size):
        super(DeepQNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

    def forward(self, x):
        return self.network(x)

class ClonerStressAI:
    def __init__(self):
        self.model_file = "brain_cloner_general.pth"
        self.cloner_package = "com.ugcloner.xfein"

        self.gamma = 0.95
        self.epsilon = 0.40  # Mantemos 40% inicial para ela aprender a nova regra rápido
        self.min_epsilon = 0.05
        self.batch_size = 32

        self.memory = deque(maxlen=4000)
        self.priorities = deque(maxlen=4000)

        # Atualização Crítica: O vetor de estado agora recebe +1 espaço para a "etapa_atual"
        self.vector_length = len(VOCABULARIO) + 2
        self.state_size = self.vector_length + 1 
        self.input_size = self.state_size + self.vector_length

        self.device = torch.device("cpu")

        self.model = DeepQNetwork(self.input_size).to(self.device)
        self.target_model = DeepQNetwork(self.input_size).to(self.device)
        self.target_update_freq = 5

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
        saida = self.root_command("pm list packages -3")
        packages = []
        for line in saida.split("\n"):
            if "package:" in line:
                pkg = line.replace("package:", "").strip()
                parts = pkg.split(".")
                clean_name = parts[-1] if len(parts) > 1 else pkg
                if clean_name.lower() not in ["vending", "cloner", "ugcloner", "xfein", "launcher"]:
                    packages.append((pkg, clean_name))
        return packages if packages else [("com.termux", "termux"), ("com.roblox.client", "roblox")]

    def get_current_package(self):
        focus = self.root_command("dumpsys window | grep -E 'mCurrentFocus'")
        match = re.search(r'u0\s+([^/]+)', focus)
        if match:
            return match.group(1).strip()
        return ""

    def get_screen_xml(self):
        self.root_command("rm -f /data/local/tmp/cloner_dump.xml")
        xml = self.root_command("uiautomator dump /data/local/tmp/cloner_dump.xml > /dev/null && cat /data/local/tmp/cloner_dump.xml")
        return xml if xml and xml.startswith("<?xml") else None

    def text_to_vector(self, text, target_name):
        text = text.lower()
        target_name = target_name.lower()
        vector = [1.0 if palavra in text else 0.0 for palavra in VOCABULARIO]
        vector.append(1.0 if target_name in text else 0.0)

        is_target_setting = (target_name in text and "settings" in text) or (f"{target_name}.settings" in text)
        is_general_setting = "general.settings" in text

        vector.append(1.0 if is_target_setting or is_general_setting else 0.0)
        return vector

    def get_state_vector(self, xml_content, target_name):
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
        actions = {}
        try:
            root = ET.fromstring(xml_content)
            for node in root.iter('node'):
                text = node.attrib.get('text', '').lower()
                desc = node.attrib.get('content-desc', '').lower()
                pkg = node.attrib.get('package', '').lower()
                full_text = text + " " + desc

                if 'termux' in pkg or "ug cloner" in full_text or len(full_text.strip()) < 2:
                    continue

                if re.match(r'^[\u200e\u200f]+$', full_text.strip()):
                    continue

                bounds = node.attrib.get('bounds', '')
                coords = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                if coords:
                    x = (int(coords.group(1)) + int(coords.group(3))) // 2
                    y = (int(coords.group(2)) + int(coords.group(4))) // 2

                    btn_vector = self.text_to_vector(full_text, target_name)
                    action_key = f"CLICK|{x},{y}|{full_text[:15].strip()}"
                    actions[action_key] = {"type": "click", "x": x, "y": y, "vector": btn_vector, "raw_text": full_text}
        except:
            pass

        scroll_vector = self.text_to_vector("scroll", target_name)
        actions["SISTEMA|scroll_down"] = {"type": "scroll", "vector": scroll_vector, "raw_text": "scroll down"}

        back_vector = self.text_to_vector("back", target_name)
        actions["SISTEMA|back"] = {"type": "back", "vector": back_vector, "raw_text": "back button"}

        return actions

    def load_model(self):
        if os.path.exists(self.model_file):
            try:
                self.model.load_state_dict(torch.load(self.model_file))
                self.target_model.load_state_dict(self.model.state_dict())
                self.model.eval()
                print("🧠 Cérebro neural carregado com sucesso!")
            except:
                pass

    def save_model(self):
        torch.save(self.model.state_dict(), self.model_file)

    def replay_experience(self):
        if len(self.memory) < self.batch_size:
            return

        prios = np.array(self.priorities)
        probs = prios ** 0.6
        probs /= probs.sum()
        indices = np.random.choice(len(self.memory), self.batch_size, p=probs)

        batch = [self.memory[i] for i in indices]
        self.model.train()

        for idx, (i, (current_state, action_vec, reward, next_current_state, next_actions_vecs, is_terminal)) in enumerate(zip(indices, batch)):
            input_tensor = torch.FloatTensor(np.concatenate([current_state, action_vec])).unsqueeze(0).to(self.device)
            current_q = self.model(input_tensor)

            if is_terminal or not next_actions_vecs:
                target_q_val = reward
            else:
                next_qs = []
                for n_a_vec in next_actions_vecs:
                    n_input = torch.FloatTensor(np.concatenate([next_current_state, n_a_vec])).unsqueeze(0).to(self.device)
                    with torch.no_grad():
                        next_qs.append(self.target_model(n_input).item())
                target_q_val = reward + self.gamma * max(next_qs)

            target_q = torch.FloatTensor([[target_q_val]]).to(self.device)

            loss = self.criterion(current_q, target_q)
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            td_error = abs(current_q.item() - target_q_val)
            self.priorities[i] = td_error + 1e-5

    def live_stress_training(self):
        os.system('clear')
        print("🔥 IA INDUSTRIAL ATIVADA (ORDEM ESTRITA: APP -> SETTINGS)")

        episode = 1
        lista_apks = self.get_installed_user_apps()

        while True:
            target_pkg, target_name = random.choice(lista_apks)

            print(f"\n╔══════════════════════════════════════════════════════════════╗")
            print(f"  EPISÓDIO #{episode} | ALVO: {target_name.upper()} | ⏱️ MAX: 1 MINUTO")
            print(f"╚══════════════════════════════════════════════════════════════╝")

            self.root_command(f"am force-stop {self.cloner_package}")
            time.sleep(0.5)
            self.root_command(f"monkey -p {self.cloner_package} -c android.intent.category.LAUNCHER 1")
            print(f"🚀 [SISTEMA] UG Cloner inicializado automaticamente.")

            session_start_time = time.time()
            outside_app_start = None
            steps = 0

            etapa_atual = 0  # 0: Início | 1: Achou App | 2: Achou Import/Load Settings | 3: Achou Download
            spam_count = 0
            historico_acoes = deque(maxlen=4)

            while True:
                elapsed_session_time = time.time() - session_start_time
                if elapsed_session_time >= 60.0:
                    print("⏱️ [SESSÃO FINALIZADA] Tempo limite esgotado. Rotacionando alvo...")
                    break

                current_package = self.get_current_package()
                is_inside = any(x in current_package for x in [self.cloner_package, target_name, "packageinstaller", "vending"]) or current_package == ""

                if not is_inside:
                    if outside_app_start is None:
                        outside_app_start = time.time()
                    elif time.time() - outside_app_start >= 30.0:
                        print("🚨 [CRÍTICO] Fora do app! APLICANDO PENALIDADE MÁXIMA.")
                        if len(self.memory) > 0:
                            last_exp = list(self.memory)[-1]
                            # Escala reduzida: de -5000 para -5.0
                            self.memory[-1] = (last_exp[0], last_exp[1], -5.0, last_exp[3], last_exp[4], True)
                            self.priorities[-1] = 5.0 
                        self.root_command(f"am force-stop {self.cloner_package}")
                        break
                else:
                    outside_app_start = None

                xml = self.get_screen_xml()
                if not xml:
                    time.sleep(1)
                    continue

                state_vector = self.get_state_vector(xml, target_name)
                # Injetando a etapa atual no vetor de visão da IA (Normalizado 0.0 a 1.0)
                etapa_norm = etapa_atual / 3.0
                current_state = np.concatenate([state_vector, [etapa_norm]])

                actions = self.get_clickables_and_scrolls(xml, target_name)

                if not actions:
                    time.sleep(1)
                    continue

                self.model.eval()
                action_scores = {}
                for key, data in actions.items():
                    input_tensor = torch.FloatTensor(np.concatenate([current_state, data["vector"]])).unsqueeze(0)
                    with torch.no_grad():
                        action_scores[key] = self.model(input_tensor).item()

                if random.uniform(0, 1) < self.epsilon:
                    chosen_key = random.choice(list(actions.keys()))
                    print(f"🎲 [Explorando] Movimento: {chosen_key.split('|')[-1]}")
                else:
                    chosen_key = max(action_scores, key=action_scores.get)
                    print(f"🧠 [Neurônios] Movimento: {chosen_key.split('|')[-1]} (Nota Q: {action_scores[chosen_key]:.2f})")

                action_data = actions[chosen_key]

                if action_data["type"] == "click":
                    self.root_command(f"input tap {action_data['x']} {action_data['y']}")
                elif action_data["type"] == "scroll":
                    self.root_command("input swipe 500 1500 500 600 300")
                elif action_data["type"] == "back":
                    self.root_command("input keyevent 4")

                time.sleep(0.2)

                new_xml = self.get_screen_xml()
                new_actions = self.get_clickables_and_scrolls(new_xml, target_name) if new_xml else {}

                if new_xml and set(new_actions.keys()) == set(actions.keys()):
                    time.sleep(0.5)
                    new_xml = self.get_screen_xml()
                    new_actions = self.get_clickables_and_scrolls(new_xml, target_name) if new_xml else {}

                steps += 1

                new_state_vec = self.get_state_vector(new_xml, target_name) if new_xml else np.zeros(self.vector_length)
                new_actions_vecs = [d["vector"] for d in new_actions.values()]

                reward = 0.0
                is_terminal = False
                txt_clicado = action_data["raw_text"]

                # ======================================================
                # 🥊 1. ANTI-PING-PONG (Recompensas achatadas)
                # ======================================================
                if chosen_key in historico_acoes:
                    spam_count += 1
                    reward = -0.5 * spam_count  # Punição gradativa suave
                    print(f"  └─> ⚠️ LOOP DETECTADO! Punição de {reward:.1f} pontos!")
                else:
                    spam_count = 0

                historico_acoes.append(chosen_key)

                # ======================================================
                # 🛡️ 2. MÁQUINA DE ESTADOS RESTRITA (Recompensas achatadas)
                # ======================================================
                if reward == 0.0:

                    if txt_clicado.strip() == "file" or "delta-" in txt_clicado:
                        print("🚫 [VENENO INTERCEPTADO] Clicou em arquivo morto. Punido!")
                        reward = -0.5

                    # 🎯 PASSO 1: ACHAR O APP
                    elif target_name in txt_clicado:
                        if etapa_atual == 0:
                            etapa_atual = 1
                            reward = 1.5
                            print(f"  └─> [Recompensa] PASSO 1 OK: Clicou no App Alvo ({target_name.upper()})")
                            historico_acoes.clear()
                        else:
                            reward = -0.3
                            print(f"  └─> ⚠️ Punição: Já escolheu o app, não precisa clicar nele de novo.")

                    # ⚙️ PASSO 2: ACHAR SETTINGS OU IMPORT
                    elif "setting" in txt_clicado or "import" in txt_clicado:
                        if etapa_atual == 0:
                            print("🚨 [ERRO DE ORDEM] Tentou clicar em Settings antes de achar o App!")
                            reward = -1.5
                        else:
                            etapa_atual = max(etapa_atual, 2)
                            reward = 1.0
                            print("  └─> [Recompensa] PASSO 2 OK: Entrou nas Configurações/Importação!")
                            historico_acoes.clear()

                    # 📥 PASSO 3: ACHAR DOWNLOAD
                    elif "download" in txt_clicado:
                        if etapa_atual >= 2:
                            etapa_atual = max(etapa_atual, 3)
                            reward = 0.8
                            print("  └─> [Recompensa] PASSO 3 OK: Entrou na pasta Downloads!")
                            historico_acoes.clear()
                        else:
                            print("🚨 [ERRO DE ORDEM] Foi para Downloads fora de ordem!")
                            reward = -1.5

                    # ⚠️ AÇÕES NEUTRAS (SCROLL, BACK, ETC)
                    else:
                        if new_xml and set(new_actions.keys()) == set(actions.keys()):
                            reward = -0.05
                            print(f"  └─> ⚠️ AÇÃO INERTE.")

                if not new_xml:
                    reward = -0.2
                    is_terminal = True

                # Salva o novo estado considerando se a etapa_atual mudou
                new_etapa_norm = etapa_atual / 3.0
                new_current_state = np.concatenate([new_state_vec, [new_etapa_norm]])

                max_prio = max(self.priorities) if self.memory else 1.0
                self.memory.append((current_state, action_data["vector"], reward, new_current_state, new_actions_vecs, is_terminal))
                self.priorities.append(max_prio)

                self.replay_experience()

                if is_terminal:
                    break

            self.save_model()

            if episode % self.target_update_freq == 0:
                self.target_model.load_state_dict(self.model.state_dict())
                print("🔄 [SISTEMA] Rede Alvo sincronizada com sucesso!")

            if self.epsilon > self.min_epsilon:
                self.epsilon -= 0.02

            episode += 1

if __name__ == "__main__":
    ai = ClonerStressAI()
    ai.live_stress_training()
