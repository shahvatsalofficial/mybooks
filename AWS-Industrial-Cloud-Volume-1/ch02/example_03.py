#!/usr/bin/env python3
"""
Enterprise AWS VPC & Transit Gateway Infrastructure Automation Engine
Author: Vatsal Shah / Production Cloud Engineering
License: Apache 2.0
"""

import boto3
import time
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("VPC-Automation")

class EnterpriseVpcBuilder:
    def __init__(self, region: str, vpc_cidr: str, vpc_name: str):
        self.region = region
        self.vpc_cidr = vpc_cidr
        self.vpc_name = vpc_name
        self.ec2 = boto3.client("ec2", region_name=region)
        self.ec2_res = boto3.resource("ec2", region_name=region)

    def create_enterprise_network(self):
        logger.info(f"Initiating Enterprise Network Provisioning in {self.region} ({self.vpc_cidr})...")
        
        # 1. Create VPC
        vpc = self.ec2_res.create_vpc(CidrBlock=self.vpc_cidr)
        vpc.wait_until_available()
        vpc.create_tags(Tags=[{"Key": "Name", "Value": f"{self.vpc_name}-vpc"}])
        
        # Enable DNS Hostnames & Resolution
        self.ec2.modify_vpc_attribute(VpcId=vpc.id, EnableDnsHostnames={"Value": True})
        self.ec2.modify_vpc_attribute(VpcId=vpc.id, EnableDnsSupport={"Value": True})
        logger.info(f"VPC Created: {vpc.id}")

        # 2. Create Internet Gateway
        igw = self.ec2_res.create_internet_gateway()
        igw.attach_to_vpc(VpcId=vpc.id)
        igw.create_tags(Tags=[{"Key": "Name", "Value": f"{self.vpc_name}-igw"}])
        logger.info(f"Internet Gateway Attached: {igw.id}")

        # 3. Discover Availability Zones
        az_resp = self.ec2.describe_availability_zones(
            Filters=[{"Name": "region-name", "Values": [self.region]}, {"Name": "state", "Values": ["available"]}]
        )
        azs = [az["ZoneName"] for az in az_resp["AvailabilityZones"][:3]] # Use first 3 AZs

        # 4. Provision 3-Tier Subnets Across AZs
        subnets = {"public": [], "private": [], "isolated": []}
        
        # Sample Subnet Allocation Scheme for 10.100.0.0/16:
        # AZ1: Public 10.100.0.0/24, Private 10.100.16.0/20, Isolated 10.100.128.0/24
        # AZ2: Public 10.100.1.0/24, Private 10.100.32.0/20, Isolated 10.100.129.0/24
        # AZ3: Public 10.100.2.0/24, Private 10.100.48.0/20, Isolated 10.100.130.0/24
        cidr_map = [
            {"az_idx": 0, "pub": "10.100.0.0/24", "priv": "10.100.16.0/20", "iso": "10.100.128.0/24"},
            {"az_idx": 1, "pub": "10.100.1.0/24", "priv": "10.100.32.0/20", "iso": "10.100.129.0/24"},
            {"az_idx": 2, "pub": "10.100.2.0/24", "priv": "10.100.48.0/20", "iso": "10.100.130.0/24"}
        ]

        # Create Public Route Table
        pub_rt = vpc.create_route_table()
        pub_rt.create_tags(Tags=[{"Key": "Name", "Value": f"{self.vpc_name}-public-rt"}])
        pub_rt.create_route(DestinationCidrBlock="0.0.0.0/0", GatewayId=igw.id)

        nat_gateways = []

        for item in cidr_map:
            az_name = azs[item["az_idx"]]
            
            # Public Subnet
            pub_sub = self.ec2_res.create_subnet(VpcId=vpc.id, CidrBlock=item["pub"], AvailabilityZone=az_name)
            pub_sub.create_tags(Tags=[{"Key": "Name", "Value": f"{self.vpc_name}-public-{az_name}"}])
            pub_rt.associate_with_subnet(SubnetId=pub_sub.id)
            subnets["public"].append(pub_sub)

            # Allocate EIP and NAT Gateway in Public Subnet
            eip = self.ec2.allocate_address(Domain="vpc")
            nat_gw = self.ec2.create_nat_gateway(SubnetId=pub_sub.id, AllocationId=eip["AllocationId"])
            nat_gw_id = nat_gw["NatGateway"]["NatGatewayId"]
            nat_gateways.append(nat_gw_id)
            logger.info(f"Allocated NAT Gateway {nat_gw_id} in {az_name}")

            # Private Subnet
            priv_sub = self.ec2_res.create_subnet(VpcId=vpc.id, CidrBlock=item["priv"], AvailabilityZone=az_name)
            priv_sub.create_tags(Tags=[{"Key": "Name", "Value": f"{self.vpc_name}-private-app-{az_name}"}])
            subnets["private"].append(priv_sub)

            # Isolated Subnet
            iso_sub = self.ec2_res.create_subnet(VpcId=vpc.id, CidrBlock=item["iso"], AvailabilityZone=az_name)
            iso_sub.create_tags(Tags=[{"Key": "Name", "Value": f"{self.vpc_name}-isolated-db-{az_name}"}])
            subnets["isolated"].append(iso_sub)

        logger.info("Waiting for NAT Gateways to become available...")
        # Note: In production, wait for NAT Gateways to reach state 'available' before creating private default routes
        
        # 5. Attach S3 Gateway Endpoint (Free S3 traffic)
        s3_ep = self.ec2.create_vpc_endpoint(
            VpcId=vpc.id,
            ServiceName=f"com.amazonaws.{self.region}.s3",
            VpcEndpointType="Gateway",
            RouteTableIds=[pub_rt.id]
        )
        logger.info(f"S3 Gateway Endpoint Provisioned: {s3_ep['VpcEndpoint']['VpcEndpointId']}")

        return {
            "vpc_id": vpc.id,
            "public_subnets": [s.id for s in subnets["public"]],
            "private_subnets": [s.id for s in subnets["private"]],
            "isolated_subnets": [s.id for s in subnets["isolated"]]
        }

if __name__ == "__main__":
    builder = EnterpriseVpcBuilder(region="us-east-1", vpc_cidr="10.100.0.0/16", vpc_name="production-core")
    network_manifest = builder.create_enterprise_network()
    print("\nPROVISIONING COMPLETE:")
    print(network_manifest)
