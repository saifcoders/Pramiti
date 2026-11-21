"""Report Export Endpoints for AyurEval (COGNEXA).

Allows downloading verification, dual-evidence cross-audits, and safety reports
as structured academic Markdown (.md) or raw JSON (.json).
"""

from typing import Any, Dict, Literal
from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.services.report_formatter import (
    format_dual_audit_report_markdown,
    format_safety_report_markdown,
    format_verification_report_markdown,
)

router = APIRouter()


class ExportReportRequest(BaseModel):
    """Payload for generating downloadable academic reports."""

    report_type: Literal["verification", "dual-audit", "safety"] = Field(
        ...,
        description="Type of report being exported",
        examples=["verification"],
    )
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description="Output file format (markdown or json)",
    )
    report_data: Dict[str, Any] = Field(
        ...,
        description="Full report payload as returned by verification, dual-audit, or safety endpoints",
    )


@router.post(
    "/report",
    status_code=status.HTTP_200_OK,
    summary="Export and download formatted academic report",
    description="Transforms verification, dual-audit, or safety reports into structured Markdown (.md) or JSON files.",
)
async def export_report(request: ExportReportRequest) -> Response:
    """Exports structured report as downloadable file attachment."""
    try:
        rtype = request.report_type
        fmt = request.format
        data = request.report_data

        if fmt == "json":
            import json
            content = json.dumps(data, indent=2, ensure_ascii=False)
            filename = f"ayureval_{rtype.replace('-', '_')}_report.json"
            media_type = "application/json"
        else:
            if rtype == "verification":
                content = format_verification_report_markdown(data)
            elif rtype == "dual-audit":
                content = format_dual_audit_report_markdown(data)
            elif rtype == "safety":
                content = format_safety_report_markdown(data)
            else:
                raise ValueError(f"Unsupported report type: {rtype}")

            filename = f"ayureval_{rtype.replace('-', '_')}_report.md"
            media_type = "text/markdown; charset=utf-8"

        return Response(
            content=content.encode("utf-8"),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report export failed: {str(exc)}",
        )
