import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1500,
    temperature=0.8,
    top_p=0.95,
    messages=[
        {
            "role": "user",
            "content": "Draft three distinct hooks for our cloud storage product."
        }
    ]
)

print(message.content[0].text)
