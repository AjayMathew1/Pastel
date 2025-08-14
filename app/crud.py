from __future__ import annotations

from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas


# Categories
def list_categories(db: Session) -> List[models.Category]:
    stmt = select(models.Category).order_by(models.Category.sort_order, models.Category.name)
    return list(db.scalars(stmt).all())


def get_category(db: Session, category_id: int) -> Optional[models.Category]:
    return db.get(models.Category, category_id)


def create_category(db: Session, data: schemas.CategoryCreate) -> models.Category:
    category = models.Category(
        name=data.name,
        color_hex=data.color_hex,
        icon_key=data.icon_key,
        sort_order=data.sort_order,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, data: schemas.CategoryUpdate) -> Optional[models.Category]:
    category = get_category(db, category_id)
    if not category:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> bool:
    category = get_category(db, category_id)
    if not category:
        return False
    # Prevent deletion if referenced by entries or activities
    entries_count = db.scalar(select(func.count()).select_from(models.Entry).where(models.Entry.category_id == category_id))
    activities_count = db.scalar(select(func.count()).select_from(models.Activity).where(models.Activity.category_id == category_id))
    if entries_count or activities_count:
        return False
    db.delete(category)
    db.commit()
    return True


# Activities
def list_activities(db: Session, category_id: Optional[int] = None) -> List[models.Activity]:
    stmt = select(models.Activity)
    if category_id is not None:
        stmt = stmt.where(models.Activity.category_id == category_id)
    stmt = stmt.order_by(models.Activity.category_id, models.Activity.sort_order, models.Activity.name)
    return list(db.scalars(stmt).all())


def get_activity(db: Session, activity_id: int) -> Optional[models.Activity]:
    return db.get(models.Activity, activity_id)


def create_activity(db: Session, data: schemas.ActivityCreate) -> models.Activity:
    activity = models.Activity(
        name=data.name,
        category_id=data.category_id,
        sort_order=data.sort_order,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def update_activity(db: Session, activity_id: int, data: schemas.ActivityUpdate) -> Optional[models.Activity]:
    activity = get_activity(db, activity_id)
    if not activity:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(activity, field, value)
    db.commit()
    db.refresh(activity)
    return activity


def delete_activity(db: Session, activity_id: int) -> bool:
    activity = get_activity(db, activity_id)
    if not activity:
        return False
    # Prevent deletion if referenced by entries
    entries_count = db.scalar(select(func.count()).select_from(models.Entry).where(models.Entry.activity_id == activity_id))
    if entries_count:
        return False
    db.delete(activity)
    db.commit()
    return True


# Entries
def list_entries(
    db: Session,
    *,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category_id: Optional[int] = None,
    activity_id: Optional[int] = None,
) -> List[models.Entry]:
    stmt = select(models.Entry)
    if date_from is not None:
        stmt = stmt.where(models.Entry.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(models.Entry.date <= date_to)
    if category_id is not None:
        stmt = stmt.where(models.Entry.category_id == category_id)
    if activity_id is not None:
        stmt = stmt.where(models.Entry.activity_id == activity_id)
    stmt = stmt.order_by(models.Entry.date.desc(), models.Entry.id.desc())
    return list(db.scalars(stmt).all())


def get_entry(db: Session, entry_id: int) -> Optional[models.Entry]:
    return db.get(models.Entry, entry_id)


def create_entry(db: Session, data: schemas.EntryCreate) -> models.Entry:
    # Enforce category/activity consistency if both provided
    if data.activity_id is not None:
        activity = get_activity(db, data.activity_id)
        if not activity:
            raise ValueError("Activity not found")
        if activity.category_id != data.category_id:
            raise ValueError("Activity does not belong to the provided category")

    entry = models.Entry(
        activity_id=data.activity_id,
        category_id=data.category_id,
        date=data.date,
        duration_minutes=data.duration_minutes,
        notes=data.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_entry(db: Session, entry_id: int, data: schemas.EntryUpdate) -> Optional[models.Entry]:
    entry = get_entry(db, entry_id)
    if not entry:
        return None
    payload = data.model_dump(exclude_unset=True)

    # If both are present or either changes, enforce consistency
    new_category_id = payload.get("category_id", entry.category_id)
    new_activity_id = payload.get("activity_id", entry.activity_id)
    if new_activity_id is not None:
        activity = get_activity(db, new_activity_id)
        if not activity:
            raise ValueError("Activity not found")
        if activity.category_id != new_category_id:
            raise ValueError("Activity does not belong to the provided category")

    for field, value in payload.items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


def delete_entry(db: Session, entry_id: int) -> bool:
    entry = get_entry(db, entry_id)
    if not entry:
        return False
    db.delete(entry)
    db.commit()
    return True


# Reports
def weekly_totals(db: Session, week_start: date) -> Tuple[List[Tuple], List[Tuple]]:
    week_end = week_start.replace()  # date object; compute end as +6 days
    from datetime import timedelta

    week_end = week_start + timedelta(days=6)

    # Category totals
    cat_stmt = (
        select(
            models.Category.id,
            models.Category.name,
            models.Category.color_hex,
            func.coalesce(func.sum(models.Entry.duration_minutes), 0),
        )
        .join(models.Entry, models.Entry.category_id == models.Category.id, isouter=True)
        .where(models.Entry.date.between(week_start, week_end))
        .group_by(models.Category.id)
        .order_by(models.Category.sort_order, models.Category.name)
    )
    category_rows = list(db.execute(cat_stmt).all())

    # Activity totals
    act_stmt = (
        select(
            models.Activity.id,
            models.Activity.name,
            models.Activity.category_id,
            func.coalesce(func.sum(models.Entry.duration_minutes), 0),
        )
        .join(models.Entry, models.Entry.activity_id == models.Activity.id, isouter=True)
        .where(models.Entry.date.between(week_start, week_end))
        .group_by(models.Activity.id)
        .order_by(models.Activity.category_id, models.Activity.sort_order, models.Activity.name)
    )
    activity_rows = list(db.execute(act_stmt).all())

    return category_rows, activity_rows


def monthly_totals(db: Session, month_start: date, month_end: date) -> Tuple[List[Tuple], List[Tuple]]:
    # Category totals
    cat_stmt = (
        select(
            models.Category.id,
            models.Category.name,
            models.Category.color_hex,
            func.coalesce(func.sum(models.Entry.duration_minutes), 0),
        )
        .join(models.Entry, models.Entry.category_id == models.Category.id, isouter=True)
        .where(models.Entry.date.between(month_start, month_end))
        .group_by(models.Category.id)
        .order_by(models.Category.sort_order, models.Category.name)
    )
    category_rows = list(db.execute(cat_stmt).all())

    # Activity totals
    act_stmt = (
        select(
            models.Activity.id,
            models.Activity.name,
            models.Activity.category_id,
            func.coalesce(func.sum(models.Entry.duration_minutes), 0),
        )
        .join(models.Entry, models.Entry.activity_id == models.Activity.id, isouter=True)
        .where(models.Entry.date.between(month_start, month_end))
        .group_by(models.Activity.id)
        .order_by(models.Activity.category_id, models.Activity.sort_order, models.Activity.name)
    )
    activity_rows = list(db.execute(act_stmt).all())

    return category_rows, activity_rows


def activity_totals_in_range(db: Session, start_date: date, end_date: date) -> List[Tuple[str, int]]:
    # Totals for entries with an activity
    act_stmt = (
        select(models.Activity.name, func.coalesce(func.sum(models.Entry.duration_minutes), 0))
        .join(models.Entry, models.Entry.activity_id == models.Activity.id)
        .where(models.Entry.date.between(start_date, end_date))
        .group_by(models.Activity.id)
        .having(func.coalesce(func.sum(models.Entry.duration_minutes), 0) > 0)
        .order_by(func.sum(models.Entry.duration_minutes).desc())
    )
    results: List[Tuple[str, int]] = [(name, int(total or 0)) for name, total in db.execute(act_stmt).all()]

    # Totals for entries without an activity (unassigned)
    unassigned_total = db.scalar(
        select(func.coalesce(func.sum(models.Entry.duration_minutes), 0)).where(
            models.Entry.activity_id.is_(None), models.Entry.date.between(start_date, end_date)
        )
    )
    if unassigned_total and int(unassigned_total) > 0:
        results.append(("Unassigned", int(unassigned_total)))

    return results


# Settings
def get_settings(db: Session) -> models.Settings:
    settings = db.get(models.Settings, 1)
    if settings is None:
        settings = models.Settings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_settings(db: Session, data: schemas.SettingsUpdate) -> models.Settings:
    settings = get_settings(db)
    payload = data.model_dump()
    for field, value in payload.items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return settings


