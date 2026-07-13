"""Unit tests for the first EmbodiedLab vertical slice."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from embodiedlab.config_diff import (
    compare_configs,
    load_config,
    load_config_text,
    render_json,
    render_markdown,
    resolve_safe_output,
    summarize,
)


ROOT = Path(__file__).resolve().parents[1]


def test_compare_nested_configs_reports_each_status() -> None:
    baseline = {
        "training": {"batch_size": 64, "steps": 1000},
        "model": {"backend": "old"},
        "removed": True,
    }
    candidate = {
        "training": {"batch_size": 128, "steps": 1000},
        "model": {"backend": "new"},
        "added": ["task_a"],
    }

    entries = compare_configs(baseline, candidate, include_unchanged=True)
    by_path = {entry.path: entry for entry in entries}

    assert by_path["training.batch_size"].status == "changed"
    assert by_path["training.steps"].status == "unchanged"
    assert by_path["added"].status == "added"
    assert by_path["removed"].status == "removed"
    assert summarize(entries) == {
        "added": 1,
        "removed": 1,
        "changed": 2,
        "unchanged": 1,
        "total": 5,
    }


def test_type_change_is_reported_even_when_values_compare_equal() -> None:
    entries = compare_configs({"value": 1}, {"value": True})
    assert len(entries) == 1
    assert entries[0].status == "changed"


def test_load_yaml_and_json_examples() -> None:
    baseline = load_config(ROOT / "examples" / "configs" / "baseline.yaml")
    assert baseline["training"]["global_batch_size"] == 128

    tmp_dir = ROOT / "tmp" / "tests"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    json_path = tmp_dir / "sample.json"
    json_path.write_text(json.dumps({"seed": 42}), encoding="utf-8")
    try:
        assert load_config(json_path) == {"seed": 42}
    finally:
        json_path.unlink(missing_ok=True)


def test_non_mapping_root_is_rejected() -> None:
    tmp_dir = ROOT / "tmp" / "tests"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / "list-root.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    try:
        with pytest.raises(ValueError, match="root must be"):
            load_config(path)
    finally:
        path.unlink(missing_ok=True)


def test_load_uploaded_config_text() -> None:
    assert load_config_text("seed: 42\n", "uploaded.yaml") == {"seed": 42}
    assert load_config_text('{"seed": 7}', "uploaded.json") == {"seed": 7}

    with pytest.raises(ValueError, match="Unable to parse uploaded.yaml"):
        load_config_text("training: [", "uploaded.yaml")

    with pytest.raises(ValueError, match="Unsupported config type"):
        load_config_text("seed = 42", "uploaded.toml")


def test_reports_contain_summary_and_paths() -> None:
    entries = compare_configs({"loss": {"world": 0.1}}, {"loss": {"world": 0.2}})
    markdown = render_markdown(entries, "old.yaml", "new.yaml")
    json_report = json.loads(render_json(entries, "old.yaml", "new.yaml"))

    assert "`loss.world`" in markdown
    assert json_report["summary"]["changed"] == 1
    assert json_report["differences"][0]["path"] == "loss.world"


def test_output_path_must_stay_inside_project() -> None:
    inside = resolve_safe_output(ROOT / "outputs" / "report.md", ROOT)
    assert inside == ROOT / "outputs" / "report.md"

    with pytest.raises(ValueError, match="inside project root"):
        resolve_safe_output(ROOT.parent / "outside.md", ROOT)
