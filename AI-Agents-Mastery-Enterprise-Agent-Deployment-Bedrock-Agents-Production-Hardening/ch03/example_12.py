from typing import Dict, Any

class PurviewClassificationGate:
    """Inspects Microsoft Purview sensitivity labels prior to agent document ingestion."""

    RESTRICTED_LABELS = {"Confidential_HR", "Secret_Financial", "Strictly_Confidential_PHI"}

    @classmethod
    def evaluate_document_sensitivity(cls, document_uri: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        purview_label = metadata.get("purview_classification", "Public")
        is_restricted = purview_label in cls.RESTRICTED_LABELS
        
        return {
            "document_uri": document_uri,
            "purview_label": purview_label,
            "ingestion_allowed": True,
            "enforce_sandbox_isolation": is_restricted,
            "disable_persistent_logging": is_restricted,
            "security_clearance_required": "Tier3_Executive" if is_restricted else "General_Access"
        }

if __name__ == '__main__':
    doc_meta = {"purview_classification": "Secret_Financial", "author": "treasury@contoso.com"}
    gate_eval = PurviewClassificationGate.evaluate_document_sensitivity("adls2://fin-lake/q3_forecast.xlsx", doc_meta)
    print("Purview Gate Evaluation:")
    print(f" - Document: {gate_eval['document_uri']}")
    print(f" - Restricted Mode: {gate_eval['enforce_sandbox_isolation']}")
