import os
import time
import json
import subprocess
import random
import xml.etree.ElementTree as ET
import re
import hashlib

class PlayStoreTrueAI:
    def __init__(self):
        self.q_table_file = "q_table_memory.json"
        self.q_table = self.load_q_table()
        
        self.alpha = 0.5
        self.gamma = 0.8
        self.epsilon = 0.6 
        self.min_epsilon = 0.20

    def root_command(self, cmd):
        full_cmd = f"su -c '{cmd}'"
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()

    def restart_playstore(self):
        print("\n🔄 Limpando a mente e reiniciando a Play Store...")
        cmd = "am force-stop com.android.vending ; sleep 0.5 ; monkey -p com.android.vending -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1"
        self.root_command(cmd)
        time.sleep(3.5)

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

    def get_smart_clickables(self, xml_content):
        """Retorna um Dicionário de botões válidos com filtro rigoroso de Parágrafos e Notificações."""
        clickables = {}
        
        junk_ids = ["ad_label", "promo", "banner", "suggestion", "overflow", "notification"]
        
        # 🔥 NOVOS VENENOS: Tudo que remete a notificações, tempo passado ou ofertas
        junk_texts = [
            "mb", "gb", "download", "instalar", "install", "opções", "options", "more options", 
            "mais opções", "avaliação", "boost", "days ago", "hours ago", "week ago", "minute", 
            "oferta", "offer", "notificação"
        ]

        seen_signatures = set()

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
                        
                    # 🧠 FILTRO DE TAMANHO: Botões reais de menu não têm 60 caracteres!
                    if len(text) > 50 or len(desc) > 50:
                        continue
                    
                    is_junk = False
                    for junk in junk_ids:
                        if junk in res_id: is_junk = True; break
                            
                    if not is_junk:
                        for junk in junk_texts:
                            if junk in text or junk in desc: is_junk = True; break
                    
                    if is_junk: continue 

                    signature = f"{res_id}|{text}|{desc}"
                    if signature != "||":
                        if signature in seen_signatures: continue
                        seen_signatures.add(signature)

                    coords = self.parse_bounds(bounds)
                    if coords:
                        action_key = f"{coords[0]},{coords[1]}"
                        clickables[action_key] = {"text": text, "desc": desc}
        except:
            pass
        return clickables

    def check_for_target(self, clickables_dict, target_texts):
        """🔥 AGORA ELE SÓ PROCURA O ALVO DENTRO DOS BOTÕES VÁLIDOS (Sem risco de ler parágrafos)."""
        target_texts = [t.lower() for t in target_texts]
        
        for action_key, data in clickables_dict.items():
            combined_text = data["text"] + " " + data["desc"]
            for target in target_texts:
                if target in combined_text:
                    return action_key
        return None

    def get_state_hash(self, clickables_dict):
        keys = sorted(list(clickables_dict.keys()))
        state_str = "|".join(keys)
        return hashlib.md5(state_str.encode('utf-8')).hexdigest()

    def click(self, action_key):
        if action_key == "swipe_down":
            self.root_command("input swipe 500 1500 500 500")
            time.sleep(1.0)
        else:
            x, y = action_key.split(',')
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

    def get_max_q_value(self, state_hash):
        if state_hash not in self.q_table or not self.q_table[state_hash]:
            return 0.0
        return max(self.q_table[state_hash].values())

    def IA_learning(self, episodes=10, max_steps_per_episode=15):
        print(f"🧠 IA CIENTÍFICA (Proteção contra Falsos Positivos e Textos Longos)")
        
        ultimate_target = ["claim", "reivindicar", "resgatar"]
        path_hints = ["conta", "account", "perfil", "profile", "play points", "pontos do play", "perks", "benefícios", "vantagens"]

        try:
            for episode in range(1, episodes + 1):
                print(f"\n========================================")
                print(f"🎬 EPISÓDIO {episode}/{episodes} (Curiosidade: {int(self.epsilon * 100)}%)")
                self.restart_playstore()
                
                start_time = time.time()
                visited_states = set()
                steps_count = 0
                scroll_count = 0

                for step in range(max_steps_per_episode):
                    xml = self.get_screen_xml()
                    if not xml:
                        time.sleep(0.5)
                        continue

                    clickables_dict = self.get_smart_clickables(xml)
                    current_state = self.get_state_hash(clickables_dict)
                    visited_states.add(current_state)
                    
                    if not clickables_dict:
                        action_key = "swipe_down"
                    else:
                        if current_state not in self.q_table:
                            self.q_table[current_state] = {k: 0.0 for k in clickables_dict.keys()}
                            self.q_table[current_state]["swipe_down"] = 0.0

                        # 1. VERIFICA O PRÊMIO FINAL (Agora usa o dicionário filtrado!)
                        alvo_key = self.check_for_target(clickables_dict, ultimate_target)
                        if alvo_key:
                            time_taken = int(time.time() - start_time)
                            reward = max(100.0, 2000.0 - (steps_count * 150) - (time_taken * 30))
                            
                            print(f"\n🎯 PRÊMIO ENCONTRADO EM {alvo_key}! (Passos: {steps_count+1})")
                            print(f"💰 Recompensa Gorda: +{reward:.1f} pontos")
                            
                            old_q = self.q_table[current_state].get(alvo_key, 0)
                            self.q_table[current_state][alvo_key] = old_q + self.alpha * (reward - old_q)
                            
                            self.click(alvo_key)
                            self.save_q_table()
                            break

                        # 2. ESCOLHE A AÇÃO
                        available_actions = list(self.q_table[current_state].keys())
                        if random.uniform(0, 1) < self.epsilon:
                            action_key = random.choice(available_actions)
                            print(f"🎲 [Explorando] Escolheu: {action_key}")
                        else:
                            action_key = max(self.q_table[current_state], key=self.q_table[current_state].get)
                            nota = self.q_table[current_state][action_key]
                            print(f"🧠 [Conhecimento] Escolheu: {action_key} (Nota: {nota:.1f})")

                    if action_key == "swipe_down":
                        scroll_count += 1
                        if scroll_count >= 3:
                            print("⚠️ Beco sem saída (3 scrolls). Forçando Voltar...")
                            self.root_command("input keyevent 4")
                            time.sleep(1.0)
                            scroll_count = 0
                            continue
                    else:
                        scroll_count = 0 

                    self.click(action_key)
                    steps_count += 1

                    # 3. AVALIA O RESULTADO DA AÇÃO
                    new_xml = self.get_screen_xml()
                    if not new_xml: new_xml = xml
                    
                    new_clickables = self.get_smart_clickables(new_xml)
                    new_state = self.get_state_hash(new_clickables)
                    
                    reward = -2.0 
                    is_outside_app = "com.android.vending" not in new_xml

                    if is_outside_app:
                        print("🚨 FATAL: Abriu outro app. Punição Severa!")
                        reward = -300.0
                        self.root_command("input keyevent 4") 
                        time.sleep(1.5)
                    elif new_state == current_state:
                        print("📉 Punição: O botão não abriu tela nova (-50 pts)")
                        reward = -50.0
                    elif new_state in visited_states:
                        print("⚠️ Punição: Voltou pra uma tela antiga (Loop) (-30 pts)")
                        reward = -30.0
                        self.root_command("input keyevent 4") 
                        time.sleep(1.0)
                    else:
                        if action_key in clickables_dict:
                            btn_text_desc = clickables_dict[action_key]["text"] + " " + clickables_dict[action_key]["desc"]
                            if any(hint in btn_text_desc for hint in path_hints):
                                print(f"📈 Recompensa: Clicou numa pista Lógica! (+60 pts)")
                                reward = 60.0
                            else:
                                print("➡️ Avanço neutro. Tela nova.")
                        else:
                            print("➡️ Scrollou. Tela nova.")

                    if current_state in self.q_table:
                        old_q_value = self.q_table[current_state].get(action_key, 0.0)
                        future_optimal_value = self.get_max_q_value(new_state)
                        
                        new_q_value = old_q_value + self.alpha * (reward + self.gamma * future_optimal_value - old_q_value)
                        self.q_table[current_state][action_key] = new_q_value
                        self.save_q_table()
                
                if self.epsilon > self.min_epsilon:
                    self.epsilon -= 0.05
                else:
                    self.epsilon = self.min_epsilon

        except KeyboardInterrupt:
            print("\n🛑 Treinamento interrompido pelo usuário.")

if __name__ == "__main__":
    ai = PlayStoreTrueAI()
    ai.IA_learning(episodes=15, max_steps_per_episode=12)
