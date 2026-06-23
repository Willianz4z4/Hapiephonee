import os
import time
import json
import subprocess
import random
import xml.etree.ElementTree as ET
import re

class PlayStoreRootAI:
    def __init__(self, device_id=""):
        self.device_cmd_prefix = f"-s {device_id} " if device_id else ""
        self.routes_history_file = "playstore_routes.json"
        self.memory = self.load_memory()

    def adb_root_command(self, cmd):
        full_cmd = f"adb {self.device_cmd_prefix}shell \"su -c '{cmd}'\""
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()

    def restart_playstore(self):
        """Mata o aplicativo e abre novamente do zero."""
        print("\n🔄 Reiniciando a Play Store (Limpando a tela)...")
        self.adb_root_command("am force-stop com.android.vending")
        time.sleep(1)
        self.adb_root_command("monkey -p com.android.vending -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1")
        time.sleep(4) # Aguarda carregar a página inicial

    def get_screen_xml(self):
        cmd = "uiautomator dump /data/local/tmp/dump.xml > /dev/null && cat /data/local/tmp/dump.xml"
        xml_content = self.adb_root_command(cmd)
        if not xml_content.startswith("<?xml"):
            return None
        return xml_content

    def parse_bounds(self, bounds_str):
        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            return (x1 + x2) // 2, (y1 + y2) // 2
        return None

    def find_node_by_text(self, xml_content, target_texts):
        try:
            root = ET.fromstring(xml_content)
        except:
            return None

        target_texts = [t.lower() for t in target_texts]
        for node in root.iter('node'):
            text = node.attrib.get('text', '').lower()
            content_desc = node.attrib.get('content-desc', '').lower()
            
            for target in target_texts:
                if target in text or target in content_desc:
                    return self.parse_bounds(node.attrib.get('bounds'))
        return None

    def get_all_clickable_nodes(self, xml_content):
        """Retorna uma lista de todas as coordenadas clicáveis na tela."""
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

    def click(self, x, y, delay=0.2):
        """Clica na coordenada e espera o mínimo possível (Background)."""
        print(f"👉 Clicando: ({x}, {y})")
        self.adb_root_command(f"input tap {x} {y} &") 
        time.sleep(delay)

    def load_memory(self):
        if os.path.exists(self.routes_history_file):
            with open(self.routes_history_file, "r") as f:
                return json.load(f)
        return {"best_route": {}, "all_successful_routes": []}

    def save_memory(self):
        with open(self.routes_history_file, "w") as f:
            json.dump(self.memory, f, indent=4)

    def IA_learning(self, time_limit_seconds=30, max_attempts=15, required_successes=3):
        """
        Modo de Aprendizado: Executa várias vezes até achar 'required_successes' rotas.
        Usa o modo Rapid Fire para tentar várias opções rápido se ficar perdida.
        """
        print(f"🧠 IA LEARNING INICIADO")
        print(f"Meta: Achar {required_successes} rotas válidas.")
        print(f"Limites: {max_attempts} tentativas | {time_limit_seconds}s por tentativa\n")
        
        ultimate_target = ["claim", "reivindicar", "resgatar"]
        path_hints = ["perfil", "conta", "profile", "account", "play points", "pontos do play", "perks", "benefícios", "vantagens"]

        success_count = 0

        for attempt in range(1, max_attempts + 1):
            print(f"========================================")
            print(f"🚀 TENTATIVA {attempt}/{max_attempts} | Sucessos até agora: {success_count}/{required_successes}")
            print(f"========================================")
            
            self.restart_playstore()
            start_time = time.time()
            current_route = []

            while (time.time() - start_time) < time_limit_seconds:
                time_taken = int(time.time() - start_time)
                tempo_restante = time_limit_seconds - time_taken
                print(f"⏱️ Restam: {tempo_restante}s...", end="\r")
                
                xml = self.get_screen_xml()
                if not xml:
                    time.sleep(1)
                    continue

                # 1. ACHOU O ALVO FINAL!
                coords_alvo = self.find_node_by_text(xml, ultimate_target)
                if coords_alvo:
                    print(f"\n🎯 ALVO FINAL ENCONTRADO! Coordenadas: {coords_alvo}")
                    self.click(coords_alvo[0], coords_alvo[1], delay=1.0) # Clique final mais lento
                    current_route.append({"action": "click_target", "coords": coords_alvo})
                    
                    time_taken = int(time.time() - start_time)
                    steps_taken = len(current_route)
                    
                    # CÁLCULO DA PONTUAÇÃO (Mais alto = Melhor)
                    pontuacao = 10000 - (steps_taken * 50) - (time_taken * 10)
                    
                    route_data = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "score": pontuacao,
                        "steps": steps_taken,
                        "time_taken_seconds": time_taken,
                        "route": current_route
                    }
                    
                    self.memory["all_successful_routes"].append(route_data)
                    print(f"🎉 SUCESSO! Rota finalizada com Pontuação: {pontuacao} (Passos: {steps_taken}, Tempo: {time_taken}s)")
                    
                    best_saved = self.memory.get("best_route", {})
                    if not best_saved or pontuacao > best_saved.get("score", 0):
                        print("🏆 NOVO RECORDE! Esta é a melhor rota até agora!")
                        self.memory["best_route"] = route_data
                    
                    self.save_memory()
                    success_count += 1
                    break

                # 2. Procurar pistas conhecidas
                coords_hint = self.find_node_by_text(xml, path_hints)
                if coords_hint:
                    print(f"\n💡 Pista encontrada! Clicando...")
                    self.click(coords_hint[0], coords_hint[1], delay=1.0) # Pista clica e espera
                    current_route.append({"action": "click_hint", "coords": coords_hint})
                    continue

                # 3. Exploração Aleatória (Modo Rapid Fire)
                print(f"\n👁️ Explorando rápido...")
                clickables = self.get_all_clickable_nodes(xml)
                
                if clickables:
                    quantidade_cliques = min(3, len(clickables))
                    alvos_rapidos = random.sample(clickables, quantidade_cliques)
                    
                    for random_coords in alvos_rapidos:
                        self.click(random_coords[0], random_coords[1], delay=0.1) # Delay quase zero
                        current_route.append({"action": "random_click", "coords": random_coords})
                else:
                    self.adb_root_command("input swipe 500 1500 500 500 &")
                    current_route.append({"action": "swipe_down"})
                    time.sleep(0.5)

            if success_count >= required_successes:
                print(f"\n✅ META ATINGIDA! A IA aprendeu {required_successes} rotas com sucesso.")
                break
                
            if (time.time() - start_time) >= time_limit_seconds:
                print(f"\n⌛ Tempo esgotado. A IA se perdeu nesta tentativa.")

        print("\n🏁 TREINAMENTO FINALIZADO.")
        if self.memory.get("best_route"):
            best = self.memory["best_route"]
            print(f"🏆 Melhor Pontuação: {best['score']} pontos (Passos: {best['steps']}, Tempo: {best['time_taken_seconds']}s)")
        else:
            print("❌ A IA não conseguiu encontrar nenhuma rota válida.")

if __name__ == "__main__":
    ai = PlayStoreRootAI()
    ai.IA_learning(time_limit_seconds=30, max_attempts=15, required_successes=3)
