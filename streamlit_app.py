"""Interactive configuration comparison UI for EmbodiedLab."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import yaml


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from embodiedlab.config_diff import (  # noqa: E402
    DiffEntry,
    compare_configs,
    load_config,
    load_config_text,
    render_json,
    render_markdown,
    summarize,
)


EXAMPLE_BASELINE = ROOT / "examples" / "configs" / "baseline.yaml"
EXAMPLE_CANDIDATE = ROOT / "examples" / "configs" / "candidate.yaml"
STATUS_LABELS = {
    "changed": "Changed",
    "added": "Added",
    "removed": "Removed",
    "unchanged": "Unchanged",
}


def display_value(value: Any) -> str:
    """Render a compact, readable table value."""
    if value is None:
        return "—"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def entries_to_frame(entries: list[DiffEntry]) -> pd.DataFrame:
    """Create a stable table shape, including when no rows match a filter."""
    return pd.DataFrame(
        [
            {
                "Path": entry.path,
                "Status": STATUS_LABELS[entry.status],
                "Baseline": display_value(entry.baseline),
                "Candidate": display_value(entry.candidate),
            }
            for entry in entries
        ],
        columns=["Path", "Status", "Baseline", "Candidate"],
    )


def decode_upload(uploaded_file: Any) -> dict[str, Any]:
    """Decode and validate one Streamlit uploaded configuration."""
    try:
        text = uploaded_file.getvalue().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{uploaded_file.name} 不是 UTF-8 文本文件") from exc
    return load_config_text(text, uploaded_file.name)


def load_inputs() -> tuple[dict[str, Any], dict[str, Any], str, str] | None:
    """Render source controls and return two configs when both are ready."""
    source = st.radio(
        "配置来源",
        ("公开示例", "上传文件"),
        horizontal=True,
        key="config_source",
        help="先用公开示例快速体验，也可以比较自己的 JSON/YAML 配置。",
    )

    if source == "公开示例":
        return (
            load_config(EXAMPLE_BASELINE),
            load_config(EXAMPLE_CANDIDATE),
            EXAMPLE_BASELINE.name,
            EXAMPLE_CANDIDATE.name,
        )

    left, right = st.columns(2)
    with left:
        baseline_file = st.file_uploader(
            "Baseline 配置", type=("json", "yaml", "yml"), key="baseline_upload"
        )
    with right:
        candidate_file = st.file_uploader(
            "Candidate 配置", type=("json", "yaml", "yml"), key="candidate_upload"
        )

    if baseline_file is None or candidate_file is None:
        st.info("请分别上传 Baseline 和 Candidate 配置后开始比较。")
        return None

    try:
        return (
            decode_upload(baseline_file),
            decode_upload(candidate_file),
            baseline_file.name,
            candidate_file.name,
        )
    except ValueError as exc:
        st.error(f"配置读取失败：{exc}")
        return None


def render_app() -> None:
    st.set_page_config(page_title="EmbodiedLab", page_icon="🦾", layout="wide")
    st.title("🦾 EmbodiedLab")
    st.caption("低算力、可复现的具身智能实验诊断工具 · Configuration Diff")

    st.markdown(
        "比较两次 VLA / WAM 实验的嵌套配置，快速定位训练参数、任务和模型后端的变化。"
    )
    loaded = load_inputs()
    if loaded is None:
        return

    baseline, candidate, baseline_name, candidate_name = loaded

    with st.sidebar:
        st.header("显示设置")
        show_unchanged = st.checkbox(
            "包含未变化字段", value=False, key="show_unchanged"
        )
        available_statuses = ["changed", "added", "removed"]
        if show_unchanged:
            available_statuses.append("unchanged")
        available_labels = [STATUS_LABELS[status] for status in available_statuses]
        selected_labels = st.multiselect(
            "状态筛选",
            available_labels,
            default=available_labels,
            key="status_filter",
        )
        selected_statuses = {
            status
            for status, label in STATUS_LABELS.items()
            if label in selected_labels
        }

    all_entries = compare_configs(
        baseline, candidate, include_unchanged=show_unchanged
    )
    summary = summarize(all_entries)

    st.subheader("比较概览")
    metric_columns = st.columns(4)
    for column, status in zip(
        metric_columns, ("changed", "added", "removed", "unchanged"), strict=True
    ):
        column.metric(STATUS_LABELS[status], summary[status])

    filtered_entries = [
        entry for entry in all_entries if entry.status in selected_statuses
    ]
    st.subheader("字段差异")
    st.dataframe(
        entries_to_frame(filtered_entries),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Path": st.column_config.TextColumn("Path", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
        },
    )
    st.caption(f"当前显示 {len(filtered_entries)} 条，共比较 {summary['total']} 个字段。")

    report_left, report_right, _ = st.columns([1, 1, 3])
    report_left.download_button(
        "下载 Markdown",
        data=render_markdown(all_entries, baseline_name, candidate_name),
        file_name="embodiedlab-config-diff.md",
        mime="text/markdown",
        key="download_markdown",
    )
    report_right.download_button(
        "下载 JSON",
        data=render_json(all_entries, baseline_name, candidate_name),
        file_name="embodiedlab-config-diff.json",
        mime="application/json",
        key="download_json",
    )

    with st.expander("查看原始配置"):
        raw_left, raw_right = st.columns(2)
        with raw_left:
            st.markdown(f"**Baseline · `{baseline_name}`**")
            st.code(yaml.safe_dump(baseline, allow_unicode=True, sort_keys=False), "yaml")
        with raw_right:
            st.markdown(f"**Candidate · `{candidate_name}`**")
            st.code(yaml.safe_dump(candidate, allow_unicode=True, sort_keys=False), "yaml")


if __name__ == "__main__":
    render_app()
