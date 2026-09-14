"""
Unit tests for the Ship 30 and Artifact skills.
Verifies prompt construction and structure — no LLM calls.
"""
import pytest

from app.skills.ship30 import build_ship30_prompt, SHIP30_SYSTEM_PROMPT
from app.skills.artifact_skill import build_artifact_prompt


class TestShip30Skill:
    def test_system_prompt_contains_principles(self):
        """Ship 30 system prompt must encode the core writing principles."""
        assert "1,250" in SHIP30_SYSTEM_PROMPT
        assert "Hook" in SHIP30_SYSTEM_PROMPT
        assert "Takeaway" in SHIP30_SYSTEM_PROMPT
        assert "Grounding Rule" in SHIP30_SYSTEM_PROMPT

    def test_build_prompt_includes_topic(self):
        prompt = build_ship30_prompt("product-market fit", "")
        assert "product-market fit" in prompt

    def test_build_prompt_includes_context_block(self):
        context = "[Source 1: Test Episode]\nSome transcript content."
        prompt = build_ship30_prompt("growth loops", context)
        assert context in prompt

    def test_build_prompt_no_context_has_fallback(self):
        prompt = build_ship30_prompt("activation", "")
        assert "No transcript context" in prompt

    def test_build_prompt_word_count_instruction(self):
        prompt = build_ship30_prompt("retention", "some context")
        assert "1,250" in prompt

    def test_system_prompt_blocks_hallucination(self):
        """Prompt must instruct model not to make up data."""
        assert "do not make it" in SHIP30_SYSTEM_PROMPT.lower() or \
               "hallucinate" in SHIP30_SYSTEM_PROMPT.lower() or \
               "don't make up" in SHIP30_SYSTEM_PROMPT.lower() or \
               "NOT make up" in SHIP30_SYSTEM_PROMPT or \
               "traceable" in SHIP30_SYSTEM_PROMPT


class TestArtifactSkill:
    def test_markdown_system_prompt_returned(self):
        system, user = build_artifact_prompt("markdown", "Test Title", "Write a summary", "")
        assert "Markdown" in system
        assert "Test Title" in user
        assert "Write a summary" in user

    def test_html_system_prompt_returned(self):
        system, user = build_artifact_prompt("html", "Test Page", "Create a dashboard", "")
        assert "HTML" in system
        assert "JavaScript" in system  # must mention no-JS rule
        assert "Create a dashboard" in user

    def test_html_prompt_mentions_no_scripts(self):
        system, _ = build_artifact_prompt("html", "Title", "Instructions", "")
        assert "JavaScript" in system or "script" in system.lower()

    def test_context_block_injected(self):
        context = "RELEVANT TRANSCRIPT EXCERPTS:\n─────\n[Source 1]"
        _, user = build_artifact_prompt("markdown", "T", "I", context)
        assert context in user

    def test_no_context_uses_fallback(self):
        _, user = build_artifact_prompt("markdown", "T", "I", "")
        assert "No prior context" in user
