#!/usr/bin/env bash
# /opt/enterprise/bin/vault-git-credential-helper
# Invoked dynamically by git when authentication is required.

set -euo pipefail

if [ "$1" = "get" ]; then
  # Request short-lived token from local in-memory Vault proxy daemon
  TOKEN=$(curl -s --unix-socket /run/vault/proxy.sock http://localhost/v1/github/token | jq -r '.data.token')
  
  echo "protocol=https"
  echo "host=github.com"
  echo "username=x-access-token"
  echo "password=${TOKEN}"
  exit 0
fi

exit 0
