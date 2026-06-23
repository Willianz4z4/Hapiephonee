import os
import time
import json
import subprocess
import random
import xml.etree.ElementTree as ET
import re
import hashlib

class PlayStoreSmartAI:
    def __init__(self):
        self.q_table_file = "q_table_memory.json"
        self.q_table = self.load_q_table()
        
        self.alpha = 0.5
        self.gamma = 0.8
        self.epsilon = 0.5
        self.min_epsilon = 0.20

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

    def get_smart_clickable_nodes(self, xml_content):
        clickables = []
        junk_ids = ["card", "cluster", "promo", "banner", "merch", "ad_label", "bucket", "suggestion"]
        junk_texts = ["app:", "jogo:", "game:", "classificação", "star rating", "download", "instalar", "install", "mb", "gb"]

        try:
            root = ET.fromstring(xml_content)
            for node in root.iter('node'):
                if node.attrib.get('clickable') == 'true':
                    text = node.attrib.get('text', '').lower()
                    desc = node.attrib.get('content-desc', '').lower()
                    res_id = node.attrib.get('resource-id', '').lower()
                    bounds = node.attrib.get('bounds', '')
                    
                    if not text and not desc and not res_id:
                        continue 
                    
                    is_junk = False
                    
                    for junk in junk_ids:
                        if junk in res_id:
                            is_junk = True
                            break
                            
                    if not is_junk:
                        for junk in junk_texts:
                            if junk in text or junk in desc:
                                is_junk = True
                                break
                    
                    if is_junk:
                        continue 

                    coords = self.parse_bounds(bounds)
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

    def IA_learning(self, episodes=15, max_steps_per_episode=10):
        print(f"🧠 REINFORCEMENT LEARNING (Salvamento Botão por Botão em Tempo Real)")
        
        ultimate_target = ["claim", "reivindicar", "resgatar"]
        path_hints = ["conta", "account", "perfil", "profile", "play points", "pontos do play", "perks", "benefícios", "vantagens"]

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
                    
                    clickables = self.get_smart_clickable_nodes(xml)
                    
                    if not clickables:
                        print("⬇️ Tela processada (Lixo ignorado). Rolando tela...")
                        self.root_command("input swipe 500 1500 500 500")
                        time.sleep(1.0)
                        continue

                    self.init_state_in_qtable(current_state, clickables)

                    alvo = self.check_for_targets(xml, ultimate_target)
                    if alvo:
                        action_key = f"{alvo[0]},{alvo[1]}"
                        time_taken = int(time.time() - start_time)
                        steps_count += 1
                        
                        reward = max(100.0, 2000.0 - (steps_count * 150) - (time_taken * 30))
                        
                        print(f"🎯 ALVO ENCONTRADO! Passo: {steps_count} | Tempo: {time_taken}s")
                        print(f"💰 Recompensa Calculada: +{reward:.1f} pontos!")
                        
                        old_q = self.q_table[current_state].get(action_key, 0)
                        self.q_table[current_state][action_key] = old_q + self.alpha * (reward - old_q)
                        
                        self.click(alvo[0], alvo[1])
                        self.save_q_table() # 🔥 SALVA IMEDIATAMENTE O SUCESSO
                        break

                    if random.uniform(0, 1) < self.epsilon:
                        top_buttons = [pt for pt in clickables if pt[1] < 400]
                        if top_buttons and random.choice([True, False]): 
                            x, y = random.choice(top_buttons)
                            print(f"🎲 [Explorando Topo] Clicou em: {x},{y}")
                        else:
                            x, y = random.choice(clickables)
                            print(f"🎲 [Explorando Geral] Clicou em: {x},{y}")
                        action_key = f"{x},{y}"
                    else:
                        best_action = max(self.q_table[current_state], key=self.q_table[current_state].get)
                        x, y = map(int, best_action.split(','))
                        action_key = best_action
                        print(f"🧠 [Usando Conhecimento] Botão {action_key} (Nota: {self.q_table[current_state][best_action]:.1f})")

                    self.click(x, y)
                    steps_count += 1

                    new_xml = self.get_screen_xml()
                    if not new_xml: new_xml = xml
                    new_state = self.get_state_hash(new_xml)
                    
                    reward = -2.0 
                    
                    is_outside_app = "com.android.vending" not in new_xml

                    if is_outside_app:
                        print("🚨 FATAL: O clique fechou a Play Store ou abriu outro app! (-500 pts)")
                        reward = -500.0
                        self.root_command("input keyevent 4") 
                        time.sleep(1.5)
                    elif new_state == current_state:
                        print("📉 Punição: Clicou em um botão inútil (-40 pts)")
                        reward = -40.0
                    elif new_state in visited_states:
                        print("⚠️ Punição: Loop de tela detectado (-25 pts)")
                        reward = -25.0
                        self.root_command("input keyevent 4") 
                        time.sleep(1.0)
                    else:
                        if self.check_for_targets(new_xml, path_hints):
                            print("📈 Recompensa: Entrou em menu com Pistas (+40 pts)")
                            reward = 40.0
                        else:
                            print("➡️ Avanço neutro.")

                    old_q_value = self.q_table[current_state].get(action_key, 0.0)
                    future_optimal_value = self.get_max_q_value(new_state)
                    
                    new_q_value = old_q_value + self.alpha * (reward + self.gamma * future_optimal_value - old_q_value)
                    self.q_table[current_state][action_key] = new_q_value
                    
                    self.save_q_table() # 🔥 SALVA IMEDIATAMENTE O APRENDIZADO DESTE BOTÃO ESPECÍFICO
                
                if self.epsilon > self.min_epsilon:
                    self.epsilon -= 0.04
                else:
                    self.epsilon = self.min_epsilon

        finally:
            self.toggle_visuals(False)

if __name__ == "__main__":
    ai = PlayStoreSmartAI()
    ai.IA_learning(episodes=10, max_steps_per_episode=12)
