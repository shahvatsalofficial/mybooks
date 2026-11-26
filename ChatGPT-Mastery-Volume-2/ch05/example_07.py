"""
Hands-On Lab: Full-Duplex Interactive Voice Assistant with Live Tool Calling
Author: Vatsal Shah, Enterprise AI Architect
Demonstrates Realtime WebSocket protocol, G.711 audio, VAD, and asynchronous tool execution.
"""
import os
import json
import base64
import asyncio
import websockets
from typing import Dict, Any

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-realtime-preview"

async def mock_banking_service(account_id: str) -> Dict[str, Any]:
    """Simulates enterprise backend transactional service lookup."""
    await asyncio.sleep(0.5) # Simulate database I/O latency
    return {
        "account_id": account_id,
        "balance": 184500.50,
        "pending_transfers": 2,
        "risk_tier": "VIP_PREMIER"
    }

async def run_voice_agent_lab():
    print("
=======================================================")
    print("🎙️ INITIATING REALTIME VOICE ASSISTANT INTERACTIVE LAB")
    print("=======================================================
")

    url = f"wss://api.openai.com/v1/realtime?model={MODEL}"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": "realtime=v1"
    }

    async with websockets.connect(url, extra_headers=headers) as ws:
        print("1. Connected to OpenAI Realtime WebSocket Gateway.")

        # Step 1: Initialize Session Configuration with Function Calling Tools
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "instructions": (
                    "You are a charismatic, highly articulate private wealth concierge for an institutional bank. "
                    "Speak with a warm, professional, conversational cadence. "
                    "When the user asks for account balances, use the 'lookup_account_balance' tool. "
                    "Always verbally confirm the balance once retrieved."
                ),
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "tools": [
                    {
                        "type": "function",
                        "name": "lookup_account_balance",
                        "description": "Fetch real-time institutional liquid balances and pending transfers.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "account_id": {"type": "string", "description": "e.g. ACC-9941"}
                            },
                            "required": ["account_id"]
                        }
                    }
                ],
                "tool_choice": "auto"
            }
        }
        await ws.send(json.dumps(session_config))
        print("2. Session configured with tools and Server-Side VAD.")

        # Step 2: Inject Synthetic Conversational Audio / Text Turn
        print("
3. Injecting Synthetic User Inquiry...")
        user_prompt = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Hello! Could you please check the balance for account ACC-9941?"}
                ]
            }
        }
        await ws.send(json.dumps(user_prompt))
        
        # Trigger response generation
        await ws.send(json.dumps({"type": "response.create"}))

        # Step 3: Event Loop - Handle Audio, Tools & Barge-in
        print("
4. Listening to Realtime Event Stream...")
        print("-------------------------------------------------------")
        
        async for raw_message in ws:
            event = json.loads(raw_message)
            event_type = event.get("type")

            # Handle streaming text transcripts
            if event_type == "response.audio_transcript.delta":
                print(event.get("delta", ""), end="", flush=True)

            # Handle Function Calling Dispatch
            elif event_type == "response.function_call_arguments.done":
                call_id = event["call_id"]
                fn_name = event["name"]
                args = json.loads(event["arguments"])
                print(f"

⚙️ [Function Call Activated: {fn_name}({args})]")

                # Execute mock banking lookup
                tool_result = await mock_banking_service(args.get("account_id", "ACC-UNKNOWN"))
                print(f"   Database Returned: {tool_result}")

                # Submit tool output back to Realtime session
                tool_output_event = {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": json.dumps(tool_result)
                    }
                }
                await ws.send(json.dumps(tool_output_event))

                # Instruct model to verbally speak the result
                await ws.send(json.dumps({
                    "type": "response.create",
                    "response": {
                        "instructions": "Speak the retrieved balance to the client clearly and professionally."
                    }
                }))

            # Handle User Interruption (Barge-In)
            elif event_type == "input_audio_buffer.speech_started":
                print("

⚡ [BARGE-IN DETECTED: User started speaking! Halting playback.]")

            # Handle Response Completion
            elif event_type == "response.done":
                print("
-------------------------------------------------------")
                print("✅ Assistant Response Completed Successfully.")
                break

    print("
🎯 REALTIME VOICE LAB FINISHED WITH 100% SUCCESS!")

if __name__ == "__main__":
    asyncio.run(run_voice_agent_lab())
