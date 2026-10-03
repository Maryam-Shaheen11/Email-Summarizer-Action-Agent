import os
import litellm

# ============================================================
# CrewAI + Groq compatibility fix
# Removes unsupported cache_breakpoint metadata
# ============================================================

_original_completion = litellm.completion


def _groq_safe_completion(*args, **kwargs):
    # Disable LiteLLM caching for Groq
    kwargs["caching"] = False

    messages = kwargs.get("messages", [])

    for message in messages:
        if isinstance(message, dict):
            # Remove unsupported field
            message.pop("cache_breakpoint", None)

            # Also remove it from content blocks
            content = message.get("content")

            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        block.pop("cache_breakpoint", None)

    return _original_completion(*args, **kwargs)


# Apply patch before CrewAI makes requests
litellm.completion = _groq_safe_completion
litellm.drop_params = True


# Import CrewAI only after the patch
from crewai import LLM


MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)


def get_llm():
    """
    Create the Groq LLM used by all CrewAI agents.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is missing.")

    return LLM(
        model=f"groq/{MODEL}",
        api_key=api_key,
        temperature=0.1,
    )
