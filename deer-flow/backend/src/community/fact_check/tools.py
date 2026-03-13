import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

from langchain.tools import tool

from src.config.paths import get_paths

# Expected GTM report sections for coverage gap detection
_EXPECTED_GTM_SECTIONS = [
    "market_sizing",
    "competitive",
    "customer_segments",
    "regulatory",
    "trends",
    "strategy",
]


def _data_points_path(thread_id: str) -> Path:
    return get_paths().thread_dir(thread_id) / "rag" / "data_points.json"


def _fact_check_telemetry_path(thread_id: str) -> Path:
    return get_paths().thread_dir(thread_id) / "rag" / "fact_check_telemetry.jsonl"


def _load_data_points(thread_id: str) -> dict:
    p = _data_points_path(thread_id)
    if not p.exists():
        return {"version": "1.0", "data_points": []}
    return json.loads(p.read_text(encoding="utf-8"))


def _save_data_points(thread_id: str, store: dict) -> None:
    p = _data_points_path(thread_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_numeric(value: str) -> float | None:
    """Try to extract a numeric value from a string like '$5.2B', '12%', '3,400'."""
    if not isinstance(value, str):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    cleaned = value.replace(",", "").replace(" ", "").strip()
    # Remove currency symbols and common suffixes
    for prefix in ("$", "€", "£", "¥"):
        cleaned = cleaned.lstrip(prefix)
    cleaned = cleaned.rstrip("%")
    multiplier = 1.0
    if cleaned.upper().endswith("T"):
        multiplier = 1e12
        cleaned = cleaned[:-1]
    elif cleaned.upper().endswith("B"):
        multiplier = 1e9
        cleaned = cleaned[:-1]
    elif cleaned.upper().endswith("M"):
        multiplier = 1e6
        cleaned = cleaned[:-1]
    elif cleaned.upper().endswith("K"):
        multiplier = 1e3
        cleaned = cleaned[:-1]
    try:
        return float(cleaned) * multiplier
    except (ValueError, TypeError):
        return None


def _log_fact_check_telemetry(
    thread_id: str,
    section: str,
    total_data_points: int,
    issues: list[dict],
    data_points_by_section: dict[str, list[dict]],
) -> None:
    """Append a lightweight telemetry event for fact_check runs."""
    path = _fact_check_telemetry_path(thread_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    issues_by_type: dict[str, int] = {}
    for issue in issues:
        issues_by_type[issue.get("type", "unknown")] = issues_by_type.get(issue.get("type", "unknown"), 0) + 1

    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "thread_id": thread_id,
        "section_filter": section or "",
        "total_data_points": total_data_points,
        "issues_total": len(issues),
        "issues_by_type": issues_by_type,
        "sections_covered": sorted(data_points_by_section.keys()),
    }

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


@tool("store_data_point", parse_docstring=True)
def store_data_point_tool(
    thread_id: str,
    section: str,
    field: str,
    value: str,
    source_url: str,
    source_name: str,
    source_date: str = "",
    confidence: str = "medium",
    source_type: str = "web",
) -> str:
    """Store a sourced data point for provenance tracking and fact-checking.

    Call this for every key statistic or claim during research to build a provenance ledger.

    Args:
        thread_id: The current thread id.
        section: Report section (e.g. "market_sizing", "competitive", "regulatory").
        field: Data field name (e.g. "TAM", "market_share_competitor_x").
        value: The data value (e.g. "$5.2B", "35%").
        source_url: URL of the source.
        source_name: Human-readable source name (e.g. "Gartner 2025 Market Report").
        source_date: Date of the source (e.g. "2025-06", "2024-Q3").
        confidence: Confidence level - "high", "medium", or "low".
        source_type: Source type - "web", "uploaded", or "derived".
    """
    if confidence not in ("high", "medium", "low"):
        confidence = "medium"
    if source_type not in ("web", "uploaded", "derived"):
        source_type = "web"

    store = _load_data_points(thread_id)
    dp_id = f"dp_{uuid.uuid4().hex[:8]}"
    data_point = {
        "id": dp_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "section": section.strip().lower(),
        "field": field.strip(),
        "value": value,
        "source_url": source_url,
        "source_name": source_name,
        "source_date": source_date,
        "source_type": source_type,
        "confidence": confidence,
    }
    store["data_points"].append(data_point)
    _save_data_points(thread_id, store)

    return json.dumps(
        {
            "ok": True,
            "message": f"Data point stored: {section}/{field} = {value}",
            "id": dp_id,
            "total_data_points": len(store["data_points"]),
        },
        ensure_ascii=False,
        indent=2,
    )


@tool("fact_check", parse_docstring=True)
def fact_check_tool(thread_id: str, section: str = "") -> str:
    """Run automated fact-checking on all stored data points for the thread.

    Detects contradictions, stale data, single-source risks, numeric outliers,
    and coverage gaps. Run this after data collection to validate findings.

    Args:
        thread_id: The current thread id.
        section: Optional section to filter (empty string checks all sections).
    """
    store = _load_data_points(thread_id)
    all_dps = store.get("data_points", [])

    if section:
        section = section.strip().lower()
        dps = [dp for dp in all_dps if dp["section"] == section]
    else:
        dps = all_dps

    if not dps:
        response = {
            "ok": True,
            "total_data_points": 0,
            "issues": [],
            "data_points_by_section": {},
            "summary": "Fact check scanned 0 data point(s). No data points found."
            + (f" (filtered by section: {section})" if section else ""),
            "message": "No data points found." + (f" (filtered by section: {section})" if section else ""),
        }
        try:
            _log_fact_check_telemetry(
                thread_id=thread_id,
                section=section or "",
                total_data_points=0,
                issues=[],
                data_points_by_section={},
            )
        except Exception:
            pass
        return json.dumps(response, ensure_ascii=False, indent=2)

    issues = []

    # Group by (section, field)
    by_section_field: dict[tuple[str, str], list[dict]] = {}
    by_section: dict[str, list[dict]] = {}
    for dp in dps:
        key = (dp["section"], dp["field"])
        by_section_field.setdefault(key, []).append(dp)
        by_section.setdefault(dp["section"], []).append(dp)

    # 1. Contradiction detection — same (section, field) with different values
    for (sec, fld), entries in by_section_field.items():
        unique_values = set(e["value"] for e in entries)
        if len(unique_values) > 1:
            value_sources = [f"{e['value']} ({e['source_name']})" for e in entries]
            issues.append({
                "type": "contradiction",
                "section": sec,
                "field": fld,
                "values": value_sources,
                "recommendation": "Verify with additional source to resolve discrepancy",
            })

    # 2. Staleness detection — source dates older than 2 years
    now = datetime.now(UTC)
    for dp in dps:
        src_date = dp.get("source_date", "")
        if not src_date:
            continue
        # Parse year from source_date (handles "2023-06", "2023", "2023-Q3", etc.)
        try:
            year = int(src_date[:4])
            if now.year - year >= 2:
                issues.append({
                    "type": "stale_data",
                    "section": dp["section"],
                    "field": dp["field"],
                    "source_date": src_date,
                    "recommendation": f"Update with {now.year}+ source",
                })
        except (ValueError, IndexError):
            pass

    # 3. Single-source risk — fields with only 1 data point
    for (sec, fld), entries in by_section_field.items():
        if len(entries) == 1:
            issues.append({
                "type": "single_source",
                "section": sec,
                "field": fld,
                "recommendation": "Cross-reference with second source",
            })

    # 4. Outlier detection — numeric values deviating >3x from section median
    for sec, sec_dps in by_section.items():
        numeric_vals = []
        for dp in sec_dps:
            num = _parse_numeric(dp["value"])
            if num is not None and num > 0:
                numeric_vals.append((dp, num))
        if len(numeric_vals) >= 3:
            med = median([v for _, v in numeric_vals])
            if med > 0:
                for dp, num in numeric_vals:
                    ratio = num / med if num > med else med / num
                    if ratio > 3:
                        issues.append({
                            "type": "outlier",
                            "section": dp["section"],
                            "field": dp["field"],
                            "value": dp["value"],
                            "median": str(med),
                            "recommendation": "Verify — significantly deviates from other estimates",
                        })

    # 5. Coverage gaps — compare stored sections against expected GTM sections
    if not section:
        stored_sections = set(by_section.keys())
        missing = [s for s in _EXPECTED_GTM_SECTIONS if s not in stored_sections]
        if missing:
            issues.append({
                "type": "coverage_gap",
                "missing_sections": missing,
                "recommendation": "Research missing sections for complete coverage",
            })

    # Build data points grouped by section
    data_points_by_section = {}
    for sec, sec_dps in by_section.items():
        data_points_by_section[sec] = [
            {
                "id": dp["id"],
                "field": dp["field"],
                "value": dp["value"],
                "source_name": dp["source_name"],
                "confidence": dp["confidence"],
            }
            for dp in sec_dps
        ]

    # Human-readable summary for user-visible surfacing
    summary_lines: list[str] = []
    summary_lines.append(
        f"Fact check scanned {len(dps)} data point(s)"
        + (f" in section '{section.strip().lower()}'." if section else " across all sections.")
    )
    if issues:
        issues_by_type: dict[str, int] = {}
        for issue in issues:
            issues_by_type[issue.get("type", "unknown")] = issues_by_type.get(issue.get("type", "unknown"), 0) + 1
        breakdown = ", ".join(f"{t}: {c}" for t, c in sorted(issues_by_type.items()))
        summary_lines.append(f"Detected {len(issues)} potential issue(s) ({breakdown}).")
    else:
        summary_lines.append("No contradictions, stale data, single-source risks, or outliers detected.")

    # Highlight coverage gaps explicitly if present
    coverage_gaps = [i for i in issues if i.get("type") == "coverage_gap"]
    if coverage_gaps:
        missing_sections = sorted(set(sec for i in coverage_gaps for sec in i.get("missing_sections", [])))
        if missing_sections:
            summary_lines.append(
                "Coverage gaps: missing data for section(s) "
                + ", ".join(f"'{sec}'" for sec in missing_sections)
                + "."
            )

    response = {
        "ok": True,
        "total_data_points": len(dps),
        "issues": issues,
        "data_points_by_section": data_points_by_section,
        "summary": " ".join(summary_lines),
    }

    # Best-effort telemetry; should not affect tool behavior on failure.
    try:
        _log_fact_check_telemetry(
            thread_id=thread_id,
            section=section,
            total_data_points=len(dps),
            issues=issues,
            data_points_by_section=data_points_by_section,
        )
    except Exception:
        # Intentionally swallow errors to keep the tool robust.
        pass

    return json.dumps(response, ensure_ascii=False, indent=2)


@tool("get_sourced_data", parse_docstring=True)
def get_sourced_data_tool(thread_id: str, section: str = "") -> str:
    """Retrieve all stored data points with full source provenance, grouped by section.

    Use this when assembling the final report to ensure every claim cites its source.

    Args:
        thread_id: The current thread id.
        section: Optional section to filter (empty string returns all sections).
    """
    store = _load_data_points(thread_id)
    all_dps = store.get("data_points", [])

    if section:
        section = section.strip().lower()
        dps = [dp for dp in all_dps if dp["section"] == section]
    else:
        dps = all_dps

    if not dps:
        return json.dumps(
            {
                "ok": True,
                "total_data_points": 0,
                "sections": {},
                "message": "No data points found." + (f" (filtered by section: {section})" if section else ""),
            },
            ensure_ascii=False,
            indent=2,
        )

    # Group by section with full provenance and citation block
    sections: dict[str, list[dict]] = {}
    for dp in dps:
        source_date = dp.get("source_date") if isinstance(dp, dict) else dp["source_date"]
        if source_date:
            citation = f"[{dp['source_name']}, {source_date}]({dp['source_url']})"
        else:
            citation = f"[{dp['source_name']}]({dp['source_url']})"
        entry = {
            "id": dp["id"],
            "field": dp["field"],
            "value": dp["value"],
            "source_url": dp["source_url"],
            "source_name": dp["source_name"],
            "source_date": dp["source_date"],
            "source_type": dp["source_type"],
            "confidence": dp["confidence"],
            "citation": citation,
        }
        sections.setdefault(dp["section"], []).append(entry)

    return json.dumps(
        {
            "ok": True,
            "total_data_points": len(dps),
            "sections": sections,
        },
        ensure_ascii=False,
        indent=2,
    )
