# Enable Appliance Mode on the Inspection VPC Attachment via AWS CLI
aws ec2 modify-transit-gateway-vpc-attachment \
    --transit-gateway-attachment-id tgw-attach-0a1b2c3d4e5f67890 \
    --options ApplianceModeSupport=enable
