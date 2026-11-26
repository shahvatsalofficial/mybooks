import re
import json
from typing import Dict, Any, Callable, List, Optional
from pydantic import BaseModel, Field, ValidationError
from anthropic import Anthropic

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    executor: Callable[[Dict[str, Any]], str]

class ReActStep(BaseModel):
    thought: str
    action_name: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None

class ProductionReActAgent:
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.tools: Dict[str, ToolDefinition] = {}
        self.max_turns = 8

    def register_tool(self, name: str, description: str, schema: Dict[str, Any], executor: Callable[[Dict[str, Any]], str]):
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters_schema=schema,
            executor=executor
        )

    def _build_system_prompt(self) -> str:
        tool_descriptions = "\n\n".join([
            f"Tool: {t.name}\nDescription: {t.description}\nParameters: {json.dumps(t.parameters_schema)}"
            for t in self.tools.values()
        ])
        return (
            "You are an enterprise autonomous ReAct operations agent. "
            "You solve complex technical requests by interleaving reasoning thoughts with action tool invocations.\n\n"
            f"Available Tools:\n{tool_descriptions}\n\n"
            "Execution Protocol:\n"
            "Use the following exact format for each step:\n"
            "Thought: [Explain your reasoning, hypotheses, and strategy]\n"
            "Action: [Tool name from available tools]\n"
            "Action Input: [Valid JSON object matching tool parameters]\n\n"
            "When you receive an Observation, write your next Thought.\n"
            "When you have gathered all necessary evidence, output:\n"
            "Thought: I have verified all evidence and can conclude.\n"
            "Final Answer: [Complete, verified response]\n\n"
            "Strict Constraints:\n"
            "- Never hallucinate tool returns.\n"
            "- Always format Action Input as valid JSON.\n"
            "- If a tool returns an error, diagnose the error in your next Thought and adapt."
        )

    def execute(self, user_goal: str) -> Dict[str, Any]:
        conversation_history = f"User Request: {user_goal}\n"
        trajectory: List[ReActStep] = []
        action_history: List[str] = []

        for turn in range(self.max_turns):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.0,
                system=self._build_system_prompt(),
                messages=[{"role": "user", "content": conversation_history}]
            )
            output = response.content[0].text
            conversation_history += output + "\n"

            # Check for Final Answer
            if "Final Answer:" in output:
                final_answer = output.split("Final Answer:")[-1].strip()
                return {
                    "status": "COMPLETED",
                    "final_answer": final_answer,
                    "turns_executed": turn + 1,
                    "trajectory": trajectory
                }

            # Parse Thought and Action
            thought_match = re.search(r"Thought:(.*?)(?:Action:|$)", output, re.DOTALL)
            action_match = re.search(r"Action:\s*([a-zA-Z0-9_\-]+)", output)
            input_match = re.search(r"Action Input:\s*(\{.*?\})", output, re.DOTALL)

            thought_text = thought_match.group(1).strip() if thought_match else "Analyzing..."
            step = ReActStep(thought=thought_text)

            if action_match and input_match:
                tool_name = action_match.group(1).strip()
                raw_input = input_match.group(1).strip()

                # Action thrashing detection
                action_sig = f"{tool_name}:{raw_input}"
                if len(action_history) >= 2 and action_history[-1] == action_sig and action_history[-2] == action_sig:
                    observation_text = "ERROR: Cycle detected. You have repeated this exact action twice without success. Try an alternate tool or parameter."
                else:
                    action_history.append(action_sig)
                    
                    if tool_name not in self.tools:
                        observation_text = f"ERROR: Tool '{tool_name}' does not exist in registry. Available: {list(self.tools.keys())}"
                    else:
                        try:
                            parsed_input = json.loads(raw_input)
                            step.action_name = tool_name
                            step.action_input = parsed_input
                            # Safe sandbox execution
                            observation_text = self.tools[tool_name].executor(parsed_input)
                        except json.JSONDecodeError as e:
                            observation_text = f"ERROR: Action Input is malformed JSON: {str(e)}"
                        except Exception as e:
                            observation_text = f"ERROR: Tool execution failed: {str(e)}"

                step.observation = observation_text
                trajectory.append(step)
                
                # Append Observation back into conversation
                obs_block = f"Observation: {observation_text}\n"
                conversation_history += obs_block
            else:
                # Model failed to emit valid action format
                conversation_history += "Observation: Protocol violation. You must emit 'Action:' and 'Action Input: {...}' or 'Final Answer:'.\n"

        return {
            "status": "BUDGET_EXHAUSTED",
            "error": "Reached maximum turn limit without reaching Final Answer.",
            "trajectory": trajectory
        }
