"""
Artifact generation skill.
Produces Markdown documents or complete standalone HTML/CSS snippets
based on conversation context.
"""

ARTIFACT_SYSTEM_MARKDOWN = """You are an expert technical writer.
Generate a well-structured Markdown document based on the user's instructions and the conversation context provided.

Rules:
- Use proper Markdown: H1 title, H2/H3 sections, bullet lists, code blocks where appropriate
- Be comprehensive but scannable
- Ground all claims in the conversation context
- Do NOT include preamble like "Here is your document" — start directly with the content
- Output ONLY valid Markdown
"""

ARTIFACT_SYSTEM_HTML = """You are an expert frontend developer and writer.
Generate a complete, self-contained HTML document with inline CSS styling.

Rules:
- Output a FULL HTML document: <!DOCTYPE html><html>...<body>...</body></html>
- Include <style> tags inside <head> for all styling — no external stylesheets
- Make it visually clean: use system fonts, good spacing, max-width ~800px, centered
- NO JavaScript — static HTML/CSS only (security constraint)
- Ground all content in the conversation context provided
- Do NOT include preamble — output ONLY the HTML document
- The HTML will be rendered inside a sandboxed iframe — no scripts will execute
"""


def build_artifact_prompt(
    artifact_type: str,
    title: str,
    instructions: str,
    context_block: str,
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_message) for artifact generation.
    """
    system = ARTIFACT_SYSTEM_MARKDOWN if artifact_type == "markdown" else ARTIFACT_SYSTEM_HTML

    user_message = f"""Generate a {artifact_type.upper()} artifact with the following:

TITLE: {title}
INSTRUCTIONS: {instructions}

CONVERSATION CONTEXT:
{context_block if context_block else "No prior context available — generate based on the title and instructions alone."}
"""
    return system, user_message
