import json
import sqlite3
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from aegissoc.agent import investigate

app = FastAPI(title="AegisSOC-X", version="0.1.0")
DB = Path("aegissoc.db")
MODEL = Path("artifacts/rf_model.joblib")
METRICS = Path("artifacts/metrics.json")


def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        score REAL NOT NULL, event_json TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'open', summary TEXT NOT NULL DEFAULT ''
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER, action TEXT NOT NULL, detail TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    db.commit()
    return db


class PredictionRequest(BaseModel):
    features: dict[str, float]


class CaseRequest(BaseModel):
    score: float = Field(ge=0, le=1)
    event: dict


class ReviewRequest(BaseModel):
    decision: str
    reviewer: str = Field(min_length=2, max_length=80)


@app.get("/health")
def health():
    return {"status": "ok", "model_ready": MODEL.exists() and METRICS.exists()}


@app.post("/predict")
def predict(payload: PredictionRequest):
    if not MODEL.exists() or not METRICS.exists():
        raise HTTPException(503, "Train the model first")
    schema = json.loads(METRICS.read_text())["features"]
    if set(payload.features) != set(schema):
        raise HTTPException(422, {"expected_features": schema})
    model = joblib.load(MODEL)  # Only load artifacts created locally by trusted training code.
    row = pd.DataFrame([payload.features], columns=schema)
    score = float(model.predict_proba(row)[0, 1])
    return {
        "score": score,
        "suspicious": score >= 0.5,
        "threshold": 0.5,
        "model": "rf-v1",
        "dataset": json.loads(METRICS.read_text())["dataset"],
    }


@app.post("/cases")
def create_case(payload: CaseRequest):
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO cases (score, event_json) VALUES (?, ?)",
            (payload.score, json.dumps(payload.event)),
        )
        case_id = cursor.lastrowid
        db.execute(
            "INSERT INTO audit (case_id, action, detail) VALUES (?, ?, ?)",
            (case_id, "case_created", "Submitted by demo API"),
        )
    return {"case_id": case_id, "status": "open"}


@app.get("/cases")
def cases():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM cases ORDER BY id DESC LIMIT 100")]


@app.get("/cases/{case_id}")
def get_case(case_id: int):
    with connect() as db:
        row = db.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Case not found")
    return dict(row)


@app.post("/cases/{case_id}/investigate")
def investigate_case(case_id: int):
    case = get_case(case_id)
    result = investigate(case)
    with connect() as db:
        db.execute(
            "UPDATE cases SET summary=?, status=? WHERE id=?",
            (result["summary"], "awaiting_review", case_id),
        )
        db.execute(
            "INSERT INTO audit (case_id, action, detail) VALUES (?, ?, ?)",
            (case_id, "investigated", "Bounded LangGraph workflow completed"),
        )
    return {
        "case_id": case_id,
        "summary": result["summary"],
        "evidence": result["evidence"],
        "status": "awaiting_review",
    }


@app.post("/cases/{case_id}/review")
def review_case(case_id: int, payload: ReviewRequest):
    case = get_case(case_id)
    if case["status"] != "awaiting_review":
        raise HTTPException(409, "Investigate case before review")
    if payload.decision not in {"benign", "confirmed", "needs_more_evidence"}:
        raise HTTPException(422, "Invalid decision")
    with connect() as db:
        db.execute("UPDATE cases SET status=? WHERE id=?", (payload.decision, case_id))
        db.execute(
            "INSERT INTO audit (case_id, action, detail) VALUES (?, ?, ?)",
            (
                case_id,
                "analyst_review",
                json.dumps({"reviewer": payload.reviewer, "decision": payload.decision}),
            ),
        )
    return {"case_id": case_id, "status": payload.decision}


@app.get("/audit")
def audit():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 100")]
