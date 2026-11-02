"""CrimeSight: historical crime-data analytics and educational ML prototype.

This application analyses aggregate records supplied with the project. It is not
an incident-forecasting system and must not be used for policing or high-impact decisions.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import logging
import os

import numpy as np
import pandas as pd
from flask import Flask, jsonify, make_response, render_template, request
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

BASE = Path(__file__).resolve().parent
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("crimesight")


def load_data() -> tuple[pd.DataFrame, str, int]:
    """Load and normalize common crime dataset header variations."""
    excel, csv = BASE / "crime1_data.xlsx", BASE / "crime_data.csv"
    if excel.exists():
        raw, source = pd.read_excel(excel), "Excel workbook"
    elif csv.exists():
        raw, source = pd.read_csv(csv), "CSV dataset"
    else:
        raise FileNotFoundError(
            "No dataset found. Place crime1_data.xlsx or crime_data.csv beside app.py."
        )

    raw.columns = [str(c).strip() for c in raw.columns]
    rename: dict[str, str] = {}
    for col in raw.columns:
        low = " ".join(col.lower().replace("_", " ").split())
        if low in {"city", "location", "district", "place", "state", "area"}:
            rename[col] = "Location"
        elif low in {"year", "date", "crime year"} or low.startswith("year "):
            rename[col] = "Year"
        elif low in {"type", "crime type", "crime", "category", "crime category"}:
            rename[col] = "Type"
        elif "population" in low:
            # Preserve the original units in the source data, including "in Lakhs".
            rename[col] = "Population"
        elif "crime rate" in low or low == "rate":
            rename[col] = "Crime Rate"

    raw = raw.rename(columns=rename)
    # If the workbook has duplicate aliases, keep the first recognized column.
    raw = raw.loc[:, ~raw.columns.duplicated()].copy()
    required = {"Year", "Location", "Type"}
    if not required.issubset(raw.columns):
        raise ValueError(
            "Dataset requires Year, Location/City, and Type/Crime Category columns. "
            f"Found: {', '.join(map(str, raw.columns))}"
        )
    for col in ("Population", "Crime Rate"):
        if col not in raw.columns:
            raw[col] = np.nan

    raw["Year"] = pd.to_numeric(raw["Year"], errors="coerce")
    raw["Location"] = raw["Location"].astype("string").str.strip()
    raw["Type"] = raw["Type"].astype("string").str.strip()
    raw["Population"] = pd.to_numeric(raw["Population"], errors="coerce")
    raw["Crime Rate"] = pd.to_numeric(raw["Crime Rate"], errors="coerce")
    before = len(raw)
    raw = raw.dropna(subset=["Year", "Location", "Type"])
    raw = raw[(raw["Location"] != "") & (raw["Type"] != "")]
    raw = raw.replace([np.inf, -np.inf], np.nan)
    raw["Year"] = raw["Year"].astype(int)
    raw = raw.reset_index(drop=True)
    if raw.empty:
        raise ValueError("The dataset contains no usable rows after data cleaning.")
    return raw, source, before - len(raw)


df, DATA_SOURCE, REMOVED_ROWS = load_data()
locations = sorted(df["Location"].astype(str).unique().tolist())
crime_types = sorted(df["Type"].astype(str).unique().tolist())
year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
features = ["Year", "Location", "Population"]
X, y = df[features].copy(), df["Type"].astype(str)


def make_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), ["Year", "Population"]),
            ("location", Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore")),
            ]), ["Location"]),
        ],
        remainder="drop",
    )


def classifier_pipeline(kind: str = "forest", trees: int = 180) -> Pipeline:
    classifier = (ExtraTreesClassifier if kind == "extra" else RandomForestClassifier)(
        n_estimators=trees,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42 if kind == "forest" else 24,
        n_jobs=-1,
    )
    return Pipeline([("prep", make_preprocessor()), ("classifier", classifier)])


metrics = {"accuracy": None, "f1": None, "test_size": 0, "note": "Insufficient data for evaluation."}
if len(df) >= 10 and y.nunique() > 1:
    try:
        counts = y.value_counts()
        stratify = y if counts.min() >= 2 and counts.size > 1 else None
        Xtr, Xte, ytr, yte = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )
        eval_model = classifier_pipeline(trees=100)
        eval_model.fit(Xtr, ytr)
        yp = eval_model.predict(Xte)
        metrics = {
            "accuracy": round(float(accuracy_score(yte, yp)) * 100, 1),
            "f1": round(float(f1_score(yte, yp, average="weighted", zero_division=0)) * 100, 1),
            "test_size": int(len(yte)),
            "note": "Random hold-out evaluation; not a future-year benchmark.",
        }
    except Exception as exc:
        log.warning("Classification evaluation skipped: %s", exc)

model = classifier_pipeline("forest", 220)
extra_model = classifier_pipeline("extra", 180)
model.fit(X, y)
extra_model.fit(X, y)

rate_df = df.dropna(subset=["Crime Rate"]).copy()
rate_model = None
rate_metrics = {"mae": None, "r2": None, "samples": int(len(rate_df))}
if len(rate_df) >= 10 and rate_df["Crime Rate"].nunique() > 1:
    try:
        rx, ry = rate_df[features].copy(), rate_df["Crime Rate"].astype(float)
        if len(rate_df) >= 20:
            xtr, xte, ytr, yte = train_test_split(rx, ry, test_size=0.2, random_state=42)
            reg_eval = Pipeline([
                ("prep", make_preprocessor()),
                ("regressor", RandomForestRegressor(n_estimators=120, min_samples_leaf=2, random_state=42, n_jobs=-1)),
            ])
            reg_eval.fit(xtr, ytr)
            rpred = reg_eval.predict(xte)
            rate_metrics["mae"] = round(float(mean_absolute_error(yte, rpred)), 3)
            rate_metrics["r2"] = round(float(r2_score(yte, rpred)), 3) if len(yte) > 1 else None
        rate_model = Pipeline([
            ("prep", make_preprocessor()),
            ("regressor", RandomForestRegressor(n_estimators=180, min_samples_leaf=2, random_state=42, n_jobs=-1)),
        ])
        rate_model.fit(rx, ry)
    except Exception as exc:
        log.warning("Rate model skipped: %s", exc)

records_by_year = df.groupby("Year").size().sort_index()
type_counts = df["Type"].value_counts().head(10)
loc_counts = df["Location"].value_counts().head(10)
rate_by_year = rate_df.groupby("Year")["Crime Rate"].mean().sort_index() if len(rate_df) else pd.Series(dtype=float)


def dashboard_context(error=None, selected_location="", selected_year=""):
    return dict(
        locations=locations, crime_types=crime_types, data_source=DATA_SOURCE,
        record_count=len(df), location_count=int(df.Location.nunique()), type_count=int(df.Type.nunique()),
        year_min=year_min, year_max=year_max, metrics=metrics, rate_metrics=rate_metrics,
        year_labels=[int(v) for v in records_by_year.index], year_values=[int(v) for v in records_by_year.values],
        type_labels=type_counts.index.astype(str).tolist(), type_values=[int(v) for v in type_counts.values],
        location_labels=loc_counts.index.astype(str).tolist(), location_values=[int(v) for v in loc_counts.values],
        rate_labels=[int(v) for v in rate_by_year.index], rate_values=[round(float(v), 3) for v in rate_by_year.values],
        error=error, selected_location=selected_location, selected_year=selected_year, removed_rows=REMOVED_ROWS,
    )


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


@app.route("/")
def home():
    return render_template("index.html", **dashboard_context())


@app.route("/predict", methods=["POST"])
def predict():
    location = request.form.get("location", "").strip()
    year_raw = request.form.get("year", "").strip()
    try:
        if location not in locations:
            raise ValueError("Select a location from the supplied dataset.")
        year = int(year_raw)
        if not 1900 <= year <= 2100:
            raise ValueError("Enter a year between 1900 and 2100.")
        subset = df[df["Location"].astype(str) == location]
        population = float(subset["Population"].dropna().median()) if subset["Population"].notna().any() else np.nan
        row = pd.DataFrame([{"Year": year, "Location": location, "Population": population}], columns=features)
        pred1, pred2 = str(model.predict(row)[0]), str(extra_model.predict(row)[0])
        probabilities = model.predict_proba(row)[0]
        classes = model.named_steps["classifier"].classes_
        ranked = sorted(((str(c), float(v)) for c, v in zip(classes, probabilities)), key=lambda item: item[1], reverse=True)
        prediction = Counter([pred1, pred2]).most_common(1)[0][0]
        confidence = round(max(probabilities) * 100, 1)
        historical = subset[subset["Year"] == year]
        history = historical.head(50).to_dict("records")
        for item in history:
            for key, value in item.items():
                if pd.isna(value): item[key] = None
                elif isinstance(value, (np.integer,)): item[key] = int(value)
                elif isinstance(value, (np.floating,)): item[key] = float(value)
        trend = subset.groupby("Year").size().sort_index()
        rate_estimate = round(max(0.0, float(rate_model.predict(row)[0])), 3) if rate_model is not None else None
        return render_template(
            "result.html", location=location, year=year, prediction=prediction, pred1=pred1, pred2=pred2,
            confidence=confidence, ranked=ranked[:7], history=history, history_count=int(len(historical)),
            trend_labels=[int(v) for v in trend.index], trend_values=[int(v) for v in trend.values],
            year_min=year_min, year_max=year_max, data_source=DATA_SOURCE, metrics=metrics,
            rate_estimate=rate_estimate, rate_metrics=rate_metrics,
            population_used=None if pd.isna(population) else population, has_exact_year=not historical.empty,
        )
    except (ValueError, TypeError) as exc:
        return render_template("index.html", **dashboard_context(str(exc), location, year_raw)), 400
    except Exception:
        log.exception("Prediction failed")
        return render_template("index.html", **dashboard_context(
            "The analysis could not be completed. Check the dataset and application logs.", location, year_raw
        )), 500


@app.route("/api/summary")
def api_summary():
    return jsonify({
        "application": "CrimeSight", "status": "ok", "records": int(len(df)),
        "locations": int(df.Location.nunique()), "crime_categories": int(df.Type.nunique()),
        "year_range": {"min": year_min, "max": year_max}, "source": DATA_SOURCE,
        "removed_invalid_rows": int(REMOVED_ROWS),
        "category_distribution": {str(k): int(v) for k, v in df.Type.value_counts().items()},
        "rate_model_available": rate_model is not None,
    })


@app.route("/api/records")
def api_records():
    try:
        location = request.args.get("location", "").strip()
        year = request.args.get("year", "").strip()
        category = request.args.get("category", "").strip()
        limit = min(max(int(request.args.get("limit", 100)), 1), 500)
        out = df.copy()
        if location: out = out[out.Location.astype(str) == location]
        if year: out = out[out.Year == int(year)]
        if category: out = out[out.Type.astype(str) == category]
        out = out.head(limit).astype(object).where(pd.notna(out.head(limit)), None)
        records = out.to_dict("records")
        # Convert numpy scalar values into standard JSON-native Python types.
        for record in records:
            for key, value in record.items():
                if isinstance(value, np.integer): record[key] = int(value)
                elif isinstance(value, np.floating): record[key] = float(value)
        return jsonify({"count_returned": len(records), "limit": limit, "records": records})
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid year or limit parameter."}), 400


@app.route("/download")
def download_csv():
    location = request.args.get("location", "").strip()
    year = request.args.get("year", "").strip()
    out = df.copy()
    if location:
        if location not in locations: return jsonify({"error": "Unknown location filter."}), 400
        out = out[out.Location.astype(str) == location]
    if year:
        try: out = out[out.Year == int(year)]
        except ValueError: return jsonify({"error": "Invalid year filter."}), 400
    response = make_response(out.to_csv(index=False))
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=crimesight_historical_records.csv"
    return response


@app.route("/health")
def health():
    return jsonify({"status": "ok", "dataset_loaded": not df.empty, "records": int(len(df))})


@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Endpoint not found."}), 404
    return "Page not found. <a href='/'>Return to CrimeSight dashboard</a>.", 404


if __name__ == "__main__":
    # Set CRIMESIGHT_HOST/PORT only when needed; debug mode is intentionally disabled.
    app.run(host=os.getenv("CRIMESIGHT_HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")), debug=False)
