"""OpenAI model tiers for the optional ARGUS cascade."""

# Assignment-scale defaults: use efficient models and increase reasoning effort
# for harder work rather than routing to the largest model.
MODEL_TIERS = {
    "small": {
        "provider": "openai",
        "model": "gpt-6-luna",
        "reasoning_effort": "low",
        "input_cost_per_million": 0.10,
        "output_cost_per_million": 0.50,
        "purpose": "Focused, high-volume planning and routing",
    },
    "medium": {
        "provider": "openai",
        "model": "gpt-6.1-sol",
        "reasoning_effort": "medium",
        "input_cost_per_million": 2.00,
        "output_cost_per_million": 10.00,
        "purpose": "Routine evidence review",
    },
    "strong": {
        "provider": "openai",
        "model": "gpt-6.1-sol",
        "reasoning_effort": "high",
        "input_cost_per_million": 2.00,
        "output_cost_per_million": 10.00,
        "purpose": "Conflicting evidence and harder reasoning",
    },
}

DEFAULT_MODEL_TIER = "medium"
