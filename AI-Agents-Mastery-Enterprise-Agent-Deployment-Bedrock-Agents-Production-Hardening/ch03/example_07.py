from typing import Dict, Any
import requests
from azure.identity import DefaultAzureCredential

class MicrosoftGraphToolGateway:
    """Queries Microsoft Graph API using Entra ID Workload Identity tokens."""

    def __init__(self, tenant_id: str):
        self.credential = DefaultAzureCredential()
        self.scope = "https://graph.microsoft.com/.default"

    def get_user_profile(self, user_principal_name: str) -> Dict[str, Any]:
        """Retrieves employee department, manager, and office location."""
        token = self.credential.get_token(self.scope).token
        headers = {"Authorization": f"Bearer {token}", "ConsistencyLevel": "eventual"}
        
        url = f"https://graph.microsoft.com/v1.0/users/{user_principal_name}?$select=displayName,jobTitle,department,officeLocation"
        
        # Simulated response for testing environment
        return {
            "displayName": "Sarah Jenkins",
            "jobTitle": "Principal Cloud Security Architect",
            "department": "Enterprise Information Security",
            "officeLocation": "Building 43 / Seattle, WA"
        }

if __name__ == "__main__":
    gw = MicrosoftGraphToolGateway("contoso-tenant-01")
    profile = gw.get_user_profile("sjenkins@contoso.com")
    print(f"Retrieved profile for {profile['displayName']} ({profile['jobTitle']})")
