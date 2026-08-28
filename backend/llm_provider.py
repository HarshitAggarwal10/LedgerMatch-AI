"""
llm_provider.py
----------------
Single place that decides which LLM actually answers a prompt, so
llm_agent.py and qa_agent.py don't each need their own provider-selection
logic. Order of preference:

  1. Groq   (GROQ_API_KEY set)      -- fast, generous free tier, no card needed
  2. Claude (ANTHROPIC_API_KEY set) -- used if Groq isn't configured
  3. Mock                           -- used if neither key is set, or if a
                                        live call fails for any reason (rate
                                        limit, billing, network, etc.)

Every caller gets back {"text": ..., "mode": "live"|"mock", "provider": ...}
so the UI can always show exactly what actually answered the question --
never silently swapped without saying so.
"""

import os

GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
CLAUDE_MODEL = "claude-sonnet-4-6"


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 300) -> dict:
    """
    Tries Groq first, then Claude, and reports which one (if either)
    actually produced the text. Raises nothing -- callers should treat a
    failure of both as "no live provider available" via the returned dict
    having text=None, and fall back to their own mock logic.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if groq_key:
        try:
            return _call_groq(system_prompt, user_prompt, max_tokens, groq_key)
        except Exception as e:
            last_error = f"Groq: {type(e).__name__}: {e}"
            if not anthropic_key:
                return {"text": None, "mode": "mock", "provider": None, "error": last_error}
            # fall through to try Claude as a second live option

    if anthropic_key:
        try:
            return _call_claude(system_prompt, user_prompt, max_tokens, anthropic_key)
        except Exception as e:
            return {"text": None, "mode": "mock", "provider": None, "error": f"Claude: {type(e).__name__}: {e}"}

    return {"text": None, "mode": "mock", "provider": None, "error": "no GROQ_API_KEY or ANTHROPIC_API_KEY set"}


def _call_groq(system_prompt, user_prompt, max_tokens, api_key):
    from groq import Groq
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        max_completion_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    text = response.choices[0].message.content
    return {"text": text.strip(), "mode": "live", "provider": f"groq:{GROQ_MODEL}"}


def _call_claude(system_prompt, user_prompt, max_tokens, api_key):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(block.text for block in response.content if hasattr(block, "text"))
    return {"text": text.strip(), "mode": "live", "provider": f"claude:{CLAUDE_MODEL}"}
