"""Synthetic water sample generator.

Encodes the contamination signatures observed in WQMIS WQ6 summary reports
(up report contaminent wise.pdf / bihar report contaminent wise.pdf):
  Unnao, Ferozabad -> fluoride;  Hardoi -> E. coli;  Katihar -> iron;
  Araria -> turbidity;  Saharsa (provisional 6th district) -> trace arsenic.
Doubles as the shape-reference for the future WQ4 ETL parser.
"""

import random
from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass
class SyntheticReading:
    parameter_key: str
    value: float


@dataclass
class SyntheticSample:
    state: str
    district: str
    village: str
    block: str | None
    source_type: str
    collected_on: date
    lab_name: str | None
    wqmis_ref: str
    readings: list[SyntheticReading] = field(default_factory=list)


BASE_RANGES = {
    "ph": (6.8, 7.7),
    "tds": (280.0, 650.0),
    "nitrate": (5.0, 38.0),
    "iron": (0.05, 0.28),
    "turbidity": (0.4, 1.8),
    "fluoride": (0.3, 0.95),
    "arsenic": (0.0, 0.008),
}

SOURCES = ["handpump", "tap water", "dug well", "submersible"]
LABS = ["District Lab", "State Lab", "FTK (field)", "NABL Lab"]


def _uniform(rng: random.Random, low: float, high: float, digits: int = 2) -> float:
    return round(rng.uniform(low, high), digits)


def _maybe_elevated(
    rng: random.Random,
    key: str,
    prob: float,
    elevated_range: tuple[float, float],
    digits: int = 2,
) -> list[SyntheticReading]:
    if rng.random() < prob:
        return [
            SyntheticReading(key, _uniform(rng, *elevated_range, digits))
        ]
    return []


def _baseline(rng: random.Random, skip: set[str]) -> list[SyntheticReading]:
    out = []
    for key, (low, high) in BASE_RANGES.items():
        if key in skip:
            continue
        out.append(SyntheticReading(key, _uniform(rng, low, high)))
    return out


PROFILES = {
    "Unnao": {"block": ["Hasanganj", "Safipur", "Purwa", "Bighapur"], "signature": ("fluoride", 0.55, (1.05, 2.20))},
    "Ferozabad": {"block": ["Jasrana", "Shikohabad", "Sirsaganj"], "signature": ("fluoride", 0.62, (1.30, 2.60))},
    "Hardoi": {"block": ["Sandila", "Bilgram", "Mallawan"], "signature": ("e_coli", 0.35, (4.0, 85.0))},
    "Katihar": {"block": ["Barsoi", "Azamnagar", "Kadwa"], "signature": ("iron", 0.50, (0.32, 1.30))},
    "Araria": {"block": ["Forbesganj", "Jokihat", "Raniganj"], "signature": ("turbidity", 0.28, (1.5, 9.0))},
    "Saharsa": {"block": ["Kahra", "Mahishi", "Saur Bazar"], "signature": ("arsenic", 0.16, (0.011, 0.06))},
}

STATES = {
    "Unnao": "Uttar Pradesh",
    "Ferozabad": "Uttar Pradesh",
    "Hardoi": "Uttar Pradesh",
    "Katihar": "Bihar",
    "Araria": "Bihar",
    "Saharsa": "Bihar",
}

SAMPLES_PER_VILLAGE = 2


def generate_samples(seed: int = 42, samples_per_village: int = SAMPLES_PER_VILLAGE) -> list[SyntheticSample]:
    rng = random.Random(seed)
    today = date(2026, 8, 15)
    samples: list[SyntheticSample] = []
    counter = 0

    for district, profile in PROFILES.items():
        sig_key, sig_prob, sig_range = profile["signature"]
        for b_idx, block in enumerate(profile["block"], start=1):
            for v_idx in range(1, 4):
                village = f"{block} Ward {v_idx}"
                for s_idx in range(samples_per_village):
                    counter += 1
                    collected = today - timedelta(days=rng.randint(1, 90))
                    sample = SyntheticSample(
                        state=STATES[district],
                        district=district,
                        village=village,
                        block=block,
                        source_type=rng.choice(SOURCES),
                        collected_on=collected,
                        lab_name=rng.choice(LABS),
                        wqmis_ref=f"SYN-{district[:3].upper()}-{counter:04d}",
                    )
                    if sig_key == "e_coli":
                        sample.readings.extend(_baseline(rng, skip={"e_coli"}))
                        sample.readings.extend(
                            _maybe_elevated(rng, "e_coli", sig_prob, sig_range, digits=0)
                        )
                    else:
                        skip = {k for k in BASE_RANGES if k == sig_key}
                        sample.readings.extend(_baseline(rng, skip=skip))
                        sample.readings.extend(
                            _maybe_elevated(rng, sig_key, sig_prob, sig_range)
                        )
                    samples.append(sample)

    return samples
