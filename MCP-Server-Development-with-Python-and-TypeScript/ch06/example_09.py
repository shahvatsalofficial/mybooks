"""
recipe_6_2_pydantic_hardened_validation.py
Advanced Pydantic v2 validation rules and custom field validators for FastMCP.
"""

import re
from typing import Literal
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator

mcp = FastMCP("HardenedSecurityServer")

# Disallowed dangerous shell characters
SHELL_METACHACTERS = re.compile(r"[;&|`$><\n\r]")


class GitBranchCreationRequest(BaseModel):
    repository: str = Field(
        ...,
        pattern="^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$",
        description="Target GitHub repository in 'owner/repo' format."
    )
    branch_name: str = Field(
        ...,
        min_length=3,
        max_length=60,
        description="Git branch name complying with semantic branch naming conventions."
    )
    branch_type: Literal["feature", "bugfix", "hotfix", "chore"] = Field(
        ...,
        description="Standardized branch classification prefix."
    )

    @field_validator("branch_name")
    @classmethod
    def validate_branch_name(cls, v: str, info) -> str:
        """Enforces enterprise git branch naming standards and sanitizes input."""
        if SHELL_METACHACTERS.search(v):
            raise ValueError("Branch name contains illegal shell metacharacters (; & | ` $ > <).")

        # Ensure branch starts with an alphanumeric token
        if not v[0].isalnum():
            raise ValueError("Branch name must begin with an alphanumeric character.")

        # Disallow double dots or trailing slashes
        if ".." in v or v.endswith("/"):
            raise ValueError("Branch name cannot contain consecutive dots ('..') or trailing slashes.")

        return v.lower()


@mcp.tool()
def create_enterprise_branch(req: GitBranchCreationRequest) -> str:
    """Creates a validated, policy-compliant git branch in an enterprise repository."""
    full_ref = f"refs/heads/{req.branch_type}/{req.branch_name}"
    return f"Successfully created branch '{full_ref}' on repository '{req.repository}'."


if __name__ == "__main__":
    mcp.run(transport="stdio")
