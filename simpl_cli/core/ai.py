#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from typing import Dict, Generator, Iterable, List, Optional

import requests

from ..config import Config
from ..context import ChromaMemoryStore
from ..persona import PersonaSearchService, create_persona
from .router import AdvancedRouter, RouterDecision, create_router


class AIChatManager:
    def __init__(self, api_key: str, context_manager) -> None:
        self.api_key = api_key
        self.context_manager = context_manager
        self.memory_store: Optional[ChromaMemoryStore] = None
        self.memory_enabled = Config.MEMORY_ENABLED
        self.memory_top_k = Config.MEMORY_TOP_K
        self.memory_error: Optional[str] = None
        self.router_enabled = Config.is_router_enabled()
        self.router: Optional[AdvancedRouter] = None
        self.search_service = PersonaSearchService()
        self.persona_memory: Dict[str, Dict] = {}
        self.command_executor = None

        if self.memory_enabled:
            try:
                self.memory_store = ChromaMemoryStore(
                    embedding_dimension=Config.MEMORY_EMBEDDING_DIM,
                    persist_directory=str(Config.MEMORY_PATH),
                    max_items=Config.MEMORY_MAX_ITEMS,
                )
            except Exception as error:  # noqa: BLE001
                self.memory_store = None
                self.memory_enabled = False
                self.memory_error = str(error)

        if self.router_enabled:
            try:
                self.router = create_router(api_key)
            except Exception:  # noqa: BLE001
                self.router = None
        else:
            self.router = None

    def set_command_executor(self, executor) -> None:
        self.command_executor = executor

    def prepare_interaction(self, user_message: str) -> Dict:
        diagnostics: List[str] = []

        decision = self._route(user_message, diagnostics)
        persona_name = decision.persona if decision else "general_chat"
        persona_context = self._build_persona_context(user_message, decision)

        persona = create_persona(persona_name, self)
        result = persona.process(user_message, persona_context)

        self.persona_memory[persona_name] = result.metadata

        return {
            "type": "persona",
            "messages": result.messages,
            "decision": decision,
            "diagnostics": diagnostics,
            "renderable": result.renderable,
            "metadata": result.metadata,
            "persona": persona_name,
        }

    def _route(self, user_message: str, diagnostics: List[str]) -> Optional[RouterDecision]:
        if not self.router_enabled:
            diagnostics.append("[yellow]Router disabled via configuration; defaulting to general_chat.[/yellow]")
            return None

        if not self.router:
            diagnostics.append("[yellow]Router unavailable, defaulting to general_chat.[/yellow]")
            return None

        diagnostics.append("[cyan]Advanced Router analyzing intent (LLM-based)...[/cyan]")
        try:
            decision = self.router.route(user_message, self.context_manager.conversation_history)
        except Exception as error:  # noqa: BLE001
            diagnostics.append(f"[red]Router error:[/red] {error}")
            return None

        if decision:
            diagnostics.append(
                f"[green]LLM Decision:[/green] {decision.persona} (confidence: {decision.confidence:.2f})"
            )
            if decision.reasoning:
                diagnostics.append(f"[dim]   Reasoning: {decision.reasoning}[/dim]")

        if decision and decision.confidence < 0.5:
            diagnostics.append("[yellow]Confidence low, fallback ke general_chat.[/yellow]")
            return None

        return decision

    def _build_persona_context(self, user_message: str, decision: Optional[RouterDecision]) -> Dict:
        shell_context = self.context_manager.build_context_for_ai()
        memory_snippets = self._retrieve_memory_snippets(user_message)

        metadata_bundle = {
            "decision": decision,
            "query": decision.query if decision else None,
            "shell_context": shell_context,
            "memory_snippets": memory_snippets,
            "supplemental_text": self._collect_persona_metadata_text(),
            "metadata": self.persona_memory.copy(),
        }
        return metadata_bundle

    def _collect_persona_metadata_text(self) -> str:
        supplemental = []
        for meta in self.persona_memory.values():
            if meta.get("results"):
                supplemental.append(meta["results"])

        return "\n\n".join(supplemental)

    def complete(self, messages: List[dict], max_tokens: int = 1024) -> str:
        payload = {
            "model": Config.get_model_name(),
            "messages": messages,
            "stream": False,
        }
        payload.update(Config.AI_CONFIG)
        payload["max_tokens"] = max_tokens
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            response = requests.post(
                Config.API_BASE_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=Config.API_TIMEOUT,
            )
            response.raise_for_status()
        except Exception as error:  # noqa: BLE001
            raise RuntimeError(f"Completion error: {error}") from error

        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            return ""

        return choices[0].get("message", {}).get("content", "")

    def run_shell_command(self, command: str) -> Dict[str, str | int]:
        shell_env = os.environ.copy()
        shell_kwargs = {}
        if os.name != "nt":
            shell_kwargs["executable"] = Config.get_shell()

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                env=shell_env,
                **shell_kwargs,
            )
        except Exception as error:  # noqa: BLE001
            output = f"Command error: {error}"
            self.context_manager.add_shell_context(command, output)
            return {
                "command": command,
                "exit_code": -1,
                "stdout": "",
                "stderr": output,
            }

        stdout = result.stdout or ""
        stderr = result.stderr or ""
        combined = (stdout + stderr).strip() or f"Exit code {result.returncode}"
        self.context_manager.add_shell_context(command, combined)

        if self.command_executor:
            try:
                self.command_executor._update_completion_if_needed(command)  # noqa: SLF001
            except Exception:
                pass

        if self.memory_enabled and self.memory_store:
            try:
                self.memory_store.add_interaction(
                    content=f"Command: {command}\nOutput: {combined[:2000]}",
                    metadata={
                        "type": "shell_persona",
                        "cwd": os.getcwd(),
                    },
                )
            except Exception:
                pass

        return {
            "command": command,
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
        }

    def create_stream(self, messages: List[dict]) -> Generator[str, None, None]:
        url = Config.API_BASE_URL
        payload = {
            "model": Config.get_model_name(),
            "messages": messages,
            "stream": True,
            **Config.AI_CONFIG,
        }
        headers = {
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                stream=True,
                timeout=Config.API_TIMEOUT,
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                line_str = line.decode("utf-8")

                if not line_str.startswith("data: "):
                    continue

                json_str = line_str[6:]

                if json_str.strip() == "[DONE]":
                    break

                try:
                    chunk_data = json.loads(json_str)

                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                        delta = chunk_data["choices"][0].get("delta", {})
                        content = delta.get("content", "")

                        if content:
                            yield content

                except json.JSONDecodeError:
                    continue

        except Exception as error:  # noqa: BLE001
            yield f"Error: {str(error)}"

    def store_conversation(self, user_message: str, ai_response: str) -> None:
        self.context_manager.add_conversation(user_message, ai_response)
        if self.memory_enabled and self.memory_store:
            try:
                self.memory_store.add_interaction(
                    content=f"User: {user_message}\nAssistant: {ai_response}",
                    metadata={
                        "type": "conversation",
                        "cwd": self.context_manager.current_directory,
                    },
                )
            except Exception:
                pass

    def add_shell_memory(self, command: str, output: str, cwd: str) -> None:
        if not self.memory_enabled or not self.memory_store:
            return

        try:
            content = f"Command: {command}\nOutput: {output.strip()[:2000]}"
            self.memory_store.add_interaction(
                content=content,
                metadata={
                    "type": "shell",
                    "cwd": cwd,
                },
            )
        except Exception:
            pass

    def _retrieve_memory_snippets(self, user_message: str) -> List:
        if not self.memory_enabled or not self.memory_store:
            return []

        try:
            return self.memory_store.similarity_search(
                query=user_message,
                top_k=self.memory_top_k,
            )
        except Exception:
            return []

    def set_memory_enabled(self, enabled: bool) -> bool:
        self.memory_error = None

        if enabled:
            if not self.memory_store:
                try:
                    self.memory_store = ChromaMemoryStore(
                        embedding_dimension=Config.MEMORY_EMBEDDING_DIM,
                        persist_directory=str(Config.MEMORY_PATH),
                        max_items=Config.MEMORY_MAX_ITEMS,
                    )
                except Exception as error:  # noqa: BLE001
                    self.memory_store = None
                    self.memory_error = str(error)
            self.memory_enabled = self.memory_store is not None
        else:
            self.memory_enabled = False
        return self.memory_enabled

    def set_memory_top_k(self, value: int) -> int:
        value = max(1, min(50, value))
        self.memory_top_k = value
        return self.memory_top_k

    def get_memory_stats(self) -> dict:
        stats = {
            "configured": Config.MEMORY_ENABLED,
            "enabled": self.memory_enabled,
            "available": self.memory_store is not None,
            "top_k": self.memory_top_k,
            "max_items": Config.MEMORY_MAX_ITEMS,
            "path": str(Config.MEMORY_PATH),
            "count": 0,
            "error": self.memory_error,
        }

        if self.memory_store:
            try:
                stats["count"] = self.memory_store.count()
                stats["path"] = self.memory_store.storage_path
            except Exception:
                stats["count"] = -1

        return stats

    def clear_memory(self) -> bool:
        if not self.memory_store:
            return False

        try:
            self.memory_store.clear()
            return True
        except Exception:
            return False

    def _format_search_results(self, payload: Dict) -> str:
        results = payload.get("organic_results", [])[:8]
        if not results:
            return "(no results)"

        lines: List[str] = []
        for item in results:
            title = item.get("title", "Untitled")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            domain = item.get("domain", "")
            date = item.get("date")
            bullet = f"- Title: {title}\n  Domain: {domain}"
            if date:
                bullet += f" | Date: {date}"
            bullet += f"\n  Summary: {snippet}\n  Link: {link}"
            lines.append(bullet)

        return "\n\n".join(lines)

    def record_interaction(self, user_message: str, ai_response: str, interaction: Dict) -> None:
        if not ai_response:
            return

        self.store_conversation(user_message, ai_response)

        if (
            interaction.get("persona") == "search_service"
            and self.memory_enabled
            and self.memory_store
            and interaction.get("metadata")
        ):
            formatted = interaction["metadata"].get("results") or ""
            try:
                self.memory_store.add_interaction(
                    content=(
                        f"Search query: {user_message}\n"
                        f"Results:\n{formatted}\n\nSummary:\n{ai_response}"
                    ),
                    metadata={
                        "type": "search",
                        "cwd": self.context_manager.current_directory,
                    },
                )
            except Exception:
                pass
