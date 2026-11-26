"""
key_vault_rotation_trigger.py
Azure Function: Automated Zero-Downtime Azure OpenAI Key Rotation
Triggered by Azure Event Grid on Microsoft.KeyVault.SecretNearExpiry
"""

import os
import json
import logging
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.keyvault.secrets import SecretClient


def main(event: func.EventGridEvent):
    logger = logging.getLogger("KeyRotationFunction")
    event_data = event.get_json()
    secret_name = event_data.get("ObjectName")
    logger.info(f"Received SecretNearExpiry event for Key Vault Secret: {secret_name}")

    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    resource_group = os.environ["AZURE_RESOURCE_GROUP"]
    account_name = os.environ["AZURE_OPENAI_ACCOUNT"]
    vault_url = os.environ["KEY_VAULT_URL"]

    credential = DefaultAzureCredential()
    mgmt_client = CognitiveServicesManagementClient(credential, subscription_id)
    secret_client = SecretClient(vault_url=vault_url, credential=credential)

    # 1. Determine active key from Key Vault tags
    current_secret = secret_client.get_secret(secret_name)
    active_key_slot = current_secret.properties.tags.get("ActiveSlot", "Key1")
    target_slot = "Key2" if active_key_slot == "Key1" else "Key1"

    logger.info(f"Current active slot: {active_key_slot}. Regenerating target slot: {target_slot}")

    # 2. Regenerate the inactive key slot via ARM API
    mgmt_client.accounts.regenerate_key(
        resource_group_name=resource_group,
        account_name=account_name,
        key_name=target_slot
    )

    # 3. Retrieve the newly regenerated key value
    keys = mgmt_client.accounts.list_keys(resource_group_name=resource_group, account_name=account_name)
    new_key_value = keys.key2 if target_slot == "Key2" else keys.key1

    # 4. Store the new key in Key Vault and update metadata tag
    secret_client.set_secret(
        name=secret_name,
        value=new_key_value,
        tags={"ActiveSlot": target_slot}
    )

    logger.info(f"Successfully rotated {secret_name} to slot {target_slot}. Zero downtime preserved.")
