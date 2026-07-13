"""Compare structured experiment configuration files.

The module intentionally keeps the comparison logic independent from any UI so
it can later be reused by a CLI, Streamlit application, tests, or report job.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


MISSING = object()
SUPPORTED_SUFFIXES = {".json", ".yaml", ".yml"}


@dataclass(frozen=True, slots=True)
class DiffEntry:
    """One difference between a baseline and candidate configuration."""

    path: str
    status: str
    baseline: Any = None
    candidate: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {key: _json_safe(value) for key, value in asdict(self).items()}


def _json_safe(value: Any) -> Any:
    """Convert YAML-specific values into JSON-compatible representations."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_safe(item) for item in value]
    return str(value)


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a JSON or YAML configuration whose root value is a mapping."""
    config_path = Path(path).expanduser().resolve()
    suffix = config_path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"Unsupported config type {suffix!r}; expected one of: {supported}")
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file does not exist: {config_path}")

    text = config_path.read_text(encoding="utf-8")
    return load_config_text(text, config_path.name)


def load_config_text(text: str, source_name: str) -> dict[str, Any]:
    """Load configuration text using the extension in ``source_name``.

    This entry point lets the web UI parse uploaded files without first writing
    them to disk, while keeping validation identical to the command-line path.
    """
    suffix = Path(source_name).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"Unsupported config type {suffix!r}; expected one of: {supported}")

    try:
        if suffix == ".json":
            loaded = json.loads(text)
        else:
            loaded = yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"Unable to parse {source_name}: {exc}") from exc

    if loaded is None:
        return {}
    if not isinstance(loaded, Mapping):
        raise ValueError(
            f"Configuration root must be an object/mapping, got {type(loaded).__name__}"
        )
    return {str(key): value for key, value in loaded.items()}


def flatten_config(config: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten nested mappings into dotted paths while keeping lists intact."""
    flattened: dict[str, Any] = {}
    for raw_key, value in config.items():
        key = str(raw_key)
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, Mapping) and value:
            flattened.update(flatten_config(value, path))
        else:
            flattened[path] = value
    return flattened


def compare_configs(
    baseline: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    include_unchanged: bool = False,
) -> list[DiffEntry]:
    """Return deterministic, path-sorted differences between two configs."""
    old_flat = flatten_config(baseline)
    new_flat = flatten_config(candidate)
    entries: list[DiffEntry] = []

    for path in sorted(old_flat.keys() | new_flat.keys()):
        old_value = old_flat.get(path, MISSING)
        new_value = new_flat.get(path, MISSING)

        if old_value is MISSING:
            entries.append(DiffEntry(path, "added", None, new_value))
        elif new_value is MISSING:
            entries.append(DiffEntry(path, "removed", old_value, None))
        elif old_value != new_value or type(old_value) is not type(new_value):
            entries.append(DiffEntry(path, "changed", old_value, new_value))
        elif include_unchanged:
            entries.append(DiffEntry(path, "unchanged", old_value, new_value))

    return entries


def summarize(entries: Sequence[DiffEntry]) -> dict[str, int]:
    summary = {"added": 0, "removed": 0, "changed": 0, "unchanged": 0}
    for entry in entries:
        summary[entry.status] = summary.get(entry.status, 0) + 1
    summary["total"] = len(entries)
    return summary


def _format_value(value: Any) -> str:
    if value is None:
        return "-"
    rendered = json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True)
    return rendered.replace("|", "\\|").replace("\n", "\\n")


def render_markdown(
    entries: Sequence[DiffEntry],
    baseline_name: str = "baseline",
    candidate_name: str = "candidate",
) -> str:
    """Render a human-readable Markdown report."""
    summary = summarize(entries)
    lines = [
        "# Experiment Configuration Diff",
        "",
        f"- Baseline: `{baseline_name}`",
        f"- Candidate: `{candidate_name}`",
        (
            f"- Summary: {summary['changed']} changed, {summary['added']} added, "
            f"{summary['removed']} removed, {summary['unchanged']} unchanged"
        ),
        "",
        "| Path | Status | Baseline | Candidate |",
        "|---|---|---|---|",
    ]
    if not entries:
        lines.append("| - | identical | - | - |")
    else:
        for entry in entries:
            lines.append(
                f"| `{entry.path}` | {entry.status} | "
                f"{_format_value(entry.baseline)} | {_format_value(entry.candidate)} |"
            )
    return "\n".join(lines) + "\n"


def render_json(
    entries: Sequence[DiffEntry],
    baseline_name: str = "baseline",
    candidate_name: str = "candidate",
) -> str:
    report = {
        "baseline": baseline_name,
        "candidate": candidate_name,
        "summary": summarize(entries),
        "differences": [entry.to_dict() for entry in entries],
    }
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"


def find_project_root(start: Path) -> Path:
    """Find the nearest Git root; use the starting directory as a fallback."""
    current = start.expanduser().resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def resolve_safe_output(path: str | Path, project_root: Path) -> Path:
    """Resolve an output path and reject writes outside the project root."""
    output = Path(path).expanduser()
    if not output.is_absolute():
        output = Path.cwd() / output
    output = output.resolve(strict=False)
    try:
        output.relative_to(project_root.resolve())
    except ValueError as exc:
        raise ValueError(
            f"Output must stay inside project root {project_root}; got {output}"
        ) from exc
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare two JSON/YAML experiment configurations."
    )
    parser.add_argument("baseline", help="Baseline JSON/YAML configuration")
    parser.add_argument("candidate", help="Candidate JSON/YAML configuration")
    parser.add_argument(
        "--output",
        help="Optional report path inside this project (.md or .json)",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        dest="output_format",
        help="Report format (default: markdown)",
    )
    parser.add_argument(
        "--show-unchanged",
        action="store_true",
        help="Include identical fields in the report",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        baseline_path = Path(args.baseline)
        candidate_path = Path(args.candidate)
        baseline = load_config(baseline_path)
        candidate = load_config(candidate_path)
        entries = compare_configs(
            baseline,
            candidate,
            include_unchanged=args.show_unchanged,
        )

        renderer = render_json if args.output_format == "json" else render_markdown
        report = renderer(entries, baseline_path.name, candidate_path.name)

        if args.output:
            project_root = find_project_root(Path.cwd())
            output_path = resolve_safe_output(args.output, project_root)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding="utf-8")
            print(f"Report written to {output_path}")
        else:
            print(report, end="")
        return 0
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
