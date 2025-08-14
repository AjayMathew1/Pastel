from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


# Category Schemas
class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color_hex: str = Field(default="#E6E0FF")
    icon_key: Optional[str] = None
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    color_hex: Optional[str] = None
    icon_key: Optional[str] = None
    sort_order: Optional[int] = None


class CategoryRead(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Activity Schemas
class ActivityBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category_id: int
    sort_order: int = 0


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    category_id: Optional[int] = None
    sort_order: Optional[int] = None


class ActivityRead(ActivityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Entry Schemas
class EntryBase(BaseModel):
    date: date
    duration_minutes: int = Field(gt=0, le=24 * 60)
    category_id: int
    activity_id: Optional[int] = None
    notes: Optional[str] = None

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v


class EntryCreate(EntryBase):
    pass


class EntryUpdate(BaseModel):
    date: Optional[date] = None
    duration_minutes: Optional[int] = Field(default=None, gt=0, le=24 * 60)
    category_id: Optional[int] = None
    activity_id: Optional[int] = None
    notes: Optional[str] = None


class EntryRead(EntryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Report Schemas
class CategoryTotal(BaseModel):
    category_id: int
    category_name: str
    category_color: str
    total_minutes: int


class ActivityTotal(BaseModel):
    activity_id: int
    activity_name: str
    category_id: int
    total_minutes: int


class SettingsRead(BaseModel):
    id: int
    rounding_mode: str
    rounding_increment: int
    week_start: str
    primary_hex: str
    accent_hex: str
    glass_alpha: int
    glass_blur_px: int

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    rounding_mode: str
    rounding_increment: int
    week_start: str
    primary_hex: str
    accent_hex: str
    glass_alpha: int
    glass_blur_px: int


