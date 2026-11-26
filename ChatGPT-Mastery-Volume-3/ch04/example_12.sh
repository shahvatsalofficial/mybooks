# Vault CLI - Requesting Ephemeral Azure OpenAI Credentials
vault write azure/creds/openai-batch-worker     ttl="30m"     max_ttl="1h"

# Sample Output Returned to Worker Microservice:
# Key                Value
# ---                -----
# client_id          8e1b4c30-9b4e-4b8a-9a1c-7f5b8e90c12a
# client_secret      vlt_dyn_s3cr3t_98f41029cba8e1
# lease_duration     30m
# lease_id           azure/creds/openai-batch-worker/h9b41a87e
