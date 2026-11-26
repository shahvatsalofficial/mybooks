class CrewOutputGuardrail:
    FORBIDDEN_PATTERNS = ["TODO", "PLACEHOLDER", "AS AN AI", "I CANNOT ASSIST"]

    @classmethod
    def validate_and_enforce(cls, output_text: str) -> bool:
        upper = output_text.upper()
        for pattern in cls.FORBIDDEN_PATTERNS:
            if pattern in upper:
                raise ValueError(f"Output Guardrail Rejection: Found forbidden pattern '{pattern}' in final draft.")
        print("[GUARDRAIL] Output verified! Zero forbidden tokens or AI caveats detected.")
        return True
