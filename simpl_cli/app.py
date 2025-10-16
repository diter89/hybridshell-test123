#!/usr/bin/env python3
from __future__ import annotations
import sys
from prompt_toolkit import prompt
from rich.console import Console

from .config import Config
from .core import HybridShell


def check_dependencies() -> None:
    try:
        import rich  # noqa: F401
        import prompt_toolkit  # noqa: F401
        import requests  # noqa: F401
        import psutil  # noqa: F401
    except ImportError as error:  # noqa: BLE001
        print(f" Required dependency not found: {error}")
        print("Please install required packages:")
        print("pip install rich prompt-toolkit requests psutil")

        try:
            import tomli  # noqa: F401
        except ImportError:
            print("Optional: pip install tomli (for Poetry project detection)")

        sys.exit(1)


def get_api_key() -> str:
    api_key = Config.get_api_key()

    if not api_key:
        console = Console()
        console.print(" [yellow]API Key not found in environment variables.[/yellow]")
        console.print("Set FIREWORKS_API_KEY environment variable or enter it now:")
        api_key = prompt("Fireworks API Key: ", is_password=True).strip()

        if not api_key:
            console.print(" [red]API Key required to run the hybrid shell[/red]")
            sys.exit(1)

    return api_key


def main() -> None:
    check_dependencies()
    Config.ensure_directories()

    api_key = get_api_key()

    shell = HybridShell(api_key)
    shell.run()


if __name__ == "__main__":
    main()
