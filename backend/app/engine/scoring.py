from dataclasses import dataclass


BIS_10500 = {
    "ph": {"label": "pH", "unit": "none", "acceptable": 6.5, "permissible": 8.5, "weight": 0.2, "strategy": "range"},
    "tds": {"label": "Total Dissolved Solids", "unit": "mg/L", "acceptable": 500.0, "permissible": 2000.0, "weight": 0.3, "strategy": "threshold"},
    "fluoride": {"label": "Fluoride", "unit": "mg/L", "acceptable": 1.0, "permissible": 1.5, "weight": 0.8, "strategy": "threshold"},
    "arsenic": {"label": "Arsenic", "unit": "mg/L", "acceptable": 0.01, "permissible": None, "weight": 1.0, "strategy": "threshold"},
    "nitrate": {"label": "Nitrate", "unit": "mg/L", "acceptable": 45.0, "permissible": None, "weight": 0.7, "strategy": "threshold"},
    "iron": {"label": "Iron", "unit": "mg/L", "acceptable": 0.3, "permissible": None, "weight": 0.4, "strategy": "threshold"},
    "turbidity": {"label": "Turbidity", "unit": "NTU", "acceptable": 1.0, "permissible": 5.0, "weight": 0.3, "strategy": "threshold"},
    "e_coli": {"label": "E. Coli", "unit": "CFU/100mL", "acceptable": 0.0, "permissible": 0.0, "weight": 0.9, "strategy": "microbial"},
    "sulphate": {"label": "Sulphate", "unit": "mg/L", "acceptable": 200.0, "permissible": 400.0, "weight": 0.5, "strategy": "threshold"},
    "total_coliform": {"label": "Total Coliform", "unit": "CFU/100mL", "acceptable": 0.0, "permissible": 0.0, "weight": 0.9, "strategy": "microbial"},
}

# Total possible weight of all BIS parameters
TOTAL_BIS_WEIGHT = sum(v["weight"] for v in BIS_10500.values())  # 6.0

# Adjusted bands: Critical=40, High=20, Medium=10, Low=0
# Original bands (75/50/25) were unreachable due to escalation logic
# New bands based on achievable score range (max ~48)
BANDS = [(40.0, "Critical"), (20.0, "High"), (10.0, "Medium"), (0.0, "Low")]
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
    """
    Compute composite risk score.
    
    FIX: Normalize against total possible BIS weight (TOTAL_BIS_WEIGHT = 6.0)
    instead of measured weight. This makes scores comparable across samples
    with different parameter coverage.
    
    Zero values for parameters with detection limits (arsenic, e_coli, total_coliform)
    are treated as "below detection limit" and excluded from scoring.
    """
    weighted_sum = 0.0
    contributions: list[tuple[float, str]] = []
    results: dict[str, SeverityResult] = {}

    # Parameters where zero means "below detection limit"
    BELOW_DETECTION_PARAMS = {"arsenic", "e_coli", "total_coliform"}

    for key, (value, spec) in readings.items():
        # Skip zero values for below-detection-limit parameters
        if key in BELOW_DETECTION_PARAMS and value == 0.0:
            # Store as non-exceeded with zero severity
            results[key] = SeverityResult(0.0, False)
            continue
            
        result = parameter_severity(
            value,
            spec["acceptable"],
            spec.get("permissible"),
            spec.get("strategy", "threshold"),
        )
        results[key] = result
        weight = spec["weight"]
        weighted_sum += weight * result.severity
        if result.exceeded:
            contributions.append((result.severity * weight, key))

    if weighted_sum == 0:
        return 0.0, "Low", None

    # Normalize against TOTAL possible weight (6.0) to make scores comparable
    score = round((weighted_sum / TOTAL_BIS_WEIGHT) * 100, 2)
    worst = max(contributions)[1] if contributions else None
    return score, escalate_band(band_for(score), results), worst


def escalate_band(band: str, results: dict[str, "SeverityResult"]) -> str:
    """Only escalate for ACUTE_HAZARDS (arsenic, e_coli, total_coliform).
    Non-acute full breaches (iron, fluoride, tds, nitrate, sulphate) contribute
    to the score but don't force band escalation."""
    acute_full_breaches = [k for k, r in results.items() if r.severity >= 1.0 and k in ACUTE_HAZARDS]
    if not acute_full_breaches:
        return band
    # Acute hazards escalate to Critical
    return BAND_ORDER[max(BAND_ORDER.index(band), 3)]
