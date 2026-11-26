"""
Streaming ReAct Parser: Extracts tool actions on-the-fly during token generation.
Allows backend orchestration engines to pre-warm API connections and validate parameters
before token generation finishes.
"""

from typing import Optional, Dict, Any, Generator
import json


class StreamingReActParser:
    """Incrementally parses tokens from the LLM stream to detect tool calls early."""

    def __init__(self):
        self.buffer = ""
        self.in_thought = False
        self.in_action = False
        self.action_name: Optional[str] = None
        self.action_payload_buffer = ""

    def process_token_chunk(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Receives streaming token deltas.
        Returns a dict event when an action tag opens or completes.
        """
        self.buffer += token

        # Detect thought transitions
        if "<thought>" in self.buffer and not self.in_thought:
            self.in_thought = True

        if "</thought>" in self.buffer and self.in_thought:
            self.in_thought = False

        # Detect action tag opening
        if "<action" in self.buffer and not self.in_action:
            match = re.search(r'<action\s+name=["\'](.*?)["\']>', self.buffer)
            if match:
                self.in_action = True
                self.action_name = match.group(1)
                # Slice buffer past the tag
                self.buffer = self.buffer[match.end():]
                return {"event": "ACTION_STARTED", "action_name": self.action_name}

        # Accumulate payload while inside action
        if self.in_action:
            if "</action>" in self.buffer:
                end_pos = self.buffer.find("</action>")
                payload_str = self.buffer[:end_pos].strip()
                self.in_action = False
                completed_action = self.action_name
                self.action_name = None
                self.buffer = self.buffer[end_pos + 9:]

                try:
                    params = json.loads(payload_str)
                    return {
                        "event": "ACTION_COMPLETED",
                        "action_name": completed_action,
                        "parameters": params,
                        "valid": True
                    }
                except json.JSONDecodeError as err:
                    return {
                        "event": "ACTION_COMPLETED",
                        "action_name": completed_action,
                        "error": str(err),
                        "valid": False
                    }

        return None
