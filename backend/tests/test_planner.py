from datetime import date

import pytest

from agents import planner
from llm import LLMError


def test_business_days_skip_weekends():
    # 2026-07-10 is a Friday
    days = planner.business_days_from(date(2026, 7, 10), 3)
    assert [d.isoformat() for d in days] == ["2026-07-10", "2026-07-13", "2026-07-14"]


def test_assign_dates_never_lands_on_weekend():
    sessions = [{"topic": f"T{i}", "description": ""} for i in range(10)]
    dated = planner.assign_dates(sessions, total_days=30, start=date(2026, 7, 11))  # a Saturday
    assert all(date.fromisoformat(s["date"]).weekday() < 5 for s in dated)


def test_assign_dates_spread_and_order():
    sessions = [{"topic": f"T{i}", "description": ""} for i in range(5)]
    dated = planner.assign_dates(sessions, total_days=20, start=date(2026, 7, 13))
    dates = [s["date"] for s in dated]
    assert dates == sorted(dates)                      # chronological
    assert dated[0]["date"] == "2026-07-13"            # starts at window start
    assert len(set(dates)) == len(dates)               # no double-booked days


def test_assign_dates_truncates_to_window():
    sessions = [{"topic": f"T{i}", "description": ""} for i in range(50)]
    dated = planner.assign_dates(sessions, total_days=10, start=date(2026, 7, 13))
    assert len(dated) == 10


def test_extract_topics_dedupes_and_cleans(monkeypatch):
    monkeypatch.setattr(planner, "chat_json", lambda **kw: {
        "topics": ["  Graphs ", "graphs", "", 42, "Trees"],
    })
    assert planner.extract_topics("syllabus") == ["Graphs", "Trees"]


def test_extract_topics_rejects_bad_shape(monkeypatch):
    monkeypatch.setattr(planner, "chat_json", lambda **kw: {"nope": True})
    with pytest.raises(LLMError):
        planner.extract_topics("syllabus")


def test_generate_study_plan_dates_are_code_assigned(monkeypatch):
    monkeypatch.setattr(planner, "chat_json", lambda **kw: {
        "sessions": [
            {"topic": "Graphs", "description": "BFS/DFS", "date": "1999-01-01"},
            {"topic": "Trees", "description": "Traversals"},
        ],
    })
    plan = planner.generate_study_plan(["Graphs", "Trees"], total_days=10)
    assert len(plan) == 2
    # Any date the LLM hallucinates is discarded; scheduling is deterministic
    assert all(s["date"] != "1999-01-01" for s in plan)
    assert all(s["status"] == "pending" for s in plan)
