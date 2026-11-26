class ResearchWorker:
    def __init__(self, name: str = "ResearchAgent_01"):
        self.name = name
        self.role = AgentRole.RESEARCHER
        self.knowledge_base = {
            "oauth2": "OAuth 2.0 uses authorization codes, PKCE, and refresh tokens for delegated authorization.",
            "jwt": "JSON Web Tokens are compact URL-safe tokens with Header, Payload, and Signature sections.",
            "cors": "Cross-Origin Resource Sharing defines headers for restricted resource requests outside origin domain."
        }

    def process_message(self, message: AgentMessage) -> AgentMessage:
        query = message.content.lower()
        findings = []
        for key, text in self.knowledge_base.items():
            if key in query:
                findings.append(f"[{key.upper()} Domain Knowledge]: {text}")
        
        result_content = "\n".join(findings) if findings else f"No direct domain match found for query: '{message.content}'. Standard protocols apply."
        return AgentMessage(
            sender=self.name,
            sender_role=self.role,
            recipient=message.sender,
            message_type=MessageType.TASK_RESULT,
            content=result_content,
            parent_id=message.message_id,
            metadata={"execution_time_ms": 12.4, "confidence": 0.94}
        )

class CodeWorker:
    def __init__(self, name: str = "CodeAgent_01"):
        self.name = name
        self.role = AgentRole.CODER

    def process_message(self, message: AgentMessage) -> AgentMessage:
        spec = message.content
        if "oauth2" in spec.lower():
            code_snippet = (
                "import hashlib, os, base64\n"
                "def generate_pkce_pair():\n"
                "    verifier = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('=')\n"
                "    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')\n"
                "    return verifier, challenge\n"
            )
        else:
            code_snippet = "# Generic secure token stub\nimport secrets\ntoken = secrets.token_hex(32)\n"

        return AgentMessage(
            sender=self.name,
            sender_role=self.role,
            recipient=message.sender,
            message_type=MessageType.TASK_RESULT,
            content=code_snippet,
            parent_id=message.message_id,
            metadata={"language": "python", "lines": len(code_snippet.splitlines())}
        )

class SecurityAuditorWorker:
    def __init__(self, name: str = "SecurityAuditor_01"):
        self.name = name
        self.role = AgentRole.AUDITOR

    def process_message(self, message: AgentMessage) -> AgentMessage:
        code_to_audit = message.content
        issues = []
        if "eval(" in code_to_audit or "exec(" in code_to_audit:
            issues.append("CRITICAL: Detected dangerous dynamic execution call.")
        if "os.urandom" in code_to_audit and "hashlib.sha256" in code_to_audit:
            issues.append("PASS: Cryptographically secure random number and hashing algorithms utilized.")
        
        passed = len([i for i in issues if "CRITICAL" in i]) == 0
        return AgentMessage(
            sender=self.name,
            sender_role=self.role,
            recipient=message.sender,
            message_type=MessageType.CRITIQUE,
            content=f"Audit Status: {'APPROVED' if passed else 'REJECTED'}\nFindings: {'; '.join(issues)}",
            parent_id=message.message_id,
            metadata={"audit_passed": passed, "vulnerabilities_found": 0 if passed else 1}
        )
