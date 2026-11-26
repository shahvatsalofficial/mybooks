import json
import boto3

def lambda_handler(event, context):
    invoking_event = json.loads(event['invokingEvent'])
    configuration_item = invoking_event['configurationItem']
    result_token = event['resultToken']
    config_client = boto3.client('config')
    
    resource_type = configuration_item['resourceType']
    resource_id = configuration_item['resourceId']
    
    compliance_status = 'COMPLIANT'
    annotation = 'Resource complies with enterprise TLS 1.3 security baseline.'
    
    # Custom Evaluation: Ensure ALB uses approved TLS 1.3 security policy
    if resource_type == 'AWS::ElasticLoadBalancingV2::LoadBalancer':
        listeners = configuration_item.get('configuration', {}).get('listeners', [])
        for listener in listeners:
            ssl_policy = listener.get('sslPolicy', '')
            if ssl_policy != 'ELBSecurityPolicy-TLS13-1-2-2021-06':
                compliance_status = 'NON_COMPLIANT'
                annotation = f'Non-compliant SSL policy detected: {ssl_policy}'
                break
                
    config_client.put_evaluations(
        Evaluations=[{
            'ComplianceResourceType': resource_type,
            'ComplianceResourceId': resource_id,
            'ComplianceType': compliance_status,
            'Annotation': annotation,
            'OrderingTimestamp': configuration_item['configurationItemCaptureTime']
        }],
        ResultToken=result_token
    )
    return {'statusCode': 200, 'body': 'Evaluation recorded'}
