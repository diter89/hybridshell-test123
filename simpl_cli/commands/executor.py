#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from typing import Optional 
from rich.columns import Columns
from rich.console import Console
from rich.table import Table

from ..config import Config
from ..environment import env_detector
from ..ui.theme import PanelTheme


class ShellCommandExecutor:
    def __init__(
        self,
        console: Console,
        ui,
        streaming_ui,
        context_manager,
        completion_manager,
    ) -> None:
        self.console = console
        self.ui = ui
        self.streaming_ui = streaming_ui
        self.context_manager = context_manager
        self.completion_manager = completion_manager
        self.ai_manager = None

    def set_ai_manager(self, ai_manager) -> None:
        self.ai_manager = ai_manager

    def execute(self, command: str) -> Optional[str]:
        if not command.strip():
            return None

        try:
            if command.strip() == "/help":
                self.ui.show_help()
                return None

            if self._handle_environment_commands(command):
                return None

            normalized = command.strip()

            if normalized == "exit":
                return "exit"
            if normalized == "clear":
                self._true_clear_terminal()
                return None
            if normalized == "cd" or normalized.startswith("cd "):
                self._handle_cd_command(normalized)
                self.completion_manager.update_cache()
                return None
            if normalized.startswith("source "):
                self._handle_source_command(normalized)
                return None
            if normalized == "deactivate":
                self._handle_deactivate_command(normalized)
                return None
            if (
                normalized.endswith("/activate")
                or normalized.endswith("\\activate")
                or normalized.startswith("activate ")
            ):
                self._handle_activate_command(normalized)
                return None

            if self._is_interactive_command(command):
                self._handle_interactive_command(command)
                return None

            self._handle_regular_command(command)
        except KeyboardInterrupt:
            self.ui.display_interrupt()
        except Exception as error:  # noqa: BLE001
            self.ui.display_error(command, f"Error: {error}")
            self.context_manager.add_shell_context(command, f"Error: {error}")

        return None

    def _true_clear_terminal(self) -> None:
        clear_sequence = "\033[2J\033[H"
        sys.stdout.write(clear_sequence)
        sys.stdout.flush()

        try:
            if os.name == "posix":
                os.system("clear")
            elif os.name == "nt":
                os.system("cls")
        except Exception:  # noqa: BLE001
            self.console.clear()

    def _is_interactive_command(self, command: str) -> bool:
        base_cmd = command.strip().split()[0]

        if base_cmd in Config.INTERACTIVE_COMMANDS:
            return True

        if "|" in command:
            parts = command.split("|")
            for part in parts:
                if part.strip().split()[0] in Config.INTERACTIVE_COMMANDS:
                    return True

        return False

    def _handle_environment_commands(self, command: str) -> bool:
        if not command.startswith("!"):
            return False

        env_cmd = command[1:]

        try:
            handlers = {
                "env": self._show_environment_status,
                "status": self._show_detailed_system_info,
                "git": self._show_git_info,
                "python": self._show_python_info,
            }

            if env_cmd in handlers:
                handlers[env_cmd]()
                self.context_manager.add_shell_context(
                    command, f"Environment command '{env_cmd}' executed"
                )
                return True

            error_msg = f"Unknown environment command: {env_cmd}"
            self.ui.display_error(command, error_msg)
            self.context_manager.add_shell_context(command, f"Error: {error_msg}")
            return True
        except Exception as error:  # noqa: BLE001
            error_msg = f"Environment command error: {error}"
            self.ui.display_error(command, error_msg)
            self.context_manager.add_shell_context(command, f"Error: {error_msg}")
            return True

    def _show_environment_status(self) -> None:
        env_info = env_detector.get_all_environments()

        table = Table(
            title="Environment Status",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Type", style="cyan", width=12)
        table.add_column("Status", style="green", width=20)
        table.add_column("Details", style="yellow")

        if env_info["python"]:
            py_env = env_info["python"]
            table.add_row(
                "Python",
                py_env["name"],
                f"v{py_env['python_version']} ({py_env['type']})",
            )
        else:
            table.add_row(
                "Python",
                "System",
                f"v{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            )

        if env_info["git"]:
            git_info = env_info["git"]
            status_indicator = "" if git_info.get("has_changes") else ""
            table.add_row(
                "Git",
                f"{status_indicator} {git_info['branch']}",
                f"Ahead: {git_info.get('ahead', 0)}, Behind: {git_info.get('behind', 0)}",
            )
        else:
            table.add_row("Git", "Not a repository", "-")

        if env_info["node"]:
            node_info = env_info["node"]
            modules_status = "" if node_info["has_modules"] else ""
            table.add_row(
                "Node.js",
                node_info["name"],
                f"v{node_info['version']} (modules: {modules_status})",
            )
        else:
            table.add_row("Node.js", "Not detected", "-")

        if env_info["docker"]:
            docker_info = env_info["docker"]
            docker_details: list[str] = []
            if docker_info.get("has_dockerfile"):
                docker_details.append("Dockerfile")
            if docker_info.get("has_compose"):
                docker_details.append("Compose")
            if docker_info.get("inside_container"):
                docker_details.append("In Container")

            table.add_row(
                "Docker",
                "Available",
                ", ".join(docker_details) if docker_details else "Basic",
            )
        else:
            table.add_row("Docker", "Not detected", "-")

        self.console.print(table)

    def _show_detailed_system_info(self) -> None:
        system_info = env_detector.get_system_info()
        env_info = env_detector.get_all_environments()

        system_text = (
            f"[bold cyan]System Resources[/bold cyan]\n"
            f"CPU Usage: {system_info['cpu_percent']:.1f}%\n"
            f"Memory Usage: {system_info['memory_percent']:.1f}%\n"
            f"Available Memory: {system_info['memory_available']}MB\n"
            f"Load Average: {system_info['load_average']:.2f}\n"
            f"Uptime: {system_info['uptime']}"
        )

        env_summary = "[bold green]Active Environments[/bold green]\n"
        active_envs: list[str] = []

        if env_info["python"]:
            active_envs.append(f"󰌠 {env_info['python']['display']}")
        if env_info["git"]:
            git_status = "" if env_info["git"].get("has_changes") else ""
            active_envs.append(f"{git_status} {env_info['git']['display']}")
        if env_info["node"]:
            active_envs.append(f"󰎙 {env_info['node']['display']}")
        if env_info["docker"]:
            active_envs.append(f"󰡨 {env_info['docker']['display']}")

        if active_envs:
            env_summary += "\n".join(active_envs)
        else:
            env_summary += "No special environments detected"

        cwd = os.getcwd()
        dir_info = f"[bold yellow]Current Directory[/bold yellow]\n{cwd}"

        panels = [
            PanelTheme.build(system_text, title="System", style="info"),
            PanelTheme.build(env_summary, title="Environments", style="info"),
            PanelTheme.build(dir_info, title="Location", style="info"),
        ]

        self.console.print(Columns(panels))

    def _show_git_info(self) -> None:
        git_info = env_detector.get_git_status()

        if not git_info:
            self.console.print("[red]Not in a Git repository[/red]")
            return

        table = Table(title="Git Repository Information", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Branch", git_info["branch"])
        table.add_row(
            "Status",
            "[red][/red] Modified" if git_info.get("has_changes") else "[green][/green] Clean",
        )
        table.add_row("Commits Ahead", str(git_info.get("ahead", 0)))
        table.add_row("Commits Behind", str(git_info.get("behind", 0)))

        self.console.print(table)

        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0 and result.stdout:
                commits = result.stdout.strip()
                self.console.print(
                    PanelTheme.build(commits, title="Recent Commits", style="info")
                )
        except Exception:  # noqa: BLE001
            pass

    def _show_python_info(self) -> None:
        py_env = env_detector.get_python_environment()

        table = Table(title="Python Environment", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row(
            "Python Version",
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )
        table.add_row("Python Executable", sys.executable)

        if py_env:
            table.add_row("Virtual Environment", py_env["name"])
            table.add_row("Environment Type", py_env["type"])
            if "path" in py_env:
                table.add_row("Environment Path", py_env["path"])
        else:
            table.add_row("Virtual Environment", "None (System Python)")

        python_paths = sys.path[:3]
        if len(sys.path) > 3:
            python_paths.append("...")
        table.add_row("Python Path", "\n".join(python_paths))

        self.console.print(table)

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[2:]
                if lines:
                    packages = "\n".join(lines[:10])
                    if len(lines) > 10:
                        packages += f"\n... and {len(lines) - 10} more packages"
                    self.console.print(
                        PanelTheme.build(packages, title="Installed Packages (Top 10)", style="info")
                    )
        except Exception:  # noqa: BLE001
            pass

    def _handle_cd_command(self, command: str) -> None:
        path = command[3:].strip()
        if not path:
            path = os.path.expanduser("~")
        else:
            path = os.path.expanduser(path)

        try:
            os.chdir(path)
            new_dir = os.getcwd()
            self.ui.display_directory_change(command, new_dir)
            self.context_manager.add_shell_context(
                command, f"Changed directory to: {new_dir}"
            )
        except OSError as error:
            error_msg = f"cd: {error}"
            self.ui.display_error(command, error_msg)
            self.context_manager.add_shell_context(command, error_msg)

    def _handle_source_command(self, command: str) -> None:
        source_file = command[7:].strip()

        if not source_file:
            error_msg = "source: missing file operand"
            self.ui.display_error(command, error_msg)
            self.context_manager.add_shell_context(command, error_msg)
            return

        source_file = os.path.expanduser(source_file)

        if not os.path.exists(source_file):
            error_msg = f"source: {source_file}: No such file or directory"
            self.ui.display_error(command, error_msg)
            self.context_manager.add_shell_context(command, error_msg)
            return

        bash_command = f'source "{source_file}" && env'
        self._execute_source_like_command(command, bash_command)

    def _handle_deactivate_command(self, command: str) -> None:
        try:
            virtual_env = os.environ.get("VIRTUAL_ENV")
            conda_env = os.environ.get("CONDA_DEFAULT_ENV")

            if not virtual_env and not conda_env:
                error_msg = "deactivate: No virtual environment currently activated"
                self.ui.display_error(command, error_msg)
                self.context_manager.add_shell_context(command, error_msg)
                return

            env_name = ""
            env_type = ""

            if virtual_env:
                env_name = os.path.basename(virtual_env)
                env_type = "virtualenv/venv"
            elif conda_env and conda_env != "base":
                env_name = conda_env
                env_type = "conda"

            with self.ui.create_status("Deactivating virtual environment..."):
                if virtual_env:
                    current_path = os.environ.get("PATH", "")
                    venv_bin = os.path.join(virtual_env, "bin")
                    path_parts = current_path.split(os.pathsep)
                    new_path_parts = [part for part in path_parts if not part.startswith(venv_bin)]
                    os.environ["PATH"] = os.pathsep.join(new_path_parts)

                    env_vars_to_remove = ["VIRTUAL_ENV", "VIRTUAL_ENV_PROMPT"]
                    removed_vars = []

                    for var in env_vars_to_remove:
                        if var in os.environ:
                            del os.environ[var]
                            removed_vars.append(var)

                    original_ps1 = os.environ.get("_OLD_VIRTUAL_PS1")
                    if original_ps1:
                        os.environ["PS1"] = original_ps1
                        del os.environ["_OLD_VIRTUAL_PS1"]
                        removed_vars.append("_OLD_VIRTUAL_PS1")

                elif conda_env:
                    conda_vars_to_remove = [
                        "CONDA_DEFAULT_ENV",
                        "CONDA_PREFIX",
                        "CONDA_PYTHON_EXE",
                    ]
                    removed_vars = []

                    for var in conda_vars_to_remove:
                        if var in os.environ:
                            del os.environ[var]
                            removed_vars.append(var)

                    conda_base = os.environ.get("CONDA_EXE")
                    if conda_base:
                        conda_base_bin = os.path.dirname(conda_base)
                        current_path = os.environ.get("PATH", "")

                        if conda_base_bin not in current_path:
                            os.environ["PATH"] = f"{conda_base_bin}{os.pathsep}{current_path}"

            success_msg = f" Deactivated {env_type} environment: {env_name}"
            self.console.print(f"[green]{success_msg}[/green]")
            self.context_manager.add_shell_context(command, success_msg)

            if "removed_vars" in locals() and removed_vars:
                self.console.print(
                    f"[dim]Removed environment variables: {', '.join(removed_vars)}[/dim]"
                )

            current_path = os.environ.get("PATH", "")
            path_parts = current_path.split(os.pathsep)[:3]
            self.console.print(f"[dim]Updated PATH: {os.pathsep.join(path_parts)}...[/dim]")

        except Exception as error:  # noqa: BLE001
            error_msg = f"deactivate: Error deactivating environment: {error}"
            self.ui.display_error(command, error_msg)
            self.context_manager.add_shell_context(command, error_msg)

    def _handle_activate_command(self, command: str) -> None:
        try:
            activate_path = ""

            if command.endswith("/activate") or command.endswith("\\activate"):
                activate_path = command
            elif command.startswith("activate "):
                env_name = command[9:].strip()
                conda_exe = os.environ.get("CONDA_EXE")
                if conda_exe:
                    bash_command = (
                        f'source "{os.path.dirname(conda_exe)}/activate" '
                        f"&& conda activate {env_name} && env"
                    )
                    self._execute_source_like_command(command, bash_command)
                    return

                error_msg = f"activate: conda not found, cannot activate environment '{env_name}'"
                self.ui.display_error(command, error_msg)
                self.context_manager.add_shell_context(command, error_msg)
                return

            if activate_path:
                activate_path = os.path.expanduser(activate_path)

                if not os.path.exists(activate_path):
                    error_msg = f"activate: {activate_path}: No such file or directory"
                    self.ui.display_error(command, error_msg)
                    self.context_manager.add_shell_context(command, error_msg)
                    return

                bash_command = f'source "{activate_path}" && env'
                self._execute_source_like_command(command, bash_command)

        except Exception as error:  # noqa: BLE001
            error_msg = f"activate: {error}"
            self.ui.display_error(command, error_msg)
            self.context_manager.add_shell_context(command, error_msg)

    def _handle_interactive_command(self, command: str) -> None:
        if self._should_stream_interactive_command(command):
            handled = self._handle_streaming_interactive_command(command)
            if handled:
                return

        self._handle_passthrough_interactive_command(command)

    def _handle_passthrough_interactive_command(self, command: str) -> None:
        try:
            self.ui.display_interactive_start(command)

            shell_kwargs = {}
            if os.name != "nt":
                shell_kwargs["executable"] = Config.get_shell()

            result = subprocess.run(
                command,
                shell=True,
                cwd=os.getcwd(),
                **shell_kwargs,
            )

            self.ui.display_interactive_end(command, result.returncode)

            context_msg = (
                f"Interactive command completed with exit code: {result.returncode}"
            )
            self.context_manager.add_shell_context(command, context_msg)

        except KeyboardInterrupt:
            self.ui.display_interrupt("Interactive mode interrupted")
            self.context_manager.add_shell_context(
                command, "Interactive command interrupted by user"
            )
        except Exception as error:  # noqa: BLE001
            error_msg = f"Error running interactive command: {error}"
            self.ui.display_error(command, error_msg)
            self.context_manager.add_shell_context(command, error_msg)

    def _should_stream_interactive_command(self, command: str) -> bool:
        parts = command.strip().split()
        if not parts:
            return False

        base_cmd = parts[0]
        if base_cmd == "sudo" and len(parts) > 1:
            base_cmd = parts[1]

        base_cmd = os.path.basename(base_cmd)
        return base_cmd in getattr(Config, "STREAMING_COMMANDS", set())

    def _handle_streaming_interactive_command(self, command: str) -> bool:
        if os.name == "nt":
            return False

        try:
            process = self._spawn_streaming_process(command)
        except KeyboardInterrupt:
            self.console.print("[yellow] Command cancelled.[/yellow]")
            return True
        except Exception as error:  # noqa: BLE001
            self.ui.display_error(command, f"Streaming setup failed: {error}")
            return False

        if process is None:
            return True

        try:
            output, exit_code, cancelled = self.streaming_ui.stream_shell_command(
                command, process
            )
        finally:
            if process.stdout:
                try:
                    process.stdout.close()
                except Exception:  # noqa: BLE001
                    pass
            if process.stdin:
                try:
                    process.stdin.close()
                except Exception:  # noqa: BLE001
                    pass

        if cancelled:
            self.context_manager.add_shell_context(
                command, "Streaming command cancelled by user"
            )
            return True

        exit_display = exit_code if exit_code is not None else "unknown"
        context_output = output or f"Exit code: {exit_display}"
        self.context_manager.add_shell_context(command, context_output)

        if self.ai_manager:
            try:
                self.ai_manager.add_shell_memory(
                    command=command,
                    output=context_output,
                    cwd=os.getcwd(),
                )
            except Exception:  # noqa: BLE001
                pass

        return True

    def _spawn_streaming_process(self, command: str) -> subprocess.Popen | None:
        shell_env = os.environ.copy()
        shell_kwargs = {}
        if os.name != "nt":
            shell_kwargs["executable"] = Config.get_shell()

        sanitized_command = command
        password: str | None = None

        if command.strip().startswith("sudo "):
            password = self._prompt_sudo_password()
            if password is None:
                self.console.print(
                    "[yellow]Cancelled command: sudo password not provided.[/yellow]"
                )
                return None
            parts = command.strip().split(maxsplit=1)
            rest = parts[1] if len(parts) > 1 else ""
            if not rest:
                self.console.print(
                    "[red]sudo requires a command to execute.[/red]"
                )
                return None
            sanitized_command = f"sudo -S {rest}".strip()

        process = subprocess.Popen(
            sanitized_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=False,
            bufsize=0,
            cwd=os.getcwd(),
            env=shell_env,
            **shell_kwargs,
        )

        if password is not None and process.stdin:
            try:
                process.stdin.write((password + "\n").encode())
                process.stdin.flush()
            except Exception:  # noqa: BLE001
                pass

        return process

    def _prompt_sudo_password(self) -> str | None:
        try:
            from prompt_toolkit import prompt as pt_prompt

            return pt_prompt("sudo password: ", is_password=True).strip() or None
        except KeyboardInterrupt:
            return None
        except Exception:  # noqa: BLE001
            try:
                from getpass import getpass

                return getpass("sudo password: ") or None
            except Exception:  # noqa: BLE001
                return None

    def _handle_regular_command(self, command: str) -> None:
        bash_builtins = [
            "source",
            "export",
            "unset",
            "alias",
            "unalias",
            "declare",
            "typeset",
            "readonly",
        ]
        command_parts = command.strip().split()
        base_command = command_parts[0] if command_parts else ""

        needs_shell_invocation = (
            "source " in command
            or command.startswith("source")
            or base_command in bash_builtins
            or "&&" in command
            or "||" in command
            or ";" in command
            or "export " in command
            or "unset " in command
        )

        shell_env = os.environ.copy()
        shell_kwargs = {}
        if os.name != "nt":
            shell_kwargs["executable"] = Config.get_shell()

        if needs_shell_invocation:
            with self.ui.create_status(f"Executing: {command}"):
                result = subprocess.run(
                    self._build_shell_invocation(command),
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd(),
                    env=shell_env,
                )
        else:
            with self.ui.create_status(f"Executing: {command}"):
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd(),
                    env=shell_env,
                    **shell_kwargs,
                )

        self.ui.display_shell_output(command, result)

        output = result.stdout + result.stderr
        self.context_manager.add_shell_context(command, output)

        if self.ai_manager:
            try:
                self.ai_manager.add_shell_memory(
                    command=command,
                    output=output,
                    cwd=os.getcwd(),
                )
            except Exception:
                pass

        self._update_completion_if_needed(command)

    def _update_completion_if_needed(self, command: str) -> None:
        modify_commands = ["touch", "mkdir", "rm", "rmdir", "mv", "cp", "ln"]
        base_cmd = command.strip().split()[0]

        if base_cmd in modify_commands:
            self.completion_manager.update_cache()

    def _execute_source_like_command(self, original_command: str, bash_command: str) -> None:
        try:
            old_env = dict(os.environ)

            with self.ui.create_status(f"Executing: {original_command}"):
                result = subprocess.run(
                    self._build_shell_invocation(bash_command),
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd(),
                )

            if result.returncode == 0:
                new_vars: dict[str, str] = {}
                changed_vars: dict[str, dict[str, str]] = {}

                for line in result.stdout.split("\n"):
                    if "=" in line and not line.startswith("_="):
                        try:
                            key, value = line.split("=", 1)
                        except ValueError:
                            continue

                        if key in ["PS1", "PS2", "BASH_FUNC_*", "_"] or key.startswith(
                            "BASH_FUNC_"
                        ):
                            continue

                        if key not in old_env:
                            new_vars[key] = value
                        elif old_env[key] != value:
                            changed_vars[key] = {"old": old_env[key], "new": value}

                        os.environ[key] = value

                success_msg = f" {original_command} completed successfully"
                if new_vars or changed_vars:
                    success_msg += (
                        f" ({len(new_vars)} new, {len(changed_vars)} changed variables)"
                    )

                self.console.print(f"[green]{success_msg}[/green]")
                self.context_manager.add_shell_context(original_command, success_msg)
                self._show_env_changes(new_vars, changed_vars)

            else:
                error_msg = (
                    f"{original_command}: {result.stderr.strip() or 'command failed'}"
                )
                self.ui.display_error(original_command, error_msg)
                self.context_manager.add_shell_context(original_command, error_msg)

        except Exception as error:  # noqa: BLE001
            error_msg = f"{original_command}: {error}"
            self.ui.display_error(original_command, error_msg)
            self.context_manager.add_shell_context(original_command, error_msg)

    def _show_env_changes(self, new_vars: dict, changed_vars: dict) -> None:
        important_vars = [
            "PATH",
            "VIRTUAL_ENV",
            "CONDA_DEFAULT_ENV",
            "NODE_ENV",
            "PYTHONPATH",
            "LD_LIBRARY_PATH",
            "JAVA_HOME",
        ]

        if new_vars:
            self.console.print("[dim]New environment variables:[/dim]")
            count = 0
            for var, value in new_vars.items():
                if var in important_vars or count < 5:
                    display_value = value
                    if len(display_value) > 60:
                        display_value = display_value[:57] + "..."
                    self.console.print(f"[dim green]  +{var}={display_value}[/dim green]")
                    count += 1

            if len(new_vars) > count:
                self.console.print(
                    f"[dim]  ... and {len(new_vars) - count} more new variables[/dim]"
                )

        if changed_vars:
            self.console.print("[dim]Changed environment variables:[/dim]")
            count = 0
            for var, values in changed_vars.items():
                if var in important_vars or count < 3:
                    old_val = values["old"]
                    new_val = values["new"]

                    if len(old_val) > 30:
                        old_val = old_val[:27] + "..."
                    if len(new_val) > 30:
                        new_val = new_val[:27] + "..."

                    self.console.print(
                        f"[dim yellow]  ~{var}: {old_val} → {new_val}[/dim yellow]"
                    )
                    count += 1

            if len(changed_vars) > count:
                self.console.print(
                    f"[dim]  ... and {len(changed_vars) - count} more changed variables[/dim]"
                )

    def _build_shell_invocation(self, command: str) -> list[str]:
        shell_path = Config.get_shell()
        if os.name == "nt":
            return [shell_path, "/C", command]
        return [shell_path, "-c", command]
