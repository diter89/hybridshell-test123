❯ cat README.md
# HybridShell

HybridShell is an interactive terminal that blends a regular shell workflow with light AI assistance. It can:

- **Switch modes instantly** – jump between raw shell commands and AI chat.
- **Plan simple tasks** – ask the helper to list, inspect, or run small shell steps in order.
- **Render nicer output** – rely on `rich` and `prompt_toolkit` for streaming results, completions, and status panels.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Export your Fireworks API key:
   ```bash
   export FIREWORKS_API_KEY="your-key"
   ```
3. Launch the shell:
   ```bash
   python3 -m simpl_cli.cli
   ```

## Key Bindings

| Shortcut | Action                |
|----------|-----------------------|
| `Ctrl+A` | Switch to AI mode     |
| `Ctrl+S` | Switch to Shell mode  |
| `Alt+H`  | Toggle help panel     |
| `Alt+C`  | Clear context/history |
| `Ctrl+C` | Exit HybridShell      |

## Project Structure

- `simpl_cli/app.py` – entrypoint that validates dependencies and starts the shell.
- `simpl_cli/core/` – hybrid engine, router, and AI integration.
- `simpl_cli/persona/` – persona implementations (planner, search, general chat).
- `simpl_cli/ui/` – Rich/prompt_toolkit UI components.

## License

Distributed as-is under the project’s repository terms.

<img width="1366" height="768" alt="Screenshot from 2025-10-16 18-01-55" src="https://github.com/user-attachments/assets/803f9eb5-a8d4-42c2-ae49-6a90bf66822f" />
