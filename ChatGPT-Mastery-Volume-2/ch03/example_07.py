"""
Production Assistant Event Stream Handler
Author: Vatsal Shah, Enterprise AI Architect
Captures streaming text tokens, code interpreter steps, and tool dispatches in real time.
"""
import sys
from typing_extensions import override
from openai import AssistantEventHandler
from openai.types.beta.threads import TextDelta, MessageDelta
from openai.types.beta.threads.runs import ToolCall, ToolCallDelta

class EnterpriseStreamEventHandler(AssistantEventHandler):
    def __init__(self):
        super().__init__()
        self.accumulated_text = ""
        self.active_tool_calls = []

    @override
    def on_text_created(self, text) -> None:
        sys.stdout.write("
Assistant: ")
        sys.stdout.flush()

    @override
    def on_text_delta(self, delta: TextDelta, snapshot) -> None:
        if delta.value:
            self.accumulated_text += delta.value
            sys.stdout.write(delta.value)
            sys.stdout.flush()

    @override
    def on_tool_call_created(self, tool_call: ToolCall) -> None:
        sys.stdout.write(f"
[Tool Activated: {tool_call.type}] ")
        sys.stdout.flush()

    @override
    def on_tool_call_delta(self, delta: ToolCallDelta, snapshot) -> None:
        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                sys.stdout.write(delta.code_interpreter.input)
                sys.stdout.flush()
        elif delta.type == "function":
            if delta.function.arguments:
                # Accumulate partial JSON arguments
                pass

    @override
    def on_event(self, event) -> None:
        # Intercept requires_action to signal client dispatcher
        if event.event == "thread.run.requires_action":
            print(f"
⚡ Run requires external tool execution! Run ID: {event.data.id}")
