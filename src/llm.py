import os
import litellm

# -------------------------------------------------------------------
# CrewAI + Groq compatibility fix
# CrewAI 1.15.x may add Anthropic-specific `cache_breakpoint`
# metadata to messages. Groq rejects this field.
# -------------------------------------------------------------------

_original_completion = litellm.completion


def _groq_safe_completion(*args, **kwargs):
    # Disable LiteLLM caching for this request.
    kwargs["caching"] = False

    messages = kwargs.get("messages", [])

    for message in messages:
        if isinstance(message, dict):
            # Remove unsupported field from the message itself.
            message.pop("cache_breakpoint", None)

            # Also remove it from content blocks if present.
            content = message.get("content")

            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        block.pop("cache_breakpoint", None)

    return _original_completion(*args, **kwargs)


# Patch LiteLLM before CrewAI makes its API calls.
litellm.completion = _groq_safe_completion
litellm.drop_params = True


from crewai import LLM


MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def get_groq_llm():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is missing.")

    return LLM(
        model=f"groq/{MODEL}",
        api_key=api_key,
        temperature=0.1,
    )
