import json
from groq import Groq
from dotenv import load_dotenv
import os

# Load API key
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)

# Load the generated prompt
with open("summary_prompt.txt", "r", encoding="utf-8") as f:
    prompt = f.read()

# Call the AI model
response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "system", "content": "You are an expert business analyst."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3,
    max_tokens=700
)

summary = response.choices[0].message.content

# Save output
with open("ai_summary.txt", "w", encoding="utf-8") as f:
    f.write(summary)

print("\n=== AI Summary Generated Successfully ===\n")
print(summary)
