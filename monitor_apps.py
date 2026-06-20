import os
import sys
import subprocess
import time

try:
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
except ImportError:
    os.system("pip install rich -q > /dev/null 2>&1")
    from rich.console import Console
    from rich.panel import Panel
    console = Console()

def get_user_apps():
    """Retorna um SET com os nomes dos pacotes instalados APENAS pelo usuário"""
    try:
        # O parâmetro -3 garante que os nativos (como teclado) não apareçam
        out = subprocess.check_output("su -c 'pm list packages -3'", shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
        return set([line.replace("package:", "").strip() for line in out.split("\n") if line.strip()])
    except:
        return set()

def start_monitor():
    os.system("clear" if os.name == "posix" else "cls")
    console.print(Panel.fit("[bold cyan]Hapiephone Monitor[/bold cyan]\n[dim]Rastreador de Aplicativos (Apenas Downloads)[/dim]", border_style="cyan"))
    
    console.print("[yellow]🔍 Mapeando aplicativos instalados...[/yellow]")
    current_apps = get_user_apps()
    
    console.print(f"[bold green]✅ Monitoramento iniciado! Total de apps encontrados: {len(current_apps)}[/bold green]")
    console.print("[dim]Aguardando instalacoes ou desinstalacoes no celular... (Pressione CTRL+C para sair)[/dim]\n")

    while True:
        try:
            time.sleep(2) # Verifica a cada 2 segundos de forma leve
            new_apps = get_user_apps()
            
            # Se a lista atual for diferente da lista anterior, alguém instalou ou apagou algo!
            if new_apps != current_apps:
                added = new_apps - current_apps
                removed = current_apps - new_apps
                
                # Alerta o que foi instalado
                if added:
                    for app in added:
                        console.print(Panel(f"[bold green]📥 Novo Aplicativo Instalado:[/bold green] {app}", style="green"))
                
                # Alerta o que foi removido
                if removed:
                    for app in removed:
                        console.print(Panel(f"[bold red]🗑️ Aplicativo Desinstalado:[/bold red] {app}", style="red"))
                
                # Imprime a lista completa atualizada
                console.print(f"\n[bold cyan]📦 Lista Atualizada de Aplicativos Baixados ({len(new_apps)} no total):[/bold cyan]")
                for idx, app in enumerate(sorted(new_apps), 1):
                    console.print(f"  [dim]{idx}.[/dim] [cyan]{app}[/cyan]")
                console.print("-" * 45 + "\n")
                
                # Atualiza a lista base para a próxima verificação
                current_apps = new_apps
                
        except KeyboardInterrupt:
            console.print("\n[bold red]🛑 Monitoramento encerrado pelo usuário.[/bold red]")
            break
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    start_monitor()
