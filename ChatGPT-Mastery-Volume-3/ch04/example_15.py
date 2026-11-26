# key_rotation_webhook_handler.py
import logging
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
import os

SUBSCRIPTION_ID = os.environ["AZURE_SUBSCRIPTION_ID"]
RESOURCE_GROUP = os.environ["AZURE_RESOURCE_GROUP"]
ACCOUNT_NAME = os.environ["AZURE_OPENAI_ACCOUNT"]

def main(event: func.EventGridEvent):
    logging.info(f"Received Key Vault Rotation Event: {event.id}")
    data = event.get_json()
    new_key_version = data.get("KeyVersion")
    vault_name = data.get("VaultName")
    
    cred = DefaultAzureCredential()
    client = CognitiveServicesManagementClient(cred, SUBSCRIPTION_ID)
    
    # Retrieve current account properties
    account = client.accounts.get(RESOURCE_GROUP, ACCOUNT_NAME)
    
    # Update encryption parameters with the newly minted key version
    new_key_vault_uri = f"https://{vault_name}.vault.azure.net/keys/oai-cmk/{new_key_version}"
    account.properties.encryption.key_vault_properties.key_version = new_key_version
    
    update_op = client.accounts.begin_create_or_update(
        RESOURCE_GROUP, ACCOUNT_NAME, account
    )
    result = update_op.result()
    logging.info(f"Successfully rotated Azure OpenAI CMK to version: {new_key_version}")
