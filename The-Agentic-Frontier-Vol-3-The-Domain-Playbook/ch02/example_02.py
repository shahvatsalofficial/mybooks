"""
SOVEREIGN ENTERPRISE ARCHITECTURE: INSURANCE & CLAIMS TRIAGE ENGINE
File: claims_triage_engine.py
Author: Vatsal Shah, Enterprise Systems Architect
Standards: ISO 20022, ACORD XML, NICB Compliance, Sub-60s STP Architecture
"""

import asyncio
import time
import enum
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [CLAIMS-CORE] %(message)s")
logger = logging.getLogger("ClaimsTriageEngine")


class ClaimState(enum.Enum):
    INGESTED = "INGESTED"
    COVERAGE_VERIFIED = "COVERAGE_VERIFIED"
    VISION_APPRAISED = "VISION_APPRAISED"
    FRAUD_CLEARED = "FRAUD_CLEARED"
    AUTO_APPROVED = "AUTO_APPROVED"
    QUARANTINED_SIU = "QUARANTINED_SIU"
    HUMAN_ESCALATION = "HUMAN_ESCALATION"


@dataclass
class FNOLPayload:
    claim_id: str
    policy_id: str
    vin: str
    incident_timestamp: float
    telematics_delta_v_kmh: float
    gps_coords: Tuple[float, float]
    image_uris: List[str]
    claimant_reported_damage: str


@dataclass
class AppraisalLineItem:
    part_name: str
    oem_part_number: str
    action: str  # REPLACE, REPAIR, REFINISH
    labor_hours: float
    part_cost_usd: float
    labor_cost_usd: float


@dataclass
class PolicyContract:
    policy_id: str
    is_active: bool
    coverage_limit_usd: float
    deductible_usd: float
    has_collision_coverage: bool
    has_rental_coverage: bool


class AutonomousClaimsEngine:
    """Enterprise Straight-Through Claims Processing and Verification Swarm."""
    
    def __init__(self, labor_rate_hourly: float = 68.0, max_stp_limit_usd: float = 15000.0):
        self.labor_rate = labor_rate_hourly
        self.max_stp_limit = max_stp_limit_usd

    async def execute_straight_through_claim(self, fnol: FNOLPayload, policy: PolicyContract) -> Dict[str, any]:
        start_time = time.perf_counter()
        logger.info(f"Initiating autonomous triage for Claim UUID: {fnol.claim_id}")

        # Stage 1: Policy Coverage Verification
        if not policy.is_active or not policy.has_collision_coverage:
            logger.warning(f"Claim {fnol.claim_id} REJECTED: Inactive policy or missing collision rider.")
            return {"claim_id": fnol.claim_id, "state": ClaimState.HUMAN_ESCALATION.value, "payout": 0.0, "reason": "COVERAGE_LAPSED"}

        # Stage 2: Parallel Vision AI Appraisal & Fraud Graph Traversal
        vision_task = self._run_vision_damage_appraisal(fnol)
        fraud_task = self._run_temporal_fraud_gnn(fnol)
        
        appraisal_items, fraud_conviction = await asyncio.gather(vision_task, fraud_task)
        
        # Stage 3: Fraud Circuit Breaker
        if fraud_conviction > 0.60:
            logger.error(f"SECURITY ALERT: Claim {fnol.claim_id} QUARANTINED. Fraud Score: {fraud_conviction:.3f}")
            return {
                "claim_id": fnol.claim_id,
                "state": ClaimState.QUARANTINED_SIU.value,
                "fraud_conviction": fraud_conviction,
                "payout": 0.0,
                "action": "LOCK_ACCOUNTS_AND_GENERATE_NICB_DOSSIER"
            }

        # Stage 4: Financial Calculation & Deductible Netting
        total_parts_cost = sum(item.part_cost_usd for item in appraisal_items)
        total_labor_cost = sum(item.labor_hours * self.labor_rate for item in appraisal_items)
        gross_repair_estimate = total_parts_cost + total_labor_cost
        
        # Apply deductible and policy caps
        net_payable = max(0.0, min(gross_repair_estimate, policy.coverage_limit_usd) - policy.deductible_usd)
        
        # Stage 5: STP Disbursement Gate
        if gross_repair_estimate > self.max_stp_limit:
            logger.info(f"Claim {fnol.claim_id} exceeds STP limit (${self.max_stp_limit}). Routed to Senior Adjuster.")
            return {
                "claim_id": fnol.claim_id,
                "state": ClaimState.HUMAN_ESCALATION.value,
                "gross_estimate": round(gross_repair_estimate, 2),
                "reason": "EXCEEDS_AUTOMATED_LIMIT"
            }

        # Stage 6: ISO 20022 FedNow Wire Compilation
        iso_xml_payload = self._generate_iso20022_pacs008_wire(fnol, net_payable)

        execution_duration = (time.perf_counter() - start_time) * 1000.0  # in ms
        logger.info(f"Claim {fnol.claim_id} AUTO-APPROVED in {execution_duration:.1f}ms. Net Payout: ${net_payable:.2f}")

        return {
            "claim_id": fnol.claim_id,
            "state": ClaimState.AUTO_APPROVED.value,
            "gross_repair_cost": round(gross_repair_estimate, 2),
            "deductible_applied": policy.deductible_usd,
            "net_disbursement_usd": round(net_payable, 2),
            "line_items_count": len(appraisal_items),
            "fraud_score": round(fraud_conviction, 3),
            "settlement_rail": "FEDNOW_INSTANT_ACH",
            "iso20022_wire_hash": hash(iso_xml_payload),
            "latency_ms": round(execution_duration, 2)
        }

    async def _run_vision_damage_appraisal(self, fnol: FNOLPayload) -> List[AppraisalLineItem]:
        """Simulates GPU Mask2Former sub-pixel segmentation and OEM parts extraction."""
        await asyncio.sleep(0.015)  # 15ms simulated GPU forward pass
        return [
            AppraisalLineItem("Front Bumper Cover", "OEM-52119-0R914", "REPLACE", 1.8, 485.00, 1.8 * self.labor_rate),
            AppraisalLineItem("Hood Assembly", "OEM-53301-0R070", "REPLACE", 2.2, 620.00, 2.2 * self.labor_rate),
            AppraisalLineItem("Left Fender Panel", "OEM-53812-0R080", "REPAIR", 3.5, 0.00, 3.5 * self.labor_rate),
            AppraisalLineItem("Left LED Headlamp", "OEM-81150-0R120", "REPLACE", 0.6, 890.00, 0.6 * self.labor_rate)
        ]

    async def _run_temporal_fraud_gnn(self, fnol: FNOLPayload) -> float:
        """Simulates Neo4j / PyG Heterogeneous GNN entity traversal."""
        await asyncio.sleep(0.010)  # 10ms graph inference
        # Returns Bayesian conviction score [0.0 - 1.0]
        return 0.035

    def _generate_iso20022_pacs008_wire(self, fnol: FNOLPayload, amount: float) -> str:
        """Constructs a deterministic ISO 20022 Customer Credit Transfer message."""
        msg_id = f"INS-STP-{fnol.claim_id[:8]}"
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.10">
  <FIToFICstmrCdtTrf>
    <GrpHdr>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{time.strftime('%Y-%m-%dT%H:%M:%SZ')}</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
      <SttlmInf><SttlmMtd>CLRG</SttlmMtd></SttlmInf>
    </GrpHdr>
    <CdtTrfTxInf>
      <PmtId><EndToEndId>{fnol.claim_id}</EndToEndId></PmtId>
      <IntrBkSttlmAmt Ccy="USD">{amount:.2f}</IntrBkSttlmAmt>
      <Dbtr><Nm>Sovereign Casualty Insurance Corp</Nm></Dbtr>
      <Cdtr><Nm>Policyholder Settlement Account</Nm></Cdtr>
      <RmtInf><Ustrd>Auto Claim Indemnity Payout: {fnol.claim_id}</Ustrd></RmtInf>
    </CdtTrfTxInf>
  </FIToFICstmrCdtTrf>
</Document>"""


class SubrogationArbitrationEngine:
    """Inter-carrier Subrogation Arbitration & Settlement Settlement Swarm."""

    def __init__(self, carrier_code: str = "SOV-INS-001"):
        self.carrier_code = carrier_code

    def evaluate_subrogation_demand(
        self,
        claim_id: str,
        gross_payout_usd: float,
        deductible_usd: float,
        claimant_fault_pct: float,
        jurisdiction_rule: str = "MODIFIED_51"
    ) -> Dict[str, any]:
        """Evaluates statutory recovery under multi-jurisdictional comparative fault law."""
        # Calculate net recovery percentage based on jurisdiction regime
        recovery_factor = 0.0
        if jurisdiction_rule == "PURE_COMPARATIVE":
            recovery_factor = max(0.0, 1.0 - (claimant_fault_pct / 100.0))
        elif jurisdiction_rule == "MODIFIED_50":
            recovery_factor = 1.0 - (claimant_fault_pct / 100.0) if claimant_fault_pct < 50.0 else 0.0
        elif jurisdiction_rule == "MODIFIED_51":
            recovery_factor = 1.0 - (claimant_fault_pct / 100.0) if claimant_fault_pct <= 50.0 else 0.0
        elif jurisdiction_rule == "CONTRIBUTORY":
            recovery_factor = 1.0 if claimant_fault_pct == 0.0 else 0.0

        recoverable_loss = gross_payout_usd * recovery_factor
        deductible_refund = deductible_usd * recovery_factor

        return {
            "claim_id": claim_id,
            "jurisdiction_applied": jurisdiction_rule,
            "claimant_fault_percentage": claimant_fault_pct,
            "statutory_recovery_factor": round(recovery_factor, 4),
            "gross_subrogation_demand_usd": round(recoverable_loss, 2),
            "policyholder_deductible_refund_usd": round(deductible_refund, 2),
            "iso20022_demand_msg": f"pacs.008.SUBRO.{claim_id[:8]}",
            "intercarrier_arbitration_status": "AUTOMATICALLY_ACCEPTED" if recovery_factor > 0.5 else "REJECTED_DEFENSE"
        }
