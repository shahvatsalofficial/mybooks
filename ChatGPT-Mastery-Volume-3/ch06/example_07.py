# realtime_webrtc_client.py — Python Realtime Audio Streaming
import asyncio
import json
import os
import pyaudio
import websockets

CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000 # 24kHz audio required by GPT-4o Realtime API

async def stream_audio_session(endpoint: str, api_key: str, deployment: str):
    p = pyaudio.PyAudio()
    mic_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
    speaker_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)

    ws_url = f"wss://{endpoint}/openai/realtime?api-version=2024-10-01-preview&deployment={deployment}"
    headers = {"api-key": api_key, "OpenAI-Beta": "realtime=v1"}

    async with websockets.connect(ws_url, extra_headers=headers) as ws:
        print("Connected to Realtime Voice Socket. Speak into microphone...")

        # Task 1: Stream microphone audio to Azure
        async def send_mic():
            while True:
                data = mic_stream.read(CHUNK_SIZE, exception_on_overflow=False)
                payload = {
                    "type": "input_audio_buffer.append",
                    "audio": data.hex()
                }
                await ws.send(json.dumps(payload))
                await asyncio.sleep(0.01)

        # Task 2: Stream incoming audio to speakers
        async def receive_audio():
            async for message in ws:
                event = json.parse(message)
                if event.get("type") == "response.audio.delta":
                    raw_audio = bytes.fromhex(event["delta"])
                    speaker_stream.write(raw_audio)

        await asyncio.gather(send_mic(), receive_audio())
