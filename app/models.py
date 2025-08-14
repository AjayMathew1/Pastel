from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    color_hex: Mapped[str] = mapped_column(String(7), nullable=False, default="#E6E0FF")
    icon_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    activities: Mapped[List["Activity"]] = relationship("Activity", back_populates="category")
    entries: Mapped[List["Entry"]] = relationship("Entry", back_populates="category")


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (UniqueConstraint("category_id", "name", name="uq_activity_per_category"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    category: Mapped[Category] = relationship("Category", back_populates="activities")
    entries: Mapped[List["Entry"]] = relationship("Entry", back_populates="activity")


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    activity_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("activities.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    activity: Mapped[Optional[Activity]] = relationship("Activity", back_populates="entries")
    category: Mapped[Category] = relationship("Category", back_populates="entries")


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rounding_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="none")  # none|up|down|nearest
    rounding_increment: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    week_start: Mapped[str] = mapped_column(String(8), nullable=False, default="monday")  # monday|sunday
    primary_hex: Mapped[str] = mapped_column(String(7), nullable=False, default="#7c83fd")
    accent_hex: Mapped[str] = mapped_column(String(7), nullable=False, default="#E6E0FF")
    glass_alpha: Mapped[float] = mapped_column(Integer, nullable=False, default=85)  # percent 0-100
    glass_blur_px: Mapped[int] = mapped_column(Integer, nullable=False, default=12)


