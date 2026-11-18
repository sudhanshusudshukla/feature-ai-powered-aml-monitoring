"""Risk domain models: country risk reference data."""
from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CountryRisk(Base):
    """Country risk reference data."""
    __tablename__ = "country_risk"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country_code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    country_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_high_risk: Mapped[bool] = mapped_column(Boolean, nullable=False)
    risk_rating: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
