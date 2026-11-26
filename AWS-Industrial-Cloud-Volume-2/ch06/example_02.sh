# Trigger Route 53 ARC Zonal Shift to evacuate us-east-1a
aws arc-zonal-shift start-zonal-shift \
  --resource-identifier "arn:aws:elasticloadbalancing:us-east-1:112233445566:loadbalancer/app/prod-payment-alb/50dc6c495c0c9188" \
  --away-from "us-east-1a" \
  --expires-in "1h" \
  --comment "Evacuating impaired Availability Zone during FIS Chaos Test"
