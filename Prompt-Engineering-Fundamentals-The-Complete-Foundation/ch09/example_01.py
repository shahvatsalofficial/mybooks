import openai

client = openai.OpenAI()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": "You are a precise data extraction engine. Output raw JSON only."
        },
        {
            "role": "user",
            "content": "Extract all transaction values from: Paid $500 for hosting, then $20 for domain."
        }
    ],
    temperature=0.0,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0
)

print(response.choices[0].message.content)
