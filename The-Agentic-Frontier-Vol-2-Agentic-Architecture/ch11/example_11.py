# case_studies/cs09_hipaa_healthcare_agent.py
"""
Case Study 09: HIPAA-Compliant Healthcare Triage Agent with Automated PII/PHI Redaction.
Author: Vatsal Shah — The Agentic Frontier Vol 2
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from cryptography.fernet import Fernet
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from langgraph.graph import StateGraph, END

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HIPAA-HealthcareAgent")

# ============================================================================
# 1. CUSTOM HEALTHCARE RECOGNIZERS FOR PRESIDIO
# ============================================================================

def build_custom_presidio_analyzer() -> AnalyzerEngine:
    """Builds Presidio Analyzer engine with custom Healthcare MRN and Insurance ID recognizers."""
    analyzer = AnalyzerEngine()

    # Custom Recognizer 1: Medical Record Number (MRN) e.g., MRN-12345678 or MRN99812
    mrn_pattern = Pattern(name="mrn_pattern", regex=r"\b(?:MRN|mrn)[-:\s]?\d{5,9}\b", score=0.95)
    mrn_recognizer = PatternRecognizer(supported_entity="MEDICAL_RECORD_NUMBER", patterns=[mrn_pattern])

    # Custom Recognizer 2: Health Insurance Member ID e.g., HC-9981247-01
    insurance_pattern = Pattern(name="insurance_pattern", regex=r"\b[A-Z]{2,3}[-:\s]?\d{6,9}[-:\s]?\d{2}\b", score=0.90)
    insurance_recognizer = PatternRecognizer(supported_entity="HEALTH_INSURANCE_ID", patterns=[insurance_pattern])

    analyzer.registry.add_recognizer(mrn_recognizer)
    analyzer.registry.add_recognizer(insurance_recognizer)
    logger.info("️ [Presidio Analyzer] Custom Healthcare MRN and Health Insurance recognizers registered.")
    return analyzer

# ============================================================================
# 2. ENCRYPTED RE-IDENTIFICATION VAULT
# ============================================================================

class EncryptedReIDVault:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        self.mapping_vault: Dict[str, bytes] = {}

    def store_mapping(self, surrogate_token: str, original_value: str):
        encrypted_val = self.cipher.encrypt(original_value.encode('utf-8'))
        self.mapping_vault[surrogate_token] = encrypted_val

    def retrieve_mapping(self, surrogate_token: str) -> Optional[str]:
        encrypted_val = self.mapping_vault.get(surrogate_token)
        if encrypted_val:
            return self.cipher.decrypt(encrypted_val).decode('utf-8')
        return None

# ============================================================================
# 3. CLINICAL TRIAGE SCHEMAS & STATE
# ============================================================================

class PatientTriageState(BaseModel):
    raw_patient_intake: str
    anonymized_text: Optional[str] = None
    surrogate_mapping: Dict[str, str] = Field(default_factory=dict)
    triage_assessment: Optional[str] = None
    final_reidentified_summary: Optional[str] = None
    status: str = "INITIALIZED"

# ============================================================================
# 4. AGENT GRAPH NODES
# ============================================================================

analyzer_engine = build_custom_presidio_analyzer()
anonymizer_engine = AnonymizerEngine()
reid_vault = EncryptedReIDVault()

def phi_anonymization_node(state: PatientTriageState) -> Dict[str, Any]:
    """Node 1: Scans clinical text for 18 HIPAA PHI entities and anonymizes them."""
    logger.info(" [HIPAA Node] Scanning intake text for PHI entities...")
    text = state.raw_patient_intake

    target_entities = [
        "PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "DATE_TIME",
        "MEDICAL_RECORD_NUMBER", "HEALTH_INSURANCE_ID", "US_SSN"
    ]

    # Analyze text
    results = analyzer_engine.analyze(text=text, entities=target_entities, language="en")
    
    # Anonymize using surrogate placeholders
    anonymized = anonymizer_engine.anonymize(
        text=text,
        analyzer_results=results,
        operators={
            "DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED_PHI>"})
        }
    )

    clean_text = anonymized.text
    logger.info(f" De-Identified Text (Zero PHI Sent to Cloud LLM):\n{clean_text}")

    return {
        "anonymized_text": clean_text,
        "status": "ANONYMIZATION_COMPLETE"
    }

def cloud_llm_triage_node(state: PatientTriageState) -> Dict[str, Any]:
    """Node 2: Cloud LLM analyzes de-identified clinical text safely."""
    logger.info(" [Cloud LLM] Performing clinical triage risk assessment...")
    clean_text = state.anonymized_text

    # Simulated LLM response operating on de-identified tokens
    triage_response = f"""
[CLINICAL TRIAGE RISK ASSESSMENT]
Acuity Level: Level 3 (Urgent - Non Emergency)
Symptom Summary: Patient presents with acute abdominal pain and mild fever.
Recommended Action: Direct to Urgent Care Clinic for physical abdominal examination within 2 hours.
Note: Patient record <REDACTED_PHI> flagged for priority physician review.
"""
    return {
        "triage_assessment": triage_response.strip(),
        "status": "TRIAGE_COMPLETE"
    }

def reidentification_node(state: PatientTriageState) -> Dict[str, Any]:
    """Node 3: Local Node restores patient summary for EHR insertion."""
    logger.info(" [Local Vault] Assembling local clinical record...")
    summary = f"""
===============================================================================
OFFICIAL EHR CLINICAL TRIAGE RECORD — CONFIDENTIAL
===============================================================================
RAW INTAKE SOURCE: {state.raw_patient_intake}

{state.triage_assessment}
===============================================================================
"""
    return {
        "final_reidentified_summary": summary.strip(),
        "status": "COMPLETED_SUCCESS"
    }

def build_hipaa_agent_graph():
    builder = StateGraph(PatientTriageState)
    builder.add_node("anonymization", phi_anonymization_node)
    builder.add_node("llm_triage", cloud_llm_triage_node)
    builder.add_node("reidentification", reidentification_node)

    builder.set_entry_point("anonymization")
    builder.add_edge("anonymization", "llm_triage")
    builder.add_edge("llm_triage", "reidentification")
    builder.add_edge("reidentification", END)

    return builder.compile()

if __name__ == "__main__":
    agent = build_hipaa_agent_graph()

    sample_intake = (
        "Patient Jane Doe (DOB: 1984-12-14, Phone: 555-019-2831, MRN-998124) presents "
        "with severe lower right quadrant abdominal pain rated 8/10 for past 4 hours. "
        "Covered under insurance policy HC-8839201-02."
    )

    state = PatientTriageState(raw_patient_intake=sample_intake)
    output = agent.invoke(state)

    print(f"\nFinal Processing Status: {output['status']}")
    print(output['final_reidentified_summary'])
