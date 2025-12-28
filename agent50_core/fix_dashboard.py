import os

# Ye code dashboard.py mein zabardasti likha jayega
code = r'''import time
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

class ConsoleUI:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()

    def welcome_screen(self):
        self.console.clear()
        header = Panel(Align.center(Text("AGENT 50 SUPREME", style="bold white on blue", justify="center")), style="blue", padding=(0, 1))
        self.console.print(header)
        
        status_text = "\n[bold green]● SYSTEM ONLINE[/bold green]\n[dim]Architecture Engine: READY\nBuilder Module: READY\nDeployer: STANDBY[/dim]\n"
        self.console.print(Panel(Align.center(status_text), title="[bold]Autonomous Architect[/bold]", border_style="white", padding=(1, 2)))
        time.sleep(1)

    def get_user_input(self, prompt_text):
        self.console.print(f"\n[bold cyan]?[/bold cyan] [bold white]{prompt_text}[/bold white]")
        return self.console.input("[dim]>>> [/dim]")

    def log(self, message, style="white"):
        self.console.print(f"[{style}]> {message}[/{style}]")

    def show_progress(self, step_name):
        with self.console.status(f"[bold green]Working on: {step_name}...[/bold green]", spinner="dots"):
            time.sleep(0.5)
            self.console.print(f"✅ [bold green]{step_name} Complete.[/bold green]")
'''

# File write karna (Overwrite)
path = os.path.join("agent50_core", "console", "dashboard.py")
with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print(f"✅ SUCCESSFULLY FIXED: {path}")
print("Ab aap main.py chala sakte hain!")