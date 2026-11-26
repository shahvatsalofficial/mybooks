# train_custom_document_model.py — Neural Layout Model Training
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceAdministrationClient
from azure.ai.documentintelligence.models import BuildDocumentModelRequest, DocumentBuildMode

def train_custom_model(endpoint: str, key: str, blob_container_sas: str, model_id: str):
    admin_client = DocumentIntelligenceAdministrationClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    request = BuildDocumentModelRequest(
        model_id=model_id,
        build_mode=DocumentBuildMode.NEURAL,
        azure_blob_source={"container_url": blob_container_sas},
        description="Enterprise Custom Aerospace Spec Extraction Model v1.0"
    )

    print(f"Beginning custom neural model training for {model_id}...")
    poller = admin_client.begin_build_document_model(request)
    model = poller.result()
    print(f"Model Training Complete! Model ID: {model.model_id} | Created: {model.created_on}")
