import os
import time
import json
import subprocess
import random
import xml.etree.ElementTree as ET
import re
import hashlib
from datetime import timedelta

class PlayStoreTrueAI:
    def __init__(self):
        self.q_table_file = "q_table_memory.json"
        self.log_file = "ai_training.log"
        self.q_table = self.load_q_table()
        
        self.alpha = 0.5
        self.gamma = 0.8
        
        self.epsilon = 0.70 
        self.min_epsilon = 0.15
        
        # 📌 Pistas de Ouro (Se tiver isso, a IA foca neles e ignora os filtros)
        self.hint_rewards = {
            "perfil": 30.0, "profile": 30.0, "conta": 30.0, "account": 30.0, 
            "logado como": 40.0, "signed in as": 40.0, "configurações": 20.0, "settings": 20.0,
            "play points": 60.0, "pontos do play": 60.0,
            "perks": 90.0, "vantagens": 90.0, "benefícios": 90.0
        }
        
        self.ultimate_target = ["claim", "reivindicar", "resgatar", "next silver prize", "available on"]
        self.global_start_time = time.time()

    def write_log(self, message):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

    def root_command(self, cmd):
        full_cmd = f"su -c '{cmd}'"
        try:
            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            self.write_log(f"⚠️ Timeout executando comando: {cmd}")
            return ""
        except Exception as e:
            return ""

    def toggle_visuals(self, enable=True):
        val = "1" if enable else "0"
        cmd = f"settings put --user 0 system show_touches {val} ; settings put --user 0 system pointer_location {val}"
        self.root_command(cmd)

    def restart_playstore(self):
        self.write_log("Forçando reinício da Play Store (True Reset)")
        self.root_command("am force-stop com.android.vending")
        time.sleep(1.0) 
        self.root_command("am start -n com.android.vending/com.google.android.finsky.activities.MainActivity")
        time.sleep(2.5) 

    def get_screen_xml(self):
        self.root_command("rm -f /data/local/tmp/dump.xml")
        cmd = "uiautomator dump /data/local/tmp/dump.xml > /dev/null && cat /data/local/tmp/dump.xml"
        xml_content = self.root_command(cmd)
        if not xml_content or not xml_content.startswith("<?xml"):
            return None
        return xml_content

    def parse_bounds(self, bounds_str):
        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            if x1 == x2 or y1 == y2:
                return None
            return (x1 + x2) // 2, (y1 + y2) // 2
        return None

    def get_smart_clickables(self, xml_content):
        clickables = {}
        # 🚫 FILTRO ANTI-APPS APRIMORADO (Bloqueia cartões, mídia e sugestões de apps)
        junk_ids = [
            "ad_label", "promo", "banner", "suggestion", "overflow", "notification",
            "play_card", "card", "cluster", "screenshot", "video_thumbnail", "list_item"
        ]
        junk_texts = [
            "mb", "gb", "download", "instalar", "install", "opções", "options", "more options", 
            "mais opções", "avaliação", "boost", "days ago", "hours ago", "week ago", "minute", 
            "oferta", "offer", "notificação", "classificação", "estrelas", "stars", "grátis", 
            "free", "compras no app", "in-app", "jogo:", "app:", "anúncio", "patrocinado"
        ]
        seen_signatures = set()

        try:
            root = ET.fromstring(xml_content)
            for node in root.iter('node'):
                text = node.attrib.get('text', '').lower()
                desc = node.attrib.get('content-desc', '').lower()
                res_id = node.attrib.get('resource-id', '').lower()
                bounds = node.attrib.get('bounds', '')
                is_clickable = node.attrib.get('clickable') == 'true'
                
                if node.attrib.get('visible-to-user') == 'false':
                    continue
                
                if not text and not desc and not res_id:
                    continue 
                if len(text) > 70 or len(desc) > 70: # Aumentado um pouco para ler o "logado como..." inteiro
                    continue

                is_target = any(t in text or t in desc for t in self.ultimate_target)
                is_hint = any(h in text or h in desc for h in self.hint_rewards.keys())

                if not is_clickable and not is_target and not is_hint:
                    continue
                
                # Só passa no Filtro Anti-Apps se o botão não for o nosso Alvo nem uma Pista de Ouro
                is_junk = False
                if not is_target and not is_hint:
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
        except Exception:
            pass
        return clickables

    def check_for_target(self, clickables_dict):
        for action_key, data in clickables_dict.items():
            combined_text = data["text"] + " " + data["desc"]
            for target in self.ultimate_target:
                if target in combined_text:
                    x, y = map(int, action_key.split(','))
                    if x > 10 and y > 10: 
                        return action_key
        return None

    def get_state_hash(self, clickables_dict):
        elements = [data["text"] + "|" + data["desc"] for data in clickables_dict.values()]
        elements = sorted([e for e in elements if e.strip() != "|"])
        state_str = "||".join(elements)
        return hashlib.md5(state_str.encode('utf-8')).hexdigest()

    def click(self, action_key):
        if action_key == "swipe_down":
            self.root_command("input swipe 500 1500 500 500")
            time.sleep(0.8) 
        else:
            x, y = action_key.split(',')
            self.root_command(f"input tap {x} {y}")
            time.sleep(0.8) 

    def load_q_table(self):
        if os.path.exists(self.q_table_file):
            try:
                with open(self.q_table_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_q_table(self):
        with open(self.q_table_file, "w") as f:
            json.dump(self.q_table, f, indent=4)

    def get_max_q_value(self, state_hash):
        if state_hash not in self.q_table or not self.q_table[state_hash]:
            return 0.0
        return max(self.q_table[state_hash].values())

    def get_formatted_time(self):
        elapsed_seconds = int(time.time() - self.global_start_time)
        return str(timedelta(seconds=elapsed_seconds))

    def IA_learning(self, max_steps_per_episode=15):
        os.system('clear' if os.name == 'posix' else 'cls')
        print("🧠 IA True Point (Filtro Anti-Apps Ativo). Monitoramento focado em navegação.")
        print("Verifique os passos reais com: tail -f ai_training.log\n")
        
        self.write_log("=== NOVO TREINAMENTO INICIADO (FOCO EM MENUS) ===")
        self.toggle_visuals(True)
        episode = 1

        try:
            while True:
                tempo_rodado = self.get_formatted_time()
                curiosidade_percentual = int(round(self.epsilon * 100))
                print(f"\r▶️ Tentativa: {episode} | Tempo: {tempo_rodado} | Curiosidade: {curiosidade_percentual}%   ", end="", flush=True)
                
                self.write_log(f"--- Iniciando Episódio {episode} ---")
                self.restart_playstore()
                
                start_time = time.time()
                visited_states = set()
                tried_actions_in_state = {} 
                steps_count = 0
                scroll_count = 0
                abortar_episodio = False

                for step in range(max_steps_per_episode):
                    if (time.time() - start_time) >= 30.0:
                        self.write_log("⏳ Limite de 30 segundos! Cortando episódio.")
                        break

                    xml = self.get_screen_xml()
                    if not xml: continue

                    clickables_dict = self.get_smart_clickables(xml)
                    current_state = self.get_state_hash(clickables_dict)
                    visited_states.add(current_state)
                    
                    if current_state not in tried_actions_in_state:
                        tried_actions_in_state[current_state] = set()
                    
                    if not clickables_dict:
                        action_key = "swipe_down"
                    else:
                        if current_state not in self.q_table:
                            self.q_table[current_state] = {k: 0.0 for k in clickables_dict.keys()}
                            self.q_table[current_state]["swipe_down"] = 0.0

                        alvo_key = self.check_for_target(clickables_dict)
                        if alvo_key:
                            time_taken = int(time.time() - start_time)
                            reward = max(100.0, 2000.0 - (steps_count * 150) - (time_taken * 40))
                            self.write_log(f"🎯 TARGET ENCONTRADO! Coord: {alvo_key} | Passos: {steps_count+1} | +{reward:.1f}")
                            
                            old_q = self.q_table[current_state].get(alvo_key, 0)
                            self.q_table[current_state][alvo_key] = old_q + self.alpha * (reward - old_q)
                            self.save_q_table()
                            abortar_episodio = True 
                            break 

                        available_actions = list(self.q_table[current_state].keys())
                        
                        acoes_virgens = [
                            k for k in available_actions 
                            if self.q_table[current_state][k] == 0.0 and k not in tried_actions_in_state[current_state]
                        ]
                        acoes_nao_clicadas_hoje = [
                            k for k in available_actions 
                            if k not in tried_actions_in_state[current_state]
                        ]

                        if random.uniform(0, 1) < self.epsilon:
                            if acoes_virgens:
                                action_key = random.choice(acoes_virgens)
                                self.write_log(f"🎲 [Curiosidade] Clicando em botão de Menu INÉDITO: {action_key}")
                            elif acoes_nao_clicadas_hoje:
                                action_key = random.choice(acoes_nao_clicadas_hoje)
                                self.write_log(f"🎲 [Curiosidade] Testando outro botão da interface: {action_key}")
                            else:
                                action_key = random.choice(available_actions)
                                self.write_log(f"🎲 [Exploração] Tudo testado na tela atual. Repetindo: {action_key}")
                        else:
                            max_q = max(self.q_table[current_state].values())
                            melhores_acoes = [k for k, v in self.q_table[current_state].items() if v == max_q]
                            
                            melhores_nao_clicados = [k for k in melhores_acoes if k not in tried_actions_in_state[current_state]]
                            if melhores_nao_clicados:
                                action_key = random.choice(melhores_nao_clicados)
                            else:
                                action_key = random.choice(melhores_acoes)
                                
                            self.write_log(f"🧠 [Conhecimento] Escolheu: {action_key} (Nota: {max_q:.1f})")

                    if action_key != "swipe_down":
                        tried_actions_in_state[current_state].add(action_key)

                    if action_key == "swipe_down":
                        scroll_count += 1
                        if scroll_count >= 3:
                            self.root_command("input keyevent 4")
                            time.sleep(1.0)
                            scroll_count = 0
                            continue
                    else:
                        scroll_count = 0 

                    self.click(action_key)
                    steps_count += 1

                    new_xml = self.get_screen_xml()
                    if not new_xml: new_xml = xml
                    
                    new_clickables = self.get_smart_clickables(new_xml)
                    new_state = self.get_state_hash(new_clickables)
                    
                    reward = -2.0 
                    is_outside_app = "com.android.vending" not in new_xml

                    if is_outside_app:
                        self.write_log("🚨 FATAL: Saiu da Play Store! (-500 pts).")
                        reward = -500.0
                        abortar_episodio = True
                    elif new_state == current_state and action_key != "swipe_down":
                        self.write_log(f"📉 Punição: O botão {action_key} não abriu tela nova (-50 pts)")
                        reward = -50.0
                    elif new_state in visited_states and action_key != "swipe_down":
                        self.write_log(f"⚠️ Punição: Voltou pra uma tela antiga (-30 pts)")
                        reward = -30.0
                        self.root_command("input keyevent 4") 
                        time.sleep(1.0)
                    else:
                        reward_given = False
                        if action_key in clickables_dict:
                            btn_text_desc = clickables_dict[action_key]["text"] + " " + clickables_dict[action_key]["desc"]
                            best_hint_reward = 0.0
                            for hint, val in self.hint_rewards.items():
                                if hint in btn_text_desc and val > best_hint_reward:
                                    best_hint_reward = val
                                    
                            if best_hint_reward > 0:
                                self.write_log(f"📈 Recompensa: Trilha Correta (+{best_hint_reward} pts) -> {btn_text_desc.strip()}")
                                reward = best_hint_reward
                                reward_given = True
                                
                        if not reward_given:
                            self.write_log("➡️ Avanço neutro.")

                    if current_state in self.q_table:
                        old_q_value = self.q_table[current_state].get(action_key, 0.0)
                        future_optimal_value = self.get_max_q_value(new_state) if not abortar_episodio else 0.0
                        
                        new_q_value = old_q_value + self.alpha * (reward + self.gamma * future_optimal_value - old_q_value)
                        self.q_table[current_state][action_key] = new_q_value
                        self.save_q_table()

                    if abortar_episodio:
                        break 
                
                if self.epsilon > self.min_epsilon:
                    self.epsilon -= 0.02
                else:
                    self.epsilon = self.min_epsilon
                    
                episode += 1

        except KeyboardInterrupt:
            print("\n\n🛑 Treinamento interrompido pelo usuário.")
        finally:
            self.toggle_visuals(False)

if __name__ == "__main__":
    ai = PlayStoreTrueAI()
    ai.IA_learning(max_steps_per_episode=15)
