"""Server-rendered evaluation report views with role-based disclosure."""

from __future__ import annotations

import json
from typing import Any

from fasthtml.common import *

from components.i18n import t
from evals import reporting


def _status(value: str):
    passed = value == "PASS"
    return Span(
        value,
        style=(
            "display:inline-block;padding:3px 9px;border-radius:999px;font-size:12px;font-weight:700;"
            f"background:{'#dcfce7' if passed else '#fee2e2'};color:{'#166534' if passed else '#991b1b'};"
        ),
    )


def _metric(label: str, value: Any, detail: str = ""):
    return Div(
        Div(str(value), cls="dashboard-card-value"),
        Div(label, cls="dashboard-card-label"),
        P(detail, cls="page-subtitle") if detail else "",
        cls="dashboard-card",
    )


def _breakdown_table(title: str, values: dict[str, dict[str, Any]]):
    rows = [
        Tr(
            Td(name.replace("_", " ").title()),
            Td(str(stats.get("passed", 0))),
            Td(str(stats.get("failed", 0))),
            Td(str(stats.get("errors", 0))),
            Td(str(stats.get("skipped", 0))),
            Td(f"{stats.get('pass_rate', 0)}%"),
        )
        for name, stats in values.items()
    ]
    return Div(
        H2(title),
        Table(
            Thead(Tr(Th("Name"), Th("Pass"), Th("Fail"), Th("Error"), Th("Skipped"), Th("Rate"))),
            Tbody(*rows), cls="manage-table",
        ) if rows else P("No results in this group.", cls="page-subtitle"),
        style="margin-top:24px;",
    )


def _case_question(row: dict[str, str]) -> str:
    try:
        payload = json.loads(row.get("input") or "{}")
    except json.JSONDecodeError:
        return row.get("input", "")
    return str(payload.get("question") or payload.get("teacher_guidance") or row.get("lesson_title") or "")


def _detail_table(results: list[dict[str, str]], total: int):
    rows = []
    for result in results[:500]:
        rows.append(Tr(
            Td(_status(result.get("status", ""))),
            Td(result.get("eval_type", "")),
            Td(result.get("agent", "").replace("_", " ").title()),
            Td(result.get("course_slug") or "—"),
            Td(_case_question(result)),
            Td(result.get("reference", "")),
            Td(result.get("actual_output", "")),
            Td(result.get("reason", "")),
        ))
    return Div(
        H2("Case evidence"),
        P(f"Showing {min(len(results), 500)} of {total} matching cases. Full evidence is available in the CSV report.", cls="page-subtitle"),
        Div(
            Table(
                Thead(Tr(
                    Th("Status"), Th("Eval type"), Th("Agent"), Th("Course"),
                    Th("Input"), Th("Ground truth"), Th("Model output"), Th("Reason"),
                )),
                Tbody(*rows), cls="manage-table",
            ),
            style="overflow-x:auto;",
        ),
        style="margin-top:24px;",
    )


def evaluation_reports_content(
    user: dict[str, Any], lang: str, run_id: str = "", *,
    query: str = "", status: str = "", eval_type: str = "",
):
    reports = reporting.list_reports()
    report = reporting.report_for_role(user.get("role", "student"), run_id or None)
    if report is None:
        return Div(
            H1(t("evaluation_reports", lang), cls="page-title"),
            P(t("evaluation_reports_empty", lang), cls="page-subtitle"),
            Code("python -m evals.run_evals --eval-type deterministic"),
            cls="page-content",
        )

    summary = report["summary"]
    can_view_details = report["can_view_details"]
    selector = Form(
        Label(t("evaluation_run", lang), for_="evaluation-run", cls="form-label"),
        Select(*[
            Option(
                f"{str(item['generated_at'])[:19].replace('T', ' ')} UTC · {item['status']} · {item['pass_rate']}%",
                value=item["run_id"], selected=item["run_id"] == summary["run_id"],
            )
            for item in reports
        ], id="evaluation-run", name="run", cls="form-input", onchange="this.form.submit()"),
        method="get", action="/app/admin/evaluations",
        style="max-width:620px;margin:16px 0 24px;",
    )
    download = A(
        "Download full CSV" if can_view_details else "Download summary JSON",
        href=f"/app/admin/evaluations/download?run={summary['run_id']}&format={'csv' if can_view_details else 'json'}",
        cls="btn btn-secondary btn-sm",
    )
    content = [
        Div(
            Div(H1(t("evaluation_reports", lang), cls="page-title"), P(t("evaluation_reports_help", lang), cls="page-subtitle")),
            download,
            style="display:flex;justify-content:space-between;gap:16px;align-items:flex-start;",
        ),
        selector,
        Div(
            _metric("Status", summary["status"]),
            _metric("Pass rate", f"{summary['pass_rate']}%", f"{summary['passed']} of {summary['total']}"),
            _metric("Failures", summary["failed"]),
            _metric("Errors", summary["errors"]),
            cls="dashboard-grid",
        ),
        _breakdown_table("Probabilistic and deterministic tracks", summary.get("by_eval_type", {})),
        _breakdown_table("Course coverage", summary.get("by_course", {})),
    ]
    if can_view_details:
        filtered = report["results"]
        if status:
            filtered = [row for row in filtered if row.get("status") == status]
        if eval_type:
            filtered = [row for row in filtered if row.get("eval_type") == eval_type]
        if query:
            needle = query.casefold()
            filtered = [
                row for row in filtered
                if any(needle in str(value).casefold() for value in row.values())
            ]
        content.extend([
            _breakdown_table("Agents", summary.get("by_agent", {})),
            Form(
                Input(type="hidden", name="run", value=summary["run_id"]),
                Input(name="q", value=query, placeholder="Search cases, courses or answers…", cls="form-input"),
                Select(
                    Option("All statuses", value="", selected=not status),
                    *[Option(item, value=item, selected=status == item) for item in ("PASS", "FAIL", "ERROR", "SKIPPED")],
                    name="status", cls="form-input",
                ),
                Select(
                    Option("All evaluation types", value="", selected=not eval_type),
                    Option("Probabilistic", value="probabilistic", selected=eval_type == "probabilistic"),
                    Option("Deterministic", value="deterministic", selected=eval_type == "deterministic"),
                    name="eval_type", cls="form-input",
                ),
                Button("Filter", type="submit", cls="btn btn-secondary btn-sm"),
                method="get", action="/app/admin/evaluations", cls="team-invite-form",
                style="margin-top:24px;",
            ),
            _detail_table(filtered, len(report["results"])),
        ])
    else:
        content.append(Div(
            H2(t("evaluation_student_summary", lang)),
            P(t("evaluation_student_redaction", lang), cls="page-subtitle"),
            style="margin-top:24px;",
        ))
    return Div(*content, cls="page-content")
