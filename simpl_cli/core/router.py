#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import requests
from ..config import Config


ROUTER_INSTRUCTIONS = """
You are an expert router. Choose the best tool. Always return strict JSON with fields:
{"intent": "...", "confidence": 0.0, "reasoning": "...", "suggested_query": "..."}

VALID INTENTS:
- GENERAL_CHAT
- SEARCH_SERVICE
- HELP_ASSISTENT

NOTES:
- Use SEARCH_SERVICE ONLY when the user explicitly asks for web lookups, latest info, prices, news, or phrases like "find", "get me", "latest info", "price", "news".
- Use GENERAL_CHAT for explanations, code samples, theory, or questions solvable without fresh web data.
- Use HELP_ASSISTENT when the user requests navigating the local project, reading many files, running multiple shell commands in sequence, or needs structured code analysis (planner + execution).
- suggested_query for SEARCH_SERVICE must be a clean search string (no extra comments).
- Confidence range 0-1. No markdown, code fences, or extra keys.
"""


@dataclass
class RouterDecision:
    persona: str
    query: Optional[str]
    confidence: float
    reasoning: str
    use_context: bool = False
    previous_results: Optional[str] = None


class AdvancedRouter:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.last_search_context: Optional[str] = None

    def route(self, user_input: str, conversation_history: List[Dict]) -> RouterDecision:
        context_text, has_search_results = self._extract_context(conversation_history)
        decision = self._classify_intent(user_input, context_text, has_search_results)

        if decision and decision.confidence >= 0.6:
            return decision

        return RouterDecision(
            persona="general_chat",
            query=user_input,
            confidence=0.5,
            reasoning="Fallback: router confidence too low",
        )

    def _extract_context(self, messages: List[Dict]) -> Tuple[str, bool]:
        if not messages:
            return "", False

        relevant = [msg for msg in messages if msg.get("role") != "system"][-8:]
        parts: List[str] = []
        has_search_results = False

        for msg in relevant:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content") or ""

            if msg.get("role") == "assistant" and any(
                marker in content
                for marker in (
                    "Source:",
                    "Sumber:",
                    "# Key Points",
                    "Web Page Summary",
                    "Address Analysis",
                    "```",
                )
            ):
                has_search_results = True
                self.last_search_context = content

            snippet = content if len(content) <= 240 else f"{content[:240]}..."
            parts.append(f"{role}: {snippet}")

        return "\n".join(parts), has_search_results

    def _classify_intent(
        self,
        user_input: str,
        context: str,
        has_search_results: bool,
    ) -> Optional[RouterDecision]:
        prompt = self._build_prompt(user_input, context)
        response = self._call_router_model(prompt)

        if not response:
            return None

        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            return None

        intent = data.get("intent", "GENERAL_CHAT")
        confidence = float(data.get("confidence", 0.5))
        reasoning = data.get("reasoning", "")
        suggested_query = data.get("suggested_query", user_input)

        tool_map = {
            "SEARCH_SERVICE": "search_service",
            "GENERAL_CHAT": "general_chat",
            "HELP_ASSISTENT": "help_assistent",
        }
        use_context = False
        previous_results = None
        query = suggested_query.strip() or user_input

        if intent == "GENERAL_CHAT":
            query = user_input
        elif intent == "SEARCH_SERVICE":
            query = suggested_query.strip() or user_input
        elif intent == "HELP_ASSISTENT":
            query = user_input

        return RouterDecision(
            persona=tool_map.get(intent, "general_chat"),
            query=query,
            confidence=confidence,
            reasoning=reasoning,
            use_context=use_context,
            previous_results=previous_results,
        )

    def _build_prompt(self, user_input: str, context: str) -> str:
        context_block = context or "(empty)"
        return (
            f"{ROUTER_INSTRUCTIONS}\n\n"
            f"CONVERSATION CONTEXT:\n---\n{context_block}\n---\n\n"
            f'CURRENT USER INPUT:\n"{user_input}"'
        )

    def _call_router_model(self, prompt: str) -> Optional[str]:
        payload = {
            "model": Config.get_router_model(),
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise intent classifier. Always answer with JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "temperature": 0.0,
            "top_p": 1,
            "response_format": {"type": "json_object"},
        }

        headers = {
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
        except Exception:  # noqa: BLE001
            return None

        try:
            json_data = response.json()
        except ValueError:
            return None

        choices = json_data.get("choices") or []
        if not choices:
            return None

        message = choices[0].get("message", {})
        return message.get("content")


def create_router(api_key: str) -> AdvancedRouter:
    return AdvancedRouter(api_key)
