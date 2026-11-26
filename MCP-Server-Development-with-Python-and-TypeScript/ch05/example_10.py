"""
recipe_5_1_fastmcp_prompts.py
Production Python FastMCP Prompt Template with embedded resource context.
"""

import sys
from mcp.server.fastmcp import FastMCP
from mcp.types import PromptMessage, TextContent, EmbeddedResource, TextResourceContents

mcp = FastMCP("EnterprisePromptServer")

# Internal mock security policy
SECURITY_GUIDELINES = """
# Enterprise Secure Coding Standards v4.2
1. Cryptographic algorithms must use AES-GCM-256 or RSA-4096. No DES/MD5.
2. All database queries must use parameterized bind variables. Zero string concat.
3. JWT validation must explicitly verify 'exp', 'nbf', and 'iss' claims.
"""


@mcp.prompt(
    name="security_audit_review",
    description="Prepares a comprehensive security audit prompt for a specified pull request."
)
def security_audit_review(
    pr_id: str,
    strict_compliance: bool = True
) -> list[PromptMessage]:
    """Assembles a multi-role prompt with embedded corporate security standards."""
    sys.stderr.write(f"[Prompts] Compiling security audit for PR #{pr_id}...\n")

    # Message 1: System-level role framing
    msg_system = PromptMessage(
        role="user",
        content=TextContent(
            type="text",
            text=(
                f"You are a Lead Application Security Engineer. Audit Pull Request #{pr_id}.\n"
                f"Strict compliance mode: {strict_compliance}.\n"
                "Review the attached security guidelines and evaluate all code changes against them."
            )
        )
    )

    # Message 2: Embedded Corporate Guidelines Resource
    msg_guidelines = PromptMessage(
        role="user",
        content=EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri="memo://security/corporate_standards.md",
                mimeType="text/markdown",
                text=SECURITY_GUIDELINES
            )
        )
    )

    # Message 3: Expected assistant confirmation framing
    msg_acknowledgment = PromptMessage(
        role="assistant",
        content=TextContent(
            type="text",
            text=(
                f"Understood. I have loaded the Enterprise Secure Coding Standards v4.2 into active context. "
                f"Please provide the diff for PR #{pr_id}, and I will identify any critical compliance violations."
            )
        )
    )

    return [msg_system, msg_guidelines, msg_acknowledgment]


if __name__ == "__main__":
    mcp.run(transport="stdio")
