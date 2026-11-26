# Implementing Native Matryoshka Slicing via OpenAI SDK
from openai import OpenAI
import numpy as np

client = OpenAI()

def get_matryoshka_embedding(text: str, dimensions: int = 1024) -> list[float]:
    # The API natively slices and re-normalizes when dimensions is passed!
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text,
        dimensions=dimensions
    )
    return response.data[0].embedding
