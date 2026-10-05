"""Request options that depend on which Groq model is in use."""

# Extra completion tokens reserved for GPT-OSS reasoning.
REASONING_TOKENS = 1024


def llm_options(model_name: str, answer_tokens: int) -> dict:
    if model_name.startswith("openai/gpt-oss"):
        return {
            "max_tokens": answer_tokens + REASONING_TOKENS,
            "extra_body": {
                "reasoning_effort": "low",
                "include_reasoning": False,
            },
        }

    if model_name.startswith("qwen/"):
        return {
            "max_tokens": answer_tokens,
            "extra_body": {"reasoning_effort": "none"},
        }

    return {"max_tokens": answer_tokens}
