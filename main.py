import os
import sys
import json
import subprocess
import argparse
import requests
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme

# Налаштування красивого виводу
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green"
})
console = Console(theme=custom_theme)

# Configuration
CONFIG_DIR = os.path.expanduser("~/.consensia")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_API_URL = "http://localhost:8050/cli/analyze-diff" 

def save_config(api_key):
    os.makedirs(CONFIG_DIR, exist_user=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({"cli_api_key": api_key}, f)
    console.print("✅ [success]API key saved successfully![/success]")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_git_diff(target=""):
    try:
        if target:
            result = subprocess.run(["git", "diff", target], capture_output=True, text=True, check=True)
            return result.stdout.strip()
            
        result = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True, check=True)
        if not result.stdout.strip():
            result = subprocess.run(["git", "diff"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        console.print(f"[danger]❌ Error: Failed to execute git diff. {e.stderr}[/danger]")
        sys.exit(1)
    except FileNotFoundError:
        console.print("[danger]❌ Error: git is not installed or not found in PATH.[/danger]")
        sys.exit(1)

def analyze(mode, target=""):
    config = load_config()
    if not config or "cli_api_key" not in config:
        console.print("[danger]❌ Error: CLI key not found. Please run: consensia auth <your_key>[/danger]")
        sys.exit(1)

    if not sys.stdin.isatty():
        diff = sys.stdin.read().strip()
    else:
        diff = get_git_diff(target)

    if not diff:
        console.print("[warning]⚠️ No changes detected for analysis (diff is empty).[/warning]")
        return

    headers = {
        "x-api-key": config["cli_api_key"],
        "Content-Type": "application/json"
    }
    payload = {
        "diff_text": diff,
        "mode": mode
    }

    try:
        # Spinner під час очікування відповіді
        with console.status(f"[bold cyan]🔍 Analyzing diff ({len(diff)} chars) in {mode} mode...[/bold cyan]", spinner="dots"):
            response = requests.post(DEFAULT_API_URL, json=payload, headers=headers)
        
        if response.status_code == 401:
            console.print("[danger]❌ Authorization Error: Invalid CLI key.[/danger]")
            sys.exit(1)
        elif response.status_code == 402:
            detail = response.json().get('detail', 'Insufficient credits. Please top up your balance.')
            console.print(f"[danger]💸 Billing Error:[/danger] {detail}")
            sys.exit(1)
            
        response.raise_for_status()
        data = response.json()
        
        verdict = data.get("verdict", {})
        
        # UI оформлення
        console.print("\n")
        
        # Блок критичних помилок
        critical = verdict.get('critical_fixes', [])
        if critical:
            crit_text = "\n".join([f"• {item}" for item in critical])
            console.print(Panel(crit_text, title="🚨 CRITICAL ISSUES (BLOCKERS)", border_style="red", expand=False))
        else:
            console.print(Panel("✅ No critical issues found. Ready to ship!", border_style="green", expand=False))
            
        # Блок покращень
        improvements = verdict.get('improvements', [])
        if improvements:
            imp_text = "\n".join([f"• {item}" for item in improvements])
            console.print(Panel(imp_text, title="💡 IMPROVEMENTS & SUGGESTIONS", border_style="blue", expand=False))
                
        # Фінальне резюме
        summary_md = Markdown(verdict.get('summary', ''))
        console.print(Panel(summary_md, title=f"📋 VERDICT: {verdict.get('title', 'Review')}", border_style="cyan"))
        
        console.print(f"[info]🪙 Tokens used: {data.get('tokens_used', 0)} ({data.get('billing_mode', 'unknown')})[/info]\n")
        
    except requests.exceptions.RequestException as e:
        console.print(f"[danger]❌ Server connection error:[/danger] {e}")
        
        # БЕЗПЕЧНА ПЕРЕВІРКА RESPONSE
        if 'response' in locals() and response is not None:
            try:
                error_details = response.json().get('detail')
                if error_details:
                    console.print(f"[warning]Details:[/warning] {error_details}")
            except (ValueError, AttributeError):
                console.print("[warning]Details: Failed to parse server error response (Server might be down or returning HTML).[/warning]")
        else:
            console.print("[warning]Details: No response received from the server. Check your internet connection.[/warning]")
            
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AI Consensia CLI - Code Review right in your terminal")
    subparsers = parser.add_subparsers(dest="command")

    auth_parser = subparsers.add_parser("auth", help="Save your CLI API key")
    auth_parser.add_argument("key", type=str, help="Your CLI API key from the web interface")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze git diff")
    analyze_parser.add_argument("--mode", type=str, choices=["ECONOMY", "BALANCED", "MAX_POWER"], default="ECONOMY", help="Power mode (default: ECONOMY)")
    analyze_parser.add_argument("target", nargs="?", default="", help="Branch or commit to diff against (e.g. HEAD~1 or origin/main)")

    args = parser.parse_args()

    if args.command == "auth":
        save_config(args.key)
    elif args.command == "analyze":
        analyze(args.mode, args.target)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()