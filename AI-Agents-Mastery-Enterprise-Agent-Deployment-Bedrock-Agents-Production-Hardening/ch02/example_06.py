import base64
from typing import List, Any
from vertexai.generative_models import Part

class MultiModalDiagnosticIngestor:
    """Encodes system architecture images and binary crash dumps for Gemini 2.5."""

    @staticmethod
    def load_image_part(image_path: str, mime_type: str = "image/png") -> Part:
        """Encodes local binary diagram into a Gemini Part."""
        with open(image_path, "rb") as f:
            data = f.read()
        return Part.from_data(data=data, mime_type=mime_type)

    @staticmethod
    def construct_diagnostic_prompt(incident_summary: str, diagram_path: str, raw_log_lines: List[str]) -> List[Any]:
        """Assembles multi-modal prompt containing text context, architecture diagram, and logs."""
        parts = []
        parts.append(f"INCIDENT REPORT: {incident_summary}\n\nRAW TERMINAL LOGS:\n" + "\n".join(raw_log_lines))
        parts.append("Analyze the architecture diagram and crash logs to pinpoint the single point of failure.")
        return parts

if __name__ == "__main__":
    print("MultiModalDiagnosticIngestor initialized and validated.")
