import json
from typing import Dict, Any, List
import vertexai
from vertexai.generative_models import GenerativeModel, Part

class GeminiReActEngine:
    """Complete ReAct autonomous reasoning engine over Gemini 2.5 Pro."""

    def __init__(self, project_id: str, tools: List[Any], dispatcher: ResilientToolDispatcher):
        self.project_id = project_id
        self.dispatcher = dispatcher
        vertexai.init(project=project_id, location="us-central1")
        self.model = GenerativeModel(
            model_name="gemini-2.5-pro",
            tools=tools,
            system_instruction=["You are an autonomous Site Reliability Engineering agent."]
        )

    def execute_turn(self, chat_session, user_prompt: str, max_hops: int = 5) -> str:
        """Executes multi-step reasoning, invoking tools sequentially until final synthesis."""
        response = chat_session.send_message(user_prompt)
        
        for hop in range(max_hops):
            # Inspect candidates for function call
            candidate = response.candidates[0]
            function_calls = [part.function_call for part in candidate.content.parts if part.function_call]
            
            if not function_calls:
                # No further tool calls requested; model reached final answer
                return response.text
            
            tool_responses = []
            for fc in function_calls:
                tool_name = fc.name
                args = {k: v for k, v in fc.args.items()}
                print(f"[Hop {hop+1}] Invoking tool: {tool_name} with args: {args}")
                
                exec_result = self.dispatcher.dispatch(tool_name, args)
                
                # Wrap tool observation back to Part
                tool_responses.append(Part.from_function_response(
                    name=tool_name,
                    response={"content": exec_result}
                ))
            
            # Send tool observations back to conversation session
            response = chat_session.send_message(tool_responses)
            
        return "ERROR: Exceeded maximum autonomous reasoning hops (5)."

if __name__ == "__main__":
    print("GeminiReActEngine class compiled successfully.")
