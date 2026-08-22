from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parameter_key: str
    value: float
    unit: str | None = None
    label: str | None = None


class RiskScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score: float
    band: str
    worst_parameter: str | None
    computed_at: datetime


class SampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    village: str
    district: str
    state: str
    source_type: str
    collected_on: datetime
    wqmis_ref: str | None


class SampleDetailOut(SampleOut):
    readings: list[ReadingOut]
    risk_score: RiskScoreOut | None


class DistrictSummary(BaseModel):
    id: int
    name: str
    state: str
    sample_count: int
    avg_score: float | None
    band_counts: dict[str, int]


class PriorityItem(BaseModel):
    rank: int
    sample_id: int
    village: str
    block: str | None
    district: str
    state: str
    score: float
    band: str
    worst_parameter: str | None
    collected_on: datetime


class StateCompare(BaseModel):
    state: str
    sample_count: int
    avg_score: float | None
    critical_count: int
    high_count: int
    top_exceedance_parameter: str | None


class CompareOut(BaseModel):
    states: list[StateCompare]
