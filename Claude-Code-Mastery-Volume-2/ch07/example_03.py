"""
aws_enterprise_mcp.py
Enterprise-grade AWS Infrastructure and DevOps Model Context Protocol Server.
Enforces STS role assumption, short-lived sessions, and CloudWatch log streaming.
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError
from mcp.server.fastmcp import FastMCP, Context

# Initialize FastMCP Server
mcp = FastMCP("enterprise-aws-mcp", version="2.0.0")

class AwsSessionManager:
    """Manages ephemeral STS credentials and role assumption."""
    
    def __init__(self, role_arn: str, external_id: Optional[str] = None):
        self.role_arn = role_arn
        self.external_id = external_id
        self._cached_credentials: Optional[Dict[str, Any]] = None
        self._expiration_time: float = 0

    def get_session(self) -> boto3.Session:
        """Returns a valid boto3 Session, refreshing STS credentials if expired."""
        if self._cached_credentials and time.time() < (self._expiration_time - 120):
            return boto3.Session(
                aws_access_key_id=self._cached_credentials['AccessKeyId'],
                aws_secret_access_key=self._cached_credentials['SecretAccessKey'],
                aws_session_token=self._cached_credentials['SessionToken']
            )

        sts_client = boto3.client('sts')
        assume_role_kwargs = {
            'RoleArn': self.role_arn,
            'RoleSessionName': 'ClaudeDevOpsSession',
            'DurationSeconds': 900  # 15 minute ephemeral lease
        }
        if self.external_id:
            assume_role_kwargs['ExternalId'] = self.external_id

        # Attach restrictive session policy restricting to read and diagnostics
        session_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "cloudwatch:GetMetricData",
                        "logs:StartQuery",
                        "logs:GetQueryResults",
                        "logs:DescribeLogGroups",
                        "ecs:DescribeTasks",
                        "ecs:ListTasks",
                        "ecs:DescribeServices",
                        "s3:ListBucket",
                        "s3:GetBucketEncryption",
                        "s3:GetBucketPolicyStatus"
                    ],
                    "Resource": "*"
                }
            ]
        }
        assume_role_kwargs['Policy'] = json.dumps(session_policy)

        response = sts_client.assume_role(**assume_role_kwargs)
        self._cached_credentials = response['Credentials']
        self._expiration_time = response['Credentials']['Expiration'].timestamp()

        return boto3.Session(
            aws_access_key_id=self._cached_credentials['AccessKeyId'],
            aws_secret_access_key=self._cached_credentials['SecretAccessKey'],
            aws_session_token=self._cached_credentials['SessionToken']
        )

# Initialize Session Manager from environment
SESSION_MANAGER = AwsSessionManager(
    role_arn=os.environ.get("AWS_AUDIT_ROLE_ARN", "arn:aws:iam::123456789012:role/ClaudeDevOpsAuditor")
)

@mcp.tool()
async def query_cloudwatch_logs(
    log_group_name: str,
    query_string: str,
    start_minutes_ago: int = 30,
    limit: int = 50,
    ctx: Context = None
) -> str:
    """
    Execute a CloudWatch Logs Insights query to extract recent log events.
    
    Args:
        log_group_name: The CloudWatch log group (e.g. /ecs/auth-service-prod)
        query_string: CloudWatch Insights query syntax (e.g. fields @timestamp, @message | filter @message like /Error/ | limit 20)
        start_minutes_ago: How many minutes in the past to query (default: 30)
        limit: Maximum results to return (max 100)
    """
    session = SESSION_MANAGER.get_session()
    logs_client = session.client('logs')
    
    start_time = int(time.time() - (start_minutes_ago * 60))
    end_time = int(time.time())
    
    try:
        start_response = logs_client.start_query(
            logGroupName=log_group_name,
            startTime=start_time,
            endTime=end_time,
            queryString=query_string,
            limit=min(limit, 100)
        )
        query_id = start_response['queryId']
        
        # Poll for query completion with exponential backoff
        for attempt in range(10):
            time.sleep(0.5 * (1.5 ** attempt))
            res = logs_client.get_query_results(queryId=query_id)
            if res['status'] == 'Complete':
                results = []
                for row in res.get('results', []):
                    entry = {field['field']: field['value'] for field in row}
                    results.append(entry)
                return json.dumps({
                    "status": "Complete",
                    "recordsScanned": res['statistics']['recordsScanned'],
                    "bytesScanned": res['statistics']['bytesScanned'],
                    "results": results
                }, indent=2)
            elif res['status'] in ['Failed', 'Cancelled']:
                return json.dumps({"status": res['status'], "error": "Query execution failed on CloudWatch."})
                
        return json.dumps({"status": "Timeout", "error": "CloudWatch query exceeded maximum wait time."})
        
    except ClientError as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
async def diagnose_ecs_service_failure(
    cluster_name: str,
    service_name: str
) -> str:
    """
    Perform an automated diagnostic triage on an ECS service with failing or crashing tasks.
    
    Args:
        cluster_name: The ECS cluster name (e.g. production-core)
        service_name: The ECS service name (e.g. billing-processor)
    """
    session = SESSION_MANAGER.get_session()
    ecs_client = session.client('ecs')
    
    try:
        # 1. Fetch service details
        svc_res = ecs_client.describe_services(cluster=cluster_name, services=[service_name])
        if not svc_res['services']:
            return json.dumps({"error": f"Service '{service_name}' not found in cluster '{cluster_name}'"})
        
        service = svc_res['services'][0]
        events = [e['message'] for e in service.get('events', [])[:5]]
        
        # 2. Fetch stopped tasks for diagnostic clues
        stopped_tasks_res = ecs_client.list_tasks(
            cluster=cluster_name,
            serviceName=service_name,
            desiredStatus='STOPPED',
            maxResults=3
        )
        
        stopped_task_details = []
        if stopped_tasks_res.get('taskArns'):
            tasks_desc = ecs_client.describe_tasks(
                cluster=cluster_name,
                tasks=stopped_tasks_res['taskArns']
            )
            for t in tasks_desc.get('tasks', []):
                container_details = []
                for c in t.get('containers', []):
                    container_details.append({
                        "name": c['name'],
                        "exitCode": c.get('exitCode'),
                        "reason": c.get('reason'),
                        "lastStatus": c.get('lastStatus')
                    })
                stopped_task_details.append({
                    "taskArn": t['taskArn'].split('/')[-1],
                    "stopCode": t.get('stopCode'),
                    "stoppedReason": t.get('stoppedReason'),
                    "containers": container_details
                })
        
        diagnosis = {
            "serviceName": service_name,
            "runningCount": service['runningCount'],
            "desiredCount": service['desiredCount'],
            "recentEvents": events,
            "stoppedTasksAnalysis": stopped_task_details
        }
        return json.dumps(diagnosis, indent=2)
        
    except ClientError as e:
        return json.dumps({"error": str(e)}, indent=2)

if __name__ == "__main__":
    mcp.run()
