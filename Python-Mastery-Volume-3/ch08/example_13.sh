# Automated security container audit
trivy image --severity HIGH,CRITICAL --exit-code 1 my-app:3.0.0
