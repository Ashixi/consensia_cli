Markdown
# AI Consensia CLI 🚀

Code Review right in your terminal. Consensia CLI analyzes your `git diff` using advanced AI models to catch bugs, security vulnerabilities, and performance bottlenecks *before* you commit your code.

## 📦 Installation

We provide a simple installation script for Linux, macOS, and Windows (via Git Bash / MSYS).

Run the following command in your terminal:

```bash
curl -sL [https://raw.githubusercontent.com/Ashixi/consensia_cli/main/install.sh](https://raw.githubusercontent.com/Ashixi/consensia_cli/main/install.sh) | bash
```
Note for Windows users: Make sure to run this in Git Bash. The script will install the executable to ~/bin. Ensure that ~/bin is added to your system's PATH.

🔑 Getting Started
Before you can analyze your code, you need to link the CLI to your Consensia account.

Go to the Consensia Web App and navigate to the CLI Access section.

Generate your personal CLI API Key.

Authenticate your terminal by running:

Bash
consensia auth <your_cli_api_key>
Your key is securely stored locally in ~/.consensia/config.json.

💻 Usage
Consensia CLI is designed to seamlessly integrate into your Git workflow.

Analyze staged or unstaged changes
By default, the CLI will try to analyze your currently staged changes. If nothing is staged, it will fall back to analyzing unstaged changes.

Bash
consensia analyze
Analyze specific commits or branches
You can pass any standard git diff target to the CLI:

Bash
consensia analyze HEAD~1
consensia analyze origin/main
Pipe diffs directly
You can also pipe the output of any command directly into the CLI:

Bash
git diff main...feature-branch | consensia analyze
⚡ Analysis Modes
You can control the depth and cost of the analysis by passing the --mode flag.

ECONOMY: Fast and cheap. Good for quick sanity checks (Default).

BALANCED: Deeper analysis with a wider context.

MAX_POWER: Maximum context window and comprehensive deep dive.

Bash
consensia analyze --mode BALANCED
🛡️ Output Overview
The CLI provides beautifully formatted terminal output using rich, which includes:

🚨 CRITICAL ISSUES (BLOCKERS): Severe bugs or security flaws that must be fixed.

💡 IMPROVEMENTS & SUGGESTIONS: Clean code and performance tips.

📋 VERDICT: The AI judge's final summary on whether the code is safe to ship.

📄 License
This project is licensed under the MIT License.
