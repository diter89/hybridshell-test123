# HybridShell

HybridShell is an interactive shell wrapper that blends a regular terminal workflow with light AI assistance. It can:

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

## Binary Download (x86_64)

1. Download `hybridshell-test123.zip` from the release page: [v0.0.0.2](https://github.com/diter89/hybridshell-test123/releases/tag/0.0.0.2).
2. Extract the archive:
   ```bash
   unzip hybridshell-test123.zip
   ```
3. Make sure the binary is executable (usually already is):
   ```bash
   chmod +x hybridshell-x86_64
   ```
4. Export your Fireworks API key:
   ```bash
   export FIREWORKS_API_KEY="your-key"
   ```
5. Run HybridShell:
   ```bash
   ./hybridshell-x86_64
   ```

The first launch creates `~/.wrapcli_awokwokw/config.ini`; tweak that file to customize prompts, styles, and command behavior without rebuilding the binary.

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

<img width="1080" height="2400" alt="Screenshot_20251016-171008_Termux" src="https://github.com/user-attachments/assets/f4f0c479-273b-4a1f-ba50-ea409c001810" />

