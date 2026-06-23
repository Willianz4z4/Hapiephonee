import os
import time
import json
import subprocess
import random
import xml.etree.ElementTree as ET
import re
import hashlib

class PlayStoreQLearningAI:
    def __init__(self):
        self.q_table_file = "q_table_memory.json"
        self.q_table = self.load_q_table()
        
        # Hyperparâmetros da IA
        self.alpha = 0.5  # Taxa de aprendizado
        self.gamma = 0.8  # Fator de desconto para decisões futuras
        self.epsilon = 0.5 # Começa com 50% de curiosidade (Exploração)
        self.min_epsilon = 0.20 # 🔥 CRUCIAL: Nunca baixa de 20%, garantindo que ela sempre teste rotas novas!

    def root_command(self, cmd):
        full_cmd = f"su -c '{cmd}'"
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()

    def toggle_visuals(self, enable=True):
        val = "1" if enable else "0"
        cmd = f"settings put --user 0 system show_touches {val} ; settings put --user 0 system pointer_location {val}"
        self.root_command(cmd)

    def restart_playstore(self):
        print("\n🔄 Resetando ambiente para novo Episódio...")
        cmd = "am force-stop com.android.vending ; sleep 0.5 ; monkey -p com.android.vending -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1"
        self.root_command(cmd)
        time.sleep(3.0)

    def get_screen_xml(self):
        cmd = "uiautomator dump /data/local/tmp/dump.xml > /dev/null && cat /data/local/tmp/dump.xml"
        xml_content = self.root_command(cmd)
        if not xml_content or not xml_content.startswith("<?xml"):
            return None
        return xml_content

    def parse_bounds(self, bounds_str):
        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            return (x1 + x2) // 2, (y1 + y2) // 2
        return None

    def get_all_clickable_nodes(self, xml_content):
        clickables = []
        try:
            root = ET.fromstring(xml_content)
            for node in root.iter('node'):
                if node.attrib.get('clickable') == 'true':
                    coords = self.parse_bounds(node.attrib.get('bounds'))
                    if coords:
                        clickables.append(coords)
        except:
            pass
        return clickables

    def check_for_targets(self, xml_content, target_texts):
        try:
            root = ET.fromstring(xml_content)
            target_texts = [t.lower() for t in target_texts]
            for node in root.iter('node'):
                text = node.attrib.get('text', '').lower()
                content_desc = node.attrib.get('content-desc', '').lower()
                for target in target_texts:
                    if target in text or target in content_desc:
                        return self.parse_bounds(node.attrib.get('bounds'))
        except:
            pass
        return None

    def get_state_hash(self, xml_string):
        return hashlib.md5(xml_string.encode('utf-8')).hexdigest()

    def click(self, x, y):
        self.root_command(f"input tap {x} {y}")
        time.sleep(1.0)

    def load_q_table(self):
        if os.path.exists(self.q_table_file):
            with open(self.q_table_file, "r") as f:
                return json.load(f)
        return {}

    def save_q_table(self):
        with open(self.q_table_file, "w") as f:
            json.dump(self.q_table, f, indent=4)

    def init_state_in_qtable(self, state_hash, clickables):
        if state_hash not in self.q_table:
            self.q_table[state_hash] = {}
            for x, y in clickables:
                action_key = f"{x},{y}"
                self.q_table[state_hash][action_key] = 0.0

    def get_max_q_value(self, state_hash):
        if state_hash not in self.q_table or not self.q_table[state_hash]:
            return 0.0
        return max(self.q_table[state_hash].values())

    def IA_learning(self, episodes=15, max_steps_per_episode=15):
        print(f"🧠 REINFORCEMENT LEARNING (Pontuação Dinâmica por Eficiência)")
        
        ultimate_target = ["claim", "reivindicar", "resgatar"]
        path_hints = ["perfil", "conta", "profile", "account", "play points", "pontos do play", "perks", "benefícios", "vantagens"]

        self.toggle_visuals(True)

        try:
            for episode in range(1, episodes + 1):
                print(f"\n========================================")
                print(f"🎬 EPISÓDIO {episode}/{episodes} (Curiosidade Ativa: {int(self.epsilon * 100)}%)")
                self.restart_playstore()
                
                start_time = time.time()
                visited_states = set()
                steps_count = 0

                for step in range(max_steps_per_episode):
                    xml = self.get_screen_xml()
                    if not xml:
                        time.sleep(0.5)
                        continue

                    current_state = self.get_state_hash(xml)
                    visited_states.add(current_state)
                    clickables = self.get_all_clickable_nodes(xml)
                    
                    if not clickables:
                        print("⬇️ Sem botões visíveis. Rolando...")
                        self.root_command("input swipe 500 1500 500 500")
                        time.sleep(1.0)
                        continue

                    self.init_state_in_qtable(current_state, clickables)

                    # 1. VERIFICA SE O ALVO ESTÁ NA TELA
                    alvo = self.check_for_targets(xml, ultimate_target)
                    if alvo:
                        action_key = f"{alvo[0]},{alvo[1]}"
                        time_taken = int(time.time() - start_time)
                        steps_count += 1
                        
                        # 🔥 RECOMPENSA DINÂMICA (Baseada em performance)
                        # Quanto menos passos e menos tempo levar, maior o prêmio.
                        # Rotas burras ou demoradas ganham muito pouca recompensa.
                        reward = max(100.0, 2000.0 - (steps_count * 150) - (time_taken * 30))
                        
                        print(f"🎯 ALVO ENCONTRADO! Passo: {steps_count} | Tempo: {time_taken}s")
                        print(f"💰 Recompensa Calculada por Eficiência: +{reward:.1f} pontos!")
                        
                        # Aplica o aprendizado na tabela Q
                        old_q = self.q_table[current_state].get(action_key, 0)
                        self.q_table[current_state][action_key] = old_q + self.alpha * (reward - old_q)
                        
                        self.click(alvo[0], alvo[1])
                        self.save_q_table()
                        break

                    # 2. SELEÇÃO DE AÇÃO (Epsilon-Greedy com trava de curiosidade)
                    if random.uniform(0, 1) < self.epsilon:
                        x, y = random.choice(clickables)
                        action_key = f"{x},{y}"
                        print(f"🎲 [Explorando Novo] Clicou em: {action_key}")
                    else:
                        best_action = max(self.q_table[current_state], key=self.q_table[current_state].get)
                        x, y = map(int, best_action.split(','))
                        action_key = best_action
                        print(f"🧠 [Usando Conhecimento] Botão {action_key} (Nota Atual: {self.q_table[current_state][best_action]:.1f})")

                    # EXECUTAR AÇÃO
                    self.click(x, y)
                    steps_count += 1

                    # 3. ANALISAR CONSEQUÊNCIAS (S')
                    new_xml = self.get_screen_xml()
                    if not new_xml: new_xml = xml

                    new_state = self.get_state_hash(new_xml)
                    
                    # Sistema de Recompensas e Punições de meio de caminho
                    reward = -2.0 # Custo por clique (força a IA a querer terminar logo)

                    if new_state == current_state:
                        print("📉 Punição: Botão inútil, não mudou a tela (-40 pts)")
                        reward = -40.0
                    elif new_state in visited_states:
                        print("⚠️ Punição: Entrou em Loop/Voltou de tela (-25 pts)")
                        reward = -25.0
                    else:
                        # Verificando se a nova tela tem pistas lógicas
                        if self.check_for_targets(new_xml, path_hints):
                            print("📈 Recompensa: Entrou em tela com pistas óbvias (+40 pts)")
                            reward = 40.0
                        else:
                            print("➡️ Avanço neutro para tela desconhecida (-2 pts)")

                    # ATUALIZAÇÃO DA TABELA MATRIZ (Equação Bellman de Q-Learning)
                    old_q_value = self.q_table[current_state].get(action_key, 0.0)
                    future_optimal_value = self.get_max_q_value(new_state)
                    
                    new_q_value = old_q_value + self.alpha * (reward + self.gamma * future_optimal_value - old_q_value)
                    self.q_table[current_state][action_key] = new_q_value

                self.save_q_table()
                
                # Diminui a curiosidade aos poucos, mas respeita o limite mínimo de 20%
                if self.epsilon > self.min_epsilon:
                    self.epsilon -= 0.04
                else:
                    self.epsilon = self.min_epsilon

        finally:
            self.toggle_visuals(False)

if __name__ == "__main__":
    ai = PlayStoreQLearningAI()
    ai.IA_learning(episodes=15, max_steps_per_episode=15)
