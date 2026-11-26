class CloudSecMockSuite:
    @staticmethod
    def lookup_iam_user(params: Dict[str, Any]) -> str:
        username = params.get("username", "")
        if "contractor" in username.lower():
            return json.dumps({
                "user_id": "usr_99812_ext",
                "arn": "arn:aws:iam::112233445566:user/devops_contractor",
                "status": "Active",
                "created_date": "2026-06-15"
            })
        return json.dumps({"error": f"User '{username}' not found in active directory."})

    @staticmethod
    def query_cloudtrail_events(params: Dict[str, Any]) -> str:
        user_id = params.get("user_id")
        event_name = params.get("event_name")
        if user_id == "usr_99812_ext" and event_name == "RunInstances":
            return json.dumps({
                "events": [
                    {"instance_id": "i-09ab12cd34ef56", "timestamp": "2026-08-12T14:22:00Z", "region": "us-east-1"},
                    {"instance_id": "i-077123aa44bb99", "timestamp": "2026-09-04T09:15:30Z", "region": "us-east-1"}
                ]
            })
        return json.dumps({"events": []})

    @staticmethod
    def describe_instance_volumes(params: Dict[str, Any]) -> str:
        inst_id = params.get("instance_id")
        if inst_id == "i-09ab12cd34ef56":
            return json.dumps({"volume_id": "vol-0123456789abcdef0", "encrypted": True, "kms_key_id": "alias/aws/ebs"})
        elif inst_id == "i-077123aa44bb99":
            return json.dumps({"volume_id": "vol-99887766554433221", "encrypted": False, "kms_key_id": None})
        return json.dumps({"error": "Instance not found."})

# Example Wiring
agent = ProductionReActAgent(api_key="sk-test-dummy")
agent.register_tool(
    name="lookup_iam_user",
    description="Resolves corporate username to IAM user ID and metadata.",
    schema={"username": {"type": "string"}},
    executor=CloudSecMockSuite.lookup_iam_user
)
agent.register_tool(
    name="query_cloudtrail_events",
    description="Queries AWS CloudTrail audit logs for API actions initiated by a user ID.",
    schema={"user_id": {"type": "string"}, "event_name": {"type": "string"}},
    executor=CloudSecMockSuite.query_cloudtrail_events
)
agent.register_tool(
    name="describe_instance_volumes",
    description="Inspects EBS volume encryption configuration for an EC2 instance ID.",
    schema={"instance_id": {"type": "string"}},
    executor=CloudSecMockSuite.describe_instance_volumes
)
