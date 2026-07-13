"""Smoke tests for the Streamlit configuration comparison page."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_example_page_renders_expected_summary() -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app.py")).run(timeout=20)

    assert not app.exception
    assert app.title[0].value == "🦾 EmbodiedLab"
    assert [metric.value for metric in app.metric] == ["4", "2", "0", "0"]
    assert len(app.dataframe) == 1
    assert len(app.dataframe[0].value) == 6


def test_unchanged_fields_can_be_included() -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app.py")).run(timeout=20)
    app.checkbox(key="show_unchanged").check().run(timeout=20)

    assert not app.exception
    assert app.metric[3].value == "8"
    assert len(app.dataframe[0].value) == 14
