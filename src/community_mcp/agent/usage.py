from dataclasses import dataclass


@dataclass(frozen=True)
class BedrockUsage:
    model_id: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
