# OpenTofu In-Place Binary Migration Runbook
# Step 1: Install OpenTofu RPM/DEB or binary
curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh -o install-opentofu.sh
chmod +x install-opentofu.sh
./install-opentofu.sh --install-method standalone

# Step 2: Initialize OpenTofu against existing Terraform state
tofu init -reconfigure -backend-config="backend_prod.hcl"

# Step 3: Compute state cryptographic verification
tofu plan -detailed-exitcode
