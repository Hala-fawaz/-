"""Per-model settings for the Groq models the guide can use.

Model ids and limits come from Groq's documentation (October 2026):
allam-2-7b has a 4,096-token context window, while openai/gpt-oss-120b,
openai/gpt-oss-20b and the Llama/Qwen models have about 131k tokens.
"""

from dataclasses import dataclass


# Extra completion tokens reserved for GPT-OSS reasoning, which is
# produced before (and counted with) the visible answer.
REASONING_TOKENS = 1024

SMALL_CONTEXT_MODELS = {
    "allam-2-7b": 4096,
}
DEFAULT_CONTEXT = 131072


@dataclass(frozen=True)
class ModelProfile:
    context_tokens: int
    evidence_chars: int   # total characters of passages sent with a question
    max_passages: int
    narrative_tokens: int # answer budget for «ماذا حدث في...» questions
    brief_tokens: int     # answer budget for «متى/كم/أين» questions


def model_profile(model_name: str) -> ModelProfile:
    context = SMALL_CONTEXT_MODELS.get(model_name, DEFAULT_CONTEXT)

    if context <= 8192:
        # 4k tokens must hold the instructions, the passages and the answer.
        return ModelProfile(context, evidence_chars=4200, max_passages=4,
                            narrative_tokens=700, brief_tokens=300)

    return ModelProfile(context, evidence_chars=9000, max_passages=6,
                        narrative_tokens=1100, brief_tokens=450)


def llm_options(model_name: str, answer_tokens: int) -> dict:
    """Keyword arguments for client.chat.completions.create()."""
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
