from dataclasses import dataclass


BIS_10500 = {
    "ph": {"label": "pH", "unit": "none", "acceptable": 6.5, "permissible": 8.5, "weight": 0.2, "strategy": "range"},
    "tds": {"label": "Total Dissolved Solids", "unit": "mg/L", "acceptable": 500.0, "permissible": 2000.0, "weight": 0.3, "strategy": "threshold"},
    "fluoride": {"label": "Fluoride", "unit": "mg/L", "acceptable": 1.0, "permissible": 1.5, "weight": 0.8, "strategy": "threshold"},
    "arsenic": {"label": "Arsenic", "unit": "mg/L", "acceptable": 0.01, "permissible": 0.05, "weight": 1.0, "strategy": "threshold"},
    "nitrate": {"label": "Nitrate", "unit": "mg/L", "acceptable": 45.0, "permissible": None, "weight": 0.7, "strategy": "threshold"},
    "iron": {"label": "Iron", "unit": "mg/L", "acceptable": 0.3, "permissible": None, "weight": 0.4, "strategy": "threshold"},
    "turbidity": {"label": "Turbidity", "unit": "NTU", "acceptable": 1.0, "permissible": 5.0, "weight": 0.3, "strategy": "threshold"},
    "e_coli": {"label": "E. Coli", "unit": "CFU/100mL", "acceptable": 0.0, "permissible": 0.0, "weight": 0.9, "strategy": "microbial"},
}

BANDS = [(75.0, "Critical"), (50.0, "High"), (25.0, "Medium"), (0.0, "Low")]
BAND_ORDER = ["Low", "Medium", "High", "Critical"]
ACUTE_HAZARDS = {"e_coli", "total_coliform", "arsenic"}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@dataclass
class SeverityResult:
    severity: float
    exceeded: bool


def parameter_severity(
    value: float,
    acceptable: float,
    permissible: float | None,
    strategy: str = "threshold",
) -> SeverityResult:
    if strategy == "range":
        low, high = acceptable, permissible or 8.5
        if low <= value <= high:
            return SeverityResult(0.0, False)
        deviation = (low - value) if value < low else (value - high)
        return SeverityResult(clamp(deviation / 1.0), True)

    if strategy == "microbial":
        return SeverityResult(1.0 if value > acceptable else 0.0, value > acceptable)

    if permissible is None or permissible <= acceptable:
        return SeverityResult(1.0 if value > acceptable else 0.0, value > acceptable)

    if value <= acceptable:
        return SeverityResult(0.0, False)
    raw = (value - acceptable) / (permissible - acceptable)
    return SeverityResult(clamp(raw), True)


def band_for(score: float) -> str:
    for threshold, name in BANDS:
        if score >= threshold:
            return name
    return "Low"


def composite_score(readings: dict[str, tuple[float, dict]]) -> tuple[float, str, str | None]:
    total_weight = 0.0
    weighted_sum = 0.0
    contributions: list[tuple[float, str]] = []
    results: dict[str, SeverityResult] = {}

    for key, (value, spec) in readings.items():
        result = parameter_severity(
            value,
            spec["acceptable"],
            spec.get("permissible"),
            spec.get("strategy", "threshold"),
        )
        results[key] = result
        weight = spec["weight"]
        weighted_sum += weight * result.severity
        total_weight += weight
        if result.exceeded:
            contributions.append((result.severity * weight, key))

    if total_weight == 0:
        return 0.0, "Low", None

    score = round((weighted_sum / total_weight) * 100, 2)
    worst = max(contributions)[1] if contributions else None
    return score, escalate_band(band_for(score), results), worst


def escalate_band(band: str, results: dict[str, "SeverityResult"]) -> str:
    full_breaches = [k for k, r in results.items() if r.severity >= 1.0]
    if not full_breaches:
        return band
    floor_idx = 3 if any(k in ACUTE_HAZARDS for k in full_breaches) else 2
    return BAND_ORDER[max(BAND_ORDER.index(band), floor_idx)]
