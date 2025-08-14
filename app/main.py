from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .database import Base, engine, get_db
from . import crud, models, schemas
from .utils.time_utils import round_minutes


app = FastAPI(title="Pastel Time Tracker", version="0.1.0")

# Create tables on startup if they don't exist
Base.metadata.create_all(bind=engine)


# Jinja2 setup
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_template(template_name: str, **context) -> HTMLResponse:
    # Inject settings for theming
    try:
        db: Optional[Session] = context.get("db")
        settings = crud.get_settings(db) if db else None
    except Exception:
        settings = None
    context.setdefault("settings", settings)
    template = jinja_env.get_template(template_name)
    return HTMLResponse(template.render(**context))


# Static files
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def get_today() -> date:
    return datetime.now().date()


@app.on_event("startup")
def seed_defaults() -> None:
    # Seed a few default categories if database is empty
    with next(get_db()) as db:  # type: ignore
        if not crud.list_categories(db):
            defaults = [
                ("Exercise", "#DFF5E1"),
                ("Reading", "#E0F2FF"),
                ("Work", "#E6E0FF"),
                ("Play", "#FFF4D6"),
            ]
            for name, color in defaults:
                crud.create_category(db, schemas.CategoryCreate(name=name, color_hex=color))

        # Seed some common activities if none exist
        if not crud.list_activities(db):
            cats = {c.name: c for c in crud.list_categories(db)}
            activity_defaults = [
                ("Work", ["Coding", "Writing", "Meetings"]),
                ("Exercise", ["Cardio", "Strength", "Yoga"]),
                ("Reading", ["Fiction", "Non-fiction"]),
                ("Play", ["Games", "Music", "Outdoors"]),
            ]
            for cat_name, names in activity_defaults:
                cat = cats.get(cat_name)
                if not cat:
                    continue
                for idx, n in enumerate(names):
                    try:
                        crud.create_activity(db, schemas.ActivityCreate(name=n, category_id=cat.id, sort_order=idx))
                    except Exception:
                        pass


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    today = get_today()
    entries = crud.list_entries(db, date_from=today, date_to=today)
    categories = crud.list_categories(db)
    activities = crud.list_activities(db)
    return render_template(
        "index.html",
        request=request,
        today=today,
        entries=entries,
        categories=categories,
        activities=activities,
        db=db,
    )


@app.post("/add-entry")
def add_entry(
    date_value: str = Form(...),
    activity_id: int = Form(...),
    duration_minutes: int = Form(...),
    notes: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    try:
        settings = crud.get_settings(db)
        duration_minutes = round_minutes(duration_minutes, settings.rounding_mode, settings.rounding_increment)
        # Derive category from activity
        act = crud.get_activity(db, activity_id)
        if not act:
            raise ValueError("Activity not found")
        payload = schemas.EntryCreate(
            date=date.fromisoformat(date_value),
            category_id=act.category_id,
            activity_id=activity_id,
            duration_minutes=duration_minutes,
            notes=notes,
        )
        crud.create_entry(db, payload)
    except Exception as exc:  # Validation or integrity errors
        raise HTTPException(status_code=400, detail=str(exc))
    return RedirectResponse(url="/", status_code=303)


@app.post("/delete-entry")
def delete_entry(entry_id: int = Form(...), db: Session = Depends(get_db)):
    ok = crud.delete_entry(db, entry_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Entry not found")
    return RedirectResponse(url="/", status_code=303)


@app.get("/weekly", response_class=HTMLResponse)
def weekly_view(week_of: Optional[str] = None, db: Session = Depends(get_db)) -> HTMLResponse:
    today = get_today()
    if week_of:
        start = date.fromisoformat(week_of)
    else:
        # find week start (Mon)
        start = today - timedelta(days=today.weekday())
    cat_rows, act_rows = crud.weekly_totals(db, start)
    return render_template(
        "weekly.html",
        week_start=start,
        category_rows=cat_rows,
        activity_rows=act_rows,
        db=db,
    )


@app.get("/monthly", response_class=HTMLResponse)
def monthly_view(month: Optional[str] = None, db: Session = Depends(get_db)) -> HTMLResponse:
    today = get_today()
    if month:
        year, mon = [int(x) for x in month.split("-")]
        start = date(year, mon, 1)
    else:
        start = date(today.year, today.month, 1)

    if start.month == 12:
        next_month = date(start.year + 1, 1, 1)
    else:
        next_month = date(start.year, start.month + 1, 1)
    end = next_month - timedelta(days=1)

    cat_rows, act_rows = crud.monthly_totals(db, start, end)
    return render_template(
        "monthly.html",
        month_start=start,
        category_rows=cat_rows,
        activity_rows=act_rows,
        db=db,
    )


@app.get("/manage/categories", response_class=HTMLResponse)
def manage_categories(db: Session = Depends(get_db)) -> HTMLResponse:
    categories = crud.list_categories(db)
    return render_template("manage_categories.html", categories=categories, db=db)


@app.post("/manage/categories/add")
def add_category(name: str = Form(...), color_hex: str = Form("#E6E0FF"), icon_key: Optional[str] = Form(None), db: Session = Depends(get_db)):
    payload = schemas.CategoryCreate(name=name, color_hex=color_hex, icon_key=icon_key)
    crud.create_category(db, payload)
    return RedirectResponse(url="/manage/categories", status_code=303)


@app.post("/manage/categories/delete")
def delete_category(category_id: int = Form(...), db: Session = Depends(get_db)):
    ok = crud.delete_category(db, category_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Cannot delete category in use")
    return RedirectResponse(url="/manage/categories", status_code=303)


@app.get("/manage/activities", response_class=HTMLResponse)
def manage_activities(category_id: Optional[int] = None, db: Session = Depends(get_db)) -> HTMLResponse:
    categories = crud.list_categories(db)
    activities = crud.list_activities(db, category_id=category_id)
    return render_template("manage_activities.html", categories=categories, activities=activities, selected_category_id=category_id, db=db)


@app.get("/settings", response_class=HTMLResponse)
def settings_page(db: Session = Depends(get_db)) -> HTMLResponse:
    settings = crud.get_settings(db)
    return render_template("settings.html", settings=settings, db=db)


@app.post("/settings")
def update_settings(
    rounding_mode: str = Form("none"),
    rounding_increment: int = Form(15),
    week_start: str = Form("monday"),
    primary_hex: str = Form("#7c83fd"),
    accent_hex: str = Form("#E6E0FF"),
    glass_alpha: int = Form(85),
    glass_blur_px: int = Form(12),
    db: Session = Depends(get_db),
):
    payload = schemas.SettingsUpdate(
        rounding_mode=rounding_mode,
        rounding_increment=rounding_increment,
        week_start=week_start,
        primary_hex=primary_hex,
        accent_hex=accent_hex,
        glass_alpha=glass_alpha,
        glass_blur_px=glass_blur_px,
    )
    crud.update_settings(db, payload)
    return RedirectResponse(url="/settings", status_code=303)


@app.post("/manage/activities/add")
def add_activity(name: str = Form(...), category_id: int = Form(...), db: Session = Depends(get_db)):
    payload = schemas.ActivityCreate(name=name, category_id=category_id)
    crud.create_activity(db, payload)
    return RedirectResponse(url=f"/manage/activities?category_id={category_id}", status_code=303)


@app.post("/manage/activities/delete")
def delete_activity(activity_id: int = Form(...), category_id: int = Form(...), db: Session = Depends(get_db)):
    ok = crud.delete_activity(db, activity_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Cannot delete activity in use")
    return RedirectResponse(url=f"/manage/activities?category_id={category_id}", status_code=303)


@app.get("/entries/export.csv")
def export_csv(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    d_from = date.fromisoformat(from_date) if from_date else None
    d_to = date.fromisoformat(to_date) if to_date else None
    # Materialize data to avoid lazy-load after session closes
    rows = []
    for e in crud.list_entries(db, date_from=d_from, date_to=d_to):
        rows.append(
            (
                e.id,
                str(e.date),
                e.category.name if e.category else "",
                e.activity.name if e.activity else "",
                e.duration_minutes,
                (e.notes or "").replace("\n", " ").replace(",", " "),
            )
        )

    def iter_rows():
        yield "id,date,category,activity,duration_minutes,notes\n"
        for r in rows:
            yield f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]}\n"

    filename = "time_entries.csv"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(iter_rows(), media_type="text/csv", headers=headers)


def _week_range(today: date, start_mode: str) -> date:
    # Monday=0, Sunday handling
    weekday = today.weekday()
    if start_mode == "sunday":
        # compute days since Sunday
        days_since_sun = (weekday + 1) % 7
        return today - timedelta(days=days_since_sun)
    return today - timedelta(days=weekday)


@app.get("/charts/daily", response_class=HTMLResponse)
def charts_daily(db: Session = Depends(get_db)) -> HTMLResponse:
    today = get_today()
    data = crud.activity_totals_in_range(db, today, today)
    return render_template("chart_pie.html", title="Daily Activity Breakdown", chart_data=data, db=db)


@app.get("/charts/weekly", response_class=HTMLResponse)
def charts_weekly(db: Session = Depends(get_db)) -> HTMLResponse:
    today = get_today()
    settings = crud.get_settings(db)
    start = _week_range(today, settings.week_start)
    end = start + timedelta(days=6)
    data = crud.activity_totals_in_range(db, start, end)
    return render_template("chart_pie.html", title="Weekly Activity Breakdown", chart_data=data, db=db)


@app.get("/charts/monthly", response_class=HTMLResponse)
def charts_monthly(db: Session = Depends(get_db)) -> HTMLResponse:
    today = get_today()
    start = date(today.year, today.month, 1)
    if start.month == 12:
        next_month = date(start.year + 1, 1, 1)
    else:
        next_month = date(start.year, start.month + 1, 1)
    end = next_month - timedelta(days=1)
    data = crud.activity_totals_in_range(db, start, end)
    return render_template("chart_pie.html", title="Monthly Activity Breakdown", chart_data=data, db=db)


