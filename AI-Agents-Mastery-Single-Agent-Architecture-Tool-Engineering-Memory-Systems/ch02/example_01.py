import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

class ReActStep(BaseModel):
    thought: str
    action_tool: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    final_answer: Optional[str] = None

class RobustReActParser:
    """Parses raw LLM completions into structured ReAct steps with graceful fallbacks."""
    
    ACTION_REGEX = re.compile(
        r"Action:\s*([a-zA-Z0-9_\-]+)\s*(?:```(?:json)?\s*)?(\{.*?\})(?:\s*```)?", 
        re.DOTALL
    )
    FINAL_REGEX = re.compile(r"Final Answer:\s*(.*)", re.DOTALL)
    THOUGHT_REGEX = re.compile(r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)", re.DOTALL)

    @classmethod
    def parse(cls, completion: str) -> ReActStep:
        # 1. Check for Final Answer
        final_match = cls.FINAL_REGEX.search(completion)
        if final_match:
            thought_match = cls.THOUGHT_REGEX.search(completion)
            thought = thought_match.group(1).strip() if thought_match else "Concluding task."
            return ReActStep(thought=thought, final_answer=final_match.group(1).strip())

        # 2. Extract Thought
        thought_match = cls.THOUGHT_REGEX.search(completion)
        thought = thought_match.group(1).strip() if thought_match else "Reasoning step."

        # 3. Extract Action & Parameters
        action_match = cls.ACTION_REGEX.search(completion)
        if not action_match:
            # Fallback check for missing JSON braces
            relaxed_match = re.search(r"Action:\s*([a-zA-Z0-9_\-]+)\s*\((.*)\)", completion, re.DOTALL)
            if relaxed_match:
                tool_name = relaxed_match.group(1).strip()
                raw_args = relaxed_match.group(2).strip()
                try:
                    args_dict = json.loads(raw_args) if raw_args.startswith("{") else {"raw_input": raw_args}
                    return ReActStep(thought=thought, action_tool=tool_name, action_input=args_dict)
                except Exception:
                    return ReActStep(thought=thought, action_tool=tool_name, action_input={"raw_input": raw_args})
            
            return ReActStep(thought=thought, final_answer=f"Could not parse valid Action from completion: '{completion[:100]}...'")

        tool_name = action_match.group(1).strip()
        raw_json = action_match.group(2).strip()
        try:
            parsed_args = json.loads(raw_json)
        except json.JSONDecodeError as err:
            # Automatic schema repair for unquoted keys
            repaired = re.sub(r'(\w+):', r'"\1":', raw_json)
            try:
                parsed_args = json.loads(repaired)
            except Exception:
                raise ValueError(f"Malformed JSON in tool action '{tool_name}': {raw_json}") from err

        return ReActStep(thought=thought, action_tool=tool_name, action_input=parsed_args)

# Verification
sample_output = """Thought: I need to verify customer status in Stripe.
Action: fetch_stripe_customer
{"customer_id": "cus_N8x02L", "expand": ["subscriptions"]}"""

step = RobustReActParser.parse(sample_output)
print(f"Parsed Tool: {step.action_tool}")
print(f"Parsed Input: {step.action_input}")
