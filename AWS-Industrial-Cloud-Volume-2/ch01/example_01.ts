// lib/industrial-vpc-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';

export interface IndustrialVpcProps extends cdk.StackProps {
  readonly maxAzs: number;
  readonly cidrBlock: string;
}

export class IndustrialVpcStack extends cdk.Stack {
  public readonly vpc: ec2.IVpc;

  constructor(scope: Construct, id: string, props: IndustrialVpcProps) {
    super(scope, id, props);

    // L2 Construct: Batteried defaults with VPC Flow Logs and Subnet Allocation
    this.vpc = new ec2.Vpc(this, 'EnterpriseCoreVpc', {
      ipAddresses: ec2.IpAddresses.cidr(props.cidrBlock),
      maxAzs: props.maxAzs,
      natGateways: props.maxAzs,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: 'PublicIngress',
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          cidrMask: 22,
          name: 'ApplicationWorkloads',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
        {
          cidrMask: 24,
          name: 'IsolatedDatabaseTier',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        }
      ],
      flowLogs: {
        'CloudWatchFlowLogs': {
          destination: ec2.FlowLogDestination.toCloudWatch(),
          trafficType: ec2.FlowLogTrafficType.ALL,
        }
      }
    });

    cdk.Tags.of(this).add('Environment', 'Production');
    cdk.Tags.of(this).add('Compliance', 'SOC2-TypeII');
  }
}
