from typing import Dict, Any

class ActionGroupSchemaBuilder:
    """Constructs valid OpenAPI 3.0 schemas for Bedrock Agent Action Groups."""
    
    @staticmethod
    def generate_cloudwatch_query_schema() -> Dict[str, Any]:
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "CloudWatch Logs Diagnostic Tool",
                "version": "1.0.0",
                "description": "Enables the autonomous agent to query enterprise application log streams."
            },
            "paths": {
                "/query_logs": {
                    "post": {
                        "summary": "Executes a CloudWatch Logs Insights query",
                        "description": "Searches application logs using CloudWatch Logs Insights query syntax.",
                        "operationId": "queryLogs",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "log_group": {
                                                "type": "string",
                                                "description": "The CloudWatch log group name (e.g. '/aws/ecs/payment-service')."
                                            },
                                            "query_string": {
                                                "type": "string",
                                                "description": "CloudWatch Logs query (e.g. 'fields @timestamp, @message | filter @message like /ERROR/ | limit 20')."
                                            },
                                            "limit": {
                                                "type": "integer",
                                                "default": 10,
                                                "description": "Maximum number of log events to return."
                                            }
                                        },
                                        "required": ["log_group", "query_string"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Successful query execution",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "status": {"type": "string"},
                                                "records_found": {"type": "integer"},
                                                "events": {
                                                    "type": "array",
                                                    "items": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

if __name__ == "__main__":
    schema = ActionGroupSchemaBuilder.generate_cloudwatch_query_schema()
    print("-> OpenAPI Schema Built:")
    print(f"   Title: {schema['info']['title']}")
    print(f"   Operations: {list(schema['paths'].keys())}")
