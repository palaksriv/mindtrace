"""Transparent rule-based scoring for the Day 3 assessment."""

from collections import defaultdict

from app.models.assessment import Response, Trait


def calculate_trait_scores(responses: list[Response]) -> dict[str, float]:
    """Return each trait's mean normalized to a 0–100 scale."""
    grouped: dict[Trait, list[int]] = defaultdict(list)
    for response in responses:
        score = 6 - response.response if response.question.reverse_scored else response.response
        grouped[response.question.trait].append(score)
    return {
        trait.value: round((sum(grouped[trait]) / len(grouped[trait])) / 5 * 100, 1)
        for trait in Trait
    }
