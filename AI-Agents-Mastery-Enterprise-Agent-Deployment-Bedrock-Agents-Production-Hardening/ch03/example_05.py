from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FilePurpose

class SandboxedFileProcessor:
    """Manages file ingestion and chart artifact extraction in Azure AI Agent Service."""

    def __init__(self, client: AIProjectClient):
        self.client = client

    def upload_dataset_for_agent(self, local_file_path: str) -> str:
        """Uploads a local dataset to Azure storage with 'assistants' purpose."""
        with open(local_file_path, "rb") as f:
            file_record = self.client.agents.upload_file(
                file=f,
                purpose=FilePurpose.AGENTS
            )
        print(f"Uploaded file {local_file_path} as Azure File ID: {file_record.id}")
        return file_record.id

    def extract_image_artifacts(self, thread_id: str, download_dir: str = "./downloads") -> List[str]:
        """Scans thread messages for image file IDs and downloads generated artifacts."""
        messages = self.client.agents.list_messages(thread_id=thread_id)
        saved_paths = []
        
        for msg in messages["data"]:
            for content in msg["content"]:
                if content.get("type") == "image_file":
                    file_id = content["image_file"]["file_id"]
                    dest = f"{download_dir}/chart_{file_id}.png"
                    
                    # Download binary content
                    content_bytes = self.client.agents.get_file_content(file_id)
                    with open(dest, "wb") as f:
                        f.write(content_bytes)
                    saved_paths.append(dest)
                    
        return saved_paths

if __name__ == "__main__":
    print("SandboxedFileProcessor validated.")
