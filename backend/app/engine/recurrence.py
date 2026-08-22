"""Recurrence & trend detection.

Distinguishes persistent contamination (flagged historically AND exceeding now)
from historical-only (since resolved) and new (fresh exceedance) patterns.
"""

from dataclasses import dataclass, field


PERSISTENT_WEIGHT = 2.0
HISTORICAL_WEIGHT = 0.5
NEW_WEIGHT = 1.0


@dataclass
class VillageRecurrence:
    village_id: int
    village: str
    district: str
    state: str
    historical: dict[str, list[int]] = field(default_factory=dict)
    current_exceedances: dict[str, float] = field(default_factory=dict)
    classifications: dict[str, str] = field(default_factory=dict)
    recurrence_score: float = 0.0
    verdict: str = "no-history"

    @property
    def persistent_params(self) -> list[str]:
        return [p for p, c in self.classifications.items() if c == "persistent"]


def classify_param(hist_years: list[int] | None, currently_exceeds: bool) -> str | None:
    has_history = bool(hist_years)
    if has_history and currently_exceeds:
        return "persistent"
    if has_history:
        return "historical-only"
    if currently_exceeds:
        return "new"
    return None


def compute_recurrence(
    historical: dict[str, list[int]],
    current_exceedances: dict[str, float],
) -> tuple[dict[str, str], float]:
    classifications: dict[str, str] = {}
    raw = 0.0

    all_params = set(historical) | set(current_exceedances)
    max_possible = PERSISTENT_WEIGHT * 2 * len(all_params)

    for param, years in historical.items():
        cls = classify_param(years, param in current_exceedances)
        if cls is None:
            continue
        classifications[param] = cls
        year_factor = min(len(years), 4) / 4
        if cls == "persistent":
            raw += PERSISTENT_WEIGHT * (1 + year_factor)
        else:
            raw += HISTORICAL_WEIGHT * year_factor

    for param in current_exceedances:
        if param in classifications:
            continue
        classifications[param] = "new"
        raw += NEW_WEIGHT

    score = round((raw / max_possible) * 100, 2) if max_possible else 0.0
    return classifications, score


def verdict_for(score: float, persistent_count: int) -> str:
    if persistent_count >= 2 or score >= 70:
        return "chronic-hotspot"
    if persistent_count == 1:
        return "recurring"
    if score > 0:
        return "watchlist"
    return "no-history"
