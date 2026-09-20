"""Durable evaluation reports and role-safe report views."""

from __future__ import annotations

import csv
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
_configured_reports = Path(os.getenv("EVAL_REPORT_DIR", "evals/reports"))
REPORTS_DIR = _configured_reports if _configured_reports.is_absolute() else ROOT / _configured_reports
RUN_ID_PATTERN = re.compile(r"^[0-9]{8}T[0-9]{6}Z(?:-[a-z0-9-]+)?$")

RESULT_FIELDS = (
    "case_id", "suite", "agent", "role", "eval_type", "scoring_method",
    "language", "course_slug", "lesson_key", "lesson_title", "status", "score",
    "reason", "critical", "critical_failures", "input", "reference", "actual_output",
    "duration_ms", "model_provider", "model", "judge_provider", "judge_model",
)


def _rate(rows: list[dict[str, Any]]) -> float:
    executed = [row for row in rows if row.get("status") != "SKIPPED"]
    if not executed:
        return 0.0
    return round(100 * sum(row.get("status") == "PASS" for row in executed) / len(executed), 1)


def _breakdown(results: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        value = str(row.get(field) or "unassigned")
        grouped[value].append(row)
    return {
        key: {
            "total": len(rows),
            "passed": sum(row.get("status") == "PASS" for row in rows),
            "failed": sum(row.get("status") == "FAIL" for row in rows),
            "errors": sum(row.get("status") == "ERROR" for row in rows),
            "skipped": sum(row.get("status") == "SKIPPED" for row in rows),
            "pass_rate": _rate(rows),
        }
        for key, rows in sorted(grouped.items())
    }


def summarize_results(
    results: list[dict[str, Any]], *, run_id: str, generated_at: str,
    corpus_version: str, selection: dict[str, Any], thresholds: dict[str, float],
    model_config: dict[str, str],
) -> dict[str, Any]:
    tracks = _breakdown(results, "eval_type")
    critical_failures = [
        row["case_id"] for row in results
        if row.get("critical") and row.get("status") in {"FAIL", "ERROR"}
    ]
    threshold_failures = [
        eval_type for eval_type, stats in tracks.items()
        if stats["pass_rate"] < 100 * thresholds.get(eval_type, 0.0)
    ]
    passed = not critical_failures and not threshold_failures and bool(results)
    return {
        "schema_version": "1.0",
        "run_id": run_id,
        "generated_at": generated_at,
        "corpus_version": corpus_version,
        "selection": selection,
        "thresholds": thresholds,
        "models": model_config,
        "status": "PASS" if passed else "FAIL",
        "total": len(results),
        "passed": sum(row.get("status") == "PASS" for row in results),
        "failed": sum(row.get("status") == "FAIL" for row in results),
        "errors": sum(row.get("status") == "ERROR" for row in results),
        "skipped": sum(row.get("status") == "SKIPPED" for row in results),
        "pass_rate": _rate(results),
        "critical_failures": critical_failures,
        "threshold_failures": threshold_failures,
        "by_eval_type": tracks,
        "by_agent": _breakdown(results, "agent"),
        "by_course": _breakdown([row for row in results if row.get("course_slug")], "course_slug"),
        "by_language": _breakdown(results, "language"),
        "by_suite": _breakdown(results, "suite"),
    }


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return value


def _markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# FastLearn evaluation report",
        "",
        f"- Run: `{summary['run_id']}`",
        f"- Generated: {summary['generated_at']}",
        f"- Corpus: {summary['corpus_version']}",
        f"- Status: **{summary['status']}**",
        f"- Overall: {summary['passed']}/{summary['total']} passed ({summary['pass_rate']}%)",
        "",
        "## Evaluation types",
        "",
        "| Type | Passed | Failed | Errors | Skipped | Rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, stats in summary["by_eval_type"].items():
        lines.append(
            f"| {name} | {stats['passed']} | {stats['failed']} | {stats['errors']} | "
            f"{stats['skipped']} | {stats['pass_rate']}% |"
        )
    lines.extend(["", "## Agents", "", "| Agent | Passed | Total | Rate |", "|---|---:|---:|---:|"])
    for name, stats in summary["by_agent"].items():
        lines.append(f"| {name} | {stats['passed']} | {stats['total']} | {stats['pass_rate']}% |")
    if summary["critical_failures"]:
        lines.extend(["", "## Critical failures", "", *[f"- `{case_id}`" for case_id in summary["critical_failures"]]])
    return "\n".join(lines) + "\n"


def write_report(
    results: list[dict[str, Any]], *, run_id: str, generated_at: str,
    corpus_version: str, selection: dict[str, Any], thresholds: dict[str, float],
    model_config: dict[str, str],
) -> tuple[Path, dict[str, Any]]:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("Invalid evaluation run ID")
    summary = summarize_results(
        results, run_id=run_id, generated_at=generated_at,
        corpus_version=corpus_version, selection=selection,
        thresholds=thresholds, model_config=model_config,
    )
    run_dir = REPORTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    with (run_dir / "results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for result in results:
            writer.writerow({field: _csv_value(result.get(field, "")) for field in RESULT_FIELDS})
    (run_dir / "report.md").write_text(_markdown_report(summary), encoding="utf-8")

    reports = [item for item in list_reports() if item.get("run_id") != run_id]
    reports.insert(0, _index_item(summary))
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "index.json").write_text(
        json.dumps({"latest": run_id, "reports": reports[:100]}, indent=2) + "\n",
        encoding="utf-8",
    )
    return run_dir, summary


def _index_item(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        key: summary[key]
        for key in ("run_id", "generated_at", "status", "total", "passed", "pass_rate")
    }


def list_reports() -> list[dict[str, Any]]:
    index_path = REPORTS_DIR / "index.json"
    if index_path.exists():
        try:
            payload = json.loads(index_path.read_text(encoding="utf-8"))
            return [item for item in payload.get("reports", []) if RUN_ID_PATTERN.fullmatch(str(item.get("run_id", "")))]
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    reports = []
    if not REPORTS_DIR.exists():
        return reports
    for path in sorted(REPORTS_DIR.iterdir(), reverse=True):
        if not path.is_dir() or not RUN_ID_PATTERN.fullmatch(path.name):
            continue
        try:
            summary = json.loads((path / "summary.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        reports.append(_index_item(summary))
    return reports


def load_report(run_id: str | None = None, *, include_results: bool = True) -> dict[str, Any] | None:
    reports = list_reports()
    selected = run_id or (reports[0]["run_id"] if reports else "")
    if not RUN_ID_PATTERN.fullmatch(selected):
        return None
    run_dir = REPORTS_DIR / selected
    try:
        summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    results: list[dict[str, Any]] = []
    if include_results:
        try:
            with (run_dir / "results.csv").open(encoding="utf-8") as handle:
                results = list(csv.DictReader(handle))
        except OSError:
            results = []
    return {"summary": summary, "results": results}


def report_for_role(role: str, run_id: str | None = None) -> dict[str, Any] | None:
    """Students receive aggregates only; staff receive case-level evidence."""
    can_view_details = role in {"teacher", "instructor", "admin"}
    report = load_report(run_id, include_results=can_view_details)
    if report is None:
        return None
    return {
        "summary": report["summary"],
        "results": report["results"] if can_view_details else [],
        "can_view_details": can_view_details,
    }


def report_file(run_id: str, filename: str) -> Path | None:
    """Resolve one known report artifact without accepting arbitrary paths."""
    if not RUN_ID_PATTERN.fullmatch(run_id) or filename not in {"summary.json", "results.csv", "report.md"}:
        return None
    path = REPORTS_DIR / run_id / filename
    return path if path.is_file() else None
