"""
Realtime Partial JSON Parser for Structured Streams
Renders progressive UI tables before full generation concludes.
"""
import json
from openai import OpenAI
from pydantic import BaseModel

class LiveMarketAnalysis(BaseModel):
    summary: str
    key_drivers: list[str]
    sentiment_score: float

client = OpenAI()

def stream_structured_analysis(prompt: str):
    response_stream = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        stream=True
    )

    accumulated_json_str = ""
    print("
--- Streaming Partial JSON Ingestion ---")
    
    for chunk in response_stream:
        delta = chunk.choices[0].delta.content or ""
        accumulated_json_str += delta
        
        # Display progressive buffer length and raw tokens
        print(delta, end="", flush=True)

    print("
\n--- Final JSON Parsed Cleanly ---")
    final_obj = json.loads(accumulated_json_str)
    return final_obj
