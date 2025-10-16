#!/usr/bin/env python3
from __future__ import annotations
import os
from datetime import datetime
from typing import List

from prompt_toolkit.application import get_app
from prompt_toolkit.formatted_text import (
    FormattedText,
    HTML,
    fragment_list_width,
    merge_formatted_text,
    to_formatted_text,
)
from prompt_toolkit.styles import Style
from rich.align import Align
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.status import Status
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from ..config import Config
from ..environment import (
    get_all_env_info,
    get_prompt_env_indicators,
)
from .theme import PanelTheme


class UIManager:
    def __init__(self, console: Console) -> None:
        self.console = console
        self._pending_footer = None

    def get_prompt_text(self, mode: str) -> FormattedText:
        os_icon = "" if os.name != "nt" else ""
        folder_icon = ""

        path_display = self._format_path_for_prompt(os.getcwd())

        env_segments = []
        if mode == "ai":
            env_segments.append("<mode_ai>AI</mode_ai>")
        for style_name, text in get_prompt_env_indicators():
            tag = style_name.split(":", 1)[1] if style_name.startswith("class:") else style_name
            env_segments.append(f"<{tag}>{text}</{tag}>")

        env_html_str = " ".join(env_segments)
        env_html_str = f" {env_html_str}" if env_html_str else ""

        top_left_str = (
            "<prompt_border>╭─</prompt_border> "
            f"<prompt_os>{os_icon}</prompt_os> "
            f"<prompt_folder>{folder_icon}</prompt_folder> "
            f"<path>{path_display}</path>"
        )

        top_left_html = HTML(top_left_str)
        top_left_ft = to_formatted_text(top_left_html)

        env_html = HTML(env_html_str) if env_html_str else None
        env_ft = to_formatted_text(env_html) if env_html else []

        try:
            total_width = get_app().output.get_size().columns
        except Exception:
            total_width = 100

        used_width = fragment_list_width(top_left_ft) + (fragment_list_width(env_ft) if env_html else 0)
        padding_calc = total_width - used_width
        if env_html:
            padding_width = padding_calc if padding_calc > 0 else 1 if padding_calc == 0 else 0
        else:
            padding_width = padding_calc if padding_calc > 0 else 0
        padding_html = HTML(f"<prompt_padding>{'─' * padding_width}</prompt_padding>")

        prompt_symbol = HTML("<prompt_symbol>❯</prompt_symbol> ")
        bottom_html = HTML("<prompt_border>╰─</prompt_border>")

        parts = [top_left_html, padding_html]
        if env_html:
            parts.append(env_html)
        parts.extend(["\n", bottom_html, prompt_symbol])

        return merge_formatted_text(parts)

    def get_style(self) -> Style:
        environment_styles = {
            "env_python": "#99d1db bold",
            "env_git": "#ef9f76 bold",
            "env_node": "#cba6f7 bold",
            "env_docker": "#81c8be bold",
            "env_system": "#e5c890 bold",
        }

        combined_styles = {
            **Config.PROMPT_STYLES,
            **Config.COMPLETION_STYLES,
            **environment_styles,
        }
        return Style.from_dict(combined_styles)

    def display_memory_status(self, stats: dict) -> None:
        status_table = Table(show_header=False, box=None, padding=(0, 1))
        status_table.add_row("Configured", "Yes" if stats.get("configured") else "No")
        status_table.add_row("Enabled", "Yes" if stats.get("enabled") else "No")
        status_table.add_row("Available", "Yes" if stats.get("available") else "No")
        status_table.add_row("Stored Items", str(stats.get("count", 0)))
        status_table.add_row("Top K", str(stats.get("top_k", 0)))
        status_table.add_row("Max Items", str(stats.get("max_items", 0)))
        status_table.add_row("Storage Path", stats.get("path", "-"))
        if stats.get("error"):
            status_table.add_row("Error", stats.get("error"))

        self.console.print(
            Panel.fit(status_table, title=" Memory Status", border_style="blue")
        )
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def display_memory_cleared(self, success: bool) -> None:
        if success:
            self.console.print(
                Panel(
                    "[green]Memory storage cleared.[/green]\n[dim]Percakapan dan konteks shell telah direset.[/dim]",
                    title="Memory",
                    border_style="green",
                )
            )
        else:
            self.console.print(
                Panel(
                    "[red]Failed to clear memory storage.[/red]",
                    title="Memory",
                    border_style="red",
                )
            )
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def display_memory_toggle(self, enabled: bool) -> None:
        if enabled:
            self.console.print("[green]Memory recording enabled.[/green]")
        else:
            self.console.print("[yellow]Memory recording disabled.[/yellow]")
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def display_memory_topk(self, value: int) -> None:
        self.console.print(f"[cyan]Memory retrieval top-k set to {value}.[/cyan]")
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def display_memory_error(self, message: str) -> None:
        self.console.print(f"[red]Memory: {message}[/red]")
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def display_router_diagnostics(self, lines: List[str]) -> None:
        if not lines:
            return

        for line in lines:
            self.console.print(line)
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def display_persona_renderable(self, renderable) -> None:
        if renderable is None:
            return
        self.console.print(renderable)
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def display_search_results(self, payload: dict) -> None:
        status = payload.get("status", "success")
        if status != "success":
            message = payload.get("message", "Unknown error")
            self.console.print(
                Panel(
                    f"[red]Search failed:[/red] {message}",
                    title="Search Service",
                    border_style="red",
                )
            )
            return

        results = payload.get("organic_results", [])
        if not results:
            self.console.print(
                Panel(
                    "No search results found.",
                    title="Search Service",
                    border_style="blue",
                )
            )
            return

        tree = Tree("[bold blue]Search Results[/bold blue]")
        for item in results[:8]:
            title = item.get("title", "Untitled")
            domain = item.get("domain", "")
            label = f"[bold]{title}[/bold]"
            if domain:
                label += f" [dim]({domain})[/dim]"

            node = tree.add(label)

            date = item.get("date")
            if date:
                node.add(f"[green]Date:[/green] {date}")

            snippet = item.get("snippet")
            if snippet:
                node.add(f"[white]{snippet}[/white]")

            link = item.get("link")
            if link:
                node.add(f"[cyan]{link}[/cyan]")

        debug = payload.get("debug", {})
        latency = payload.get("searchParameters", {}).get("latency_ms")
        if latency is not None:
            tree.add(f"[dim]Latency: {latency} ms[/dim]")
        if debug.get("result_count") is not None:
            tree.add(f"[dim]Results: {debug.get('result_count')}[/dim]")

        self.console.print(tree)
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def _format_path_for_prompt(self, path: str) -> str:
        try:
            current_path = os.path.abspath(path)
        except OSError:
            return path

        home_dir = os.path.expanduser("~")

        if current_path == home_dir:
            return "~"

        if current_path.startswith(home_dir):
            relative = current_path[len(home_dir) + 1 :]
            if not relative:
                return "~"

            parts = relative.split(os.sep)
            if len(parts) == 1:
                return f"~/{parts[0]}"

            return f"../../{parts[-1]}"

        return current_path

    def show_welcome(self) -> None:
        env_info = get_all_env_info()

        welcome_parts: List[str] = [Config.WELCOME_MESSAGE]

        env_summary: List[str] = []
        if env_info.get("python"):
            py_env = env_info["python"]
            env_summary.append(
                f"󰌠 Python: {py_env['display']} (v{py_env['python_version']})"
            )

        if env_info.get("git"):
            git_info = env_info["git"]
            status_indicator = "" if git_info.get("has_changes") else ""
            env_summary.append(f" Git: {git_info['branch']} {status_indicator}")

        if env_info.get("node"):
            node_info = env_info["node"]
            env_summary.append(
                f"󰎙 Node: {node_info['name']} (v{node_info['version']})"
            )

        if env_info.get("docker"):
            docker_info = env_info["docker"]
            env_summary.append(f"󰡨 Docker: {docker_info['display']}")

        if env_summary:
            welcome_parts.append("\n\n Detected Environments:")
            welcome_parts.extend([f"  {item}" for item in env_summary])

        welcome_panel = PanelTheme.build("\n".join(welcome_parts), style="info", fit=True)
        self.console.print(welcome_panel)
        self.console.print()
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def show_help(self) -> None:
        keybindings_lines = ["[bold]Keybindings[/bold]"]
        for keybind, description in Config.HELP_KEYBINDS:
            keybindings_lines.append(f"  • [cyan]{keybind}[/cyan] – {description}")
        keybindings_lines.append("  • [cyan]Alt+Z[/cyan] – Resume cancelled AI stream")

        commands_lines = ["\n[bold]Special Commands[/bold]"]
        for command, mode, description in Config.HELP_SPECIAL_COMMANDS:
            commands_lines.append(
                f"  • [cyan]{command}[/cyan] ({mode}) – {description}"
            )
        commands_lines.extend(
            [
                "  • [cyan]memory status[/cyan] (Shell) – Show memory statistics",
                "  • [cyan]memory enable[/cyan] (Shell) – Enable memory recording",
                "  • [cyan]memory disable[/cyan] (Shell) – Disable memory recording",
                "  • [cyan]memory topk <n>[/cyan] (Shell) – Set retrieval top-k",
                "  • [cyan]resume[/cyan] (AI) – Resume cancelled AI response",
                "  • [cyan]cancelstate[/cyan] (AI) – Show cancelled stream details",
            ]
        )

        env_lines = ["\n[bold]Environment Commands[/bold]"]
        env_lines.extend(
            [
                "  • [cyan]!env[/cyan] – Show current environment status",
                "  • [cyan]!status[/cyan] – Show detailed system and environment info",
                "  • [cyan]!git[/cyan] – Show git repository information",
                "  • [cyan]!python[/cyan] – Show Python environment details",
            ]
        )

        help_text = "\n".join(keybindings_lines + commands_lines + env_lines)

        self.console.print()
        self.console.print(PanelTheme.build(help_text, title="Help", style="info", fit=True))
        self.console.print()
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def show_mode_switch(self, mode_name: str) -> None:  # noqa: D401
        """Tampilkan perubahan mode (dikosongkan untuk menghindari clutter)."""

        return

    def show_context_cleared(self) -> None:
        self.console.print(
            PanelTheme.build(
                " Context and conversation cleared!",
                title="Cleared",
                style="success",
            )
        )
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def show_conversation_cleared(self) -> None:
        self.console.print(
            PanelTheme.build(
                " Conversation history cleared",
                title="Cleared",
                style="success",
            )
        )
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def show_context_table(self, shell_context: list) -> None:
        if not shell_context:
            self.console.print(
                PanelTheme.build(
                    "[yellow]No shell context available[/yellow]",
                    title="Shell Context",
                    style="warning",
                )
            )
            return

        context_table = Table(
            title="Shell Context", show_header=True, header_style="bold cyan"
        )
        context_table.add_column("Time", style="dim", no_wrap=True)
        context_table.add_column("Command", style="cyan")
        context_table.add_column("Directory", style="yellow", no_wrap=True)
        context_table.add_column("Output Preview", style="white")

        for entry in shell_context[-Config.CONTEXT_FOR_AI :]:
            output_preview = (
                entry["output"][:50] + "..."
                if len(entry["output"]) > 50
                else entry["output"]
            )
            output_preview = output_preview.replace("\n", " ")

            context_table.add_row(
                entry["timestamp"],
                entry["command"],
                entry["cwd"].split("/")[-1],
                output_preview,
            )

        self.console.print(PanelTheme.build(context_table, title="Shell Context", style="info"))

    def display_shell_output(self, command: str, result) -> None:
        base_cmd = command.strip().split()[0]
        if self._should_use_ls_table(command, base_cmd):
            self._display_ls_table(command, result)
            if self._pending_footer:
                self.console.print(f"[dim]{self._pending_footer}[/dim]")
                self._pending_footer = None
            return

        output = result.stdout + result.stderr

        if result.stdout and result.stderr:
            combined_output = Text()
            if result.stdout:
                combined_output.append(result.stdout, style="white")
            if result.stderr:
                combined_output.append(result.stderr, style="red")

            self.console.print(
                PanelTheme.build(
                    combined_output,
                    title=f" Shell: {command}",
                    style="default",
                    fit=True,
                )
            )
        elif result.stdout:
            syntax_content = self._try_syntax_highlighting(command, result.stdout)
            self.console.print(
                PanelTheme.build(
                    syntax_content,
                    title=f" Shell: {command}",
                    style="default",
                    fit=True,
                )
            )
        elif result.stderr:
            self.console.print(
                PanelTheme.build(
                    f"[red]{result.stderr}[/red]",
                    title=f" Shell: {command}",
                    style="error",
                    fit=True,
                )
            )
        else:
            self.console.print(
                PanelTheme.build(
                    "[dim]No output[/dim]",
                    title=f" Shell: {command}",
                    style="default",
                    fit=True,
                )
            )

        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def _should_use_ls_table(self, command: str, base_cmd: str) -> bool:
        if base_cmd in Config.LS_COMMANDS:
            return True

        if base_cmd == "ls" or command.startswith("ls "):
            return True

        return False

    def _display_ls_table(self, command: str, result) -> None:
        if result.returncode != 0:
            self.console.print(
                PanelTheme.build(
                    f"[red]{result.stderr}[/red]",
                    title=f" Shell: {command}",
                    style="error",
                )
            )
            return

        if not result.stdout.strip():
            self.console.print(
                PanelTheme.build(
                    "[yellow]Directory is empty[/yellow]",
                    title=f" Directory Listing: {command}",
                    style="warning",
                )
            )
            return

        try:
            ls_table = self._create_ls_table(command, result.stdout)
            self.console.print(
                PanelTheme.build(
                    ls_table,
                    title=f" Directory Listing: {command}",
                    style="info",
                    fit=True,
                    padding=(1, 2),
                )
            )
        except Exception:  # noqa: BLE001
            self.console.print(
                PanelTheme.build(
                    result.stdout,
                    title=f" Shell: {command}",
                    style="default",
                )
            )

    def _create_ls_table(self, command: str, ls_output: str) -> Table:
        table = Table(show_header=True, header_style="bold cyan", box=None)

        lines = ls_output.strip().split("\n")
        has_details = self._is_detailed_listing(lines, command)

        if has_details:
            table.add_column("Permissions", style="dim")
            table.add_column("Links", style="dim", justify="right")
            table.add_column("Owner", style="dim")
            table.add_column("Group", style="dim")
            table.add_column("Size", style="cyan", justify="right")
            table.add_column("Date", style="yellow")
            table.add_column("Name", style="bold")
        else:
            table.add_column("Type", justify="center", width=4)
            table.add_column("Name", style="bold")
            table.add_column("Size", style="cyan", justify="right")
            table.add_column("Modified", style="yellow")

        target_dir = self._extract_target_directory(command)
        for line in lines:
            line = line.strip()
            if not line or line.startswith("total "):
                continue

            try:
                if has_details:
                    self._add_detailed_row(table, line, target_dir)
                else:
                    self._add_simple_row(table, line, target_dir)
            except Exception:  # noqa: BLE001
                continue

        return table

    def _is_detailed_listing(self, lines: list, command: str) -> bool:
        if "-l" in command:
            return True

        detailed_patterns = 0
        for line in lines[:5]:
            line = line.strip()
            if not line or line.startswith("total"):
                continue

            parts = line.split()
            if len(parts) >= 8:
                first_part = parts[0]
                if (
                    len(first_part) == 10
                    and first_part[0] in "-dlbcsp"
                    and all(c in "rwx-" for c in first_part[1:])
                ):
                    detailed_patterns += 1

        non_empty_lines = len([l for l in lines if l.strip() and not l.startswith("total")])
        return detailed_patterns > 0 and (
            detailed_patterns / max(non_empty_lines, 1)
        ) > 0.5

    def _extract_target_directory(self, command: str) -> str:
        parts = command.split()
        for part in parts[1:]:
            if not part.startswith("-"):
                if os.path.isabs(part):
                    return part
                return os.path.join(os.getcwd(), part)

        return os.getcwd()

    def _add_detailed_row(self, table: Table, line: str, current_dir: str) -> None:
        parts = line.split()
        if len(parts) < 8:
            return

        permissions = parts[0]
        links = parts[1]
        owner = parts[2]
        group = parts[3]
        size = parts[4]

        if len(parts) >= 9:
            date_parts = parts[5:8]
            name = " ".join(parts[8:])
        else:
            date_parts = parts[5:7]
            name = " ".join(parts[7:])

        date_str = " ".join(date_parts)

        _, icon, color = self._get_file_info(name, current_dir, permissions)

        formatted_size = self._format_size(size) if size.isdigit() else size

        table.add_row(
            f"[dim]{permissions}[/dim]",
            f"[dim]{links}[/dim]",
            f"[dim]{owner}[/dim]",
            f"[dim]{group}[/dim]",
            f"[cyan]{formatted_size}[/cyan]",
            f"[yellow]{date_str}[/yellow]",
            f"[{color}]{icon} {name}[/{color}]",
        )

    def _add_simple_row(self, table: Table, filename: str, current_dir: str) -> None:
        file_path = os.path.join(current_dir, filename)
        _, icon, color = self._get_file_info(filename, current_dir)

        size = "-"
        mtime = "?"

        try:
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                if not os.path.isdir(file_path):
                    size = self._format_size(stat_info.st_size)
                else:
                    size = "-"
                mtime = datetime.fromtimestamp(stat_info.st_mtime).strftime("%b %d %H:%M")
        except (OSError, PermissionError, FileNotFoundError):
            size = "?"
            mtime = "?"

        table.add_row(
            f"[{color}]{icon}[/{color}]",
            f"[{color}]{filename}[/{color}]",
            f"[cyan]{size}[/cyan]",
            f"[yellow]{mtime}[/yellow]",
        )

    def _get_file_info(self, filename: str, current_dir: str, permissions: str | None = None):
        file_path = os.path.join(current_dir, filename)

        is_hidden = filename.startswith('.')

        try:
            if permissions:
                if permissions.startswith('d'):
                    file_type = 'directory'
                elif permissions.startswith('l'):
                    file_type = 'symlink'
                elif 'x' in permissions:
                    file_type = 'executable'
                else:
                    file_type = self._get_file_type_by_extension(filename)
            elif os.path.exists(file_path):
                if os.path.isdir(file_path):
                    file_type = 'directory'
                elif os.path.islink(file_path):
                    file_type = 'symlink'
                elif os.access(file_path, os.X_OK) and not os.path.isdir(file_path):
                    file_type = 'executable'
                else:
                    file_type = self._get_file_type_by_extension(filename)
            else:
                alt_path = os.path.join(os.getcwd(), filename)
                if current_dir != os.getcwd() and os.path.exists(alt_path):
                    if os.path.isdir(alt_path):
                        file_type = 'directory'
                    elif os.path.islink(alt_path):
                        file_type = 'symlink'
                    elif os.access(alt_path, os.X_OK):
                        file_type = 'executable'
                    else:
                        file_type = self._get_file_type_by_extension(filename)
                else:
                    file_type = self._get_file_type_by_extension(filename)
        except (OSError, PermissionError):
            file_type = self._get_file_type_by_extension(filename)

        icon = Config.FILE_ICONS.get(file_type, Config.FILE_ICONS['file'])
        color_key = 'hidden' if is_hidden else file_type
        color = Config.FILE_COLORS.get(color_key, Config.FILE_COLORS['file'])
        return file_type, icon, color

    def _get_file_type_by_extension(self, filename: str) -> str:
        if not filename or (filename.startswith('.') and '.' not in filename[1:]):
            return 'file'

        ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        return Config.FILE_EXTENSIONS.get(ext, 'file')

    def _format_size(self, size_bytes) -> str:
        try:
            size_bytes = int(size_bytes)
        except (ValueError, TypeError):
            return str(size_bytes)

        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        if i == 0:
            return f"{size_bytes} {size_names[i]}"
        return f"{size_bytes:.1f} {size_names[i]}"

    def _try_syntax_highlighting(self, command: str, output: str):
        base_cmd = command.split()[0]
        if base_cmd not in Config.SYNTAX_HIGHLIGHT_COMMANDS:
            return output

        for ext, lang in Config.SYNTAX_EXTENSIONS.items():
            if ext in command:
                try:
                    return Syntax(output, lang, theme="vim", line_numbers=True, indent_guides=True)
                except Exception:  # noqa: BLE001
                    break

        return output

    def display_directory_change(self, command: str, new_dir: str) -> None:
        self.console.print(
            PanelTheme.build(
                f"[green]Changed directory to: {new_dir}[/green]",
                title=f" Shell: {command}",
                style="default",
                fit=True,
                highlight=True,
            )
        )

    def display_error(self, command: str, error_msg: str) -> None:
        self.console.print(
            PanelTheme.build(
                f"[red]{error_msg}[/red]",
                title=f" Shell: {command}",
                style="error",
            )
        )

    def display_interactive_start(self, command: str) -> None:
        tree = Tree(
            f" [yellow]Starting interactive mode: {command}[/yellow]",
            guide_style="dim",
        )
        tree.add("[cyan]Use Ctrl+C or app's exit command to return to shell[/cyan]")
        self.console.print(tree)

    def display_interactive_end(self, command: str, return_code: int) -> None:
        if return_code == 0:
            tree = Tree(
                f" [green]{command} completed successfully[/green]",
                guide_style="dim",
            )
            self.console.print(tree)
        else:
            tree = Tree(
                f" [yellow]{command} exited with code: {return_code}[/yellow]",
                guide_style="dim",
            )
            self.console.print(tree)
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def display_interrupt(self, message: str = "^C - Command interrupted") -> None:
        self.console.print(
            PanelTheme.build(
                f"[yellow]{message}[/yellow]",
                title=" Shell",
                style="warning",
            )
        )

    def display_goodbye(self) -> None:
        self.console.print("\n [yellow]Goodbye![/yellow]")

    def create_status(self, message: str) -> Status:
        return Status(f"[bold green]{message}", console=self.console)

    def show_cancelled_stream_notification(self, user_message: str) -> None:
        notification_text = f""" [yellow]AI response cancelled[/yellow]

[cyan]Original question:[/cyan] {user_message[:80]}{'...' if len(user_message) > 80 else ''}

[green]To resume:[/green]
• Press [bold]Alt+Z[/bold] or type [bold]resume[/bold]
• Type [bold]cancelstate[/bold] to see details

[dim]Partial response has been saved for resume[/dim]"""

        self.console.print(
            PanelTheme.build(
                notification_text,
                title=" Stream Cancelled",
                style="warning",
                padding=(1, 2),
            )
        )
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    def show_cancelled_stream_info(self, state_info: dict) -> None:
        user_message = state_info["user_message"]
        word_count = state_info["partial_word_count"]
        timestamp = state_info["timestamp"]

        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%H:%M:%S")
        except Exception:  # noqa: BLE001
            time_str = timestamp

        info_text = f"""[cyan]Cancelled Stream Details:[/cyan]

[bold]Original Question:[/bold] {user_message}
[bold]Partial Words:[/bold] {word_count}
[bold]Cancelled At:[/bold] {time_str}

[green]Available Actions:[/green]
• [bold]resume[/bold] - Continue from where it stopped
• [bold]Alt+Z[/bold] - Quick resume via keybinding
• [bold]clear[/bold] - Clear this cancelled state"""

        self.console.print(
            PanelTheme.build(
                info_text,
                title=" Cancelled Stream State",
                style="info",
                padding=(1, 2),
            )
        )
        if self._pending_footer:
            self.console.print(f"[dim]{self._pending_footer}[/dim]")
            self._pending_footer = None

    @staticmethod
    def create_progress_bar(description: str) -> Progress:
        progress = Progress(
            SpinnerColumn("point"),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            transient=False,
        )
        progress.add_task(description, total=None)
        return progress

    def render_markdown(self, content: str):
        try:
            return Markdown(content)
        except Exception:  # noqa: BLE001
            return Text(content, overflow="fold")
