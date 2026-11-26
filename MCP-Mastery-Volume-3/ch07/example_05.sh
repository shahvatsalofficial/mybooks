# Verify if the provider artifact is safe to deploy against production consumer versions
pact-broker can-i-deploy \
  --pacticipant mcp-server-crm \
  --version ${GIT_COMMIT} \
  --to-environment production \
  --broker-base-url https://pact-broker.internal.corp
