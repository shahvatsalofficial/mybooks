#!/usr/bin/env python3
"""
Autonomous Bedrock Multi-Agent Orchestrator with Guardrails & RAG
AWS Industrial Cloud Series — Volume 3
Author: Vatsal Shah (Enterprise Security & AI Architect)
"""

import boto3
import json
import logging
import time
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class SovereignBedrockAgentOrchestrator:
    def __init__(
        self,
        guardrail_id: str,
        guardrail_version: str = "DRAFT",
        knowledge_base_id: Optional[str] = None,
        model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0",
        region_name: str = "us-east-1"
    ):
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=region_name)
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version
        self.knowledge_base_id = knowledge_base_id
        self.model_id = model_id
        self.region = region_name

    def apply_guardrail_preflight(self, text_input: str) -> Dict[str, Any]:
        """
        Executes pre-inference safety inspection via Bedrock Guardrails.
        """
        logger.info("Executing Bedrock Guardrails pre-flight prompt evaluation...")
        response = self.bedrock_runtime.apply_guardrail(
            guardrailIdentifier=self.guardrail_id,
            guardrailVersion=self.guardrail_version,
            source='INPUT',
            content=[{'text': {'text': text_input}}]
        )
        action = response.get('action')
        if action == 'GUARDRAIL_INTERVENED':
            logger.warning("Prompt VIOLATED enterprise guardrails! Execution blocked.")
            return {
                "allowed": False,
                "action": action,
                "outputs": response.get('outputs', [{}])[0].get('text', 'Blocked by policy.')
            }
        return {"allowed": True, "action": action, "outputs": text_input}

    def retrieve_rag_context(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves grounded context from OpenSearch Serverless via Bedrock Knowledge Bases.
        """
        if not self.knowledge_base_id:
            return []
        
        logger.info(f"Querying Knowledge Base [{self.knowledge_base_id}] with hybrid search...")
        response = self.bedrock_agent_runtime.retrieve(
            knowledgeBaseId=self.knowledge_base_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': top_k,
                    'overrideSearchType': 'HYBRID'
                }
            }
        )
        results = []
        for match in response.get('retrievalResults', []):
            results.append({
                "content": match.get('content', {}).get('text'),
                "score": match.get('score'),
                "location": match.get('location', {}).get('s3Location', {}).get('uri')
            })
        logger.info(f"Retrieved {len(results)} grounded chunks from OpenSearch Serverless.")
        return results

    def invoke_grounded_agent(self, user_prompt: str) -> Dict[str, Any]:
        """
        Orchestrates full safe inference cycle: Guardrails -> RAG -> Foundation Model -> Post-Guardrails.
        """
        # Step 1: Pre-flight Guardrails Check
        preflight = self.apply_guardrail_preflight(user_prompt)
        if not preflight["allowed"]:
            return {"status": "BLOCKED", "response": preflight["outputs"]}

        # Step 2: Retrieve Grounded Context
        context_chunks = self.retrieve_rag_context(user_prompt, top_k=3)
        context_str = "\n\n".join([f"[Source: {c['location']}]: {c['content']}" for c in context_chunks])

        # Step 3: Construct Grounded System Prompt
        system_prompt = (
            "You are the Sovereign Financial AI Agent. Answer strictly using the provided context. "
            "If the answer is not present in the context, respond that you do not have sufficient data."
        )
        user_message = f"<context>\n{context_str}\n</context>\n\nUser Question: {user_prompt}"

        # Step 4: Invoke Foundation Model with Guardrails Configuration
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.0,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}]
        })

        logger.info(f"Invoking Foundation Model [{self.model_id}]...")
        start_time = time.perf_counter()
        
        response = self.bedrock_runtime.invoke_model(
            modelId=self.model_id,
            body=body,
            guardrailIdentifier=self.guardrail_id,
            guardrailVersion=self.guardrail_version,
            trace='ENABLED'
        )
        latency = (time.perf_counter() - start_time) * 1000.0
        response_body = json.loads(response['body'].read())
        completion = response_body.get('content', [{}])[0].get('text', '')

        logger.info(f"Model generation completed in {latency:.2f} ms.")
        return {
            "status": "SUCCESS",
            "latency_ms": latency,
            "response": completion,
            "sources": [c['location'] for c in context_chunks]
        }

if __name__ == "__main__":
    agent = SovereignBedrockAgentOrchestrator(
        guardrail_id="gr-sovereign-01",
        guardrail_version="1",
        knowledge_base_id="kb-fin-ledger-99"
    )
    print("Sovereign Bedrock Agent Orchestrator initialized and ready for production inference.")
