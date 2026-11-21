"""Ayurvedic Safety, Matra & Contraindication API Endpoints.

Exposes endpoints for auditing Ayurvedic treatments, claims, and formulations against
classical safety guidelines (Charaka, Sushruta, API) and modern phytovigilance data.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.safety_checker import safety_checker

router = APIRouter()


# ==============================================================================
# Pydantic Schemas
# ==============================================================================
class SafetyCheckRequest(BaseModel):
    """Payload for auditing Ayurvedic text or prescription for safety."""

    text: str = Field(
        ...,
        description="Ayurvedic text, clinical question, dosage advice, or claim to audit for safety.",
        examples=["Patient is pregnant and prescribed 10g of Ashwagandha daily with warm milk."],
    )
    claims: Optional[List[str]] = Field(
        default=None,
        description="Optional list of discrete atomic claims to audit individually.",
        examples=[
            "Ashwagandha can be taken safely at 10g daily during pregnancy.",
            "Turmeric should be taken with Warfarin to reduce arthritis inflammation.",
        ],
    )


class SafetyAlertResponse(BaseModel):
    """Individual safety alert detailing a hazard, precaution, or advisory."""

    herb: str = Field(..., description="Herb or substance associated with the alert")
    alert_type: str = Field(..., description="Classification (CONTRAINDICATION, DRUG_INTERACTION, DOSAGE_WARNING, VIRUDDHA_AHARA, PRECAUTION, ADVISORY)")
    severity: str = Field(..., description="Severity level (CRITICAL, WARNING, ADVISORY)")
    message: str = Field(..., description="Detailed clinical alert explanation")
    recommendation: str = Field(..., description="Actionable clinical or classical guidance")
    classical_reference: Optional[str] = Field(default=None, description="Canonical Samhita citation or API reference")


class HerbSafetyProfileResponse(BaseModel):
    """Comprehensive safety and classical pharmacology profile for a detected herb."""

    herb_name: str
    botanical_name: str
    classical_matra: str
    max_daily_matra: str
    max_dose_grams: float
    anupana: List[str]
    contraindications: List[str]
    herb_drug_interactions: List[str]
    special_precautions: str
    classical_source: str


class SafetyCheckResponse(BaseModel):
    """Full safety audit response for the submitted text."""

    input_text: str
    detected_herbs: List[str]
    is_safe: bool = Field(..., description="True if no CRITICAL contraindications or hazards are triggered")
    summary: str = Field(..., description="Executive summary of the safety evaluation")
    alerts: List[SafetyAlertResponse]
    profiles: Dict[str, HerbSafetyProfileResponse]
    claims_results: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Individual audit results if a list of claims was submitted",
    )


# ==============================================================================
# Endpoints
# ==============================================================================
@router.post(
    "/check",
    response_model=SafetyCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Audit Ayurvedic text for safety, matra (dosage), and contraindications",
    description=(
        "Scans input text for Ayurvedic herbs and cross-references them against "
        "classical Brihat Trayi texts and API safety data to detect contraindications "
        "(e.g., pregnancy, biliary obstruction, bleeding), modern drug interactions "
        "(e.g., blood thinners, sedatives), excessive dosages, and Viruddha Ahara."
    ),
)
async def check_safety(request: SafetyCheckRequest) -> SafetyCheckResponse:
    """Audits text and claims for Ayurvedic safety compliance."""
    try:
        # Perform primary text audit
        result = safety_checker.scan_text(request.text)

        # Audit individual claims if provided
        claims_data: Optional[List[Dict[str, Any]]] = None
        if request.claims:
            claims_results = safety_checker.scan_claims(request.claims)
            claims_data = [cr.to_dict() for cr in claims_results]

        # Format alerts
        formatted_alerts = [
            SafetyAlertResponse(
                herb=a.herb,
                alert_type=a.alert_type.value,
                severity=a.severity.value,
                message=a.message,
                recommendation=a.recommendation,
                classical_reference=a.classical_reference,
            )
            for a in result.alerts
        ]

        # Format profiles
        formatted_profiles = {
            k: HerbSafetyProfileResponse(
                herb_name=v.herb_name,
                botanical_name=v.botanical_name,
                classical_matra=v.classical_matra,
                max_daily_matra=v.max_daily_matra,
                max_dose_grams=v.max_dose_grams,
                anupana=v.anupana,
                contraindications=v.contraindications,
                herb_drug_interactions=v.herb_drug_interactions,
                special_precautions=v.special_precautions,
                classical_source=v.classical_source,
            )
            for k, v in result.profiles.items()
        }

        return SafetyCheckResponse(
            input_text=result.input_text,
            detected_herbs=result.detected_herbs,
            is_safe=result.is_safe,
            summary=result.summary,
            alerts=formatted_alerts,
            profiles=formatted_profiles,
            claims_results=claims_data,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Safety checker encountered an error: {str(exc)}",
        )
