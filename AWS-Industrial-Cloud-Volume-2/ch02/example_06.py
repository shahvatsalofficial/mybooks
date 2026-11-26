#!/usr/bin/env python3
"""
AWS Industrial Cloud Series — Volume 2
Production Tool: CodeDeploy AfterAllowTestTraffic Synthetic Verification Hook
Author: Vatsal Shah
"""

import json
import urllib.request
import urllib.error
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

codedeploy = boto3.client('codedeploy')

def lambda_handler(event, context):
    logger.info("Received CodeDeploy lifecycle event: %s", json.dumps(event))

    deployment_id = event.get('DeploymentId')
    lifecycle_event_hook_execution_id = event.get('LifecycleEventHookExecutionId')

    # Test endpoint on ALB Test Listener Port 8443
    test_endpoint = "https://test-internal.enterprise-cloud.io:8443/healthz"
    test_passed = False

    try:
        req = urllib.request.Request(
            test_endpoint,
            headers={'User-Agent': 'CodeDeploy-PreFlight-Synthetics/2.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            body = response.read().decode('utf-8')
            payload = json.loads(body)

            if status_code == 200 and payload.get('status') == 'HEALTHY':
                logger.info("✅ Synthetic test PASSED. Container is healthy: %s", body)
                test_passed = True
            else:
                logger.error("❌ Synthetic test FAILED: Invalid payload: %s", body)

    except urllib.error.HTTPError as http_err:
        logger.error("❌ Synthetic test HTTP error: %d - %s", http_err.code, http_err.reason)
    except Exception as err:
        logger.error("❌ Synthetic test failed with exception: %s", str(err))

    # Report status back to CodeDeploy control plane
    execution_status = 'Succeeded' if test_passed else 'Failed'
    
    response = codedeploy.put_lifecycle_event_hook_execution_status(
        deploymentId=deployment_id,
        lifecycleEventHookExecutionId=lifecycle_event_hook_execution_id,
        status=execution_status
    )

    logger.info("Reported '%s' status to CodeDeploy: %s", execution_status, response)
    return {'statusCode': 200, 'body': json.dumps({'status': execution_status})}
