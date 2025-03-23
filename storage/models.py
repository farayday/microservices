from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, DateTime, Float, func
import uuid


class Base(DeclarativeBase):
    pass


class ConditionsReport(Base):
    __tablename__ = "conditions_report"
    id = mapped_column(Integer, primary_key=True)
    device_id = mapped_column(String(50), nullable=False)
    location = mapped_column(String(100), nullable=False)
    vehicle_count = mapped_column(Integer, nullable=False)
    average_speed = mapped_column(Float, nullable=False)
    timestamp = mapped_column(String(100), nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())
    trace_id = mapped_column(String(36), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "location": self.location,
            "vehicle_count": self.vehicle_count,
            "average_speed": self.average_speed,
            "timestamp": self.timestamp,
            "date_created": (
                self.date_created.isoformat() if self.date_created else None
            ),
            "trace_id": self.trace_id,
        }


class IncidentReport(Base):
    __tablename__ = "incident_report"
    id = mapped_column(Integer, primary_key=True)
    reporter_id = mapped_column(String(50), nullable=False)
    location = mapped_column(String(100), nullable=False)
    incident_type = mapped_column(String(50), nullable=False)
    description = mapped_column(String(250), nullable=False)
    timestamp = mapped_column(String(100), nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())
    trace_id = mapped_column(String(36), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "reporter_id": self.reporter_id,
            "location": self.location,
            "incident_type": self.incident_type,
            "description": self.description,
            "timestamp": self.timestamp,
            "date_created": (
                self.date_created.isoformat() if self.date_created else None
            ),
            "trace_id": self.trace_id,
        }
