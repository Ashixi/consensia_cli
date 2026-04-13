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

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green"
})
console = Console(theme=custom_theme)

CONFIG_DIR = os.path.expanduser("~/.consensia")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_API_URL = "https://api.consensia.world/cli/analyze-diff" 

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

def analyze(mode, target="", output_format="human"):
    config = load_config()
    if not config or "cli_api_key" not in config:
        if output_format == "json":
            print(json.dumps({"error": "CLI key not found"}))
        else:
            console.print("[danger]❌ Error: CLI key not found. Please run: consensia auth <your_key>[/danger]")
        sys.exit(1)

    if not sys.stdin.isatty():
        diff = sys.stdin.read().strip()
    else:
        diff = get_git_diff(target)

    if not diff:
        if output_format == "json":
            print(json.dumps({"error": "No changes detected"}))
        else:
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
        if output_format == "json":
            response = requests.post(DEFAULT_API_URL, json=payload, headers=headers)
        else:
            with console.status(f"[bold cyan]🔍 Analyzing diff ({len(diff)} chars) in {mode} mode...[/bold cyan]", spinner="dots"):
                response = requests.post(DEFAULT_API_URL, json=payload, headers=headers)
        
        response.raise_for_status()
        data = response.json()
        
        if output_format == "json":
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return

        verdict = data.get("verdict", {})
        console.print("\n")
        
        inline_comments = verdict.get('inline_comments', [])
        
        critical = [c for c in inline_comments if c.get('type') == 'CRITICAL']
        if critical:
            crit_text = "\n".join([f"• **{c.get('path')}** (Line {c.get('line', '?')}): {c.get('body')}" for c in critical])
            console.print(Panel(crit_text, title="🚨 CRITICAL ISSUES (BLOCKERS)", border_style="red", expand=False))
        else:
            console.print(Panel("✅ No critical issues found. Ready to ship!", border_style="green", expand=False))
            
        improvements = [c for c in inline_comments if c.get('type') != 'CRITICAL']
        if improvements:
            imp_text = "\n".join([f"• **{c.get('path')}** (Line {c.get('line', '?')}): {c.get('body')}" for c in improvements])
            console.print(Panel(imp_text, title="💡 IMPROVEMENTS & SUGGESTIONS", border_style="blue", expand=False))
                
        summary_md = Markdown(verdict.get('summary', ''))
        console.print(Panel(summary_md, title=f"📋 VERDICT: {verdict.get('title', 'Review')}", border_style="cyan"))
        console.print(f"[info]🪙 Tokens used: {data.get('tokens_used', 0)} ({data.get('billing_mode', 'unknown')})[/info]\n")
        
    except requests.exceptions.RequestException as e:
        if output_format == "json":
            print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[danger]❌ API Error:[/danger] {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AI Consensia CLI - Code Review right in your terminal")
    subparsers = parser.add_subparsers(dest="command")

    auth_parser = subparsers.add_parser("auth", help="Save your CLI API key")
    auth_parser.add_argument("key", type=str, help="Your CLI API key from the web interface")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze git diff")
    analyze_parser.add_argument("--mode", type=str, choices=["ECONOMY", "BALANCED", "MAX_POWER"], default="BALANCED", help="Power mode")
    analyze_parser.add_argument("--format", type=str, choices=["human", "json"], default="human", help="Output format (human or json)")
    analyze_parser.add_argument("target", nargs="?", default="", help="Branch or commit to diff against")

    args = parser.parse_args()

    if args.command == "auth":
        save_config(args.key)
    elif args.command == "analyze":
        analyze(args.mode, args.target, args.format)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()