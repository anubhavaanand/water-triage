from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def utcnow():
    return datetime.now(timezone.utc)


class State(Base):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    districts: Mapped[list["District"]] = relationship(back_populates="state")


class District(Base):
    __tablename__ = "districts"
    __table_args__ = (UniqueConstraint("state_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"))
    name: Mapped[str] = mapped_column(String(100))

    state: Mapped["State"] = relationship(back_populates="districts")
    villages: Mapped[list["Village"]] = relationship(back_populates="district")


class Village(Base):
    __tablename__ = "villages"
    __table_args__ = (UniqueConstraint("district_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    district_id: Mapped[int] = mapped_column(ForeignKey("districts.id"))
    name: Mapped[str] = mapped_column(String(150))
    block: Mapped[str | None] = mapped_column(String(150), nullable=True)
    panchayat: Mapped[str | None] = mapped_column(String(150), nullable=True)

    district: Mapped["District"] = relationship(back_populates="villages")
    samples: Mapped[list["WaterSample"]] = relationship(back_populates="village")


class BisParameter(Base):
    __tablename__ = "bis_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(50), unique=True)
    label: Mapped[str] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(30))
    acceptable_limit: Mapped[float]
    permissible_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight: Mapped[float]
    strategy: Mapped[str] = mapped_column(String(20), default="threshold")


class WaterSample(Base):
    __tablename__ = "water_samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    village_id: Mapped[int] = mapped_column(ForeignKey("villages.id"))
    source_type: Mapped[str] = mapped_column(String(50), default="handpump")
    collected_on: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lab_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    wqmis_ref: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    village: Mapped["Village"] = relationship(back_populates="samples")
    readings: Mapped[list["Reading"]] = relationship(
        back_populates="sample", cascade="all, delete-orphan"
    )
    risk_score: Mapped["RiskScore | None"] = relationship(
        back_populates="sample", cascade="all, delete-orphan", uselist=False
    )


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("water_samples.id"))
    parameter_key: Mapped[str] = mapped_column(String(50), index=True)
    value: Mapped[float]

    sample: Mapped["WaterSample"] = relationship(back_populates="readings")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("water_samples.id"), unique=True)
    score: Mapped[float]
    band: Mapped[str] = mapped_column(String(20), index=True)
    worst_parameter: Mapped[str | None] = mapped_column(String(50), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    sample: Mapped["WaterSample"] = relationship(back_populates="risk_score")


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(primary_key=True)
    village_id: Mapped[int] = mapped_column(ForeignKey("villages.id"))
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    action: Mapped[str] = mapped_column(String(300))
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class HistoricalContamination(Base):
    __tablename__ = "historical_contamination"

    id: Mapped[int] = mapped_column(primary_key=True)
    village_id: Mapped[int] = mapped_column(ForeignKey("villages.id"), index=True)
    parameter: Mapped[str] = mapped_column(String(60), index=True)
    year: Mapped[int] = mapped_column(index=True)
    registry: Mapped[str] = mapped_column(
        String(80), default="quality-affected-habitations"
    )
    habitation: Mapped[str | None] = mapped_column(String(200), nullable=True)
