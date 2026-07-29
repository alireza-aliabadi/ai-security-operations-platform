"""Token and cost estimation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field


# Approximate USD per 1M tokens (input, output)
MODEL_PRICES: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "text-embedding-3-small": (0.02, 0.02),
    "text-embedding-3-large": (0.13, 0.13),
    "llama3.2": (0.0, 0.0),
    "mock": (0.0, 0.0),
}


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars per token)."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


@dataclass
class CostTracker:
    """Accumulates estimated token usage and cost across LLM calls."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    embedding_tokens: int = 0
    estimated_cost_usd: float = 0.0
    calls: list[dict[str, float | int | str]] = field(default_factory=list)

    def record_chat(
        self,
        *,
        model: str,
        prompt: str,
        completion: str,
        provider: str,
    ) -> dict[str, float | int | str]:
        pt = estimate_tokens(prompt)
        ct = estimate_tokens(completion)
        cost = self._cost(model, pt, ct)
        self.prompt_tokens += pt
        self.completion_tokens += ct
        self.estimated_cost_usd += cost
        entry: dict[str, float | int | str] = {
            "type": "chat",
            "provider": provider,
            "model": model,
            "prompt_tokens": pt,
            "completion_tokens": ct,
            "cost_usd": round(cost, 6),
        }
        self.calls.append(entry)
        return entry

    def record_embed(
        self,
        *,
        model: str,
        text: str,
        provider: str,
    ) -> dict[str, float | int | str]:
        tokens = estimate_tokens(text)
        cost = self._cost(model, tokens, 0)
        self.embedding_tokens += tokens
        self.estimated_cost_usd += cost
        entry: dict[str, float | int | str] = {
            "type": "embed",
            "provider": provider,
            "model": model,
            "prompt_tokens": tokens,
            "completion_tokens": 0,
            "cost_usd": round(cost, 6),
        }
        self.calls.append(entry)
        return entry

    def summary(self) -> dict[str, float | int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "embedding_tokens": self.embedding_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens + self.embedding_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "call_count": len(self.calls),
        }

    @staticmethod
    def _cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        key = model.lower()
        prices = MODEL_PRICES.get(key)
        if prices is None:
            for name, pair in MODEL_PRICES.items():
                if name in key:
                    prices = pair
                    break
        if prices is None:
            prices = (0.5, 1.5)
        pin, pout = prices
        return (prompt_tokens / 1_000_000) * pin + (completion_tokens / 1_000_000) * pout
