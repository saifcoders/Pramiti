"""Ayurvedic Safety, Matra (Dosage) & Contraindication Checker Service.

Scans input text, clinical questions, or AI-generated claims for Ayurvedic herbs
and formulations, cross-referencing them against authoritative classical texts
(Charaka Samhita, Sushruta Samhita, API) and contemporary phytovigilance data.

Flags:
  1. Critical Contraindications (e.g., Pregnancy, Gallstones, Bleeding, High Pitta)
  2. Modern Herb-Drug Interactions (e.g., Blood thinners, Sedatives, Antidiabetics)
  3. Matra (Classical Dosage) and Anupana (Adjuvant) Guidelines
  4. Classical Dietary Incompatibilities (Viruddha Ahara, e.g., equal ghee + honey)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Path to the curated safety guidelines dataset
_SAFETY_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "scientific" / "safety_guidelines.json"


# ---------------------------------------------------------------------------
# Enums and Data Models
# ---------------------------------------------------------------------------
class SafetySeverity(str, Enum):
    """Severity of the safety alert."""
    CRITICAL = "CRITICAL"   # Absolute clinical contraindication (potential harm)
    WARNING = "WARNING"     # Known drug interaction, potential overdosage, or high-risk condition
    ADVISORY = "ADVISORY"   # Classical Matra, Anupana, and swasthavritta administration guidance


class AlertType(str, Enum):
    """Categorisation of safety alerts."""
    CONTRAINDICATION = "CONTRAINDICATION"
    DRUG_INTERACTION = "DRUG_INTERACTION"
    DOSAGE_WARNING = "DOSAGE_WARNING"
    VIRUDDHA_AHARA = "VIRUDDHA_AHARA"
    PRECAUTION = "PRECAUTION"
    ADVISORY = "ADVISORY"


@dataclass
class SafetyAlert:
    """Individual safety alert or guideline."""
    herb: str
    alert_type: AlertType
    severity: SafetySeverity
    message: str
    recommendation: str
    classical_reference: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "herb": self.herb,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "recommendation": self.recommendation,
            "classical_reference": self.classical_reference,
        }


@dataclass
class HerbSafetyProfile:
    """Safety and pharmacological reference profile for one herb."""
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

    def to_dict(self) -> dict:
        return {
            "herb_name": self.herb_name,
            "botanical_name": self.botanical_name,
            "classical_matra": self.classical_matra,
            "max_daily_matra": self.max_daily_matra,
            "max_dose_grams": self.max_dose_grams,
            "anupana": self.anupana,
            "contraindications": self.contraindications,
            "herb_drug_interactions": self.herb_drug_interactions,
            "special_precautions": self.special_precautions,
            "classical_source": self.classical_source,
        }


@dataclass
class SafetyAuditResult:
    """Overall safety evaluation of an input text or claim."""
    input_text: str
    detected_herbs: List[str]
    is_safe: bool                      # False if any CRITICAL alert is triggered
    alerts: List[SafetyAlert]
    profiles: Dict[str, HerbSafetyProfile]
    summary: str

    def to_dict(self) -> dict:
        return {
            "input_text": self.input_text,
            "detected_herbs": self.detected_herbs,
            "is_safe": self.is_safe,
            "summary": self.summary,
            "alerts": [a.to_dict() for a in self.alerts],
            "profiles": {k: v.to_dict() for k, v in self.profiles.items()},
        }


# ---------------------------------------------------------------------------
# Clinical & Context Trigger Patterns
# ---------------------------------------------------------------------------
_PREGNANCY_PATTERN = re.compile(
    r"\b(pregnant|pregnancy|expecting|trimester|lactat(ing|ion)|breastfeed(ing)?|conception|infant|baby)\b",
    re.IGNORECASE,
)

_DRUG_PATTERNS = {
    "blood_thinners": (
        re.compile(r"\b(warfarin|aspirin|heparin|clopidogrel|blood\s*thinner|anticoagulant|antiplatelet|dabigatran|rivaroxaban)\b", re.IGNORECASE),
        "Blood Thinners / Anticoagulants",
    ),
    "sedatives": (
        re.compile(r"\b(sedative|benzodiazepine|diazepam|lorazepam|alprazolam|sleeping\s*pill|barbiturate|anxiolytic|ambien|zolpidem)\b", re.IGNORECASE),
        "Sedatives / CNS Depressants",
    ),
    "thyroid_meds": (
        re.compile(r"\b(levothyroxine|synthroid|thyroxine|thyroid\s*medication|antithyroid|methimazole)\b", re.IGNORECASE),
        "Thyroid Medications",
    ),
    "antidiabetics": (
        re.compile(r"\b(metformin|insulin|glipizide|antidiabetic|hypoglycemic|blood\s*sugar\s*medication)\b", re.IGNORECASE),
        "Antidiabetic / Hypoglycemic Agents",
    ),
    "immunosuppressants": (
        re.compile(r"\b(immunosuppressant|cyclosporine|tacrolimus|corticosteroid|prednisone|azathioprine|methotrexate)\b", re.IGNORECASE),
        "Immunosuppressive Drugs",
    ),
    "nsaids": (
        re.compile(r"\b(nsaid|ibuprofen|naproxen|diclofenac|celecoxib|painkiller)\b", re.IGNORECASE),
        "NSAIDs / Anti-inflammatory Drugs",
    ),
}

_CONDITION_PATTERNS = {
    "gallstones": (
        re.compile(r"\b(gallstone|gallbladder|biliary|cholelithiasis|bile\s*duct)\b", re.IGNORECASE),
        "Biliary Obstruction / Gallstones",
    ),
    "peptic_ulcer": (
        re.compile(r"\b(peptic\s*ulcer|gastric\s*ulcer|gastritis|hyperacidity|amlapitta|gerd|stomach\s*ulcer)\b", re.IGNORECASE),
        "Peptic Ulcer / Severe Gastritis",
    ),
    "bleeding_disorders": (
        re.compile(r"\b(bleeding\s*disorder|hemorrhage|raktapitta|active\s*bleeding|hemorrhoids|piles\s*bleeding)\b", re.IGNORECASE),
        "Bleeding Disorders (Raktapitta)",
    ),
    "hyperthyroid": (
        re.compile(r"\b(hyperthyroid(ism)?|thyrotoxicosis|grave'?s\s*disease)\b", re.IGNORECASE),
        "Hyperthyroidism / Thyrotoxicosis",
    ),
    "autoimmune": (
        re.compile(r"\b(autoimmune|lupus|sle|multiple\s*sclerosis|rheumatoid\s*arthritis)\b", re.IGNORECASE),
        "Autoimmune Disorders",
    ),
    "bradycardia": (
        re.compile(r"\b(bradycardia|heart\s*block|slow\s*heart\s*rate)\b", re.IGNORECASE),
        "Bradycardia / Conduction Defect",
    ),
    "estrogen_sensitive": (
        re.compile(r"\b(breast\s*cancer|uterine\s*cancer|ovarian\s*cancer|endometriosis|uterine\s*fibroid)\b", re.IGNORECASE),
        "Estrogen-Sensitive Neoplasm / Condition",
    ),
    "ama_indigestion": (
        re.compile(r"\b(ama\b|endotoxin|nava\s*jwara|acute\s*fever|coated\s*tongue|acute\s*pancreatitis|hepatitis|jaundice)\b", re.IGNORECASE),
        "Ama / Acute Toxic Indigestion / Liver Inflammation",
    ),
}

# Dosage detection regex: extracts number + unit (g, grams, gm, mg)
_DOSE_REGEX = re.compile(
    r"\b(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>g|grams?|gm|mg|milligrams?|ml|milliliters?)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# AyurvedicSafetyChecker Class
# ---------------------------------------------------------------------------
class AyurvedicSafetyChecker:
    """Scans Ayurvedic text/claims to flag safety hazards, dosage bounds, and contraindications."""

    def __init__(self, dataset_path: Optional[Path] = None) -> None:
        self.dataset_path = dataset_path or _SAFETY_DATA_PATH
        self.profiles: Dict[str, HerbSafetyProfile] = {}
        self._alias_map: Dict[str, str] = {}       # lowercase alias -> canonical herb_name
        self._alias_patterns: List[Tuple[re.Pattern, str]] = []
        self._load_dataset()

    def _load_dataset(self) -> None:
        """Loads and parses safety_guidelines.json into memory."""
        if not self.dataset_path.exists():
            logger.warning("Safety guidelines dataset not found at %s. Using empty database.", self.dataset_path)
            return

        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for entry in data.get("herbs", []):
                name = entry["herb_name"]
                profile = HerbSafetyProfile(
                    herb_name=name,
                    botanical_name=entry.get("botanical_name", ""),
                    classical_matra=entry.get("classical_matra", ""),
                    max_daily_matra=entry.get("max_daily_matra", ""),
                    max_dose_grams=float(entry.get("max_dose_grams", 10.0)),
                    anupana=entry.get("anupana", []),
                    contraindications=entry.get("contraindications", []),
                    herb_drug_interactions=entry.get("herb_drug_interactions", []),
                    special_precautions=entry.get("special_precautions", ""),
                    classical_source=entry.get("classical_source", ""),
                )
                self.profiles[name] = profile

                # Index aliases for fast regex scanning
                aliases = set(entry.get("sanskrit_aliases", []))
                aliases.add(name.lower())
                aliases.add(entry.get("botanical_name", "").lower())

                for alias in aliases:
                    cleaned_alias = alias.strip().lower()
                    if cleaned_alias:
                        self._alias_map[cleaned_alias] = name
                        pattern = re.compile(rf"\b{re.escape(cleaned_alias)}\b", re.IGNORECASE)
                        self._alias_patterns.append((pattern, name))

            logger.info("Loaded %d herb safety profiles from %s", len(self.profiles), self.dataset_path)
        except Exception as exc:
            logger.error("Failed to load safety dataset: %s", exc, exc_info=True)

    # -----------------------------------------------------------------------
    # Public Scanning Methods
    # -----------------------------------------------------------------------
    def scan_text(self, text: str) -> SafetyAuditResult:
        """Performs a comprehensive safety audit on an input text.

        Args:
            text: Raw input query, recommendation, or AI-generated claim.

        Returns:
            SafetyAuditResult with detected herbs, flagged alerts, and guidelines.
        """
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            return SafetyAuditResult(
                input_text="",
                detected_herbs=[],
                is_safe=True,
                alerts=[],
                profiles={},
                summary="No text provided for safety audit.",
            )

        # 1. Identify all mentioned herbs
        detected_herbs = self._detect_herbs(cleaned_text)
        if not detected_herbs:
            return SafetyAuditResult(
                input_text=cleaned_text,
                detected_herbs=[],
                is_safe=True,
                alerts=[],
                profiles={},
                summary="No known Ayurvedic herbs or formulations detected in the text.",
            )

        alerts: List[SafetyAlert] = []
        matched_profiles: Dict[str, HerbSafetyProfile] = {}

        for herb_name in detected_herbs:
            profile = self.profiles[herb_name]
            matched_profiles[herb_name] = profile

            # A. Check Contraindication Signals
            self._check_contraindications(cleaned_text, profile, alerts)

            # B. Check Herb-Drug Interaction Signals
            self._check_drug_interactions(cleaned_text, profile, alerts)

            # C. Check Mentioned Dosages vs Classical Matra
            self._check_dosage(cleaned_text, profile, alerts)

            # D. Classical Matra & Anupana Advisory
            self._add_advisory(profile, alerts)

        # E. Check Classical Incompatibilities (Viruddha Ahara)
        self._check_viruddha_ahara(cleaned_text, detected_herbs, alerts)

        # Check overall safety verdict
        has_critical = any(a.severity == SafetySeverity.CRITICAL for a in alerts)
        is_safe = not has_critical

        # Build executive summary
        summary = self._build_summary(detected_herbs, alerts, is_safe)

        return SafetyAuditResult(
            input_text=cleaned_text,
            detected_herbs=detected_herbs,
            is_safe=is_safe,
            alerts=alerts,
            profiles=matched_profiles,
            summary=summary,
        )

    def scan_claims(self, claims: List[str | Dict[str, Any]]) -> List[SafetyAuditResult]:
        """Audits multiple claims or sentences in batch."""
        results = []
        for claim in claims:
            claim_text = claim if isinstance(claim, str) else claim.get("claim_text", "")
            results.append(self.scan_text(claim_text))
        return results

    # -----------------------------------------------------------------------
    # Detection Helpers
    # -----------------------------------------------------------------------
    def _detect_herbs(self, text: str) -> List[str]:
        """Finds all unique canonical herb names mentioned in text."""
        found: set[str] = set()
        for pattern, herb_name in self._alias_patterns:
            if pattern.search(text):
                found.add(herb_name)
        # Return alphabetically sorted list for deterministic ordering
        return sorted(list(found))

    def _check_contraindications(
        self, text: str, profile: HerbSafetyProfile, alerts: List[SafetyAlert]
    ) -> None:
        """Flags critical clinical contraindications when context signals match."""
        herb = profile.herb_name

        # 1. Pregnancy / Lactation
        if _PREGNANCY_PATTERN.search(text):
            pregnancy_risks = {
                "Ashwagandha": "Spasmolytic & uterine stimulant activity at therapeutic doses; contraindicated in gestation.",
                "Guduchi": "Insufficient safety data for concentrated extracts during gestation; use caution.",
                "Triphala": "Downwards Apana Vayu stimulation; contraindicated in first trimester.",
                "Shallaki": "Traditional emmenagogue properties; lack of established safety in pregnancy.",
                "Neem": "Documented spermicidal, anti-implantation, and abortifacient actions; strictly contraindicated.",
                "Shigru": "Moringa root and bark contain moringinine/spirochin alkaloids that induce uterine spasms.",
                "Guggulu": "Documented emmenagogue and uterine stimulant actions; strictly contraindicated in pregnancy.",
            }
            if herb in pregnancy_risks:
                alerts.append(
                    SafetyAlert(
                        herb=herb,
                        alert_type=AlertType.CONTRAINDICATION,
                        severity=SafetySeverity.CRITICAL,
                        message=f"Critical Pregnancy Contraindication: {herb} should be avoided in pregnancy or lactation ({pregnancy_risks[herb]}).",
                        recommendation="Discontinue or avoid administration during pregnancy unless under specialized Ayurvedic physician supervision.",
                        classical_reference=profile.classical_source,
                    )
                )

        # 2. Condition-specific triggers
        if herb == "Turmeric" and _CONDITION_PATTERNS["gallstones"][0].search(text):
            alerts.append(
                SafetyAlert(
                    herb=herb,
                    alert_type=AlertType.CONTRAINDICATION,
                    severity=SafetySeverity.CRITICAL,
                    message="Critical Biliary Hazard: Curcumin induces strong gallbladder contractions (cholagogue) and can precipitate biliary colic in patients with gallstones.",
                    recommendation="Avoid concentrated curcumin or high-dose turmeric in active cholelithiasis or biliary tract obstruction.",
                    classical_reference="API Part I, Vol I",
                )
            )

        if herb in ["Pippali", "Shigru", "Ashwagandha"] and _CONDITION_PATTERNS["peptic_ulcer"][0].search(text):
            alerts.append(
                SafetyAlert(
                    herb=herb,
                    alert_type=AlertType.CONTRAINDICATION,
                    severity=SafetySeverity.WARNING,
                    message=f"Gastric Sensitivity Warning: {herb} possesses hot (ushna) or penetrating (tikshna) virya and may exacerbate active peptic ulcers or acute gastritis.",
                    recommendation="Avoid on an empty stomach; use mild anupana like warm milk, ghee, or seek medical alternatives.",
                    classical_reference=profile.classical_source,
                )
            )

        if herb in ["Turmeric", "Guggulu", "Pippali"] and _CONDITION_PATTERNS["bleeding_disorders"][0].search(text):
            alerts.append(
                SafetyAlert(
                    herb=herb,
                    alert_type=AlertType.CONTRAINDICATION,
                    severity=SafetySeverity.CRITICAL,
                    message=f"Hemorrhagic Risk: {herb} has antiplatelet or heating properties that may exacerbate active bleeding disorders (Raktapitta).",
                    recommendation="Contraindicated in active hemorrhage or pre-surgical states; stop 2 weeks prior to surgery.",
                    classical_reference=profile.classical_source,
                )
            )

        if herb == "Ashwagandha" and _CONDITION_PATTERNS["hyperthyroid"][0].search(text):
            alerts.append(
                SafetyAlert(
                    herb=herb,
                    alert_type=AlertType.CONTRAINDICATION,
                    severity=SafetySeverity.CRITICAL,
                    message="Thyrotoxicosis Hazard: Ashwagandha stimulates endogenous T3 and T4 thyroid hormone synthesis.",
                    recommendation="Contraindicated in severe hyperthyroidism or thyrotoxicosis without endocrinological monitoring.",
                    classical_reference="API Part I, Vol I",
                )
            )

        if herb == "Guduchi" and _CONDITION_PATTERNS["autoimmune"][0].search(text):
            alerts.append(
                SafetyAlert(
                    herb=herb,
                    alert_type=AlertType.CONTRAINDICATION,
                    severity=SafetySeverity.WARNING,
                    message="Autoimmune Flare Warning: Guduchi is a potent macrophage and cell-mediated immune stimulator which may exacerbate acute autoimmune flares.",
                    recommendation="Exercise caution and monitor inflammatory parameters in conditions like SLE or Multiple Sclerosis.",
                    classical_reference="Charaka Samhita Sutrasthana 25/40",
                )
            )

        if herb == "Shatavari" and _CONDITION_PATTERNS["estrogen_sensitive"][0].search(text):
            alerts.append(
                SafetyAlert(
                    herb=herb,
                    alert_type=AlertType.CONTRAINDICATION,
                    severity=SafetySeverity.CRITICAL,
                    message="Hormone-Sensitive Condition Hazard: Shatavari contains steroidal saponins (shatavarins) with phytoestrogenic activity that may stimulate estrogen-receptor-positive tissue.",
                    recommendation="Avoid in estrogen-dependent cancers (breast, uterine, ovarian) or severe endometriosis.",
                    classical_reference="API Part I, Vol IV",
                )
            )

        if herb == "Ghee" and _CONDITION_PATTERNS["ama_indigestion"][0].search(text):
            alerts.append(
                SafetyAlert(
                    herb=herb,
                    alert_type=AlertType.CONTRAINDICATION,
                    severity=SafetySeverity.WARNING,
                    message="Ama & Digestive Impairment: Ingesting Ghee during acute fever (Nava Jwara), heavy Ama, or acute pancreatitis clogs srotas (channels) and worsens toxic buildup.",
                    recommendation="Contraindicated until digestive fire (Agni) is rekindled via Langhana or Pachana dravyas.",
                    classical_reference="Charaka Samhita Sutrasthana 27/231",
                )
            )

    def _check_drug_interactions(
        self, text: str, profile: HerbSafetyProfile, alerts: List[SafetyAlert]
    ) -> None:
        """Detects co-mentioned modern pharmaceuticals and flags potential interactions."""
        herb = profile.herb_name

        # Blood thinners
        if _DRUG_PATTERNS["blood_thinners"][0].search(text):
            if herb in ["Turmeric", "Guggulu", "Triphala"]:
                alerts.append(
                    SafetyAlert(
                        herb=herb,
                        alert_type=AlertType.DRUG_INTERACTION,
                        severity=SafetySeverity.WARNING,
                        message=f"Drug Interaction: Co-administration of {herb} with anticoagulant/antiplatelet drugs (Warfarin, Aspirin, Heparin) elevates bleeding risk.",
                        recommendation="Regularly monitor INR/prothrombin time; consult attending physician before combining.",
                    )
                )

        # Sedatives
        if _DRUG_PATTERNS["sedatives"][0].search(text):
            if herb in ["Ashwagandha", "Brahmi"]:
                alerts.append(
                    SafetyAlert(
                        herb=herb,
                        alert_type=AlertType.DRUG_INTERACTION,
                        severity=SafetySeverity.WARNING,
                        message=f"Drug Interaction: {herb} possesses GABAergic/central nervous system calming properties that synergistically potentiate sedatives and benzodiazepines.",
                        recommendation="Monitor for excessive drowsiness or psychomotor impairment; dosage adjustments may be necessary.",
                    )
                )

        # Antidiabetics
        if _DRUG_PATTERNS["antidiabetics"][0].search(text):
            if herb in ["Guduchi", "Neem", "Turmeric", "Ashwagandha", "Shigru"]:
                alerts.append(
                    SafetyAlert(
                        herb=herb,
                        alert_type=AlertType.DRUG_INTERACTION,
                        severity=SafetySeverity.WARNING,
                        message=f"Drug Interaction: {herb} has proven hypoglycemic actions that may amplify the effects of insulin or oral antidiabetic drugs (Metformin).",
                        recommendation="Closely monitor blood glucose levels to prevent unanticipated hypoglycemic episodes.",
                    )
                )

        # Thyroid meds
        if _DRUG_PATTERNS["thyroid_meds"][0].search(text):
            if herb in ["Ashwagandha", "Brahmi", "Shigru"]:
                alerts.append(
                    SafetyAlert(
                        herb=herb,
                        alert_type=AlertType.DRUG_INTERACTION,
                        severity=SafetySeverity.WARNING,
                        message=f"Drug Interaction: {herb} can modulate thyroid hormone levels or absorption, altering the efficacy of synthetic thyroid medications (Levothyroxine).",
                        recommendation="Maintain consistent thyroid panel testing (TSH, free T3/T4) if used concurrently.",
                    )
                )

        # Immunosuppressants
        if _DRUG_PATTERNS["immunosuppressants"][0].search(text):
            if herb in ["Ashwagandha", "Guduchi", "Neem"]:
                alerts.append(
                    SafetyAlert(
                        herb=herb,
                        alert_type=AlertType.DRUG_INTERACTION,
                        severity=SafetySeverity.WARNING,
                        message=f"Drug Interaction: {herb} possesses immunostimulating properties that may directly antagonize immunosuppressive therapy (Cyclosporine, Corticosteroids).",
                        recommendation="Avoid co-administration in organ transplant recipients or active immunosuppressive regimens.",
                    )
                )

        # Broad bioavailability enhancement (Pippali / Piperine)
        if herb == "Pippali":
            alerts.append(
                SafetyAlert(
                    herb=herb,
                    alert_type=AlertType.DRUG_INTERACTION,
                    severity=SafetySeverity.WARNING,
                    message="Bioavailability Alert (Piperine Effect): Pippali inhibits intestinal CYP3A4 and P-glycoprotein, dramatically increasing blood concentrations of concurrent medications.",
                    recommendation="Separate administration of narrow therapeutic index drugs (Phenytoin, Theophylline, Warfarin) by at least 2–3 hours.",
                    classical_reference="Charaka Samhita Vimanasthana 1/16",
                )
            )

    def _check_dosage(
        self, text: str, profile: HerbSafetyProfile, alerts: List[SafetyAlert]
    ) -> None:
        """Parses numerical dosage statements in text and flags if exceeding maximum matra."""
        matches = _DOSE_REGEX.finditer(text)
        for m in matches:
            val_str = m.group("val")
            unit = m.group("unit").lower()
            try:
                val = float(val_str)
            except ValueError:
                continue

            # Normalize to grams
            dose_in_grams = val / 1000.0 if "mg" in unit or "milligram" in unit else val

            if dose_in_grams > profile.max_dose_grams:
                alerts.append(
                    SafetyAlert(
                        herb=profile.herb_name,
                        alert_type=AlertType.DOSAGE_WARNING,
                        severity=SafetySeverity.WARNING,
                        message=f"Exceeded Classical Matra: Detected dose of {val_str} {unit} exceeds the recommended maximum daily threshold of {profile.max_daily_matra}.",
                        recommendation=f"Standard classical matra is {profile.classical_matra}. Reduce daily dosage to prevent toxic accumulation.",
                        classical_reference=profile.classical_source,
                    )
                )

    def _add_advisory(self, profile: HerbSafetyProfile, alerts: List[SafetyAlert]) -> None:
        """Adds standard classical dosage (matra) and adjuvant (anupana) guidance."""
        anupana_str = ", ".join(profile.anupana[:3])
        alerts.append(
            SafetyAlert(
                herb=profile.herb_name,
                alert_type=AlertType.ADVISORY,
                severity=SafetySeverity.ADVISORY,
                message=f"Classical Matra (Dosage): {profile.classical_matra}.",
                recommendation=f"Recommended Classical Anupana (Adjuvant): {anupana_str}. {profile.special_precautions}",
                classical_reference=profile.classical_source,
            )
        )

    def _check_viruddha_ahara(
        self, text: str, detected_herbs: List[str], alerts: List[SafetyAlert]
    ) -> None:
        """Checks for classical toxic food/herb combinations (Viruddha Ahara)."""
        lower = text.lower()
        # Equal Ghee + Honey
        if ("ghee" in lower or "ghrita" in lower) and ("honey" in lower or "madhu" in lower):
            if "equal" in lower or "same ratio" in lower or "1:1" in lower:
                alerts.append(
                    SafetyAlert(
                        herb="Ghee & Honey",
                        alert_type=AlertType.VIRUDDHA_AHARA,
                        severity=SafetySeverity.CRITICAL,
                        message="Critical Viruddha Ahara: Ingesting Ghee and Honey in equal proportions by weight is canonical incompatible toxicity in classical Ayurveda.",
                        recommendation="Never combine ghee and honey in equal quantities (1:1). Always administer in unequal proportions (e.g., 2:1 or 1:2) or separate intake.",
                        classical_reference="Charaka Samhita Sutrasthana 26/84",
                    )
                )

    def _build_summary(
        self, detected_herbs: List[str], alerts: List[SafetyAlert], is_safe: bool
    ) -> str:
        """Constructs an academic executive summary of the safety audit."""
        critical_count = sum(1 for a in alerts if a.severity == SafetySeverity.CRITICAL)
        warning_count = sum(1 for a in alerts if a.severity == SafetySeverity.WARNING)
        advisory_count = sum(1 for a in alerts if a.severity == SafetySeverity.ADVISORY)

        herbs_str = ", ".join(detected_herbs)
        if not is_safe:
            return (
                f"Safety Audit FAILED (CRITICAL HAZARDS DETECTED). Identified {len(detected_herbs)} herb(s) ({herbs_str}). "
                f"Flagged {critical_count} critical contraindication(s), {warning_count} potential drug/dosage warning(s), "
                f"and {advisory_count} classical matra guideline(s). Clinical intervention or dosage revision required."
            )

        if warning_count > 0:
            return (
                f"Safety Audit PASSED WITH PRECAUTIONS. Identified {len(detected_herbs)} herb(s) ({herbs_str}). "
                f"Found no critical contraindications, but flagged {warning_count} drug interaction or dosage precaution(s). "
                f"Classical Matra and Anupana guidelines should be observed."
            )

        return (
            f"Safety Audit PASSED. Identified {len(detected_herbs)} herb(s) ({herbs_str}). "
            f"All claims adhere to classical safety guidelines. Provided {advisory_count} standard Matra and Anupana recommendation(s)."
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
safety_checker = AyurvedicSafetyChecker()
